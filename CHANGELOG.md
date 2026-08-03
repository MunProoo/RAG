# 업데이트 내역

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 참고했습니다.  
날짜는 작업이 반영된 기준(2026-04-17)입니다.

## [Unreleased]

### 응답 지연 목표(80%)·GPU Ollama·품질 가드레일 (2026-08-03)

성능 목표(TTFT 2초 / 일반 5–8초 / 긴 설명 10–15초 / 검색 500ms / 동시 10–20명)의 **최소 80%**를 warm 단독 기준으로 맞추고, 기존 답변 품질(단말기 사용자 관리 등)은 유지했습니다.

- **`docker-compose.yml`**: compose GPU `ollama` 서비스 추가(`gpus: all`, `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_NUM_PARALLEL=2`). pipelines/open-webui의 `OLLAMA_*`를 `http://ollama:11434`로 연결. 호스트 `%USERPROFILE%\.ollama`를 컨테이너에 바인드해 기존 pull 모델을 재사용합니다. `USE_QUERY_REWRITE=false`, `RERANK_NEURAL=false`(크로스인코더 대신 evidence 리랭크), `VECTOR/BM25_CANDIDATES=12`, `OLLAMA_NUM_CTX=4096`, `OLLAMA_NUM_PREDICT=768` 유지.
- **`rag/pipelines/rag_pipeline.py`**: 단계별 `[RAG] timing` 로그, 진행 상태를 `event.type=status`로 분리(본문 미혼입), evidence-only 리랭크·`keep_alive` 전달, 식별자 공백 복원, 「단말기 사용자 관리」(User Guide p.39–40) 전용 의도·확장·프롬프트·품질 enforce 유지.
- **`rag/scripts/index_documents.py`**: PDF 「단말기 사용자 관리」섹션 분리(재인덱싱 반영, 청크 1592).
- **회귀·평가**: `golden_questions.json`에 `terminal_user_management` 추가, `test_rag_regression.py` 보강. warm 측정 예: TTFT ~0.9s, 일반 wall ~2s, 긴 설명 ~7–9s, 검색 151–375ms. regression 71/71. 동시 5명 P95는 단독×2 대비 PARTIAL(실패율 0).
- **운영**: 호스트에서 11434를 쓰는 Ollama가 있으면 **서비스는 중지**한 뒤 `docker compose up -d`로 compose `ollama`를 기동하세요. 모델 디렉터리(`%USERPROFILE%\.ollama`)는 compose가 재사용하므로 **폴더 삭제 금지**. 호스트 Ollama **앱만** 제거하는 것은 가능하나, 제거 전 compose GPU 경로로 답이 나오는지 확인하세요.
- 측정·이상답 근거: `rag/data/eval/artifacts/15_*`, `16_*`, `17_*`, `18_perf_comparison.md` 등.

### 지연 최적화 부작용 복구·단말기 사용자 관리 답변 정렬 (2026-08-03)

- **빈/깨진 답변처럼 보이던 회귀**: `OLLAMA_NUM_PREDICT` 과소(`reason=length` 조기 절단)와 status 문자열의 content 혼입을 수정. predict **768**, status는 event 분리, 식별자 공백 복원(`PLF-20260803-001`).
- **「alpeta 단말기 사용자 관리 메뉴」**: p.34 단말기 정보·일반 사용자 등록(고유아이디/권한8) 혼입 대신 User Guide **p.39–40** 메뉴(가져오기/업로드/추가·단말기에서만 삭제)로 정렬. ideal: `17_ideal_terminal_user_mgmt.md`.

### 알페타 자동화 버전 빌드 절 완결성·사용자 단말기 이중 방법 분리 (2026-08-02)

- **이슈 1: "알페타 설치 패키지 빌드(자동화 버전)" 전체가 안 나옴**
  - `rag/pipelines/rag_pipeline.py`: `is_automated_build_intent(query)`를 추가해 "자동화 버전", "자동빌드", "자동 빌드", "automated build" 등 일반 마커로 자동 빌드 의도를 감지합니다.
  - `expand_retrieval_query()`에 이 의도일 때 `git pull`/`gitpull.bat`/`define.go`/`eXbuilder`/`build_install.bat`/`proto_compile`/`D:\nsis\install` 등 문서 실제 표현으로 검색을 확장합니다.
  - `complete_automated_build_context()`를 신설해 "자동화 버전" 섹션의 앵커 표현으로 같은 출처 내 `chunk_index` 최소~최대 구간을 계산하고, 그 구간의 모든 청크(앵커가 없는 중간 청크 포함)를 강제로 포함하며 구간 밖 수동 절차 청크는 제거합니다.
  - `build_context_prompt()`에 자동화 버전 전용 안내 블록을 추가해 1~7단계(특히 5번의 하위 6개 작업, 6번 결과 경로, 7번 대체 안내)를 문서 순서대로 빠짐없이 답하고 수동 절차(`MakeNSISW` 등)를 섞지 않도록 지시합니다.
  - 이 의도에서 `effective_top_k`/`effective_max_chunks_per_source`/후보 수를 상향해 섹션 전체가 후보에서 잘리지 않게 했습니다.
- **이슈 2: "alpeta 사용자를 단말기에 추가 + 자동동기화" 답변 불완전**
  - `build_context_prompt()`의 사용자·단말기 절차 안내(`procedure_block`)를 보강해, 문서에 "단말기리스트" 경로와 "단말기 사용자 리스트 추가" 경로가 **두 가지 독립된 방법**으로 있으면 반드시 각각 별도 방법으로 구분해 설명하도록 지시합니다.
  - 문서에 `출입그룹 단말기 리스트`/`등록된 단말기`/`추가가능한 단말기` 화면 구성 3가지가 있으면 요약하거나 합치지 말고 원문 표기 그대로 3가지 모두 나열하도록, `[주의사항]` 문단이 있으면 그 안의 사실을 하나도 빠짐없이 나열하도록, 특정 동작이 "필수로 연결"되어 있어야 한다는 조건이 있으면 생략하지 말도록 조건부(문서에 실제로 있을 때만) 지시를 추가했습니다.
  - 답변 지침의 기존 병합된 화살표 절차 문장(`[단말기리스트] → [단말기 사용자 리스트] → …`)을 제거해 두 방법이 하나로 뭉개지지 않게 했습니다.
  - `enforce_document_term_pairs()`가 `[단말기 리스트]` 공백 의역을 문서의 `[단말기리스트]`로 복원하고, 컨텍스트에 있는 화면 구성 항목(`출입그룹 단말기 리스트` 등)이 답에서 빠지면 문서 원문 줄을 보완합니다. `단말기 사용자 리스트 > [추가]`처럼 breadcrumb `>`가 이동 버튼보다 앞에 나오지 않도록 정규화합니다. `terminal_list_composition` facet으로 해당 청크를 컨텍스트에 보존합니다.
  - 검색 확장에 `단말기리스트`/`출입그룹 단말기 리스트` 등 문서 원문 UI 표기를 추가하고, 프롬프트에 띄어쓰기 없는 `[단말기리스트]` 표기 고정을 명시합니다.
- `rag/data/eval/golden_questions.json`: "alpeta 자동빌드하려면 어떻게 하면돼?" 신규 문항을 추가하고 `expected_keywords`에 `gitpull.bat`/`define.go`/`alpeta_device.nsi`/`alpeta.nsi`/`build_install.bat`/`proto_compile`/`D:\nsis\install`을 포함했습니다. 기존 사용자·단말기 자동동기화 문항의 화면 구성/필수 연결/출입그룹 기반 설정 키워드도 보강했습니다.
- `rag/scripts/test_rag_regression.py`: 자동화 버전 의도·쿼리 확장·구간 완결성·프롬프트 지시, 사용자·단말기 UI 표기 복원·화면 구성 facet 보완 회귀를 추가·갱신했습니다.
- 청킹·메타데이터·임베딩 모델은 변경하지 않아 재인덱싱은 필요하지 않습니다(인덱스 1591 chunks 유지). 파이프라인 코드 반영에는 `docker compose up -d --force-recreate pipelines`가 필요합니다.

### NSIS 산출 역할·사용자 단말기 절차 검색 개선 (2026-08-02)

- `rag/pipelines/rag_pipeline.py`: 설치 경로 질문을 **최종 빌드 산출물**, **확인 폴더**, **명시된 개별 실행 파일 위치**, **빌드 입력 복사 폴더**로 구분했습니다. 일반적인 “빌드 완료 후 어디에 생성되는가”는 완료 문장의 최종 설치 파일 경로를 우선하고, 명시적 `AlpetaDevice.exe` 질문은 기존 device setup 경로를 유지합니다.
- `rag/pipelines/rag_pipeline.py`: 사용자·단말기 추가/전송/동기화 조합의 절차 질문은 명시적 문서명이 없어도 `user_guide` 범위로 제한합니다. 수동 추가와 자동 동기화의 연속 근거를 함께 보존하고, 답변 프롬프트에서 두 절차·조건·제한을 구분하며 Protocol/NSIS 혼입을 금지합니다.
- `rag/pipelines/rag_pipeline.py`: 자동 동기화 답변에서 문서 용어 `덮어쓰기`·`다시 다운로드`/`다운로드 재진행`이 빠지거나 의어로 바뀌지 않도록 검색 확장·절차 facet(`overwrite_option`)·프롬프트 표기 규칙을 보강했습니다.
- `rag/data/eval/golden_questions.json`, `rag/scripts/test_rag_regression.py`: 최종 NSIS 산출 경로 및 Alpeta User Guide 수동 추가·자동 동기화·동일 출입그룹·덮어쓰기 옵션 회귀를 추가했습니다.
- 청킹·문서 메타데이터·임베딩 모델은 변경하지 않아 재인덱싱은 필요하지 않습니다. 파이프라인 코드 반영에는 `docker compose up -d --force-recreate pipelines`가 필요합니다.

### 목록 완결성·경로 역할 구분 (2026-08-02)

v4.0 프로토콜 “전부 리스트”가 Command Preview 중간(~0x0108)에서 끊기고, 빌드 완료 후 설치 확인 폴더가 `D:\nsis\Alpeta\setup`으로 오인되던 문제를 일반 규칙으로 개선했습니다.

**v4.0 프로토콜 전체 목록**

- **증상**: “v4.0 프로토콜 전부 리스트업” 질문에 TOC 후반(`0x010A`/`0x010B`/`0x010C`, 출입그룹, 스냅샷 등)이 빠지고 Preview 일부만 나옴.
- **원인**: TOC 페이지가 번호 제목마다 쪼개져 `MAX_CHUNKS_PER_SOURCE=2`에 잘림. Preview가 의미 점수로 앞서도 TOC보다 불완전함.
- **해결**:
  - `rag/scripts/index_documents.py`: 목차·명령 카탈로그처럼 짧은 번호/hex/점선 행이 밀집한 PDF 페이지는 섹션 분리하지 않고, 더 큰 임베딩 청크(960)로 인덱싱.
  - `rag/pipelines/rag_pipeline.py`: 전부/전체/리스트업 의도 감지, 소스당·top-k 상한 확대, 동일 출처 카탈로그 보충, **인접 목차 페이지 hex 커버리지 보강**, 답변 프롬프트에 목록 완결성 규칙 추가. 특정 command hex 하드코딩 없음.

**빌드 완료 후 설치 확인 폴더**

- **증상**: “설치 파일을 확인하는 폴더”에 `D:\nsis\Alpeta\setup`(device exe 위치) 또는 `D:\nsis`만 답함. 기대는 `D:\nsis\install`.
- **원인**: “설치 파일”이 `executable` 의도로 분류되어 `.exe` 생성 경로가 리랭크에서 앞섬.
- **해결**: `output_folder` 의도(확인 폴더/이동하면/생성된 설치 등). 확인 폴더 질문에서는 executable 의도를 제거하고, 확인·이동 표현이 있는 폴더 경로에 경로 역할 점수를 가산. AlpetaDevice.exe 생성 경로 골든은 executable로 유지.

**재인덱싱·회귀**

- TOC 청킹 변경으로 **`--reset` 재인덱싱 필요**(청크 1615 → 1591).
- `test_rag_regression.py` **45/45** 통과. 골든에 v4 전부 리스트·install 확인 폴더 문항 추가.
- eval(rerank): 대상 2문항 키워드 PASS. 기존 NSIS automation·FaceWT·AlpetaDevice setup 유지.

**운영 반영**

```bash
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

### 기술 토큰·API 문서 검색 품질 개선 (2026-08-02)

알페타 설치 자동화 질문에서 산출물(`.exe`)을 자동화 파일로 오인하거나, alpeta swagger FaceWT/FAW API 질문에서 `swagger_kr.md`가 검색되지 않던 문제를 개선했습니다. Open WebUI 무응답(첫 토큰 대기)은 원인 분석만 했고 이번 코드 수정 범위가 아닙니다.

**NSIS 자동화 파일 검색**

- **증상**: “nsis로 알페타 설치하는 자동화 파일” 류 질문에 `AlpetaDevice.exe`가 우선되거나 `build_install.bat` 전체 경로가 안정적으로 나오지 않음.
- **원인**: 의미 유사도만으로는 `.bat`(자동화) / `.nsi`(스크립트) / `.exe`(산출물) 역할이 구분되지 않음. 평가기도 출처만 맞으면 필수 키워드 누락을 성공 처리할 수 있었음.
- **해결** (`rag/pipelines/rag_pipeline.py`): 파일 역할(artifact intent) 감지, 원문·경로·확장자 보존, RRF·리랭크에 기술 근거 점수 가산, 같은 지시문의 폴더+파일명 전체 경로 결합, 답변 프롬프트에 역할 구분·경로 비추측 규칙 추가.
- **평가 계약** (`rag/scripts/eval_retrieval.py`): 항목 성공 = **출처 + 모든 필수 키워드**. 골든에 NSIS 문항과 전체 경로(`D:\nsis\eXbuilder\build_install.bat`) 요구 추가.

**Swagger FaceWT/FAW API 검색**

- **증상**: “alpeta swagger에서 FAW/FaceWT 스키마·API” 질문에 User Guide·Protocol만 인용되고 “문서에 API 없다”에 가까운 오답.
- **원인**: 질문의 `alpeta` → `product=alpeta` 필터로 product 미태그인 `swagger_kr.md`가 후보에서 완전 배제. `FaceWT` 같은 CamelCase가 technical token으로 추출되지 않음.
- **해결**:
  - `rag/scripts/index_documents.py`: 파일명 swagger/openapi/api → `document_type=api`.
  - `rag_pipeline.py`: API 의도 시 `document_type=api` 스코프·product 필터 완화, CamelCase/대문자 식별자 토큰 보존, API evidence 가점, “Swagger 근거가 있으면 UI/프로토콜로 API 대체 금지” 프롬프트 규칙.
  - `rag/scripts/swagger_yaml_to_md.py`: 컨테이너 `/app/docs`와 로컬 `rag/data/docs` 기본 경로 자동 선택. `swagger_kr.md` 재생성.
- **재인덱싱**: 메타데이터 `api` + swagger 청킹 반영으로 청크 1437 → 1615. **반영 시 `--reset` 재인덱싱 필요**(이미 실행된 환경이면 pipelines 재기동만으로 코드 반영 가능).

**회귀·골든·실패 기록**

- `rag/scripts/test_rag_regression.py`: NSIS 역할 구분·FaceWT/API 스코프·평가 계약 등 추가 (**39/39** 통과).
- `rag/data/eval/golden_questions.json`: NSIS 4문항, FaceWT/FAW swagger 1문항, stream 경로 문항 등 추가.
- `PL_FAILURE_LOG.md`: PLF-20260801-001(무응답 분석·수정 대기), PLF-002(키워드 계약), PLF-003(기준선·pipe 원문 보존) 및 예방 체크리스트.
- eval 대상 FaceWT·NSIS는 PASS. 전체 exit 1은 stream 경로 키워드·일부 flaky 등 **비대상 잔여 FAIL** 때문.

**운영 반영**

```bash
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/swagger_yaml_to_md.py --input /app/docs/swagger_kr.yaml --output /app/docs/swagger_kr.md
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset
docker compose up -d --force-recreate pipelines
```

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
