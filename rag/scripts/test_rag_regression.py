"""Regression tests for scoped retrieval and answer-stream configuration.

Run in the pipeline container after dependencies are installed:
    python /app/scripts/test_rag_regression.py
"""

import json
import io
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

RAG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAG_ROOT))


def _install_dependency_stubs_for_unit_tests():
    """Allow pure retrieval tests to run on a host without container packages.

    Production imports the real packages.  The small fallbacks only cover the
    code paths exercised here; integration tests still run in the container.
    """
    try:
        import requests  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["requests"] = types.SimpleNamespace(post=None)
    try:
        from pydantic import BaseModel  # noqa: F401
    except ModuleNotFoundError:
        pydantic = types.ModuleType("pydantic")
        pydantic.BaseModel = object
        sys.modules["pydantic"] = pydantic
    try:
        import chromadb  # noqa: F401
    except ModuleNotFoundError:
        chromadb = types.ModuleType("chromadb")
        chromadb.PersistentClient = object
        chromadb_utils = types.ModuleType("chromadb.utils")
        chromadb_utils.embedding_functions = types.SimpleNamespace()
        sys.modules["chromadb"] = chromadb
        sys.modules["chromadb.utils"] = chromadb_utils
    try:
        from rank_bm25 import BM25Okapi  # noqa: F401
    except ModuleNotFoundError:
        rank_bm25 = types.ModuleType("rank_bm25")

        class BM25Okapi:  # Minimal lexical scorer for scoped-retrieval tests.
            def __init__(self, corpus):
                self.corpus = corpus

            def get_scores(self, query):
                return [sum(token in document for token in query) for document in self.corpus]

        rank_bm25.BM25Okapi = BM25Okapi
        sys.modules["rank_bm25"] = rank_bm25
    try:
        from transformers import AutoTokenizer  # noqa: F401
    except ModuleNotFoundError:
        transformers = types.ModuleType("transformers")
        transformers.AutoTokenizer = object
        sys.modules["transformers"] = transformers
    try:
        import yaml  # noqa: F401
    except ModuleNotFoundError:
        yaml = types.ModuleType("yaml")
        yaml.safe_load = lambda *_: {}
        sys.modules["yaml"] = yaml


_install_dependency_stubs_for_unit_tests()

from pipelines import rag_pipeline
from scripts import eval_retrieval
from scripts.index_documents import (
    classify_document,
    is_toc_or_catalog_page,
    split_inline_menu_sections,
    split_pdf_page_sections,
)
from scripts.swagger_yaml_to_md import collect_operation_schema_refs


class ScopedRetrievalTests(unittest.TestCase):
    def test_alpeta_protocol_scope_is_explicit(self):
        self.assertEqual(
            rag_pipeline.detect_retrieval_scope("Alpeta 프로토콜의 Param3[0]을 설명해줘"),
            {"document_type": "protocol", "product": "alpeta"},
        )

    def test_known_protocol_filename_is_classified_as_alpeta(self):
        metadata = classify_document(Path("주장치_Protocol_v1.0.pdf"))
        self.assertEqual(metadata["document_type"], "protocol")
        self.assertEqual(metadata["product"], "alpeta")
        self.assertEqual(metadata["protocol_generation"], "legacy")
        self.assertEqual(metadata["protocol_version"], "1.0")

    def test_current_protocol_filename_has_version_scope(self):
        metadata = classify_document(Path("Communication protocol for Terminal v4.0_Re19.pdf"))
        self.assertEqual(metadata["document_type"], "protocol")
        self.assertEqual(metadata["product"], "alpeta")
        self.assertEqual(metadata["protocol_generation"], "current")
        self.assertEqual(metadata["protocol_version"], "4.0")

    def test_new_protocol_query_selects_current_generation(self):
        self.assertEqual(
            rag_pipeline.detect_retrieval_scope("신규 protocol에서 출입그룹 어떻게 내려?"),
            {"document_type": "protocol", "protocol_generation": "current"},
        )

    def test_download_word_expands_to_protocol_transfer_terms(self):
        expanded = rag_pipeline.expand_retrieval_query(
            "신규 protocol에서 출입그룹 어떻게 내려?",
            "신규 프로토콜 출입그룹",
        )
        self.assertIn("Server Terminal", expanded)
        self.assertIn("Door 설정 전송", expanded)
        self.assertIn("v4.0", expanded)

    def test_swagger_filename_is_classified_as_api(self):
        """swagger/openapi/api 파일명은 document_type=api로 분류되어야 합니다."""
        metadata = classify_document(Path("swagger_kr.md"))
        self.assertEqual(metadata["document_type"], "api")

    def test_api_markdown_filename_is_classified_as_api(self):
        """일반 api 문서도 document_type=api로 분류되어야 합니다."""
        metadata = classify_document(Path("api.md"))
        self.assertEqual(metadata["document_type"], "api")

    def test_alpeta_swagger_scope_prefers_api_without_product(self):
        """alpeta+swagger 질문은 product 필터로 swagger를 지우지 않도록 api 타입만 씁니다."""
        scope = rag_pipeline.detect_retrieval_scope(
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 스키마 구조와 사용하는 API 명세 줘"
        )
        self.assertEqual(scope, {"document_type": "api"})

    def test_facewt_technical_tokens_are_preserved(self):
        """CamelCase·대문자 스키마 토큰이 exact token으로 보존되는지 확인합니다."""
        tokens = {
            token.casefold()
            for token in rag_pipeline.extract_technical_tokens("FaceWT와 FAW 스키마")
        }
        self.assertIn("facewt", tokens)
        self.assertIn("faw", tokens)

    def test_api_intent_ranks_swagger_over_user_guide(self):
        """API/스키마 의도에서는 swagger 청크가 User Guide FAW 설명보다 근거 점수가 높아야 합니다."""
        query = "alpeta swagger에서 FaceWT 스키마와 API 명세 줘"
        swagger = (
            "[Document: swagger_kr | Type: api] ## GET `/v1/users/{id}/faceWTInfo` "
            "**스키마 `FaceWTInfo`** TemplateType TemplateSize TemplateData"
        )
        guide = (
            "[Document: Alpeta User Guide | Type: user_guide | Product: alpeta] "
            "인증 수단에 FAW가 포함된 경우 얼굴 등록 UI"
        )
        self.assertGreater(
            rag_pipeline.technical_evidence_score(query, swagger),
            rag_pipeline.technical_evidence_score(query, guide),
        )

    def test_scope_excludes_user_guide_and_install_manual(self):
        records = [
            {
                "id": "protocol",
                "document": "[Document: 주장치_Protocol] Param3 command protocol",
                "metadata": {
                    "source": "주장치_Protocol_v1.0.pdf",
                    "document_type": "protocol",
                    "product": "alpeta",
                },
            },
            {
                "id": "guide",
                "document": "[Document: Alpeta User Guide] Alpeta login guide",
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                    "product": "alpeta",
                },
            },
            {
                "id": "install",
                "document": "[Document: NSIS 알페타 설치] install package",
                "metadata": {
                    "source": "NSIS 알페타 설치 패키지 빌드 매뉴얼_V2.1.pdf",
                    "document_type": "install",
                    "product": "alpeta",
                },
            },
        ]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(records, handle, ensure_ascii=False)
            index_path = handle.name
        self.addCleanup(lambda: Path(index_path).unlink(missing_ok=True))

        with patch.object(rag_pipeline, "retrieve_vector_documents", return_value=[]):
            documents = rag_pipeline.retrieve_documents(
                chroma_path="unused",
                collection_name="unused",
                embedding_model="unused",
                query="Alpeta protocol Param3",
                top_k=4,
                min_relevance_score=0.0,
                bm25_index_path=index_path,
                scope={"document_type": "protocol", "product": "alpeta"},
            )

        self.assertEqual([doc["source"] for doc in documents], ["주장치_Protocol_v1.0.pdf"])

    def test_user_terminal_procedure_scope_excludes_protocol_and_install(self):
        """사용자·단말기 추가와 동기화 절차는 명시적 문서명 없이도 User Guide만 검색합니다."""
        question = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        self.assertTrue(rag_pipeline.is_user_terminal_procedure_intent(question))
        self.assertEqual(
            rag_pipeline.detect_retrieval_scope(question),
            {"product": "alpeta", "document_type": "user_guide"},
        )

    def test_context_budget_keeps_whole_chunks(self):
        documents = [
            {"source": "protocol.pdf", "content": "a" * 60, "score": 1.0},
            {"source": "guide.pdf", "content": "b" * 60, "score": 0.9},
        ]
        selected = rag_pipeline.limit_documents_for_context(documents, 100)
        self.assertEqual([doc["source"] for doc in selected], ["protocol.pdf"])

    def test_bm25_index_is_cached_until_file_changes(self):
        records = [{"id": "a", "document": "protocol packet", "metadata": {"source": "a.pdf"}}]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            json.dump(records, handle, ensure_ascii=False)
            index_path = handle.name
        self.addCleanup(lambda: Path(index_path).unlink(missing_ok=True))

        first_records, first_bm25 = rag_pipeline._get_bm25_index(index_path)
        second_records, second_bm25 = rag_pipeline._get_bm25_index(index_path)
        self.assertIs(first_records, second_records)
        self.assertIs(first_bm25, second_bm25)


class RerankTests(unittest.TestCase):
    def test_rerank_orders_documents_by_cross_encoder_score(self):
        documents = [
            {"source": "guide.pdf", "content": "irrelevant text", "score": 0.9},
            {"source": "protocol.pdf", "content": "access group transfer", "score": 0.8},
        ]

        class FakeCrossEncoder:
            def predict(self, pairs):
                return [0.1 if "irrelevant" in doc else 0.9 for _, doc in pairs]

        with patch.object(rag_pipeline, "_get_reranker", return_value=FakeCrossEncoder()):
            ranked = rag_pipeline.rerank_documents("출입그룹 전송", documents, "fake-model", top_k=2)

        self.assertEqual([doc["source"] for doc in ranked], ["protocol.pdf", "guide.pdf"])
        self.assertGreater(ranked[0]["rerank_score"], ranked[1]["rerank_score"])

    def test_rerank_falls_back_to_input_order_without_model(self):
        documents = [
            {"source": "first.pdf", "content": "one", "score": 0.9},
            {"source": "second.pdf", "content": "two", "score": 0.8},
        ]
        with patch.object(rag_pipeline, "_get_reranker", return_value=None):
            ranked = rag_pipeline.rerank_documents("질문", documents, "fake-model", top_k=2)
        self.assertEqual([doc["source"] for doc in ranked], ["first.pdf", "second.pdf"])


class TechnicalEvidenceTests(unittest.TestCase):
    """파일 역할·경로·명령 질문의 일반 검색 근거 보존을 검증합니다."""

    def test_expansion_always_preserves_original_question(self):
        """재작성 결과가 의미를 바꿔도 원질문 lexical signal을 첫 변형에 유지합니다."""
        original = "자동화 배치 파일 이름과 경로가 뭐야?"
        expanded = rag_pipeline.expand_retrieval_query(
            original,
            "installer executable configuration",
        )
        self.assertEqual(expanded.splitlines()[0], original)
        self.assertIn("installer executable configuration", expanded)

    def test_bm25_tokenizer_keeps_path_filename_and_extension_parts(self):
        """Windows 경로와 파일명의 전체·부분 토큰이 각각 검색 가능해야 합니다."""
        tokens = rag_pipeline._bm25_tokens(
            r"D:\tools\release\deploy_package.bat output.exe"
        )
        self.assertIn(r"d:\tools\release\deploy_package.bat", tokens)
        self.assertIn("deploy_package", tokens)
        self.assertIn("bat", tokens)
        self.assertIn("output.exe", tokens)
        self.assertIn("exe", tokens)

    def test_artifact_intent_distinguishes_automation_from_executable(self):
        """자동화 파일 질문이 실행 산출물 의도로 변형되지 않게 분류합니다."""
        intents = rag_pipeline.detect_artifact_intents(
            "설치 자동화 파일 이름이 뭐야?"
        )
        self.assertIn("automation", intents)
        self.assertNotIn("executable", intents)

    def test_batch_script_does_not_gain_nsis_script_priority(self):
        """batch script 질문은 자동화로만 분류하고 `.bat` 근거를 `.nsi`보다 높입니다."""
        query = "Which batch script runs the package automation?"
        self.assertEqual(rag_pipeline.detect_artifact_intents(query), ["automation"])
        batch_score = rag_pipeline.technical_evidence_score(
            query,
            "Run package_release.bat to automate the build.",
        )
        nsis_score = rag_pipeline.technical_evidence_score(
            query,
            "Edit package_installer.nsi before compiling.",
        )
        self.assertGreater(batch_score, nsis_score)

    def test_nsis_script_prefers_nsi_over_batch_file(self):
        """NSIS 소스 스크립트 질문에서는 `.nsi` 근거가 `.bat` 자동화보다 높습니다."""
        query = "설치 패키지의 NSIS 스크립트 파일은?"
        self.assertEqual(rag_pipeline.detect_artifact_intents(query), ["script"])
        nsis_score = rag_pipeline.technical_evidence_score(
            query,
            "package_installer.nsi 스크립트를 수정합니다.",
        )
        batch_score = rag_pipeline.technical_evidence_score(
            query,
            "package_release.bat 파일을 실행합니다.",
        )
        self.assertGreater(nsis_score, batch_score)

    def test_technical_evidence_prefers_matching_file_role(self):
        """자동화 질문에서는 배치 실행 근거가 exe 산출물 근거보다 높아야 합니다."""
        query = "패키지를 만드는 자동화 파일 이름은?"
        batch_score = rag_pipeline.technical_evidence_score(
            query,
            r"C:\release 폴더에서 deploy.bat 파일을 실행합니다.",
        )
        executable_score = rag_pipeline.technical_evidence_score(
            query,
            r"완료되면 C:\release\output.exe 설치 파일이 생성됩니다.",
        )
        self.assertGreater(batch_score, executable_score)

    def test_rrf_boosts_matching_artifact_without_specific_filename(self):
        """일반 자동화 의도만으로 배치 근거가 exe 근거보다 우선해야 합니다."""
        vector_docs = [
            {"source": "guide.pdf", "content": "output.exe 설치 파일이 생성됩니다.", "score": 0.9},
            {"source": "guide.pdf", "content": "release.bat 파일을 실행합니다.", "score": 0.8},
        ]
        ranked = rag_pipeline._rrf_merge(
            vector_docs,
            [],
            top_k=2,
            query="설치 자동화 파일 이름은?",
        )
        self.assertIn("release.bat", ranked[0]["content"])
        self.assertGreater(ranked[0]["technical_evidence_score"], 0)

    def test_reranker_combines_semantic_and_artifact_evidence(self):
        """근소한 모델 점수 차이보다 일치하는 파일 역할 근거를 우선합니다."""
        documents = [
            {"source": "guide.pdf", "content": "output.exe 설치 파일이 생성됩니다.", "score": 0.9},
            {"source": "guide.pdf", "content": "release.bat 파일을 실행합니다.", "score": 0.8},
        ]

        class FakeCrossEncoder:
            """고정 점수로 결합 리랭킹만 검증하는 테스트 대역입니다."""

            def predict(self, pairs):
                """첫 문서에 조금 높은 의미 점수를 반환합니다."""
                return [0.95, 0.85]

        with patch.object(rag_pipeline, "_get_reranker", return_value=FakeCrossEncoder()):
            ranked = rag_pipeline.rerank_documents(
                "설치 자동화 파일 이름은?",
                documents,
                "fake-model",
                top_k=2,
            )
        self.assertIn("release.bat", ranked[0]["content"])
        self.assertGreater(
            ranked[0]["combined_rerank_score"],
            ranked[1]["combined_rerank_score"],
        )

    def test_answer_prompt_requires_exact_role_and_path_evidence(self):
        """답변 프롬프트가 파일 역할 구분과 경로 비추측 규칙을 포함해야 합니다."""
        prompt = rag_pipeline.build_context_prompt(
            "배포 자동화 파일 이름과 경로는?",
            [
                {
                    "source": "guide.pdf",
                    "score": 1.0,
                    "content": r"C:\release 폴더의 deploy.bat 파일을 실행합니다.",
                }
            ],
        )
        self.assertIn("자동화/배치 파일", prompt)
        self.assertIn(r"`폴더\파일명` 전체 경로", prompt)
        self.assertIn("문서에 없는 경로를 추측하지 마세요", prompt)
        self.assertIn(r"C:\release\deploy.bat", prompt)

    def test_explicit_path_derivation_requires_same_instruction(self):
        """한 지시문 안의 폴더와 파일명만 결합하고 청크 사이는 연결하지 않습니다."""
        paths = rag_pipeline.derive_explicit_file_paths(
            [
                {"content": r"C:\tools\release 폴더로 이동해 deploy.cmd 파일을 실행합니다."},
                {"content": r"D:\unrelated 폴더로 이동합니다."},
                {"content": "other.exe 파일을 실행합니다."},
            ]
        )
        self.assertEqual(paths, [r"C:\tools\release\deploy.cmd"])

    def test_target_retrieval_and_prompt_contract_excludes_executable_answer(self):
        """대상 질문에서 배치 청크가 exe 청크보다 앞서고 전체 경로가 프롬프트에 남습니다."""
        question = "nsis로 알페타 설치하는 자동화 파일 이름이 뭐야?"
        candidates = [
            {
                "source": "install.pdf",
                "content": (
                    r"D:\nsis\eXbuilder 폴더로 이동해 "
                    "build_install.bat 파일을 실행합니다."
                ),
                "score": 0.8,
            },
            {
                "source": "install.pdf",
                "content": r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
                "score": 0.9,
            },
        ]
        ranked = rag_pipeline._rrf_merge(candidates, [], top_k=2, query=question)
        self.assertIn("build_install.bat", ranked[0]["content"])
        prompt = rag_pipeline.build_context_prompt(question, ranked[:1])
        self.assertIn(r"D:\nsis\eXbuilder\build_install.bat", prompt)
        self.assertNotIn("AlpetaDevice.exe", prompt)

    def test_list_completeness_intent_and_catalog_heuristic(self):
        """전부/목록 질문은 목록 의도로 분류되고 hex 밀집 청크를 카탈로그로 봅니다."""
        question = "v4.0 프로토콜 전부 리스트업해줘"
        self.assertTrue(rag_pipeline.detect_list_completeness_intent(question))
        catalog = (
            "4.1 Logon (0x0001) ..... 11\n"
            "4.2 Logoff (0x0002) ..... 13\n"
            "5.15 Access (0x010A) .... 59\n"
            "5.16 Init (0x010B) ...... 62\n"
            "5.17 Admin (0x010C) ..... 63\n"
            "5.18 Snapshot (0x0) ..... 64\n"
        )
        partial = "Command Preview 0x0001 0x0002 0x0108"
        self.assertTrue(rag_pipeline.looks_like_command_catalog(catalog))
        self.assertGreater(
            rag_pipeline.technical_evidence_score(question, catalog),
            rag_pipeline.technical_evidence_score(question, partial),
        )
        prompt = rag_pipeline.build_context_prompt(
            question,
            [{"source": "protocol.pdf", "score": 1.0, "content": catalog}],
        )
        self.assertIn("목록 완결성", prompt)

    def test_list_intent_expands_same_source_catalog_chunks(self):
        """목록 의도에서 소스당 상한을 넘기지 않는 범위로 카탈로그 청크를 보충합니다."""
        question = "프로토콜 명령 전체 목록 알려줘"
        selected = [
            {
                "source": "protocol.pdf",
                "content": "overview only 0x0001",
                "score": 1.0,
            }
        ]
        candidates = selected + [
            {
                "source": "protocol.pdf",
                "content": (
                    "TOC 4.1 (0x0001) .. 11 4.2 (0x0002) .. 13 "
                    "5.15 (0x010A) .. 59 5.16 (0x010B) .. 62 "
                    "5.17 (0x010C) .. 63 5.18 (0x0000) .. 64"
                ),
                "score": 0.5,
            },
            {
                "source": "other.pdf",
                "content": "unrelated 0x0001 0x0002 0x0003 0x0004 0x0005 0x0006",
                "score": 0.9,
            },
        ]
        expanded = rag_pipeline.expand_catalog_chunks_from_candidates(
            selected, candidates, question, top_k=4, max_chunks_per_source=3
        )
        self.assertEqual(len(expanded), 2)
        self.assertIn("0x010A", expanded[1]["content"])
        self.assertEqual(expanded[1]["source"], "protocol.pdf")

    def test_complete_catalog_hex_coverage_adds_missing_codes(self):
        """목록 의도에서 같은 출처 BM25 카탈로그로 아직 없는 hex를 보충합니다."""
        question = "프로토콜 명령 전부 리스트업해줘"
        selected = [
            {
                "source": "protocol.pdf",
                "content": "Command Preview 0x0001 0x0002 0x0108",
                "score": 1.0,
            }
        ]
        records = [
            {
                "document": "Command Preview 0x0001 0x0002 0x0108",
                "metadata": {"source": "protocol.pdf"},
            },
            {
                "document": "5.15 출입그룹 (0x010A) ................ 59",
                "metadata": {"source": "protocol.pdf"},
            },
            {
                "document": "5.16 초기화 (0x010B) ................ 62",
                "metadata": {"source": "protocol.pdf"},
            },
            {
                "document": "unrelated other.pdf 0xFFFF",
                "metadata": {"source": "other.pdf"},
            },
        ]
        completed = rag_pipeline.complete_catalog_hex_coverage(
            selected, records, question, top_k=4, max_chunks_per_source=4
        )
        joined = "\n".join(doc["content"] for doc in completed)
        self.assertIn("0x010A", joined)
        self.assertIn("0x010B", joined)
        self.assertTrue(all(doc["source"] == "protocol.pdf" for doc in completed))

    def test_output_folder_intent_prefers_verify_path_over_exe_location(self):
        """빌드 후 확인 폴더 질문은 exe 생성 경로보다 확인/이동 폴더 근거를 우선합니다."""
        question = "alpeta 빌드 완료 후에 설치 파일을 확인하는 폴더는?"
        intents = rag_pipeline.detect_artifact_intents(question)
        self.assertIn("output_folder", intents)
        self.assertNotIn("executable", intents)
        verify_score = rag_pipeline.technical_evidence_score(
            question,
            r"완료하면 창을 닫고 D:\nsis\install 폴더로 이동하면 생성된 설치 파일을 확인할 수 있습니다.",
        )
        setup_score = rag_pipeline.technical_evidence_score(
            question,
            r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
        )
        self.assertGreater(verify_score, setup_score)
        ranked = rag_pipeline._rrf_merge(
            [
                {
                    "source": "install.pdf",
                    "content": r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
                    "score": 0.95,
                },
                {
                    "source": "install.pdf",
                    "content": (
                        r"완료하면 창을 닫고 D:\nsis\install 폴더로 이동하면 "
                        "생성된 설치 파일을 확인할 수 있습니다."
                    ),
                    "score": 0.8,
                },
            ],
            [],
            top_k=2,
            query=question,
        )
        self.assertIn(r"D:\nsis\install", ranked[0]["content"])
        prompt = rag_pipeline.build_context_prompt(question, ranked[:1])
        self.assertIn("결과물 확인 폴더", prompt)

    def test_device_exe_path_question_still_uses_executable_intent(self):
        """기존 AlpetaDevice.exe 생성 경로 질문은 executable로 남아 setup 근거를 유지합니다."""
        question = "AlpetaDevice.exe 설치 파일이 생성되는 경로는?"
        intents = rag_pipeline.detect_artifact_intents(question)
        self.assertIn("executable", intents)
        self.assertNotIn("output_folder", intents)
        setup_score = rag_pipeline.technical_evidence_score(
            question,
            r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
        )
        verify_score = rag_pipeline.technical_evidence_score(
            question,
            r"D:\nsis\install 폴더로 이동하면 생성된 설치 파일을 확인합니다.",
        )
        self.assertGreater(setup_score, verify_score)

    def test_build_output_intent_prefers_completed_batch_output_over_device_stage(self):
        """일반 빌드 완료 산출 경로는 Device exe 중간 위치보다 완료 문장을 우선합니다."""
        question = "alpeta 빌드 완료 후에 설치 파일이 어디에 생겨?"
        intents = rag_pipeline.detect_artifact_intents(question)
        self.assertIn("build_output", intents)
        self.assertNotIn("executable", intents)
        final_score = rag_pipeline.technical_evidence_score(
            question,
            r"배치파일 실행이 완료되면 D:\nsis\install 폴더에 설치파일이 생성됩니다.",
        )
        device_stage_score = rag_pipeline.technical_evidence_score(
            question,
            r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
        )
        self.assertGreater(final_score, device_stage_score)
        ranked = rag_pipeline._rrf_merge(
            [
                {
                    "source": "install.pdf",
                    "content": r"AlpetaDevice.exe 파일 위치는 D:\nsis\Alpeta\setup 입니다.",
                    "score": 0.95,
                },
                {
                    "source": "install.pdf",
                    "content": (
                        r"배치파일 실행이 완료되면 D:\nsis\install 폴더에 "
                        "설치파일이 생성됩니다."
                    ),
                    "score": 0.8,
                },
            ],
            [],
            top_k=2,
            query=question,
        )
        self.assertIn(r"D:\nsis\install", ranked[0]["content"])

    def test_user_terminal_procedure_evidence_and_prompt_keep_manual_automatic_split(self):
        """수동 전송·자동 동기화 청크가 가점과 답변 범위 지침을 함께 받는지 확인합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        manual = (
            "단말기 사용자 리스트 추가에서 사용자를 선택하고 적용하면 "
            "단말기로 사용자 정보가 전송됩니다."
        )
        automatic = (
            "일반설정 사용자에서 단말기 사용자 정보 자동 동기화 사용을 설정합니다. "
            "사용자와 단말기가 동일한 출입그룹으로 설정되어야 동기화됩니다."
        )
        unrelated = "NSIS 설치 파일을 빌드합니다."
        self.assertGreater(
            rag_pipeline.procedure_evidence_score(question, manual),
            rag_pipeline.procedure_evidence_score(question, unrelated),
        )
        self.assertGreater(
            rag_pipeline.procedure_evidence_score(question, automatic),
            rag_pipeline.procedure_evidence_score(question, unrelated),
        )
        prompt = rag_pipeline.build_context_prompt(
            question,
            [
                {"source": "Alpeta User Guide.pdf", "score": 1.0, "content": manual},
                {"source": "Alpeta User Guide.pdf", "score": 0.9, "content": automatic},
            ],
        )
        self.assertIn("수동으로 특정 단말기에 추가·전송", prompt)
        self.assertIn("독립된 방법으로 각각 설명", prompt)
        self.assertNotIn("[단말기리스트] → [단말기 사용자 리스트]", prompt)
        self.assertIn("단말기 저장 리스트", prompt)
        self.assertIn("Protocol·NSIS 문서", prompt)

    def test_procedure_context_completes_manual_and_automatic_facets(self):
        """복합 절차 질문은 같은 가이드의 수동 전송과 자동 동기화 근거를 모두 남깁니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        selected = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": "사용자 정보 저장 시 변경 사항을 업데이트합니다.",
                "score": 1.0,
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            }
        ]
        records = [
            {
                "document": (
                    "단말기 사용자 리스트 추가에서 사용자를 선택하고 적용하면 "
                    "단말기로 사용자 정보가 전송됩니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
            {
                "document": (
                    "단말기 사용자 정보 자동 동기화 사용을 설정합니다. "
                    "사용자와 단말기가 동일한 출입그룹으로 설정되어야 동기화됩니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
        ]
        completed = rag_pipeline.complete_procedure_context(
            selected,
            records,
            question,
            top_k=4,
            scope={"document_type": "user_guide"},
        )
        joined = "\n".join(document["content"] for document in completed)
        self.assertIn("단말기 사용자 리스트", joined)
        self.assertIn("자동 동기화", joined)

    def test_procedure_context_preserves_parent_terminal_list_menu(self):
        """분리된 상위 메뉴 청크도 수동 전송 답변의 메뉴 순서 근거로 보존합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        selected = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": "단말기 사용자 리스트에서 사용자를 선택하고 적용하면 전송됩니다.",
                "score": 1.0,
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            }
        ]
        records = [
            {
                "document": (
                    "[단말기리스트]를 클릭하면 해당 사용자가 내려가 있는 단말기 리스트를 "
                    "보고 원하는 단말기에 사용자를 내릴 수 있습니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            }
        ]
        completed = rag_pipeline.complete_procedure_context(
            selected,
            records,
            question,
            top_k=2,
            scope={"document_type": "user_guide"},
        )
        self.assertIn("[단말기리스트]", "\n".join(doc["content"] for doc in completed))

    def test_build_output_context_keeps_completed_install_folder(self):
        """빌드 완료 문장이 떨어진 청크여도 최종 설치 폴더 근거를 선택합니다."""
        question = "빌드 완료 후 설치 파일이 어디에 생겨?"
        selected = [
            {
                "source": "install.pdf",
                "content": r"AlpetaDevice.exe는 D:\nsis\Alpeta\setup에서 생성됩니다.",
                "score": 1.0,
                "metadata": {"source": "install.pdf", "document_type": "install"},
            }
        ]
        records = [
            {
                "document": r"배치파일 실행이 완료되면 D:\nsis\install 폴더에 설치파일이 생성됩니다.",
                "metadata": {"source": "install.pdf", "document_type": "install"},
            }
        ]
        completed = rag_pipeline.complete_build_output_context(
            selected,
            records,
            question,
            top_k=2,
            scope={"document_type": "install"},
        )
        self.assertIn(r"D:\nsis\install", "\n".join(doc["content"] for doc in completed))

    def test_is_automated_build_intent_detects_general_markers(self):
        """특정 질문 문자열이 아닌 일반 마커 조합으로 자동화 버전 빌드 의도를 감지합니다."""
        self.assertTrue(
            rag_pipeline.is_automated_build_intent("alpeta 자동빌드하려면 어떻게 하면돼?")
        )
        self.assertTrue(
            rag_pipeline.is_automated_build_intent("빌드를 자동화 버전으로 진행하는 방법은?")
        )
        self.assertFalse(
            rag_pipeline.is_automated_build_intent("alpeta 수동 빌드는 어떻게 해?")
        )
        self.assertFalse(
            rag_pipeline.is_automated_build_intent("설치 자동화 파일 이름이 뭐야?")
        )

    def test_expand_retrieval_query_adds_automated_build_section_terms(self):
        """자동화 버전 빌드 의도에서 문서 실제 표현으로 검색 확장이 추가되는지 확인합니다."""
        expanded = rag_pipeline.expand_retrieval_query(
            "alpeta 자동빌드하려면 어떻게 하면돼?", "alpeta 자동빌드하려면 어떻게 하면돼?"
        )
        self.assertIn("gitpull.bat", expanded)
        self.assertIn("build_install.bat", expanded)
        self.assertIn("define.go", expanded)

    def test_complete_automated_build_context_forces_full_section_and_drops_manual(self):
        """자동화 섹션 청크(앵커 없는 중간 청크 포함)를 모두 포함하고 수동 섹션은 제거합니다."""
        question = "alpeta 자동빌드하려면 어떻게 하면돼?"
        source = "NSIS 알페타 설치 패키지 빌드 매뉴얼_V2.1.pdf"

        def _record(index: int, text: str) -> dict:
            return {
                "document": text,
                "metadata": {
                    "source": source,
                    "chunk_index": index,
                    "document_type": "install",
                    "product": "alpeta",
                },
            }

        records = [
            _record(9, "10. device 설치 파일 빌드가 완료되면 D:\\nsis\\install 폴더로 이동합니다."),
            _record(10, "완료되면 창을 닫고 D:\\nsis\\install 폴더로 이동합니다."),
            _record(
                11,
                "알페타 설치 패키지 빌드(자동화 버전) 1. git pull 을 진행합니다. "
                "D:\\nsis\\eXbuilder 폴더로 이동해 gitpull.bat 을 실행합니다.",
            ),
            _record(
                12,
                "3. alpeta_device.nsi 파일을 열어 버전을 수정합니다. "
                "PRODUCT_VERSION 을 만들고자 하는 버전과 맞게 수정합니다.",
            ),
            _record(
                13,
                "5. build_install.bat 파일을 실행합니다. proto_compile 실행. "
                "완료되면 D:\\nsis\\install 폴더에 설치파일이 생성됩니다.",
            ),
            _record(14, "NSIS 스크립트 가이드: Alpeta 설치 파일 스크립트 세부 설명."),
        ]
        # 실제 버그 재현: 검색이 수동 섹션(9, 10)만 반환하고 자동화 섹션은 놓친 상태.
        selected = [
            {
                "content": records[0]["document"],
                "source": source,
                "score": 0.5,
                "metadata": records[0]["metadata"],
            },
            {
                "content": records[1]["document"],
                "source": source,
                "score": 0.4,
                "metadata": records[1]["metadata"],
            },
        ]
        completed = rag_pipeline.complete_automated_build_context(
            selected,
            records,
            question,
            top_k=2,
            scope={"document_type": "install", "product": "alpeta"},
        )
        joined = "\n".join(doc["content"] for doc in completed)
        self.assertIn("gitpull.bat", joined)
        self.assertIn("PRODUCT_VERSION", joined)
        self.assertIn("build_install.bat", joined)
        self.assertNotIn("완료되면 창을 닫고", joined)
        self.assertNotIn("NSIS 스크립트 가이드", joined)

    def test_automated_build_prompt_requires_full_procedure_and_excludes_manual(self):
        """자동화 버전 답변 지침이 1~7단계 요구와 수동 절차 배제를 함께 명시합니다."""
        question = "alpeta 자동빌드하려면 어떻게 하면돼?"
        prompt = rag_pipeline.build_context_prompt(
            question,
            [
                {
                    "source": "NSIS 알페타 설치 패키지 빌드 매뉴얼_V2.1.pdf",
                    "score": 1.0,
                    "content": "알페타 설치 패키지 빌드(자동화 버전) git pull gitpull.bat",
                }
            ],
        )
        self.assertIn("자동화 버전 빌드 절차", prompt)
        self.assertIn("gitpull.bat", prompt)
        self.assertIn("build_install.bat", prompt)
        self.assertIn("D:\\nsis\\install", prompt)
        self.assertIn("MakeNSISW", prompt)
        self.assertIn("수동 빌드 절차", prompt)

    def test_user_terminal_prompt_requires_dual_method_split_and_caution_enumeration(self):
        """사용자·단말기 절차 지침이 독립된 두 방법 구분과 주의사항 전체 나열을 요구합니다."""
        question = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        prompt = rag_pipeline.build_context_prompt(
            question,
            [
                {
                    "source": "Alpeta User Guide.pdf",
                    "score": 1.0,
                    "content": "단말기 사용자 리스트 추가에서 사용자를 선택하고 적용합니다.",
                }
            ],
        )
        self.assertIn("방법 1」/「방법 2」", prompt)
        self.assertIn("표기 고정", prompt)
        self.assertIn("`출입그룹 단말기 리스트`", prompt)
        self.assertIn("`등록된 단말기`", prompt)
        self.assertIn("`추가가능한 단말기`", prompt)
        self.assertIn("[주의사항]", prompt)

    def test_document_term_pair_completion_preserves_redownload_word(self):
        """재동기화 답변이 재다운로드를 괄호로 축약하면 문서 표현을 보완합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        documents = [
            {
                "content": (
                    "단말기에서 사용자 제거 뒤 출입그룹 다시 동기화 진행이 되면 "
                    "출입그룹에 맞춰 사용자가 다시 다운로드 됩니다."
                )
            }
        ]
        incomplete = "사용자를 제거한 뒤 출입그룹 다시 동기화가 진행됩니다."
        completed = rag_pipeline.enforce_document_term_pairs(
            question,
            documents,
            incomplete,
        )
        self.assertIn("다시 동기화", completed)
        self.assertIn("다시 다운로드", completed)
        self.assertNotEqual(completed, incomplete)

    def test_document_term_enforcement_restores_terminal_list_spelling_and_items(self):
        """공백 의역된 메뉴명과 빠진 화면 구성 항목을 문서 표기로 복원합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        documents = [
            {
                "content": (
                    "[단말기리스트]를 클릭하면 출입그룹 단말기 리스트, "
                    "등록된 단말기, 추가가능한 단말기를 확인할 수 있습니다."
                )
            }
        ]
        paraphrased = (
            "방법 1: [단말기 리스트]를 클릭합니다. "
            "등록된 단말기와 추가 가능한 단말기만 설명합니다."
        )
        completed = rag_pipeline.enforce_document_term_pairs(
            question,
            documents,
            paraphrased,
        )
        self.assertIn("[단말기리스트]", completed)
        self.assertNotIn("[단말기 리스트]", completed)
        self.assertIn("출입그룹 단말기 리스트", completed)

    def test_document_term_enforcement_normalizes_breadcrumb_gt_before_move_button(self):
        """메뉴 breadcrumb `>`를 제거해 이동 버튼 `>` 순서 근거가 깨지지 않게 합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        documents = [{"content": "[단말기리스트] 단말기 사용자 리스트 추가 적용 전송"}]
        answer = (
            "[단말기리스트] 확인 후 "
            "단말기 사용자 리스트 > [추가] 에서 사용자를 선택하고 > 로 옮긴 뒤 "
            "[적용]하면 단말기 전송됩니다."
        )
        completed = rag_pipeline.enforce_document_term_pairs(question, documents, answer)
        self.assertIn("단말기 사용자 리스트의 [추가]", completed)
        self.assertNotIn("단말기 사용자 리스트 > [추가]", completed)
        self.assertIn("사용자를 선택하고 > 로 옮긴", completed)

    def test_procedure_context_completes_terminal_list_composition_facet(self):
        """단말기리스트 화면 구성 3항목 청크가 빠지면 같은 가이드에서 보충합니다."""
        question = "사용자를 단말기에 추가하고 자동 동기화하는 방법은?"
        selected = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": "단말기 사용자 리스트에서 사용자를 선택하고 적용하면 전송됩니다.",
                "score": 1.0,
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            }
        ]
        records = [
            {
                "document": (
                    "출입그룹 단말기 리스트는 할당 출입그룹의 목록입니다. "
                    "등록된 단말기와 추가가능한 단말기도 함께 표시됩니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            }
        ]
        completed = rag_pipeline.complete_procedure_context(
            selected,
            records,
            question,
            top_k=2,
            scope={"document_type": "user_guide"},
        )
        joined = "\n".join(doc["content"] for doc in completed)
        self.assertIn("출입그룹 단말기 리스트", joined)


class EvaluationContractTests(unittest.TestCase):
    """골든 평가가 출처와 모든 필수 키워드를 함께 요구하는지 검증합니다."""

    def test_source_hit_with_missing_keyword_returns_failure(self):
        """예상 출처가 있어도 필수 키워드 하나가 빠지면 평가 결과는 1이어야 합니다."""
        entries = [
            {
                "question": "배포 명령은?",
                "expected_source": "guide.md",
                "expected_keywords": ["deploy.cmd", "C:\\tools\\deploy.cmd"],
            }
        ]
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".json", delete=False
        ) as handle:
            json.dump(entries, handle, ensure_ascii=False)
            golden_path = handle.name
        self.addCleanup(lambda: Path(golden_path).unlink(missing_ok=True))
        documents = [
            {"source": "guide.md", "content": "deploy.cmd 파일을 실행합니다.", "score": 1.0}
        ]
        output = io.StringIO()
        with patch.object(
            eval_retrieval.rag_pipeline,
            "retrieve_documents",
            return_value=documents,
        ), redirect_stdout(output):
            result = eval_retrieval.evaluate(golden_path, top_k=2, rerank=False)
        self.assertEqual(result, 1)
        self.assertIn("[FAIL]", output.getvalue())
        self.assertIn("source: PASS", output.getvalue())
        self.assertIn("keywords: FAIL", output.getvalue())

    def test_source_and_all_keywords_return_success(self):
        """예상 출처와 모든 필수 키워드가 있으면 평가 결과는 0이어야 합니다."""
        entries = [
            {
                "question": "배포 명령은?",
                "expected_source": "guide.md",
                "expected_keywords": ["deploy.cmd", "C:\\tools\\deploy.cmd"],
            }
        ]
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".json", delete=False
        ) as handle:
            json.dump(entries, handle, ensure_ascii=False)
            golden_path = handle.name
        self.addCleanup(lambda: Path(golden_path).unlink(missing_ok=True))
        documents = [
            {
                "source": "guide.md",
                "content": r"C:\tools 폴더에서 deploy.cmd 파일을 실행합니다.",
                "score": 1.0,
            }
        ]
        output = io.StringIO()
        with patch.object(
            eval_retrieval.rag_pipeline,
            "retrieve_documents",
            return_value=documents,
        ), redirect_stdout(output):
            result = eval_retrieval.evaluate(golden_path, top_k=2, rerank=False)
        self.assertEqual(result, 0)
        self.assertIn("[PASS]", output.getvalue())
        self.assertIn("source: PASS", output.getvalue())
        self.assertIn("keywords: PASS", output.getvalue())


class PdfSectionChunkingTests(unittest.TestCase):
    def test_numbered_headings_split_page_into_sections(self):
        page_text = (
            "intro line\n"
            "3.1 출입그룹 설정\n"
            "출입그룹을 단말기로 전송한다.\n"
            "3.2 사용자 전송\n"
            "사용자 정보를 전송한다."
        )
        sections = split_pdf_page_sections(page_text)
        self.assertEqual([title for title, _ in sections], ["", "3.1 출입그룹 설정", "3.2 사용자 전송"])
        self.assertIn("출입그룹을 단말기로 전송한다.", sections[1][1])

    def test_page_without_headings_stays_single_unit(self):
        sections = split_pdf_page_sections("plain paragraph\nwith no numbered headings")
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0][0], "")

    def test_toc_like_page_is_kept_as_single_unit(self):
        """목차처럼 짧은 번호·hex·점선 행이 밀집한 페이지는 항목마다 쪼개지 않습니다."""
        page_text = "\n".join(
            [
                "Contents",
                "4.1 Terminal Logon (0x0001) ................................................. 11",
                "4.2 Terminal logoff (0x0002) ............................................. 13",
                "4.3 Time Synchronization (0x0009) ........................................ 14",
                "5.14 Door-lock (0x0108) .................................................... 58",
                "5.15 출입그룹 Door 설정 전송 (0x010A) ...................................................... 59",
                "5.16 주장치 초기화 요청 (0x010B) ................................................................ 62",
                "5.17 주장치 관리자 계정 설정 요청 (0x010C) .............................................. 63",
                "5.18 스냅샷 (주장치 설정 정보) 요청 (0x0) .................................................. 64",
            ]
        )
        self.assertTrue(is_toc_or_catalog_page(page_text))
        sections = split_pdf_page_sections(page_text)
        self.assertEqual(len(sections), 1)
        self.assertIn("0x010A", sections[0][1])
        self.assertIn("스냅샷", sections[0][1])

    def test_inline_menu_title_splits_voip_from_terminal_user_mgmt(self):
        """번호 없는 「단말기 사용자 관리」제목이 VoIP 절과 한 덩어리일 때 분리합니다."""
        text = (
            "단말기에 VoIP 설정을 하는 기능입니다. "
            "단말기 사용자 관리 단말기에 등록된 사용자 정보를 삭제하거나 "
            "서버로 가져올 수 있습니다. 해당 메뉴에서 삭제한 사용자는 단말기에서만 삭제됩니다."
        )
        sections = split_inline_menu_sections("", text)
        self.assertEqual(len(sections), 2)
        self.assertIn("VoIP", sections[0][1])
        self.assertNotIn("단말기 사용자 관리", sections[0][1])
        self.assertEqual(sections[1][0], "단말기 사용자 관리")
        self.assertIn("단말기에서만", sections[1][1])


class TerminalUserManagementIntentTests(unittest.TestCase):
    """「단말기 사용자 관리」메뉴 의도·가점·컨텍스트·프롬프트 회귀."""

    QUESTION = "alpeta 단말기 사용자 관리 메뉴 사용법 알려줘"

    def test_intent_detects_menu_howto_and_excludes_sync_procedure(self):
        """메뉴 사용법 질문만 tum 의도이고, 추가·동기화 복합 질문은 기존 절차 의도입니다."""
        self.assertTrue(rag_pipeline.is_terminal_user_management_intent(self.QUESTION))
        self.assertFalse(rag_pipeline.is_user_terminal_procedure_intent(self.QUESTION))
        sync_q = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        self.assertFalse(rag_pipeline.is_terminal_user_management_intent(sync_q))
        self.assertTrue(rag_pipeline.is_user_terminal_procedure_intent(sync_q))

    def test_query_expansion_prefers_import_upload_terms(self):
        """검색 확장에 가져오기·업로드·단말기에서만 표현이 포함됩니다."""
        expanded = rag_pipeline.expand_retrieval_query(self.QUESTION, self.QUESTION)
        self.assertIn("가져오기", expanded)
        self.assertIn("업로드", expanded)
        self.assertIn("단말기에서만", expanded)
        self.assertIn("단말기 사용자 관리", expanded)

    def test_evidence_prefers_menu_and_import_over_user_reg_and_port(self):
        """메뉴·가져오기 청크가 9003/고유아이디 청크보다 가점이 높습니다."""
        good_overview = (
            "단말기 사용자 관리 단말기에 등록된 사용자를 삭제하거나 서버로 가져올 수 있습니다. "
            "해당 메뉴에서 삭제한 사용자는 단말기에서만 삭제됩니다."
        )
        good_ops = (
            "(단말기 저장 리스트) 가져오기: 선택된 단말기의 사용자 정보를 불러 옵니다. "
            "(단말기 저장 리스트) 업로드: 가져오기로 불러온 사용자 정보를 알페타로 업로드합니다. "
            "(단말기 사용자 리스트) 추가: 적용하면 단말기로 사용자 정보가 전송됩니다."
        )
        bad_port = "단말기 정보 통신포트 9003 으로 설정해야 합니다."
        bad_reg = "사용자 추가 시 고유아이디와 권한(8)을 입력합니다."
        self.assertGreater(
            rag_pipeline.terminal_user_mgmt_evidence_score(self.QUESTION, good_overview),
            rag_pipeline.terminal_user_mgmt_evidence_score(self.QUESTION, bad_port),
        )
        self.assertGreater(
            rag_pipeline.terminal_user_mgmt_evidence_score(self.QUESTION, good_ops),
            rag_pipeline.terminal_user_mgmt_evidence_score(self.QUESTION, bad_reg),
        )

    def test_context_completes_overview_and_ops_facets(self):
        """개요만 선택된 경우 가져오기·추가 조작 청크를 같은 가이드에서 보충합니다."""
        selected = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": (
                    "단말기 사용자 관리 서버로 가져오기와 단말로 내려보내기가 가능합니다. "
                    "삭제하면 단말기에서만 삭제됩니다."
                ),
                "score": 1.0,
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            }
        ]
        records = [
            {
                "document": (
                    "(단말기 저장 리스트) 가져오기 / 업로드 / 엑셀 내보내기 / 삭제. "
                    "알페타에는 남고 단말기에서만 삭제됩니다."
                ),
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            },
            {
                "document": (
                    "(단말기 사용자 리스트) 추가: 사용자를 선택하고 > 후 [적용]하면 "
                    "단말기로 사용자 정보가 전송됩니다."
                ),
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            },
        ]
        completed = rag_pipeline.complete_terminal_user_mgmt_context(
            selected,
            records,
            self.QUESTION,
            top_k=4,
            scope={"document_type": "user_guide"},
        )
        joined = "\n".join(doc["content"] for doc in completed)
        self.assertIn("가져오기", joined)
        self.assertIn("업로드", joined)
        self.assertIn("단말기 사용자 리스트", joined)

    def test_prompt_requires_menu_scope_and_forbids_p34_reg(self):
        """답변 지침이 메뉴 조작을 요구하고 9003·고유아이디 중심을 금합니다."""
        prompt = rag_pipeline.build_context_prompt(
            self.QUESTION,
            [
                {
                    "source": "Alpeta User Guide.pdf",
                    "score": 1.0,
                    "content": "단말기 사용자 관리 가져오기 업로드 추가",
                }
            ],
        )
        self.assertIn("단말기 사용자 관리 메뉴", prompt)
        self.assertIn("가져오기", prompt)
        self.assertIn("9003", prompt)
        self.assertIn("고유아이디", prompt)
        self.assertIn("쓰지 마세요", prompt)


class FollowUpContextTests(unittest.TestCase):
    """후속 질문 감지와 문맥 반영 질문 변환(question condensing) 검증."""

    HISTORY = [
        {"role": "user", "content": "UserFaceWT 관련 API 알려줘"},
        {"role": "assistant", "content": "GET /v1/users/{id}/faceWTInfo 로 조회합니다. ![사진](http://localhost:8090/a.jpg)"},
    ]

    def test_demonstrative_or_short_question_is_follow_up(self):
        self.assertTrue(rag_pipeline.is_follow_up_question("그거 수정하는 API는?", self.HISTORY))
        self.assertTrue(rag_pipeline.is_follow_up_question("해당 스키마 구조 알려줘", self.HISTORY))
        self.assertTrue(rag_pipeline.is_follow_up_question("예시는?", self.HISTORY))

    def test_standalone_question_is_not_follow_up(self):
        self.assertFalse(rag_pipeline.is_follow_up_question("Alpeta 출입그룹 등록 API 알려줘", self.HISTORY))

    def test_without_history_never_follow_up(self):
        self.assertFalse(rag_pipeline.is_follow_up_question("그거 수정하는 API는?", []))

    def test_compact_history_strips_image_markdown(self):
        compacted = rag_pipeline._compact_history(self.HISTORY)
        self.assertIn("faceWTInfo", compacted)
        self.assertNotIn("![", compacted)

    def test_condense_returns_llm_standalone_question(self):
        with patch.object(
            rag_pipeline, "ollama_chat",
            return_value="UserFaceWT 정보를 수정하는 API를 알려줘\n",
        ):
            condensed = rag_pipeline.condense_question(
                "http://ollama", "model", "그거 수정하는 API는?", self.HISTORY,
            )
        self.assertEqual(condensed, "UserFaceWT 정보를 수정하는 API를 알려줘")

    def test_condense_falls_back_to_original_on_llm_error(self):
        with patch.object(rag_pipeline, "ollama_chat", side_effect=RuntimeError("down")):
            condensed = rag_pipeline.condense_question(
                "http://ollama", "model", "그거 수정하는 API는?", self.HISTORY,
            )
        self.assertEqual(condensed, "그거 수정하는 API는?")


class SwaggerSchemaInlineTests(unittest.TestCase):
    """API 상세 청크가 응답/파라미터 스키마까지 품는지(자기완결 청크) 검증."""

    def test_endpoint_collects_nested_response_schemas(self):
        defs = {
            "UserFaceWTInfoResult": {
                "properties": {
                    "Result": {"$ref": "#/definitions/Result"},
                    "UserFaceWTInfo": {"type": "array", "items": {"$ref": "#/definitions/UserFaceWTInfo"}},
                }
            },
            "Result": {"properties": {"ResultCode": {"type": "integer"}}},
            "UserFaceWTInfo": {"properties": {"TemplateData": {"type": "string"}}},
        }
        op = {"responses": {"200": {"schema": {"$ref": "#/definitions/UserFaceWTInfoResult"}}}}
        refs = collect_operation_schema_refs(op, params=[], defs=defs)
        self.assertEqual(refs, ["UserFaceWTInfoResult", "Result", "UserFaceWTInfo"])

    def test_body_parameter_schema_is_collected(self):
        defs = {"UserInfo": {"properties": {"UserID": {"type": "integer"}}}}
        op = {"responses": {}}
        params = [{"name": "body", "in": "body", "schema": {"$ref": "#/definitions/UserInfo"}}]
        self.assertEqual(collect_operation_schema_refs(op, params, defs), ["UserInfo"])


class StreamingOptionsTests(unittest.TestCase):
    def test_stream_passes_token_options_and_handles_length_reason(self):
        payloads = []

        class Response:
            def raise_for_status(self):
                return None

            def iter_lines(self):
                yield b'{"message": {"content": "continued"}, "done": false}'
                yield b'{"done": true, "done_reason": "length", "prompt_eval_count": 100, "eval_count": 20}'

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        def fake_post(*_, **kwargs):
            payloads.append(kwargs["json"])
            return Response()

        with patch.object(rag_pipeline.requests, "post", side_effect=fake_post):
            result = "".join(rag_pipeline.ollama_chat_stream(
                "http://ollama", "model", [{"role": "user", "content": "test"}],
                options={"num_ctx": 8192, "num_predict": 2048},
            ))

        self.assertEqual(result, "continued")
        self.assertEqual(payloads[0]["options"], {"num_ctx": 8192, "num_predict": 2048})
        self.assertIs(payloads[0].get("think"), False)

    def test_status_event_is_not_plain_content_string(self):
        """status는 Open WebUI event dict여야 하며 본문 문자열이 아니어야 합니다."""
        event = rag_pipeline._status_event("문서 검색 준비 중...")
        self.assertIsInstance(event, dict)
        self.assertEqual(event["event"]["type"], "status")
        self.assertEqual(event["event"]["data"]["description"], "문서 검색 준비 중...")
        self.assertFalse(event["event"]["data"]["done"])
        done = rag_pipeline._status_event("", done=True)
        self.assertTrue(done["event"]["data"]["done"])

    def test_repair_spaced_document_tokens_restores_identifiers(self):
        """문서에 있는 식별자의 글자 사이 공백 깨짐을 복원합니다."""
        documents = [
            {
                "source": "swagger_kr.md",
                "content": "FaceWTInfo and /v1/terminals/{id}/scan/facewt",
                "score": 1.0,
            }
        ]
        broken = "Use FA W T and FaceWTIn f o via /v1/t e r m i n a l s/{id}/scan/facewt"
        repaired = rag_pipeline.repair_spaced_document_tokens(documents, broken)
        self.assertIn("FaceWTInfo", repaired)
        self.assertIn("/v1/terminals/{id}/scan/facewt", repaired)
        self.assertNotIn("t e r m i n a l s", repaired)

    def test_answer_prompt_forbids_letter_spacing_in_identifiers(self):
        """답변 프롬프트에 식별자 글자 사이 공백 금지 지침이 포함되는지 확인합니다."""
        prompt = rag_pipeline.build_context_prompt(
            "FaceWT API?",
            [{"source": "swagger_kr.md", "content": "FaceWTInfo", "score": 1.0}],
        )
        self.assertIn("글자 사이 공백", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
