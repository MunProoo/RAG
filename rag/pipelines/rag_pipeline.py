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


# ─────────────────────────────────────────
# 기본값 (환경변수로 override 가능)
# ─────────────────────────────────────────
DEFAULT_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_REWRITE_MODEL = os.getenv("REWRITE_MODEL", "qwen3:1.7b")
DEFAULT_ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen3:1.7b")

_DEFAULT_CHROMA_PATH = str(Path(__file__).resolve().parents[2] / "data" / "chroma_db")
DEFAULT_CHROMA_PATH = os.getenv("CHROMA_PATH", _DEFAULT_CHROMA_PATH)
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
            f"[문서 {i}] (출처: {doc['source']}, 관련도: {doc['score']})\n{doc['content']}"
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
- 출처를 인용할 때는 [문서 N] 형식을 사용하세요
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

        SHOW_SOURCES: bool = True
        SHOW_REWRITTEN_QUERY: bool = False

    def __init__(self):
        self.name = "Pipeline"
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

        focus = extract_query_focus(user_message)
        if focus:
            before = len(documents)
            documents = filter_documents_by_focus(
                documents, focus, self.valves.TOP_K
            )
            print(
                f"[Step 2b] 질문 초점: 「{focus}」 → 초점 포함 청크만 사용 "
                f"({before} → {len(documents)}개)"
            )

        context_prompt = build_context_prompt(user_message, documents, focus=focus)

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
            )

        return generate()

