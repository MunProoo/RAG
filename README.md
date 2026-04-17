# LLM → RAG → LLM Pipeline (Open WebUI + Ollama)

이 프로젝트는 **Windows 호스트에서 실행 중인 Ollama**를 사용하면서, **Docker Compose로 Open WebUI + Pipelines 서버 + 인덱싱(indexer)**를 띄워
사내 문서 기반 RAG 질의응답을 제공하는 파이프라인입니다.

## 동작 구조

```
클라이언트 질문 (Open WebUI)
        ↓
[LLM 1] 질문 재작성 (검색 최적화)
        ↓
[ChromaDB] 벡터 유사도 검색 (로컬 chroma_db)
        ↓
컨텍스트 조합 (질문 + 검색 문서)
        ↓
[LLM 2] 최종 답변 생성 (스트리밍)
        ↓
Open WebUI에 응답 표시
```

## 전제 조건

- **Windows 호스트에 Ollama가 실행 중**이어야 합니다. (기본: `http://localhost:11434`)
- **Docker Desktop 실행 중**이어야 합니다. (`docker compose` 사용)

## 빠른 시작 (권장 절차)

### 1) 문서 준비

1. 프로젝트 루트에 `docs/` 폴더를 만들고 문서를 넣습니다.
2. 현재 인덱싱 스크립트가 지원하는 형식은 아래와 같습니다.

- **지원**: `.md`, `.txt`, `.pdf`, `.html`, `.htm`, `.rst`
- **미지원**: Word (`.doc`, `.docx`)  
  - Word 문서는 **PDF 또는 Markdown/TXT로 변환 후** 넣어주세요.

### 2) 스택 실행

```bash
docker compose up -d
```

기본 포트:
- Open WebUI: `http://localhost:8080`
- Pipelines(OpenAI 호환 API): `http://localhost:9099`

### 3) 문서 인덱싱 (컨테이너에서 실행)

`docs/`에 문서를 넣은 뒤, 아래 명령으로 ChromaDB를 생성/갱신합니다.

```bash
# 기본 인덱싱
docker compose run --rm indexer

# 상태 확인
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --status

# DB 초기화 후 재인덱싱
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
```

인덱싱 결과는 로컬의 `./chroma_db/`에 저장되며, `pipelines` 서비스가 동일 폴더를 마운트하여 검색에 사용합니다.

#### ChromaDB 버전 정합성(중요)

`pipelines`와 `indexer`는 **같은 `./chroma_db` 디렉터리를 공유**합니다.  
따라서 두 컨테이너의 `chromadb` 버전이 다르면(예: `1.0.20` vs `1.5.7`) 퍼시스턴트 DB 로딩 과정에서 **Rust panic** 같은 치명 오류가 날 수 있습니다.

이 레포는 `requirements.txt`에서 `chromadb`를 **고정(pin)** 해서 두 컨테이너가 동일 버전을 쓰도록 맞춥니다.

`requirements.txt`를 변경했다면(특히 `chromadb` 버전 변경), 아래를 꼭 수행하세요.

```bash
# indexer 이미지 재빌드(고정된 requirements 반영)
docker compose build --no-cache indexer

# (권장) chroma_db 완전 초기화 후 재인덱싱
docker compose down
# Windows 탐색기에서 ./chroma_db 폴더 삭제
docker compose up -d
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
```

버전 확인(재시작 중이어도 1회 실행 컨테이너로 확인 가능):

```bash
docker compose run --rm --entrypoint python pipelines -c "import chromadb; print(chromadb.__version__)"
docker compose run --rm indexer python -c "import chromadb; print(chromadb.__version__)"
```

### 4) Open WebUI에서 파이프라인 사용 (Pipelines 메뉴 없이 연결)

Open WebUI 버전에 따라 “관리자→Pipelines” 메뉴가 없을 수 있습니다.  
이 경우 **OpenAI 호환(Provider) 연결**로 `pipelines`를 등록해야 합니다.

- **Base URL**: `http://localhost:9099`
- **API Key**: 임의 값(예: `0p3n-w3bu!`)

그 후 모델/프로바이더 선택 화면에서 **파이프라인 모델(예: `LLM → RAG → LLM Pipeline`)**을 선택하여 대화하면,
인덱싱된 `docs/` 기반으로 RAG 응답이 생성됩니다.

## 환경변수(주요)

파이프라인 서버(`pipelines`)와 인덱서(`indexer`)는 아래 변수로 동작을 제어합니다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` (컨테이너 기준) | Windows 호스트 Ollama 주소 |
| `REWRITE_MODEL` | `qwen3.5:4b` | 질문 재작성용 모델 |
| `ANSWER_MODEL` | `qwen3.5:4b` | 최종 답변용 모델 |
| `CHROMA_PATH` | `/app/chroma_db` (컨테이너 기준) | ChromaDB 저장 경로 |
| `CHROMA_COLLECTION` | `rag_documents` | 컬렉션 이름 |
| `EMBEDDING_MODEL` | `jhgan/ko-sroberta-multitask` | 임베딩 모델(한국어 기본) |
| `TOP_K` | `5` | 검색 청크 수 |
| `MIN_SCORE` | `0.3` | 최소 관련도 점수 (0~1) |

## 파일 구조

```
RAG_PipeLine/
├── docker-compose.yml
├── Dockerfile.indexer
├── pipelines/
│   ├── __init__.py
│   └── rag_pipeline.py          # Open WebUI Pipelines 서버가 로드
├── scripts/
│   ├── index_documents.py       # 문서 인덱싱(ChromaDB)
│   └── test_pipeline.py         # 로컬 테스트 스크립트(선택)
├── docs/                        # 인덱싱할 문서 폴더(직접 생성)
├── chroma_db/                   # ChromaDB 저장소(자동 생성)
├── requirements.txt
└── README.md
```

## 운영 팁

- **문서를 바꿨다면**: 인덱싱을 다시 실행해야 검색 결과에 반영됩니다.
- **한국어 검색 품질**: `EMBEDDING_MODEL`을 바꾸면 **반드시 `--reset` 후 재인덱싱**하세요. (임베딩이 달라지면 기존 벡터가 무의미해짐)
- **Ollama 접근이 안 될 때**: 컨테이너에서 호스트로 접근하는 주소는 일반적으로 `host.docker.internal`입니다(Windows Docker Desktop 기준).
