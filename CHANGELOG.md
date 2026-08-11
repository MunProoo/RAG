# 업데이트 내역

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/)를 참고했습니다.

> **공개본 안내:** 사내 제품·경로·절차가 담긴 상세 변경 이력은 제거했습니다.  
> 아래는 저장소에 남은 **일반 기능** 요약입니다.

## [Unreleased]

### 공개용 데이터 정리

- 사내 원본 문서·평가 artifact·발표 산출물을 저장소에서 제거하고 `sample_*.md` 데모 문서만 유지
- `golden_questions.json`을 샘플 문서 기준으로 축소
- `PL_FAILURE_LOG.md`를 일반 예방 규칙만 남기도록 정리
- `rag/data/eval/artifacts/*` 는 gitignore (런타임 증거는 커밋하지 않음)

### 파이프라인 기능 (요약)

- Open WebUI Pipelines + Ollama 기반 RAG
- BGE-M3 벡터 검색 + BM25 + RRF, 선택적 리랭크
- 문서 메타데이터(`document_type` 등) 기반 범위 필터
- 후속 질문 문맥화 및 주제 가드
- 골든 질문 평가 · 회귀 테스트 스크립트

과거 비공개 상세 이력이 필요하면 사내 백업에서 확인하세요.
