# PL 실패 학습 기록

이 파일은 PL 개발 루프에서 발생한 실패의 원인과 재발 방지 방법을 프로젝트에 지속해서 남기는 기록이다.

모든 `pl`, `developer`, `verifier` 에이전트는 작업을 시작할 때 이 파일을 먼저 읽고 현재 작업에 관련된 예방 항목을 확인한다.

## 기록 규칙

1. `REVISE` 또는 `BLOCKED` 판정이 발생하면 PL이 재작업 전에 기록한다.
2. ID는 `PLF-YYYYMMDD-NNN` 형식을 사용한다.
3. 같은 근본 원인의 재발은 새 항목을 만들지 않고 기존 항목의 재발 횟수와 최신 근거를 갱신한다.
4. 원인이 입증되지 않았으면 `원인 조사 중`으로 표시하고 추측을 사실처럼 기록하지 않는다.
5. 재발 방지 항목은 다음 작업에서 확인할 수 있는 테스트, 명령 또는 코드 조건으로 작성한다.
6. 비밀값, 개인정보, 토큰, 전체 로그 덤프는 남기지 않는다.

## 상태

- `원인 조사 중`: 증상은 확인했지만 근본 원인이 입증되지 않음
- `수정 대기`: 근본 원인은 확인했고 수정이 필요함
- `검증 대기`: 수정했지만 재발 방지 검증이 완료되지 않음
- `해결·예방 확인`: 수정과 재발 방지 검증이 모두 통과함
- `외부 차단`: 권한, 외부 서비스 또는 실행 환경 때문에 진행할 수 없음

## 활성 예방 체크리스트

실패 기록에서 반복 적용해야 하는 예방 항목을 PL이 이곳에 요약한다. 각 항목에는 반드시 실패 ID와 적용 범위를 표시한다.

- [PLF-20260801-001] qwen3.5 계열은 Ollama 기본이 thinking이라 `think:false` 없이 호출하면 `message.content`가 비고 UI가 빈/점만 보일 수 있다. `ollama_chat`/`ollama_chat_stream`에 `think: False` 유지와, content 0·eval_count>0 시 경고/폴백을 확인한다.
- [PLF-20260801-001] `PIPELINES_DIR`에 빈 `__init__.py`를 두지 않는다. pipelines 런타임이 모듈로 로드해 `failed/`·`__init__/valves.json` 부산물을 만든다.
- [PLF-20260801-001] `pipe()`가 첫 yield 전에 재작성·검색·리랭크를 동기 수행하면 UI가 장시간 무응답처럼 보인다. 수정 시 즉시 상태 yield 또는 작업을 generator 안으로 옮기는지 확인한다.
- [PLF-20260801-002] 검색 평가는 예상 출처뿐 아니라 각 질문의 필수 키워드가 모두 검색되었을 때만 성공해야 한다. 파일 경로 질문은 폴더만이 아니라 파일명까지 포함한 전체 경로를 골든 기대값으로 검증한다.
- [PLF-20260801-003] 검색 품질 작업은 구현 전에 동일 인덱스의 기준선 출력과 종료 코드를 보존하고, 완료 후 실제 운영 파이프라인 답변 원문과 assertion을 verifier가 확인 가능한 기록으로 남긴다.
- [PLF-20260802-001] Postgres/config 복구 후 `alembic_version` stamp만으로 스키마가 최신이라 가정하지 않는다. `chat.pinned`/`meta`/`folder_id` 존재, `chat.chat` JSON 타입, `config.openai.api_base_urls`=`http://pipelines:9099`를 확인하고, Open WebUI→pipelines e2e(`chats/new`+`/api/chat/completions`+pipelines 로그 inlet/completions)로 연동을 증명한다.
- [PLF-20260802-002] 검색·생성 품질 작업은 최종 코드 변경 뒤 pipelines recreate → Ollama `/api/chat` readiness → direct `Pipeline.pipe()` raw/JSON assertion → basic/`--rerank` → regression을 같은 인덱스로 다시 실행하고, 각 종료 코드와 원문을 `rag/data/eval/artifacts/`에 남긴 뒤에만 완료로 본다.
- [PLF-20260802-003] 새 이슈의 Pipe probe/골든 항목을 추가할 때, 기존 probe 스크립트의 `QUESTIONS`/골든 파일에 있는 과거(이미 PASS된) 질문 키를 재사용하거나 그대로 두지 말고, 이번 작업의 실제 신규 질문 문자열이 `QUESTIONS`와 `golden_questions.json`에 새 키로 존재하는지, 그 raw 답변·assertion 파일이 이번 실행에서 새로 생성됐는지(타임스탬프·내용) 확인한다.
- [PLF-20260803-001] 지연 최적화 시 `OLLAMA_NUM_PREDICT`를 과도하게 낮추면 `reason=length`로 절차/표 답변이 중간에 끊겨 UI에서 “답변 안 됨”처럼 보인다. pipe/SSE assertion에 `reason=stop`(또는 충분한 본문)과 non-status 본문을 포함한다.
- [PLF-20260803-001] 진행 상태 문구를 일반 문자열로 yield하면 Open WebUI가 `delta.content`로 저장해 status가 본문에 섞이거나 최종 답변처럼 보인다. status는 `event.type=status` dict로 분리하고, e2e에서 `legacy_status_in_content=false`를 확인한다.
- [PLF-20260803-002] 「표로」후속 문맥화/MediaServer 표 enforce는 **최근 대화 주제가 미디어 서버 스펙일 때만** 적용한다. FaceWT/스키마/API 후속 「표로」에 MediaServer 표를 강제하면 안 된다. Case A(스키마→표로)와 Case B(미디어→표로) history pipe를 함께 회귀한다.
- [PLF-20260803-003] `is_media_server_spec_intent`인 단독 질문(예: `미디어서버 스펙 알려줘`)은 `len≤12` 후속 오탐·API 주제 가드에 의해 FaceWT/UG 문맥으로 덮어쓰지 않는다. solo MediaServer pipe와 FaceWT/MediaServer 「표로」후속을 함께 회귀한다.
- [PLF-20260803-004] 「정리/표도/알아보기 편하게/표를 활용/보기 쉽게」같은 **일반 재포맷 후속**은 최근 사용자 주제(자동빌드·API·미디어 등)로 문맥화한다. 마커는 `표 활용`(공백)만이 아니라 **`표를 활용`·`보기 쉽게`** 등 실제 UI 문구 변형을 포함해야 한다. 주제 불명이면 확인 요청. S1·`표를 활용해서 더 보기 쉽게 해줘`·S4와 S2/S3/S5를 함께 회귀한다.
- [PLF-20260803-004] 복수 인물 질문(`박준언, 방인재에 대해…`)은 단일 `extract_query_focus`만으로 intent를 끄지 말고 **이름 목록 추출** 후 Test.md 근거만 답하게 한다. MediaServer/UG 혼입·「없다」오진 금지.

## 실패 이력

### PLF-20260803-004: 자동빌드 후 「정리/표」후속이 UG 무관 주제로 환각

- 상태: 해결·예방 확인
- 분류: 구현 / 검색 품질
- 최초 발생: 2026-08-03
- 최근 재발: 2026-08-03 (문구 변형 `표를 활용해서 더 보기 쉽게 해줘`; 동 루프에서 복수 인물 intent 실패도 수정)
- 재발 횟수: 2
- 적용 범위: `is_follow_up_question`, `recent_user_follow_up_topic`, `rule_contextualize_follow_up`, 재포맷 마커, `extract_person_names`
- 관련: PLF-20260803-002/003

#### 실패 내용

- 작업 목표: `alpeta 자동빌드…` 후 재포맷 후속 → NSIS 자동화 절차 표/정리
- 실패한 수용 기준: S1 — UG 검색·카드·건강이력 등 무관 답; 재발 시 UG 사용자·그룹 관리 표
- 근거: 사용자 스크린샷; `24_baseline_diagnose.json` — `표를 활용해서…`에 `is_follow_up=false`, marker hits `[]`
- 부가(동 루프): `박준언, 방인재에 대해 알려줘` — `person_intent=false`(단일 focus 정규식), 방인재 누락·MediaServer 혼입

#### 원인

- 직접 원인: (1) 재포맷 마커가 `표 활용`/`읽기 쉽게`에 한정되어 `표를 활용`/`보기 쉽게` 미매칭 (2) 복수 인물 질문이 `[가-힣]{2,4}` 단일 focus에 걸려 person intent 실패
- 근본 원인: 후속/인물 감지가 **일부 문구·단일 이름**만 가정하고 UI에 나오는 실제 변형·복수 나열을 계약으로 두지 않음
- 원인 확신도: 높음

#### 해결

- 마커에 `표를 활용`/`보기 쉽게` 추가; `extract_person_names` + Test.md 다중 주입/필터
- S-build/S-people pipe + regression
- 외부 차단: 없음

#### 재발 방지 확인

- [x] `알아보기 편하게 정리해서 적어줘 표도 활용하고` (23_)
- [x] **`표를 활용해서 더 보기 쉽게 해줘`** history pipe — NSIS, UG 금지 (`24_post_pipe_*`)
- [x] `박준언, 방인재에 대해 알려줘` — 1994+1996, 무관 혼입 없음
- [x] S2/S3/S5/S4 유지; regression exit 0

#### 검증 이력

- 검증 일자: 2026-08-03
- 결과: verifier **PASS** (23_ 루프 및 24_ 재발 수정)
- 근거: 24_ S-build/S-people pass; regression 89/89; recreate+Ollama 200

---

### PLF-20260803-003: 단독 「미디어서버 스펙 알려줘」가 후속 오탐으로 UG/FaceWT 문맥에 덮임

- 상태: 해결·예방 확인
- 분류: 구현 / 검색 품질
- 최초 발생: 2026-08-03
- 최근 재발: 2026-08-03
- 재발 횟수: 1
- 적용 범위: `is_follow_up_question`, `rule_contextualize_follow_up` (PLF-20260803-002 FaceWT 가드의 부작용)
- 관련: PLF-20260803-002

#### 실패 내용

- 작업 목표: `"미디어서버 스펙 알려줘"` → MediaServer_Specs_New.md 4구간 표
- 실패한 수용 기준: A — UI가 UG만 출처로 “스펙 없다”+단말기 절차 설명
- 관찰: history 있는 채팅에서 단독 미디어 질문이 후속으로 처리됨
- 근거: `22_baseline_diagnose.json` — len=12, `is_follow_up=true`; Step0이 UG/FaceWT 스키마 표로 문맥화. retrieval top은 MediaServer였음(H4 아님)

#### 원인

- 직접 원인: (1) `len(q)<=12`가 완전 미디어 스펙 질문을 후속 오탐 (2) API 주제 가드가 후속 「스펙」을 FaceWT 스키마 표 질문으로 덮어씀
- 근본 원인: FaceWT 「표로」가드(002)와 짧은 질문 후속 휴리스틱이 **이미 media intent인 단독 질문**을 예외로 두지 않음
- 원인 확신도: 높음

#### 해결

- media intent면 `is_follow_up_question` → False
- `rule_contextualize_follow_up`에서 현재 질문이 media intent면 API 덮어쓰기 금지
- 외부 차단: 없음

#### 재발 방지 확인

- [x] `"미디어서버 스펙 알려줘"` pipe — MediaServer 4구간 (`22_post_pipe_mediaserver_solo_spec`)
- [x] FaceWT/MediaServer 「표로」후속 동시 PASS (`22_post_pipe_facewt_*`, `*_mediaserver_followup_*`)
- [x] `test_mediaserver_solo_spec_not_follow_up_or_api_hijack` + regression exit 0

#### 검증 이력

- 검증 일자: 2026-08-03
- 결과: verifier **PASS**
- 근거: solo/Case A/B pass; regression 85/85; recreate+Ollama 200

---

### PLF-20260803-002: FaceWT/스키마 「표로」후속이 MediaServer 스펙 표로 강제됨


- 상태: 해결·예방 확인
- 분류: 구현 / 검색 품질
- 최초 발생: 2026-08-03
- 최근 재발: 2026-08-03
- 재발 횟수: 1
- 적용 범위: `rag/pipelines/rag_pipeline.py`(`rule_contextualize_follow_up`, MediaServer enforce), follow-up 「표로」

#### 실패 내용

- 작업 목표: MediaServer 「표로」후속 품질(20_) 이후, FaceWT 스키마 대화에서 「표로」후속이 swagger 표를 유지
- 실패한 수용 기준: (회귀) 후속이 MediaServer_Specs 카메라 구간 표를 출력
- 관찰된 증상: FaceWT Q 후 `스키마 구조는 표로 해서 읽기 쉽게 다시 알려줘` → 출처 MediaServer_Specs_New.md
- 재현: FaceWT history + 해당 후속 문자열로 `Pipeline.pipe()`
- 근거: 사용자 스크린샷; `rule_contextualize_follow_up`이 media 마커+표/스펙 시 MediaServer 고정 질문으로 변환

#### 원인

- 직접 원인: MediaServer 표 후속 규칙·LIST 「표로」확장이 주제 가드 없이(또는 최근 API 주제 미우선으로) 스키마 후속에도 적용
- 근본 원인: 「표로」를 MediaServer 전용 완결 신호로 취급하고 최근 대화 주제(API vs media)를 분리하지 않음
- 원인 확신도: 높음(코드·Case A/B pipe)

#### 해결

- `recent_user_follow_up_topic` 가드: API/스키마 → FaceWT 스키마 표 문맥화; media일 때만 MediaServer 고정
- 「표로」단독 MediaServer 강제 제거; Case A/B/C pipe + 단위 테스트
- 외부 차단: 없음

#### 재발 방지 확인

- [x] Case A: 후속 문자열 history pipe — swagger FaceWT, MediaServer/카메라 구간 없음 (`21_post_pipe_facewt_schema_table_followup`)
- [x] Case B: MediaServer 「스펙을 표로」— 4구간 유지
- [x] `test_bare_table_marker_alone_does_not_force_mediaserver` 등 회귀
- [x] 신규 probe/golden에 실제 후속 문자열 (PLF-20260802-003)

#### 검증 이력

- 검증 일자: 2026-08-03
- 결과: verifier **PASS**
- 근거: Case A/B pass; regression 84/84 exit 0; recreate+Ollama 200
- 후속 재발: 동일 가드가 단독 MediaServer 질문을 API 문맥으로 덮어씀 → **PLF-20260803-003**으로 분리 기록·수정 후 Case A/B 재확인 PASS

---

### PLF-20260803-001: 지연 최적화 후 status content 혼입·NUM_PREDICT 과소로 UI가 빈/깨진 답변처럼 보임


- 상태: 해결·예방 확인
- 분류: 구현 / 성능 / 환경
- 최초 발생: 2026-08-03
- 최근 재발: 2026-08-03
- 재발 횟수: 1
- 적용 범위: `docker-compose.yml`(`OLLAMA_NUM_PREDICT`), `rag/pipelines/rag_pipeline.py`(status yield, 토큰 공백 복원), Open WebUI↔pipelines SSE

#### 실패 내용

- 작업 목표: 지연 최적화(15_latency) 이후 사용자가 보고한 RAG 무응답/빈 답변 회귀 복구
- 실패한 수용 기준: (회귀 보고) A/B — UI에서 답변이 없거나 status만/깨진 출력으로 보임
- 관찰된 증상: 파이프라인은 검색·생성까지 진행하나 `reason=length`(220 tok) 조기 절단; chat history ASSISTANT가 `문서 검색 준비 중...` 등 status 문자열로 시작; 본문에 `FA W T`/`t e r m i n a l s` 글자 공백 깨짐
- 재현 절차: latency 설정(`NUM_PREDICT=220`, status 문자열 yield)으로 절차형 질문 pipe/SSE 후 Open WebUI 저장 답변·pipelines 로그 확인
- 근거: `16_pipelines_logs.txt`(length×3, status 혼입, 공백 깨짐); 수정 후 `16_empty_fix_summary.json` pass true, `16_e2e_pipelines_sse.json` content_len>0·legacy_status_in_content=false

#### 원인

- 직접 원인: (1) `OLLAMA_NUM_PREDICT=220`으로 생성 조기 종료 (2) status를 plain string yield → Open WebUI `delta.content` 혼입 (3) 절단/생성 품질로 식별자 글자 공백 깨짐
- 근본 원인: 지연 목표만 warm wall-clock으로 합격 처리하고, UI content 계약(status 분리)·완결 생성(`reason=stop`/충분 predict)·본문 품질 assertion을 완료 조건에 넣지 않음
- 원인 확신도: 높음(전후 로그·SSE·pipe assertion)

#### 해결

- 적용한 수정:
  1. `OLLAMA_NUM_PREDICT` 220→768
  2. status를 Open WebUI `event.type=status` dict로 분리(본문 미혼입)
  3. 식별자 공백 금지 지침 + `repair_spaced_document_tokens()`
  4. think:false 유지; regression에 status/공백/think 테스트 추가
- 외부 차단 해소 조건: 없음

#### 재발 방지 확인

- [x] pipe/SSE assertion: non-empty 본문, status-only 아님, `legacy_status_in_content=false`
- [x] 절차형 대표 질문에서 `reason=stop` 또는 eval_count가 이전 length 한도(220)를 넘는 생성 증거
- [x] compose/런타임 `OLLAMA_NUM_PREDICT`가 과도하게 낮지 않음(현재 768) 및 recreate 반영
- [x] `think: False` 유지, `__init__.py` 없음, 첫 status event는 검색 전 즉시(first_yield≈0)

#### 검증 이력

- 검증 일자: 2026-08-03
- 결과: verifier **PASS** (수용 기준 A–G)
- 근거: `16_empty_fix_*` 2/2 pass; SSE e2e content_len=235 exit 0; regression 63/63 exit 0; NUM_PREDICT=768; FaceWT 48.8s stop / user_terminal 76.5s stop(지연 trade-off 명시)

---

### PLF-20260802-003: 신규 이슈의 Pipe 검증이 기존(이미 해결된) 질문만 재확인하고 실제 신규 질문을 검증하지 않음

- 상태: 해결·예방 확인
- 분류: 테스트 / 검색 품질
- 최초 발생: 2026-08-02
- 최근 재발: 2026-08-02
- 재발 횟수: 1
- 적용 범위: `rag/data/eval/artifacts/11_probe_pipeline_issues.py`(`QUESTIONS`), `rag/data/eval/golden_questions.json`, NSIS 자동화 버전·User Guide 사용자/단말기 답변 완결성

#### 실패 내용

- 작업 목표: "alpeta 자동빌드하려면 어떻게 하면돼?" 질문이 자동화 버전 섹션의 1~7단계(특히 5번 하위 작업, 6번 D:\nsis\install)를 빠짐없이 답하는지 실제 `Pipeline.pipe()`로 증명
- 실패한 수용 기준: A, E — 이슈1의 실제 신규 질문에 대한 pipe 원문·assertion·골든 항목이 존재하지 않음(초기); 재작업 중간에는 이슈2 assertion(`[단말기리스트]`/`출입그룹 단말기 리스트`) 미달
- 관찰된 증상: `09_probe_pipeline_role_scope.py`의 `QUESTIONS`가 `nsis_build_output`과 `user_terminal_sync`만 포함하여 신규 자동빌드 질문이 검증되지 않음
- 재현 절차: probe `QUESTIONS`와 `golden_questions.json`에 신규 질문 키 부재 여부 확인
- 근거: 상위 감독이 산출물을 직접 대조해 재작업 지시

#### 원인

- 직접 원인: developer가 이슈1 코드는 구현했으나 probe/골든에 실제 신규 질문을 추가하지 않고 과거 PASS 질문만 재실행함
- 근본 원인: PL이 기존 probe에 과거 질문이 들어 있다는 사실과 신규 질문 추가 여부를 명시적으로 대조하지 않음
- 원인 확신도: 높음(파일 내용 직접 대조)

#### 해결

- 적용한 수정:
  1. `11_probe_pipeline_issues.py`에 `automated_build` 새 키와 이슈1 질문 문자열·assertion(수동 배제·하위 작업·install 경로) 추가
  2. `golden_questions.json`에 신규 질문과 `gitpull.bat`/`define.go`/`alpeta_device.nsi`/`alpeta.nsi`/`build_install.bat`/`proto_compile`/`D:\nsis\install` 키워드 추가
  3. User Guide 표기 보존(`\[단말기리스트\]`, 화면 구성 3항목) 프롬프트·facet·`enforce_document_term_pairs` 보강
  4. 최종 코드 뒤 pipelines recreate → Ollama readiness → `14_final3` pipe raw/JSON → eval basic/rerank → regression
- 외부 차단 해소 조건: 없음

#### 재발 방지 확인

- [x] `golden_questions.json`에 이슈1 신규 질문 골든 항목 존재, `expected_keywords`에 `gitpull.bat`/`define.go`/`alpeta_device.nsi`/`alpeta.nsi`/`build_install.bat`/`proto_compile`/`D:\nsis\install` 포함
- [x] probe `QUESTIONS`에 `automated_build` 새 키와 신규 질문 문자열이 있고, `14_final3_pipe_automated_build.json`/raw가 이번 실행 타임스탬프(`2026-08-02T11:07:40Z`)로 생성됨
- [x] assertion에 수동 방식(MakeNSISW, 파일 아이콘, Compile NSI scripts) 배제 검사 포함
- [x] 최종 assertion `pass: true` (이슈1·이슈2 모두 `14_final3_pipe_*.json`)

#### 검증 이력

- 검증 일자: 2026-08-02
- 결과: verifier **PASS** (수용 기준 A–F)
- 근거: `14_final3_pipe_automated_build.json`/`14_final3_pipe_user_terminal_sync.json` pass true; ideal md 대조; regression 60/60 exit 0; eval 대상 골든 PASS(전체 basic 15/18·rerank 16/18 exit 1은 Test.md 등 비대상); index 1591; Ollama chat 200; recreate→ollama→pipe→eval→regression 체인 확인

---

### PLF-20260802-002: RAG 품질 변경의 실제 Pipe 생성 검증과 전체 골든 평가가 완료되지 않음

- 상태: 해결·예방 확인
- 분류: 환경 / 검색 품질 / 테스트
- 최초 발생: 2026-08-02
- 최근 재발: 2026-08-02
- 재발 횟수: 4 (이후 검증 완료 루프로 해소)
- 적용 범위: `rag/pipelines/rag_pipeline.py`, Ollama 접근 경로, `rag/data/eval/golden_questions.json`, 평가·Pipe 증거 산출물

#### 실패 내용

- 작업 목표: NSIS 산출물 경로 역할 구분 및 User Guide 사용자·단말기 동기화 답변 품질을 실제 Pipeline.pipe로 증명
- 실패한 수용 기준: A, B, D, E — 실제 생성 답변 assertion, User Guide 필수 검색 키워드, 변경 후 basic/rerank 품질 비교 (과거 BLOCKED 시점)
- 관찰된 증상: post Pipe probe의 답변은 `None`이고 assertions가 모두 false이며, User Guide 골든에서 `단말기 사용자 리스트` 필수 키워드가 누락됨; 이후에는 최종 코드 뒤 Pipe·eval 미재실행으로 BLOCKED
- 재현 절차: `08_post_pipe_runlog.exit.txt`의 Pipe probe 및 `08_baseline_eval_basic.txt`의 골든 평가 결과 확인
- 근거:
  - `08_post_pipe_runlog.exit.txt`: `http://host.docker.internal:11434/api/chat` 호출이 404로 종료(exit 1)
  - `08_post_pipe_nsis_build_output.json`, `08_post_pipe_user_terminal_sync.json`: 생성 답변 `None`, assertion `pass: false`
  - `08_baseline_eval_basic.txt`: 13/17, source 15/17, keyword 29/33이며 새 User Guide 항목의 필수 키워드 실패
  - post basic/rerank 평가 원문과 종료 코드가 없어 변경 전후 비하락을 판정할 수 없음
  - 재작업 뒤 raw Pipe 원문과 endpoint 200은 확보했지만, `08_post_pipe_user_terminal_sync.json`의 10개 assertion 중 생성기 `assert_user_terminal_sync()`가 실제 계산하는 것은 6개뿐이라 확장 assertion의 재현 근거가 없음
  - assertion 생성기 일치 보강 뒤에도 실제 User Guide 답변 첫 메뉴가 PDF의 `[단말기리스트]`가 아닌 `[단말기 저장 리스트]`로 생성됐고, post index-status artifact가 없음
  - 최종 코드에서는 메뉴·facet·assertion을 다시 변경했지만, 변경 뒤 Pipeline.pipe()와 basic/rerank 평가를 재실행하지 않아 저장 raw 재검증(exit 0)만 존재하고 최종 동작 증거가 없음

#### 원인

- 직접 원인: Pipe probe가 Ollama Chat API가 아닌 404 응답 경로를 호출해 생성 단계를 완료하지 못했고, User Guide 검색 결과가 필요한 절차 용어를 모두 회수하지 못했으며, 보강한 assertion JSON의 일부 필드가 실제 생성 함수에서 계산되지 않았고, 메뉴명 정확성·순서를 assertion으로 검증하지 않았으며, 마지막 코드 변경 후 직접 Pipe·평가를 다시 실행하지 않음
- 근본 원인: 운영 파이프라인과 동일한 Ollama endpoint, post 평가, 모든 저장 assertion의 코드-출력 대응, PDF 핵심 UI 용어의 금지/순서 검증, post 인덱스 상태 보존 및 최종 diff 뒤 전체 재검증을 구현 완료 조건 앞에 배치하지 않음
- 원인 확신도: 높음(HTTP 404·Pipe JSON·평가 원문)

#### 해결

- 적용한 수정:
  1. Ollama `/api/chat` readiness 확인 후 pipelines recreate
  2. User Guide 검색 확장·`overwrite_option` facet·문서 용어 보존 프롬프트, 골든 키워드 `다시 다운로드` 보강
  3. 최종 코드 기준 direct `Pipeline.pipe()`로 Q1/Q2 raw·JSON assertion 재생성 (`09_*`)
  4. 동일 인덱스(1591)에서 basic/`--rerank`·regression 재실행 및 exit·원문 보존
- 외부 차단 해소 조건: 없음(검증 완료로 해소)

#### 재발 방지 확인

- [x] Pipe probe 전에 pipelines 컨테이너의 Ollama API base URL에 `/api/chat` 요청이 200 또는 유효한 모델 응답을 내는지 별도 종료 코드로 확인 (`09_pipelines_ollama_chat.txt` STATUS=200, exit 0)
- [x] User Guide 골든은 출처뿐 아니라 `단말기 사용자 리스트` 등 모든 절차 필수 키워드를 실제 평가 결과에서 확인 (`09_post_eval_basic/rerank` 대상 골든 PASS)
- [x] post basic/rerank 원문·각 종료 코드·인덱스 상태를 artifact로 보존하고 verifier가 답변 원문과 assertion을 확인 (`09_post_eval_*`, `09_index_status.txt` 1591)
- [x] assertion JSON에 기록한 모든 필드는 생성 함수가 원문을 대상으로 실제 계산하고 같은 실행에서 출력됐는지 코드와 artifact를 대조 (`09_probe_pipeline_role_scope.py` ↔ JSON 키 1:1)
- [x] PDF UI 메뉴는 정확한 용어와 순서를 원문 assertion으로 검사하고 유사하지만 문서에 없는 메뉴명을 배제 (`has_terminal_list_menu`, `excludes_wrong_terminal_storage_list`)
- [x] post 실행 전후 인덱스 상태를 별도 status artifact와 종료 코드로 보존 (`09_index_status.exit.txt` = 0)
- [x] 모든 최종 코드 변경 뒤 pipelines 재생성, direct `Pipeline.pipe()` raw/JSON, basic·rerank 평가를 같은 인덱스 조건에서 다시 실행하고 각 종료 코드를 보존 (`09_pipelines_recreate2`, `09_post_pipe_*`, eval/regression)

#### 검증 이력

- 검증 일자: 2026-08-02
- 결과: 이전 verifier REVISE(4회)·BLOCKED(재작업 한도) 후, 검증 완료 루프에서 verifier **PASS**
- 근거: `09_post_pipe_nsis_build_output.json`/`09_post_pipe_user_terminal_sync.json` pass true; `09_post_regression` 51/51 exit 0; basic 14/17·rerank 15/17(전체 exit 1, 대상 골든 PASS); index 1591; Ollama chat 200

---

### PLF-20260802-001: Open WebUI↔Pipelines 질문이 chat 스키마 손상으로 전달되지 않음

- 상태: 해결·예방 확인
- 분류: 환경
- 최초 발생: 2026-08-02
- 최근 재발: 2026-08-02 (verifier REVISE: e2e/스키마 증거 파일 미보존)
- 재발 횟수: 2
- 적용 범위: Open WebUI Postgres(`chat`, `config`), docker-compose OpenAI env, pipelines 연동

#### 실패 내용

- 작업 목표: Open WebUI에서 도우미(`rag_pipeline`)로 질문이 pipelines까지 전달되게 복구
- 실패한 수용 기준: A — pipelines 로그에 chat/completions 또는 inlet 요청이 없음(복구 전); 이후 verifier A/B 증거 파일 부재
- 관찰된 증상: pipelines는 GET `/models` 200만 기록; Open WebUI `POST /api/v1/chats/new` 400
- 재현 절차: DB 복구 직후 a@a.com으로 도우미 채팅 생성/질문; 또는 `chats/new` API
- 근거:
  - open-webui 로그: `column "pinned" of relation "chat" does not exist`
  - `chat` 컬럼을 추가한 뒤에도 `chat` 타입이 `text`라 ChatModel 검증 `dict_type` 실패
  - `config.data`가 `{}`였고, compose env의 OPENAI_*는 모델 목록(GET `/models`)에는 반영됨
  - verifier REVISE: PL 콘솔 출력만 있고 `rag/data/eval/artifacts/`에 e2e·스키마·pipelines 로그 스냅샷이 없음

#### 원인

- 직접 원인: 채팅 INSERT/검증 실패로 completions 호출 전에 UI/API가 중단됨
- 근본 원인: Postgres 복구 시 alembic head stamp와 빈 `config`만 맞추고, 실제 `chat` 스키마·OpenAI PersistentConfig를 현재 앱 모델에 맞추지 않음
- 원인 확신도: 높음(에러 로그·스키마·e2e 전후 비교)
- 검증 절차 결함: 운영 수정 후 통과 근거를 verifier가 읽을 파일로 고정하지 않음(PLF-20260801-003과 동일 계열)

#### 해결

- 적용한 수정(운영 DB, 볼륨 wipe 없음):
  1. `chat`에 `pinned`/`meta`/`folder_id` 및 관련 인덱스 추가
  2. `chat.chat`를 `text`→`json` 변환
  3. `config`에 openai enable·`http://pipelines:9099`·API key 복구 후 open-webui 재시작
  4. e2e/스키마/ps/pipelines 로그를 `rag/data/eval/artifacts/06_*`로 재캡처
- 외부 차단 해소 조건: 없음

#### 재발 방지 확인

- [x] `\d chat`/information_schema 스냅샷 파일에 pinned/meta/folder_id 및 chat json 타입 (`06_schema_config_snapshot.txt`)
- [x] config 스냅샷에 openai.api_base_urls=pipelines(키는 set/length만) (`06_schema_config_snapshot.txt`)
- [x] Open WebUI 모델 목록에 `rag_pipeline` 포함 (`06_e2e_webui_pipeline.txt`, `06_pipelines_models.txt`)
- [x] e2e stdout에 chats_new/completions 200·content_len>0 및 pipelines 로그 inlet/completions 200 (`06_e2e_*.txt`, `06_pipelines_logs_since.txt`)

#### 검증 이력

- 검증 일자: 2026-08-02
- 결과: 첫 verifier `REVISE` 후 `06_*` 증거 고정, 재검증 `PASS`
- 근거: `06_compose_ps.txt`, `06_schema_config_snapshot.txt`, `06_e2e_webui_pipeline.txt`(exit 0, content_len=208), `06_pipelines_logs_since.txt`(inlet·completions 200)

---

### PLF-20260801-001: Open WebUI 도우미 응답이 점(·)만 보이거나 비어 보임

- 상태: 수정 대기
- 분류: 구현 / 환경
- 최초 발생: 2026-08-01
- 최근 재발: 2026-08-01
- 재발 횟수: 1
- 적용 범위: `rag/pipelines/rag_pipeline.py`, Open WebUI↔pipelines↔Ollama(qwen3.5), `rag/pipelines/` 로드 구조

#### 실패 내용

- 작업 목표: 채팅 무응답/점만 표시 원인 분석
- 실패한 수용 기준: (분석 단계) UI에 실질 답변 텍스트가 보여야 함
- 관찰된 증상: 도우미 응답 영역에 검은 점만 표시; pipelines는 inlet/chat/completions 200
- 재현 절차: Open WebUI에서 도우미(rag_pipeline)로 단문 전송; 또는 Ollama에 qwen3.5:4b를 `think` 미지정으로 스트리밍
- 근거:
  - Ollama 프로브: `think=false` → content 있음; `think` 생략/`true` → content 0·thinking만 존재
  - pipelines 직접 SSE: `rag_pipeline` 스트림에 delta.content 정상(수백 자)
  - DB 채팅: rag_pipeline 답변은 저장됨; 동일 대화 첫 응답은 model=`qwen3.5:4b` + reasoning details
  - `pipe()`는 첫 yield 전 재작성·검색·리랭크 동기 수행(리랭크 배치 ~18s 로그)
  - `rag/pipelines/__init__.py` 삭제 및 `__init__/`, `failed/`는 런타임 부산물로 빈 응답의 직접 원인 아님

#### 원인

- 직접 원인:
  1. qwen3.5 기본 thinking 시 `message.content` 공백 → 스트리밍 yield 없음 → UI 빈/점
  2. RAG `pipe()` 선지연으로 첫 토큰 전 UI가 장시간 비어 보임
  3. 모델 선택 혼선(직접 qwen3.5 vs 도우미)으로 증상이 겹쳐 보임
- 근본 원인: thinking 모델과 Open WebUI/파이프라인 스트리밍 계약(`delta.content`) 불일치 + 첫 토큰 전 동기 작업
- 원인 확신도: 높음(thinking 공백 content·SSE 정상·선지연은 재현/코드로 확인). 스크린샷 순간의 “완료 후 점만 고정”은 중간(UI 상태/버퍼링)

#### 해결

- 적용한 수정: 없음(분석만). 기존 코드에 `think: False`는 이미 있음
- 외부 차단 해소 조건: 없음
- 권장 수정(대기):
  1. `ollama_chat_stream`에서 content 없이 thinking만 오면 폴백 yield 또는 명시 오류
  2. done 시 content 0·eval_count>0 경고 로그
  3. `pipe()`가 generator 반환 직후/작업 중 상태 문구를 먼저 yield
  4. pipelines 디렉터리에서 `__init__.py` 모듈 로드 방지(빈 패키지 파일 제거 유지·`failed/` 정리)

#### 재발 방지 확인

- [ ] `think` 생략 Ollama 호출 시 content 공백을 회귀 테스트로 고정하고, 파이프라인 경로는 content 또는 명시 오류를 보장
- [ ] 도우미로 "안녕" 전송 시 UI/ SSE에 비어 있지 않은 답변 텍스트 확인
- [ ] `rag/pipelines/`에 로드 대상이 `rag_pipeline.py`만 있는지(`failed/`, `__init__/` 부산물 설명 가능) 확인
- [ ] 첫 yield 전 동기 검색이 남아 있으면 상태 메시지 또는 구조 변경 여부 확인

#### 검증 이력

- 검증 일자: 2026-08-01
- 결과: 원인 분석 완료, 코드 수정 미실시
- 근거: Ollama think 필드 프로브, pipelines SSE 프로브, postgres chat 메시지 길이/모델, pipelines/Open WebUI 로그

---

### PLF-20260801-002: 검색 평가가 필수 정답 누락을 성공 처리함

- 상태: 해결·예방 확인
- 분류: 테스트 / 검색 품질
- 최초 발생: 2026-08-01
- 최근 재발: 2026-08-01
- 재발 횟수: 1
- 적용 범위: `rag/scripts/eval_retrieval.py`, `rag/data/eval/golden_questions.json`, 기술 파일명·경로 검색 평가

#### 실패 내용

- 작업 목표: NSIS 자동화 파일 질문과 유사한 기술 토큰 검색 개선을 회귀 평가로 보장
- 실패한 수용 기준: C, E — 필수 정답 키워드 누락 시 평가 실패 및 전체 경로 정확성 보장
- 관찰된 증상: 평가기가 예상 출처만 검색되면 필수 키워드가 누락되어도 성공 종료할 수 있고, 대상 골든은 폴더 경로만 검사함
- 재현 절차: `evaluate()`의 종료 조건과 대상 골든의 `expected_keywords`를 확인
- 근거:
  - `eval_retrieval.py`가 `source_hits == len(entries)`만으로 종료 코드를 결정함
  - 대상 골든이 `D:\nsis\eXbuilder`까지만 요구해 `D:\nsis\eXbuilder\build_install.bat` 전체 경로를 보장하지 않음
  - 첫 verifier 판정 `REVISE`

#### 원인

- 직접 원인: 키워드 적중 수를 평가 성공 조건에 포함하지 않았고 골든 기대값의 경로 정밀도가 부족함
- 근본 원인: 검색 평가 계약이 “정답 출처 검색”과 “질문에 필요한 근거 검색”을 구분하지 않음
- 원인 확신도: 높음

#### 해결

- 적용한 수정: 출처와 모든 필수 키워드를 항목 성공 조건에 포함하고, 대상 경로 기대값을 파일명까지 포함한 전체 경로로 강화함
- 외부 차단 해소 조건: verifier의 Windows 읽기 전용 셸 제한은 셸 실행 가능한 developer와 PL의 결과 및 후속 정적 검증으로 보완

#### 재발 방지 확인

- [x] 하나라도 필수 키워드가 빠진 골든 항목은 `evaluate()`가 실패 종료하는 단위 테스트 추가
- [x] 파일 경로 골든은 폴더와 파일명을 결합한 전체 경로를 요구
- [x] Docker 회귀 테스트와 기본/리랭커 평가의 종료 코드 및 항목별 키워드 결과를 함께 보고

#### 검증 이력

- 검증 일자: 2026-08-01
- 결과: 첫 verifier `REVISE` 후 수정, 예방 확인 완료
- 근거: Docker 회귀 테스트 34/34 통과, 기본/리랭커 평가에서 대상 출처·파일명·전체 경로 적중, 누락 키워드 실패 계약 단위 테스트 통과

---

### PLF-20260801-003: verifier 환경에서 통합·변경 전 증거를 독립 실행하지 못함

- 상태: 해결·예방 확인
- 분류: 환경 / 테스트
- 최초 발생: 2026-08-01
- 최근 재발: 2026-08-01
- 재발 횟수: 1
- 적용 범위: Windows verifier 읽기 전용 셸, 실제 파이프라인 답변, 검색 평가 변경 전 기준선

#### 실패 내용

- 작업 목표: 실제 답변과 변경 전후 검색 품질을 verifier가 독립 확인
- 실패한 수용 기준: A, E — 실제 파이프라인 답변 원문 및 동일 조건 변경 전 평가 원시 출력
- 관찰된 증상: verifier가 코드·Docker 결과 기록은 확인했지만 읽기 전용 셸 격리 부재로 직접 실행하지 못했고, PL 실행 기록에는 실제 파이프라인 probe와 변경 전 원시 평가가 없음
- 재현 절차: verifier에서 Git/Docker 명령 실행 시 Windows 읽기 전용 샌드박스 생성 실패
- 근거:
  - Docker 회귀 34/34 및 현재 기본/리랭커/단계 진단 원시 기록은 존재
  - 대상 정답 청크는 현재 RRF·리랭커 1위이나 실제 생성 답변 원문은 developer 요약에만 존재
  - 최종 verifier 판정 `BLOCKED`

#### 원인

- 직접 원인: verifier 실행 환경 제약과 구현 전 원시 결과 미보존
- 근본 원인: 구현 전 기준선 및 최종 통합 probe를 verifier가 접근 가능한 실행 기록으로 남기는 절차가 작업 시작 시 확립되지 않음
- 원인 확신도: 높음

#### 해결

- 적용한 수정: 운영 `Pipeline.pipe()` 답변 원문과 자동 assertion을 기록하고, `git show HEAD` 코드를 임시 read-only 마운트로 격리 실행해 동일 인덱스 기준선을 재현함
- 외부 차단 해소 조건: 셸 실행 가능한 환경에서 실제 파이프라인 probe 원문을 기록하고, 가능하면 동일 인덱스의 변경 전 코드를 격리 실행해 기준선을 보존한 뒤 verifier가 기록을 확인

#### 재발 방지 확인

- [x] 검색 품질 구현 전에 기준선 명령·출력·인덱스 조건을 verifier가 접근 가능한 위치에 보존
- [x] 최종 통합 probe 명령과 답변 원문을 테스트 기록에 포함
- [x] 순차 명령은 각 종료 코드를 별도 기록해 마지막 명령의 성공으로 앞선 실패를 가리지 않음

#### 검증 이력

- 검증 일자: 2026-08-01
- 결과: 첫 최종 verifier `BLOCKED` 후 증거를 보강해 재검증 `PASS`
- 근거: 운영 답변 세 assertion 통과, HEAD 기준선 basic/rerank 각각 Source 6/7·Keyword 5/8, 현재 기존 7개 동일 수치로 비하락 확인

---

## 새 기록 템플릿

### PLF-YYYYMMDD-NNN: 실패 제목

- 상태:
- 분류: 구현 / 테스트 / 요구사항 / 성능 / 검색 품질 / 환경 / 권한
- 최초 발생:
- 최근 재발:
- 재발 횟수:
- 적용 범위:

#### 실패 내용

- 작업 목표:
- 실패한 수용 기준:
- 관찰된 증상:
- 재현 절차:
- 근거:

#### 원인

- 직접 원인:
- 근본 원인:
- 원인 확신도: 높음 / 중간 / 낮음

#### 해결

- 적용한 수정:
- 외부 차단 해소 조건:

#### 재발 방지 확인

- [ ] 다음 작업에서 실행할 테스트 또는 명령
- [ ] 확인할 코드 조건 또는 설정

#### 검증 이력

- 검증 일자:
- 결과:
- 근거:
