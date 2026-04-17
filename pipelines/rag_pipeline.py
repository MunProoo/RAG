"""
LLM → RAG → LLM Pipeline for Open WebUI
=========================================
동작 방식:
  1. LLM 1: 사용자 질문을 검색에 최적화된 쿼리로 재작성
  2. ChromaDB: 재작성된 쿼리로 관련 문서 청크 검색
  3. LLM 2: 검색 결과를 컨텍스트로 사용하여 최종 답변 생성 (스트리밍)
"""

import os
import json
from typing import List, Union, Generator, Iterator, Dict, Tuple

import requests
from pydantic import BaseModel

import chromadb
from chromadb.utils import embedding_functions


# ─────────────────────────────────────────
# 기본값 (환경변수로 override 가능)
# ─────────────────────────────────────────
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_REWRITE_MODEL = os.getenv("REWRITE_MODEL", "qwen3:1.7b")
DEFAULT_ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen3:1.7b")

DEFAULT_CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
DEFAULT_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "rag_documents")

DEFAULT_TOP_K = int(os.getenv("TOP_K", "5"))
DEFAULT_MIN_RELEVANCE_SCORE = float(os.getenv("MIN_SCORE", "0.3"))

# 한국어 사내 문서 기준 기본 임베딩 모델
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")


# ─────────────────────────────────────────
# Open WebUI 내부 작업 감지
# ─────────────────────────────────────────
def is_openwebui_internal_task(user_message: str) -> bool:
    """
    Open WebUI가 채팅 UX를 위해 추가로 호출하는 내부 작업 프롬프트를 감지합니다.
    (후속 질문/제목/태그 생성 등)
    """
    text = (user_message or "").lstrip()
    if text.startswith("### Task:"):
        return True
    if "### Chat History:" in (user_message or ""):
        return True
    return False


# ─────────────────────────────────────────
# ChromaDB 유틸
# ─────────────────────────────────────────
def get_chroma_collection(
    chroma_path: str,
    collection_name: str,
    embedding_model: str,
):
    """ChromaDB 컬렉션을 반환합니다."""
    client = chromadb.PersistentClient(path=chroma_path)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model
    )
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


# ─────────────────────────────────────────
# Ollama API 호출 유틸
# ─────────────────────────────────────────
def ollama_chat(
    base_url: str,
    model: str,
    messages: list,
    stream: bool = False,
) -> str:
    """Ollama chat API를 호출합니다."""
    url = f"{base_url}/api/chat"
    # 일부 Ollama 모델은 think/thinking 옵션을 지원합니다.
    # Open WebUI/RAG 응답에서 사고과정 노출을 피하기 위해 기본적으로 think=false를 전달합니다.
    payload = {"model": model, "messages": messages, "stream": stream, "think": False}
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def ollama_chat_stream(
    base_url: str,
    model: str,
    messages: list,
) -> Generator[str, None, None]:
    """Ollama chat API 스트리밍 버전."""
    url = f"{base_url}/api/chat"
    payload = {"model": model, "messages": messages, "stream": True, "think": False}
    with requests.post(url, json=payload, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if not data.get("done", False):
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content


# ─────────────────────────────────────────
# Step 1: 질문 재작성 (LLM 1)
# ─────────────────────────────────────────
def rewrite_query(
    base_url: str,
    model: str,
    original_query: str,
    chat_history: list,
) -> str:
    """
    LLM 1: 사용자 질문을 벡터 검색에 최적화된 쿼리로 재작성합니다.
    - 검색 친화적인 키워드 강조
    - 모호한 지시어(이것, 그것 등) 명확화
    """
    # 성능/안정성 목적: 대화 컨텍스트는 재작성에 반영하지 않습니다.
    # (입력 토큰 감소 → 지연 감소, 내부 태스크/잡담 변형 최소화)
    system_prompt = """당신은 벡터 DB 검색 쿼리 최적화 전문가입니다.
사용자의 질문을 "검색 친화적 쿼리"로 재작성하세요.

출력 규칙(매우 중요):
- 반드시 2~4개의 검색 쿼리 변형을 생성하세요.
- 각 변형은 한 줄에 하나씩 출력하세요. (줄바꿈으로만 구분)
- 각 줄은 4~12개의 핵심 키워드/구(phrase)로 구성하세요.
- 인사말/감탄사/설명/머리말/번호/따옴표/JSON/마크다운 금지.
- 한국어 질문은 한국어로 유지하세요.
- 고유명사(제품명/프로젝트명/약어/파일명/명령어/경로/API명)는 원문 표기를 그대로 보존하세요.
- 고유명사 오타/철자 변경/유사 발음 변형 금지. (예: "알페타"→"알파타" 금지)

재작성 가이드:
- 동의어/표현 변형을 섞으세요 (예: "하루치"↔"일일"↔"24시간", "대당"↔"단말기 1대"↔"채널 1개")
- 단위/수치가 유추되면 함께 포함하세요 (예: GB, TB, Mbps, fps 등)
- 불필요하게 문장으로 만들지 말고 검색 키워드 묶음으로 만드세요."""

    user_message = f"""원본 질문: {original_query}

검색 쿼리 변형(2~4줄):"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    rewritten = ollama_chat(base_url, model, messages, stream=False)
    # 2~4줄로 제한(모델이 과다 생성할 때 대비)
    lines = [ln.strip() for ln in rewritten.splitlines() if ln.strip()]
    lines = lines[:4] if len(lines) > 4 else lines
    return "\n".join(lines).strip()


# ─────────────────────────────────────────
# Step 2: 벡터 검색 (RAG)
# ─────────────────────────────────────────
def retrieve_documents(
    chroma_path: str,
    collection_name: str,
    embedding_model: str,
    query: str,
    top_k: int,
    min_relevance_score: float,
) -> list:
    """
    ChromaDB에서 쿼리와 관련된 문서 청크를 검색합니다.
    반환: [{"content": str, "source": str, "score": float}, ...]
    """
    try:
        collection = get_chroma_collection(
            chroma_path=chroma_path,
            collection_name=collection_name,
            embedding_model=embedding_model,
        )
        doc_count = collection.count()
        if doc_count == 0:
            return []

        # rewrite_query()가 여러 줄(2~4 변형)을 반환할 수 있으므로 멀티쿼리 검색을 지원합니다.
        queries = [q.strip() for q in (query or "").splitlines() if q.strip()]
        if not queries:
            return []

        # 쿼리별로 top_k씩 뽑아 병합(중복 제거 + 최고 점수 유지)
        actual_k = min(top_k, doc_count)
        results = collection.query(
            query_texts=queries,
            n_results=actual_k,
            include=["documents", "metadatas", "distances"],
        )

        merged: Dict[Tuple[str, str], Dict] = {}
        docs_by_query = results.get("documents") or []
        metas_by_query = results.get("metadatas") or []
        dists_by_query = results.get("distances") or []

        for docs, metas, dists in zip(docs_by_query, metas_by_query, dists_by_query):
            for doc, meta, dist in zip(docs or [], metas or [], dists or []):
                score = 1 - dist
                if score < min_relevance_score:
                    continue
                source = (meta or {}).get("source", "unknown")
                key = (source, doc)
                prev = merged.get(key)
                if (prev is None) or (score > prev["score"]):
                    merged[key] = {
                        "content": doc,
                        "source": source,
                        "score": round(score, 3),
                    }

        # 점수 높은 순으로 정렬 후 top_k로 절단
        retrieved = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return retrieved[:top_k]
    except Exception as e:
        print(f"[RAG] 검색 오류: {e}")
        return []


# ─────────────────────────────────────────
# Step 3: 최종 답변 생성 (LLM 2)
# ─────────────────────────────────────────
def build_context_prompt(query: str, documents: list) -> str:
    """검색된 문서를 컨텍스트로 포함한 프롬프트를 생성합니다."""
    if not documents:
        return query

    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[문서 {i}] (출처: {doc['source']}, 관련도: {doc['score']})\n{doc['content']}"
        )

    context_str = "\n\n".join(context_parts)
    return f"""다음 참고 문서들을 바탕으로 질문에 답변하세요.

=== 참고 문서 ===
{context_str}

=== 질문 ===
{query}

=== 답변 지침 ===
- 참고 문서의 내용을 기반으로 답변하세요
- 문서에 없는 내용은 "제공된 문서에서 확인할 수 없습니다"라고 명시하세요
- 출처를 인용할 때는 [문서 N] 형식을 사용하세요
- 명확하고 구조적으로 답변하세요"""


# ─────────────────────────────────────────
# Open WebUI Pipeline 클래스
# ─────────────────────────────────────────
class Pipeline:
    """
    Open WebUI가 인식하는 Pipeline 클래스입니다.
    pipelines 서버에 배포 후 Open WebUI에서 커스텀 모델로 등록하세요.
    """

    class Valves(BaseModel):
        """Open WebUI UI에서 설정 가능한 파라미터"""

        OLLAMA_BASE_URL: str = DEFAULT_OLLAMA_BASE_URL
        REWRITE_MODEL: str = DEFAULT_REWRITE_MODEL
        ANSWER_MODEL: str = DEFAULT_ANSWER_MODEL

        CHROMA_PATH: str = DEFAULT_CHROMA_PATH
        CHROMA_COLLECTION: str = DEFAULT_COLLECTION_NAME
        EMBEDDING_MODEL: str = DEFAULT_EMBEDDING_MODEL

        TOP_K: int = DEFAULT_TOP_K
        MIN_RELEVANCE_SCORE: float = DEFAULT_MIN_RELEVANCE_SCORE

        SHOW_SOURCES: bool = True
        SHOW_REWRITTEN_QUERY: bool = False

    def __init__(self):
        self.name = "LLM → RAG → LLM Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[Pipeline] 시작: {self.name}")
        print(f"[Pipeline] Ollama: {self.valves.OLLAMA_BASE_URL}")
        print(f"[Pipeline] 재작성 모델: {self.valves.REWRITE_MODEL}")
        print(f"[Pipeline] 답변 모델: {self.valves.ANSWER_MODEL}")
        print(f"[Pipeline] 임베딩 모델: {self.valves.EMBEDDING_MODEL}")
        try:
            col = get_chroma_collection(
                chroma_path=self.valves.CHROMA_PATH,
                collection_name=self.valves.CHROMA_COLLECTION,
                embedding_model=self.valves.EMBEDDING_MODEL,
            )
            print(f"[Pipeline] ChromaDB 연결 성공. 문서 수: {col.count()}")
        except BaseException as e:
            # chromadb의 rust 바인딩 일부 오류는 Exception이 아닌 BaseException 계열로 전파될 수 있습니다.
            print(f"[Pipeline] ChromaDB 연결 실패: {type(e).__name__}: {e}")
            print(
                "[Pipeline] 힌트: `./chroma_db`를 삭제(완전 초기화)한 뒤 indexer로 재인덱싱하고, "
                "`pipelines`/`indexer`의 chromadb 버전이 동일한지 확인하세요."
            )

    async def on_shutdown(self):
        print(f"[Pipeline] 종료: {self.name}")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[str, Generator, Iterator]:
        chat_history = messages[:-1] if len(messages) > 1 else []

        print(f"\n[Step 1] 원본 질문: {user_message}")

        # Open WebUI 내부 작업(후속질문/제목/태그 등)은 RAG/재작성 스킵
        if is_openwebui_internal_task(user_message):
            print("[Route] Open WebUI 내부 작업: RAG/재작성 스킵")
            stream = bool((body or {}).get("stream", True))

            def generate_internal():
                if stream:
                    yield from ollama_chat_stream(
                        base_url=self.valves.OLLAMA_BASE_URL,
                        model=self.valves.ANSWER_MODEL,
                        messages=messages,
                    )
                else:
                    yield ollama_chat(
                        base_url=self.valves.OLLAMA_BASE_URL,
                        model=self.valves.ANSWER_MODEL,
                        messages=messages,
                        stream=False,
                    )

            return generate_internal()

        # 성능 목적: 질문 재작성 시 대화 컨텍스트를 반영하지 않음
        rewritten_query = rewrite_query(
            base_url=self.valves.OLLAMA_BASE_URL,
            model=self.valves.REWRITE_MODEL,
            original_query=user_message,
            chat_history=[],
        )
        print(f"[Step 1] 재작성된 쿼리: {rewritten_query}")

        print(f"[Step 2] 벡터 검색 중... (top_k={self.valves.TOP_K})")
        documents = retrieve_documents(
            chroma_path=self.valves.CHROMA_PATH,
            collection_name=self.valves.CHROMA_COLLECTION,
            embedding_model=self.valves.EMBEDDING_MODEL,
            query=rewritten_query,
            top_k=self.valves.TOP_K,
            min_relevance_score=self.valves.MIN_RELEVANCE_SCORE,
        )
        print(f"[Step 2] 검색된 문서: {len(documents)}개")

        context_prompt = build_context_prompt(user_message, documents)

        prefix = ""
        if self.valves.SHOW_REWRITTEN_QUERY:
            prefix += f"> **재작성된 검색 쿼리:** `{rewritten_query}`\n\n"
        if self.valves.SHOW_SOURCES and documents:
            sources = ", ".join(sorted(set(d["source"] for d in documents)))
            prefix += f"> **참조 출처:** {sources}\n\n---\n\n"

        print(f"[Step 3] 답변 생성 중... (모델: {self.valves.ANSWER_MODEL})")
        system_message = (
            "당신은 친절하고 정확한 AI 어시스턴트입니다. 주어진 참고 문서를 바탕으로 답변하세요."
        )
        answer_messages = [
            {"role": "system", "content": system_message},
            *chat_history[-4:],  # 최근 2턴 유지
            {"role": "user", "content": context_prompt},
        ]

        def generate():
            if prefix:
                yield prefix
            yield from ollama_chat_stream(
                base_url=self.valves.OLLAMA_BASE_URL,
                model=self.valves.ANSWER_MODEL,
                messages=answer_messages,
            )

        return generate()

