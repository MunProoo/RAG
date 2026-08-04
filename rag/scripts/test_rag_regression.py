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

    def test_facewt_api_schema_questions_not_protocol_hex_intent(self):
        """FaceWT swagger A/B(알려줘 포함)가 프로토콜 hex 단건으로 오인되지 않아야 합니다."""
        question_a = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
            "스키마 구조와 사용하는 API 명세 줘"
        )
        question_b = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
            "API와 스키마구조 알려줘"
        )
        self.assertTrue(rag_pipeline.is_facewt_faw_api_intent(question_a))
        self.assertTrue(rag_pipeline.is_facewt_faw_api_intent(question_b))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(question_a))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(question_b))
        # 위겐드 단건은 여전히 hex 상세여야 합니다.
        self.assertTrue(
            rag_pipeline.is_protocol_hex_detail_intent(
                "v4.0에서 set wiegand 알려줘"
            )
        )

    def test_facewt_ab_expand_converges_without_protocol_command(self):
        """A·B expand가 FaceWT 경로·스키마로 수렴하고 Command 프로토콜 확장을 넣지 않습니다."""
        question_a = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
            "스키마 구조와 사용하는 API 명세 줘"
        )
        question_b = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
            "API와 스키마구조 알려줘"
        )
        for question in (question_a, question_b):
            expanded = rag_pipeline.expand_retrieval_query(question, "")
            self.assertIn("FaceWTInfo", expanded)
            self.assertIn("/v1/users/{id}/faceWTInfo", expanded)
            self.assertIn("/v1/terminals/{id}/scan/facewt", expanded)
            self.assertIn("FAW", expanded)
            self.assertNotIn("Command 명령 코드", expanded)
            self.assertNotIn(
                "Communication protocol for Terminal", expanded
            )

    def test_reinject_essential_facewt_tokens_after_rewrite_drop(self):
        """재작성에서 FaceWT/FAW가 빠지면 필수 토큰이 재주입되어야 합니다."""
        original = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 API와 스키마구조 알려줘"
        )
        rewritten = "alpeta swagger holiday lock option API schema"
        reinjected = rag_pipeline.reinject_essential_retrieval_tokens(
            original, rewritten
        )
        lower = reinjected.casefold()
        self.assertIn("facewt", lower)
        self.assertIn("faw", lower)
        self.assertIn("facewtinfo", lower)

    def test_extract_api_paths_and_enforce_catalog_includes_scan(self):
        """API 카탈로그 헬퍼가 문서 경로를 추출하고 누락 scan을 AND로 보강해야 합니다."""
        query = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
            "스키마 구조와 사용하는 API 명세 줘"
        )
        docs = [
            {
                "source": "swagger_kr.md",
                "content": (
                    "## GET `/v1/users/{id}/faceWTInfo`\n"
                    "- **요약**: 얼굴(faceWT) 정보 조회\n"
                ),
                "score": 1.0,
                "metadata": {"section": "GET `/v1/users/{id}/faceWTInfo`"},
            },
            {
                "source": "swagger_kr.md",
                "content": (
                    "## PUT `/v1/users/{id}/faceWTInfo`\n"
                    "- **요약**: 얼굴(faceWT) 정보 수정\n"
                ),
                "score": 0.9,
                "metadata": {"section": "PUT `/v1/users/{id}/faceWTInfo`"},
            },
            {
                "source": "swagger_kr.md",
                "content": (
                    "## GET `/v1/terminals/{id}/scan/facewt`\n"
                    "- **요약**: 얼굴 이미지 캡쳐 (faceWt)\n"
                ),
                "score": 0.8,
                "metadata": {"section": "GET `/v1/terminals/{id}/scan/facewt`"},
            },
        ]
        extracted = rag_pipeline.extract_api_paths_from_documents(docs)
        paths = {e["path"] for e in extracted}
        self.assertIn("/v1/users/{id}/faceWTInfo", paths)
        self.assertIn("/v1/terminals/{id}/scan/facewt", paths)
        weak = (
            "FaceWT API는 GET/PUT `/v1/users/{id}/faceWTInfo` 만 있습니다."
        )
        enforced = rag_pipeline.enforce_api_endpoint_catalog(query, docs, weak)
        self.assertIn("/v1/users/{id}/faceWTInfo", enforced)
        self.assertIn("/v1/terminals/{id}/scan/facewt", enforced)
        self.assertRegex(enforced, r"캡처|캡쳐")
        siblings = rag_pipeline.sibling_api_paths_for_answer(extracted, weak)
        sibling_paths = {e["path"] for e in siblings}
        self.assertIn("/v1/terminals/{id}/scan/facewt", sibling_paths)

    def test_complete_related_api_endpoint_chunks_injects_scan(self):
        """선택 청크에 scan이 없으면 BM25 레코드에서 scan 엔드포인트를 주입해야 합니다."""
        query = (
            "alpeta swagger에서 FAW 또는 FaceWT 관련한 API와 스키마구조 알려줘"
        )
        selected = [
            {
                "source": "swagger_kr.md",
                "content": "## GET `/v1/users/{id}/faceWTInfo`\n- **요약**: 조회\n",
                "score": 1.0,
                "metadata": {
                    "source": "swagger_kr.md",
                    "section": "GET `/v1/users/{id}/faceWTInfo`",
                    "document_type": "api",
                },
            },
            {
                "source": "swagger_kr.md",
                "content": "### 스키마 `FaceWTInfo`\n| TemplateType | integer |\n",
                "score": 0.9,
                "metadata": {
                    "source": "swagger_kr.md",
                    "section": "스키마 `FaceWTInfo`",
                    "document_type": "api",
                },
            },
        ]
        records = [
            {
                "document": (
                    "## GET `/v1/terminals/{id}/scan/facewt`\n"
                    "- **요약**: 얼굴 이미지 캡쳐 (faceWt)\n"
                ),
                "metadata": {
                    "source": "swagger_kr.md",
                    "section": "GET `/v1/terminals/{id}/scan/facewt`",
                    "document_type": "api",
                },
            }
        ]
        completed = rag_pipeline.complete_related_api_endpoint_chunks(
            selected, records, query, top_k=4, scope={"document_type": "api"}
        )
        blob = "\n".join(d.get("content") or "" for d in completed).casefold()
        self.assertIn("scan/facewt", blob)

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
        """전부/목록 질문은 목록 의도로 분류되고 TOC/Preview만 카탈로그로 봅니다."""
        question = "v4.0 프로토콜 전부 리스트업해줘"
        listup = "v4.0 프로토콜 리스트업해줘"
        self.assertTrue(rag_pipeline.detect_list_completeness_intent(question))
        self.assertTrue(rag_pipeline.detect_list_completeness_intent(listup))
        self.assertTrue(rag_pipeline.is_protocol_command_list_intent(listup))
        catalog = (
            "4.1 Logon (0x0001) ..... 11\n"
            "4.2 Logoff (0x0002) ..... 13\n"
            "5.15 Access (0x010A) .... 59\n"
            "5.16 Init (0x010B) ...... 62\n"
            "5.17 Admin (0x010C) ..... 63\n"
            "5.18 Snapshot (0x0) ..... 64\n"
        )
        partial = "Command Preview 0x0001 0x0002 0x0108 0x0109"
        enum_page = (
            "Data Type 0x01 0x02 0x03 0x04 0x05 0x06 0x07 0x08 "
            "0x09 0x0A 0x0B 0x0C 0x0D 0x0F"
        )
        self.assertTrue(rag_pipeline.looks_like_command_catalog(catalog))
        self.assertTrue(rag_pipeline.is_command_list_catalog(partial))
        self.assertFalse(rag_pipeline.is_command_list_catalog(enum_page))
        self.assertGreater(
            rag_pipeline.technical_evidence_score(question, catalog),
            rag_pipeline.technical_evidence_score(question, enum_page),
        )
        prompt = rag_pipeline.build_context_prompt(
            question,
            [{"source": "protocol.pdf", "score": 1.0, "content": catalog}],
        )
        self.assertIn("목록 완결성", prompt)
        self.assertIn("0x00으로", prompt)

    def test_enforce_protocol_command_catalog_fills_missing_hex(self):
        """생성 답에 hex·스냅샷이 없거나 추정하면 문서 TOC/Preview로 보강합니다."""
        question = "v4.0 프로토콜 리스트업해줘"
        documents = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "3 Command Preview Command Value Content "
                    "인증 기록 가져오기 0x0016 "
                    "출입그룹 Door 설정 전송 0x010A "
                    "주장치 초기화 요청 0x010B "
                    "주장치 관리자 계정 설정 요청 0x010C "
                    "사용자 정보 전송 0x0100 "
                    "단말기 정보 요청 0x0101 "
                    "시간 동기화 0x0009 "
                ),
                "metadata": {},
            },
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "5.18 스냅샷 (주장치 설정 정보) 요청 (0x0) "
                    ".................................................. 64"
                ),
                "metadata": {"page": 4},
            },
        ]
        weak = "프로토콜 명령이 여러 개 있습니다. 출입그룹만 있습니다."
        enforced = rag_pipeline.enforce_protocol_command_catalog(
            question, documents, weak
        )
        self.assertIn("0x010A", enforced)
        self.assertIn("0x010B", enforced)
        self.assertIn("0x010C", enforced)
        self.assertIn("스냅샷", enforced)
        self.assertIn("0x0", enforced)
        self.assertNotRegex(enforced, r"(?i)varies or missing")

        guessed = (
            "출입그룹 0x010A 목록입니다. "
            "Snapshot request not mentioned in the provided document. "
            "스냅샷 hex는 추정이 불가능하며 [문서에 없음]."
        )
        enforced_guess = rag_pipeline.enforce_protocol_command_catalog(
            question, documents, guessed
        )
        self.assertIn("스냅샷", enforced_guess)
        self.assertNotRegex(enforced_guess, r"추정이 불가능")
        self.assertNotRegex(enforced_guess, r"문서에 없음")
        self.assertNotRegex(enforced_guess, r"(?i)not mentioned")
        self.assertFalse(
            rag_pipeline.answer_has_protocol_guess_phrases(enforced_guess)
        )

    def test_protocol_detail_token_extraction_hex_and_command_name(self):
        """hex·명령명 질의 토큰 추출이 하드코딩 분기 없이 핵심을 공유하는지 검증합니다."""
        hex_q = "v4.0에서 0x0041 알려줘"
        name_q = "v4.0에서 set Wiegand 알려줘"
        name_q_case = "v4.0에서 Set Wiegand 알려줘"
        hex_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(hex_q)}
        name_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(name_q)}
        name_tokens_case = {
            t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(name_q_case)
        }
        # 대소문자 변형은 동일 핵심 토큰을 내야 합니다.
        self.assertEqual(name_tokens, name_tokens_case)
        self.assertTrue(any("wiegand" in t for t in name_tokens))
        self.assertTrue(
            any(t.replace(" ", "") == "setwiegand" or t == "set wiegand" for t in name_tokens)
        )
        self.assertTrue(any(t in {"0x0041", "0x41", "0041", "41"} for t in hex_tokens))
        # 두 질문 모두 단건 상세 intent이며 목록 intent가 아닙니다.
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(hex_q))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(name_q))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(name_q_case))
        self.assertFalse(rag_pipeline.is_protocol_command_list_intent(name_q))
        # 표현별 하드코딩 분기 문자열이 추출기 소스에 없어야 합니다.
        src = Path(rag_pipeline.__file__).read_text(encoding="utf-8")
        self.assertNotIn('if "set wiegand" in', src.casefold())
        self.assertNotIn("if 'set wiegand' in", src.casefold())

    def test_protocol_logon_synonym_tokens_and_intent(self):
        """logon/로그인 동의어가 토큰·단건 intent로 잡혀 목록 enforce와 분리됩니다."""
        en_q = "v4.0 logon 프로토콜 알려줘"
        ko_q = "v4.0 단말기 로그인 프로토콜 알려줘"
        en_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(en_q)}
        ko_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(ko_q)}
        self.assertTrue(any("logon" in t for t in en_tokens))
        self.assertTrue(any(t == "0x0001" or t == "0x1" for t in en_tokens))
        self.assertTrue(any("logon" in t for t in ko_tokens))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(en_q))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(ko_q))
        self.assertFalse(rag_pipeline.is_protocol_command_list_intent(en_q))
        self.assertFalse(rag_pipeline.is_protocol_command_list_intent(ko_q))
        docs = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "4.1 Terminal Logon 단말기 로그온 (0x0001)\n"
                    "단말은 서버로 Logon을 시도한다.\n"
                    "Request ] (Server <- Terminal)\n"
                    "Command 0x0001 Param1 Terminal IP\n"
                ),
                "metadata": {"page": 11, "chunk_index": 20},
            }
        ]
        weak = "제공된 문서에는 로그인 절차가 없습니다. Overview 포트는 9003입니다."
        enforced = rag_pipeline.enforce_protocol_hex_detail(en_q, docs, weak)
        self.assertIn("0x0001", enforced)
        self.assertRegex(enforced, r"(?i)logon")
        self.assertNotRegex(enforced, r"로그인\s*절차가\s*없")

    def test_protocol_wiegand_synonym_tokens_and_struct_enforce(self):
        """위겐드/wiegand 동의어 intent·검색 토큰과 Config 필드 강제 보강을 검증합니다."""
        ko_q = "v4.0에서 위겐드 설정하는 프로토콜 알려줘"
        en_q = "v4.0에서 wiegand 설정하는 프로토콜 알려줘"
        plain_q = "v4.0에서 set wiegand 알려줘"
        ko_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(ko_q)}
        en_tokens = {t.casefold() for t in rag_pipeline.extract_protocol_detail_tokens(en_q)}
        self.assertTrue(any("wiegand" in t for t in ko_tokens))
        self.assertTrue(any(t in {"0x0041", "0x41"} for t in ko_tokens))
        self.assertTrue(any("wiegand" in t for t in en_tokens))
        self.assertTrue(any(t in {"0x0041", "0x41"} for t in en_tokens))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(ko_q))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(en_q))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(plain_q))
        self.assertFalse(rag_pipeline.is_protocol_command_list_intent(ko_q))
        docs = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "5.19 Set Wiegand (0x0041)\n"
                    "서버에서 단말로 Wiegand 정보를 얻거나 설정할 경우 사용한다.\n"
                    "Command 0x0041 Param1 사용안함 Param2 사용안함\n"
                    "ControlBase의 경우 WiegandConfig가 함께 전달된다.\n"
                    "WiegandConfig\n"
                    "Base device_type rs485_port device_cp_id\n"
                    "base 0: ControlBase\n"
                    "device_type 5: Wiegand\n"
                ),
                "metadata": {"page": 65, "chunk_index": 158},
            }
        ]
        denial = "제공된 문서에는 위겐드 설정 관련 프로토콜이 없습니다."
        enforced_ko = rag_pipeline.enforce_protocol_hex_detail(ko_q, docs, denial)
        self.assertIn("0x0041", enforced_ko)
        self.assertRegex(enforced_ko, r"(?i)set\s*wiegand|wiegand")
        self.assertRegex(enforced_ko, r"(?i)wiegandconfig|device_type")
        self.assertNotRegex(enforced_ko, r"프로토콜이\s*없")
        # Config 이름만 있고 필드 없는 부분 답은 base/device_type을 붙입니다.
        partial = "Set Wiegand(0x0041)는 Param1·Param2 사용안함이며 WiegandConfig를 전달합니다."
        enforced_plain = rag_pipeline.enforce_protocol_hex_detail(plain_q, docs, partial)
        self.assertIn("0x0041", enforced_plain)
        self.assertRegex(enforced_plain, r"(?i)\bbase\b")
        self.assertRegex(enforced_plain, r"(?i)device_type")
        src = Path(rag_pipeline.__file__).read_text(encoding="utf-8")
        self.assertNotIn('if "위겐드" in', src)
        self.assertNotIn("if 'wiegand' in query", src.casefold())

    def test_protocol_listup_spaced_and_table_followup_topic(self):
        """공백 리스트업·표 후속이 protocol_catalog로 문맥화되고 MediaServer로 가지 않습니다."""
        list_q = "v4.0 프로토콜 리스트업 해줘"
        list_q_nospace = "v4.0 프로토콜 리스트업해줘"
        self.assertNotEqual(list_q, list_q_nospace)
        self.assertTrue(rag_pipeline.is_protocol_command_list_intent(list_q))
        follow_up = "보기 좋게 표로 정리해줘"
        history = [
            {"role": "user", "content": list_q},
            {"role": "assistant", "content": "명령 일부: 0x010A 출입그룹"},
        ]
        self.assertEqual(
            rag_pipeline.recent_user_follow_up_topic(history), "protocol_catalog"
        )
        ruled = rag_pipeline.rule_contextualize_follow_up(follow_up, history)
        self.assertIsNotNone(ruled)
        self.assertTrue(rag_pipeline.is_protocol_command_list_intent(ruled))
        self.assertTrue(rag_pipeline.query_has_retrieval_topic(ruled))
        self.assertFalse(
            rag_pipeline.is_ambiguous_reformat_request(follow_up, history)
        )
        self.assertNotIn("미디어 서버", ruled)
        self.assertNotIn("MediaServer", ruled or "")
        degraded = (
            "主张 请求 Termainl 스냅썸트\n"
            "| 보완 항목 | 0x00 |\n"
            "출입그룹 0x010A만 있습니다."
        )
        documents = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "3 Command Preview Command Value Content "
                    "Terminal Logon 0x0001 "
                    "출입그룹 Door 설정 전송 0x010A "
                    "주장치 초기화 요청 0x010B "
                    "주장치 관리자 계정 설정 요청 0x010C "
                    "5.18 스냅샷 (주장치 설정 정보) 요청 (0x0)"
                ),
                "metadata": {"catalog_page": True},
            }
        ]
        enforced = rag_pipeline.enforce_protocol_command_catalog(
            list_q, documents, degraded
        )
        self.assertIn("0x0001", enforced)
        self.assertIn("0x010A", enforced)
        self.assertIn("스냅샷", enforced)
        self.assertIn("|", enforced)
        self.assertNotIn("主张", enforced)
        self.assertNotIn("보완 항목", enforced)
        self.assertNotIn("MediaServer", enforced)

    def test_protocol_hex_detail_intent_and_enforce(self):
        """단건 hex/명령명 질의는 목록 enforce를 피하고 섹션·Config 요약을 강제합니다."""
        question = "v4.0에서 0x0041 알려줘"
        name_q = "v4.0에서 set Wiegand 알려줘"
        listup = "v4.0 프로토콜 리스트업해줘"
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(question))
        self.assertTrue(rag_pipeline.is_protocol_hex_detail_intent(name_q))
        self.assertFalse(rag_pipeline.is_protocol_command_list_intent(question))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(listup))
        variants = rag_pipeline.hex_code_variants("0x0041")
        # 변형에 짧은 표기 0x41이 포함되는지 확인합니다.
        self.assertTrue(any(v.lower() == "0x41" for v in variants))
        expanded = rag_pipeline.expand_retrieval_query(question, "")
        self.assertIn("0x0041", expanded)
        self.assertIn("0x41", expanded.casefold())
        expanded_name = rag_pipeline.expand_retrieval_query(name_q, "")
        self.assertRegex(expanded_name, r"(?i)wiegand")
        scope = rag_pipeline.detect_retrieval_scope(question)
        self.assertEqual(scope.get("document_type"), "protocol")
        self.assertEqual(scope.get("protocol_generation"), "current")
        scope_name = rag_pipeline.detect_retrieval_scope(name_q)
        self.assertEqual(scope_name.get("document_type"), "protocol")
        docs = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "5.19 Set Wiegand (0x0041)\n"
                    "서버에서 단말로 Wiegand 정보를 얻거나 설정할 경우 사용한다.\n"
                    "Request ] (Server -> Terminal)\n"
                    "Command   0x0041\n"
                    "일반 단말의 경우 WiegandFormat만 전달되며, "
                    "ControlBase의 경우 WiegandConfig가 함께 전달된다.\n"
                    "WiegandConfig Base device_type rs485_port device_cp_id\n"
                ),
                "metadata": {
                    "page": 65,
                    "section": "5.19 Set Wiegand (0x0041)",
                    "chunk_index": 158,
                },
            }
        ]
        weak = "제공된 참고 문서에는 0x0041 관련 표가 포함되어 있지 않습니다. Time Stamp는 ms 8bytes입니다."
        enforced = rag_pipeline.enforce_protocol_hex_detail(question, docs, weak)
        self.assertIn("0x0041", enforced)
        self.assertRegex(enforced, r"(?i)wiegand")
        self.assertRegex(enforced, r"(?i)wiegandconfig|device_type")
        self.assertNotRegex(enforced, r"포함되어\s*있지\s*않")
        # 명령명 질의도 동일 문서 요약을 강제합니다.
        partial = "Set Wiegand(0x0041)는 Param3로 얻거나 설정합니다."
        enforced_name = rag_pipeline.enforce_protocol_hex_detail(name_q, docs, partial)
        self.assertRegex(enforced_name, r"(?i)wiegandconfig|device_type")
        # 목록 enforce가 단건을 표로 덮지 않는지
        cataloged = rag_pipeline.enforce_protocol_command_catalog(question, docs, weak)
        self.assertEqual(cataloged, weak)

    def test_complete_hex_detail_context_injects_section(self):
        """RRF 상위가 TimeStamp여도 BM25에서 절·인접 Config 청크를 주입합니다."""
        query = "v4.0에서 0x0041 알려줘"
        selected = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": "Time Stamp Milliseconds(ms) 8 bytes",
                "score": 0.04,
                "metadata": {
                    "page": 25,
                    "chunk_index": 53,
                    "document_type": "protocol",
                    "protocol_generation": "current",
                },
            }
        ]
        records = [
            {
                "document": selected[0]["content"],
                "metadata": selected[0]["metadata"] | {"source": selected[0]["source"]},
            },
            {
                "document": (
                    "5.19 Set Wiegand (0x0041) 서버에서 단말로 Wiegand 정보를 얻거나 설정. "
                    "WiegandConfig Base device_type rs485_port"
                ),
                "metadata": {
                    "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                    "page": 65,
                    "chunk_index": 158,
                    "section": "5.19 Set Wiegand (0x0041)",
                    "document_type": "protocol",
                    "protocol_generation": "current",
                },
            },
            {
                "document": "| WiegandConfig | Base | device type | rs485 port |",
                "metadata": {
                    "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                    "page": 65,
                    "chunk_index": 160,
                    "section": "5.19 Set Wiegand (0x0041)",
                    "document_type": "protocol",
                    "protocol_generation": "current",
                },
            },
        ]
        completed = rag_pipeline.complete_hex_detail_context(
            selected, records, query, top_k=2, scope={"document_type": "protocol"}
        )
        blob = "\n".join(doc.get("content") or "" for doc in completed)
        self.assertIn("0x0041", blob)
        self.assertRegex(blob, r"(?i)wiegand")
        self.assertRegex(blob, r"(?i)wiegandconfig")
        # 명령명 질의도 동일 절을 끌어옵니다.
        completed_name = rag_pipeline.complete_hex_detail_context(
            selected,
            records,
            "v4.0에서 set Wiegand 알려줘",
            top_k=2,
            scope={"document_type": "protocol"},
        )
        blob_name = "\n".join(doc.get("content") or "" for doc in completed_name)
        self.assertRegex(blob_name, r"(?i)0x0041|wiegandconfig")


    def test_ensure_protocol_golden_hex_rows_fills_010c(self):
        """extract가 0x010C를 빠뜨려도 문서 blob에 있으면 보강합니다."""
        documents = [
            {
                "source": "Communication protocol for Terminal v4.0_Re19.pdf",
                "content": (
                    "출입그룹 Door 설정 전송 0x010A "
                    "주장치 초기화 요청 0x010B "
                    "주장치 관리자 계정 설정 요청 0x010C "
                    "5.18 스냅샷 (주장치 설정 정보) 요청 (0x0)"
                ),
                "metadata": {},
            }
        ]
        # catalog로 안 잡혀도 출입그룹 청크에서 Preview hex를 뽑는지 확인합니다.
        rows = rag_pipeline.extract_protocol_command_rows(documents)
        codes = {code.upper() for _, code in rows}
        self.assertIn("0X010A", codes)
        self.assertIn("0X010C", codes)
        ensured = rag_pipeline.ensure_protocol_golden_hex_rows(documents, rows[:1])
        ensured_codes = {code.upper() for _, code in ensured}
        self.assertIn("0X010B", ensured_codes)
        self.assertIn("0X010C", ensured_codes)
        self.assertTrue(any("스냅샷" in name for name, _ in ensured))

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
        self.assertIn("서로 다른 메뉴 3경로", prompt)
        self.assertIn("「사용자 관리」", prompt)
        self.assertIn("「단말기 사용자 확장」", prompt)
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

    def test_user_terminal_prompt_requires_three_path_split_and_caution_enumeration(self):
        """사용자·단말기 절차 지침이 수동 3경로 메뉴 구분과 주의사항 나열을 요구합니다."""
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
        self.assertIn("서로 다른 메뉴 3경로", prompt)
        self.assertIn("「사용자 관리」", prompt)
        self.assertIn("「단말기 사용자 관리」", prompt)
        self.assertIn("「단말기 사용자 확장」", prompt)
        self.assertIn("표기 고정", prompt)
        self.assertIn("`출입그룹 단말기 리스트`", prompt)
        self.assertIn("`등록된 단말기`", prompt)
        self.assertIn("`추가가능한 단말기`", prompt)
        self.assertIn("[주의사항]", prompt)
        self.assertIn("단말기 사용자 정보 자동 동기화 사용", prompt)

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

    def test_procedure_context_completes_three_manual_path_facets(self):
        """수동 추가 3경로(확장 포함) 청크가 빠지면 같은 가이드에서 보충합니다."""
        question = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
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
                    "사용자 관리에서 [단말기리스트]를 클릭하면 출입그룹 단말기 리스트, "
                    "등록된 단말기, 추가가능한 단말기를 확인할 수 있습니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
            {
                "document": (
                    "단말기 사용자 관리의 단말기 사용자 리스트에서 추가 후 > 와 "
                    "[적용]으로 단말 전송합니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
            {
                "document": (
                    "단말기 사용자 확장에서 N:N으로 전송하고 작업리스트로 진행을 확인합니다."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
            {
                "document": (
                    "단말기 사용자 정보 자동 동기화 사용. 동일한 출입그룹, 덮어쓰기."
                ),
                "metadata": {"source": "Alpeta User Guide.pdf", "document_type": "user_guide"},
            },
        ]
        completed = rag_pipeline.complete_procedure_context(
            selected,
            records,
            question,
            top_k=8,
            scope={"document_type": "user_guide"},
        )
        joined = "\n".join(document["content"] for document in completed)
        self.assertIn("단말기리스트", joined)
        self.assertIn("단말기 사용자 관리", joined)
        self.assertIn("단말기 사용자 확장", joined)
        self.assertIn("자동 동기화", joined)

    def test_enforce_three_paths_appends_missing_menu_names(self):
        """3경로 근거가 있는데 메뉴명이 빠진 답변을 문서 사실로 보강합니다."""
        question = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        documents = [
            {
                "content": (
                    "사용자 관리 [단말기리스트] 출입그룹 단말기 리스트. "
                    "단말기 사용자 관리 단말기 사용자 리스트 추가 적용 전송. "
                    "단말기 사용자 확장 N:N 전송 작업리스트. "
                    "단말기 사용자 정보 자동 동기화 사용 동일한 출입그룹 덮어쓰기."
                )
            }
        ]
        incomplete = "사용자를 단말기에 추가하고 자동 동기화할 수 있습니다."
        completed = rag_pipeline.enforce_document_term_pairs(
            question, documents, incomplete
        )
        self.assertTrue(rag_pipeline._has_standalone_user_management_menu(completed))
        self.assertIn("단말기 사용자 관리", completed)
        self.assertIn("단말기 사용자 확장", completed)
        self.assertIn("단말기 사용자 정보 자동 동기화", completed)


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

    def test_enforce_adds_menu_name_when_missing(self):
        """생성 답변에 메뉴명이 없으면 문서 근거가 있을 때 보강합니다."""
        documents = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": (
                    "단말기 사용자 관리 단말기에 등록된 사용자 정보를 삭제. "
                    "가져오기와 업로드가 있습니다."
                ),
            }
        ]
        completed = rag_pipeline.enforce_document_term_pairs(
            self.QUESTION,
            documents,
            "- 추가 후 적용하여 전송합니다.",
        )
        self.assertIn("단말기 사용자 관리", completed)
        self.assertIn("가져오기", completed)
        self.assertIn("업로드", completed)

    def test_rerank_neural_false_skips_cross_encoder(self):
        """RERANK_NEURAL=false면 크로스인코더를 호출하지 않습니다."""
        documents = [
            {"source": "a.pdf", "content": "단말기 사용자 관리 가져오기 업로드", "score": 0.5},
            {"source": "b.pdf", "content": "일반 텍스트", "score": 0.9},
        ]
        with patch.object(rag_pipeline, "_get_reranker") as get_reranker:
            ranked = rag_pipeline.rerank_documents(
                self.QUESTION,
                documents,
                "fake-model",
                top_k=2,
                use_neural=False,
            )
            get_reranker.assert_not_called()
        self.assertEqual(len(ranked), 2)


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

    def test_spec_table_follow_up_marker_and_rule_contextualize(self):
        """미디어 서버 스펙 주제의 표 후속만 MediaServer 전체 표 질문으로 고정됩니다."""
        history = [
            {"role": "user", "content": "미디어 서버 스펙 알려줘"},
            {"role": "assistant", "content": "MediaServer_Specs_New.md 표를 참고하세요."},
        ]
        self.assertTrue(rag_pipeline.is_follow_up_question("스펙을 표로 알려줘", history))
        # 미디어 서버+스펙이 이미 있으면 후속 문맥화가 필요 없는 독립 질문입니다.
        self.assertFalse(
            rag_pipeline.is_follow_up_question("미디어 서버 스펙을 표로 알려줘", history)
        )
        ruled = rag_pipeline.rule_contextualize_follow_up("스펙을 표로 알려줘", history)
        self.assertIn("미디어 서버", ruled)
        self.assertIn("전체 표", ruled)
        with patch.object(rag_pipeline, "ollama_chat") as mocked:
            condensed = rag_pipeline.condense_question(
                "http://ollama", "model", "스펙을 표로 알려줘", history,
            )
            mocked.assert_not_called()
        self.assertEqual(condensed, ruled)

    def test_monitor_status_table_follow_up_not_mediaserver(self):
        """모니터링 연결상태 후 「표로」후속은 녹·적·이벤트 표로 문맥화됩니다."""
        history = [
            {"role": "user", "content": "alpeta 단말기 연결 상태는 어떻게 확인해?"},
            {"role": "assistant", "content": "모니터링 메뉴에서 확인합니다."},
        ]
        follow = "상태에 대한 정보를 포함해서 표로 정리해서 보여줘"
        self.assertEqual(rag_pipeline.recent_user_follow_up_topic(history), "terminal_monitor")
        ruled = rag_pipeline.rule_contextualize_follow_up(follow, history)
        self.assertIsNotNone(ruled)
        self.assertIn("모니터링", ruled or "")
        self.assertIn("녹", ruled or "")
        self.assertNotIn("FaceWT", ruled or "")
        self.assertNotIn("카메라", ruled or "")

    def test_mediaserver_solo_spec_not_follow_up_or_api_hijack(self):
        """「미디어서버 스펙 알려줘」는 len<=12여도 UG/FaceWT history 후속으로 오탐되지 않습니다."""
        question = "미디어서버 스펙 알려줘"
        self.assertEqual(len(question), 12)
        self.assertTrue(rag_pipeline.is_media_server_spec_intent(question))
        ug_history = [
            {
                "role": "user",
                "content": "사용자를 단말기에 수동으로 넣는 방법과 자동동기화 알려줘",
            },
            {
                "role": "assistant",
                "content": "Alpeta User Guide.pdf 기준 수동 3경로와 자동동기화가 있습니다.",
            },
        ]
        facewt_history = [
            {
                "role": "user",
                "content": (
                    "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
                    "스키마 구조와 사용하는 API 명세 줘"
                ),
            },
            {
                "role": "assistant",
                "content": "swagger_kr.md의 FaceWTInfo 스키마를 참고하세요.",
            },
        ]
        self.assertFalse(rag_pipeline.is_follow_up_question(question, ug_history))
        self.assertFalse(rag_pipeline.is_follow_up_question(question, facewt_history))
        self.assertIsNone(
            rag_pipeline.rule_contextualize_follow_up(question, facewt_history)
        )
        self.assertIsNone(
            rag_pipeline.rule_contextualize_follow_up(question, ug_history)
        )

    def test_facewt_schema_table_follow_up_not_mediaserver(self):
        """FaceWT/스키마 후속 「표로」는 스키마 표로 문맥화되고 MediaServer로 고정되지 않습니다."""
        follow_up = "스키마 구조는 표로 해서 읽기 쉽게 다시 알려줘"
        history = [
            {
                "role": "user",
                "content": (
                    "alpeta swagger에서 FAW 또는 FaceWT 관련한 "
                    "스키마 구조와 사용하는 API 명세 줘"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "swagger_kr.md의 FaceWTInfo 스키마와 "
                    "/v1/users/{id}/faceWTInfo API를 참고하세요."
                ),
            },
        ]
        self.assertTrue(rag_pipeline.is_follow_up_question(follow_up, history))
        self.assertEqual(rag_pipeline.recent_user_follow_up_topic(history), "api")
        ruled = rag_pipeline.rule_contextualize_follow_up(follow_up, history)
        self.assertIsNotNone(ruled)
        self.assertIn("FaceWT", ruled)
        self.assertIn("스키마", ruled)
        self.assertIn("표로", ruled)
        self.assertIn("FaceWTInfo", ruled)
        self.assertNotIn("미디어 서버", ruled)
        self.assertFalse(rag_pipeline.is_media_server_spec_intent(ruled))
        self.assertTrue(rag_pipeline.detect_api_doc_intent(ruled))
        with patch.object(rag_pipeline, "ollama_chat") as mocked:
            condensed = rag_pipeline.condense_question(
                "http://ollama", "model", follow_up, history,
            )
            mocked.assert_not_called()
        self.assertEqual(condensed, ruled)

    def test_table_follow_up_prefers_api_topic_over_incidental_media(self):
        """히스토리에 media 문자열이 섞여도 최근 API 주제면 MediaServer로 고정하지 않습니다."""
        follow_up = "스키마 구조는 표로 해서 읽기 쉽게 다시 알려줘"
        history = [
            {
                "role": "user",
                "content": "alpeta swagger에서 FaceWT 스키마 구조와 API 명세 줘",
            },
            {
                "role": "assistant",
                "content": (
                    "FaceWTInfo 스키마입니다. (참고: MediaServer 스트림 API와는 별개)"
                ),
            },
        ]
        ruled = rag_pipeline.rule_contextualize_follow_up(follow_up, history)
        self.assertIsNotNone(ruled)
        self.assertIn("스키마", ruled)
        self.assertNotIn("미디어 서버", ruled)
        self.assertFalse(rag_pipeline.is_media_server_spec_intent(ruled))

    def test_bare_table_marker_alone_does_not_force_mediaserver(self):
        """「표로」단독은 MediaServer를 강제하지 않고, 주제 없으면 확인 요청 대상입니다."""
        self.assertIsNone(
            rag_pipeline.rule_contextualize_follow_up("표로 알려줘", [])
        )
        self.assertTrue(
            rag_pipeline.is_ambiguous_reformat_request("표로 알려줘", [])
        )
        history = [
            {"role": "user", "content": "출입그룹 등록 방법 알려줘"},
            {"role": "assistant", "content": "User Guide를 참고하세요."},
        ]
        self.assertEqual(
            rag_pipeline.recent_user_follow_up_topic(history), "general"
        )
        ruled = rag_pipeline.rule_contextualize_follow_up("표로 알려줘", history)
        self.assertIsNotNone(ruled)
        self.assertIn("출입그룹", ruled)
        self.assertNotIn("미디어 서버", ruled)
        self.assertFalse(
            rag_pipeline.is_ambiguous_reformat_request("표로 알려줘", history)
        )

    def test_nsis_autobuild_reformat_follow_up_contextualize(self):
        """자동빌드 대화 후 정리/표 후속은 NSIS 자동화 절차 질문으로 문맥화됩니다."""
        follow_up = "알아보기 편하게 정리해서 적어줘 표도 활용하고"
        history = [
            {
                "role": "user",
                "content": "alpeta 자동빌드하려면 어떻게 하면돼?",
            },
            {
                "role": "assistant",
                "content": (
                    "NSIS 매뉴얼 자동화 버전: gitpull.bat, define.go, "
                    "alpeta.nsi, build_install.bat, D:\\nsis\\install 순입니다."
                ),
            },
        ]
        self.assertTrue(rag_pipeline.is_reformat_follow_up_intent(follow_up))
        self.assertTrue(rag_pipeline.is_follow_up_question(follow_up, history))
        self.assertEqual(
            rag_pipeline.recent_user_follow_up_topic(history), "automated_build"
        )
        self.assertFalse(
            rag_pipeline.is_ambiguous_reformat_request(follow_up, history)
        )
        ruled = rag_pipeline.rule_contextualize_follow_up(follow_up, history)
        self.assertIsNotNone(ruled)
        self.assertIn("자동빌드", ruled)
        self.assertIn("자동화", ruled)
        self.assertIn("표", ruled)
        self.assertTrue(rag_pipeline.is_automated_build_intent(ruled))
        self.assertNotIn("미디어 서버", ruled)
        with patch.object(rag_pipeline, "ollama_chat") as mocked:
            condensed = rag_pipeline.condense_question(
                "http://ollama", "model", follow_up, history,
            )
            mocked.assert_not_called()
        self.assertEqual(condensed, ruled)

    def test_nsis_table_pyoreul_hwalyong_follow_up_markers(self):
        """「표를 활용해서 더 보기 쉽게」후속은 마커로 follow-up·NSIS 문맥화됩니다."""
        follow_up = "표를 활용해서 더 보기 쉽게 해줘"
        history = [
            {
                "role": "user",
                "content": "alpeta 자동빌드하려면 어떻게 하면돼?",
            },
            {
                "role": "assistant",
                "content": (
                    "NSIS 자동화: gitpull.bat, define.go, build_install.bat, "
                    "D:\\nsis\\install"
                ),
            },
        ]
        self.assertIn("표를 활용", follow_up)
        self.assertIn("보기 쉽게", follow_up)
        self.assertNotIn("표 활용", follow_up)
        self.assertNotIn("읽기 쉽게", follow_up)
        self.assertTrue(rag_pipeline.is_reformat_follow_up_intent(follow_up))
        self.assertTrue(rag_pipeline.is_follow_up_question(follow_up, history))
        self.assertEqual(
            rag_pipeline.recent_user_follow_up_topic(history), "automated_build"
        )
        self.assertFalse(
            rag_pipeline.is_ambiguous_reformat_request(follow_up, history)
        )
        ruled = rag_pipeline.rule_contextualize_follow_up(follow_up, history)
        self.assertIsNotNone(ruled)
        self.assertIn("자동빌드", ruled)
        self.assertTrue(rag_pipeline.is_automated_build_intent(ruled))
        self.assertNotIn("미디어 서버", ruled)

    def test_ambiguous_reformat_no_history_needs_clarification(self):
        """history 없는 정리/표 후속은 주제 불명으로 확인 요청 대상입니다."""
        follow_up = "알아보기 편하게 정리해서 적어줘 표도 활용하고"
        self.assertTrue(rag_pipeline.is_reformat_follow_up_intent(follow_up))
        self.assertTrue(
            rag_pipeline.is_ambiguous_reformat_request(follow_up, [])
        )
        self.assertFalse(rag_pipeline.is_follow_up_question(follow_up, []))
        self.assertIsNone(
            rag_pipeline.rule_contextualize_follow_up(follow_up, [])
        )
        similar = "표로 정리해줘"
        self.assertTrue(rag_pipeline.is_ambiguous_reformat_request(similar, []))

    def test_person_profile_question_is_not_follow_up(self):
        """인물 질문은 짧아도 이전 스펙 대화의 후속으로 오인하지 않습니다."""
        history = [
            {"role": "user", "content": "미디어 서버 스펙 알려줘"},
            {"role": "assistant", "content": "48GB 권장"},
        ]
        self.assertFalse(
            rag_pipeline.is_follow_up_question("박준언에 대해 알려줘", history)
        )


class MediaServerAndPersonIntentTests(unittest.TestCase):
    """미디어 서버 표·인물 프로필 의도/보강 회귀."""

    def test_media_server_spec_intent_and_not_api_scope(self):
        """미디어 서버 스펙 표 질문은 API 스코프로 오분류되지 않습니다."""
        question = "미디어 서버 카메라 대수별 권장 스펙 전체 표로 알려줘"
        self.assertTrue(rag_pipeline.is_media_server_spec_intent(question))
        self.assertTrue(rag_pipeline.detect_list_completeness_intent(question))
        self.assertFalse(rag_pipeline.detect_api_doc_intent(question))
        self.assertEqual(rag_pipeline.detect_retrieval_scope(question), {})

    def test_api_schema_table_expansion_skips_protocol_toc(self):
        """API 스키마 표 질문은 프로토콜 목차 확장이 아니라 스키마 필드 확장을 씁니다."""
        query = (
            "FaceWT/FAW 스키마 FaceWTInfo TemplateType TemplateData "
            "필드 구조를 마크다운 표로 읽기 쉽게 다시 알려줘"
        )
        self.assertTrue(rag_pipeline.is_api_schema_table_intent(query))
        expanded = rag_pipeline.expand_retrieval_query(query, query)
        self.assertIn("FaceWTInfo", expanded)
        self.assertIn("TemplateType", expanded)
        self.assertNotIn("Command Preview", expanded)
        self.assertNotIn("프로토콜 명령", expanded)
        self.assertFalse(rag_pipeline.is_media_server_spec_intent(query))

    def test_bare_api_term_still_detects_explicit_api_questions(self):
        """명시적 API 질문은 단독 api 토큰 없이도 감지됩니다."""
        self.assertTrue(
            rag_pipeline.detect_api_doc_intent("미디어서버에 스트림 추가하는 API 알려줘")
        )
        self.assertTrue(
            rag_pipeline.detect_api_doc_intent("얼굴 정보 조회 API의 응답 스키마 구조 알려줘")
        )

    def test_enforce_mediaserver_table_appends_missing_ranges(self):
        """일부 구간만 있는 답변에 문서 표가 보강됩니다."""
        context = (
            "| 카메라(스트림) 수 | CPU 권장 | RAM 권장 | 네트워크 권장 | HDD 권장(30일) |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| 10 ~ 24 | 6코어 | 16GB | 1Gbps | 4TB |\n"
            "| 25 ~ 49 | 8코어 | 32GB | 2.5Gbps | 6TB |\n"
            "| 50 ~ 79 | 12코어 | 48GB | 2.5Gbps | 8TB |\n"
            "| 80 ~ 100 | 16코어 | 64GB | 2.5Gbps+ | 12TB |\n"
        )
        docs = [{"source": "MediaServer_Specs_New.md", "content": context, "score": 1.0}]
        answer = "- 10~24: 16GB\n- 50~79: 48GB"
        enforced = rag_pipeline.enforce_mediaserver_spec_table(
            "미디어 서버 스펙을 표로 알려줘", docs, answer
        )
        self.assertIn("25 ~ 49", enforced)
        self.assertIn("80 ~ 100", enforced)
        self.assertIn("64GB", enforced)

    def test_person_profile_intent_and_prompt_keeps_name(self):
        """박준언 질문은 프로필 의도이며 프롬프트에 이름 보존 지침이 있습니다."""
        question = "박준언에 대해 알려줘"
        self.assertTrue(rag_pipeline.is_person_profile_intent(question))
        self.assertEqual(rag_pipeline.extract_query_focus(question), "박준언")
        self.assertEqual(rag_pipeline.extract_person_names(question), ["박준언"])
        prompt = rag_pipeline.build_context_prompt(
            question,
            [{
                "source": "Test.md",
                "score": 1.0,
                "content": "## 박준언\n- SW1팀 연동파트\n- 1994년생\n",
            }],
            focus="박준언",
        )
        self.assertIn("인물 프로필", prompt)
        self.assertIn("박준언", prompt)
        self.assertIn("박준연", prompt)  # 오타 금지 안내 문구

    def test_multi_person_profile_names_complete_and_filter(self):
        """복수 인물 질문은 두 이름을 모두 의도·주입·필터·프롬프트에 반영합니다."""
        question = "박준언, 방인재에 대해 알려줘"
        self.assertEqual(
            rag_pipeline.extract_query_focus(question), "박준언, 방인재"
        )
        self.assertEqual(
            rag_pipeline.extract_person_names(question),
            ["박준언", "방인재"],
        )
        self.assertTrue(rag_pipeline.is_person_profile_intent(question))
        selected = [{
            "source": "MediaServer_Specs_New.md",
            "content": "카메라(스트림) 수 10 ~ 24 48GB",
            "score": 0.2,
            "metadata": {"source": "MediaServer_Specs_New.md"},
        }]
        records = [
            {
                "document": "## 박준언\n- SW1팀 연동파트 - 1994년생\n",
                "metadata": {"source": "Test.md"},
            },
            {
                "document": "## 방인재\n- SW1팀 코어파트 - 1996년생 - 헬스\n",
                "metadata": {"source": "Test.md"},
            },
        ]
        completed = rag_pipeline.complete_person_profile_context(
            selected, records, question, top_k=4
        )
        contents = "\n".join(d.get("content") or "" for d in completed)
        self.assertIn("박준언", contents)
        self.assertIn("방인재", contents)
        self.assertIn("1994", contents)
        self.assertIn("1996", contents)
        filtered = rag_pipeline.filter_documents_by_focus(
            completed,
            "박준언, 방인재",
            top_k=4,
            person_names=["박준언", "방인재"],
        )
        filtered_body = "\n".join(d.get("content") or "" for d in filtered)
        self.assertIn("박준언", filtered_body)
        self.assertIn("방인재", filtered_body)
        self.assertNotIn("카메라(스트림)", filtered_body)
        prompt = rag_pipeline.build_context_prompt(
            question, filtered, focus="박준언, 방인재"
        )
        self.assertIn("박준언", prompt)
        self.assertIn("방인재", prompt)
        self.assertIn("모두", prompt)
        self.assertIn("없다", prompt)

    def test_person_profile_complete_injects_named_chunk(self):
        """top-k에 이름이 없어도 records에서 프로필 청크를 주입합니다."""
        selected = [{
            "source": "swagger_kr.md",
            "content": "POST /v1/tna/setting/payment",
            "score": 0.1,
            "metadata": {"source": "swagger_kr.md"},
        }]
        records = [{
            "document": "## 박준언\n- 1994년생\n",
            "metadata": {"source": "Test.md"},
        }]
        completed = rag_pipeline.complete_person_profile_context(
            selected, records, "박준언에 대해 알려줘", top_k=4
        )
        self.assertTrue(any(d.get("source") == "Test.md" for d in completed))
        self.assertTrue(any("1994" in (d.get("content") or "") for d in completed))


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


class TerminalMonitorAndAddIntentTests(unittest.TestCase):
    """단말기 연결상태(모니터링)·단말기 추가(단말기 관리) 의도 회귀."""

    QUESTION = (
        "alpeta 단말기 연결 상태는 어떻게 확인해? 그리고 단말기 어떻게 추가해?"
    )

    def test_intent_detects_monitor_add_and_excludes_user_paths(self):
        """신규 질문은 monitor/add 의도이고 3경로·tum과 겹치지 않습니다."""
        self.assertTrue(rag_pipeline.is_terminal_monitor_and_add_intent(self.QUESTION))
        self.assertFalse(rag_pipeline.is_user_terminal_procedure_intent(self.QUESTION))
        self.assertFalse(rag_pipeline.is_terminal_user_management_intent(self.QUESTION))
        sync_q = "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        self.assertFalse(rag_pipeline.is_terminal_monitor_and_add_intent(sync_q))
        tum_q = "alpeta 단말기 사용자 관리 메뉴 사용법 알려줘"
        self.assertFalse(rag_pipeline.is_terminal_monitor_and_add_intent(tum_q))

    def test_scope_and_expansion_prefer_user_guide_menus(self):
        """검색 범위는 user_guide이고 확장에 모니터링·단말기 관리가 포함됩니다."""
        scope = rag_pipeline.detect_retrieval_scope(self.QUESTION)
        self.assertEqual(scope.get("document_type"), "user_guide")
        expanded = rag_pipeline.expand_retrieval_query(self.QUESTION, self.QUESTION)
        self.assertIn("모니터링", expanded)
        self.assertIn("단말기 관리", expanded)
        self.assertNotIn("출입그룹 단말기 리스트", expanded)
        self.assertNotIn("단말기 찾기", expanded)

    def test_evidence_prefers_monitor_and_mgmt_over_wrong_paths(self):
        """모니터링·단말기 관리 청크가 찾기/0x0A/출입그룹보다 가점이 높습니다."""
        good_mon = (
            "모니터링 단말기의 실시간 상태와 인증 기록, 이벤트 기록을 확인할 수 있습니다. "
            "상태: 단말기가 서버와 연결된 상태 / 연결이 끊어진 상태."
        )
        good_add = (
            "단말기 관리 단말기를 조회, 추가, 수정, 삭제할 수 있는 메뉴입니다. "
            "추가: 단말기 등록 창. 아이디, 이름, 설명."
        )
        bad_find = "단말기 찾기 UDP 통신을 통하여 망내 존재하는 단말기를 찾는 기능입니다."
        bad_proto = "Protocol 상태 알림 0x0A Terminal status notification"
        bad_group = "출입그룹 단말기 리스트 등록된 단말기 추가가능한 단말기"
        bad_fw = "펌웨어 파일 등록 버전 설명 단말기 종류"
        self.assertGreater(
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, good_mon),
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, bad_find),
        )
        self.assertGreater(
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, good_add),
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, bad_proto),
        )
        self.assertGreater(
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, good_add),
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, bad_group),
        )
        self.assertGreater(
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, good_add),
            rag_pipeline.terminal_monitor_and_add_evidence_score(self.QUESTION, bad_fw),
        )

    def test_prompt_and_enforce_require_menus_forbid_wrong_paths(self):
        """프롬프트에 모니터링·단말기 관리 지침이 있고 enforce가 메뉴명을 보강합니다."""
        docs = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": (
                    "모니터링 단말기 상태 접속 상태. "
                    "단말기 관리 추가 아이디 이름 설명."
                ),
                "score": 1.0,
                "metadata": {"document_type": "user_guide"},
            }
        ]
        prompt = rag_pipeline.build_context_prompt(self.QUESTION, docs)
        self.assertIn("모니터링", prompt)
        self.assertIn("단말기 관리", prompt)
        self.assertIn("단말기 찾기", prompt)  # 금지 지침에 언급
        self.assertIn("0x0A", prompt)
        thin = "단말기를 확인하세요."
        enforced = rag_pipeline.enforce_terminal_monitor_and_add(
            self.QUESTION, docs, thin
        )
        self.assertIn("모니터링", enforced)
        self.assertIn("단말기 관리", enforced)

    def test_status_only_intent_excludes_device_add(self):
        """연결상태 단독 질문은 status_only이고 추가-only 질문과 구분됩니다."""
        status_q = "alpeta 단말기 연결 상태는 어떻게 확인해?"
        combined_q = (
            "alpeta 단말기 연결 상태는 어떻게 확인해? 그리고 단말기 어떻게 추가해?"
        )
        self.assertTrue(rag_pipeline.is_terminal_monitor_status_only_intent(status_q))
        self.assertFalse(rag_pipeline.is_terminal_monitor_status_only_intent(combined_q))

    def test_monitor_table_follow_up_contextualize(self):
        """모니터링 후속 표 질문은 녹·적·이벤트 키워드로 문맥화됩니다."""
        history = [
            {"role": "user", "content": "alpeta 단말기 연결 상태는 어떻게 확인해?"},
            {"role": "assistant", "content": "모니터링 메뉴에서 확인합니다."},
        ]
        follow = "상태에 대한 정보를 포함해서 표로 정리해서 보여줘"
        topic = rag_pipeline.recent_user_follow_up_topic(history)
        self.assertEqual(topic, "terminal_monitor")
        ruled = rag_pipeline.rule_contextualize_follow_up(follow, history)
        self.assertIsNotNone(ruled)
        self.assertIn("모니터링", ruled or "")
        self.assertIn("녹", ruled or "")
        self.assertIn("출입문", ruled or "")

    def test_enforce_status_only_adds_green_red_and_events(self):
        """status_only enforce는 녹·적+이벤트 AND를 보장하고 추가 절차를 넣지 않습니다."""
        status_q = "alpeta 단말기 연결 상태는 어떻게 확인해?"
        docs = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": (
                    "모니터링 단말기 상태 접속 상태 연결 끊어진 출입문 열린 닫힌 이벤트."
                ),
                "score": 1.0,
                "metadata": {"document_type": "user_guide"},
            }
        ]
        thin = "모니터링 메뉴에서 확인하세요."
        enforced = rag_pipeline.enforce_terminal_monitor_and_add(
            status_q, docs, thin
        )
        self.assertIn("녹", enforced)
        self.assertIn("빨", enforced)
        self.assertIn("출입문", enforced)
        self.assertNotIn("단말기 관리", enforced)

    def test_enforce_table_followup_replaces_pollution(self):
        """표 후속 enforce는 근태 오염 답을 모니터링 상태 표로 교체합니다."""
        table_q = (
            "Alpeta User Guide 모니터링 메뉴 단말기 접속 상태 "
            "녹색 연결 빨간 끊김 이벤트 출입문 열림 닫힘 표로 정리해줘"
        )
        docs = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": "모니터링 상태 연결 끊어진 출입문 열린 닫힌",
                "score": 1.0,
                "metadata": {"document_type": "user_guide"},
            }
        ]
        polluted = "근태 결근 조퇴 지각 기록 | 표 |"
        enforced = rag_pipeline.enforce_terminal_monitor_and_add(
            table_q, docs, polluted
        )
        self.assertIn("|", enforced)
        self.assertIn("녹", enforced)
        self.assertNotIn("근태", enforced)

    def test_context_completes_monitor_and_add_facets(self):
        """모니터링만 선택되면 단말기 관리 추가 청크를 같은 가이드에서 보충합니다."""
        selected = [
            {
                "source": "Alpeta User Guide.pdf",
                "content": (
                    "모니터링 단말기 상태, 인증 로그, 이벤트 로그. "
                    "상태: 서버와 연결된 상태 / 연결이 끊어진 상태."
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
                    "단말기 관리 단말기를 조회, 추가, 수정, 삭제. "
                    "추가: 등록 창. 아이디 1~99999999 이름 설명."
                ),
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            },
            {
                "document": "단말기 찾기 UDP 검색 0x0A",
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            },
            {
                "document": "펌웨어 파일 등록 버전 설명 단말기 종류",
                "metadata": {
                    "source": "Alpeta User Guide.pdf",
                    "document_type": "user_guide",
                },
            },
        ]
        completed = rag_pipeline.complete_terminal_monitor_add_context(
            selected, records, self.QUESTION, top_k=4, scope={"document_type": "user_guide"}
        )
        joined = "\n".join(d.get("content", "") for d in completed)
        self.assertIn("모니터링", joined)
        self.assertIn("단말기 관리", joined)
        self.assertIn("아이디", joined)
        self.assertNotIn("단말기 찾기", joined)
        self.assertNotIn("펌웨어", joined)


class Loop32DocQaIntentTests(unittest.TestCase):
    """Loop32 핵심 문서 Q&A: 펌웨어·로그인·출입그룹 UI·대역폭 산정 의도 회귀."""

    def test_protocol_firmware_download_expands_0x0020(self):
        """한글 펌웨어 다운로드 질문이 Upgrade firmware 0x0020으로 확장됩니다."""
        q = "v4.0에서 펌웨어 다운로드 프로토콜이 뭐야?"
        self.assertTrue(rag_pipeline.is_protocol_firmware_download_intent(q))
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("0x0020", expanded)
        self.assertIn("Upgrade firmware", expanded)

    def test_api_login_expands_post_v1_login_not_protocol_logon(self):
        """Swagger 로그인 API는 POST /v1/login으로 확장되고 protocol 전용 확장을 피합니다."""
        q = "alpeta swagger에서 서버 로그인 API 경로랑 요청 바디 필드 알려줘"
        self.assertTrue(rag_pipeline.is_api_login_endpoint_intent(q))
        self.assertTrue(rag_pipeline.detect_api_doc_intent(q))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(q))
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("/v1/login", expanded)
        self.assertIn("userType", expanded)
        self.assertNotIn("Command Preview", expanded)

    def test_access_group_ui_scopes_user_guide_not_protocol(self):
        """영문 Alpeta access group UI 질문은 user_guide로 한정됩니다."""
        q = "Alpeta access group 만들 때 ID·명칭·타임존이랑 구역 지정 방법 알려줘"
        self.assertTrue(rag_pipeline.is_access_group_ui_intent(q))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(q))
        scope = rag_pipeline.detect_retrieval_scope(q)
        self.assertEqual(scope.get("document_type"), "user_guide")
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("타임존", expanded)
        self.assertNotIn("Communication protocol for Terminal", expanded)

    def test_mediaserver_capacity_calc_expands_600mbps(self):
        """시청자 합계 대역폭 질문은 600 Mbps 산정 앵커로 확장됩니다."""
        q = "미디어서버에서 시청자 2명일 때 인입+WebRTC 합계 대역폭은 얼마로 잡혀 있어?"
        self.assertTrue(rag_pipeline.is_media_server_capacity_calc_intent(q))
        self.assertFalse(rag_pipeline.is_media_server_spec_intent(q))
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("600 Mbps", expanded)
        self.assertIn("200 Mbps", expanded)

    def test_storage_calc_intent_without_mediaserver_word(self):
        """「미디어서버」없이 동시 녹화·1.2배·스토리지 질문도 capacity intent입니다."""
        q = "동시 녹화 6대·30일 보관일 때 여유 1.2배 반영 스토리지는 약 얼마야?"
        self.assertTrue(rag_pipeline.is_media_server_capacity_calc_intent(q))
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("15GB", expanded)
        self.assertIn("3.24TB", expanded)

    def test_protocol_access_group_download_not_ui_intent(self):
        """「protocol에서 출입그룹 내려」는 UI가 아니라 protocol 전송 확장입니다."""
        q = "신규 protocol에서 출입그룹 어떻게 내려?"
        self.assertFalse(rag_pipeline.is_access_group_ui_intent(q))
        self.assertEqual(
            rag_pipeline.detect_retrieval_scope(q).get("document_type"),
            "protocol",
        )
        expanded = rag_pipeline.expand_retrieval_query(q, "신규 프로토콜 출입그룹")
        self.assertIn("Door 설정 전송", expanded)

    def test_enforce_mediaserver_capacity_adds_600_total(self):
        """아웃바운드만 답한 경우 문서 근거가 있으면 600 Mbps 합계를 보강합니다."""
        q = "MediaServer network calc: 100 streams at 2Mbps with 2 viewers — total Mbps?"
        docs = [
            {
                "content": (
                    "인입 100×2=200 Mbps. 시청자 2명 400 Mbps. 합계 600 Mbps"
                ),
                "source": "MediaServer_Specs_New.md",
            }
        ]
        out = rag_pipeline.enforce_mediaserver_capacity_calc(
            q, docs, "WebRTC only: 400 Mbps"
        )
        self.assertIn("600", out)
        self.assertIn("200", out)

    def test_enforce_storage_adds_15gb_and_1_2_and_4tb(self):
        """90/3240만 있는 스토리지 답에 15GB·1.2배·4TB를 보강합니다."""
        q = "동시 녹화 6대·30일 보관일 때 여유 1.2배 반영 스토리지는 약 얼마야?"
        docs = [
            {
                "content": "1대/일 15GB. 90GB/일×30=2.7TB×1.2≈3.24TB. HDD 4TB 이상",
                "source": "MediaServer_Specs_New.md",
            }
        ]
        out = rag_pipeline.enforce_mediaserver_capacity_calc(
            q,
            docs,
            "하루 90GB, 총 2700GB, 권장 3240GB 입니다.",
        )
        self.assertRegex(out, r"(?i)15\s*GB")
        self.assertIn("1.2", out)
        self.assertRegex(out, r"(?i)4\s*TB")
        self.assertIn("3.24", out)

    def test_timezone_create_ui_scopes_user_guide(self):
        """「alpeta에서 타임존 어떻게 만들어?」는 타임존 UI·user_guide로 한정됩니다."""
        q = "alpeta에서 타임존 어떻게 만들어?"
        self.assertTrue(rag_pipeline.is_timezone_ui_intent(q))
        self.assertFalse(rag_pipeline.is_access_group_ui_intent(q))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(q))
        scope = rag_pipeline.detect_retrieval_scope(q)
        self.assertEqual(scope.get("document_type"), "user_guide")
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("타임존 관리", expanded)
        self.assertNotIn("Door 설정 전송", expanded)

    def test_holiday_create_ui_scopes_user_guide(self):
        """「alpeta에서 공휴일 어떻게 만들어?」는 공휴일 UI·user_guide로 한정됩니다."""
        q = "alpeta에서 공휴일 어떻게 만들어?"
        self.assertTrue(rag_pipeline.is_holiday_ui_intent(q))
        self.assertFalse(rag_pipeline.is_protocol_hex_detail_intent(q))
        scope = rag_pipeline.detect_retrieval_scope(q)
        self.assertEqual(scope.get("document_type"), "user_guide")
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("공휴일 관리", expanded)
        self.assertIn("30", expanded)

    def test_access_group_user_register_not_access_group_create(self):
        """출입그룹 사용자 등록은 access group 생성 UI와 분리됩니다."""
        q = "알페타 출입그룹에 사용자를 등록하려면 어떻게 해?"
        self.assertTrue(rag_pipeline.is_access_group_user_ui_intent(q))
        self.assertFalse(rag_pipeline.is_access_group_ui_intent(q))

    def test_enforce_holiday_ui_adds_menu_and_30(self):
        """공휴일 생성 enforce는 메뉴·달력 추가·30개를 AND로 보강합니다."""
        q = "alpeta에서 공휴일 어떻게 만들어?"
        docs = [
            {
                "content": (
                    "[타임존] > [공휴일 관리]. 최대 30 개. ID 와 이름. "
                    "달력 [추가]. 저장"
                ),
                "source": "Alpeta User Guide.pdf",
            }
        ]
        out = rag_pipeline.enforce_holiday_ui_procedure(q, docs, "공휴일은 설정합니다.")
        self.assertIn("공휴일 관리", out)
        self.assertIn("달력", out)
        self.assertIn("30", out)

    def test_timezone_create_enforce_corrects_timeline_confusion(self):
        """Q1 enforce는 새 타임라인 혼동 시 한주간·콤보박스 절차로 교정합니다."""
        q = "alpeta에서 타임존 어떻게 만들어?"
        wrong = (
            "1. **[새 타임라인]** 버튼으로 시작합니다. "
            "타임존 관리 [추가] 후 ID·NAME 입력. "
            "3. **한주간의 일정**을 콤보박스에서 선택. [저장] [출입그룹]."
        )
        out = rag_pipeline.enforce_timezone_ui_procedure(q, [], wrong)
        self.assertIn("한주", out)
        self.assertIn("콤보박스", out)
        self.assertNotIn("1. **[새 타임라인]**", out)
        bare = "타임존 관리에서 [추가] 후 [새 타임라인] 버튼으로 일정을 만듭니다."
        out2 = rag_pipeline.enforce_timezone_ui_procedure(q, [], bare)
        self.assertIn("콤보박스", out2)

    def test_timeline_create_separate_from_timezone_create(self):
        """Q7 타임라인 신규는 is_timeline_create_ui_intent로 Q1과 분리됩니다."""
        q_tz = "alpeta에서 타임존 어떻게 만들어?"
        q_tl = "알페타 타임라인 새로 만들 때 뭘 입력해야 해?"
        self.assertTrue(rag_pipeline.is_timezone_create_ui_intent(q_tz))
        self.assertFalse(rag_pipeline.is_timeline_create_ui_intent(q_tz))
        self.assertTrue(rag_pipeline.is_timeline_create_ui_intent(q_tl))
        self.assertFalse(rag_pipeline.is_timezone_create_ui_intent(q_tl))

    def test_enforce_authlog_categories_six_and_no_denial(self):
        """인증 로그 카테고리 enforce는 6항 AND·단말기명 부정 제거."""
        q = "알페타 인증 로그 조회할 때 검색 카테고리에는 뭐가 있어?"
        wrong = (
            "전체, 사용자 ID, 단말기 ID, 유니크 ID. "
            "[단말기명]은 명시되어 있지 않습니다."
        )
        out = rag_pipeline.enforce_authlog_search_categories(q, [], wrong)
        self.assertIn("단말기명", out)
        self.assertIn("전체", out)
        self.assertNotIn("명시되어 있지", out.split("단말기명")[-1][:80])

    def test_enforce_access_zone_adds_timezone_before_save(self):
        """Q3 enforce는 타임존 선택 단계를 AND로 보강합니다."""
        q = "알페타에서 출입구역 추가하는 방법 알려줘"
        wrong = (
            "출입구역 ID·출입구역명 입력. "
            "추가 가능한 단말기 ↔ 등록된 단말기 이동 후 [저장]."
        )
        out = rag_pipeline.enforce_access_zone_ui_procedure(q, [], wrong)
        self.assertIn("타임존", out)
        self.assertIn("저장", out)

    def test_enforce_timeline_create_adds_double_click(self):
        """Q7 enforce는 출입 상태 더블클릭 시간대 생성 단계를 보강합니다."""
        q = "알페타 타임라인 새로 만들 때 뭘 입력해야 해?"
        wrong = (
            "ID와 NAME 입력 후 [새 타임라인] 버튼 클릭. [저장]으로 저장."
        )
        out = rag_pipeline._enforce_timeline_create_ui_procedure(q, [], wrong)
        self.assertIn("더블클릭", out)
        self.assertIn("새 타임라인", out)

    def test_auto_sync_setting_intent_excludes_combined_manual_sync(self):
        """일반설정 자동동기화 단독 질문만 auto_sync 의도이고 복합 절차는 user_terminal입니다."""
        solo = "알페타 일반설정에서 단말기 사용자 정보 자동 동기화 켜는 방법 알려줘"
        combined = (
            "alpeta에서 사용자를 단말기에 어떻게 추가해? 그리고 자동동기화는 어떻게 해?"
        )
        self.assertTrue(rag_pipeline.is_auto_sync_setting_intent(solo))
        self.assertFalse(rag_pipeline.is_user_terminal_procedure_intent(solo))
        self.assertFalse(rag_pipeline.is_auto_sync_setting_intent(combined))
        self.assertTrue(rag_pipeline.is_user_terminal_procedure_intent(combined))

    def test_enforce_auto_sync_setting_replaces_manual_primary(self):
        """자동동기화 단독 질문에서 수동 3경로가 앞서면 canonical으로 교체합니다."""
        q = "알페타 일반설정에서 단말기 사용자 정보 자동 동기화 켜는 방법 알려줘"
        manual_first = (
            "### [사용자 관리]\n단말기리스트에서 사용자를 내려갑니다.\n\n"
            "### [자동동기화]\n단말기 사용자 정보 자동 동기화 사용."
        )
        out = rag_pipeline.enforce_auto_sync_setting_procedure(q, [], manual_first)
        self.assertIn("일반설정", out)
        self.assertIn("단말기 사용자 정보 자동 동기화", out)
        self.assertIn("출입그룹", out)
        self.assertNotIn("단말기리스트", out)
        self.assertNotIn("사용자 관리", out)

    def test_auto_sync_prompt_excludes_manual_paths(self):
        """자동동기화 단독 질문 프롬프트에 수동 전송 금지 지침이 있습니다."""
        q = "알페타 일반설정에서 단말기 사용자 정보 자동 동기화 켜는 방법 알려줘"
        prompt = rag_pipeline.build_context_prompt(
            q,
            [{"source": "Alpeta User Guide.pdf", "score": 1.0, "content": "사용자 설정"}],
        )
        self.assertIn("자동 동기화 설정", prompt)
        self.assertIn("단말기 사용자 정보 자동 동기화 사용", prompt)
        self.assertIn("수동 전송", prompt)
        self.assertNotIn("서로 다른 메뉴 3경로", prompt)


class ApiEntitySynonymIntentRegression(unittest.TestCase):
    """Loop36: 한글↔영문 API 엔티티 동의어·의도 우선순위 일반화."""

    def test_access_group_api_ko_not_ui_scope(self):
        """출입그룹+API는 UG UI intent가 아니고 api scope·accessGroups 확장입니다."""
        q = "alpeta 출입그룹 관련한 API 알려줘"
        self.assertTrue(rag_pipeline.detect_api_doc_intent(q))
        self.assertTrue(rag_pipeline.is_api_entity_doc_intent(q))
        self.assertFalse(rag_pipeline.is_access_group_ui_intent(q))
        scope = rag_pipeline.detect_retrieval_scope(q)
        self.assertEqual(scope.get("document_type"), "api")
        expanded = rag_pipeline.expand_retrieval_query(q, q)
        self.assertIn("/v1/accessGroups", expanded)
        self.assertIn("accessGroups", expanded)

    def test_access_group_swagger_and_spaced_en(self):
        """swagger 한글·Access Group 띄어쓰기도 api scope와 시드 경로를 씁니다."""
        questions = (
            "alpeta swagger에서 출입그룹 관련한 API 알려줘",
            "alpeta에서 Access Group 관련 API 알려줘",
            "alpeta에서 AccessGroup API 알려줘",
        )
        for q in questions:
            with self.subTest(q=q):
                self.assertTrue(rag_pipeline.detect_api_doc_intent(q))
                self.assertFalse(rag_pipeline.is_access_group_ui_intent(q))
                self.assertEqual(
                    rag_pipeline.detect_retrieval_scope(q).get("document_type"),
                    "api",
                )
                seeds = rag_pipeline.required_api_seed_paths_for_query(q)
                paths = {s["path"] for s in seeds}
                self.assertIn("/v1/accessGroups", paths)

    def test_access_group_ui_howto_stays_user_guide(self):
        """API 키워드 없는 출입그룹 추가 질문은 user_guide를 유지합니다."""
        q = "alpeta에서 출입그룹 어떻게 추가해?"
        self.assertFalse(rag_pipeline.detect_api_doc_intent(q))
        self.assertTrue(rag_pipeline.is_access_group_ui_intent(q))
        self.assertEqual(
            rag_pipeline.detect_retrieval_scope(q).get("document_type"),
            "user_guide",
        )

    def test_users_and_terminals_entity_lexicon(self):
        """사용자/단말기 한글·영문 API 질문이 동일 엔티티 시드를 받습니다."""
        pairs = (
            (
                "alpeta에서 사용자 API 알려줘",
                "alpeta에서 users API 알려줘",
                "/v1/users",
            ),
            (
                "alpeta에서 단말기 API 알려줘",
                "alpeta에서 terminals API 알려줘",
                "/v1/terminals",
            ),
        )
        for ko, en, path in pairs:
            with self.subTest(path=path):
                for q in (ko, en):
                    self.assertTrue(rag_pipeline.is_api_entity_doc_intent(q))
                    seeds = rag_pipeline.required_api_seed_paths_for_query(q)
                    self.assertTrue(any(s["path"] == path for s in seeds))

    def test_enforce_access_groups_catalog_seeds(self):
        """출입그룹 API 답에 경로가 없으면 시드 카탈로그로 POST/GET/PUT을 보강합니다."""
        q = "alpeta 출입그룹 관련한 API 알려줘"
        docs = [
            {
                "content": "## GET `/v1/accessGroups`\n출입그룹 목록",
                "source": "swagger_kr.md",
            }
        ]
        out = rag_pipeline.enforce_api_endpoint_catalog(
            q, docs, "출입그룹 API는 User Guide에만 있습니다."
        )
        self.assertIn("/v1/accessGroups", out)
        self.assertIn("POST", out)
        self.assertIn("PUT", out)
        self.assertIn("/v1/accessGroups/{id}", out)

if __name__ == "__main__":
    unittest.main(verbosity=2)
