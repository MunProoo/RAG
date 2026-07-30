# 업데이트 내역

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 참고했습니다.  
날짜는 작업이 반영된 기준(2026-04-17)입니다.

## [Unreleased]

### 후속 질문 문맥화 (2026-07-30)

- `rag/pipelines/rag_pipeline.py`: 기존에는 답변 LLM만 최근 2턴을 보고 **검색은 현재 질문 문자열만 사용**해, "그거 수정하는 API는?" 같은 후속 질문이 엉뚱한 문서를 검색했음.
- **Step 0(질문 문맥화)** 추가: 지시어("그거", "해당", "위에" 등)나 12자 이하 초단문 질문을 후속 질문으로 감지(`is_follow_up_question`)하면, 최근 대화를 압축해(`_compact_history`, 이미지 마크다운 제거) 재작성 모델로 **독립형 질문**을 생성(`condense_question`). 이후 재작성·범위 필터·초점 추출·리랭킹·답변 프롬프트가 모두 이 질문을 사용.
- 감지될 때만 LLM을 추가 호출하므로 일반 질문의 지연은 그대로. LLM 실패·비정상 출력 시 원본 질문 폴백.
- `CONTEXTUALIZE_FOLLOW_UP`(기본 `true`)로 on/off. 회귀 테스트 6개 추가 (총 21개, 전부 통과).

### API 상세 + 스키마 동시 검색 (2026-07-30)

- `rag/scripts/swagger_yaml_to_md.py`: 각 엔드포인트 섹션 안에 그 API가 `$ref`로 참조하는 **스키마 필드 표를 인라인**(중첩 참조 2단계까지, `collect_operation_schema_refs`). API 상세와 스키마 정의가 서로 다른 청크로 쪼개져 스키마가 답변에서 누락되던 문제를 해소(자기완결 청크). 스키마는 `###` 헤딩이 아닌 굵은 텍스트로 넣어 인덱서가 엔드포인트 섹션에서 분리하지 않도록 함. 문서 말미의 `## 스키마 정의` 섹션은 스키마 단독 질문용으로 유지.
- `swagger_kr.md` 재생성(496KB). **반영하려면 `--reset` 재인덱싱 필요.**
- 회귀 테스트 2개(중첩 스키마 수집, body 파라미터 스키마 수집)와 골든 질문(응답 스키마 구조 질문) 추가.

### 다중 문서 정확도·속도 개선 (2026-07-30)

**검색 정확도**

- **리랭커 도입** (`rag/pipelines/rag_pipeline.py`): RRF로 병합한 후보(기본 20개)를 크로스 인코더 `BAAI/bge-reranker-v2-m3`가 (질문, 청크) 쌍으로 재채점한 뒤 top-k를 선별. 모델 로드/추론 실패 시 자동으로 RRF 순위 폴백. `RERANK_ENABLED` / `RERANK_MODEL` / `RERANK_CANDIDATES`로 제어.
- **PDF 섹션 청킹** (`rag/scripts/index_documents.py`): 페이지 단위에 더해 `3.1` 같은 다단계 번호 제목 줄에서 섹션을 분리(`split_pdf_page_sections`). 섹션 제목이 메타데이터와 임베딩 본문에 함께 남아, 제목 키워드로 질문해도 본문 청크가 검색됨. **반영하려면 `--reset` 재인덱싱 필요.**

**응답 속도**

- **BM25 인덱스 캐시**: 질문마다 `bm25_index.json` 파싱 + BM25 재구축을 반복하던 것을 파일 mtime 기준 프로세스 내 캐시로 교체. 재인덱싱하면 다음 질문부터 자동 반영(파이프라인 재시작 불필요).
- **질문 재작성 생략 옵션**: `USE_QUERY_REWRITE=false`면 재작성 LLM 호출을 건너뛰고 원본 질문 + 규칙 기반 확장만 사용.

**운영 루프**

- **골든 질문셋 평가** 추가: `rag/data/eval/golden_questions.json`(질문/기대 출처/기대 키워드) + `rag/scripts/eval_retrieval.py`(출처·키워드 적중률 리포트, 실패 시 종료 코드 1). indexer 컨테이너에 `rag/data/eval` 마운트 추가.
- **회귀 테스트 보강** (`rag/scripts/test_rag_regression.py`): BM25 캐시 재사용, 리랭커 정렬·폴백, PDF 섹션 분리 테스트 추가 (총 13개, 전부 통과).
- **프로젝트 스킬** 추가: `.cursor/skills/SKILL.md` — 구조·핵심 명령·운영 규칙·트러블슈팅 요약.

**설정**

- `docker-compose.yml`(pipelines): `RERANK_ENABLED`, `RERANK_MODEL`, `RERANK_CANDIDATES`, `USE_QUERY_REWRITE` 추가.
- README: 리랭커/캐시/PDF 섹션 청킹 설명, 평가 명령, 환경변수 표, 속도 관련 운영 팁 반영.

### 정리 (2026-04-17)

- `rag/pipelines/rag_pipeline.py`: 사용자 프롬프트·`source_hint`·`structure_rules`·이미지 블록·`system_message` 등 **중복 문구 축약** (동작은 유지).

---

## 이전 누적 변경 (요약)

### 구조·Docker

- 프로젝트 루트 대신 **`rag/`** 아래에 파이프라인 코드·의존성·인덱싱 스크립트·데이터를 모음 (`rag/pipelines`, `rag/scripts`, `rag/requirements.txt`, `rag/data/docs|chroma_db|assets`).
- `docker-compose.yml`: `pipelines` / `indexer` 볼륨 경로를 `rag/` 기준으로 변경, **`imageserver`**(nginx, `rag/data/assets` 서빙, 호스트 8090) 추가.
- `open-webui`: **`ENABLE_FOLLOW_UP_GENERATION=false`** 환경 변수 추가(이미 DB에 저장된 설정이 있으면 UI에서도 끄는 것이 필요할 수 있음).

### RAG 파이프라인 (`rag/pipelines/rag_pipeline.py`)

- **질문 재작성**: 멀티라인 검색 쿼리, 고유명사 보존·오타 금지, `think: false` 등.
- **검색**: 멀티쿼리 병합, `MIN_SCORE` / `TOP_K`.
- **질문 초점**: `…에 대해` 등 패턴으로 초점 추출 후, 해당 문자열이 들어간 청크만 남기는 **필터**(없으면 원본 유지).
- **동일 출처 병합**: `merge_documents_by_source` — 같은 `source` 청크를 참고 블록 **한 덩어리**로 합침(완전 동일 본문은 한 번만).
- **이미지**: 청크에서 `![...](URL)` 추출 → 있을 때만 별도 블록, 초점 있으면 섹션/윈도우 기준 추출; 없을 때 가짜 URL 금지 등.
- **답변 톤**: 장황한 “문서에는 … 없습니다” 면책 문단 금지, 질문과 무관한 참고 내용 생략 유도.
- **출처 표기**: `[문서 N]` 대신 **파일명** 인용 유도; 참고 블록 헤더를 `[참고 i] 출처 파일: …` 형태로 정리.
- **다중 파일**: 파일마다 `### 파일명` 한 번, `### ###`·`(참고 N)` 금지 등; 단일 파일이면 `###` 없이 한 흐름.
- **Open WebUI 내부 작업**: 첫 비어 있지 않은 줄이 `### Task:`일 때만 RAG 스킵(오탐 완화).
- **Chroma 기본 경로**: `CHROMA_PATH` 미설정 시 `rag/data/chroma_db` 기준으로 잡도록 보강.

### 문서·샘플

- 인물/이미지 샘플: **`rag/data/docs/Test.md`** (섹션·이미지 URL), `Test.txt` 제거 방향.
- 정적 이미지: **`rag/data/assets/`**, `ImageServer/README.txt` 안내.

### README

- 디렉터리 구조, ImageServer, 인덱싱 경로, Chroma 정합성, 후속 질문 끄기, RAG 요약, 운영 팁 등 반영.

---

## 참고

- 상세 사용법은 **`README.md`** 를 봅니다.
- 컨테이너 반영 후 **`docker compose`** 로 스택을 재시작해야 파이프라인 코드 변경이 적용됩니다.
