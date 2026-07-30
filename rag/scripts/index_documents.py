"""Index local documents into ChromaDB with BGE-M3 token-aware chunks.

The companion BM25 index is stored beside ChromaDB so the RAG pipeline can
perform hybrid (dense + keyword) retrieval.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from transformers import AutoTokenizer

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "rag_documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
# Keep chunks small enough that the answer model can use several of them without
# exhausting its context window.  These are embedding-model tokens, not LLM tokens.
DEFAULT_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "480"))
DEFAULT_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))
BM25_INDEX_PATH = Path(os.getenv("BM25_INDEX_PATH", str(Path(CHROMA_PATH) / "bm25_index.json")))

DOCUMENT_TYPE_RULES = {
    "protocol": ("protocol", "프로토콜", "주장치"),
    "install": ("설치", "install", "nsis", "빌드", "package"),
    "user_guide": ("user guide", "사용자 가이드", "사용자매뉴얼", "매뉴얼"),
}
PRODUCT_RULES = {
    # "주장치_Protocol" is the Alpeta protocol document even though its
    # filename does not repeat the product name.
    "alpeta": (
        "alpeta",
        "알페타",
        "주장치_protocol",
        "communication protocol for terminal",
    ),
}


def get_tokenizer():
    """Load the embedding model tokenizer once; chunk limits are token counts."""
    print(f"Loading tokenizer: {EMBEDDING_MODEL}")
    return AutoTokenizer.from_pretrained(EMBEDDING_MODEL)


def token_len(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        BM25_INDEX_PATH.unlink(missing_ok=True)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )


def clean_text(text: str) -> str:
    """Keep paragraph breaks but turn PDF layout line-wraps into spaces."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<![.!?。！？])\n(?!\n)", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _table_to_markdown(table) -> str:
    rows = [[str(cell or "").replace("\n", " ").strip() for cell in row] for row in table.extract()]
    rows = [row for row in rows if any(row)]
    if len(rows) < 2:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    return "\n".join([
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
        *["| " + " | ".join(row) + " |" for row in rows[1:]],
    ])


def _extract_pdf_pages(file_path: Path) -> list[tuple[int, str]]:
    """Extract PDF text one page at a time so page metadata survives chunking."""
    try:
        import fitz
    except ImportError:
        print("  [error] PyMuPDF is not installed. Run the indexer image rebuild.")
        return []

    ocr_enabled = os.getenv("PDF_OCR_FALLBACK", "false").lower() == "true"
    pages = []
    with fitz.open(file_path) as pdf:
        for page_no, page in enumerate(pdf, 1):
            page_text = page.get_text("text", sort=True).strip()
            tables = []
            try:
                tables = [_table_to_markdown(t) for t in page.find_tables().tables]
            except Exception:
                pass
            if not page_text and ocr_enabled:
                try:
                    import pytesseract
                    from PIL import Image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    page_text = pytesseract.image_to_string(image, lang=os.getenv("OCR_LANG", "kor+eng"))
                except Exception as exc:
                    print(f"  [warning] OCR skipped on page {page_no}: {exc}")
            page_content = "\n\n".join(part for part in [page_text, *tables] if part)
            if page_content.strip():
                pages.append((page_no, page_content))
    return pages


def _extract_text(file_path: Path) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _extract_html(file_path: Path) -> str:
    from html.parser import HTMLParser

    class Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text, self.skip = [], False
        def handle_starttag(self, tag, attrs):
            self.skip = self.skip or tag in ("script", "style")
        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self.skip = False
        def handle_data(self, data):
            if not self.skip:
                self.text.append(data)

    extractor = Extractor()
    extractor.feed(_extract_text(file_path))
    return " ".join(extractor.text)


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return "\n\n".join(text for _, text in _extract_pdf_pages(file_path))
    if suffix in (".txt", ".md", ".markdown", ".rst"):
        return _extract_text(file_path)
    if suffix in (".html", ".htm"):
        return _extract_html(file_path)
    return ""


def classify_document(file_path: Path) -> dict[str, str]:
    """Derive stable, queryable metadata from the filename.

    Keep this rule-based and explicit: it is predictable and can be extended as
    new internal document categories are added.
    """
    name = file_path.stem.casefold()
    document_type = "other"
    for candidate, terms in DOCUMENT_TYPE_RULES.items():
        if any(term.casefold() in name for term in terms):
            document_type = candidate
            break
    product = ""
    for candidate, terms in PRODUCT_RULES.items():
        if any(term.casefold() in name for term in terms):
            product = candidate
            break
    protocol_version = ""
    protocol_generation = ""
    if document_type == "protocol":
        version_match = re.search(r"(?:^|[_\s-])v?(\d+(?:\.\d+)*)", name)
        if version_match:
            protocol_version = version_match.group(1)
            try:
                protocol_generation = "current" if int(protocol_version.split(".")[0]) >= 4 else "legacy"
            except ValueError:
                pass
        if "communication protocol for terminal" in name:
            protocol_generation = "current"
            protocol_version = protocol_version or "4.0"
        elif "주장치_protocol" in name:
            protocol_generation = "legacy"
            protocol_version = protocol_version or "1.0"

    return {
        "document_type": document_type,
        "product": product,
        "protocol_generation": protocol_generation,
        "protocol_version": protocol_version,
    }


def _section_title(text: str) -> str:
    """Return a nearby heading for display/retrieval metadata, when present."""
    for line in text.splitlines()[:12]:
        line = line.strip()
        if re.match(r"^(?:#{1,6}\s+|\d+(?:\.\d+)*\.?\s+)", line):
            return re.sub(r"^#{1,6}\s+", "", line)[:160]
    return ""


# Only multi-level numbered lines (e.g. "3.1 출입그룹 설정") are treated as section
# starts; single "1." lines are usually list items and would over-fragment pages.
_PDF_SECTION_HEADING = re.compile(r"^\d+(?:\.\d+)+\.?\s+\S.*$")


def split_pdf_page_sections(page_text: str) -> list[tuple[str, str]]:
    """Split one PDF page into (section_title, text) blocks at numbered headings.

    Page-only chunking cuts a section body away from its title, so queries that
    match the title terms miss the chunk that holds the actual details.
    """
    sections: list[tuple[str, str]] = []
    title, lines = "", []
    for line in page_text.splitlines():
        if _PDF_SECTION_HEADING.match(line.strip()):
            if lines and "\n".join(lines).strip():
                sections.append((title, "\n".join(lines)))
            title, lines = line.strip()[:160], []
        lines.append(line)
    if lines and "\n".join(lines).strip():
        sections.append((title, "\n".join(lines)))
    return sections or [("", page_text)]


def extract_document_units(file_path: Path) -> list[dict]:
    """Return independently chunkable units with page and heading information."""
    if file_path.suffix.lower() == ".pdf":
        return [
            {"text": text, "page": page_no, "section": section or _section_title(text)}
            for page_no, page_text in _extract_pdf_pages(file_path)
            for section, text in split_pdf_page_sections(page_text)
        ]

    text = extract_text_from_file(file_path)
    if not text:
        return []
    # Preserve Markdown heading boundaries; a section title is repeated in every
    # descendant chunk so the title never gets separated from its details.
    if file_path.suffix.lower() in (".md", ".markdown", ".rst"):
        units, current_heading, current_lines = [], "", []
        for line in text.splitlines():
            heading = re.match(r"^#{1,6}\s+(.+)$", line.strip())
            if heading and current_lines:
                units.append({"text": "\n".join(current_lines), "page": 0, "section": current_heading})
                current_lines = []
            if heading:
                current_heading = heading.group(1).strip()[:160]
            current_lines.append(line)
        if current_lines:
            units.append({"text": "\n".join(current_lines), "page": 0, "section": current_heading})
        return units
    return [{"text": text, "page": 0, "section": _section_title(text)}]


def _split_oversized_sentence(tokenizer, sentence: str, chunk_size: int) -> list[str]:
    ids = tokenizer.encode(sentence, add_special_tokens=False)
    return [tokenizer.decode(ids[i:i + chunk_size], skip_special_tokens=True).strip()
            for i in range(0, len(ids), chunk_size)]


def split_into_chunks(text: str, tokenizer, chunk_size: int, overlap: int) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    # Newlines have been normalized: only punctuation or true paragraph breaks split sentences.
    sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+|\n{2,}", text) if s.strip()]
    normalized = []
    for sentence in sentences:
        normalized.extend(_split_oversized_sentence(tokenizer, sentence, chunk_size)
                          if token_len(tokenizer, sentence) > chunk_size else [sentence])

    chunks, current, current_tokens = [], [], 0
    for sentence in normalized:
        sentence_tokens = token_len(tokenizer, sentence)
        if current and current_tokens + sentence_tokens > chunk_size:
            chunks.append(" ".join(current))
            overlap_sentences, overlap_tokens = [], 0
            for previous in reversed(current):
                previous_tokens = token_len(tokenizer, previous)
                if overlap_tokens + previous_tokens > overlap:
                    break
                overlap_sentences.insert(0, previous)
                overlap_tokens += previous_tokens
            current, current_tokens = overlap_sentences, overlap_tokens
        current.append(sentence)
        current_tokens += sentence_tokens
    if current:
        chunks.append(" ".join(current))
    return [chunk for chunk in chunks if token_len(tokenizer, chunk) >= 8]


def _document_context(file_path: Path, chunk: str, metadata: dict) -> str:
    """Repeat retrieval-critical identity in every embedded chunk."""
    identity = [f"Document: {file_path.stem}", f"Type: {metadata['document_type']}"]
    if metadata.get("product"):
        identity.append(f"Product: {metadata['product']}")
    if metadata.get("page"):
        identity.append(f"Page: {metadata['page']}")
    if metadata.get("section"):
        identity.append(f"Section: {metadata['section']}")
    return f"[{' | '.join(identity)}]\n{chunk}"


def index_file(collection, tokenizer, file_path: Path, chunk_size: int, overlap: int) -> int:
    print(f"  indexing: {file_path.name}")
    units = extract_document_units(file_path)
    chunks = []
    document_metadata = classify_document(file_path)
    for unit in units:
        for chunk in split_into_chunks(unit["text"], tokenizer, chunk_size, overlap):
            metadata = {**document_metadata, "page": unit["page"], "section": unit["section"]}
            chunks.append((chunk, metadata))
    if not chunks:
        print("  [skip] no extractable chunk")
        return 0
    file_hash = hashlib.sha256(str(file_path.resolve()).encode()).hexdigest()[:12]
    existing = collection.get(where={"path": str(file_path)})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
    collection.add(
        ids=[f"{file_hash}_{i:04d}" for i in range(len(chunks))],
        documents=[_document_context(file_path, chunk, metadata) for chunk, metadata in chunks],
        metadatas=[{
            "source": file_path.name,
            "path": str(file_path),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "title": file_path.stem,
            **metadata,
        } for i, (_, metadata) in enumerate(chunks)],
    )
    print(f"  {len(chunks)} chunks indexed")
    return len(chunks)


def write_bm25_index(collection) -> None:
    """Persist corpus data used by rank_bm25 in the serving pipeline."""
    data = collection.get(include=["documents", "metadatas"])
    records = [{"id": doc_id, "document": doc, "metadata": metadata}
               for doc_id, doc, metadata in zip(data["ids"], data["documents"], data["metadatas"])]
    BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    BM25_INDEX_PATH.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    print(f"  BM25 index written: {BM25_INDEX_PATH} ({len(records)} chunks)")


def main():
    parser = argparse.ArgumentParser(description="Index documents with BGE-M3 token-aware chunking.")
    parser.add_argument("directory", nargs="?", default="./data/docs")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Maximum embedding tokens per chunk")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="Token overlap between chunks")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    collection = get_collection(reset=args.reset)
    if args.status:
        print(f"Collection: {COLLECTION_NAME}\nEmbedding model: {EMBEDDING_MODEL}\nChunks: {collection.count()}\nBM25 index: {BM25_INDEX_PATH}")
        return
    directory = Path(args.directory)
    if not directory.exists():
        sys.exit(f"Directory does not exist: {directory}")
    files = [p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".txt", ".md", ".markdown", ".rst", ".html", ".htm"}]
    if not files:
        sys.exit(f"No supported documents in: {directory}")
    tokenizer = get_tokenizer()
    for file_path in sorted(files):
        index_file(collection, tokenizer, file_path, args.chunk_size, args.overlap)
    write_bm25_index(collection)
    print(f"Completed. ChromaDB chunks: {collection.count()}")


if __name__ == "__main__":
    main()
