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


def evaluate(golden_path: str, top_k: int, rerank: bool) -> int:
    entries = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    if not entries:
        sys.exit(f"No golden questions in: {golden_path}")

    source_hits = keyword_hits = keyword_total = 0
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
        combined = "\n".join(doc.get("content", "") for doc in documents)

        source_ok = entry.get("expected_source") in sources
        source_hits += source_ok
        keyword_marks = []
        for keyword in entry.get("expected_keywords", []):
            keyword_total += 1
            found = keyword in combined
            keyword_hits += found
            keyword_marks.append(f"{'O' if found else 'X'} {keyword}")

        print(f"[{'PASS' if source_ok else 'FAIL'}] {question}")
        print(f"    expected: {entry.get('expected_source')} / got: {sources}")
        if keyword_marks:
            print(f"    keywords: {', '.join(keyword_marks)}")

    print(
        f"\nSource hit rate: {source_hits}/{len(entries)}"
        + (f" | Keyword hit rate: {keyword_hits}/{keyword_total}" if keyword_total else "")
    )
    return 0 if source_hits == len(entries) else 1


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval against the golden question set.")
    parser.add_argument("--golden", default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--top-k", type=int, default=rag_pipeline.DEFAULT_TOP_K)
    parser.add_argument("--rerank", action="store_true", help="Enable the cross-encoder reranker during evaluation")
    args = parser.parse_args()
    sys.exit(evaluate(args.golden, args.top_k, args.rerank))


if __name__ == "__main__":
    main()
