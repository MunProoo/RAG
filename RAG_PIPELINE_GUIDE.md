# RAG Pipeline 구조와 동작 가이드

## 한 줄 요약

이 프로젝트는 **사용자 질문과 의미가 비슷한 문서 조각을 찾은 다음, 그 조각을 LLM에 참고자료로 제공해 답변하게 하는 시스템**이다.

관련 문서:

- [README.md](README.md) — 빠른 시작·환경변수·운영 명령
- [RAG_PIPELINE_GUIDE_EASY.md](RAG_PIPELINE_GUIDE_EASY.md) — 비전공자용 쉬운 설명
- [RAG_PIPELINE_GUIDE.html](RAG_PIPELINE_GUIDE.html) — 이 가이드의 HTML 버전
- [CHANGELOG.md](CHANGELOG.md) — 변경 이력
- [PL_FAILURE_LOG.md](PL_FAILURE_LOG.md) — PL 루프 실패·예방 체크리스트

## 전체 구성

```text
사용자 → Open WebUI(:8080) → Pipelines(:9099)
                              ├─ ChromaDB + BM25 검색
                              ├─ 리랭커(선택)
                              └─ Windows 호스트 Ollama(:11434)
Indexer ← rag/data/docs → ChromaDB + bm25_index.json
ImageServer(:8090) ← rag/data/assets
```

### 구성요소별 역할

- **Open WebUI**: 사용자가 질문하고 답변을 확인하는 채팅 화면
- **Pipelines**: 질문 처리, 문서 검색, 컨텍스트 구성, Ollama 호출을 제어하는 핵심 백엔드
- **Indexer**: 원본 문서를 검색 가능한 ChromaDB와 BM25 인덱스로 변환
- **ChromaDB**: 의미가 비슷한 문서 조각을 찾는 벡터 데이터베이스
- **BM25**: API명, 파라미터, 버전처럼 정확한 단어를 찾는 키워드 검색
- **Ollama**: 질문을 정리하고 최종 답변을 생성하는 LLM 실행 환경
- **PostgreSQL**: Open WebUI의 대화와 설정 저장
- **Redis**: Open WebUI 캐시
- **ImageServer**: `rag/data/assets`에 있는 문서 이미지 제공

Ollama는 Docker 컨테이너가 아니라 Windows 호스트에서 실행되며, 컨테이너에서는 `http://host.docker.internal:11434`로 접근한다.

## 주요 파일

```text
RAG_MJY/
├── docker-compose.yml
├── README.md
├── RAG_PIPELINE_GUIDE.md / .html / _EASY.md
├── CHANGELOG.md
├── PL_FAILURE_LOG.md
├── rag/
│   ├── pipelines/
│   │   └── rag_pipeline.py
│   ├── scripts/
│   │   ├── index_documents.py
│   │   ├── swagger_yaml_to_md.py
│   │   ├── eval_retrieval.py
│   │   └── test_rag_regression.py
│   └── data/
│       ├── docs/
│       ├── eval/
│       │   ├── golden_questions.json
│       │   └── artifacts/ideal_answer_*.md
│       ├── chroma_db/
│       └── assets/
└── ImageServer/
```

- `rag/pipelines/rag_pipeline.py`: 질문을 받아 검색하고 답변을 생성하는 핵심 파이프라인
- `rag/scripts/index_documents.py`: 문서를 청크로 나눠 ChromaDB와 BM25에 저장
- `rag/scripts/swagger_yaml_to_md.py`: Swagger YAML → `swagger_kr.md` 변환(엔드포인트별 스키마 인라인)
- `rag/scripts/eval_retrieval.py`: 골든 질문셋으로 검색 품질 평가
- `rag/scripts/test_rag_regression.py`: 검색·스트림 회귀 테스트(**약 60개** `test_` 메서드)
- `rag/data/docs`: 검색할 원본 문서
- `rag/data/chroma_db`: 벡터 DB와 `bm25_index.json` 저장 위치
- `rag/data/eval/artifacts/ideal_answer_*.md`: 주요 질문의 이상적 답변 기준

## 1. 문서를 검색 가능하게 준비하는 과정

담당 파일은 `rag/scripts/index_documents.py`다.

```text
rag/data/docs 문서
    ↓
PDF·Markdown·텍스트 내용 추출
    ↓
페이지와 섹션 단위로 구분
    ↓
480토큰 청크로 분할하고 80토큰 중첩
(목차·명령 카탈로그 페이지는 더 큰 청크 ~960)
    ↓
BGE-M3로 임베딩 벡터 생성
    ↓
ChromaDB 저장 + BM25 인덱스 생성
```

### 문서 추출과 청킹

인덱서는 PDF, Markdown, TXT, RST, HTML 문서를 읽는다. Word 문서는 직접 지원하지 않으므로 PDF나 Markdown으로 변환해야 한다.

긴 문서는 기본적으로 **480토큰 단위**로 나누며, 문맥이 경계에서 끊기는 것을 줄이기 위해 앞뒤 청크에 **80토큰을 겹쳐서** 저장한다.

PDF는 페이지 단위에 더해 `3.1`처럼 다단계 번호 제목에서 섹션을 나눈다.  
단, **목차·명령 카탈로그**처럼 짧은 번호/hex/점선 행이 밀집한 페이지는 섹션을 쪼개지 않고 **더 큰 청크(약 960토큰)**로 인덱싱한다. 이렇게 해야 “v4.0 프로토콜 전부 리스트”처럼 목록 전체가 한 출처에서 잘리지 않는다.

### 임베딩과 ChromaDB 저장

각 문서 청크를 `BAAI/bge-m3` 임베딩 모델로 숫자 벡터로 변환한다. 의미가 비슷한 문장은 벡터 공간에서도 가까운 위치를 갖는다.

문서 청크에는 본문과 함께 다음 메타데이터가 저장된다.

- 파일명, 경로, 페이지, 섹션
- 문서 종류(`document_type`): `protocol`, `install`, `user_guide`, **`api`**
- 제품(`product`): `alpeta` 등 (일부 API 문서는 product 미태그일 수 있음)
- 프로토콜 세대: `current`, `legacy`
- 프로토콜 버전

파일명에 swagger/openapi/api가 들어가면 `document_type=api`로 분류한다.

### BM25 인덱스 생성

동일한 문서 청크를 사용해 `rag/data/chroma_db/bm25_index.json`도 생성한다. BM25는 의미보다 정확한 단어 일치를 잘 찾으므로 벡터 검색을 보완한다.

문서를 추가하거나 수정하면 인덱서를 다시 실행해야 검색 결과에 반영된다.

```bash
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
```

### Swagger Markdown 재생성

API 스펙 YAML이 바뀌면 md를 다시 만든 뒤 재인덱싱한다. 변환기는 각 엔드포인트 섹션에 참조 스키마 표를 인라인한다(자기완결 청크).

```bash
docker compose run --rm --no-deps --entrypoint python indexer \
  /app/scripts/swagger_yaml_to_md.py \
  --input /app/docs/swagger_kr.yaml \
  --output /app/docs/swagger_kr.md

docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

## 2. 질문 한 건이 처리되는 과정

핵심 진입점은 `rag/pipelines/rag_pipeline.py`의 `Pipeline.pipe()`다.

```text
질문
 → 후속 질문 문맥화(필요 시)
 → 검색 질문 재작성
 → 메타데이터 검색 범위 결정
 → ChromaDB 벡터 검색 + BM25 키워드 검색
 → RRF 병합 → CrossEncoder 리랭킹
 → 참고 문맥 구성(역할·절차·목록 규칙 적용)
 → Ollama 최종 답변(스트리밍)
```

### 2.1 후속 질문 문맥화

“그거 자세히 설명해줘”처럼 질문만으로 대상을 알 수 없으면 최근 대화를 반영해 독립적인 질문으로 바꾼다.

```text
그거 자세히 설명해줘
→ Alpeta 프로토콜의 Param3을 자세히 설명해줘
```

이 단계는 `CONTEXTUALIZE_FOLLOW_UP=true`이고 후속 질문으로 감지됐을 때만 `REWRITE_MODEL` LLM을 호출한다.

### 2.2 검색 질문 재작성

`USE_QUERY_REWRITE=true`이면 LLM이 질문을 검색에 유리한 2~4개의 표현으로 재작성한다. 이후 규칙 기반 확장으로 도메인 동의어와 버전 표현도 추가한다.

자동화 빌드·FaceWT·단말기 UI 표기 등 의도별 확장 키워드가 추가로 붙을 수 있다.

### 2.3 검색 범위 결정

질문에 포함된 키워드로 검색할 문서 범위를 먼저 제한한다.

```text
질문: Alpeta 신규 프로토콜의 Param3을 알려줘

필터 예:
- product = alpeta
- document_type = protocol
- protocol_generation = current
```

**API/Swagger 의도**에서는 `document_type=api`로 스코프하고, product 미태그 문서(`swagger_kr.md` 등)가 배제되지 않도록 **product 필터를 완화**한다. FaceWT처럼 CamelCase 식별자도 기술 토큰으로 보존한다.

**User Guide 절차**(사용자 단말기 추가·동기화 등)는 명시적 문서명이 없어도 `user_guide` 범위로 제한해 Protocol/NSIS가 섞이지 않게 한다.

벡터 검색에는 ChromaDB `where` 조건으로 적용하고, BM25 결과에도 동일한 메타데이터 조건을 적용한다.

### 2.4 ChromaDB 벡터 검색

질문을 문서와 동일한 `BAAI/bge-m3` 모델로 벡터화하고, 저장된 문서 벡터와 코사인 유사도를 비교한다.

따라서 질문과 문서에 완전히 같은 단어가 없어도 의미가 비슷하면 검색될 수 있다. 임베딩 모델을 변경하면 기존 벡터와 공간이 달라지므로 전체 재인덱싱이 필요하다.

### 2.5 BM25 키워드 검색

BM25는 `Param3`, API 이름, 명령어, 버전 번호처럼 정확한 문자열이 중요한 질문을 보완한다.

- 벡터 검색: 의미가 비슷한 내용에 강함
- BM25 검색: 정확한 용어와 코드에 강함

### 2.6 RRF 병합과 리랭킹

벡터 검색과 BM25 검색 결과를 RRF(Reciprocal Rank Fusion)로 병합한다.

```text
벡터 검색 결과 ─┐
                 ├─ RRF 병합 → 리랭커 → 최종 후보
BM25 검색 결과 ─┘
```

이후 `BAAI/bge-reranker-v2-m3` CrossEncoder가 원래 질문과 각 후보 청크를 직접 비교해 관련도가 높은 순서로 다시 정렬한다.

리랭커는 답변을 작성하는 LLM이 아니다. 관련도 점수를 계산하는 분류 모델이며, 로드나 실행에 실패하면 RRF 순위를 그대로 사용한다.

기술 토큰·경로 역할·API 근거 등은 RRF/리랭크에 **가점 규칙**으로 반영된다.

### 2.7 참고 문맥 구성

최종 후보에서 다음 제한을 적용한다.

- 동일 출처가 차지할 수 있는 최대 청크 수 제한(목록·자동화 섹션 의도에서는 상향)
- 전체 컨텍스트 글자 수 제한
- 질문 초점과 관계없는 청크 제거
- 실제 문서에서 찾은 이미지 URL만 포함
- 자동화 버전 섹션은 앵커 구간(`chunk_index` 최소~최대)의 청크를 강제 포함, 수동 절차 청크는 제거
- 목록 완결성: 인접 목차 페이지 hex 커버리지 보강

선택된 문서 조각은 다음과 비슷한 형태로 조립된다.

```text
=== 참고 문서 ===
[참고 1] 출처: 주장치_Protocol_v1.0.pdf
Param3 관련 문서 내용...

=== 질문 ===
Param3[0]과 Param3[1]을 설명해줘
```

### 2.8 최종 답변 생성

Ollama의 `ANSWER_MODEL`이 검색된 참고 문서, 질문, 최근 대화를 받아 최종 답변을 스트리밍한다.

현재 Docker Compose 기준 주요 모델은 다음과 같다.

- 질문 재작성 및 문맥화: `qwen3.5:4b`
- 최종 답변 생성: `qwen3.5:4b`
- 임베딩: `BAAI/bge-m3`
- 리랭커: `BAAI/bge-reranker-v2-m3`

qwen3.5 계열은 Ollama 기본이 thinking이라 **`think: false`** 없이 호출하면 `message.content`가 비어 UI가 점만 보일 수 있다. 파이프라인은 `think: False`를 유지한다.

## 3. 검색 품질 규칙 (2026-08 반영)

### 3.1 기술 토큰·파일 역할 구분 (NSIS)

의미 유사도만으로는 파일 역할이 섞인다. 파이프라인은 다음을 구분한다.

| 확장자 / 종류 | 역할 |
|---------------|------|
| `.bat` | 자동화 실행 파일 (예: `build_install.bat`, `gitpull.bat`) |
| `.nsi` | NSIS 빌드 스크립트 (예: `alpeta.nsi`, `alpeta_device.nsi`) |
| `.exe` | 빌드 **산출물** (예: `AlpetaDevice.exe`, 설치 실행 파일) |

경로 역할도 구분한다.

| 경로 | 역할 |
|------|------|
| `D:\nsis\install` | 빌드 완료 후 **설치 확인 / 최종 설치 파일** 폴더 |
| `D:\nsis\Alpeta\setup` | device exe 등 **개별 실행 파일**이 놓이는 setup 경로 |
| `D:\nsis\eXbuilder\build_install.bat` | 자동화 배치의 **전체 경로** 예 |

일반 “빌드 완료 후 어디에 생성되나 / 설치 파일 확인 폴더”는 `D:\nsis\install`을 우선한다. 명시적 `AlpetaDevice.exe` 질문은 setup 경로를 유지한다.

### 3.2 API / Swagger 스코프

- swagger/openapi/api 파일 → `document_type=api`
- API 의도: api 스코프 + product 필터 완화
- Swagger 근거가 있으면 User Guide/Protocol로 API를 대체하지 않음
- FaceWT/FAW 등 CamelCase·대문자 식별자 보존
- 이상적 답변 참고: `rag/data/eval/artifacts/ideal_answer_facewt_swagger_kr.md`

### 3.3 v4 프로토콜 전체 리스트

- TOC/카탈로그 페이지는 큰 청크로 인덱싱
- “전부/전체/리스트업” 의도 시 소스당·top-k 상한 확대, 동일 출처 카탈로그 보충
- 답변 프롬프트에 **목록 완결성** 규칙(중간 Preview만으로 끝내지 않음)
- 특정 command hex 하드코딩 없음

### 3.4 절차형 User Guide (단말기·자동동기화)

두 방법을 **독립적으로** 설명한다. 하나로 합치지 않는다.

1. 사용자 정보 화면의 **`[단말기리스트]`** (띄어쓰기 없는 문서 표기 유지)
   - 화면 구성 3가지를 원문 그대로: `출입그룹 단말기 리스트`, `등록된 단말기`, `추가가능한 단말기`
2. 단말기 관리의 **`단말기 사용자 리스트` → [추가]** 절차
3. **자동 동기화**: `[일반설정] > [사용자] > [사용자 데이터]`, 동일 출입그룹, `덮어쓰기`, `다시 다운로드` 등 문서 용어 보존

Protocol/NSIS를 이 절차 답에 섞지 않는다.  
이상적 답변: `rag/data/eval/artifacts/ideal_answer_terminal_user_sync.md`

### 3.5 NSIS 자동화 버전 전체 절차

“자동화 버전 / 자동빌드” 의도일 때 **알페타 설치 패키지 빌드(자동화 버전)** 섹션 1~7단계를 문서 순서대로 완결한다.

1. `gitpull.bat` (git pull)
2. `define.go` 버전 수정
3. `alpeta_device.nsi` 버전 수정
4. `alpeta.nsi` 버전 수정
5. `build_install.bat` 실행 — 하위 작업 전부  
   (`proto_compile`, `go build`, 서버 복사, control/setting export, 두 NSI 컴파일 등)
6. 결과 경로 **`D:\nsis\install`**
7. 문제 시 문서가 안내한 수동 빌드 가이드로 전환(자동화 답변에 **MakeNSISW / Compile NSI scripts 혼입 금지**)

이상적 답변: `rag/data/eval/artifacts/ideal_answer_nsis_auto_build.md`

## 4. 평가·회귀·이상적 답변

### 회귀 테스트

모델 없이 실행 가능한 단위/계약 테스트다. `test_rag_regression.py`에 **약 60개** `test_` 메서드가 있다.

```bash
docker compose run --rm --no-deps --entrypoint python \
  indexer /app/scripts/test_rag_regression.py
```

### 골든 질문셋 평가

`rag/data/eval/golden_questions.json` 기준으로 출처·키워드 적중을 본다.  
**성공 조건 = 기대 출처 + 해당 질문의 필수 키워드 전부** (출처만 맞고 키워드 누락이면 실패).

```bash
docker compose run --rm --no-deps --entrypoint python \
  indexer /app/scripts/eval_retrieval.py

docker compose run --rm --no-deps --entrypoint python \
  indexer /app/scripts/eval_retrieval.py --rerank
```

### 이상적 답변 아티팩트

실제 Pipe 답변을 대조할 때 참고한다.

- `ideal_answer_facewt_swagger_kr.md`
- `ideal_answer_nsis_auto_build.md`
- `ideal_answer_terminal_user_sync.md`

경로: `rag/data/eval/artifacts/`

### 품질 변경 후 권장 검증 순서

[PLF-20260802-002] 기준:

1. 코드 반영 → `docker compose up -d --force-recreate pipelines`
2. Ollama `/api/chat` readiness 확인
3. direct `Pipeline.pipe()` raw/JSON assertion
4. `eval_retrieval.py` (basic / `--rerank`)
5. `test_rag_regression.py`
6. 종료 코드·원문을 `rag/data/eval/artifacts/`에 보존

신규 이슈의 probe/골든에는 **이번 질문 문자열을 새 키로** 넣는다. 과거 PASS 질문만 재실행하지 않는다. [PLF-20260802-003]

## 5. Open WebUI ↔ Pipelines 연동

### 연결

- 컨테이너 간(권장): Base URL `http://pipelines:9099`, API Key 예시 `0p3n-w3bu!` (compose에 공개된 예시 수준만 문서화)
- 호스트 브라우저: `http://localhost:9099`
- 모델/도우미: `rag_pipeline`

### DB / config 복구 주의 [PLF-20260802-001]

Postgres 복구 후 alembic stamp만으로 스키마가 최신이라고 가정하지 않는다.

- `chat` 테이블: `pinned`, `meta`, `folder_id` 존재
- `chat.chat` 컬럼 타입: **json** (text면 ChatModel 검증 실패)
- `config.openai.api_base_urls` = `http://pipelines:9099`
- 복구 후 e2e: `chats/new` + `/api/chat/completions` + pipelines 로그의 inlet/completions 확인

비밀값·실토큰·전체 로그 덤프는 문서·실패 기록에 넣지 않는다.

### 런타임 주의 [PLF-20260801-001]

- `PIPELINES_DIR`에 빈 `__init__.py`를 두지 않는다. pipelines가 모듈로 로드해 `failed/`·`__init__/valves.json` 부산물을 만든다.
- `pipe()`가 첫 yield 전에 재작성·검색·리랭크를 길게 동기 수행하면 UI가 무응답처럼 보인다(첫 토큰 대기).

## 6. 재인덱싱이 필요한 경우

| 변경 | `--reset` 재인덱싱 | pipelines recreate |
|------|--------------------|--------------------|
| 문서 추가·수정·삭제 | 권장(파일명 변경 시 특히) | 불필요(BM25 mtime 캐시) |
| 청킹 규칙(TOC 큰 청크 등) | **필수** | 권장 |
| `document_type` 등 메타데이터 분류 | **필수** | 권장 |
| 임베딩 모델 변경 | **필수** | 권장 |
| swagger md 재생성 | **필수**(md 반영 후) | 권장 |
| 파이프라인 코드만 변경 | 불필요 | **필수** |

```bash
# 파이프라인 코드만 반영
docker compose up -d --force-recreate pipelines

# swagger 반영 전체
docker compose run --rm --no-deps --entrypoint python indexer \
  /app/scripts/swagger_yaml_to_md.py \
  --input /app/docs/swagger_kr.yaml --output /app/docs/swagger_kr.md
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

## 7. LLM이 담당하는 일 / 하지 않는 일

### LLM이 담당하는 일

1. **후속 질문 문맥화**: “그거”가 무엇인지 이전 대화로 보완
2. **검색 질문 재작성**: 검색에 유리한 표현과 키워드 생성
3. **최종 답변 생성**: 검색된 문서 조각을 읽고 답변 작성

독립적인 일반 질문이면 후속 질문 문맥화는 생략되므로 보통 질문 재작성과 최종 답변 생성, 두 번의 LLM 호출이 발생한다.

### LLM이 담당하지 않는 일

- 문서 및 질문 임베딩: BGE-M3
- 벡터 저장과 검색: ChromaDB
- 키워드 검색: BM25
- 검색 결과 병합: RRF
- 후보 재정렬: BGE CrossEncoder 리랭커
- 메타데이터 필터·역할 점수·절차 규칙: 코드에 정의된 규칙

## 기억하기 쉬운 핵심 정리

> **Indexer는 문서를 검색 DB로 만들고, Pipeline은 관련 문서를 찾으며, Ollama는 찾은 내용을 읽고 답변한다.**

```text
문서 준비: 문서 → Indexer → ChromaDB + BM25
질문 처리: 질문 → Pipeline → 검색 → Ollama → 답변
```

## 8. 운영·트러블슈팅 체크리스트

1. 문서를 변경하면 인덱서를 다시 실행한다.
2. 임베딩 모델을 변경하면 `--reset`으로 전체 재인덱싱한다.
3. 청킹이나 메타데이터 분류 규칙을 변경해도 재인덱싱한다.
4. 검색 로직을 변경하면 회귀 테스트와 검색 평가를 실행한다.
5. pipelines와 indexer의 `chromadb` 버전을 동일하게 유지한다.
6. 품질 작업 전·후 기준선·pipe 원문을 artifacts에 남긴다. [PLF-20260801-003]
7. 평가는 출처+필수 키워드 모두. [PLF-20260801-002]
8. 답변이 점만 보이면 qwen `think:false`·빈 content 경로를 확인한다. [PLF-20260801-001]
9. 도우미가 안 보이면 OpenAI Base URL·chat 스키마·config를 확인한다. [PLF-20260802-001]
10. 첫 질문이 매우 느리면 임베딩·리랭커 최초 로딩일 수 있다. 장시간 무응답이면 첫 yield 전 동기 작업도 의한다.

PL 개발 루프를 쓸 때는 작업 시작 전 `PL_FAILURE_LOG.md`의 **활성 예방 체크리스트**를 읽고 수용 기준에 포함한다.
