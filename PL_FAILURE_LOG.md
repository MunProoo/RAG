# PL 실패 학습 기록

이 파일은 PL 개발 루프에서 발생한 실패의 원인과 재발 방지 방법을 남기는 기록이다.

공개 저장소에는 **일반화된 예방 규칙만** 둡니다. 사내 제품명·경로·원문 답변·전체 로그는 기록하지 마세요.

## 기록 규칙

1. `REVISE` 또는 `BLOCKED` 판정이 발생하면 PL이 재작업 전에 기록한다.
2. ID는 `PLF-YYYYMMDD-NNN` 형식을 사용한다.
3. 같은 근본 원인의 재발은 새 항목을 만들지 않고 기존 항목을 갱신한다.
4. 원인이 입증되지 않았으면 `원인 조사 중`으로 표시한다.
5. 재발 방지 항목은 테스트·명령·코드 조건으로 작성한다.
6. 비밀값, 개인정보, 토큰, 사내 문서 원문, 전체 로그 덤프는 남기지 않는다.

## 상태

- `원인 조사 중` / `수정 대기` / `검증 대기` / `해결·예방 확인` / `외부 차단`

## 활성 예방 체크리스트 (일반)

- [PLF-GENERIC-001] qwen 계열은 Ollama 호출에 `think:false`를 명시한다. content가 비면 thinking 여부를 의심한다.
- [PLF-GENERIC-002] `PIPELINES_DIR`에 빈 `__init__.py`를 두지 않는다.
- [PLF-GENERIC-003] `pipe()` 첫 yield 전에 긴 동기 작업을 두지 말고, 상태 이벤트를 먼저 보낸다.
- [PLF-GENERIC-004] 검색 평가는 **기대 출처 + 필수 키워드 전부**일 때만 성공으로 본다.
- [PLF-GENERIC-005] 품질 작업은 recreate → readiness → pipe assertion → eval → regression 순으로 같은 인덱스에서 검증한다.
- [PLF-GENERIC-006] 새 골든/probe 질문은 **이번 이슈의 신규 문자열**이어야 하며, 과거 PASS 문항만 재실행해 통과한 것처럼 보이게 하지 않는다.
- [PLF-GENERIC-007] 후속 「표로/정리해줘」는 **최근 대화 주제**를 유지하고, 주제가 다르면 교차 오염하지 않는다.
- [PLF-GENERIC-008] `OLLAMA_NUM_PREDICT`를 과도하게 낮추면 답이 중간에 끊길 수 있다 (`reason=length`).
- [PLF-GENERIC-009] status 문구는 `event.type=status`로 분리하고 본문 content에 섞지 않는다.
- [PLF-GENERIC-010] chromadb 버전은 indexer와 pipelines를 동일 pin으로 유지한다.

## 실패 상세 기록

사내 전용 상세 기록은 비공개 위치에 두세요. 이 공개본에는 항목을 추가하지 않거나, 제품·경로를 익명화한 뒤에만 추가하세요.
