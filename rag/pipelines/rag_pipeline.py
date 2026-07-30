"""
LLM → RAG → LLM Pipeline for Open WebUI
=========================================
동작 방식:
  1. LLM 1: 사용자 질문을 검색에 최적화된 쿼리로 재작성
  2. ChromaDB: 재작성된 쿼리로 관련 문서 청크 검색
  3. LLM 2: 검색 결과를 컨텍스트로 사용하여 최종 답변 생성 (스트리밍)
"""

import os
import re
import json
from pathlib import Path
from typing import List, Union, Generator, Iterator, Dict, Tuple, Optional

import requests
from pydantic import BaseModel

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi


# ─────────────────────────────────────────
# 기본값 (환경변수로 override 가능)
# ─────────────────────────────────────────
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_REWRITE_MODEL = os.getenv("REWRITE_MODEL", "qwen3:1.7b")
DEFAULT_ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen3:1.7b")

# Local default is rag/data/chroma_db; Docker overrides this with /app/chroma_db.
_DEFAULT_CHROMA_PATH = str(Path(__file__).resolve().parents[1] / "data" / "chroma_db")
DEFAULT_CHROMA_PATH = os.getenv("CHROMA_PATH", _DEFAULT_CHROMA_PATH)
DEFAULT_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "rag_documents")

DEFAULT_TOP_K = int(os.getenv("TOP_K", "5"))
DEFAULT_MIN_RELEVANCE_SCORE = float(os.getenv("MIN_SCORE", "0.3"))

# 한국어 사내 문서 기준 기본 임베딩 모델
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
DEFAULT_BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", str(Path(DEFAULT_CHROMA_PATH) / "bm25_index.json"))
DEFAULT_VECTOR_CANDIDATES = int(os.getenv("VECTOR_CANDIDATES", "20"))
DEFAULT_BM25_CANDIDATES = int(os.getenv("BM25_CANDIDATES", "20"))
DEFAULT_MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))
DEFAULT_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
DEFAULT_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "2048"))
DEFAULT_OLLAMA_READ_TIMEOUT = int(os.getenv("OLLAMA_READ_TIMEOUT", "600"))
DEFAULT_MAX_CHUNKS_PER_SOURCE = int(os.getenv("MAX_CHUNKS_PER_SOURCE", "2"))

# 리랭커(크로스 인코더): RRF 후보를 질문-본문 쌍으로 다시 채점해 정밀도를 올립니다.
# 모델 로드 실패(오프라인 등) 시 자동으로 RRF 순위를 그대로 사용합니다.
DEFAULT_RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() == "true"
DEFAULT_RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
DEFAULT_RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "20"))

# false면 LLM 재작성을 생략하고 원본 질문 + 규칙 기반 확장만 사용합니다(지연 감소).
DEFAULT_USE_QUERY_REWRITE = os.getenv("USE_QUERY_REWRITE", "true").lower() == "true"

# 후속 질문("그거 자세히", "해당 API 수정은?")을 감지하면 이전 대화를 반영해
# 독립형 질문으로 바꾼 뒤 검색합니다. 감지될 때만 LLM을 추가 호출합니다.
DEFAULT_CONTEXTUALIZE_FOLLOW_UP = os.getenv("CONTEXTUALIZE_FOLLOW_UP", "true").lower() == "true"

FOLLOW_UP_MARKERS = (
    "그거", "그것", "이거", "그건", "이건", "저거", "그중", "그 중",
    "해당", "위에", "위의", "방금", "아까", "앞서", "그럼", "그러면",
    "그 api", "이 api", "그 방법", "이 방법", "더 자세히", "자세히 좀",
    "예시", "예제", "다른 것도", "나머지",
)

DOCUMENT_TYPE_TERMS = {
    "protocol": ("protocol", "프로토콜", "패킷", "packet", "명령 구분", "param3"),
    "install": ("설치", "install", "nsis", "빌드", "package"),
    "user_guide": ("user guide", "사용자 가이드", "사용법", "매뉴얼"),
}
PRODUCT_TERMS = {
    "alpeta": ("alpeta", "알페타"),
}
CURRENT_PROTOCOL_TERMS = ("신규", "최신", "새 프로토콜", "new protocol", "v4", "4.0")
LEGACY_PROTOCOL_TERMS = ("구형", "기존 프로토콜", "legacy", "v1", "1.0")


# ─────────────────────────────────────────
# Open WebUI 내부 작업 감지
# ─────────────────────────────────────────
def is_openwebui_internal_task(user_message: str) -> bool:
    """
    Open WebUI가 채팅 UX를 위해 추가로 호출하는 내부 작업 프롬프트를 감지합니다.
    (후속 질문/제목/태그 생성 등)
    """
    # `### Chat History:`만으로 판별하면 오탐 위험이 커서,
    # 실제 내부 작업은 보통 첫 줄이 `### Task:`로 시작합니다.
    for line in (user_message or "").splitlines():
        s = line.strip()
        if not s:
            continue
        return s.startswith("### Task:")
    return False


def extract_query_focus(query: str) -> Optional[str]:
    """
    질문에서 '누구/무엇에 대해' 형태의 핵심 대상(고유명사)을 추출합니다.
    추출 실패 시 None.
    """
    q = (query or "").strip()
    if not q:
        return None
    patterns = [
        r"^(.{2,40}?)\s*(?:에\s*대해|에\s*관해|에\s*대해서|대해\s*설명|대해\s*알려|에\s*대해\s*알려|에\s*대해\s*설명)",
        r"^(.{2,40}?)\s*(?:을|를)\s*(?:소개|설명|알려)",
        r"^(.{2,40}?)\s*(?:은|는|이|가)\s*(?:누구|무엇|어떤|어떻게)",
    ]
    for pat in patterns:
        m = re.match(pat, q)
        if m:
            s = m.group(1).strip()
            if len(s) >= 2:
                return s
    return None


def filter_documents_by_focus(
    documents: list,
    focus: Optional[str],
    top_k: int,
) -> list:
    """질문 초점 문자열이 본문에 등장하는 청크만 남깁니다(없으면 원본 유지)."""
    if not documents or not focus or len(focus) < 2:
        return documents
    filtered = [d for d in documents if focus in (d.get("content") or "")]
    if not filtered:
        return documents
    filtered = sorted(filtered, key=lambda x: x.get("score", 0), reverse=True)
    return filtered[:top_k]


def detect_retrieval_scope(query: str) -> Dict[str, str]:
    """Infer only deterministic document constraints from a user question.

    Document type must be applied before retrieval.  Filtering only after global
    top-k search is too late because a common product keyword can crowd out the
    desired document type completely.
    """
    normalized = (query or "").casefold()
    scope: Dict[str, str] = {}
    for document_type, terms in DOCUMENT_TYPE_TERMS.items():
        if any(term.casefold() in normalized for term in terms):
            scope["document_type"] = document_type
            break
    for product, terms in PRODUCT_TERMS.items():
        if any(term.casefold() in normalized for term in terms):
            scope["product"] = product
            break
    if scope.get("document_type") == "protocol":
        if any(term.casefold() in normalized for term in CURRENT_PROTOCOL_TERMS):
            scope["protocol_generation"] = "current"
        elif any(term.casefold() in normalized for term in LEGACY_PROTOCOL_TERMS):
            scope["protocol_generation"] = "legacy"
    return scope


def expand_retrieval_query(original_query: str, rewritten_query: str) -> str:
    """Add deterministic domain synonyms that the rewrite LLM may miss."""
    original = (original_query or "").casefold()
    expansions = []
    if "내려" in original or "내리" in original:
        expansions.append("설정 전송 Server Terminal 서버 단말기 배포 적용 Request")
    if "출입그룹" in original or "출입 그룹" in original:
        expansions.append("출입그룹 출입 그룹 access group Door 설정 전송")
    if any(term.casefold() in original for term in CURRENT_PROTOCOL_TERMS):
        expansions.append("신규 프로토콜 v4.0 current Communication protocol for Terminal")
    lines = [line.strip() for line in (rewritten_query or "").splitlines() if line.strip()]
    lines.extend(expansions)
    return "\n".join(dict.fromkeys(lines))


def _chroma_where(scope: Optional[Dict[str, str]]) -> Optional[dict]:
    if not scope:
        return None
    conditions = [{key: value} for key, value in scope.items()]
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


def _metadata_matches_scope(metadata: Optional[dict], scope: Optional[Dict[str, str]]) -> bool:
    return not scope or all((metadata or {}).get(key) == value for key, value in scope.items())


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
    options: Optional[dict] = None,
    read_timeout: int = DEFAULT_OLLAMA_READ_TIMEOUT,
) -> str:
    """Ollama chat API를 호출합니다."""
    url = f"{base_url}/api/chat"
    # 일부 Ollama 모델은 think/thinking 옵션을 지원합니다.
    # Open WebUI/RAG 응답에서 사고과정 노출을 피하기 위해 기본적으로 think=false를 전달합니다.
    payload = {"model": model, "messages": messages, "stream": stream, "think": False}
    if options:
        payload["options"] = options
    response = requests.post(url, json=payload, timeout=(10, read_timeout))
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def ollama_chat_stream(
    base_url: str,
    model: str,
    messages: list,
    options: Optional[dict] = None,
    read_timeout: int = DEFAULT_OLLAMA_READ_TIMEOUT,
) -> Generator[str, None, None]:
    """Ollama chat API 스트리밍 버전."""
    url = f"{base_url}/api/chat"
    payload = {"model": model, "messages": messages, "stream": True, "think": False}
    if options:
        payload["options"] = options
    with requests.post(url, json=payload, stream=True, timeout=(10, read_timeout)) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("done", False):
                print(
                    "[RAG] Ollama stream completed: "
                    f"reason={data.get('done_reason', 'unknown')}, "
                    f"prompt_tokens={data.get('prompt_eval_count', 'unknown')}, "
                    f"generated_tokens={data.get('eval_count', 'unknown')}"
                )
                break
            else:
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
# Step 0: 후속 질문 문맥화 (Question Condensing)
# ─────────────────────────────────────────
def is_follow_up_question(query: str, chat_history: list) -> bool:
    """이전 대화 없이는 이해하기 어려운 후속 질문인지 감지합니다.

    검색은 현재 질문 문자열만 사용하므로, 지시어("그거", "해당")나 아주 짧은
    질문("왜?", "예시는?")은 문맥을 되살려 주지 않으면 검색이 실패합니다.
    """
    if not chat_history:
        return False
    q = (query or "").strip()
    if not q:
        return False
    normalized = q.casefold()
    if any(marker in normalized for marker in FOLLOW_UP_MARKERS):
        return True
    return len(q) <= 12


def _compact_history(chat_history: list, max_turns: int = 4, max_chars: int = 500) -> str:
    """문맥화 프롬프트용으로 최근 대화를 압축합니다(이미지 마크다운 제거)."""
    lines = []
    for message in chat_history[-max_turns:]:
        role = message.get("role", "")
        if role not in ("user", "assistant"):
            continue
        content = re.sub(r"!\[[^\]]*\]\([^)\s]+\)", "", str(message.get("content", ""))).strip()
        if not content:
            continue
        if len(content) > max_chars:
            content = content[:max_chars] + "…"
        lines.append(f"{'사용자' if role == 'user' else '어시스턴트'}: {content}")
    return "\n".join(lines)


def condense_question(
    base_url: str,
    model: str,
    question: str,
    chat_history: list,
) -> str:
    """최근 대화를 반영해 혼자 봐도 이해되는 독립형 질문으로 다시 씁니다.

    실패하거나 결과가 이상하면(빈 값·과도한 길이) 원본 질문으로 폴백합니다.
    """
    history_text = _compact_history(chat_history)
    if not history_text:
        return question

    system_prompt = """당신은 대화 문맥을 반영해 질문을 완성하는 전문가입니다.
최근 대화를 참고해, 마지막 질문을 혼자 봐도 이해되는 완전한 질문 한 문장으로 다시 쓰세요.

규칙(매우 중요):
- 출력은 완성된 질문 한 줄만. 설명/머리말/따옴표/마크다운 금지.
- 지시어("그거", "해당", "위에서" 등)를 대화에 나온 실제 대상으로 바꾸세요.
- 고유명사(제품명/API명/스키마명/파일명)는 원문 표기를 그대로 보존하고, 대화에 없는 정보를 지어내지 마세요.
- 마지막 질문이 이전 대화와 무관하면 마지막 질문을 그대로 출력하세요."""

    user_message = f"""최근 대화:
{history_text}

마지막 질문: {question}

완성된 질문:"""

    try:
        condensed = ollama_chat(
            base_url,
            model,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=False,
        )
    except Exception as exc:
        print(f"[RAG] 질문 문맥화 실패, 원본 질문 사용: {exc}")
        return question

    condensed = next((line.strip() for line in condensed.splitlines() if line.strip()), "")
    if not condensed or len(condensed) > 300:
        return question
    return condensed


# ─────────────────────────────────────────
# Step 2: 벡터 검색 (RAG)
# ─────────────────────────────────────────
def retrieve_vector_documents(
    chroma_path: str,
    collection_name: str,
    embedding_model: str,
    query: str,
    top_k: int,
    min_relevance_score: float,
    scope: Optional[Dict[str, str]] = None,
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
        query_args = {
            "query_texts": queries,
            "n_results": actual_k,
            "include": ["documents", "metadatas", "distances"],
        }
        where = _chroma_where(scope)
        if where:
            query_args["where"] = where
        results = collection.query(**query_args)

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
                        "metadata": meta or {},
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
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)\s]+\)")


def extract_markdown_images(text: str) -> List[str]:
    """본문에서 Markdown 이미지 문법 `![...](url)` 줄만 추출합니다."""
    if not text:
        return []
    found = _MD_IMAGE.findall(text)
    # 순서 유지 중복 제거
    seen: set[str] = set()
    out: List[str] = []
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def extract_images_for_focus(content: str, focus: str) -> List[str]:
    """
    질문 초점(예: 인명)에 해당하는 구간의 이미지만 추출합니다.
    - `## 방인재` ~ 다음 `##` 전까지(Markdown)
    - 또는 본문에서 focus 첫 등장 이후 일정 길이(플레인 텍스트 대비)
    """
    if not content or not focus:
        return []

    sec = re.search(
        rf"(?:^|\n)##\s*{re.escape(focus)}(?:[^\n]*)\n([\s\S]*?)(?=\n##\s|\Z)",
        content,
    )
    if sec:
        return extract_markdown_images(sec.group(1))

    if focus not in content:
        return []
    i = content.find(focus)
    window = content[i : i + 2000]
    return extract_markdown_images(window)


def collect_mandatory_image_lines(documents: list, focus: Optional[str]) -> List[str]:
    """검색된 청크에서 답변에 실을 이미지 마크다운 줄을 수집합니다."""
    lines: List[str] = []
    seen: set[str] = set()
    for doc in documents:
        body = doc.get("content") or ""
        imgs = extract_images_for_focus(body, focus) if focus else extract_markdown_images(body)
        for im in imgs:
            if im not in seen:
                seen.add(im)
                lines.append(im)
    return lines


def format_mandatory_image_block(lines: List[str]) -> str:
    """이미지 줄이 있을 때만 별도 블록 문자열을 만듭니다."""
    if not lines:
        return ""
    body = "\n".join(lines)
    return f"""
=== 답변 상단에 둘 이미지(참고 문서에 실제로 존재, 수정·요약 금지) ===
{body}
(이 블록이 있을 때만 해당:
  1) **당신이 출력하는 텍스트의 맨 처음**에 위 이미지 마크다운을 **그대로** 두세요. (그 위에 불릿·문장·소제목 금지)
  2) 이미지 다음에 빈 줄 한 줄 후 설명·불릿을 이어가세요.)
"""


def build_context_prompt(
    query: str,
    documents: list,
    focus: Optional[str] = None,
) -> str:
    """검색된 문서를 컨텍스트로 포함한 프롬프트를 생성합니다."""
    if not documents:
        return query

    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[참고 {i}] 출처 파일: `{doc['source']}` · 관련도: {doc['score']}\n{doc['content']}"
        )

    context_str = "\n\n".join(context_parts)
    image_lines = collect_mandatory_image_lines(documents, focus)
    image_block = format_mandatory_image_block(image_lines)
    has_images = bool(image_lines)

    if has_images:
        image_rules = """- 위 `=== 답변 상단에 둘 이미지 ===` 블록이 있을 때만: 답변 본문 **첫 출력**을 그 이미지 마크다운으로 시작하고, 그 아래에만 설명·불릿을 쓰세요. 블록에 있는 URL/대체텍스트는 바꾸지 마세요."""
    else:
        image_rules = """- 위에 이미지 블록이 **없으면** 참고 문서에 추출된 `![...](URL)` 이미지가 없는 것입니다. 이미지 마크다운이나 URL을 **지어내지 마세요**. 사용자가 사진·도식을 물었을 때만 "검색된 문서에는 관련 이미지가 없습니다"처럼 **한 문장**으로만 답하고, 그 외에는 이미지 유무를 길게 언급하지 마세요."""

    scope_block = ""
    if focus:
        scope_block = f"""
=== 답변 범위(필수) ===
- 사용자 질문의 핵심 대상은 「{focus}」입니다.
- 「{focus}」와 **직접 해당하는 문장·불릿·표 항목**만 근거로 답하세요.
- 같은 파일에 다른 사람·다른 주제가 있어도, **이름·별명·사진·소속을 들먹이거나 설명하지 마세요.** (질문에 없는 인물/항목은 무시)
- 참고 문서에 「{focus}」가 거의 없으면 한두 문장으로만 답하고, 다른 문서로 빗겨가지 마세요.
"""
    return f"""다음 참고 문서들을 바탕으로 질문에 답변하세요.

=== 참고 문서 ===
{context_str}
{image_block}
=== 질문 ===
{query}
{scope_block}
=== 답변 지침 ===
- 참고 문서의 내용을 기반으로 답변하세요
- 명확하고 구조적으로 답변하세요
- **금지(매우 중요)**: "제공된 참고 문서에는 … 포함되어 있지 않습니다/명시되어 있지 않습니다", "문서에는 … 에 대한 정보가 없습니다" 같은 **장황한 면책·부정 문단**을 쓰지 마세요. 문서에 없는 세부는 **굳이 나열하지 말고 생략**하거나, 꼭 필요할 때만 한 문장으로 짧게 처리하세요.
- 질문에 답하는 데 필요한 사실만 말하세요. 없는 내용을 억지로 채우지 마세요.
{image_rules}"""


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
        BM25_INDEX_PATH: str = DEFAULT_BM25_INDEX_PATH
        VECTOR_CANDIDATES: int = DEFAULT_VECTOR_CANDIDATES
        BM25_CANDIDATES: int = DEFAULT_BM25_CANDIDATES
        MAX_CONTEXT_CHARS: int = DEFAULT_MAX_CONTEXT_CHARS
        NUM_CTX: int = DEFAULT_NUM_CTX
        NUM_PREDICT: int = DEFAULT_NUM_PREDICT
        OLLAMA_READ_TIMEOUT: int = DEFAULT_OLLAMA_READ_TIMEOUT
        MAX_CHUNKS_PER_SOURCE: int = DEFAULT_MAX_CHUNKS_PER_SOURCE

        RERANK_ENABLED: bool = DEFAULT_RERANK_ENABLED
        RERANK_MODEL: str = DEFAULT_RERANK_MODEL
        RERANK_CANDIDATES: int = DEFAULT_RERANK_CANDIDATES
        USE_QUERY_REWRITE: bool = DEFAULT_USE_QUERY_REWRITE
        CONTEXTUALIZE_FOLLOW_UP: bool = DEFAULT_CONTEXTUALIZE_FOLLOW_UP

        SHOW_SOURCES: bool = True
        SHOW_REWRITTEN_QUERY: bool = False

    def __init__(self):
        self.name = "도우미"
        self.valves = self.Valves()

    def answer_options(self) -> dict:
        return {"num_ctx": self.valves.NUM_CTX, "num_predict": self.valves.NUM_PREDICT}

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
                "[Pipeline] 힌트: 호스트의 `rag/data/chroma_db`(컨테이너 기준 `/app/chroma_db`)를 삭제(완전 초기화)한 뒤 "
                "indexer로 재인덱싱하고, `pipelines`/`indexer`의 chromadb 버전이 동일한지 확인하세요."
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
                        options=self.answer_options(),
                        read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
                    )
                else:
                    yield ollama_chat(
                        base_url=self.valves.OLLAMA_BASE_URL,
                        model=self.valves.ANSWER_MODEL,
                        messages=messages,
                        stream=False,
                        options=self.answer_options(),
                        read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
                    )

            return generate_internal()

        # Step 0: 후속 질문이면 이전 대화를 반영해 독립형 질문으로 변환.
        # 검색·범위 필터·초점 추출은 전부 이 질문 기준으로 동작합니다.
        retrieval_question = user_message
        if self.valves.CONTEXTUALIZE_FOLLOW_UP and is_follow_up_question(user_message, chat_history):
            retrieval_question = condense_question(
                base_url=self.valves.OLLAMA_BASE_URL,
                model=self.valves.REWRITE_MODEL,
                question=user_message,
                chat_history=chat_history,
            )
            if retrieval_question != user_message:
                print(f"[Step 0] 후속 질문 감지 → 문맥 반영 질문: {retrieval_question}")

        # 성능 목적: 질문 재작성 시 대화 컨텍스트를 반영하지 않음(문맥은 Step 0에서 반영됨)
        if self.valves.USE_QUERY_REWRITE:
            rewritten_query = rewrite_query(
                base_url=self.valves.OLLAMA_BASE_URL,
                model=self.valves.REWRITE_MODEL,
                original_query=retrieval_question,
                chat_history=[],
            )
        else:
            rewritten_query = retrieval_question
        rewritten_query = expand_retrieval_query(retrieval_question, rewritten_query)
        print(f"[Step 1] 재작성된 쿼리: {rewritten_query}")

        scope = detect_retrieval_scope(retrieval_question)
        print(f"[Step 2] 검색 중... (top_k={self.valves.TOP_K}, scope={scope or 'none'})")
        documents = retrieve_documents(
            chroma_path=self.valves.CHROMA_PATH,
            collection_name=self.valves.CHROMA_COLLECTION,
            embedding_model=self.valves.EMBEDDING_MODEL,
            query=rewritten_query,
            top_k=self.valves.TOP_K,
            min_relevance_score=self.valves.MIN_RELEVANCE_SCORE,
            bm25_index_path=self.valves.BM25_INDEX_PATH,
            vector_candidates=self.valves.VECTOR_CANDIDATES,
            bm25_candidates=self.valves.BM25_CANDIDATES,
            scope=scope,
            max_chunks_per_source=self.valves.MAX_CHUNKS_PER_SOURCE,
            rerank_enabled=self.valves.RERANK_ENABLED,
            rerank_model=self.valves.RERANK_MODEL,
            rerank_candidates=self.valves.RERANK_CANDIDATES,
            # 리랭커는 재작성 변형이 아닌 (문맥 반영된) 질문과의 적합도를 봐야 합니다.
            rerank_query=retrieval_question,
        )
        print(f"[Step 2] 검색된 문서: {len(documents)}개")

        focus = extract_query_focus(retrieval_question)
        if focus:
            before = len(documents)
            documents = filter_documents_by_focus(
                documents, focus, self.valves.TOP_K
            )
            print(
                f"[Step 2b] 질문 초점: 「{focus}」 → 초점 포함 청크만 사용 "
                f"({before} → {len(documents)}개)"
            )

        documents = limit_documents_for_context(documents, self.valves.MAX_CONTEXT_CHARS)
        print(f"[Step 2c] 답변 컨텍스트: {len(documents)}개 청크, 최대 {self.valves.MAX_CONTEXT_CHARS}자")

        # 답변 프롬프트에도 문맥 반영 질문을 사용합니다. ("그거 자세히"보다 명확)
        # 이전 대화는 answer_messages의 chat_history로 별도 전달됩니다.
        context_prompt = build_context_prompt(retrieval_question, documents, focus=focus)

        prefix = ""
        if self.valves.SHOW_REWRITTEN_QUERY:
            prefix += f"> **재작성된 검색 쿼리:** `{rewritten_query}`\n\n"
        if self.valves.SHOW_SOURCES and documents:
            sources = ", ".join(sorted(set(d["source"] for d in documents)))
            prefix += f"> **참조 출처:** {sources}\n\n---\n\n"

        print(f"[Step 3] 답변 생성 중... (모델: {self.valves.ANSWER_MODEL})")
        system_message = (
            "당신은 친절하고 정확한 AI 어시스턴트입니다. 주어진 참고 문서를 바탕으로 답변하세요. "
            "이전 대화에 나온 다른 인물·추측은 무시하고, 이번 사용자 질문과 참고 문서만 따르세요. "
            "질문에 특정 인물·주제가 있으면 그 범위를 벗어난 인물 이름·설명을 쓰지 마세요. "
            "답변 말미에 '문서에는 … 없습니다' 식의 긴 면책 문장을 반복하지 마세요."
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
                options=self.answer_options(),
                read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
            )

        return generate()


# Hybrid retrieval is intentionally kept here because the pipeline container only
# mounts this directory. The indexer writes bm25_index.json beside ChromaDB.
def _bm25_tokens(text: str) -> list:
    """Language-neutral tokenization: Korean syllable runs, words, numbers and codes."""
    return re.findall(r"[\uac00-\ud7a3]+|[A-Za-z0-9][A-Za-z0-9_./:-]*", (text or "").lower())


def _load_bm25_records(index_path: str) -> list:
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError) as exc:
        print(f"[RAG] BM25 index unavailable ({index_path}): {exc}")
        return []


# 질문마다 JSON 파싱 + BM25 재구축을 반복하면 문서가 늘수록 응답이 느려집니다.
# 인덱스 파일 mtime이 같으면 프로세스 내 캐시를 재사용합니다(재인덱싱 시 자동 갱신).
_BM25_CACHE: dict = {"path": None, "mtime": None, "records": [], "bm25": None}


def _get_bm25_index(index_path: str) -> Tuple[list, Optional[object]]:
    try:
        mtime = os.path.getmtime(index_path)
    except OSError:
        return [], None
    if _BM25_CACHE["path"] == index_path and _BM25_CACHE["mtime"] == mtime:
        return _BM25_CACHE["records"], _BM25_CACHE["bm25"]
    records = _load_bm25_records(index_path)
    corpus = [_bm25_tokens(record.get("document", "")) for record in records]
    bm25 = BM25Okapi(corpus) if records and any(corpus) else None
    _BM25_CACHE.update({"path": index_path, "mtime": mtime, "records": records, "bm25": bm25})
    if records:
        print(f"[RAG] BM25 index loaded and cached: {len(records)} chunks")
    return records, bm25


_RERANKER_CACHE: dict = {"model_name": None, "model": None}


def _get_reranker(model_name: str):
    if _RERANKER_CACHE["model_name"] == model_name:
        return _RERANKER_CACHE["model"]
    model = None
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(model_name)
        print(f"[RAG] Reranker loaded: {model_name}")
    except Exception as exc:
        print(f"[RAG] Reranker unavailable ({model_name}), falling back to RRF order: {exc}")
    _RERANKER_CACHE.update({"model_name": model_name, "model": model})
    return model


def rerank_documents(query: str, documents: list, model_name: str, top_k: int) -> list:
    """크로스 인코더로 (질문, 청크) 쌍을 재채점합니다. 모델이 없으면 입력 순서 유지."""
    if len(documents) <= 1:
        return documents[:top_k]
    model = _get_reranker(model_name)
    if model is None:
        return documents[:top_k]
    question = next((line.strip() for line in (query or "").splitlines() if line.strip()), query)
    try:
        scores = model.predict([(question, doc.get("content", "")) for doc in documents])
    except Exception as exc:
        print(f"[RAG] Rerank failed, falling back to RRF order: {exc}")
        return documents[:top_k]
    ranked = sorted(zip(documents, scores), key=lambda pair: float(pair[1]), reverse=True)
    return [{**doc, "rerank_score": round(float(score), 4)} for doc, score in ranked[:top_k]]


def _rrf_merge(vector_docs: list, bm25_docs: list, top_k: int, k: int = 60) -> list:
    merged = {}
    for rank, doc in enumerate(vector_docs, 1):
        key = (doc.get("source", "unknown"), doc.get("content", ""))
        item = merged.setdefault(key, {**doc, "score": 0.0})
        item["score"] += 1 / (k + rank)
    for rank, doc in enumerate(bm25_docs, 1):
        key = (doc.get("source", "unknown"), doc.get("content", ""))
        item = merged.setdefault(key, {**doc, "score": 0.0})
        item["score"] += 1 / (k + rank)
    return [{**doc, "score": round(doc["score"], 4)}
            for doc in sorted(merged.values(), key=lambda item: item["score"], reverse=True)[:top_k]]


def limit_documents_per_source(documents: list, top_k: int, max_chunks_per_source: int) -> list:
    """Avoid letting many adjacent chunks from one broad document crowd out others."""
    counts: Dict[str, int] = {}
    selected = []
    for document in documents:
        source = document.get("source", "unknown")
        if counts.get(source, 0) >= max_chunks_per_source:
            continue
        counts[source] = counts.get(source, 0) + 1
        selected.append(document)
        if len(selected) >= top_k:
            break
    return selected


def limit_documents_for_context(documents: list, max_context_chars: int) -> list:
    """Keep only complete chunks that fit the answer model's input budget."""
    selected, used = [], 0
    for document in documents:
        size = len(document.get("content", ""))
        if selected and used + size > max_context_chars:
            continue
        if size > max_context_chars:
            continue
        selected.append(document)
        used += size
    return selected


def retrieve_documents(
    chroma_path: str,
    collection_name: str,
    embedding_model: str,
    query: str,
    top_k: int,
    min_relevance_score: float,
    bm25_index_path: str = DEFAULT_BM25_INDEX_PATH,
    vector_candidates: int = DEFAULT_VECTOR_CANDIDATES,
    bm25_candidates: int = DEFAULT_BM25_CANDIDATES,
    scope: Optional[Dict[str, str]] = None,
    max_chunks_per_source: int = DEFAULT_MAX_CHUNKS_PER_SOURCE,
    rerank_enabled: bool = False,
    rerank_model: str = DEFAULT_RERANK_MODEL,
    rerank_candidates: int = DEFAULT_RERANK_CANDIDATES,
    rerank_query: Optional[str] = None,
) -> list:
    """Fuse dense BGE-M3 and exact-keyword BM25 rankings with RRF, then rerank."""
    candidate_count = max(top_k, vector_candidates, rerank_candidates if rerank_enabled else 0)

    def _finalize(candidates: list) -> list:
        if rerank_enabled:
            candidates = rerank_documents(rerank_query or query, candidates, rerank_model, candidate_count)
        return limit_documents_per_source(candidates, top_k, max_chunks_per_source)

    vector_docs = retrieve_vector_documents(
        chroma_path, collection_name, embedding_model, query,
        candidate_count, min_relevance_score, scope,
    )
    records, bm25 = _get_bm25_index(bm25_index_path)
    if not records or bm25 is None:
        return _finalize(vector_docs)
    allowed = [index for index, record in enumerate(records)
               if _metadata_matches_scope(record.get("metadata"), scope)]
    if not allowed:
        print(f"[RAG] No documents matched required scope: {scope}")
        return []
    scores = [0.0] * len(records)
    for query_variant in [q for q in query.splitlines() if q.strip()]:
        for index, score in enumerate(bm25.get_scores(_bm25_tokens(query_variant))):
            scores[index] = max(scores[index], float(score))
    ranked = sorted(allowed, key=lambda index: scores[index], reverse=True)
    bm25_docs = []
    for index in ranked[:bm25_candidates]:
        if scores[index] <= 0:
            continue
        record = records[index]
        metadata = record.get("metadata") or {}
        bm25_docs.append({"content": record.get("document", ""), "source": metadata.get("source", "unknown"), "score": scores[index], "metadata": metadata})
    merged = _rrf_merge(vector_docs, bm25_docs, candidate_count)
    return _finalize(merged)

