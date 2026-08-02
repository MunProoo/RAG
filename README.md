# LLM → RAG → LLM Pipeline (Open WebUI + Ollama)

## 문서 가이드

| 문서 | 대상 |
|------|------|
| [RAG_PIPELINE_GUIDE.md](RAG_PIPELINE_GUIDE.md) | 구조·검색 품질·인덱싱·평가·트러블슈팅 (상세) |
| [RAG_PIPELINE_GUIDE.html](RAG_PIPELINE_GUIDE.html) | 위 가이드 HTML (브라우저용, md와 동기화) |
| [RAG_PIPELINE_GUIDE_EASY.md](RAG_PIPELINE_GUIDE_EASY.md) | 비전공자용 — 질문이 답으로 나오기까지·FAQ |
| [CHANGELOG.md](CHANGELOG.md) | 변경 이력 (Unreleased 포함) |
| [PL_FAILURE_LOG.md](PL_FAILURE_LOG.md) | PL 루프 실패·활성 예방 체크리스트 |

## 최근 핵심 개선 (2026-08 요약)

- **파일 역할 구분**: NSIS `.bat`(자동화) / `.nsi`(스크립트) / `.exe`(산출물). 설치 확인 폴더는 `D:\nsis\install`, device setup은 `D:\nsis\Alpeta\setup` 등으로 구분.
- **API/Swagger**: `document_type=api`, FaceWT 등 CamelCase 보존, product 필터 완화. swagger md 재생성 후 `--reset` 재인덱싱.
- **v4 프로토콜 전체 리스트**: TOC/카탈로그 큰 청크 + 목록 완결성 규칙.
- **User Guide 절차**: 단말기 추가·자동동기화의 **두 방법 분리**, `[단말기리스트]` 등 UI 표기 보존.
- **자동화 버전 빌드**: `build_install.bat` 하위 작업 포함 1~7단계 완결, 수동(MakeNSISW) 혼입 금지.
- **평가**: 회귀 약 **60개** (`test_rag_regression.py`) + 골든 질문셋. 성공 = 출처 + 필수 키워드 전부. 이상적 답변은 `rag/data/eval/artifacts/ideal_answer_*.md`.
- **연동**: pipelines `http://pipelines:9099`, DB 복구 시 chat 스키마(`pinned`/`meta`/`folder_id`, chat JSON)·config 확인. qwen은 `think:false`, 첫 토큰 전 긴 동기 작업 시 UI 무응답처럼 보일 수 있음.

상세·운영 주의는 위 가이드와 `PL_FAILURE_LOG.md`를 보세요. 비밀값·전체 로그는 문서에 넣지 않습니다.

## Retrieval and indexing defaults

- Default embeddings use `BAAI/bge-m3`. Because vector spaces differ, run a full reset and re-index after changing the embedding model.
- Chunks use the BGE-M3 tokenizer rather than character length: `480` tokens with `80` tokens of overlap by default. Each embedded chunk includes document type, product, page, and section metadata.
- PDF text is extracted by PyMuPDF in layout-aware order. Single layout line breaks become spaces and paragraph breaks remain. For scanned PDFs only, set `PDF_OCR_FALLBACK=true` after installing Tesseract OCR.
- The indexer writes `bm25_index.json` next to ChromaDB. The pipeline combines BGE-M3 vector and BM25 keyword rankings using Reciprocal Rank Fusion (RRF).
- RRF 후보는 크로스 인코더 리랭커(`BAAI/bge-reranker-v2-m3`, `RERANK_ENABLED`)가 재채점합니다. 모델 로드에 실패하면 자동으로 RRF 순위를 그대로 사용합니다.
- BM25 인덱스는 파일 mtime 기준으로 프로세스 내 캐시되어, 질문마다 다시 로드/구축하지 않습니다. 재인덱싱하면 다음 질문부터 자동 반영됩니다.
- PDF는 페이지 단위에 더해 `3.1`처럼 다단계 번호가 붙은 제목 줄에서 섹션을 나눠, 제목과 본문이 같은 청크에 남도록 합니다.
- Swagger 변환(`scripts/swagger_yaml_to_md.py`)은 각 엔드포인트 섹션에 그 API가 참조하는 **스키마 필드 표를 함께 인라인**합니다(중첩 참조 2단계까지). API 상세와 스키마 정의가 원문에서 멀리 떨어져 있어도 한 청크로 같이 검색됩니다.

이 프로젝트는 **Windows 호스트에서 실행 중인 Ollama**를 사용하면서, **Docker Compose로 Open WebUI + Pipelines 서버 + 인덱싱(indexer)**를 띄워
사내 문서 기반 RAG 질의응답을 제공하는 파이프라인입니다.

## 동작 구조

```
클라이언트 질문 (Open WebUI)
        ↓
[LLM 1] 질문 재작성 (검색 최적화)
        ↓
[ChromaDB] 벡터 유사도 검색 (로컬 `rag/data/chroma_db`)
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

1. `rag/data/docs/` 폴더에 문서를 넣습니다. (레포에 샘플 문서가 포함되어 있을 수 있습니다.)
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
- ImageServer(정적 이미지): `http://localhost:8090`

### 3) 문서 인덱싱 (컨테이너에서 실행)

`rag/data/docs/`에 문서를 넣은 뒤, 아래 명령으로 ChromaDB를 생성/갱신합니다.

```bash
# 기본 인덱싱
docker compose run --rm indexer

# 상태 확인
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --status

# DB 초기화 후 재인덱싱
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
```

### 검색 정확도 변경 후 필수 적용 절차

이번 인덱서는 파일명에서 `document_type`(`protocol`, `user_guide`, `install`, **`api`**)과 `product`(현재 `alpeta`)를 저장합니다. 질문에 “Alpeta 프로토콜”처럼 문서 종류가 있으면 **검색 전에** 이 메타데이터로 범위를 제한하므로, 관련 규칙을 바꿨다면 기존 DB를 초기화하여 재인덱싱해야 합니다.  
파일명에 swagger/openapi/api가 있으면 `document_type=api`입니다. API 의도 검색에서는 product 미태그 문서가 배제되지 않도록 필터가 완화됩니다.

```bash
docker compose build indexer
docker compose up -d --force-recreate pipelines
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset

# 모델 없이 실행 가능한 검색/스트림 회귀 테스트 (약 60개)
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/test_rag_regression.py
```

#### Swagger Markdown 재생성 후 재인덱싱

```bash
docker compose run --rm --no-deps --entrypoint python indexer \
  /app/scripts/swagger_yaml_to_md.py \
  --input /app/docs/swagger_kr.yaml \
  --output /app/docs/swagger_kr.md
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

#### 파이프라인 코드만 변경한 경우

재인덱싱 없이 recreate만 하면 됩니다.

```bash
docker compose up -d --force-recreate pipelines
```

품질 변경 후 권장 검증 순서: recreate → Ollama `/api/chat` readiness → pipe 원문 assertion → eval(basic/`--rerank`) → regression. 근거는 `PL_FAILURE_LOG.md` [PLF-20260802-002].

### 검색 품질 평가 (골든 질문셋)

`rag/data/eval/golden_questions.json`에 실제 질문과 기대 출처/키워드를 적어 두면, 아래 명령으로 검색 적중률을 측정할 수 있습니다. 검색·인덱싱 로직을 바꿀 때마다 실행해 회귀를 조기에 잡고, **운영 중 실패한 질문을 계속 추가**하세요.

**평가 성공 조건**: 기대 출처 적중 **그리고** 해당 질문의 필수 키워드가 **모두** 검색 결과에 포함되어야 합니다. 출처만 맞고 키워드가 빠지면 실패입니다. [PLF-20260801-002]

이상적 답변 기준(대조용): `rag/data/eval/artifacts/ideal_answer_facewt_swagger_kr.md`, `ideal_answer_nsis_auto_build.md`, `ideal_answer_terminal_user_sync.md`

```bash
# 인덱싱이 끝난 상태에서 실행
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py

# 리랭커까지 포함해 평가
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py --rerank
```

재인덱싱 후 Open WebUI에서 아래를 확인하세요.

```text
Alpeta 프로토콜의 Param3[0]과 Param3[1]을 설명해줘.
```

참조 출처에 `주장치_Protocol_v1.0.pdf`만 표시되어야 하며, `Alpeta User Guide.pdf`나 설치 패키지 매뉴얼이 섞이면 안 됩니다.

인덱싱 결과는 로컬의 `rag/data/chroma_db/`에 저장되며, `pipelines` 서비스가 동일 폴더를 마운트하여 검색에 사용합니다.

#### ChromaDB 버전 정합성(중요)

`pipelines`와 `indexer`는 **같은 `rag/data/chroma_db` 디렉터리를 공유**합니다.  
따라서 두 컨테이너의 `chromadb` 버전이 다르면(예: `1.0.20` vs `1.5.7`) 퍼시스턴트 DB 로딩 과정에서 **Rust panic** 같은 치명 오류가 날 수 있습니다.

이 레포는 `rag/requirements.txt`에서 `chromadb`를 **고정(pin)** 해서 두 컨테이너가 동일 버전을 쓰도록 맞춥니다.

`rag/requirements.txt`를 변경했다면(특히 `chromadb` 버전 변경), 아래를 꼭 수행하세요.

```bash
# indexer 이미지 재빌드(고정된 requirements 반영)
docker compose build --no-cache indexer

# (권장) chroma_db 완전 초기화 후 재인덱싱
docker compose down
# Windows 탐색기에서 rag/data/chroma_db 폴더 삭제
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

- **컨테이너 간(권장, compose env와 동일)**: Base URL `http://pipelines:9099`, API Key `0p3n-w3bu!`
- **호스트 브라우저에서 직접 넣을 때**: Base URL `http://localhost:9099`, API Key 동일

그 후 모델/프로바이더 선택 화면에서 **도우미(`rag_pipeline`)**를 선택하여 대화하면,
인덱싱된 `rag/data/docs/` 기반으로 RAG 응답이 생성됩니다.

**Postgres/config 복구 후** [PLF-20260802-001]: `config`가 비거나 alembic만 stamp된 경우 OpenAI 연결·`chat` 스키마(`pinned`/`meta`/`folder_id`, `chat` JSON 타입)가 빠질 수 있습니다.  
볼륨 wipe 없이 `config.openai.api_base_urls`=`http://pipelines:9099`를 다시 넣고, `chat` 테이블 컬럼/타입을 현재 Open WebUI 모델에 맞춘 뒤 open-webui를 재시작하세요. env만으로는 DB에 박힌 빈 설정을 덮지 못할 수 있습니다. 복구 후 `chats/new` + chat completions와 pipelines inlet/completions 로그로 연동을 확인하세요.

`PIPELINES_DIR`에 빈 `__init__.py`를 두지 마세요. pipelines 런타임이 모듈로 로드해 실패 부산물을 만듭니다. [PLF-20260801-001]

## RAG 파이프라인(`rag/pipelines/rag_pipeline.py`) 요약

- **후속 질문 문맥화**: "그거", "해당" 같은 지시어나 아주 짧은 질문이 감지되면, 최근 대화(2턴)를 반영해 혼자 봐도 이해되는 독립형 질문으로 변환한 뒤 검색·범위 필터·초점 추출·리랭킹에 사용합니다. 감지될 때만 LLM을 추가 호출하며, 실패 시 원본 질문으로 폴백합니다.
- **기술 토큰·역할**: `.bat`/`.nsi`/`.exe`와 경로 역할(`D:\nsis\install` vs `D:\nsis\Alpeta\setup`)을 구분해 검색·답변에 반영합니다.
- **API 스코프**: Swagger/FaceWT 등 API 질문은 `document_type=api` 중심으로 검색하고, User Guide·Protocol로 API를 대체하지 않습니다.
- **목록·자동화 절차**: v4 전부 리스트 완결성, NSIS 자동화 버전 1~7단계 완결(수동 혼입 금지), User Guide 단말기 이중 방법·UI 표기 보존.
- **질문 초점**: `…에 대해 설명`, `…를 소개` 등 패턴이 맞으면, 검색된 청크 중 **그 이름(또는 구)**이 본문에 포함된 것만 남겨 다른 인물·문서가 섞이는 것을 줄입니다.
- **이미지**: 참고 청크에서 `![대체텍스트](URL)` 형태를 **실제로 찾았을 때만** 별도 블록을 붙이고, 답변 본문 **맨 위**에 두도록 유도합니다. 없을 때는 URL을 지어내지 않습니다.
- **답변 톤**: "제공된 참고 문서에는 … 포함되어 있지 않습니다" 같은 **긴 면책·부정 문단**을 피하도록 지시합니다.
- **qwen thinking**: Ollama 호출에 `think: false`를 유지합니다. 없으면 content가 비어 UI에 점만 보일 수 있습니다.

## 이미지(ImageServer) 사용

`docker-compose.yml`의 **`imageserver`** 서비스(nginx)가 `rag/data/assets/`를 웹 루트로 서빙합니다.

문서/답변에서 이미지 URL이 필요하면 파일을 `rag/data/assets/`에 넣고 아래 URL로 참조하세요.

- 호스트(PC 브라우저): `http://localhost:8090/<파일명>`
- 컨테이너 내부(서비스 간): `http://imageserver/<파일명>`

**문서(Markdown) 작성 팁**

- 인물·절별로 `## 제목`으로 나누고, 그 섹션 안에 `![설명](http://localhost:8090/파일.jpg)`를 두면 검색·이미지 추출에 유리합니다. (샘플: `rag/data/docs/Test.md`)
- 답변에 그림이 **깨져 보이면** 이미지를 여는 주체가 어디인지에 따라 URL이 달라질 수 있습니다. 필요 시 `http://host.docker.internal:8090/...`(호스트의 nginx 포트로 노출된 경우) 등으로 조정하세요.

## Open WebUI 후속 질문(답변 아래 칩) 끄기

`docker-compose.yml`의 `open-webui`에 **`ENABLE_FOLLOW_UP_GENERATION=false`** 가 들어 있습니다.  
Open WebUI는 설정을 DB에 저장하는 경우가 많아, **예전에 켜 둔 값이 남아 있으면 env만으로는 안 꺼질 수 있습니다.** 그때는 UI에서 끄세요.

- 관리자(전역): **Admin → Settings → Interface → Follow Up Generation**
- 사용자: **Settings → Interface → Chat → Follow-Up Auto-Generation**

공식 안내: [Follow-Up Prompts](https://docs.openwebui.com/features/chat-conversations/chat-features/follow-up-prompts/)

## 환경변수(주요)

### Open WebUI(`open-webui` 서비스)

| 변수 | 예시 | 설명 |
|------|------|------|
| `ENABLE_FOLLOW_UP_GENERATION` | `false` | 답변 아래 후속 질문(칩) 자동 생성 끄기(위 UI 병행 권장) |

### Pipelines / Indexer

파이프라인 서버(`pipelines`)와 인덱서(`indexer`)는 아래 변수로 동작을 제어합니다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` (컨테이너 기준) | Windows 호스트 Ollama 주소 |
| `REWRITE_MODEL` | `qwen3.5:4b` | 질문 재작성용 모델 |
| `ANSWER_MODEL` | `qwen3.5:4b` | 최종 답변용 모델 |
| `CHROMA_PATH` | `/app/chroma_db` (컨테이너 기준) | ChromaDB 저장 경로 |
| `CHROMA_COLLECTION` | `rag_documents` | 컬렉션 이름 |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | 임베딩 모델(한국어 기본) |
| `TOP_K` | `5` (`docker-compose`에서는 `4`) | 검색 청크 수 |
| `MIN_SCORE` | `0.3` | 최소 관련도 점수 (0~1) |
| `MAX_CHUNKS_PER_SOURCE` | `2` | 한 출처가 최종 컨텍스트에서 차지할 최대 청크 수 |
| `MAX_CONTEXT_CHARS` | `12000` | 답변 모델에 전달할 검색 문맥의 최대 문자 수 |
| `OLLAMA_NUM_CTX` | `8192` | Ollama 답변 모델 컨텍스트 창 크기 |
| `OLLAMA_NUM_PREDICT` | `2048` | 한 답변의 최대 생성 토큰 수 |
| `OLLAMA_READ_TIMEOUT` | `600` | 긴 스트림 응답에 적용할 읽기 타임아웃(초) |
| `RERANK_ENABLED` | `true` | 크로스 인코더 리랭커 사용 여부(로드 실패 시 자동 폴백) |
| `RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | 리랭커 모델(첫 사용 시 다운로드) |
| `RERANK_CANDIDATES` | `20` | 리랭커에 전달할 RRF 후보 수 |
| `USE_QUERY_REWRITE` | `true` | `false`면 LLM 질문 재작성을 생략(원본 질문+규칙 확장만 사용, 지연 감소) |
| `CONTEXTUALIZE_FOLLOW_UP` | `true` | 후속 질문("그거 자세히", "해당 API 수정은?")을 이전 대화를 반영한 독립형 질문으로 바꿔 검색 |

## 파일 구조

```
RAG_MJY/
├── docker-compose.yml           # Open WebUI 스택 + pipelines + indexer + imageserver
├── README.md
├── RAG_PIPELINE_GUIDE.md        # 상세 가이드
├── RAG_PIPELINE_GUIDE.html
├── RAG_PIPELINE_GUIDE_EASY.md   # 비전공자용
├── CHANGELOG.md
├── PL_FAILURE_LOG.md
├── rag/
│   ├── Dockerfile.indexer
│   ├── requirements.txt
│   ├── pipelines/
│   │   └── rag_pipeline.py      # Open WebUI Pipelines 서버가 로드
│   ├── scripts/
│   │   ├── index_documents.py   # 문서 인덱싱(ChromaDB + BM25)
│   │   ├── swagger_yaml_to_md.py
│   │   ├── eval_retrieval.py    # 골든 질문셋 검색 평가
│   │   ├── test_rag_regression.py # 검색/스트림 회귀(~60)
│   │   └── test_pipeline.py     # 로컬 테스트 스크립트(선택)
│   └── data/
│       ├── docs/                # 인덱싱할 문서
│       ├── eval/                # 골든 + artifacts/ideal_answer_*.md
│       ├── chroma_db/           # ChromaDB 저장소(자동 생성)
│       └── assets/              # ImageServer 정적 파일
└── ImageServer/
    └── README.txt
```

## 운영 팁

- **문서를 바꿨다면**: 인덱싱을 다시 실행해야 검색 결과에 반영됩니다.
- **파일명/경로가 바뀌면**(예: `Test.txt` 삭제 후 `Test.md`만 둔 경우): Chroma에 예전 출처 청크가 남을 수 있으므로, 필요하면 **`--reset` 후 재인덱싱**이 가장 확실합니다.
- **청킹·메타데이터·swagger md·임베딩 모델**을 바꾸면 `--reset` 재인덱싱이 필요합니다. TOC 큰 청크·`document_type=api` 반영도 동일합니다.
- **한국어 검색 품질**: `EMBEDDING_MODEL`을 바꾸면 **반드시 `--reset` 후 재인덱싱**하세요. (임베딩이 달라지면 기존 벡터가 무의미해짐)
- **첫 질문이 유난히 느릴 때**: 임베딩(BGE-M3)과 리랭커 모델의 최초 다운로드/로딩 때문입니다. 이후에는 프로세스 캐시로 빨라집니다. 다운로드가 불가능한 환경이면 `RERANK_ENABLED=false`로 두세요.
- **응답이 전반적으로 느릴 때 / 첫 토큰이 안 올 때**: `REWRITE_MODEL`과 `ANSWER_MODEL`을 같은 모델로 두면 Ollama의 모델 스왑이 없어집니다. 그래도 느리면 `USE_QUERY_REWRITE=false`로 재작성 LLM 호출을 생략할 수 있습니다. 재작성·검색·리랭크가 첫 yield 전에 길게 돌면 UI가 무응답처럼 보일 수 있습니다. [PLF-20260801-001]
- **답이 점만 보이거나 비어 보일 때**: qwen3.5는 `think:false` 없이 호출하면 content가 비는 경우가 있습니다.
- **도우미가 목록에 없을 때**: OpenAI Base URL·DB `config`·chat 스키마를 확인하세요. [PLF-20260802-001]
- **답변이 끊길 때**: pipelines 로그의 `[RAG] Ollama stream completed`에서 `reason=length`인지 확인하세요. `length`면 `OLLAMA_NUM_PREDICT` 또는 `OLLAMA_NUM_CTX`를 올리되, VRAM 사용량도 함께 확인하세요.
- **Ollama 접근이 안 될 때**: 컨테이너에서 호스트로 접근하는 주소는 일반적으로 `host.docker.internal`입니다(Windows Docker Desktop 기준).
- **로컬로 파이프라인만 테스트**: `rag/` 디렉터리에서 `python scripts/test_pipeline.py` (Ollama가 로컬에서 떠 있어야 함).
- **PL 개발**: 작업 전 `PL_FAILURE_LOG.md` 예방 체크리스트를 수용 기준에 포함하고, 비밀값·토큰·전체 로그 덤프는 남기지 않습니다.
