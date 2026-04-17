"""
문서 인덱싱 스크립트
====================
PDF, TXT, Markdown 파일을 청크로 분할하여 ChromaDB에 저장합니다.

사용법(권장: `rag/` 디렉터리에서 실행):
  python scripts/index_documents.py ./data/docs/
  python scripts/index_documents.py ./data/docs/ --chunk-size 500 --overlap 50
  python scripts/index_documents.py --reset   # DB 초기화
"""

import os
import re
import sys
import argparse
import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "rag_documents")
# 한국어 사내 문서 기준 기본 임베딩 모델
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
DEFAULT_CHUNK_SIZE = 400    # 토큰 기준 (대략 글자 수)
DEFAULT_OVERLAP = 50        # 청크 간 겹치는 글자 수


# ─────────────────────────────────────────
# ChromaDB 초기화
# ─────────────────────────────────────────
def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[초기화] 컬렉션 '{COLLECTION_NAME}' 삭제 완료")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


# ─────────────────────────────────────────
# 텍스트 추출
# ─────────────────────────────────────────
def extract_text_from_file(file_path: Path) -> str:
    """파일에서 텍스트를 추출합니다."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in (".txt", ".md", ".markdown", ".rst"):
        return _extract_text(file_path)
    elif suffix in (".html", ".htm"):
        return _extract_html(file_path)
    else:
        print(f"  [경고] 지원하지 않는 파일 형식: {suffix}")
        return ""


def _extract_pdf(file_path: Path) -> str:
    try:
        import pypdf
        text_parts = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    except ImportError:
        print("  [오류] pypdf 미설치. pip install pypdf")
        return ""


def _extract_text(file_path: Path) -> str:
    for encoding in ["utf-8", "cp949", "euc-kr"]:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _extract_html(file_path: Path) -> str:
    try:
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style"):
                    self.skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style"):
                    self.skip = False

            def handle_data(self, data):
                if not self.skip:
                    self.text.append(data)

        extractor = TextExtractor()
        extractor.feed(_extract_text(file_path))
        return " ".join(extractor.text)
    except Exception:
        return _extract_text(file_path)


# ─────────────────────────────────────────
# 텍스트 청킹
# ─────────────────────────────────────────
def clean_text(text: str) -> str:
    """불필요한 공백/특수문자 제거"""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list:
    """
    텍스트를 문장 경계를 고려하여 청크로 분할합니다.
    """
    text = clean_text(text)
    if not text:
        return []

    # 문장 분리 (한국어/영어 모두 지원)
    sentences = re.split(r'(?<=[.!?。\n])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)

        if current_len + s_len > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)

            # 오버랩: 마지막 몇 문장 재사용
            overlap_text = ""
            overlap_chunks = []
            for prev_s in reversed(current_chunk):
                if len(overlap_text) + len(prev_s) <= overlap:
                    overlap_chunks.insert(0, prev_s)
                    overlap_text += prev_s
                else:
                    break
            current_chunk = overlap_chunks
            current_len = len(overlap_text)

        current_chunk.append(sentence)
        current_len += s_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c for c in chunks if len(c.strip()) > 20]


# ─────────────────────────────────────────
# 인덱싱
# ─────────────────────────────────────────
def index_file(collection, file_path: Path, chunk_size: int, overlap: int) -> int:
    """단일 파일을 청크로 분할하여 ChromaDB에 저장합니다."""
    print(f"  처리 중: {file_path.name}")

    text = extract_text_from_file(file_path)
    if not text:
        print(f"  [건너뜀] 텍스트 추출 실패: {file_path.name}")
        return 0

    chunks = split_into_chunks(text, chunk_size, overlap)
    if not chunks:
        print(f"  [건너뜀] 청크 없음: {file_path.name}")
        return 0

    # 문서 ID 생성 (파일명 + 청크 인덱스 기반)
    file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        doc_id = f"{file_hash}_{i:04d}"
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append({
            "source": file_path.name,
            "path": str(file_path),
            "chunk_index": i,
            "total_chunks": len(chunks)
        })

    # 기존 문서 삭제 후 재삽입 (업데이트)
    try:
        existing = collection.get(where={"path": str(file_path)})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    # 배치 삽입 (100개씩)
    batch_size = 100
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end]
        )

    print(f"  ✓ {len(chunks)}개 청크 저장 완료")
    return len(chunks)


def index_directory(
    directory: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    reset: bool = False
):
    """디렉토리 내 모든 지원 파일을 인덱싱합니다."""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[오류] 디렉토리가 존재하지 않습니다: {directory}")
        sys.exit(1)

    supported_ext = {".pdf", ".txt", ".md", ".markdown", ".rst", ".html", ".htm"}

    files = [
        f for f in dir_path.rglob("*")
        if f.is_file() and f.suffix.lower() in supported_ext
    ]

    if not files:
        print(f"[경고] 지원되는 파일이 없습니다: {directory}")
        return

    print(f"\n=== 문서 인덱싱 시작 ===")
    print(f"디렉토리: {dir_path.absolute()}")
    print(f"파일 수: {len(files)}개")
    print(f"청크 크기: {chunk_size}자, 오버랩: {overlap}자\n")

    collection = get_collection(reset=reset)
    before_count = collection.count()

    total_chunks = 0
    for file_path in sorted(files):
        total_chunks += index_file(collection, file_path, chunk_size, overlap)

    after_count = collection.count()
    print(f"\n=== 완료 ===")
    print(f"추가된 청크: {after_count - before_count}개")
    print(f"전체 저장된 청크: {after_count}개")
    print(f"ChromaDB 경로: {Path(CHROMA_PATH).absolute()}")


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="문서를 ChromaDB에 인덱싱합니다.")
    parser.add_argument("directory", nargs="?", default="./data/docs",
                        help="인덱싱할 문서 디렉토리 (기본값: ./data/docs)")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"청크 크기 (기본값: {DEFAULT_CHUNK_SIZE}자)")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP,
                        help=f"청크 오버랩 크기 (기본값: {DEFAULT_OVERLAP}자)")
    parser.add_argument("--reset", action="store_true",
                        help="인덱싱 전 기존 DB 초기화")
    parser.add_argument("--status", action="store_true",
                        help="현재 DB 상태 확인")

    args = parser.parse_args()

    if args.status:
        collection = get_collection()
        count = collection.count()
        print(f"ChromaDB 경로: {Path(CHROMA_PATH).absolute()}")
        print(f"컬렉션: {COLLECTION_NAME}")
        print(f"임베딩 모델: {EMBEDDING_MODEL}")
        print(f"저장된 청크 수: {count}개")
        if count > 0:
            sample = collection.get(limit=3, include=["metadatas"])
            sources = list(set(m["source"] for m in sample["metadatas"]))
            print(f"샘플 출처: {sources}")
    else:
        index_directory(
            directory=args.directory,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            reset=args.reset
        )
