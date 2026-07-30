"""Regression tests for scoped retrieval and answer-stream configuration.

Run in the pipeline container after dependencies are installed:
    python /app/scripts/test_rag_regression.py
"""

import json
import sys
import tempfile
import types
import unittest
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
from scripts.index_documents import classify_document, split_pdf_page_sections
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
