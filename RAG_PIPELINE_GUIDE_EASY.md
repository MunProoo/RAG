# RAG 도우미 쉬운 가이드 (비전공자용)

사내 문서에게 질문하면, 컴퓨터가 **관련 문서 조각을 찾아** 그 내용을 바탕으로 답해 주는 도우미입니다.  
이 문서는 “무엇을 하면 질문이 답으로 나오는지”만 짧게 정리합니다.

전문 설명이 필요하면 [RAG_PIPELINE_GUIDE.md](RAG_PIPELINE_GUIDE.md) 또는 [README.md](README.md)를 보세요.

---

## 한 줄로 이해하기

도서관에서 책을 찾는 일과 비슷합니다.

1. 미리 책을 카드에 정리해 둡니다. (**인덱싱** = 문서를 검색 가능하게 저장)
2. 질문을 받으면 관련 카드만 골라 옵니다. (**검색**)
3. 골라 온 카드를 읽고 말로 풀어 답합니다. (**답변 생성**)

도우미는 인터넷 전체가 아니라, **우리가 넣어 둔 사내 문서**만 봅니다.

---

## 무엇이 필요한가

| 이름 | 쉬운 말 |
|------|---------|
| Docker Desktop | 도우미·화면·검색 DB를 한꺼번에 켜 주는 상자 |
| Ollama (Windows) | 답을 쓰는 AI 엔진 (PC에서 실행) |
| Open WebUI | 채팅 화면 (`http://localhost:8080`) |
| Pipelines | 문서 검색 + 답변을 연결하는 뒷단 |
| 문서 폴더 | `rag/data/docs` 에 넣는 PDF·Markdown 등 |

비밀 비밀번호·전체 로그는 이 문서에 적지 않습니다. 연결에 쓰는 예시 키는 compose에 공개된 `0p3n-w3bu!` 수준만 안내합니다.

---

## 질문이 답으로 나오기까지 (단계)

### 1단계. PC 준비

1. Windows에서 **Ollama**를 실행합니다.
2. **Docker Desktop**을 실행합니다.

### 2단계. 서비스 켜기

프로젝트 폴더에서:

```bash
docker compose up -d
```

브라우저에서 `http://localhost:8080` 을 엽니다.

### 3단계. 문서 넣기

1. PDF·Markdown 등을 `rag/data/docs` 에 넣습니다.  
   (Word는 직접 안 됩니다. PDF나 Markdown으로 바꾼 뒤 넣으세요.)
2. 문서를 **인덱싱**합니다.

```bash
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
```

인덱싱이 끝나야 도우미가 그 문서를 “알고” 있습니다.

### 4단계. 채팅에서 도우미 선택

1. Open WebUI에서 모델/프로바이더로 **도우미(`rag_pipeline`)** 를 고릅니다.
2. Pipelines 주소가 맞는지 확인합니다.  
   - 컨테이너끼리: `http://pipelines:9099`  
   - PC 브라우저에서 직접: `http://localhost:9099`  
   - API Key 예시: `0p3n-w3bu!`
3. 평소처럼 질문합니다.

### 5단계. (개발자가 코드를 고친 뒤)

검색·답변 로직만 바꿨다면 보통 문서 재인덱싱은 필요 없고, 파이프라인만 다시 띄웁니다.

```bash
docker compose up -d --force-recreate pipelines
```

청킹 방식·문서 종류 태그·임베딩 모델·Swagger md를 바꿨다면 **재인덱싱이 필요**합니다. 자세한 표는 상세 가이드를 보세요.

---

## 이런 질문일 때 답이 어떻게 나와야 하나 (예시)

### 설치 자동화 (NSIS)

- `.bat` = 자동으로 돌리는 파일  
- `.nsi` = 설치 파일을 만드는 **스크립트**  
- `.exe` = 만들어진 **결과물**
- 빌드가 끝난 뒤 설치 파일을 확인하는 폴더는 보통 **`D:\nsis\install`**  
- `D:\nsis\Alpeta\setup` 은 device exe 등이 있는 **다른 역할**의 폴더입니다.
- “자동빌드” 질문은 문서의 **1~7단계**가 빠지지 않아야 하고, MakeNSISW 같은 **수동 방법과 섞이면 안 됩니다.**

좋은 답의 기준 예시: `rag/data/eval/artifacts/ideal_answer_nsis_auto_build.md`

### 사용자 → 단말기 추가 / 자동동기화

문서에는 **두 가지 방법**이 있습니다. 하나로 합치지 않습니다.

1. `[단말기리스트]` 로 확인·다운로드 (화면 구성 3가지를 그대로)
2. `단말기 사용자 리스트`에서 `[추가]` 후 전송
3. 그다음 **자동 동기화** 설정 (같은 출입그룹, 덮어쓰기 등)

UI 글자 `[단말기리스트]` 처럼 **문서에 적힌 띄어쓰기**를 유지하는 것이 좋습니다.

좋은 답의 기준 예시: `rag/data/eval/artifacts/ideal_answer_terminal_user_sync.md`

### Swagger / FaceWT API

API 질문은 User Guide나 프로토콜만으로 대체하면 안 되고, **`swagger_kr.md` 쪽**을 근거로 답해야 합니다.

좋은 답의 기준 예시: `rag/data/eval/artifacts/ideal_answer_facewt_swagger_kr.md`

### 프로토콜 “전부 리스트”

목차처럼 긴 목록은 중간만 잘리면 안 됩니다. “전부/전체/리스트업”이라고 물으면 **끝까지** 나와야 합니다.

---

## 자주 묻는 질문 (FAQ)

### Q. 채팅에 도우미(`rag_pipeline`)가 안 보여요

1. `docker compose ps` 로 open-webui·pipelines가 떠 있는지 확인합니다.
2. Open WebUI의 OpenAI 연결 Base URL이 `http://pipelines:9099` (또는 로컬 `9099`)인지 확인합니다.
3. DB를 복구한 직후라면, 채팅 테이블·설정이 깨졌을 수 있습니다.  
   담당자에게 `chat`의 `pinned` / `meta` / `folder_id`, `chat` 타입이 json인지, pipelines URL이 설정에 들어갔는지 확인을 요청하세요.  
   (자세한 내용: 상세 가이드의 Open WebUI↔Pipelines 절)

### Q. 답이 점(·)만 나오거나 비어 보여요

qwen 계열 모델이 “생각 모드”만 하고 본문이 비는 경우가 있습니다.  
파이프라인은 `think:false` 설정을 씁니다. 코드/설정을 건드렸다면 담당자에게 확인을 요청하세요.

또한 검색이 길면 **첫 글자가 나오기 전**에 화면이 멈춘 것처럼 보일 수 있습니다. 잠시 기다리거나, 로그에 진행 상태가 있는지 확인합니다.

### Q. 답이 틀리거나 다른 문서가 나와요

1. 해당 PDF/Markdown이 `rag/data/docs`에 있는지 확인합니다.
2. **인덱싱을 다시** 했는지 확인합니다. (문서를 넣기만 하고 인덱싱을 안 하면 모릅니다.)
3. 질문어를 문서에 나온 단어에 가깝게 바꿔 봅니다.  
   예: “자동빌드”, “FaceWT”, `[단말기리스트]`
4. 그래도 반복되면 담당자에게 **회귀 테스트·골든 평가** 실행을 요청하세요.

### Q. 서비스를 다시 시작하고 싶어요

```bash
docker compose up -d
```

파이프라인 코드만 반영:

```bash
docker compose up -d --force-recreate pipelines
```

문서 DB를 처음부터 다시 만들 때(`--reset`)는 시간이 더 걸립니다. 담당자와 함께 하는 것이 안전합니다.

### Q. Swagger(API 설명)를 고쳤는데 답이 예전 그대로예요

YAML → Markdown 변환 → 재인덱싱 → pipelines 재시작 순서가 필요합니다. 명령은 상세 가이드의 “Swagger Markdown 재생성”을 보세요.

---

## 품질을 어떻게 확인하나 (알아두면 좋은 것)

개발·운영 담당자는 보통 다음을 돌립니다.

- **회귀 테스트** (`test_rag_regression.py`): 약 **60개** 자동 검사 (AI 모델 없이 가능)
- **골든 질문셋** (`eval_retrieval.py`): “이 질문이면 이 문서 + 이 키워드”가 나오는지 채점  
  → **출처만 맞고 단어가 빠지면 실패**로 봅니다.
- **이상적 답변** 파일 (`ideal_answer_*.md`): “이런 식으로 나와야 한다”는 모범 답안

문제가 반복되면 `PL_FAILURE_LOG.md`에 예방 항목을 남기고, 다음 작업 전에 그 목록을 다시 확인합니다.

---

## 하지 말아야 할 것

- 문서·채팅·로그에 **토큰·비밀번호·개인정보**를 붙여 넣지 않기
- 잘 모르는 상태에서 `chroma_db` 폴더를 임의로 지우기
- 자동빌드 답변에 수동 빌드(MakeNSISW 등)를 섞어 안내하기
- API 질문에 User Guide만 보고 “API 없다”고 단정하기

---

## 다음에 읽을 문서

| 문서 | 언제 |
|------|------|
| [README.md](README.md) | 설치·명령·환경변수 |
| [RAG_PIPELINE_GUIDE.md](RAG_PIPELINE_GUIDE.md) | 검색 규칙·재인덱싱·연동 상세 |
| [RAG_PIPELINE_GUIDE.html](RAG_PIPELINE_GUIDE.html) | 위 가이드를 브라우저로 읽기 |
| [CHANGELOG.md](CHANGELOG.md) | 최근에 뭐가 바뀌었는지 |
| [PL_FAILURE_LOG.md](PL_FAILURE_LOG.md) | 예전에 깨졌던 것과 예방 |
