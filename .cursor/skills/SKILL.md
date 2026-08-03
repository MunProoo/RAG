---
name: rag-pipeline-ops
description: 이 저장소(Open WebUI + Ollama 기반 사내 문서 RAG 파이프라인)의 구조, 인덱싱·재인덱싱 절차, 하이브리드 검색/리랭커 설정, 회귀 테스트·검색 평가 실행법, 자주 겪는 장애 대처법을 안내한다. RAG 파이프라인 수정, 문서 인덱싱, 검색 품질 개선, ChromaDB/BM25/리랭커 관련 작업 시 사용한다.
---

# RAG Pipeline 운영 스킬

## 구조 한눈에 보기

- `rag/pipelines/rag_pipeline.py` — Open WebUI Pipelines가 로드하는 핵심 코드.
  질문 재작성(LLM) → 하이브리드 검색(BGE-M3 벡터 + BM25, RRF 병합) → 리랭커(선택) → 컨텍스트 조립 → 답변 생성(스트리밍).
- `rag/scripts/index_documents.py` — 문서를 ChromaDB에 인덱싱하고 `bm25_index.json`을 생성.
  파일명 기반 메타데이터: `document_type`(protocol/install/user_guide), `product`, `protocol_generation`, `protocol_version`.
- `rag/scripts/test_rag_regression.py` — 모델 없이 실행 가능한 검색/스트림 회귀 테스트.
- `rag/scripts/eval_retrieval.py` + `rag/data/eval/golden_questions.json` — 골든 질문셋 기반 검색 적중률 평가.
- `rag/data/docs` 인덱싱 대상 문서, `rag/data/chroma_db` 벡터 DB(자동 생성), `rag/data/assets` ImageServer(nginx, 8090) 정적 파일.

## 핵심 명령

```bash
# 재인덱싱 (문서/청킹/메타데이터 규칙 변경 후 필수)
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --reset

# 인덱싱 상태 확인
docker compose run --rm indexer python /app/scripts/index_documents.py /app/docs --status

# 회귀 테스트 (Ollama·모델 불필요)
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/test_rag_regression.py

# 검색 평가 (인덱싱 완료 후)
docker compose run --rm --no-deps --entrypoint python indexer /app/scripts/eval_retrieval.py

# 파이프라인 코드 변경 반영
docker compose up -d --force-recreate pipelines
```

## 반드시 지킬 규칙

1. **chromadb 버전은 pin 유지** (`rag/requirements.txt`). `pipelines`와 `indexer`가 같은 DB 디렉터리를 공유하므로 버전이 어긋나면 Rust panic이 난다.
2. **임베딩 모델(`EMBEDDING_MODEL`) 변경 시 `--reset` 재인덱싱 필수.** 벡터 공간이 달라져 기존 인덱스는 무의미해진다.
3. 청킹·메타데이터 규칙(`classify_document`, `extract_document_units`)을 바꾸면 재인덱싱해야 반영된다. BM25 인덱스는 재인덱싱 시 함께 갱신된다.
   - Swagger 문서는 `python scripts/swagger_yaml_to_md.py`로 md를 재생성한 뒤 재인덱싱한다. 변환기는 각 엔드포인트 섹션에 참조 스키마 표를 인라인해(자기완결 청크) API 상세와 스키마가 함께 검색되게 한다. 엔드포인트 섹션 내부에는 `###` 헤딩을 추가하지 말 것(인덱서가 별도 청크로 분리함).
4. 파이프라인은 파일 mtime 기준으로 BM25 인덱스를 캐시하므로, 재인덱싱만 하면 파이프라인 재시작 없이 다음 질문부터 반영된다.
5. 검색 로직 수정 시 `test_rag_regression.py`에 회귀 테스트를 함께 추가하고, `golden_questions.json`에 실패 사례 질문을 누적한다.

## 주요 환경변수 (docker-compose.yml의 pipelines 서비스)

- `TOP_K`, `MIN_SCORE`, `MAX_CHUNKS_PER_SOURCE`, `MAX_CONTEXT_CHARS` — 검색·컨텍스트 예산.
- `RERANK_ENABLED`, `RERANK_MODEL`(기본 `BAAI/bge-reranker-v2-m3`), `RERANK_CANDIDATES` — 크로스 인코더 리랭커. 로드 실패 시 자동으로 RRF 순위로 폴백.
- `USE_QUERY_REWRITE=false` — LLM 질문 재작성을 끄고 원본 질문+규칙 기반 확장만 사용(응답 지연 감소).
- `CONTEXTUALIZE_FOLLOW_UP` — 후속 질문(지시어·초단문)을 이전 대화 기반 독립형 질문으로 변환해 검색. 감지 마커는 `FOLLOW_UP_MARKERS`.
- `REWRITE_MODEL` / `ANSWER_MODEL` — 서로 다르면 Ollama가 모델을 스왑하며 느려질 수 있으니 가급적 동일 모델 사용.

## 트러블슈팅

- **답변이 중간에 끊김**: pipelines 로그의 `[RAG] Ollama stream completed`에서 `reason=length` 확인 → `OLLAMA_NUM_PREDICT`/`OLLAMA_NUM_CTX` 상향.
- **엉뚱한 문서가 섞임**: 질문에 문서 종류 키워드(프로토콜/설치/가이드)가 있으면 검색 전에 메타데이터 필터가 걸린다. 필터 규칙은 `DOCUMENT_TYPE_TERMS`/`PRODUCT_TERMS`에 있고, 문서 쪽 분류는 `classify_document`가 담당한다. 둘이 어긋나면 결과가 0개가 되니 함께 수정한다.
- **ChromaDB 로딩 오류**: `rag/data/chroma_db` 삭제 후 `--reset` 재인덱싱. 두 컨테이너의 chromadb 버전 일치 확인.
- **첫 질문이 매우 느림**: 임베딩·리랭커 모델 최초 다운로드/로딩 때문. 이후에는 프로세스 캐시로 빨라진다.
