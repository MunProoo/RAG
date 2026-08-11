# LLM → RAG → LLM Pipeline (Open WebUI + Ollama)

## 문서 가이드

| 문서 | 대상 |
|------|------|
| [RAG_PIPELINE_GUIDE.md](RAG_PIPELINE_GUIDE.md) | 구조·검색 품질·인덱싱·평가·트러블슈팅 (상세) |
| [RAG_PIPELINE_GUIDE.html](RAG_PIPELINE_GUIDE.html) | 위 가이드 HTML (브라우저용, md와 동기화) |
| [RAG_PIPELINE_GUIDE_EASY.md](RAG_PIPELINE_GUIDE_EASY.md) | 비전공자용 — 질문이 답으로 나오기까지·FAQ |
| [CHANGELOG.md](CHANGELOG.md) | 변경 이력 (Unreleased 포함) |
| [PL_FAILURE_LOG.md](PL_FAILURE_LOG.md) | PL 루프 실패·활성 예방 체크리스트 |

## 최근 핵심 개선 (요약)

- **하이브리드 검색**: 벡터(BGE-M3) + BM25 + RRF, 선택적 리랭크
- **문서 메타데이터 필터**: `document_type`(protocol / user_guide / install / api) 등으로 검색 범위 제한
- **후속 질문 문맥화**: 「표로」「정리해줘」 등 짧은 후속을 최근 주제에 묶고, 주제 교차 오염 방지
- **평가**: `test_rag_regression.py` + `rag/data/eval/golden_questions.json` (성공 = 출처 + 필수 키워드)
- **공개 데모 문서**: `rag/data/docs/sample_*.md` 만 저장소에 포함 (실문서는 로컬/비공개)
- **Ollama 컨테이너화**: 초기에는 Windows 호스트 Ollama를 썼으나, 지금은 Compose의 **GPU `ollama` 서비스**가 기본입니다 (`http://ollama:11434`)

상세·운영 주의는 위 가이드와 `PL_FAILURE_LOG.md`를 보세요. 비밀값·사내 문서 원문·전체 로그는 문서에 넣지 않습니다.

## Retrieval and indexing defaults

- Default embeddings use `BAAI/bge-m3`. Because vector spaces differ, run a full reset and re-index after changing the embedding model.
- Chunks use the BGE-M3 tokenizer rather than character length: `480` tokens with `80` tokens of overlap by default. Each embedded chunk includes document type, product, page, and section metadata.
- PDF text is extracted by PyMuPDF in layout-aware order. Single layout line breaks become spaces and paragraph breaks remain. For scanned PDFs only, set `PDF_OCR_FALLBACK=true` after installing Tesseract OCR.
- The indexer writes `bm25_index.json` next to ChromaDB. The pipeline combines BGE-M3 vector and BM25 keyword rankings using Reciprocal Rank Fusion (RRF).
- RRF 후보는 크로스 인코더 리랭커(`BAAI/bge-reranker-v2-m3`, `RERANK_ENABLED`)가 재채점합니다. 모델 로드에 실패하면 자동으로 RRF 순위를 그대로 사용합니다.
- BM25 인덱스는 파일 mtime 기준으로 프로세스 내 캐시되어, 질문마다 다시 로드/구축하지 않습니다. 재인덱싱하면 다음 질문부터 자동 반영됩니다.
- PDF는 페이지 단위에 더해 `3.1`처럼 다단계 번호가 붙은 제목 줄에서 섹션을 나눠, 제목과 본문이 같은 청크에 남도록 합니다.
- Swagger 변환(`scripts/swagger_yaml_to_md.py`)은 각 엔드포인트 섹션에 그 API가 참조하는 **스키마 필드 표를 함께 인라인**합니다(중첩 참조 2단계까지). API 상세와 스키마 정의가 원문에서 멀리 떨어져 있어도 한 청크로 같이 검색됩니다.

이 프로젝트는 **Docker Compose**로 Open WebUI + Pipelines + **Ollama(GPU 컨테이너)** + 인덱싱(indexer)을 띄워
문서 기반 RAG 질의응답을 제공하는 파이프라인입니다.

초기에는 Windows 호스트 Ollama(`host.docker.internal:11434`)를 썼지만, 호스트 CUDA/포트 이슈를 줄이기 위해
지금은 compose의 **`ollama` 서비스**가 기본 LLM입니다. pipelines·open-webui는 `http://ollama:11434`로 붙습니다.

## 동작 구조

```
클라이언트 질문 (Open WebUI)
        ↓
[Pipelines] 질문 재작성(선택) → 하이브리드 검색 → 컨텍스트 조립
        ↓
[ChromaDB + BM25] 로컬 `rag/data/chroma_db`
        ↓
[Ollama 컨테이너] 최종 답변 생성 (스트리밍, GPU)
        ↓
Open WebUI에 응답 표시
```

## 전제 조건

- **Docker Desktop 실행 중** (`docker compose` 사용). GPU를 쓰려면 Docker GPU(WSL2/NVIDIA) 설정이 필요합니다.
- **호스트에서 11434를 쓰는 Ollama 앱/서비스는 중지**하세요. compose `ollama`가 같은 포트를 사용합니다.
- 모델 파일은 Windows `%USERPROFILE%\.ollama`를 컨테이너에 바인드하므로, 예전에 호스트에서 `pull`해 둔 모델을 그대로 재사용할 수 있습니다. **이 폴더는 삭제하지 마세요.**

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
- Ollama API: `http://localhost:11434` (컨테이너, 호스트에서도 접근 가능)
- ImageServer(정적 이미지): `http://localhost:8090`

모델이 아직 없다면 Ollama 컨테이너에서 pull 합니다. (`docker-compose` 기본 답변 모델 예: `qwen3.5:4b`)

```bash
docker compose exec ollama ollama pull qwen3.5:4b
docker compose exec ollama ollama list
# 준비 확인 (호스트에서)
curl http://localhost:11434/api/tags
```

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

이번 인덱서는 파일명에서 `document_type`(`protocol`, `user_guide`, `install`, **`api`**)과 `product`를 저장할 수 있습니다. 질문에 문서 종류가 있으면 **검색 전에** 이 메타데이터로 범위를 제한하므로, 관련 규칙을 바꿨다면 기존 DB를 초기화하여 재인덱싱해야 합니다.  
파일명에 swagger/openapi/api가 있으면 `document_type=api`입니다. API 의도 검색에서는 product 미태그 문서가 배제되지 않도록 필터가 완화될 수 있습니다.

```bash
docker compose build indexer
docker compose up -d --force-recreate pipelines
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset

# 모델 없이 실행 가능한 검색/스트림 회귀 테스트 (약 137개)
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/test_rag_regression.py
```

#### Swagger Markdown 재생성 후 재인덱싱

```bash
docker compose run --rm --no-deps --entrypoint python indexer \
  /app/scripts/swagger_yaml_to_md.py \
  --input /app/docs/your_openapi.yaml \
  --output /app/docs/your_openapi.md
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

재인덱싱 후 Open WebUI에서 샘플 문서로 아래를 확인하세요.

```text
VPN 서버 주소가 뭐야?
```

참조 출처에 `sample_employee_guide.md`가 나오고, 무관한 샘플 문서가 섞이면 안 됩니다.
#### 파이프라인 코드만 변경한 경우

재인덱싱 없이 recreate만 하면 됩니다.

```bash
docker compose up -d --force-recreate pipelines
```

품질 변경 후 권장 검증 순서: recreate → Ollama `/api/chat` readiness → pipe 원문 assertion → eval(basic/`--rerank`) → regression. 근거는 `PL_FAILURE_LOG.md` [PLF-GENERIC-005].

### 검색 품질 평가 (골든 질문셋)

`rag/data/eval/golden_questions.json`에 질문과 기대 출처/키워드를 적어 두면, 아래 명령으로 검색 적중률을 측정할 수 있습니다. 검색·인덱싱 로직을 바꿀 때마다 실행해 회귀를 조기에 잡고, **실패한 질문을 계속 추가**하세요.

**평가 성공 조건**: 기대 출처 적중 **그리고** 해당 질문의 필수 키워드가 **모두** 검색 결과에 포함되어야 합니다. 출처만 맞고 키워드가 빠지면 실패입니다. [PLF-GENERIC-004]

공개 저장소 기준으로는 `rag/data/docs/sample_*.md`와 `golden_questions.json` 샘플을 사용하세요.  
런타임 증거(`rag/data/eval/artifacts/`의 답 원문·probe 덤프)는 **커밋하지 마세요**.

```bash
# 인덱싱이 끝난 상태에서 실행
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py

# 리랭커까지 포함해 평가
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py --rerank
```

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

- **후속 질문 문맥화**: 「표로」「정리해줘」처럼 주제 없이 재포맷만 요청하면 최근 사용자 주제로 문맥화한 뒤 검색합니다. 주제별 가드로 서로 덮어쓰지 않습니다. 이전 주제가 없으면 확인을 요청합니다 (`CONTEXTUALIZE_FOLLOW_UP`).
- **기술 토큰·경로**: 파일 확장자·경로·CamelCase API 토큰을 보존해 검색·답변에 반영합니다.
- **API 스코프**: API/Swagger 질문은 `document_type=api` 중심으로 검색하고, 가이드/프로토콜 문서로 API를 대체하지 않도록 범위를 나눕니다.
- **질문 초점**: `…에 대해 설명` 등 패턴이 맞으면, 해당 이름/구가 들어간 청크만 남겨 다른 문서가 섞이는 것을 줄입니다.
- **이미지**: 참고 청크에서 `![대체텍스트](URL)` 를 실제로 찾았을 때만 별도 블록을 붙입니다.
- **답변 톤**: 긴 면책·부정 문단을 피하도록 지시합니다.
- **qwen thinking**: Ollama 호출에 `think: false`를 유지합니다.

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
| `OLLAMA_BASE_URL` | `http://ollama:11434` | compose **`ollama` GPU 컨테이너**. (구방식 호스트 Ollama: `http://host.docker.internal:11434`) |
| `REWRITE_MODEL` | `qwen3.5:4b` | 질문 재작성·문맥화용 모델 |
| `ANSWER_MODEL` | `qwen3.5:4b` | 최종 답변용 모델 |
| `CHROMA_PATH` | `/app/chroma_db` (컨테이너 기준) | ChromaDB 저장 경로 |
| `CHROMA_COLLECTION` | `rag_documents` | 컬렉션 이름 |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | 임베딩 모델(한국어 기본) |
| `TOP_K` | `5` (`docker-compose`에서는 `4`) | 검색 청크 수 |
| `MIN_SCORE` | `0.3` | 최소 관련도 점수 (0~1) |
| `MAX_CHUNKS_PER_SOURCE` | `2` | 한 출처가 최종 컨텍스트에서 차지할 최대 청크 수 |
| `MAX_CONTEXT_CHARS` | `5600` (`docker-compose` 품질용) | 답변 모델에 전달할 검색 문맥의 최대 문자 수 |
| `OLLAMA_NUM_CTX` | `8192` | Ollama 답변 모델 컨텍스트 창 크기 |
| `OLLAMA_NUM_PREDICT` | `768` (`docker-compose`) | 한 답변의 최대 생성 토큰(과소 시 `reason=length` 절단 주의) |
| `OLLAMA_READ_TIMEOUT` | `600` | 긴 스트림 응답에 적용할 읽기 타임아웃(초) |
| `OLLAMA_KEEP_ALIVE` | `30m` | 모델 언로드 방지 |
| `RERANK_ENABLED` | `true` | 리랭크 사용 |
| `RERANK_NEURAL` | `false` (`docker-compose`) | `false`면 크로스인코더 대신 evidence-only 리랭크(지연↓) |
| `RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | neural 리랭커 모델(첫 사용 시 다운로드) |
| `RERANK_CANDIDATES` | `8`~`12` (`docker-compose`) | 리랭커/후보 수 |
| `USE_QUERY_REWRITE` | `false` (`docker-compose`) | `false`면 LLM 질문 재작성을 생략(원본+규칙 확장, 지연 감소) |
| `CONTEXTUALIZE_FOLLOW_UP` | `true` | 후속·재포맷 질문을 이전 주제 반영 독립형으로 바꿔 검색(규칙 가드+LLM) |

## 파일 구조

```
RAG_PipeLine/
├── docker-compose.yml           # open-webui + postgres + redis + ollama(GPU) + pipelines + indexer + imageserver
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
│   │   ├── test_rag_regression.py # 검색/스트림 회귀
│   │   └── test_pipeline.py     # 로컬 테스트 스크립트(선택)
│   └── data/
│       ├── docs/                # 인덱싱할 문서 (공개: sample_*.md)
│       ├── eval/                # golden_questions.json + artifacts/(gitignore)
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
- **Ollama 접근이 안 될 때**: 기본은 compose `ollama` (`http://ollama:11434`, 호스트에서는 `http://localhost:11434`)입니다. `docker compose ps`로 `ollama`가 Up인지 확인하고, 호스트 Ollama가 11434를 점유 중이면 **호스트 쪽을 중지**한 뒤 `docker compose up -d ollama` 하세요. 모델 디렉터리(`%USERPROFILE%\.ollama`)는 compose가 재사용하므로 **폴더 삭제 금지**.
- **호스트 Ollama로 되돌리려면**(비권장): pipelines/open-webui의 `OLLAMA_*`를 `http://host.docker.internal:11434`로 바꾸고 compose `ollama` 서비스를 내리면 됩니다. 포트 충돌에 주의하세요.
- **로컬로 파이프라인만 테스트**: `rag/` 디렉터리에서 `python scripts/test_pipeline.py` (호스트에서 `localhost:11434`로 compose Ollama에 닿을 수 있어야 함).
- **PL 개발**: 작업 전 `PL_FAILURE_LOG.md` 예방 체크리스트를 수용 기준에 포함하고, 비밀값·토큰·전체 로그 덤프는 남기지 않습니다.
