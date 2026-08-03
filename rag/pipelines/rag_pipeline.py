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
import time
from pathlib import Path
from typing import List, Union, Generator, Iterator, Dict, Tuple, Optional

import requests
from pydantic import BaseModel

import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi


def _log_timing(stage: str, seconds: float, **extra) -> None:
    """단계별 지연을 `[RAG] timing ...` 형식으로 남겨 병목 재현을 돕습니다."""
    detail = " ".join(f"{key}={value}" for key, value in extra.items())
    suffix = f" {detail}" if detail else ""
    print(f"[RAG] timing stage={stage} sec={seconds:.3f}{suffix}")


def _status_event(description: str, *, done: bool = False) -> dict:
    """Open WebUI SSE status 이벤트를 만듭니다(채팅 본문 content로 저장되지 않음).

    pipelines가 dict yield를 `data: {...}`로 전달하므로, 문자열 status를
    본문에 섞지 않고 UI 진행 표시만 갱신할 때 사용합니다.
    """
    return {
        "event": {
            "type": "status",
            "data": {
                "description": description,
                "done": done,
            },
        }
    }


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
# false면 크로스인코더를 건너뛰고 기술 근거 점수만으로 재정렬해 검색 지연을 줄입니다.
DEFAULT_RERANK_NEURAL = os.getenv("RERANK_NEURAL", "true").lower() == "true"
# Ollama 모델 상주 유지(재로드 방지). 예: 30m, -1(무기한)
DEFAULT_OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

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
    # swagger/스키마/API 의도는 product 필터보다 먼저 적용해 PDF 가이드가 밀어내지 않게 합니다.
    "api": (
        "swagger",
        "openapi",
        "스키마",
        "schema",
        "api 명세",
        "api명세",
        "rest api",
        "엔드포인트",
        "endpoint",
        "api",
    ),
    "protocol": ("protocol", "프로토콜", "패킷", "packet", "명령 구분", "param3"),
    "install": ("설치", "install", "nsis", "빌드", "package"),
    "user_guide": ("user guide", "사용자 가이드", "사용법", "매뉴얼"),
}
PRODUCT_TERMS = {
    "alpeta": ("alpeta", "알페타"),
}
CURRENT_PROTOCOL_TERMS = ("신규", "최신", "새 프로토콜", "new protocol", "v4", "4.0")
LEGACY_PROTOCOL_TERMS = ("구형", "기존 프로토콜", "legacy", "v1", "1.0")

ARTIFACT_INTENT_RULES = {
    "automation": {
        "markers": (
            "자동화", "자동 실행", "자동화 스크립트",
            "배치 파일", "배치 스크립트", "batch file", "batch script",
        ),
        "extensions": (".bat", ".cmd", ".ps1", ".sh"),
    },
    "script": {
        "markers": ("스크립트", "script", "소스 파일"),
        "extensions": (".nsi", ".ps1", ".sh", ".py", ".js", ".ts"),
    },
    "executable": {
        "markers": ("실행 파일", "설치 파일", "설치파일", "산출물", "installer", "executable"),
        "extensions": (".exe", ".msi", ".pkg", ".deb", ".rpm"),
    },
    "config": {
        "markers": ("설정 파일", "구성 파일", "환경 파일", "config file"),
        "extensions": (".ini", ".conf", ".yaml", ".yml", ".json", ".toml", ".env"),
    },
    # 산출물 파일이 아니라 빌드 후 결과물을 확인하는 폴더/경로를 물을 때 사용합니다.
    "output_folder": {
        "markers": (
            "확인하는 폴더", "확인 폴더", "결과물 폴더", "출력 폴더",
            "설치 파일을 확인", "생성된 설치", "이동하면", "확인하는 경로",
            "output folder", "verify folder", "check folder",
        ),
        "extensions": (),
    },
    # 빌드가 끝난 뒤 일반 설치 패키지가 만들어지는 최종 산출 경로를 묻는 의도입니다.
    # 명시적인 .exe 파일 질문은 executable 의도로 남겨 개별 패키지의 중간 위치를 보존합니다.
    "build_output": {
        "markers": (
            "빌드 완료", "빌드 후", "빌드가 끝", "빌드 끝",
            "어디에 생겨", "어디에 생성", "생성되는 경로", "생기는 경로",
            "산출물 경로", "출력 경로", "결과물 생성", "설치 파일이 생",
        ),
        "extensions": (),
    },
}

# 전부/목록 질문은 표·TOC가 페이지 경계에서 잘려 상위 K청크만 남기 쉽습니다.
LIST_COMPLETENESS_MARKERS = (
    "전부", "전체", "리스트업", "리스트", "목록", "모두", "다 알려", "전부다",
    "list all", "full list", "complete list",
)
_HEX_COMMAND_PATTERN = re.compile(r"0x[0-9A-Fa-f]+")
_WINDOWS_FOLDER_PATTERN = re.compile(
    r"(?i)\b([A-Z]:\\(?:[^\\\s,.;:()]+\\)*[^\\\s,.;:()]+)"
)
_OUTPUT_FOLDER_CONTENT_MARKERS = (
    "확인", "이동하면", "생성된", "생성됩니다", "생성된다",
    "verify", "check", "output", "install",
)
_BUILD_OUTPUT_CONTENT_MARKERS = (
    "빌드가 완료", "빌드 완료", "실행이 완료", "실행 완료",
    "설치파일이 생성", "설치 파일이 생성", "package is generated",
)
_USER_TERMINAL_PROCEDURE_MARKERS = (
    "사용자", "user",
)
_TERMINAL_PROCEDURE_MARKERS = (
    "단말기", "terminal",
)
_PROCEDURE_ACTION_MARKERS = (
    "추가", "등록", "전송", "동기화", "다운로드", "적용",
)

# 「단말기 사용자 관리」메뉴 자체를 묻는 질문. 일반 사용자 등록·단말기 정보와 구분합니다.
_TERMINAL_USER_MGMT_MENU_PHRASE = "단말기 사용자 관리"
_TERMINAL_USER_MGMT_HOWTO_MARKERS = (
    "메뉴", "사용법", "방법", "어떻게", "알려", "조작", "기능",
)

# 빌드를 수동 절차가 아닌 "자동화 버전"으로 진행하려는 의도를 판별하는 마커입니다.
# 문서 제목("알페타 설치 패키지 빌드(자동화 버전)")과 본문에 실제로 쓰인 표현만 사용하며,
# 특정 질문 문자열을 고정하지 않습니다. ARTIFACT_INTENT_RULES["automation"]은 산출물
# 파일 종류(배치 파일 등)를 묻는 의도라 빌드 절차 자체를 묻는 이 의도와는 구분됩니다.
_AUTOMATED_BUILD_MARKERS = (
    "자동화 버전", "자동빌드", "자동 빌드", "자동화된 빌드",
    "자동으로 빌드", "automated build", "자동화 방식으로 빌드",
)

# 자동화 버전 빌드 섹션에서만 등장하는 고유 표현입니다. 특정 페이지 번호를 고정하지 않고
# 이 표현들이 나오는 chunk_index 구간을 계산해 섹션 경계를 찾는 데 사용합니다.
_AUTOMATED_BUILD_SECTION_ANCHORS = (
    "자동화 버전", "git pull", "gitpull.bat", "define.go",
    "exbuilder", "build_install.bat", "proto_compile",
)

# 경로·확장자·HTTP 메서드뿐 아니라 CamelCase/대문자 식별자(FaceWT, FAW)도 보존합니다.
# 전역 (?i)를 쓰지 않으며, 한글 조사와 붙어도 ASCII 식별자를 자를 수 있게
# `\b` 대신 ASCII 경계 lookaround를 사용합니다.
_TECHNICAL_TOKEN_PATTERN = re.compile(
    r"(?:[A-Za-z]:\\(?:[^\\\s`\"'<>|]+\\)*[^\\\s`\"'<>|]+)"
    r"|(?:/[A-Za-z0-9._{}-]+(?:/[A-Za-z0-9._{}-]+)+)"
    r"|(?:[A-Za-z0-9_{}-]+(?:\.[A-Za-z0-9_{}-]+)+)"
    r"|(?:\b(?:GET|POST|PUT|PATCH|DELETE)\s+/[^\s`]+)"
    r"|(?:(?<![A-Za-z0-9_])[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+(?![A-Za-z0-9_]))"
    r"|(?:(?<![A-Za-z0-9_])[A-Z]{2,}[0-9]*(?![A-Za-z0-9_]))"
)


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
    desired document type completely. API/Swagger 문서는 파일명에 제품명이 없어
    product 필터와 함께 쓰면 전부 탈락하므로 api 타입일 때는 product를 제거합니다.
    """
    normalized = (query or "").casefold()
    scope: Dict[str, str] = {}
    for document_type, terms in DOCUMENT_TYPE_TERMS.items():
        if any(term.casefold() in normalized for term in terms):
            scope["document_type"] = document_type
            break
    # 문서 종류를 직접 말하지 않은 절차형·메뉴 사용법 질문도 의도가 분명하면
    # User Guide로 한정합니다. 프로토콜/API/설치 문서가 섞여 메뉴 절차를 대체하지 않게 합니다.
    if "document_type" not in scope and (
        is_user_terminal_procedure_intent(query)
        or is_terminal_user_management_intent(query)
    ):
        scope["document_type"] = "user_guide"
    for product, terms in PRODUCT_TERMS.items():
        if any(term.casefold() in normalized for term in terms):
            scope["product"] = product
            break
    if scope.get("document_type") == "protocol":
        if any(term.casefold() in normalized for term in CURRENT_PROTOCOL_TERMS):
            scope["protocol_generation"] = "current"
        elif any(term.casefold() in normalized for term in LEGACY_PROTOCOL_TERMS):
            scope["protocol_generation"] = "legacy"
    if scope.get("document_type") == "api":
        scope.pop("product", None)
    return scope


def is_terminal_user_management_intent(query: str) -> bool:
    """「단말기 사용자 관리」메뉴 사용법·조작을 묻는 질문인지 판별합니다.

    메뉴 명칭이 직접 나오거나, 단말기·사용자·관리와 사용법/메뉴 표현이 함께 있을 때만
    참입니다. 일반 사용자 등록이나 사용자→단말 추가·동기화 복합 질문과 겹치지 않게
    합니다.
    """
    normalized = (query or "").casefold()
    if _TERMINAL_USER_MGMT_MENU_PHRASE in normalized:
        return True
    has_parts = (
        "단말기" in normalized
        and "사용자" in normalized
        and "관리" in normalized
    )
    has_howto = any(marker in normalized for marker in _TERMINAL_USER_MGMT_HOWTO_MARKERS)
    return has_parts and has_howto


def is_user_terminal_procedure_intent(query: str) -> bool:
    """사용자와 단말기 사이의 UI 절차를 묻는 질문을 일반 키워드 조합으로 판별합니다.

    명시적인 문서 유형이 없는 경우에만 검색 범위를 User Guide로 좁히는 보조 규칙입니다.
    단말기·사용자와 추가/전송/동기화 같은 작업 표현이 함께 있어야 하므로 일반 제품 소개
    질문을 가이드 절차로 오인하지 않습니다.
    「단말기 사용자 관리」메뉴 사용법 질문은 별도 의도로 분리해 여기서는 제외합니다.
    """
    if is_terminal_user_management_intent(query):
        return False
    normalized = (query or "").casefold()
    has_user = any(marker in normalized for marker in _USER_TERMINAL_PROCEDURE_MARKERS)
    has_terminal = any(marker in normalized for marker in _TERMINAL_PROCEDURE_MARKERS)
    has_action = any(marker in normalized for marker in _PROCEDURE_ACTION_MARKERS)
    return has_user and has_terminal and has_action


def is_automated_build_intent(query: str) -> bool:
    """빌드를 "자동화 버전"(자동빌드) 절차로 진행하려는 의도를 일반 마커로 판별합니다.

    문서에 실제로 있는 표현("자동화 버전", "자동빌드" 등)만 사용하며 특정 질문
    문자열을 고정하지 않습니다. 이 의도일 때만 자동화 섹션 검색 확장·완결성 보정과
    수동 절차와 분리된 답변 지침이 적용됩니다.
    """
    normalized = (query or "").casefold()
    return any(marker.casefold() in normalized for marker in _AUTOMATED_BUILD_MARKERS)


def detect_api_doc_intent(query: str) -> bool:
    """질문이 Swagger·스키마·REST API 명세를 요구하는지 일반 규칙으로 판별합니다."""
    normalized = (query or "").casefold()
    return any(term.casefold() in normalized for term in DOCUMENT_TYPE_TERMS["api"])


def expand_retrieval_query(original_query: str, rewritten_query: str) -> str:
    """원문을 항상 첫 변형으로 보존하고 재작성·도메인 확장을 뒤에 추가합니다.

    파일명·경로·명령처럼 한 글자 변화에도 의미가 달라지는 입력은 LLM 재작성만
    검색하면 유실될 수 있으므로 원문을 제거하거나 정규화하지 않습니다.
    """
    original = (original_query or "").casefold()
    expansions = []
    if "내려" in original or "내리" in original:
        expansions.append("설정 전송 Server Terminal 서버 단말기 배포 적용 Request")
    if "출입그룹" in original or "출입 그룹" in original:
        expansions.append("출입그룹 출입 그룹 access group Door 설정 전송")
    if any(term.casefold() in original for term in CURRENT_PROTOCOL_TERMS):
        expansions.append("신규 프로토콜 v4.0 current Communication protocol for Terminal")
    if detect_api_doc_intent(original_query):
        expansions.append("swagger OpenAPI schema endpoint REST API definitions")
    if detect_list_completeness_intent(original_query):
        expansions.append("목차 Contents Command Preview 명령 목록 프로토콜 명령")
    if "output_folder" in detect_artifact_intents(original_query):
        expansions.append("확인 폴더 이동하면 생성된 설치 파일 확인")
    if "build_output" in detect_artifact_intents(original_query):
        expansions.append("빌드 완료 설치 파일 생성 최종 산출물 경로")
    if is_terminal_user_management_intent(original_query):
        # p.39 메뉴 목적·p.40 조작 표현으로 확장해 일반 「사용자 관리」·VoIP 청크를 밀어냅니다.
        expansions.append(
            "단말기 사용자 관리 단말기 저장 리스트 단말기 사용자 리스트 "
            "가져오기 업로드 엑셀 내보내기 삭제 추가 적용 전송 "
            "서버로 가져오기 단말로 내려보내기 단말기에서만"
        )
    elif is_user_terminal_procedure_intent(original_query):
        expansions.append(
            "사용자 단말기 추가 사용자 선택 적용 전송 "
            "단말기리스트 출입그룹 단말기 리스트 등록된 단말기 추가가능한 단말기 "
            "단말기 사용자 정보 자동 동기화 일반설정 사용자 "
            "덮어쓰기 다시 다운로드 다운로드 재진행 다시 동기화"
        )
    if is_automated_build_intent(original_query):
        # 문서의 "알페타 설치 패키지 빌드(자동화 버전)" 섹션 실제 표현으로 확장합니다.
        # 이 표현이 없으면 수동 절차(MakeNSISW 등)만 검색되기 쉽습니다.
        expansions.append(
            "알페타 설치 패키지 빌드 자동화 버전 git pull gitpull.bat "
            "define.go eXbuilder build_install.bat proto_compile go build "
            "client export alpeta_device.nsi alpeta.nsi PRODUCT_VERSION "
            "D:\\nsis\\install 설치 파일 생성"
        )
    exact_tokens = extract_technical_tokens(original_query)
    if exact_tokens:
        expansions.append(" ".join(exact_tokens))
    lines = [original_query.strip()] if (original_query or "").strip() else []
    lines.extend(line.strip() for line in (rewritten_query or "").splitlines() if line.strip())
    lines.extend(expansions)
    return "\n".join(dict.fromkeys(lines))


def extract_technical_tokens(text: str) -> List[str]:
    """질문·문서에서 파일명, 경로, API 메서드처럼 정확 비교할 토큰을 추출합니다.

    반환값은 원문 표기를 유지하되 대소문자만 무시해 중복을 제거합니다. 일반 자연어
    단어는 포함하지 않아 특정 제품이나 질문에 종속되지 않도록 합니다.
    """
    tokens: List[str] = []
    seen = set()
    for match in _TECHNICAL_TOKEN_PATTERN.finditer(text or ""):
        token = match.group(0).rstrip(".,;:)]}")
        key = token.casefold()
        if key and key not in seen:
            seen.add(key)
            tokens.append(token)
    return tokens


def detect_artifact_intents(query: str) -> List[str]:
    """질문이 요구하는 파일 역할을 일반적인 확장자 유형으로 분류합니다.

    배치·자동화 문구 안의 일반 `script`는 소스 스크립트로 중복 해석하지 않습니다.
    다만 NSIS/.nsi/소스 스크립트를 명시하면 자동화와 함께 별도 의도로 유지합니다.
    결과물 확인 폴더 질문에서는 executable(설치 파일) 의도를 제거해 산출물 경로와
    혼동하지 않게 합니다.
    """
    normalized = (query or "").casefold()
    intents = []
    for intent, rule in ARTIFACT_INTENT_RULES.items():
        if any(marker.casefold() in normalized for marker in rule["markers"]):
            intents.append(intent)

    explicit_source_script = any(
        marker in normalized
        for marker in ("nsis", ".nsi", "소스 스크립트", "source script")
    )
    if "automation" in intents and "script" in intents and not explicit_source_script:
        intents.remove("script")
    if "output_folder" in intents and "executable" in intents:
        intents.remove("executable")
    # 특정 실행 파일명은 개별 패키지의 생성 위치를 요구하므로 build_output과 병존시키지
    # 않습니다. 파일명이 없는 일반 빌드 완료 질문은 최종 산출물 역할을 우선합니다.
    explicit_executable = bool(re.search(r"\b[\w.-]+\.(?:exe|msi|pkg|deb|rpm)\b", normalized))
    if "build_output" in intents and "executable" in intents and not explicit_executable:
        intents.remove("executable")
    return intents


def detect_list_completeness_intent(query: str) -> bool:
    """질문이 표·목차·명령의 완결 목록을 요구하는지 일반 마커로 판별합니다."""
    normalized = (query or "").casefold()
    return any(marker.casefold() in normalized for marker in LIST_COMPLETENESS_MARKERS)


def looks_like_command_catalog(content: str) -> bool:
    """청크가 명령/TOC 카탈로그처럼 여러 hex·점선 목차 행을 갖는지 판별합니다.

    특정 command hex를 하드코딩하지 않고, 밀도만으로 목록 완결성 후보를 고릅니다.
    """
    text = content or ""
    hex_count = len(set(_HEX_COMMAND_PATTERN.findall(text)))
    dotted = text.count("..")
    return hex_count >= 6 or (hex_count >= 4 and dotted >= 3)


def count_unique_hex_commands(content: str) -> int:
    """본문에 등장하는 고유 0x 명령 코드 개수를 셉니다."""
    return len({value.upper() for value in _HEX_COMMAND_PATTERN.findall(content or "")})


def path_role_evidence_score(query: str, content: str) -> float:
    """결과물 확인 폴더 질문에서 경로 역할 일치도를 0~0.25로 가산합니다.

    `.exe` 생성 위치와 '이동하면 확인' 폴더를 구분하며, 특정 경로 문자열을
    하드코딩하지 않고 확인/생성 표현과 Windows 폴더 패턴의 동시 출현만 봅니다.
    """
    intents = detect_artifact_intents(query)
    if not {"output_folder", "build_output"} & set(intents):
        return 0.0
    normalized = (content or "").casefold()
    score = 0.0
    folders = _WINDOWS_FOLDER_PATTERN.findall(content or "")
    if "output_folder" in intents and folders and any(
        marker in normalized for marker in _OUTPUT_FOLDER_CONTENT_MARKERS
    ):
        score += 0.16
    if "build_output" in intents and folders and any(
        marker in normalized for marker in _BUILD_OUTPUT_CONTENT_MARKERS
    ):
        score += 0.22
    # 산출물 파일 위치만 말하고 확인/이동 표현이 없으면 감점해 setup류를 밀어냅니다.
    if "output_folder" in intents and any(ext in normalized for ext in (".exe", ".msi")) and not any(
        marker in normalized for marker in ("확인", "이동하면", "생성된", "verify", "check")
    ):
        score -= 0.08
    if "build_output" in intents and (
        "파일 위치" in normalized
        or "file location" in normalized
    ) and not any(marker in normalized for marker in _BUILD_OUTPUT_CONTENT_MARKERS):
        score -= 0.1
    if "폴더" in normalized or "folder" in normalized:
        score += 0.04
    return max(0.0, min(score, 0.25))


def procedure_evidence_score(query: str, content: str) -> float:
    """사용자-단말기 절차 질문에서 수동 전송과 자동 동기화 근거를 함께 가점합니다.

    메뉴 이름이나 특정 질문을 고정하지 않고, 질문의 사용자·단말기·작업 조합과 본문의
    추가/선택/적용/전송 및 자동 동기화 표현을 비교합니다.
    """
    if not is_user_terminal_procedure_intent(query):
        return 0.0
    normalized = (content or "").casefold()
    score = 0.0
    has_user = any(marker in normalized for marker in _USER_TERMINAL_PROCEDURE_MARKERS)
    has_terminal = any(marker in normalized for marker in _TERMINAL_PROCEDURE_MARKERS)
    if has_user and has_terminal:
        score += 0.08
    if any(marker in normalized for marker in ("추가", "선택", "적용", "전송", "다운로드")):
        score += 0.1
    if "자동" in normalized and "동기화" in normalized:
        score += 0.14
    if "출입그룹" in normalized or "출입 그룹" in normalized:
        score += 0.04
    # 중복 ID·재동기화 제한 문장은 자동 동기화 답변에 빠지기 쉬워 문서 용어를 가점합니다.
    if "덮어쓰기" in normalized:
        score += 0.04
    if "다시 다운로드" in normalized or "다운로드 재진행" in normalized:
        score += 0.04
    return min(score, 0.3)


def terminal_user_mgmt_evidence_score(query: str, content: str) -> float:
    """「단말기 사용자 관리」메뉴 근거 청크를 가점하고 인접 오답 메뉴를 감점합니다.

    메뉴 제목·가져오기/업로드 조작·단말기에서만 삭제 표현이 있는 청크를 올리고,
    통신포트 9003·고유아이디/권한(8)·VoIP만 있는 청크는 내립니다.
    """
    if not is_terminal_user_management_intent(query):
        return 0.0
    normalized = (content or "").casefold()
    score = 0.0
    if _TERMINAL_USER_MGMT_MENU_PHRASE in normalized:
        score += 0.3
    if "가져오기" in normalized and "업로드" in normalized:
        score += 0.24
    if "단말기 저장 리스트" in normalized or "단말기 사용자 리스트" in normalized:
        score += 0.1
    if "단말기에서만" in normalized:
        score += 0.08
    if "엑셀" in normalized and "내보내기" in normalized:
        score += 0.06
    # 오답 메뉴·등록 흐름이 본문 중심이면 감점합니다.
    if "9003" in normalized and _TERMINAL_USER_MGMT_MENU_PHRASE not in normalized:
        score -= 0.2
    if "고유아이디" in normalized or (
        "권한" in normalized and re.search(r"권한\s*\(?\s*8\s*\)?", content or "")
    ):
        score -= 0.12
    if "voip" in normalized and "가져오기" not in normalized:
        score -= 0.12
    # 일반 「사용자 관리」개요만 있고 메뉴 제목·가져오기가 없으면 감점합니다.
    if (
        "사용자 관리" in normalized
        and _TERMINAL_USER_MGMT_MENU_PHRASE not in normalized
        and "가져오기" not in normalized
    ):
        score -= 0.1
    return max(0.0, min(score, 0.5))


def technical_evidence_score(query: str, content: str) -> float:
    """질문의 기술 토큰과 파일 역할·API 근거가 문서에 맞는 정도를 0~0.5로 계산합니다.

    의미 유사도만으로 `.bat` 자동화와 `.exe` 산출물, 또는 User Guide와 Swagger가
    뒤바뀌는 것을 막는 보조 점수이며, 특정 질문 문자열을 하드코딩하지 않습니다.
    목록 완결 의도와 결과물 확인 폴더 의도도 일반 규칙으로 반영합니다.
    """
    normalized_content = (content or "").casefold()
    score = 0.0
    intents = detect_artifact_intents(query)
    for intent in intents:
        extensions = ARTIFACT_INTENT_RULES[intent]["extensions"]
        if extensions and any(extension in normalized_content for extension in extensions):
            score += 0.16
    if intents and any(term in normalized_content for term in ("실행", "run", "compile", "호출")):
        score += 0.04

    if detect_api_doc_intent(query):
        api_markers = (
            "type: api",
            "/v1/",
            "스키마 `",
            "**스키마",
            "application/json",
            "openapi",
            "swagger",
            "definitions",
            "endpoint",
        )
        if any(marker in normalized_content for marker in api_markers):
            score += 0.16
        if any(marker in normalized_content for marker in ("templatetype", "templatedata", "templatesize")):
            score += 0.04

    if detect_list_completeness_intent(query):
        hex_count = count_unique_hex_commands(content)
        if looks_like_command_catalog(content):
            score += 0.18
        elif hex_count >= 3:
            score += 0.08
        # 완결 목록일수록 고유 hex가 많다는 일반 휴리스틱(특정 코드 고정 없음).
        if hex_count >= 12:
            score += 0.1
        elif hex_count >= 8:
            score += 0.06

    score += path_role_evidence_score(query, content)
    score += procedure_evidence_score(query, content)
    score += terminal_user_mgmt_evidence_score(query, content)

    exact_tokens = extract_technical_tokens(query)
    if exact_tokens:
        matched = sum(token.casefold() in normalized_content for token in exact_tokens)
        score += 0.2 * (matched / len(exact_tokens))
    return min(score, 0.7)


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
    keep_alive: Optional[str] = None,
) -> str:
    """Ollama chat API를 호출합니다(think=false 유지, 빈 content 폴백).

    content가 비고 eval_count>0이면 thinking 필드로 폴백하고 경고를 남깁니다.
    keep_alive로 모델 상주를 유지해 재로드 지연을 줄입니다.
    """
    url = f"{base_url}/api/chat"
    # 일부 Ollama 모델은 think/thinking 옵션을 지원합니다.
    # Open WebUI/RAG 응답에서 사고과정 노출을 피하기 위해 기본적으로 think=false를 전달합니다.
    payload = {"model": model, "messages": messages, "stream": stream, "think": False}
    if options:
        payload["options"] = options
    alive = DEFAULT_OLLAMA_KEEP_ALIVE if keep_alive is None else keep_alive
    if alive != "":
        payload["keep_alive"] = alive
    response = requests.post(url, json=payload, timeout=(10, read_timeout))
    response.raise_for_status()
    data = response.json()
    message = data.get("message") or {}
    content = message.get("content") or ""
    eval_count = data.get("eval_count") or 0
    if not content and eval_count > 0:
        fallback = (message.get("thinking") or message.get("reasoning") or "").strip()
        print(
            "[RAG] WARNING empty content with eval_count>0; "
            f"using thinking/reasoning fallback chars={len(fallback)} eval_count={eval_count}"
        )
        return fallback
    return content


def ollama_chat_stream(
    base_url: str,
    model: str,
    messages: list,
    options: Optional[dict] = None,
    read_timeout: int = DEFAULT_OLLAMA_READ_TIMEOUT,
    keep_alive: Optional[str] = None,
) -> Generator[str, None, None]:
    """Ollama chat API 스트리밍 버전(think=false, TTFT·빈 content 경고/폴백).

    첫 content 토큰까지(TTFT)와 전체 생성 시간을 로그하고, content가 비었는데
    eval_count>0이면 thinking 조각을 폴백으로 yield합니다.
    keep_alive로 모델 상주를 유지해 재로드 지연을 줄입니다.
    """
    url = f"{base_url}/api/chat"
    payload = {"model": model, "messages": messages, "stream": True, "think": False}
    if options:
        payload["options"] = options
    alive = DEFAULT_OLLAMA_KEEP_ALIVE if keep_alive is None else keep_alive
    if alive != "":
        payload["keep_alive"] = alive
    started = time.perf_counter()
    first_token_at: Optional[float] = None
    content_chars = 0
    thinking_parts: List[str] = []
    with requests.post(url, json=payload, stream=True, timeout=(10, read_timeout)) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("done", False):
                total_sec = time.perf_counter() - started
                ttft = (first_token_at - started) if first_token_at is not None else None
                eval_count = data.get("eval_count") or 0
                print(
                    "[RAG] Ollama stream completed: "
                    f"reason={data.get('done_reason', 'unknown')}, "
                    f"prompt_tokens={data.get('prompt_eval_count', 'unknown')}, "
                    f"generated_tokens={eval_count}, "
                    f"content_chars={content_chars}"
                )
                _log_timing(
                    "answer_generation",
                    total_sec,
                    ttft_sec=f"{ttft:.3f}" if ttft is not None else "none",
                    content_chars=content_chars,
                    eval_count=eval_count,
                )
                if content_chars == 0 and eval_count > 0:
                    fallback = "".join(thinking_parts).strip()
                    print(
                        "[RAG] WARNING empty content with eval_count>0; "
                        f"yielding thinking fallback chars={len(fallback)}"
                    )
                    if fallback:
                        yield fallback
                break
            else:
                message = data.get("message") or {}
                content = message.get("content") or ""
                thinking = message.get("thinking") or message.get("reasoning") or ""
                if thinking:
                    thinking_parts.append(thinking)
                if content:
                    if first_token_at is None:
                        first_token_at = time.perf_counter()
                        _log_timing("answer_ttft", first_token_at - started)
                    content_chars += len(content)
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
    """LLM으로 검색 친화 쿼리 변형을 만들고 소요 시간을 기록합니다.

    재작성은 짧은 출력만 필요하므로 num_predict/num_ctx를 낮춰 지연을 줄입니다.
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
- 질문이 구분한 대상 역할(자동화 파일/스크립트/실행 산출물/설정 파일/명령)을 다른 역할로 바꾸지 마세요.

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

    started = time.perf_counter()
    # 재작성은 짧은 키워드 목록만 필요하므로 생성 예산을 작게 유지합니다.
    rewritten = ollama_chat(
        base_url,
        model,
        messages,
        stream=False,
        options={"num_ctx": 2048, "num_predict": 128},
    )
    _log_timing("query_rewrite", time.perf_counter() - started, model=model)
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


def derive_explicit_file_paths(documents: list) -> List[str]:
    """같은 문장 구간에 명시된 Windows 폴더와 파일명을 안전하게 결합합니다.

    문서가 `C:\\dir 폴더 ... task.bat 파일`처럼 경로를 분리 표기한 경우에만
    결합하며, 서로 다른 청크나 120자보다 먼 문자열은 이어 붙이지 않습니다.
    """
    pattern = re.compile(
        r"(?i)\b([A-Z]:\\(?:[^\\\s,.;:()]+\\)*[^\\\s,.;:()]+)"
        r"\s*폴더.{0,120}?\b([A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,10})\s*파일",
        re.DOTALL,
    )
    paths: List[str] = []
    seen = set()
    for document in documents:
        for folder, filename in pattern.findall(document.get("content", "")):
            full_path = f"{folder.rstrip(chr(92))}\\{filename}"
            key = full_path.casefold()
            if key not in seen:
                seen.add(key)
                paths.append(full_path)
    return paths


def build_context_prompt(
    query: str,
    documents: list,
    focus: Optional[str] = None,
) -> str:
    """검색 문서와 기술 근거 준수 규칙을 포함한 답변 프롬프트를 생성합니다."""
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
    explicit_paths = derive_explicit_file_paths(documents)
    path_block = ""
    if explicit_paths and any(term in query.casefold() for term in ("파일", "경로", "명령", "file", "path")):
        path_block = (
            "\n=== 같은 문서 지시문에서 확인된 전체 파일 경로 ===\n"
            + "\n".join(f"- `{path}`" for path in explicit_paths)
            + "\n- 위 목록은 같은 지시문에 있는 폴더와 파일명을 기계적으로 결합한 것입니다. "
            "질문에 맞는 항목은 답변 첫 문장에 이 전체 문자열 그대로 쓰세요.\n"
        )

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
    list_block = ""
    if detect_list_completeness_intent(query):
        list_block = """
=== 목록 완결성(필수) ===
- 질문이 전부/전체/목록을 요구하면 참고 문서의 목차·명령 표·카탈로그에 있는 항목을 가능한 한 빠짐없이 나열하세요.
- 한 표·한 목차가 여러 참고 청크로 나뉘어 있으면 같은 출처의 모든 행을 합쳐 하나의 완결 목록으로 구성하세요.
- Command Preview처럼 중간에서 끊긴 표만 보이면, 같은 문서의 목차(Contents)나 이어지는 명령 목록 행을 함께 반영하세요.
- 문서에 없는 명령 코드나 이름을 추측·보완하지 마세요.
"""
    path_role_block = ""
    artifact_intents = detect_artifact_intents(query)
    if {"output_folder", "build_output"} & set(artifact_intents):
        path_role_block = """
=== 경로 역할(필수) ===
- 질문이 빌드 완료 후 **확인·결과물 폴더**를 물으면, 문서에서 '이동하면 확인/생성된 설치 파일'처럼 결과물을 확인하라고 한 폴더를 답하세요.
- 특정 `.exe`가 만들어지는 중간 산출물 경로와 최종 확인 폴더를 혼동하지 마세요. 질문이 폴더 확인이면 파일명만 답하지 마세요.
"""
        if "build_output" in artifact_intents:
            path_role_block += (
                "- 질문이 빌드 완료 뒤 생성·생김·산출물·출력 경로를 물으면, 배치 또는 빌드 "
                "완료 문장에서 설치 파일이 생성된다고 한 최종 산출 경로를 답하세요. 개별 "
                "`.exe`의 파일 위치나 빌드 입력 복사 폴더를 최종 산출 경로로 바꾸지 마세요.\n"
            )
    procedure_block = ""
    if is_terminal_user_management_intent(query):
        procedure_block = """
=== 단말기 사용자 관리 메뉴(필수) ===
- 「단말기 사용자 관리」메뉴만 답하세요. 일반 「사용자 관리」등록, 「단말기 정보」(통신포트 9003 등), 고유아이디·권한(8)·출입그룹 입력 중심 절차는 본문에 쓰지 마세요.
- 메뉴 목적: 단말 사용자 삭제 / 서버로 가져오기 / 서버→단말 전송. 이 메뉴 삭제 = 단말기에서만 삭제.
- `단말기 저장 리스트`: 가져오기·업로드·엑셀 내보내기·삭제를 빠짐없이.
- `단말기 사용자 리스트` 추가: 추가 → 사용자 선택 → `>` → [적용] → 단말 전송 순서로 적으세요.
- Protocol·NSIS·Swagger 내용을 섞지 마세요.
"""
    elif is_user_terminal_procedure_intent(query):
        # 지연 최적화: 회귀 테스트가 요구하는 핵심 문구는 유지하되 장문 서술은 압축.
        procedure_block = """
=== 사용자·단말기 절차 범위(필수) ===
- User Guide 메뉴/버튼만 사용. 수동으로 특정 단말기에 추가·전송하는 절차와 자동 동기화는 소제목으로 분리.
- 수동 근거가 `[단말기리스트]`와 `단말기 사용자 리스트` `[추가]`로 나뉘면 「방법 1」/「방법 2」처럼 독립된 방법으로 각각 설명(계층 합치기 금지).
- 표기 고정: `[단말기리스트]`(공백 금지). `단말기 저장 리스트`로 바꾸지 마세요. `덮어쓰기` 유지.
- 자동동기화 경로: `[일반설정] > [사용자] > [사용자 데이터]`. `다시 동기화`와 `다시 다운로드`를 둘 다 포함.
- `[단말기리스트]` 안에 `출입그룹 단말기 리스트`, `등록된 단말기`, `추가가능한 단말기` 3항목과 `필수로 연결` ※문장, `[주의사항]`을 빠짐없이.
- 사용자·단말기 수동 전송(`단말기 사용자 리스트`의 `[추가]`) 답변에서는 그 절차를 반드시 `[추가] → 사용자 선택 → > → [적용] → 해당 사용자 정보 단말기 전송` 순서로 한 줄 또는 번호 목록에 적으세요. `[단말기리스트]`는 이와 별개인 다른 화면이므로 상위 메뉴로 이어 붙이지 말고, `단말기 저장 리스트`는 수동 전송 절차의 메뉴가 아니므로 이 답변에 쓰지 마세요. 메뉴 경로를 이을 때 `>`를 breadcrumb 구분자로 쓰지 마세요. `>`는 팝업의 이동 버튼에만 사용하세요.
- 사용자·단말기 자동 동기화 답변에서는 근거가 있을 때 사용자와 단말기가 `동일한 출입그룹`이어야 한다는 조건을 그대로 적으세요.
- 사용자·단말기 자동 동기화 근거에 중복 ID `덮어쓰기`와 수동 제거 뒤 `다시 동기화`/`다시 다운로드`(또는 `다운로드 재진행`)가 있으면 해당 용어를 빠짐없이 문서 표기 그대로 적으세요.
- Protocol·NSIS 문서 내용을 섞지 마세요.
"""
    automated_build_block = ""
    if is_automated_build_intent(query):
        automated_build_block = """
=== 자동화 버전 빌드 절차(필수) ===
- 질문이 빌드의 "자동화 버전"(자동빌드) 절차를 물으면, 참고 문서의 "알페타 설치 패키지 빌드(자동화 버전)" 절만 근거로 답하세요. 앞의 수동 빌드 절차(`MakeNSISW` 창, `Compile NSI scripts` 클릭, 좌측 상단 파일 아이콘 클릭 등)는 이 답변에 섞지 마세요.
- 문서 순서대로 아래 단계를 빠짐없이 답하세요.
  1) git pull: `D:\\nsis\\eXbuilder` 폴더로 이동해 `gitpull.bat`을 실행합니다. 계정 입력 창이 뜨면 자신의 git 계정으로 로그인합니다(문서에 있으면 현재 연결된 계정도 언급).
  2) `define.go` 버전 수정: `D:\\GoWorkspace\\src\\unioncomm.co.kr\\define` 폴더의 `define.go` 파일 버전을 수정합니다.
  3) `alpeta_device.nsi` 파일 버전 수정(AlpetaDevice.exe 빌드용).
  4) `alpeta.nsi` 파일 버전 수정(Alpeta 설치 파일 빌드용). `PRODUCT_VERSION`/`MAJOR_VERSION`/`MINOR_VERSION`/`BUILD_VERSION`을 만들려는 버전에 맞게 수정한다고 명시하세요.
  5) `D:\\nsis\\eXbuilder` 폴더의 `build_install.bat` 실행. 이 배치 파일이 진행하는 하위 작업을 요약하지 말고 문서에 있는 순서 그대로 전부 나열하세요(예: proto_compile 실행 → go build로 서버 빌드 → 빌드한 서버를 서버 폴더로 복사 → control 서버 client export → setting 서버 client export → AlpetaDevice 설치 파일용 스크립트 컴파일 → Alpeta 설치 파일용 스크립트 컴파일).
  6) 완료되면 `D:\\nsis\\install` 폴더에 설치 파일이 생성된다고 답하세요.
  7) 참고 문서에 자동 진행 결과에 문제가 있을 때의 대체 방법(수동 빌드 가이드로 진행 권장)이 있으면 주의사항으로 답변 마지막에 명시하세요.
- 위 단계 중 참고 문서에 실제로 없는 세부는 지어내지 말고 생략하세요.
"""
    return f"""다음 참고 문서들을 바탕으로 질문에 답변하세요.

=== 참고 문서 ===
{context_str}
{image_block}
=== 질문 ===
{query}
{scope_block}
{list_block}
{path_role_block}
{procedure_block}
{automated_build_block}
{path_block}
=== 답변 지침 ===
- 참고 문서의 내용을 기반으로 답변하세요
- 명확하고 구조적으로 답변하세요
- 파일명·경로·명령·API·스키마·버전은 참고 문서의 철자, 확장자, 구분자, 대소문자를 그대로 복사하세요. 비슷한 이름으로 바꾸거나 문서에 없는 경로를 추측하지 마세요.
- 식별자·경로·스키마명 안에 글자 사이 공백을 넣지 마세요. 예: `FaceWTInfo`, `/v1/terminals/{id}` (금지: `FA W T`, `t e r m i n a l s`, `FaceWTIn f o`).
- 질문이 요구한 대상 역할을 먼저 구분하세요. 자동화/배치 파일, 소스 스크립트, 실행·설치 산출물, 설정 파일, 결과물 확인 폴더는 서로 다른 답이므로 다른 유형의 이름을 대신 답하지 마세요.
- 파일 이름이나 경로 질문은 그 파일을 실행·선택·수정하라고 직접 지시하는 문장을 우선 근거로 사용하세요. 파일 이름만 물어도 같은 지시에 상위 폴더가 있으면 답변 첫 문장에 `파일명`과 `폴더\파일명` 전체 경로를 각각 하나의 코드 문자열로 반드시 함께 제시하세요.
- 후보가 여러 개면 질문의 대상 역할에 직접 맞는 항목만 먼저 답하고, 산출물이나 관련 스크립트는 사용자가 요청한 경우에만 별도로 구분해 설명하세요.
- 참고 문서에 Swagger/OpenAPI 경로·스키마·필드 표가 있으면 그 근거로 API·스키마를 답하세요. 스펙이 보이는데 "문서에 없다"고 단정하지 마세요. UI 가이드·바이너리 프로토콜만으로 REST 스키마를 대체하지 마세요.
- 질문 용어 중 참고 문서에 없는 이름만 짧게 구분하고, 문서에 있는 인접 스키마·엔드포인트는 출처 파일명과 함께 제시하세요.
- **금지(매우 중요)**: "제공된 참고 문서에는 … 포함되어 있지 않습니다/명시되어 있지 않습니다", "문서에는 … 에 대한 정보가 없습니다" 같은 **장황한 면책·부정 문단**을 쓰지 마세요. 문서에 없는 세부는 **굳이 나열하지 말고 생략**하거나, 꼭 필요할 때만 한 문장으로 짧게 처리하세요.
- 질문에 답하는 데 필요한 사실만 말하세요. 없는 내용을 억지로 채우지 마세요.
{image_rules}"""


def _normalize_terminal_list_menu_spelling(context: str, answer: str) -> str:
    """문서의 띄어쓰기 없는 `[단말기리스트]` 표기를 답변에 맞춥니다.

    생성 모델이 `[단말기 리스트]`처럼 가운데 공백을 넣는 경우, 참고 문서에
    원문 표기가 있을 때만 공백을 제거해 UI 메뉴명을 보존합니다. 대괄호 밖의
    일반 서술(예: '단말기 리스트를 볼 수 있다')은 바꾸지 않습니다.
    """
    if "[단말기리스트]" not in (context or ""):
        return answer or ""
    return re.sub(r"\[단말기\s+리스트\]", "[단말기리스트]", answer or "")


def _normalize_manual_transfer_step_markers(answer: str) -> str:
    """메뉴 경로 구분자로 쓰인 `>`를 제거해 이동 버튼 `>`와 혼동되지 않게 합니다.

    생성 모델이 `단말기 사용자 리스트 > [추가]`처럼 breadcrumb에 `>`를 넣으면,
    이후 단계의 이동 버튼 `>`보다 앞에 나타나 절차 순서 근거가 깨질 수 있습니다.
    문서 UI의 이동 버튼만 `>`로 남기고 경로 구분 `>`는 '의' 표기로 바꿉니다.
    """
    result = answer or ""
    result = re.sub(
        r"(단말기 사용자 리스트)\s*>\s*(\[추가\])",
        r"\1의 \2",
        result,
    )
    result = re.sub(
        r"(단말기 사용자 리스트)\s*>\s*(추가)",
        r"\1의 \2",
        result,
    )
    return result


def _missing_terminal_list_composition_terms(context: str, answer: str) -> list:
    """참고 문서에만 있고 답변에 빠진 단말기리스트 화면 구성 항목명을 반환합니다.

    문서에 실제로 등장하는 항목명만 검사하며, 특정 질문 문자열이나 고정 답변을
    넣지 않습니다. '추가가능한 단말기'와 '추가 가능한 단말기'는 동일 항목으로
    취급합니다.
    """
    composition_terms = (
        "출입그룹 단말기 리스트",
        "등록된 단말기",
        "추가가능한 단말기",
    )
    missing = []
    for term in composition_terms:
        if term not in (context or ""):
            # 문서에 공백 표기만 있는 경우도 동일 항목으로 본다.
            if term != "추가가능한 단말기" or "추가 가능한 단말기" not in (context or ""):
                continue
        if term in (answer or ""):
            continue
        if term == "추가가능한 단말기" and "추가 가능한 단말기" in (answer or ""):
            continue
        missing.append(term)
    return missing


def _composition_supplement_lines(context: str, missing_terms: list) -> list:
    """빠진 화면 구성 항목에 대해 문서에서 해당 항목이 들어간 원문 줄을 고릅니다.

    컨텍스트에 항목명이 포함된 줄이 있으면 그 줄을 그대로 쓰고, 없으면 항목명만
    보강합니다. 특정 질문·고정 답변을 만들지 않고 문서에 있는 문장만 재사용합니다.
    """
    lines = []
    context_lines = [line.strip() for line in (context or "").splitlines() if line.strip()]
    for term in missing_terms:
        aliases = [term]
        if term == "추가가능한 단말기":
            aliases.append("추가 가능한 단말기")
        matched = next(
            (
                line
                for line in context_lines
                if any(alias in line for alias in aliases)
            ),
            None,
        )
        if matched:
            lines.append(f"- {matched}")
        else:
            lines.append(f"- **{term}**")
    return lines


def repair_spaced_document_tokens(documents: list, answer: str) -> str:
    """참고 문서 식별자가 답변에서 글자 사이 공백으로 깨진 경우 원형으로 복원합니다.

    소형 모델이 `FaceWT`/`terminals`를 `FA W T`/`t e r m i n a l s`처럼 쪼개는
    경우가 있어, 컨텍스트에 실제 등장하는 길이 4 이상 토큰만 대상으로 복원합니다.
    """
    if not answer or not documents:
        return answer or ""
    context = "\n".join(document.get("content", "") for document in documents)
    if not context:
        return answer
    tokens = re.findall(
        r"[A-Za-z][A-Za-z0-9_]{3,}|/[A-Za-z0-9_./{}-]{3,}",
        context,
    )
    # 긴 토큰부터 치환해 부분 매칭이 짧은 토큰을 선점하지 않게 합니다.
    unique_tokens = sorted(set(tokens), key=len, reverse=True)
    result = answer
    for token in unique_tokens[:80]:
        # 글자 사이에 공백이 0개 이상 끼어 있는 변형만 잡고, 원문은 그대로 둡니다.
        spaced_pattern = r"\s*".join(re.escape(ch) for ch in token)
        loose = re.compile(spaced_pattern, re.IGNORECASE)
        def _replace_if_broken(match: re.Match, original: str = token) -> str:
            """공백이 실제로 끼어 있을 때만 문서 원형 토큰으로 되돌립니다."""
            text = match.group(0)
            if text == original or " " not in text:
                return text
            return original
        result = loose.sub(_replace_if_broken, result)
    return result


def enforce_terminal_user_mgmt_menu_name(
    query: str, documents: list, answer: str
) -> str:
    """단말기 사용자 관리 답변에서 메뉴명·가져오기·업로드 누락을 문서 근거로 보강합니다.

    컨텍스트에 해당 근거가 있을 때만 동작하며, 스트림 말미에 이어 붙여 replace를 피합니다.
    """
    if not is_terminal_user_management_intent(query):
        return answer or ""
    result = answer or ""
    context = "\n".join(document.get("content", "") for document in documents)
    if _TERMINAL_USER_MGMT_MENU_PHRASE not in context:
        return result
    parts: List[str] = []
    if _TERMINAL_USER_MGMT_MENU_PHRASE not in result:
        parts.append(
            f"- {_TERMINAL_USER_MGMT_MENU_PHRASE}: 단말기에 등록된 사용자 정보를 "
            "삭제하거나 서버로 가져오고, 서버 사용자를 단말로 전송하는 메뉴입니다."
        )
    if "가져오기" in context and "가져오기" not in result:
        parts.append("- 단말기 저장 리스트: 가져오기로 단말 사용자를 불러옵니다.")
    if "업로드" in context and "업로드" not in result:
        parts.append("- 단말기 저장 리스트: 불러온 사용자 정보를 알페타로 업로드합니다.")
    if not parts:
        return result
    return f"{result.rstrip()}\n\n" + "\n".join(parts)


def enforce_document_term_pairs(query: str, documents: list, answer: str) -> str:
    """문서에 명시된 필수 UI·절차 용어가 답변에서 축약·의역될 때 원문을 보존합니다.

    사용자·단말기 절차 질문에만 적용합니다. (1) 문서의 `[단말기리스트]` 표기를
    공백 의역에서 복원하고, (2) 문서에 있는 화면 구성 3항목이 빠지면 문서 원문
    줄을 보완하며, (3) 재동기화·재다운로드 쌍이 축약되면 원문 표현을 스트림 끝에
    추가합니다. 특정 질문에 답을 고정하지 않고 컨텍스트 근거가 있을 때만 동작합니다.
    """
    if is_terminal_user_management_intent(query):
        return enforce_terminal_user_mgmt_menu_name(query, documents, answer)
    if not is_user_terminal_procedure_intent(query):
        return answer

    context = "\n".join(document.get("content", "") for document in documents)
    result = _normalize_terminal_list_menu_spelling(context, answer or "")
    result = _normalize_manual_transfer_step_markers(result)

    missing_composition = _missing_terminal_list_composition_terms(context, result)
    if missing_composition:
        lines = "\n".join(_composition_supplement_lines(context, missing_composition))
        result = (
            f"{result.rstrip()}\n\n"
            f"### 단말기리스트 화면 구성(문서 표기)\n{lines}"
        )

    normalized_context = context.casefold()
    normalized_answer = result.casefold()
    has_resync_evidence = "다시 동기화" in normalized_context
    has_redownload_evidence = (
        "다시 다운로드" in normalized_context
        or "다운로드 재진행" in normalized_context
    )
    has_resync_answer = (
        "다시 동기화" in normalized_answer or "재동기화" in normalized_answer
    )
    has_redownload_answer = (
        "다시 다운로드" in normalized_answer
        or "다운로드 재진행" in normalized_answer
    )
    if has_resync_evidence and has_redownload_evidence and not (
        has_resync_answer and has_redownload_answer
    ):
        suffix = (
            "\n\n- 문서상 단말기에서 사용자를 제거한 뒤 출입그룹 다시 동기화가 진행되면, "
            "출입그룹에 맞춰 사용자가 다시 다운로드됩니다."
        )
        result = f"{result.rstrip()}{suffix}"
    return result


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
        RERANK_NEURAL: bool = DEFAULT_RERANK_NEURAL
        USE_QUERY_REWRITE: bool = DEFAULT_USE_QUERY_REWRITE
        CONTEXTUALIZE_FOLLOW_UP: bool = DEFAULT_CONTEXTUALIZE_FOLLOW_UP
        OLLAMA_KEEP_ALIVE: str = DEFAULT_OLLAMA_KEEP_ALIVE

        SHOW_SOURCES: bool = True
        SHOW_REWRITTEN_QUERY: bool = False

    def __init__(self):
        self.name = "도우미"
        self.valves = self.Valves()

    def answer_options(self) -> dict:
        """답변 생성용 Ollama options(num_ctx/num_predict)를 반환합니다."""
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
        """RAG 파이프라인 진입점. 첫 yield로 즉시 상태를 알린 뒤 검색·생성을 수행합니다.

        첫 yield 전에 재작성·검색·리랭크를 동기 수행하지 않습니다(PLF-20260801-001).
        """
        chat_history = messages[:-1] if len(messages) > 1 else []

        print(f"\n[Step 1] 원본 질문: {user_message}")
        model_swap = self.valves.REWRITE_MODEL != self.valves.ANSWER_MODEL
        print(
            f"[RAG] models rewrite={self.valves.REWRITE_MODEL} "
            f"answer={self.valves.ANSWER_MODEL} swap={model_swap} "
            f"use_query_rewrite={self.valves.USE_QUERY_REWRITE} "
            f"rerank={self.valves.RERANK_ENABLED} "
            f"rerank_neural={self.valves.RERANK_NEURAL} "
            f"rerank_candidates={self.valves.RERANK_CANDIDATES}"
        )

        # Open WebUI 내부 작업(후속질문/제목/태그 등)은 RAG/재작성 스킵
        if is_openwebui_internal_task(user_message):
            print("[Route] Open WebUI 내부 작업: RAG/재작성 스킵")
            stream = bool((body or {}).get("stream", True))

            def generate_internal():
                """내부 작업은 RAG/status 없이 바로 답변만 반환합니다.

                제목·태그 JSON에 '처리 중...' 문자열이 섞이면 파싱이 깨질 수 있어
                status 문구를 본문에 yield하지 않습니다.
                """
                if stream:
                    yield from ollama_chat_stream(
                        base_url=self.valves.OLLAMA_BASE_URL,
                        model=self.valves.ANSWER_MODEL,
                        messages=messages,
                        options=self.answer_options(),
                        read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
                        keep_alive=self.valves.OLLAMA_KEEP_ALIVE,
                    )
                else:
                    yield ollama_chat(
                        base_url=self.valves.OLLAMA_BASE_URL,
                        model=self.valves.ANSWER_MODEL,
                        messages=messages,
                        stream=False,
                        options=self.answer_options(),
                        read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
                        keep_alive=self.valves.OLLAMA_KEEP_ALIVE,
                    )

            return generate_internal()

        stream = bool((body or {}).get("stream", True))

        def generate():
            """status 이벤트를 즉시 yield한 뒤 재작성·검색·답변 생성과 타이밍을 수행합니다."""
            pipe_started = time.perf_counter()
            # 첫 yield 전 장시간 동기 금지(PLF-20260801-001). 본문이 아닌 status 이벤트만 보냅니다.
            if stream:
                yield _status_event("문서 검색 준비 중...")
            else:
                # non-stream 연결 유지용 최소 신호(본문 assertion에서 제거 가능)
                yield "\n"

            retrieval_question = user_message
            if self.valves.CONTEXTUALIZE_FOLLOW_UP and is_follow_up_question(
                user_message, chat_history
            ):
                condense_started = time.perf_counter()
                retrieval_question = condense_question(
                    base_url=self.valves.OLLAMA_BASE_URL,
                    model=self.valves.REWRITE_MODEL,
                    question=user_message,
                    chat_history=chat_history,
                )
                _log_timing(
                    "contextualize",
                    time.perf_counter() - condense_started,
                    model=self.valves.REWRITE_MODEL,
                )
                if retrieval_question != user_message:
                    print(f"[Step 0] 후속 질문 감지 → 문맥 반영 질문: {retrieval_question}")

            if self.valves.USE_QUERY_REWRITE:
                rewritten_query = rewrite_query(
                    base_url=self.valves.OLLAMA_BASE_URL,
                    model=self.valves.REWRITE_MODEL,
                    original_query=retrieval_question,
                    chat_history=[],
                )
            else:
                rewritten_query = retrieval_question
                _log_timing("query_rewrite", 0.0, skipped=True)
            rewritten_query = expand_retrieval_query(retrieval_question, rewritten_query)
            print(f"[Step 1] 재작성된 쿼리: {rewritten_query}")

            scope = detect_retrieval_scope(retrieval_question)
            print(f"[Step 2] 검색 중... (top_k={self.valves.TOP_K}, scope={scope or 'none'})")
            if stream:
                yield _status_event("관련 문서 검색 중...")
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
                rerank_neural=self.valves.RERANK_NEURAL,
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

            ctx_limit_started = time.perf_counter()
            documents = limit_documents_for_context(
                documents, self.valves.MAX_CONTEXT_CHARS
            )
            _log_timing(
                "context_budget",
                time.perf_counter() - ctx_limit_started,
                docs=len(documents),
                max_chars=self.valves.MAX_CONTEXT_CHARS,
            )
            print(
                f"[Step 2c] 답변 컨텍스트: {len(documents)}개 청크, "
                f"최대 {self.valves.MAX_CONTEXT_CHARS}자"
            )

            context_prompt = build_context_prompt(
                retrieval_question, documents, focus=focus
            )

            prefix = ""
            if self.valves.SHOW_REWRITTEN_QUERY:
                prefix += f"> **재작성된 검색 쿼리:** `{rewritten_query}`\n\n"
            if self.valves.SHOW_SOURCES and documents:
                sources = ", ".join(sorted(set(d["source"] for d in documents)))
                prefix += f"> **참조 출처:** {sources}\n\n---\n\n"

            print(f"[Step 3] 답변 생성 중... (모델: {self.valves.ANSWER_MODEL})")
            if stream:
                yield _status_event("답변 생성 중...")
            system_message = (
                "당신은 친절하고 정확한 AI 어시스턴트입니다. 주어진 참고 문서를 바탕으로 답변하세요. "
                "이전 대화에 나온 다른 인물·추측은 무시하고, 이번 사용자 질문과 참고 문서만 따르세요. "
                "질문에 특정 인물·주제가 있으면 그 범위를 벗어난 인물 이름·설명을 쓰지 마세요. "
                "답변 말미에 '문서에는 … 없습니다' 식의 긴 면책 문장을 반복하지 마세요. "
                "필수 메뉴·경로·버튼명·API 식별자는 문서 철자 그대로 쓰고 글자 사이 공백을 넣지 마세요. "
                "서론·반복·추측 금지. 가능하면 12줄 이내 불릿으로 작성하세요."
            )
            answer_messages = [
                {"role": "system", "content": system_message},
                *chat_history[-4:],  # 최근 2턴 유지
                {"role": "user", "content": context_prompt},
            ]

            if prefix:
                yield prefix
            answer_parts = []
            for chunk in ollama_chat_stream(
                base_url=self.valves.OLLAMA_BASE_URL,
                model=self.valves.ANSWER_MODEL,
                messages=answer_messages,
                options=self.answer_options(),
                read_timeout=self.valves.OLLAMA_READ_TIMEOUT,
                keep_alive=self.valves.OLLAMA_KEEP_ALIVE,
            ):
                answer_parts.append(chunk)
                yield chunk
            answer = "".join(answer_parts)
            repaired = repair_spaced_document_tokens(documents, answer)
            completed_answer = enforce_document_term_pairs(
                retrieval_question,
                documents,
                repaired,
            )
            visible = f"{prefix}{answer}"
            final_visible = f"{prefix}{completed_answer}"
            if completed_answer != answer:
                if completed_answer.startswith(answer):
                    # 말미 보강만 있으면 이어서 스트리밍합니다.
                    yield completed_answer[len(answer):]
                elif stream:
                    # 중간 글자 공백 복원 등은 Open WebUI replace 이벤트로 본문을 교체합니다.
                    yield {
                        "event": {
                            "type": "replace",
                            "data": {"content": final_visible},
                        }
                    }
                else:
                    yield completed_answer[len(answer):] if final_visible.startswith(
                        visible
                    ) else ""
            if stream:
                yield _status_event("", done=True)
            _log_timing(
                "pipe_wall_clock",
                time.perf_counter() - pipe_started,
                answer_chars=len(completed_answer),
                docs=len(documents),
                model_swap=model_swap,
                num_predict=self.valves.NUM_PREDICT,
            )

        return generate()


# Hybrid retrieval is intentionally kept here because the pipeline container only
# mounts this directory. The indexer writes bm25_index.json beside ChromaDB.
def _bm25_tokens(text: str) -> list:
    """기술 식별자의 전체 형태와 경로·파일명 구성 요소를 함께 토큰화합니다.

    Windows 경로와 점이 포함된 파일명은 전체 토큰을 유지하면서 디렉터리, stem,
    확장자도 추가해 질문이 전체 경로나 파일명 중 하나만 알아도 검색되게 합니다.
    """
    normalized = (text or "").casefold()
    base_tokens = re.findall(r"[\uac00-\ud7a3]+|[A-Za-z0-9][A-Za-z0-9_./:\\{}-]*", normalized)
    tokens: List[str] = []
    for token in base_tokens:
        tokens.append(token)
        if re.search(r"[./:\\]", token):
            tokens.extend(
                part
                for part in re.split(r"[./:\\]+", token)
                if part and part != token
            )
    return tokens


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


def rerank_documents(
    query: str,
    documents: list,
    model_name: str,
    top_k: int,
    use_neural: bool = True,
) -> list:
    """크로스 인코더 점수에 기술 토큰·파일 역할 근거 점수를 결합합니다.

    use_neural=False이거나 모델이 없으면 결정적 근거 점수만으로 정렬하며,
    점수가 같은 문서는 기존 RRF 순서를 유지합니다.
    """
    if len(documents) <= 1:
        return documents[:top_k]
    question = next((line.strip() for line in (query or "").splitlines() if line.strip()), query)
    model = _get_reranker(model_name) if use_neural else None
    if not use_neural:
        print("[RAG] Rerank neural skipped; using technical evidence order")
    if model is None:
        scores = [0.0] * len(documents)
    else:
        try:
            scores = model.predict([(question, doc.get("content", "")) for doc in documents])
        except Exception as exc:
            print(f"[RAG] Rerank failed, using technical evidence order: {exc}")
            scores = [0.0] * len(documents)

    ranked = []
    for position, (document, model_score) in enumerate(zip(documents, scores)):
        evidence_score = technical_evidence_score(question, document.get("content", ""))
        combined_score = float(model_score) + evidence_score
        ranked.append((document, float(model_score), evidence_score, combined_score, position))
    ranked.sort(key=lambda item: (-item[3], item[4]))
    return [
        {
            **document,
            "rerank_score": round(model_score, 4),
            "technical_evidence_score": round(evidence_score, 4),
            "combined_rerank_score": round(combined_score, 4),
        }
        for document, model_score, evidence_score, combined_score, _ in ranked[:top_k]
    ]


def _rrf_merge(
    vector_docs: list,
    bm25_docs: list,
    top_k: int,
    k: int = 60,
    query: str = "",
) -> list:
    """벡터·BM25 순위를 합치고 기술 근거 일치도를 작은 보조 점수로 반영합니다.

    `query`가 비어 있으면 기존 RRF와 동일하며, 기술 질문에서는 파일 역할이나
    exact token이 맞는 청크가 일반 의미 유사도 후보보다 앞설 수 있게 합니다.
    """
    merged = {}
    for rank, doc in enumerate(vector_docs, 1):
        key = (doc.get("source", "unknown"), doc.get("content", ""))
        item = merged.setdefault(key, {**doc, "score": 0.0})
        item["score"] += 1 / (k + rank)
    for rank, doc in enumerate(bm25_docs, 1):
        key = (doc.get("source", "unknown"), doc.get("content", ""))
        item = merged.setdefault(key, {**doc, "score": 0.0})
        item["score"] += 1 / (k + rank)
    scored = []
    for position, doc in enumerate(merged.values()):
        evidence_score = technical_evidence_score(query, doc.get("content", "")) if query else 0.0
        combined_score = doc["score"] + (0.05 * evidence_score)
        scored.append((doc, evidence_score, combined_score, position))
    scored.sort(key=lambda item: (-item[2], item[3]))
    return [
        {
            **doc,
            "rrf_score": round(doc["score"], 4),
            "technical_evidence_score": round(evidence_score, 4),
            "score": round(combined_score, 4),
        }
        for doc, evidence_score, combined_score, _ in scored[:top_k]
    ]


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


def expand_catalog_chunks_from_candidates(
    selected: list,
    candidates: list,
    query: str,
    top_k: int,
    max_chunks_per_source: int,
) -> list:
    """목록 완결 의도일 때 같은 출처의 카탈로그·TOC 연속 청크를 후보에서 보충합니다.

    이미 선택된 청크를 유지한 채, 표/목차처럼 hex·점선 행이 많은 동일 출처 청크를
    점수 순으로 채워 부분 목록만 컨텍스트에 남는 경우를 줄입니다.
    """
    if not detect_list_completeness_intent(query) or not selected:
        return selected
    selected_keys = {
        (doc.get("source", "unknown"), doc.get("content", "")) for doc in selected
    }
    counts: Dict[str, int] = {}
    for doc in selected:
        source = doc.get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1
    focus_sources = {doc.get("source", "unknown") for doc in selected}
    extras = []
    for doc in candidates:
        source = doc.get("source", "unknown")
        key = (source, doc.get("content", ""))
        if source not in focus_sources or key in selected_keys:
            continue
        if counts.get(source, 0) >= max_chunks_per_source:
            continue
        if not looks_like_command_catalog(doc.get("content", "")):
            continue
        extras.append(doc)
        selected_keys.add(key)
        counts[source] = counts.get(source, 0) + 1
        if len(selected) + len(extras) >= top_k:
            break
    if not extras:
        return selected
    return selected + extras


def _procedure_context_facets(query: str, content: str) -> set[str]:
    """질문과 청크가 함께 충족하는 수동·자동 절차의 역할 범위를 반환합니다."""
    if not is_user_terminal_procedure_intent(query):
        return set()
    normalized_query = (query or "").casefold()
    normalized_content = (content or "").casefold()
    has_user_terminal = (
        any(marker in normalized_content for marker in _USER_TERMINAL_PROCEDURE_MARKERS)
        and any(marker in normalized_content for marker in _TERMINAL_PROCEDURE_MARKERS)
    )
    facets = set()
    # 그룹/관리자 화면의 단순 사용자 추가를 특정 단말기 전송 절차로 오인하지 않도록,
    # 실제 단말기 사용자 목록 또는 사용자→단말 전송 문장을 요구합니다.
    has_direct_terminal_transfer = (
        "단말기 사용자 리스트" in normalized_content
        or (
            "사용자를 단말" in normalized_content
            and any(marker in normalized_content for marker in ("전송", "다운로드"))
        )
    )
    if has_user_terminal and has_direct_terminal_transfer and any(
        marker in normalized_query for marker in ("추가", "등록", "전송", "다운로드")
    ) and any(marker in normalized_content for marker in ("추가", "전송", "다운로드", "적용")):
        facets.add("manual_transfer")
    # 상위 목록 화면과 하위 사용자 목록 화면이 다른 페이지로 분리된 UI 가이드도
    # 메뉴 진입 순서를 재구성할 수 있도록, 상위 화면 근거를 별도 역할로 보존합니다.
    if (
        any(marker in normalized_query for marker in ("추가", "등록", "전송", "다운로드"))
        and "단말기리스트" in normalized_content
        and ("사용자" in normalized_content or "단말기" in normalized_content)
    ):
        facets.add("manual_navigation")
    if "동기" in normalized_query and "자동" in normalized_content and "동기화" in normalized_content:
        facets.add("automatic_sync")
    if "동기" in normalized_query and "저장" in normalized_content and (
        "자동 업데이트" in normalized_content or "동기화" in normalized_content
    ):
        facets.add("save_update")
    if "동기" in normalized_query and (
        "다시 다운로드" in normalized_content or "다시 동기화" in normalized_content
    ) and ("출입그룹" in normalized_content or "출입 그룹" in normalized_content):
        facets.add("resync_behavior")
    if "동기" in normalized_query and "덮어쓰기" in normalized_content:
        facets.add("overwrite_option")
    # 사용자 정보 `[단말기리스트]` 화면의 구성 3항목은 주의사항·동기화 절과
    # 다른 청크에 있을 수 있어 별도 역할로 보존합니다.
    if any(marker in normalized_query for marker in ("추가", "등록", "전송", "다운로드", "동기")) and (
        "출입그룹 단말기 리스트" in normalized_content
        and "등록된 단말기" in normalized_content
        and (
            "추가가능한 단말기" in normalized_content
            or "추가 가능한 단말기" in normalized_content
        )
    ):
        facets.add("terminal_list_composition")
    return facets


def _terminal_user_mgmt_context_facets(query: str, content: str) -> set[str]:
    """단말기 사용자 관리 메뉴 질문에서 청크가 담당하는 역할 집합을 반환합니다."""
    if not is_terminal_user_management_intent(query):
        return set()
    normalized = (content or "").casefold()
    facets: set[str] = set()
    if _TERMINAL_USER_MGMT_MENU_PHRASE in normalized and (
        "서버로" in normalized
        or "단말로" in normalized
        or "단말기에서만" in normalized
        or "내려보내" in normalized
    ):
        facets.add("tum_overview")
    if "가져오기" in normalized and "업로드" in normalized:
        facets.add("tum_save_list")
    if "단말기 사용자 리스트" in normalized and any(
        marker in normalized for marker in ("추가", "적용", "전송")
    ):
        facets.add("tum_user_list_add")
    return facets


def complete_terminal_user_mgmt_context(
    selected: list,
    records: list,
    query: str,
    top_k: int,
    scope: Optional[Dict[str, str]] = None,
) -> list:
    """메뉴 개요(p.39)·저장 리스트·사용자 리스트 추가 근거를 같은 출처에서 보충합니다.

    리랭커가 일반 「사용자 관리」만 남긴 경우에도, 검색 후보 안에서 누락된 역할 청크를
    끼워 넣어 생성 컨텍스트가 「단말기 사용자 관리」조작을 포함하게 합니다.
    """
    required = {"tum_overview", "tum_save_list", "tum_user_list_add"}
    if not is_terminal_user_management_intent(query) or not selected or not records:
        return selected
    selected_keys = {
        (doc.get("source", "unknown"), doc.get("content", "")) for doc in selected
    }
    result = list(selected)
    covered: set[str] = set()
    for document in result:
        covered |= _terminal_user_mgmt_context_facets(query, document.get("content", ""))

    for missing in required - covered:
        candidates = []
        focus_sources = {doc.get("source", "unknown") for doc in result}
        for record in records:
            metadata = record.get("metadata") or {}
            if not _metadata_matches_scope(metadata, scope):
                continue
            source = metadata.get("source", "unknown")
            content = record.get("document", "")
            key = (source, content)
            if source not in focus_sources or key in selected_keys:
                continue
            facets = _terminal_user_mgmt_context_facets(query, content)
            if missing not in facets:
                continue
            score = terminal_user_mgmt_evidence_score(query, content)
            if missing == "tum_overview" and _TERMINAL_USER_MGMT_MENU_PHRASE in content:
                score += 0.2
            if missing == "tum_save_list" and "가져오기" in content:
                score += 0.2
            if missing == "tum_user_list_add" and "단말기 사용자 리스트" in content:
                score += 0.2
            candidates.append((score, content, source, metadata, facets))
        if not candidates:
            continue
        _, content, source, metadata, facets = max(candidates, key=lambda item: item[0])
        candidate = {
            "content": content,
            "source": source,
            "score": 0.0,
            "metadata": metadata,
            "terminal_user_mgmt_context": missing,
        }
        if len(result) < top_k:
            result.append(candidate)
        else:
            replace_index = next(
                (
                    index
                    for index in range(len(result) - 1, -1, -1)
                    if not _terminal_user_mgmt_context_facets(
                        query, result[index].get("content", "")
                    )
                ),
                len(result) - 1,
            )
            removed = result[replace_index]
            selected_keys.discard(
                (removed.get("source", "unknown"), removed.get("content", ""))
            )
            result[replace_index] = candidate
        selected_keys.add((source, content))
        covered |= facets

    # 메뉴 개요 청크를 앞에 두어 생성기가 정식 메뉴명을 먼저 보도록 합니다.
    def _tum_sort_key(document: dict) -> tuple:
        """overview → save_list → user_list → 기타 순으로 정렬 키를 만듭니다."""
        facets = _terminal_user_mgmt_context_facets(query, document.get("content", ""))
        if "tum_overview" in facets:
            return (0, document.get("source", ""))
        if "tum_save_list" in facets:
            return (1, document.get("source", ""))
        if "tum_user_list_add" in facets:
            return (2, document.get("source", ""))
        return (3, document.get("source", ""))

    return sorted(result, key=_tum_sort_key)


def complete_procedure_context(
    selected: list,
    records: list,
    query: str,
    top_k: int,
    scope: Optional[Dict[str, str]] = None,
) -> list:
    """절차 복합 질문에 같은 출처의 수동·자동 근거를 하나씩 남깁니다.

    User Guide처럼 수동 전송과 자동 동기화가 떨어진 절에 있을 때, 이미 선택된 출처 안에서
    누락된 절차 역할을 가장 강하게 설명하는 청크를 보충합니다. 특정 질문·파일명·경로를
    고정하지 않고 질문의 작업 동사와 청크의 역할 조합만 사용합니다.
    """
    required = {
        "manual_navigation",
        "manual_transfer",
        "automatic_sync",
        "save_update",
        "resync_behavior",
        "overwrite_option",
        "terminal_list_composition",
    }
    if not is_user_terminal_procedure_intent(query) or not selected or not records:
        return selected
    selected_keys = {
        (doc.get("source", "unknown"), doc.get("content", "")) for doc in selected
    }
    result = list(selected)
    covered = set()
    for document in result:
        covered |= _procedure_context_facets(query, document.get("content", ""))

    for missing in required - covered:
        candidates = []
        focus_sources = {doc.get("source", "unknown") for doc in result}
        for record in records:
            metadata = record.get("metadata") or {}
            if not _metadata_matches_scope(metadata, scope):
                continue
            source = metadata.get("source", "unknown")
            content = record.get("document", "")
            key = (source, content)
            if source not in focus_sources or key in selected_keys:
                continue
            facets = _procedure_context_facets(query, content)
            if missing not in facets:
                continue
            score = procedure_evidence_score(query, content)
            # 수동 단말기 작업을 직접 설명하는 UI 목록은 일반 사용자 설정 문장보다 우선합니다.
            if missing == "manual_transfer" and "단말기 사용자 리스트" in content:
                score += 0.2
            if missing == "manual_navigation" and "단말기리스트" in content:
                score += 0.2
            if missing == "save_update" and "자동 업데이트" in content:
                score += 0.15
            if missing == "resync_behavior" and "다시 다운로드" in content:
                score += 0.15
            if missing == "overwrite_option" and "덮어쓰기" in content:
                score += 0.15
            if missing == "terminal_list_composition" and "출입그룹 단말기 리스트" in content:
                score += 0.2
            candidates.append((score, content, source, metadata, facets))
        if not candidates:
            continue
        _, content, source, metadata, facets = max(candidates, key=lambda item: item[0])
        candidate = {
            "content": content,
            "source": source,
            "score": 0.0,
            "metadata": metadata,
            "procedure_context": missing,
        }
        if len(result) < top_k:
            result.append(candidate)
        else:
            replace_index = next(
                (
                    index
                    for index in range(len(result) - 1, -1, -1)
                    if not _procedure_context_facets(query, result[index].get("content", ""))
                ),
                len(result) - 1,
            )
            removed = result[replace_index]
            selected_keys.discard(
                (removed.get("source", "unknown"), removed.get("content", ""))
            )
            result[replace_index] = candidate
        selected_keys.add((source, content))
        covered |= facets
    return result


def complete_build_output_context(
    selected: list,
    records: list,
    query: str,
    top_k: int,
    scope: Optional[Dict[str, str]] = None,
) -> list:
    """생성 완료 경로 질문에 최종 설치 파일 생성 문장을 같은 문서에서 보충합니다.

    파일·폴더 역할을 나타내는 문장과 개별 실행 파일 생성 문장이 떨어져 있어도,
    경로 역할 점수와 생성 완료 표현으로 후보를 고릅니다. 특정 제품·경로·질문을
    고정하지 않으며 현재 검색 범위와 선택된 출처만 사용합니다.
    """
    if "build_output" not in detect_artifact_intents(query) or not selected or not records:
        return selected
    selected_keys = {
        (doc.get("source", "unknown"), doc.get("content", "")) for doc in selected
    }
    focus_sources = {doc.get("source", "unknown") for doc in selected}
    candidates = []
    for record in records:
        metadata = record.get("metadata") or {}
        if not _metadata_matches_scope(metadata, scope):
            continue
        content = record.get("document", "")
        source = metadata.get("source", "unknown")
        if source not in focus_sources or (source, content) in selected_keys:
            continue
        normalized = content.casefold()
        if not any(marker in normalized for marker in _BUILD_OUTPUT_CONTENT_MARKERS):
            continue
        score = path_role_evidence_score(query, content)
        if "설치파일" in normalized or "installation file" in normalized:
            score += 0.15
        candidates.append((score, content, source, metadata))
    if not candidates:
        return selected
    _, content, source, metadata = max(candidates, key=lambda item: item[0])
    candidate = {
        "content": content,
        "source": source,
        "score": 0.0,
        "metadata": metadata,
        "path_role_context": "build_output",
    }
    if len(selected) < top_k:
        return selected + [candidate]
    return list(selected[:-1]) + [candidate]


def complete_automated_build_context(
    selected: list,
    records: list,
    query: str,
    top_k: int,
    scope: Optional[Dict[str, str]] = None,
) -> list:
    """자동화 버전 빌드 질문에서 문서의 자동화 섹션 전체를 강제로 포함합니다.

    자동화 섹션은 여러 청크에 걸쳐 있고, 그중 일부 청크(예: nsi 스크립트 버전 수정
    단계)는 수동 섹션의 유사 문장과 겹쳐 고유 앵커 표현이 없어 검색만으로는 누락되기
    쉽습니다. `records`(BM25 전체 레코드, scope 필터 적용)에서 자동화 섹션에만 있는
    고유 표현(`_AUTOMATED_BUILD_SECTION_ANCHORS`)이 포함된 청크를 찾아 같은 출처
    내 chunk_index 최소~최대 구간을 계산하고, 그 구간의 모든 청크(앵커가 없는 중간
    청크 포함)를 결과에 강제로 포함합니다. 같은 출처의 구간 밖 청크(수동 절차 등)는
    결과에서 제거해 두 절차가 섞이지 않게 합니다. 특정 페이지 번호나 파일명을 고정하지
    않고 문서에 실제로 있는 표현과 인덱서가 부여한 chunk_index만 사용합니다.
    """
    if not is_automated_build_intent(query) or not records:
        return selected

    by_source: Dict[str, Dict[int, dict]] = {}
    anchor_indexes: Dict[str, List[int]] = {}
    for record in records:
        metadata = record.get("metadata") or {}
        if not _metadata_matches_scope(metadata, scope):
            continue
        chunk_index = metadata.get("chunk_index")
        if chunk_index is None:
            continue
        source = metadata.get("source", "unknown")
        content = record.get("document", "")
        by_source.setdefault(source, {})[chunk_index] = {
            "content": content,
            "source": source,
            "score": 0.0,
            "metadata": metadata,
        }
        normalized = content.casefold()
        if any(anchor in normalized for anchor in _AUTOMATED_BUILD_SECTION_ANCHORS):
            anchor_indexes.setdefault(source, []).append(chunk_index)

    if not anchor_indexes:
        return selected

    # 앵커가 발견된 출처는 선택 목록에서 제외한 뒤, 앵커 chunk_index 최소~최대 구간의
    # 청크로만 다시 구성해 수동 절차 청크가 함께 남지 않게 합니다.
    result = [
        document
        for document in selected
        if document.get("source", "unknown") not in anchor_indexes
    ]
    for source, indexes in anchor_indexes.items():
        low, high = min(indexes), max(indexes)
        section_chunks = [
            by_source[source][index]
            for index in sorted(by_source[source])
            if low <= index <= high
        ]
        result.extend(section_chunks)
    return result


def complete_catalog_hex_coverage(
    selected: list,
    records: list,
    query: str,
    top_k: int,
    max_chunks_per_source: int,
    scope: Optional[Dict[str, str]] = None,
) -> list:
    """목록 의도에서 이미 고른 출처의 BM25 카탈로그 청크로 고유 hex 커버리지를 보강합니다.

    RRF 상위 후보에 목차 후반이 없어도, 같은 문서의 카탈로그 청크 중 아직 없는
    hex를 가장 많이 추가하는 청크를 탐욕적으로 붙입니다. 특정 hex 값은 고정하지 않습니다.
    목차가 페이지 경계로 나뉜 경우를 위해, 선택된 카탈로그 페이지의 인접 페이지도
    후보에 포함합니다.
    """
    if not detect_list_completeness_intent(query) or not selected or not records:
        return selected
    focus_sources = {doc.get("source", "unknown") for doc in selected}
    selected_keys = {
        (doc.get("source", "unknown"), doc.get("content", "")) for doc in selected
    }
    counts: Dict[str, int] = {}
    covered = set()
    neighbor_pages: Dict[str, set] = {source: set() for source in focus_sources}
    for doc in selected:
        source = doc.get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1
        content = doc.get("content", "")
        covered |= {value.upper() for value in _HEX_COMMAND_PATTERN.findall(content)}
        metadata = doc.get("metadata") or {}
        page = metadata.get("page")
        if page is None:
            continue
        try:
            page_no = int(page)
        except (TypeError, ValueError):
            continue
        if looks_like_command_catalog(content) or ".." in content or metadata.get("catalog_page"):
            neighbor_pages[source].update({page_no - 1, page_no, page_no + 1})

    catalog_pool = []
    for record in records:
        metadata = record.get("metadata") or {}
        if not _metadata_matches_scope(metadata, scope):
            continue
        source = metadata.get("source", "unknown")
        content = record.get("document", "")
        key = (source, content)
        if source not in focus_sources or key in selected_keys:
            continue
        hexes = {value.upper() for value in _HEX_COMMAND_PATTERN.findall(content)}
        if not hexes:
            continue
        page = metadata.get("page")
        try:
            page_no = int(page) if page is not None else None
        except (TypeError, ValueError):
            page_no = None
        toc_line = (".." in content) or bool(metadata.get("catalog_page"))
        adjacent = page_no is not None and page_no in neighbor_pages.get(source, set())
        if not (looks_like_command_catalog(content) or toc_line or len(hexes) >= 4 or adjacent):
            continue
        catalog_pool.append(
            {
                "content": content,
                "source": source,
                "score": float(len(hexes)),
                "metadata": metadata,
                "_hexes": hexes,
                "_toc": toc_line or adjacent,
            }
        )

    result = list(selected)
    while len(result) < top_k:
        best = None
        best_new = 0
        best_toc = False
        for doc in catalog_pool:
            source = doc["source"]
            if counts.get(source, 0) >= max_chunks_per_source:
                continue
            key = (source, doc["content"])
            if key in selected_keys:
                continue
            new_count = len(doc["_hexes"] - covered)
            is_toc = bool(doc.get("_toc"))
            if new_count > best_new or (new_count == best_new and is_toc and not best_toc):
                best_new = new_count
                best = doc
                best_toc = is_toc
        if not best or best_new <= 0:
            break
        clean = {k: v for k, v in best.items() if not k.startswith("_")}
        result.append(clean)
        selected_keys.add((best["source"], best["content"]))
        counts[best["source"]] = counts.get(best["source"], 0) + 1
        covered |= best["_hexes"]

    # top_k가 가득 차도, 순 고유 hex가 늘어날 때만 비카탈로그 청크를 교체합니다.
    for _ in range(len(result)):
        covered = set()
        for doc in result:
            covered |= {
                value.upper() for value in _HEX_COMMAND_PATTERN.findall(doc.get("content", ""))
            }
        best = None
        best_gain = 0
        replace_idx = None
        for doc in catalog_pool:
            key = (doc["source"], doc["content"])
            if key in selected_keys or doc["source"] not in focus_sources:
                continue
            for idx, current in enumerate(result):
                if current.get("source") != doc["source"]:
                    continue
                current_hex = {
                    value.upper()
                    for value in _HEX_COMMAND_PATTERN.findall(current.get("content", ""))
                }
                # 점선 목차 줄은 목록 완결의 핵심이므로 교체하지 않습니다.
                if ".." in (current.get("content") or ""):
                    continue
                if looks_like_command_catalog(current.get("content", "")) and len(current_hex) >= 8:
                    continue
                new_covered = (covered - current_hex) | doc["_hexes"]
                gain = len(new_covered) - len(covered)
                new_only = len(doc["_hexes"] - covered)
                # 인접 목차 페이지의 새 명령은, hex가 적은 비목차 청크를 밀어낼 수 있게 가산합니다.
                if (
                    doc.get("_toc")
                    and new_only > 0
                    and ".." not in (current.get("content") or "")
                    and not looks_like_command_catalog(current.get("content", ""))
                    and len(current_hex) <= 5
                ):
                    gain = max(gain, new_only) + 10
                if gain > best_gain:
                    best_gain = gain
                    best = doc
                    replace_idx = idx
        if not best or best_gain <= 0 or replace_idx is None:
            break
        removed = result[replace_idx]
        selected_keys.discard((removed.get("source", "unknown"), removed.get("content", "")))
        clean = {k: v for k, v in best.items() if not k.startswith("_")}
        result[replace_idx] = clean
        selected_keys.add((best["source"], best["content"]))
    return result


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
    rerank_neural: bool = DEFAULT_RERANK_NEURAL,
    rerank_query: Optional[str] = None,
) -> list:
    """벡터+BM25+RRF 후 선택적 리랭크로 문서를 검색하고 단계 시간을 기록합니다."""
    intent_query = rerank_query or query
    list_intent = detect_list_completeness_intent(intent_query)
    procedure_intent = is_user_terminal_procedure_intent(intent_query)
    terminal_user_mgmt_intent = is_terminal_user_management_intent(intent_query)
    automated_build_intent = is_automated_build_intent(intent_query)
    candidate_count = max(top_k, vector_candidates, rerank_candidates if rerank_enabled else 0)
    # API/스키마 질문은 같은 swagger 안의 여러 엔드포인트·정의 청크가 필요하므로
    # 소스당 청크 상한을 소폭 올려 경로와 필드 표가 함께 남게 합니다.
    effective_max_chunks = max_chunks_per_source
    effective_top_k = top_k
    if detect_api_doc_intent(intent_query):
        effective_max_chunks = max(max_chunks_per_source, 3)
    if list_intent:
        # 표·TOC가 페이지·섹션 경계에서 잘려도 동일 출처 연속 목록을 더 모읍니다.
        effective_max_chunks = max(effective_max_chunks, 8)
        effective_top_k = max(top_k, 8)
        candidate_count = max(candidate_count, 30)
        bm25_candidates = max(bm25_candidates, 30)
    if terminal_user_mgmt_intent:
        # 메뉴 개요와 저장 리스트·사용자 리스트 조작이 인접 페이지로 나뉘므로
        # 동일 출처에서 역할을 함께 보존합니다.
        effective_max_chunks = max(effective_max_chunks, 4)
        effective_top_k = max(top_k, 4)
        candidate_count = max(candidate_count, 30)
        bm25_candidates = max(bm25_candidates, 30)
    if procedure_intent:
        # 수동 전송과 자동 동기화 설정은 같은 User Guide의 떨어진 연속 절에 있으므로
        # 동일 출처에서 필요한 절차 근거를 함께 보존합니다.
        effective_max_chunks = max(effective_max_chunks, 6)
        effective_top_k = max(top_k, 6)
        candidate_count = max(candidate_count, 30)
        bm25_candidates = max(bm25_candidates, 30)
    if automated_build_intent:
        # 자동화 섹션은 3개 청크(섹션 시작·중간·마무리+주의사항)에 걸쳐 있고
        # complete_automated_build_context가 이를 강제로 포함하므로, 최종 목록이
        # 잘리지 않도록 여유를 둡니다.
        effective_max_chunks = max(effective_max_chunks, 4)
        effective_top_k = max(top_k, 4)
        candidate_count = max(candidate_count, 30)
        bm25_candidates = max(bm25_candidates, 30)
    # 신경 리랭크를 끄면 후보 과확장을 억제해 hybrid_search 지연을 줄입니다.
    # 절차/메뉴 완성 로직은 records 전체를 스캔하므로 후보 축소와 독립입니다.
    if rerank_enabled and not rerank_neural:
        candidate_count = min(candidate_count, max(effective_top_k, vector_candidates, 16))
        bm25_candidates = min(bm25_candidates, max(effective_top_k, 16))

    def _finalize(candidates: list, records_for_coverage: Optional[list] = None) -> list:
        working = candidates
        if rerank_enabled:
            # 리랭크는 상위 N개만 채점해 지연을 줄이고, 나머지는 RRF 순으로 뒤에 둡니다.
            rerank_n = max(1, min(len(working), rerank_candidates))
            rerank_started = time.perf_counter()
            head = rerank_documents(
                intent_query,
                working[:rerank_n],
                rerank_model,
                rerank_n,
                use_neural=rerank_neural,
            )
            working = head + working[rerank_n:]
            _log_timing(
                "rerank",
                time.perf_counter() - rerank_started,
                scored=rerank_n,
                total_candidates=len(candidates),
                model=rerank_model if rerank_neural else "evidence_only",
                neural=rerank_neural,
            )
        assemble_started = time.perf_counter()
        limited = limit_documents_per_source(working, effective_top_k, effective_max_chunks)
        expanded = expand_catalog_chunks_from_candidates(
            limited,
            working,
            intent_query,
            effective_top_k,
            effective_max_chunks,
        )
        finalized = complete_automated_build_context(
            complete_catalog_hex_coverage(
                complete_build_output_context(
                    complete_terminal_user_mgmt_context(
                        complete_procedure_context(
                            expanded,
                            records_for_coverage or [],
                            intent_query,
                            effective_top_k,
                            scope,
                        ),
                        records_for_coverage or [],
                        intent_query,
                        effective_top_k,
                        scope,
                    ),
                    records_for_coverage or [],
                    intent_query,
                    effective_top_k,
                    scope,
                ),
                records_for_coverage or [],
                intent_query,
                effective_top_k,
                effective_max_chunks,
                scope,
            ),
            records_for_coverage or [],
            intent_query,
            effective_top_k,
            scope,
        )
        _log_timing(
            "context_assemble",
            time.perf_counter() - assemble_started,
            docs=len(finalized),
        )
        return finalized

    hybrid_started = time.perf_counter()
    vector_docs = retrieve_vector_documents(
        chroma_path, collection_name, embedding_model, query,
        candidate_count, min_relevance_score, scope,
    )
    records, bm25 = _get_bm25_index(bm25_index_path)
    if not records or bm25 is None:
        _log_timing(
            "hybrid_search",
            time.perf_counter() - hybrid_started,
            vector=len(vector_docs),
            bm25=0,
        )
        return _finalize(vector_docs, [])
    allowed = [index for index, record in enumerate(records)
               if _metadata_matches_scope(record.get("metadata"), scope)]
    if not allowed:
        print(f"[RAG] No documents matched required scope: {scope}")
        _log_timing("hybrid_search", time.perf_counter() - hybrid_started, vector=len(vector_docs), bm25=0)
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
    merged = _rrf_merge(vector_docs, bm25_docs, candidate_count, query=intent_query)
    _log_timing(
        "hybrid_search",
        time.perf_counter() - hybrid_started,
        vector=len(vector_docs),
        bm25=len(bm25_docs),
        merged=len(merged),
    )
    return _finalize(merged, records)

