"""Golden-set retrieval evaluation.

Measures whether hybrid retrieval returns the expected source document (and
optional keywords) for real user questions.  Run after every retrieval or
indexing change so quality regressions are caught before users notice them.

Container usage:
    docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py

Golden entries live in rag/data/eval/golden_questions.json:
    {"question": "...", "expected_source": "file.md", "expected_keywords": ["..."]}
Add every question that failed in production to keep the set representative.
"""

import argparse
import json
import os
import sys
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAG_ROOT))

from pipelines import rag_pipeline  # noqa: E402

DEFAULT_GOLDEN_PATH = os.getenv(
    "GOLDEN_QUESTIONS_PATH",
    str(RAG_ROOT / "data" / "eval" / "golden_questions.json"),
)


def _print_ranked_documents(stage: str, documents: list, limit: int = 20) -> None:
    """진단 단계의 후보 순위·점수·출처·원문 앞부분을 읽기 쉽게 출력합니다."""
    print(f"\n[{stage}]")
    for rank, document in enumerate(documents[:limit], 1):
        scores = [
            f"score={document.get('score')}",
            f"rrf={document.get('rrf_score')}",
            f"rerank={document.get('rerank_score')}",
            f"technical={document.get('technical_evidence_score')}",
            f"combined={document.get('combined_rerank_score')}",
        ]
        score_text = " ".join(score for score in scores if not score.endswith("=None"))
        preview = " ".join(document.get("content", "").split())[:300]
        print(f"{rank:>2}. {document.get('source')} | {score_text}")
        print(f"    {preview}")


def diagnose_question(question: str, rerank: bool, limit: int = 20) -> int:
    """한 질문의 vector→BM25→RRF→reranker 후보를 동일 설정으로 추적합니다.

    평가와 같은 로컬 인덱스를 사용하며 LLM 재작성은 호출하지 않습니다. 원질문
    보존과 결정적 확장 이후 각 단계의 순위 변화를 조사하는 용도입니다.
    """
    scope = rag_pipeline.detect_retrieval_scope(question)
    query = rag_pipeline.expand_retrieval_query(question, question)
    candidate_count = max(
        limit,
        rag_pipeline.DEFAULT_VECTOR_CANDIDATES,
        rag_pipeline.DEFAULT_RERANK_CANDIDATES if rerank else 0,
    )
    print(f"Question: {question}")
    print(f"Scope: {scope or 'none'}")
    print(f"Expanded query: {query!r}")
    print(f"BM25 tokens: {rag_pipeline._bm25_tokens(query)}")
    print(f"Technical tokens: {rag_pipeline.extract_technical_tokens(question)}")
    print(f"Artifact intents: {rag_pipeline.detect_artifact_intents(question)}")

    vector_documents = rag_pipeline.retrieve_vector_documents(
        rag_pipeline.DEFAULT_CHROMA_PATH,
        rag_pipeline.DEFAULT_COLLECTION_NAME,
        rag_pipeline.DEFAULT_EMBEDDING_MODEL,
        query,
        candidate_count,
        rag_pipeline.DEFAULT_MIN_RELEVANCE_SCORE,
        scope,
    )
    records, bm25 = rag_pipeline._get_bm25_index(rag_pipeline.DEFAULT_BM25_INDEX_PATH)
    allowed = [
        index
        for index, record in enumerate(records)
        if rag_pipeline._metadata_matches_scope(record.get("metadata"), scope)
    ]
    scores = [0.0] * len(records)
    if bm25 is not None:
        for query_variant in [line for line in query.splitlines() if line.strip()]:
            for index, score in enumerate(
                bm25.get_scores(rag_pipeline._bm25_tokens(query_variant))
            ):
                scores[index] = max(scores[index], float(score))
    ranked_indexes = sorted(allowed, key=lambda index: scores[index], reverse=True)
    bm25_documents = []
    for index in ranked_indexes[:rag_pipeline.DEFAULT_BM25_CANDIDATES]:
        if scores[index] <= 0:
            continue
        record = records[index]
        metadata = record.get("metadata") or {}
        bm25_documents.append(
            {
                "content": record.get("document", ""),
                "source": metadata.get("source", "unknown"),
                "score": round(scores[index], 4),
                "metadata": metadata,
            }
        )

    rrf_documents = rag_pipeline._rrf_merge(
        vector_documents,
        bm25_documents,
        candidate_count,
        query=question,
    )
    _print_ranked_documents("VECTOR", vector_documents, limit)
    _print_ranked_documents("BM25", bm25_documents, limit)
    _print_ranked_documents("RRF + TECHNICAL EVIDENCE", rrf_documents, limit)
    if rerank:
        reranked = rag_pipeline.rerank_documents(
            question,
            rrf_documents,
            rag_pipeline.DEFAULT_RERANK_MODEL,
            candidate_count,
        )
        _print_ranked_documents("RERANKER + TECHNICAL EVIDENCE", reranked, limit)
    return 0


def build_evaluation_context(documents: list) -> str:
    """검색 원문과 같은 지시문에서 결정적으로 결합된 파일 경로를 평가합니다.

    사용자 질문이나 생성 프롬프트 전체는 넣지 않아 기대 키워드가 질문에서
    유입되는 오탐을 막고, 실제 답변 컨텍스트에 추가되는 안전한 경로만 포함합니다.
    """
    parts = [doc.get("content", "") for doc in documents]
    parts.extend(rag_pipeline.derive_explicit_file_paths(documents))
    return "\n".join(parts)


def evaluate(golden_path: str, top_k: int, rerank: bool) -> int:
    """골든 질문별 출처와 모든 필수 키워드를 평가해 성공 여부를 반환합니다.

    각 항목은 예상 출처가 검색되고 `expected_keywords`가 하나도 빠지지 않아야
    PASS입니다. 반환값 0은 모든 항목의 두 조건이 충족된 경우에만 사용합니다.
    """
    entries = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    if not entries:
        sys.exit(f"No golden questions in: {golden_path}")

    source_hits = keyword_hits = keyword_total = passed_entries = 0
    for entry in entries:
        question = entry["question"]
        scope = rag_pipeline.detect_retrieval_scope(question)
        query = rag_pipeline.expand_retrieval_query(question, question)
        documents = rag_pipeline.retrieve_documents(
            chroma_path=rag_pipeline.DEFAULT_CHROMA_PATH,
            collection_name=rag_pipeline.DEFAULT_COLLECTION_NAME,
            embedding_model=rag_pipeline.DEFAULT_EMBEDDING_MODEL,
            query=query,
            top_k=top_k,
            min_relevance_score=rag_pipeline.DEFAULT_MIN_RELEVANCE_SCORE,
            scope=scope,
            rerank_enabled=rerank,
            rerank_query=question,
        )
        sources = [doc.get("source") for doc in documents]
        combined = build_evaluation_context(documents)

        source_ok = entry.get("expected_source") in sources
        source_hits += source_ok
        keyword_marks = []
        all_keywords_ok = True
        for keyword in entry.get("expected_keywords", []):
            keyword_total += 1
            found = keyword in combined
            keyword_hits += found
            all_keywords_ok = all_keywords_ok and found
            keyword_marks.append(f"{'O' if found else 'X'} {keyword}")

        entry_ok = source_ok and all_keywords_ok
        passed_entries += entry_ok
        print(f"[{'PASS' if entry_ok else 'FAIL'}] {question}")
        print(
            f"    source: {'PASS' if source_ok else 'FAIL'} "
            f"| expected: {entry.get('expected_source')} / got: {sources}"
        )
        if keyword_marks:
            print(
                f"    keywords: {'PASS' if all_keywords_ok else 'FAIL'} "
                f"| {', '.join(keyword_marks)}"
            )
        else:
            print("    keywords: PASS | none required")

    print(
        f"\nEntry pass rate: {passed_entries}/{len(entries)}"
        + f" | Source hit rate: {source_hits}/{len(entries)}"
        + (f" | Keyword hit rate: {keyword_hits}/{keyword_total}" if keyword_total else "")
    )
    return 0 if passed_entries == len(entries) else 1


def main():
    """명령행 인자를 해석해 골든셋 평가 또는 단일 질문 진단을 실행합니다."""
    parser = argparse.ArgumentParser(description="Evaluate retrieval against the golden question set.")
    parser.add_argument("--golden", default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--top-k", type=int, default=rag_pipeline.DEFAULT_TOP_K)
    parser.add_argument("--rerank", action="store_true", help="Enable the cross-encoder reranker during evaluation")
    parser.add_argument(
        "--diagnose-question",
        help="Print vector/BM25/RRF/reranker ranks for one question instead of evaluating the golden set",
    )
    parser.add_argument("--diagnose-limit", type=int, default=20)
    args = parser.parse_args()
    if args.diagnose_question:
        sys.exit(diagnose_question(args.diagnose_question, args.rerank, args.diagnose_limit))
    sys.exit(evaluate(args.golden, args.top_k, args.rerank))


if __name__ == "__main__":
    main()
