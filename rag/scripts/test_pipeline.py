"""
파이프라인 테스트 스크립트
==========================
Open WebUI 없이 파이프라인의 각 단계를 직접 테스트합니다.

사용법(권장: `rag/` 디렉터리에서 실행):
  python scripts/test_pipeline.py
  python scripts/test_pipeline.py --query "원하는 질문"
"""

import sys
import time
import argparse
from pathlib import Path

RAG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAG_ROOT))
sys.path.insert(0, str(RAG_ROOT / "pipelines"))

from pipelines.rag_pipeline import (
    rewrite_query,
    retrieve_documents,
    build_context_prompt,
    detect_retrieval_scope,
    ollama_chat,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_REWRITE_MODEL,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_CHROMA_PATH,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_NUM_CTX,
    DEFAULT_NUM_PREDICT,
)


def run_test(query: str, verbose: bool = True):
    """전체 파이프라인을 단계별로 실행하고 결과를 출력합니다."""
    separator = "─" * 60

    print(f"\n{separator}")
    print("  LLM → RAG → LLM 파이프라인 테스트")
    print(separator)
    print(f"원본 질문: {query}\n")

    # ── Step 1: 질문 재작성 ─────────────────────
    print("[Step 1] 질문 재작성 (LLM 1)")
    t0 = time.time()
    rewritten = rewrite_query(
        base_url=DEFAULT_OLLAMA_BASE_URL,
        model=DEFAULT_REWRITE_MODEL,
        original_query=query,
        chat_history=[],
    )
    t1 = time.time()
    print(f"  모델: {DEFAULT_REWRITE_MODEL}")
    print(f"  결과: {rewritten}")
    print(f"  소요 시간: {t1-t0:.2f}s\n")

    # ── Step 2: 벡터 검색 ──────────────────────
    print("[Step 2] 벡터 검색 (ChromaDB)")
    t2 = time.time()
    docs = retrieve_documents(
        chroma_path=DEFAULT_CHROMA_PATH,
        collection_name=DEFAULT_COLLECTION_NAME,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        query=rewritten,
        top_k=5,
        min_relevance_score=0.0,
        scope=detect_retrieval_scope(query),
    )
    t3 = time.time()
    print(f"  검색된 문서: {len(docs)}개")
    print(f"  소요 시간: {t3-t2:.2f}s")

    if docs:
        print("\n  검색 결과:")
        for i, doc in enumerate(docs, 1):
            preview = doc['content'][:100].replace('\n', ' ')
            print(f"  [{i}] 관련도: {doc['score']} | 출처: {doc['source']}")
            print(f"      미리보기: {preview}...")
    else:
        print("  (저장된 문서가 없습니다. index_documents.py를 먼저 실행하세요)")
    print()

    # ── Step 3: 최종 답변 생성 ──────────────────
    print("[Step 3] 최종 답변 생성 (LLM 2)")
    context_prompt = build_context_prompt(query, docs)

    system_msg = "당신은 친절하고 정확한 AI 어시스턴트입니다. 주어진 참고 문서를 바탕으로 답변하세요."
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": context_prompt}
    ]

    t4 = time.time()
    answer = ollama_chat(
        base_url=DEFAULT_OLLAMA_BASE_URL,
        model=DEFAULT_ANSWER_MODEL,
        messages=messages,
        stream=False,
        options={"num_ctx": DEFAULT_NUM_CTX, "num_predict": DEFAULT_NUM_PREDICT},
    )
    t5 = time.time()

    print(f"  모델: {DEFAULT_ANSWER_MODEL}")
    print(f"  소요 시간: {t5-t4:.2f}s\n")
    print(separator)
    print("최종 답변:")
    print(separator)
    print(answer)
    print(separator)
    print(f"\n총 소요 시간: {t5-t0:.2f}s")


def test_rewrite_only():
    """질문 재작성 기능만 테스트합니다."""
    test_queries = [
        "이것에 대해 더 자세히 설명해줘",
        "파이썬으로 어떻게 만들어?",
        "RAG 시스템에서 청크 크기가 성능에 미치는 영향은?",
        "회사 휴가 정책이 어떻게 돼?",
    ]

    print("\n=== 질문 재작성 테스트 ===\n")
    for q in test_queries:
        rewritten = rewrite_query(
            base_url=DEFAULT_OLLAMA_BASE_URL,
            model=DEFAULT_REWRITE_MODEL,
            original_query=q,
            chat_history=[],
        )
        print(f"원본:     {q}")
        print(f"재작성:   {rewritten}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="파이프라인 테스트")
    parser.add_argument("--query", "-q", type=str,
                        default="RAG 시스템에서 벡터 검색은 어떻게 동작하나요?",
                        help="테스트할 질문")
    parser.add_argument("--rewrite-only", action="store_true",
                        help="질문 재작성 기능만 테스트")

    args = parser.parse_args()

    if args.rewrite_only:
        test_rewrite_only()
    else:
        run_test(args.query)
