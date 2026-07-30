# Alpeta Server Web API (Swagger 2.0 → Markdown)

벡터 검색·RAG용으로 `swagger_kr.yaml`을 마크다운으로 변환한 문서입니다.

- **title**: Server Web Ubio Alpeta API
- **version**: 1.0.0
- **description**: Server Web Ubio Alpeta API document
- **Base URL**: `http://15.15.15.3:9004/v1`

## API 태그 목록

| 태그 | 설명 |
|------|------|
| `licenses` |  |
| `sessions` | 세션 관리 |
| `visitor` | 방문객 |
| `options` | 옵션 관리 |
| `users` | 사용자 관리 |
| `blacklists` | 블랙리스트 관리 |
| `privileges` | 권한 관리 |
| `groups` | 그룹 관리 |
| `positions` | 직급 관리 |
| `notices` | 공지사항 관리 |
| `web notice` | Web 공지사항 관리 |
| `messages` | 사용자 메시지 관리 |
| `terminals` | 단말기 관리 |
| `terminalUsers` | 단말기 사용자 관리 |
| `terminalAdmins` | 단말기 관리자 관리 |
| `access group` | 출입그룹 관리 |
| `timezones` | 타임존 관리 |
| `antiPassback` | 안티패스백 관리 |
| `wiegand` | wiegand 관리 |
| `map` | 위치형상화 관리 |
| `logs` | 작업 로그, 이벤트 로그 관리 |
| `authLogs` | 인증 로그 관리 |
| `tna` | 근태 관리 |
| `meal` | 식수 관리 |
| `elevator` | 엘리베이터 관리 |

## POST `/v1/ExdbLogin`

- **요약**: ExDB(Get Table List)
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | ExdbLoginAccountInfo | ExDB(Get Table List) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/accessAreas`

- **요약**: 출입구역 목록 조회
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/accessAreas`

- **요약**: 출입구역 등록
- **설명**: 출입구역 등록
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | AccessAreaPost | 등록할 출입구역과 단말기 리스트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## PUT `/v1/accessAreas/{id}`

- **요약**: 출입구역 저장
- **설명**: 출입구역 저장
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 저장할 출입구역 아이디 |
| `body` | body | 예 | AccessAreaPost | 저장할 출입구역 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## DELETE `/v1/accessAreas/{id}`

- **요약**: 출입그룹 삭제
- **설명**: 출입구역 삭제
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 출입구역 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/accessAreas/{id}/terminals`

- **요약**: 출입구역내 단말 목록 조회
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 출입구역 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/accessGroups`

- **요약**: 출입그룹 목록 조회
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `areas` | query | 아니오 |  | 출입구역 전체 리스트 포함 |
| `joinInfo` | query | 아니오 |  | 출입 그룹과 구역 조인 리스트 포함 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `AccessGroupList` |
| `405` | Invalid input |  |

---

## POST `/v1/accessGroups`

- **요약**: 출입 그룹 등록
- **설명**: 새로운 출입그룹을 등록한다
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | AccessGroup | 추가할 출입그룹 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## POST `/v1/accessGroups/terminal`

- **요약**: 출입그룹 정보 단말로 전송
- **설명**: 선택된 단말기 출입그룹 단말로 전송
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | array<integer> | 전송할 단말기 리스트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/accessGroups/{id}`

- **요약**: 출입그룹 조회
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 출입그룹 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## PUT `/v1/accessGroups/{id}`

- **요약**: 출입 그룹 수정
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 출입그룹 아이디 |
| `body` | body | 예 | AccessGroup | 수정할 출입그룹 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/accessGroups/{id}`

- **요약**: 출입그룹 삭제
- **설명**: 출입그룹 삭제 시 연관된 단말기, 사용자 삭제
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 컨트롤러 아이디 |
| `deleteCategory` | query | 예 |  | 삭제 유형 0:출입그룹, 1:단말기, 2:사용자 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/accessGroups/{id}/accessAreas`

- **요약**: 출입그룹에서 출입구역 삭제
- **설명**: 출입그룹에서 출입구역을 삭제합니다
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 출입그룹 아이디 |
| `body` | body | 예 | AccessAreaIDs | 수정할 출입그룹 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/accessGroups/{id}/allUsers`

- **요약**: 출입그룹 사용자 조회
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 출입그룹 아이디 |
| `offset` | query | 예 |  | 조회 시작 위치 |
| `limit` | query | 예 |  | 조회 카운트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## PUT `/v1/accessGroups/{id}/users`

- **요약**: 출입그룹 사용자 등록 혹은 삭제
- **태그**: access group
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자를 등록 혹은 삭제 출입그룹 아이디 |
| `body` | body | 예 | AccessGroupUserID | Source : 사용자 등록시 0, 삭제시 출입그룹 아이디, Target : 사용자 등록시 출입그룹 아이디, 사용자 삭제시 0 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/antiPassback`

- **요약**: anti-passback 목록 조회
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `full` | query | 아니오 |  | Determin whether full information |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalAPBInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/antiPassback`

- **요약**: anti-passback 생성
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | array<TerminalAPBInfo> | anti-passback 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/antiPassback`

- **요약**: 단말기 anti-passback 초기화
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `terminalID` | query | 예 |  | anti-passback 정보를 초기화 할 단말기 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/antiPassback/areas`

- **요약**: 영역 목록 조회
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/antiPassback/areas`

- **요약**: 영역 생성
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | APBAreaInfo | 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/antiPassback/areas/{id}`

- **요약**: 영역 정보 조회
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 영역 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/antiPassback/areas/{id}`

- **요약**: 영역 정보 수정
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 영역 ID |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/antiPassback/areas/{id}`

- **요약**: 영역 정보 삭제
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 영역 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/antiPassback/areas/{id}/details`

- **요약**: 영역 상세 정보 조회
- **태그**: antiPassback
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 영역 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaDetailInfo` |
| `405` | Invalid input |  |

---

## GET `/v1/authLogs`

- **요약**: 인증로그 목록 조회
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 예 |  | 시작일. format = ex.2018-05-10 |
| `endTime` | query | 예 |  | 종료일. format = ex.2018-05-10 |
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |
| `offset` | query | 예 |  | 조회 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |
| `fields` | query | 아니오 |  | 가져올 항목 명칭 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/authLogs/terminal/{id}/count`

- **요약**: 단말기 인증 로그 카운트
- **설명**: 단말기에 저장된 인증 로그 카운트 가져오기
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 로그 카운트 가져올 단말기 아이디 |
| `searchCategory` | query | 예 |  | 조회 유형 not:미전송 로그 카운트, all:단말기에 기록된 모든 로그 카운트, period:조회 기간 범위 모든 로그 카운트 |
| `startDate` | query | 아니오 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endDate` | query | 아니오 |  | 조회 마지막 날짜 (ex.2018-05-11) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | ‘log count’ |  |
| `405` | Invalid input |  |

---

## GET `/v1/authLogs/terminal/{id}/data`

- **요약**: 단말기 인증 로그 가져오기
- **설명**: 단말기로 부터 인증 로그 데이터 가져오기
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 인증 로그 가져올 단말기 아이디 |
| `searchCategory` | query | 예 |  | 조회 유형 not:미전송 로그 데이터, all:단말기에 기록된 모든 로그 데이터, period:조회 기간 범위 모든 로그 데이터 |
| `startDate` | query | 아니오 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endDate` | query | 아니오 |  | 조회 마지막 날짜 (ex.2018-05-11) |
| `attachPicture` | query | 아니오 |  | 인증 사진 첨부 여부 선택 |
| `offset` | query | 아니오 |  | 조회 시작 위치 |
| `limit` | query | 아니오 |  | 조회 할 목록 수 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/authLogs/{logIndex}`

- **요약**: 인증로그 상세 정보
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `logIndex` | path | 예 |  | 조회 할 로그의 Index key |
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |
| `offset` | query | 예 |  | Index key 기준 조회 할 로그. -1: 이전 로그, 0현재 로그, 1: 다음 로그 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/authLogs/{logIndex}/logImage`

- **요약**: 인증로그 이미지 가져오기
- **설명**: 단말기에 저장된 인증 로그 이미지 가져오기
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `logIndex` | path | 예 |  | 로그 이미지를 가져올 index Key |
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |
| `offset` | query | 예 |  | Index key 기준 조회 할 로그. -1: 이전 로그, 0: 현재 로그, 1: 다음 로그 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/authLogsStatistics/month`

- **요약**: 월별 인증로그 통계
- **설명**: 월별 인증로그 통계 정보 얻기
- **태그**: authLogs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `year` | query | 예 |  | 조회 년도 (ex.2019) |
| `month` | query | 예 |  | 조회 월 (ex.04) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/blacklists`

- **요약**: 블랙리스트 목록 조회
- **설명**: 등록된 이용자 및 방문자를 블랙리스트에 등록하는 블랙리스트 관리는 특정 사용자의 접근을 제한해야 할 때 사용합니다.
- **태그**: blacklists
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회할 키워드 |
| `offset` | query | 예 |  | 조회할 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserListResult` |
| `405` | Invalid input |  |

---

## GET `/v1/blacklists/{id}`

- **요약**: 블랙리스트 정보 조회
- **태그**: blacklists
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 블랙리스트 아이디 |
| `picture` | query | 예 |  | 사진 첨부 유무 결정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserInfoResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/blacklists/{id}`

- **요약**: 블랙리스트 삭제
- **태그**: blacklists
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 블랙리스트 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/blacklists/{id}/apply`

- **요약**: Blacklist designation
- **설명**: Designate the user as blacklisted.
- **태그**: blacklists
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | Specify blacklist ID to remove infomation |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/blacklists/{id}/release`

- **요약**: 블랙리스트 해제
- **설명**: 블랙리스트 사용자를 일반 사용자로 전환합니다
- **태그**: blacklists
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 해제할 블랙리스트 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/elevators`

- **요약**: 출입층 관리
- **설명**: 출입층 관리
- **태그**: elevator
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/elevators`

- **요약**: 출입층 관리
- **설명**: 출입층 관리
- **태그**: elevator
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | ElevatorSetInfo | 출입증 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/elevators/{elevatorID}`

- **요약**: 출입층 관리
- **설명**: 출입층 관리
- **태그**: elevator
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `elevatorID` | path | 예 |  | elevatorID |
| `body` | body | 예 | ElevatorSetInfo | Acces Floor |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/elevators/{elevatorID}`

- **요약**: 출입층 관리
- **설명**: 출입층 관리
- **태그**: elevator
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `elevatorID` | path | 예 |  | elevatorID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/groups`

- **요약**: 그룹 목록 조회
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | query | 예 |  | 그룹 ID (하위 그룹 포함, 0=전체 그룹) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GroupListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/groups`

- **요약**: 그룹 등록
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | GroupInfoReq | 그룹 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GroupResult` |
| `405` | Invalid input |  |

---

## GET `/v1/groups/user/count`

- **요약**: 그룹에 소속된 사용자 수
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserCountInGroupResult` |
| `405` | Invalid input |  |

---

## GET `/v1/groups/{id}`

- **요약**: 그룹 정보 조회
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 그룹 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GroupListResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/groups/{id}`

- **요약**: 그룹 정보 수정
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 그룹 ID |
| `body` | body | 예 | GroupInfoReq | 수정 할 그룹 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/groups/{id}`

- **요약**: 그룹 정보 삭제 (하위 그룹 포함)
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 그룹 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/groups/{id}/terminals`

- **요약**: 단말기 그룹 정보 수정
- **설명**: 해당 그룹으로 수정 할 단말기 목록
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 그룹 ID |
| `body` | body | 예 | TerminalIDList | 해당 그룹으로 수정 할 단말기 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/groups/{id}/users`

- **요약**: 사용자 그룹 정보 수정
- **설명**: 해당 그룹으로 수정할 사용자 목록
- **태그**: groups
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 그룹 ID |
| `body` | body | 예 | UserIDList | 해당 그룹으로 수정 할 사용자 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/license`

- **요약**: 서버에 등록된 라이선스 정보 요청
- **태그**: licenses
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResultLicenseInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/license/activate`

- **요약**: 라이선스 활성화 요청
- **태그**: licenses
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | ActivationInfo | 라이선스 활성화 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/license/clientKey`

- **요약**: 서버에서 클라이언트 키 정보 요청
- **설명**: 서버에 라이선스를 발급하기 위한 클라이언트 키를 요청합니다.
- **태그**: licenses
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResultClientKeyInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/login`

- **요약**: 서버에 로그인 요청
- **태그**: sessions
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | Login | 로그인 요청 객체 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `LoginResult` |
| `405` | Invalid input |  |

---

## GET `/v1/logout`

- **요약**: 서버에 로그아웃 요청
- **태그**: sessions
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/logs/audit_log`

- **요약**: 작업 로그 목록 조회
- **태그**: logs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 예 |  | 조회 시작 시간 포맷 (ex.2018-05-10) |
| `endTime` | query | 예 |  | 조회 종료 시간 포맷 (ex.2018-05-11) |
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회 키워드 |
| `offset` | query | 예 |  | 조회 시작 위치 |
| `limit` | query | 예 |  | 조회 카운트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## DELETE `/v1/logs/audit_log`

- **요약**: 작업 로그 삭제
- **설명**: 해당 조회 조건에 맞는 로그를 삭제한다.
- **태그**: logs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 아니오 |  | 조회 시작 날짜 (ex.2018-05-10 04:27:06) |
| `endTime` | query | 아니오 |  | 조회 마지막 날짜 (ex.2018-05-11 15:13:12) |
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회 키워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/logs/audit_log/{id}/terminal`

- **요약**: 단말기 작업 로그 가져오기
- **설명**: 단말기로 부터 작업 로그를 가져온다. 실질적인 로그는 서버에서 저장되며 카운트만 반환됨
- **태그**: logs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 작업로그 가져올 단말기 아이디 |
| `all` | query | 예 |  | 모든 로그 가져올지 선택 true: 모든 로그 가져오기, false: 서버로 전송하지 않은 로그만 가져오기 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/logs/event_log`

- **요약**: 단말기 이벤트 로그 목록 조회
- **태그**: logs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 예 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endTime` | query | 예 |  | 조회 마지막 날짜 (ex.2018-05-11) |
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회 키워드 |
| `offset` | query | 예 |  | 조회 시작 위치 |
| `limit` | query | 예 |  | 조회 카운트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## DELETE `/v1/logs/event_log`

- **요약**: 단말기 이벤트 로그 삭제
- **설명**: 해당 조회 조건에 맞는 로그를 삭제한다.
- **태그**: logs
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 아니오 |  | 삭제 시작 날짜 (ex.2018-05-10 04:27:06) |
| `endTime` | query | 아니오 |  | 삭제 마지막 날짜 (ex.2018-05-11 15:13:12) |
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회 키워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/map`

- **요약**: 전체 영역 이미지 데이터 가져오기
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ImageInfoResult` |
| `405` | Invalid input |  |

---

## POST `/v1/map`

- **요약**: 전체 영역 이미지 설정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | array<MapAreaInfo> | 이미지 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/map/areas`

- **요약**: 위치 영역 조회
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/map/areas`

- **요약**: 위치 영역 생성
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MapAreaInfo | 도면 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/map/areas/position`

- **요약**: 위치 영역 정보 일괄 수정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/map/areas/terminals`

- **요약**: 단말기 전체 목록 가져오기
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaInfo` |
| `405` | Invalid input |  |

---

## GET `/v1/map/areas/{code}`

- **요약**: 위치 영역 정보 조회
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 조회 할 영역 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/map/areas/{code}`

- **요약**: 위치 영역 정보 수정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/map/areas/{code}`

- **요약**: 위치 영역 정보 삭제
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 삭제 할 영역 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/map/areas/{code}/image`

- **요약**: 위치 영역 이미지 수정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/map/areas/{code}/position`

- **요약**: 영역 위치 수정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/map/areas/{code}/terminals`

- **요약**: 영역 내 단말기 목록 가져오기
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/map/areas/{code}/terminals`

- **요약**: 영역 단말기 추가
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/map/areas/{code}/terminals/{id}`

- **요약**: 영역 단말기 정보 조회
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 영역 코드 |
| `id` | path | 예 |  | 단말기 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `APBAreaInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/map/areas/{code}/terminals/{id}`

- **요약**: 영역 단말기 정보 수정
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 수정 할 영역 코드 |
| `id` | path | 예 |  | 단말기 ID |
| `body` | body | 예 | APBAreaInfo | 수정 할 영역 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/map/areas/{code}/terminals/{id}`

- **요약**: 영역 단말기 정보 삭제
- **태그**: map
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | 삭제 할 영역 코드 |
| `id` | path | 예 |  | 단말기 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/mealData`

- **요약**: 끼니 목록 가져오기
- **설명**: 등록된 모든 끼니 정보를 가져온다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealDataListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/mealData`

- **요약**: 끼니 정보 등록
- **설명**: 끼니 정보 등록한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MealDataInfo | 식수 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/mealData/{meadDataCode}`

- **요약**: 끼니 수정
- **설명**: 끼니 정보를 수정한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `meadDataCode` | path | 예 |  | 변경할 끼니 코드 |
| `body` | body | 예 | MealDataInfo | 식수 끼니 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/mealData/{meadDataCode}`

- **요약**: 끼니 정보 삭제
- **설명**: 끼니 데이터를 삭제 한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `meadDataCode` | path | 예 |  | 끼니 코드 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/mealProcess`

- **요약**: 식수처리 작업관리자 등록
- **설명**: 식수처리를 작업관리자에 등록한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MealProcessReq | 식수처리 요청 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealProcessResult` |
| `405` | Invalid input |  |

---

## GET `/v1/mealResults`

- **요약**: 식수 결과 가져오기
- **설명**: 식수 결과 리스트를 가져온다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `StartAt` | query | 예 |  | 식수결과조회 시작일 |
| `EndAt` | query | 예 |  | 식수결과조회 종료일 |
| `offset` | query | 예 |  | 조회할 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealResultListResult` |
| `405` | Invalid input |  |

---

## GET `/v1/mealStatistics`

- **요약**: 식수 기록 통계
- **설명**: 식수 통계를 가져온다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `Year` | query | 예 |  | 조회 년도 (ex.2019) |
| `Month` | query | 예 |  | 조회 월 (ex.04) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealStatisticsResult` |
| `405` | Invalid input |  |

---

## GET `/v1/mealStatistics/month/totalStatus`

- **요약**: 식수결과 종합 현황
- **설명**: 월단위 식수결과의 총합 현황을 가져온다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `Year` | query | 예 |  | 조회 년도 (ex.2019) |
| `Month` | query | 예 |  | 조회 월 (ex.04) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealTotalStatusResult` |
| `405` | Invalid input |  |

---

## GET `/v1/meals`

- **요약**: 식수 목록 가져오기
- **설명**: 식수 리스트를 가져온다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MealListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/meals`

- **요약**: 식수 코드 등록
- **설명**: 끼니를 조합한 식수 정보를 등록한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MealInfo | 식수 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/meals/{mealcode}`

- **요약**: 식수 정보 수정
- **설명**: 식수정보를 변경 한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `mealcode` | path | 예 |  | 변경할 식수 코드 |
| `body` | body | 예 | MealInfo | 식수 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/meals/{mealcode}`

- **요약**: 식수 정보 삭제
- **설명**: 식수 데이터를 삭제 한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `mealcode` | path | 예 |  | 식수 코드 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/meals/{mealcode}/userMealCode`

- **요약**: 사용자에 설정된 식수 코드 변경
- **설명**: 사용자에 설정된 식수코드를 변경한다.
- **태그**: meal
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `mealcode` | path | 예 |  | 식수코드 |
| `body` | body | 예 | array<integer> | 수정할 사용자 ID 리스트 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/menuGroups`

- **요약**: 사용자 메뉴 폴더 정보 등록
- **설명**: 사용자 메뉴 폴더 정보를 등록
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MenuGroup | 메뉴 폴더 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/menuGroups`

- **요약**: 사용자 메뉴 폴더 정보 변경
- **설명**: 사용자 메뉴 폴더 관련 정보를 변경
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MenuGroupsInfo | 메뉴 폴더 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/menuGroups/{id}`

- **요약**: 지정된 관리자 메뉴 폴더 정보 변경
- **설명**: 지정된 관리자 메뉴 폴더 정보 변경
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 변경할 그룹 아이디 |
| `body` | body | 예 | MenuGroupsInfo | 메뉴 그룹 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/menuGroups/{id}`

- **요약**: 지정된 메뉴 그룹 정보 삭제
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 메뉴 그룹 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## POST `/v1/menuUsers`

- **요약**: 사용자 메뉴 정보 등록
- **설명**: 사용자 메뉴 정보를 등록
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MenuUser | 사용자 메뉴 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/menuUsers`

- **요약**: 사용자 메뉴 정보 변경
- **설명**: 사용자 메뉴 정보를 변경
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MenuUsersInfo | 사용자 메뉴 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/menuUsers/{id}`

- **요약**: 지정된 사용자 메뉴 정보 변경
- **설명**: 사용자 메뉴 정보를 변경
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 변경을 위해서 지정된 menuID |
| `body` | body | 예 | MenuUsersInfo | 사용자 메뉴 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/menuUsers/{id}`

- **요약**: 지정된 사용자 메뉴 정보 삭제
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 메뉴 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/menus`

- **요약**: 사용자 로그인 하는 경우, 메뉴관련 전체 데이터 가져오기
- **태그**: menus
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MenusInfo` |
| `405` | Invalid input |  |

---

## GET `/v1/messages`

- **요약**: 메시지 목록 조회
- **태그**: messages
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserMessageListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/messages`

- **요약**: 메시지 등록
- **태그**: messages
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | MessageInfo | 메시지 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserMessageResult` |
| `405` | Invalid input |  |

---

## GET `/v1/messages/{id}`

- **요약**: 메시지 정보 조회
- **태그**: messages
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 메시지 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserMessageResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/messages/{id}`

- **요약**: 메시지 정보 수정
- **태그**: messages
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 메시지 ID |
| `body` | body | 예 | MessageInfo | 수정 할 메시지 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/messages/{id}`

- **요약**: 메시지 정보 삭제
- **태그**: messages
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 메시지 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/notices`

- **요약**: 공지사항 목록 조회
- **설명**: ‘‘
- **태그**: notices
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation/ | `NoticeListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/notices`

- **요약**: 공지사항 정보 등록
- **설명**: ‘‘
- **태그**: notices
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | NoticeInfo | 공지사항 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `NoticeResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/notices/{id}`

- **요약**: 공지사항 정보 수정
- **설명**: ‘‘
- **태그**: notices
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 공지사항 ID |
| `body` | body | 예 | NoticeInfo | 수정 할 메시지 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `NoticeResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/auth`

- **요약**: 인증설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/auth`

- **요약**: 인증 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionAuthList | 인증 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/dashboard`

- **요약**: 대시보드 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/dashboard`

- **요약**: 대시보드 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionDashboardInfo | 대시보드 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/ddns`

- **요약**: DDNS 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/ddns`

- **요약**: DDNS 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionDDNSList | DDNS 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/elevator`

- **요약**: 엘리베이터 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/elevator`

- **요약**: 엘리베이터 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionElevatorInfo | 엘리베이터 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/log`

- **요약**: 로그 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/log`

- **요약**: 로그 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionLogList | 로그 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/mail`

- **요약**: 메일 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/mail`

- **요약**: 메일 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionMailList | 메일 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/system`

- **요약**: 일반 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/system`

- **요약**: 일반 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionSystemList | 일반 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/terminal`

- **요약**: 긴급 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/terminal`

- **요약**: 긴급 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionTerminalList | 긴급 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/tna`

- **요약**: TNA 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/tna`

- **요약**: TNA 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionTNAList | TNA 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/options/user`

- **요약**: 일반 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/options/user`

- **요약**: 사용자 설정
- **태그**: options
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | OptionUserList | 사용자 설정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/positions`

- **요약**: 직급 목록 조회
- **태그**: positions
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `PositionsResult` |
| `405` | Invalid input |  |

---

## POST `/v1/positions`

- **요약**: 직급 정보 등록
- **설명**: ‘‘
- **태그**: positions
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | PositionInfo | 직급 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/positions/{id}`

- **요약**: 직급 정보 조회
- **설명**: ‘‘
- **태그**: positions
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 직급 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `PositionInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/positions/{id}`

- **요약**: 직급 정보 수정
- **설명**: ‘‘
- **태그**: positions
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 직급 ID |
| `body` | body | 예 | PositionInfo | 직급 정보 수정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/positions/{id}`

- **요약**: 직급 정보 삭제
- **설명**: ‘‘
- **태그**: positions
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 직급 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/privileges`

- **요약**: 권한 목록 조회
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |
| `offset` | query | 예 |  | 조회 할 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |
| `full` | query | 아니오 |  | 전체 정보 여부 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `PrivilegeInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/privileges`

- **요약**: 권한 등록
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | PrivilegeInfo | 권한 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `Result` |
| `405` | Invalid input |  |

---

## GET `/v1/privileges/{id}`

- **요약**: 권한 정보 조회
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 권한 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `PrivilegeInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/privileges/{id}`

- **요약**: 권한 정보 수정
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 권한 ID |
| `body` | body | 예 | PrivilegeInfo | 수정 할 권한 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `Result` |
| `405` | Invalid input |  |

---

## DELETE `/v1/privileges/{id}`

- **요약**: 권한 정보 삭제
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 권한 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `Result` |
| `405` | Invalid input |  |

---

## GET `/v1/privileges/{id}/groups`

- **요약**: 권한 그룹 목록 조회.
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalTinyList` |
| `405` | Invalid input |  |

---

## POST `/v1/privileges/{id}/groups`

- **요약**: 권한 그룹 목록 추가
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | GroupIDList | 그룹 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/privileges/{id}/groups`

- **요약**: 권한 그룹 목록 삭제
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | GroupIDList | 단말기 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/privileges/{id}/terminals`

- **요약**: 권한 단말기 목록 조회.
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalTinyList` |
| `405` | Invalid input |  |

---

## POST `/v1/privileges/{id}/terminals`

- **요약**: 권한 단말기 목록 추가
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | TerminalIDList | 단말기 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/privileges/{id}/terminals`

- **요약**: 권한 단말기 목록 삭제
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | TerminalIDList | 단말기 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/privileges/{id}/users`

- **요약**: 권한 사용자 목록 조회
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserTinyList` |
| `405` | Invalid input |  |

---

## POST `/v1/privileges/{id}/users`

- **요약**: 권한 사용자 목록 추가
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | UserIDList | 사용자 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/privileges/{id}/users`

- **요약**: 권한 사용자 목록 삭제
- **태그**: privileges
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 권한 ID |
| `body` | body | 예 | UserIDList | 삭제 할 사용자 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminalAdmins`

- **요약**: 단말기 관리자 체크
- **설명**: 특정 단말기에 관리 권한이 있는지 검사한다.
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `userID` | query | 예 |  | 관리자 아이디 |
| `terminalID` | query | 예 |  | 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## POST `/v1/terminalAdmins`

- **요약**: 단말기 관리자 지정
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TerminalAdmins | 적용할 단말기 관리자 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminalAdmins`

- **요약**: 단말기 관리자 삭제
- **설명**: 단말기 관리자로 설정된 사용자를 해제합니다
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TerminalAdmins | 삭제할 단말기 관리자 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminalAdmins/{id}/admin`

- **요약**: 관리 단말기 목록 조회
- **설명**: 특정 관리자가 관리하고 있는 단말기 목록을 조회합니다
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 관리자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalAdmins` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminalAdmins/{id}/admin`

- **요약**: 관리 단말기 목록 삭제
- **설명**: 특정 관리자가 관리되고 있는 단말기 목록을 삭제합니다
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 관리자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminalAdmins/{id}/terminals`

- **요약**: 단말기 관리자 목록 조회
- **설명**: 특정 단말기의 관리자 목록을 조회합니다
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalAdmins` |
| `405` | Invalid input |  |

---

## POST `/v1/terminalAdmins/{id}/terminals`

- **요약**: 단말기 관리자 지정
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 관리자 아이디 |
| `body` | body | 예 | TerminalAdminSave | 단말기 관리자 저장 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminalAdmins/{id}/terminals`

- **요약**: 특정 단말기의 관리자 목록을 삭제합니다.
- **설명**: 특정 단말기의 관리자 목록을 삭제합니다.
- **태그**: terminalAdmins
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 관리자를 삭제할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminalUsers/{id}/count`

- **요약**: 단말기 사용자 수 조회
- **태그**: terminalUsers
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자 수를 가져 올 단말기 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalUserCount` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminalUsers/{id}/data`

- **요약**: 사용자 정보 가져오기
- **태그**: terminalUsers
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자 정보를 가져 올 단말기 ID |
| `body` | body | 예 | UserIDs | 정보를 가져 올 사용자 목록 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminalUsers/{id}/info`

- **요약**: 단말기 사용자 목록 조회
- **태그**: terminalUsers
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자 목록을 가져올 단말기 ID |
| `offset` | query | 아니오 |  | 조회 시작 위치 |
| `limit` | query | 아니오 |  | 조회 할 목록 수 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalUserInfo` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals`

- **요약**: 단말기 목록 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회할 키워드 |
| `offset` | query | 아니오 |  | 조회할 시작 위치 |
| `limit` | query | 아니오 |  | 조회 할 목록 수 |
| `fields` | query | 아니오 |  | 가져올 항목 명칭 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/terminals`

- **요약**: 단말기 추가
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | CreateTerminal | 추가할 단말기 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/accessgroupdownload`

- **요약**: 출입그룹 정보 전송
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | array<integer> | 출입그룹 정보를 받을 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/notice`

- **요약**: 공지사항
- **설명**: 설정 기간동안 단말기에 공지사항을 보여준다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | PublicNotice | 적용할 공지사항 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}`

- **요약**: 단말기 정보 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |
| `apbflag` | query | 예 |  | 단말기에 해당하는 안티패스백 정보 포함 |
| `imageflag` | query | 아니오 |  | 단말기 모델에 해당하는 이미지 정보 포함 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}`

- **요약**: 단말기 수정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 단말기 아이디 |
| `body` | body | 예 | TerminalInfo | 수정할 단말기 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminals/{id}`

- **요약**: 단말기 삭제
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/control/door`

- **요약**: 단말기 출입문 제어
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 아이디 |
| `body` | body | 예 | TerminalDoorControl | 단말기 출입문 제어 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/control/emergency`

- **요약**: 단말기 긴급상황 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 아이디 |
| `body` | body | 예 | TerminalSetEmergency | 제어 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/control/lockdown`

- **요약**: 단말기 락 제어
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 아이디 |
| `body` | body | 예 | TerminalLockControl | 단말기 락 제어 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/alarm`

- **요약**: 알람 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalAlarmInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/alarm`

- **요약**: 알람 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | AlarmOptionList | 설정할 알람 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/basic`

- **요약**: 기본 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalBasicOption` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/basic`

- **요약**: 기본 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalBasicOption | 설정할 기본 옵션 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/display`

- **요약**: 단말기 디스플레이 설정 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalSystemOption` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/entire`

- **요약**: 단말기 모든 옵션 조회(NAC-5000 / T3 / T5)
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalBasicOption` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/entire`

- **요약**: 단말기 모든 옵션 설정(NAC-5000 / T3 / T5)
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalBasicOption | 설정할 기본 옵션 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/holiday`

- **요약**: 공휴일 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalHolidayOption` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/holiday`

- **요약**: 공휴일 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalHolidayOption | 설정할 공휴일 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/holiday/timezone`

- **요약**: 선택된 공휴일 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 공휴일 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneHolidayToTerminalOptResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/lock`

- **요약**: 락 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation In order, 'Sun, Mon, Tue, Wed, Thu, Fri, Sat, Hol1, Hol2, Hol3' | `TerminalLockOptionResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/lock`

- **요약**: 락 스케줄 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalLockOption | 설정할 락 스케줄 정보 Sun, Mon, Tue, Wed, Thu, Fri, Sat, Hol1, Hol2, Hol3 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/meal`

- **요약**: 식수 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalMealInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/meal`

- **요약**: 식수 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalMealOption | 설정할 식수 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/network`

- **요약**: 네트워크 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalNetworkOption` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/option/network`

- **요약**: 네트워크 옵션 설정
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 설정할 단말기 아이디 |
| `body` | body | 예 | TerminalNetworkOption | 설정할 네트워크 옵션 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/setting`

- **요약**: 단말기 설정 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalSystemOption` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/system`

- **요약**: 시스템 옵션 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalSystemOption` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/option/voip`

- **요약**: Voip 설정 조회
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalVoipOption` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/readerNames`

- **요약**: 리더기, 위겐드 이름 가져오기
- **설명**: MCP-040의 리더기 이름과 위겐드 이름 정보를 가져온다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 정보를 가져올 단말기의 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `MCP_ReaderInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/readerNames`

- **요약**: 리더기, 위겐드 이름 추가
- **설명**: MCP-040의 리더기, 위겐드의 이름을 추가한다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 ID |
| `body` | body | 예 | MCP_ReaderInfo | 추가할 리더기, 위겐드 이름 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## PUT `/v1/terminals/{id}/readerNames`

- **요약**: 리더기, 위겐드 이름 수정
- **설명**: MCP-040의 리더기, 위겐드의 이름을 수정한다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 ID |
| `body` | body | 예 | MCP_ReaderInfo | 수정할 리더기, 위겐드 이름 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/scan/card`

- **요약**: 카드정보 읽기
- **설명**: 단말기로 부터 카드 정보를 읽어온다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 카드 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `CardInfo` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/scan/face`

- **요약**: 얼굴 이미지 캡쳐
- **설명**: 단말기로 부터 얼굴 이미지를 캡쳐한다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 얼굴 단말기 아이디 |
| `type` | query | 예 |  | 단말로 요청 타입 (0:시작 1:취소) 고정값 0 |
| `regcount` | query | 예 |  | 얼굴 등록 갯수 (3얼굴,  5얼굴) |
| `regtimeout` | query | 예 |  | 얼굴 등록 타임아웃 |
| `UserID` | query | 예 |  | 얼굴 등록 사용자 ID |
| `Index` | query | 예 |  | 등록할 얼굴 순번(1 ~ 2) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GetFaceInfoFromTerminal` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/scan/facewt`

- **요약**: 얼굴 이미지 캡쳐 (faceWt)
- **설명**: 단말기로 부터 얼굴 워크스루 이미지를 캡쳐한다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 워크스루형 단말기 아이디 |
| `capture_timeout` | query | 예 |  | 얼굴 워크스루 등록 타임아웃 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GetFaceWtInfoFromTerminal` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/scan/fp_image`

- **요약**: 지문 이미지 캡쳐
- **설명**: 단말기로 부터 지문 이미지를 캡쳐한다.
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 지문 단말기 아이디 |
| `regcount` | query | 예 |  | 고정값 1 |
| `regtimeout` | query | 예 |  | 지문 등록 타임아웃 설정 |
| `UserID` | query | 예 |  | 등록 사용자 ID |
| `FingerID` | query | 예 |  | 등록 지문 위치정보 (0~ 9) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `GetFpImageFromTerminal` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminals/{id}/users`

- **요약**: 단말기 사용자 전체 삭제
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 전제 사용자를 삭제 할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/wiegand/in`

- **요약**: Wiegand In 가져오기
- **설명**: 단말기로 부터 Wiegand In 정보를 가져온다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  |  |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandIn` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/wiegand/in`

- **요약**: Wiegand In 설정
- **설명**: 단말로 Wiegand In 정보를 설정한다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 아이디 |
| `body` | body | 예 | WiegandIn | 적용할 Wiegand In 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/terminals/{id}/wiegand/out`

- **요약**: Wiegand Out 가져오기
- **설명**: 단말기로 부터 Wiegand Out 정보를 가져온다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 단말기 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandOut` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{id}/wiegand/out`

- **요약**: Wiegand Out 설정
- **설명**: 단말로 Wiegand Out 정보를 설정한다
- **태그**: terminals
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 적용할 단말기 아이디 |
| `body` | body | 예 | WiegandOut | 적용할 위겐드 아웃 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## POST `/v1/terminals/{terminalID}/users/{userID}`

- **요약**: 단말기에 사용자 다운로드
- **태그**: terminalUsers
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `terminalID` | path | 예 |  | 다운로드 할 단말기 ID |
| `userID` | path | 예 |  | 다운로드 할 사용자 ID |
| `body` | body | 예 | DownloadInfoData |  |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/terminals/{terminalID}/users/{userID}`

- **요약**: 단말기에서 사용자 삭제
- **태그**: terminalUsers
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `terminalID` | path | 예 |  | 사용자를 삭제 할 단말기 ID |
| `userID` | path | 예 |  | 삭제 할 사용자 ID |
| `body` | body | 예 | DownloadInfoData |  |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones`

- **요약**: 타임존 목록 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `full` | query | 아니오 |  | 전체 구조 여부 (true=전체, false=요약) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/timezones`

- **요약**: 타임존 생성
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TimezoneInfo | 타임존 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones/holidays`

- **요약**: 공휴일 목록 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneHolidayInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/timezones/holidays`

- **요약**: 공휴일 생성
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TimezoneHolidayInfo | 공휴일 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones/holidays/{id}`

- **요약**: 공휴일 정보 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 공휴일 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneHolidayInfo` |
| `405` | Invalid input |  |

---

## POST `/v1/timezones/holidays/{id}`

- **요약**: 공휴일 정보 수정
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 공휴일 ID |
| `body` | body | 예 | TimezoneHolidayInfo | 수정 할 공휴일 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/timezones/holidays/{id}`

- **요약**: 공휴일 정보 삭제
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 공휴일 정보 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones/timelines`

- **요약**: 타임라인 목록 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 검색 조건 |
| `searchKeyword` | query | 아니오 |  | 검색 키워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneTimelineInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/timezones/timelines`

- **요약**: 타임라인 생성
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TimezoneTimelinePutInfoValue | 타임라인 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones/timelines/{id}`

- **요약**: 타임라인 정보 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 타임라인 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneTimelineInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/timezones/timelines/{id}`

- **요약**: 타임라인 정보 수정
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 타임라인 ID |
| `body` | body | 예 | TimezoneTimelinePutInfoValue | 수정 할 타임라인 정보 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/timezones/timelines/{id}`

- **요약**: 타임라인 정보 삭제
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 타임라인 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/timezones/{id}`

- **요약**: 타임존 정보 조회
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회 할 타임존 ID |
| `full` | query | 아니오 |  | 전체 구조 여부 (true=전체, false=요약) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TimezoneInfo` |
| `405` | Invalid input |  |

---

## PUT `/v1/timezones/{id}`

- **요약**: 타임존 정보 수정
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정 할 타임존 ID |
| `body` | body | 예 | TimezoneInfo | 수정 할 타임존 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/timezones/{id}`

- **요약**: 타임존 정보 삭제
- **태그**: timezones
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 타임존 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/absenteeism`

- **요약**: 결근자 조회.
- **설명**: 결근자를 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startDate` | query | 예 |  | 조회 시작일 (ex.2018-05-10) |
| `endDate` | query | 예 |  | 조회 종료일 (ex.2018-05-11) |
| `group` | query | 아니오 |  | 그룹 코드 |
| `user` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/tna/early_depatures`

- **요약**: 조퇴자 조회
- **설명**: 조퇴자를 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startDate` | query | 예 |  | 조회 시작일 (ex.2018-05-10) |
| `endDate` | query | 예 |  | 조회 종료일 (ex.2018-05-11) |
| `group` | query | 아니오 |  | 그룹 코드 |
| `user` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/tna/late_arrivals`

- **요약**: 지각자 조회
- **설명**: 지각자를 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startDate` | query | 예 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endDate` | query | 예 |  | 조회 마지막 날짜 (ex.2018-05-11) |
| `group` | query | 아니오 |  | 그룹 코드 |
| `user` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/tna/periodResult`

- **요약**: 근태 결과 조회
- **설명**: 근태 처리된 결과값을 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `startTime` | query | 예 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endTime` | query | 예 |  | 조회 마지막 날짜 (ex.2018-05-11) |
| `group` | query | 아니오 |  | 그룹 코드, 지정시 해당 그룹에 포함된 사용자만 조회 |
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회할 키워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/tna/periodWorkTime`

- **요약**: 기간별 사용자 근무시간 집계정보를 조회한다.
- **설명**: 기간별 사용자 근무시간 집계정보를 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회할 키워드 |
| `offset` | query | 예 |  | 조회할 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |
| `startDate` | query | 예 |  | 조회 시작 날짜 (ex.2018-05-10) |
| `endDate` | query | 예 |  | 조회 마지막 날짜 (ex.2018-05-11) |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/tna/setting/payment`

- **요약**: 근태 지급액 조회
- **설명**: 등록되어 있는 근태 지급액을 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 조회할 근태 지급액 코드 정보, 만약 빈값이면 모두 조회 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/tna/setting/payment`

- **요약**: 근태 지급액 등록
- **설명**: 근무 시간별 지급액 및 정산 단위를 설정한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TNA_PaymentConfig | 근태 지급액 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/tna/setting/payment`

- **요약**: 근태 지급액 삭제
- **설명**: 등록된 근태 지급액을 삭제한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 삭제할 근태 지급액 코드, 만약 빈값이면 모두 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/setting/schedule`

- **요약**: 근무 형태 조회
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 코드값 근무 형태를 조회하며 빈값일 경우 모든 근무 형태를 조회한다. |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/tna/setting/schedule`

- **요약**: 근무 형태 등록
- **설명**: 근무 일정에 맞게 근무 형태를 등록한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TNA_ScheduleConfig | 근무 형태 등록 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/tna/setting/schedule`

- **요약**: 근무 형태 삭제
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 근무 코드 삭제, 빈값일 경우 모두 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/setting/shift`

- **요약**: 근무 시간 조회
- **설명**: 근태 처리 기준 사항을 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 코드값 근무 시간을 조회하며 빈값일 경우 모든 근무 시간을 조회한다. |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/tna/setting/shift`

- **요약**: 근무 시간 등록
- **설명**: 기본 근무 시간 및 근태 처리 기준의 기본 사항을 등록한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TNA_ShiftConfig | 근무 시간 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/tna/setting/shift`

- **요약**: 근무 시간 삭제
- **설명**: 등록된 근무 시간 코드 삭제
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | query | 아니오 |  | 근무 코드 삭제, 빈값일 경우 모두 삭제 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/setting/workconfig`

- **요약**: 근태 설정 조회
- **설명**: 설정된 근태 옵션을 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TNA_WorkConfig` |
| `405` | Invalid input |  |

---

## PUT `/v1/tna/setting/workconfig`

- **요약**: 근태 설정 수정
- **설명**: 설정된 근태 옵션을 수정한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TNA_WorkConfig | 수정할 근태 설정 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/specialshift`

- **요약**: 특별 근무 조회
- **설명**: 특별 근무를 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `workDate` | query | 아니오 |  | 근무 날짜 |
| `userID` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## POST `/v1/tna/specialshift`

- **요약**: 특별 근무 지정
- **설명**: 등록된 근무 일정과는 별도로 특별 근무를 지정할 수 있다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | TNA_SepcialShift | 특별 근무 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## DELETE `/v1/tna/specialshift`

- **요약**: 특별 근무 삭제
- **설명**: 특별 근무로 지정된 날짜의 사용자를 삭제한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `workDate` | query | 아니오 |  | 날짜 |
| `userID` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ApiResponse` |
| `405` | Invalid input |  |

---

## GET `/v1/tna/sum_result`

- **요약**: 근태 집계 결과 조회
- **설명**: 집계 처리된 결과값을 조회한다.
- **태그**: tna
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 예 |  | 조회 유형 |
| `searchKeyword` | query | 예 |  | 조회 키워드 |
| `group` | query | 아니오 |  | 그룹 코드, 지정시 해당 그룹에 포함된 사용자만 조회 |
| `user` | query | 아니오 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation |  |
| `405` | Invalid input |  |

---

## GET `/v1/users`

- **요약**: 사용자 목록 조회
- **설명**: 사용자 목록 보기
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `searchCategory` | query | 아니오 |  | 조회 유형 |
| `searchKeyword` | query | 아니오 |  | 조회할 키워드 |
| `groupID` | query | 예 |  | 조회할 그룹 아이디 (0이면 미지정) |
| `subInclude` | query | 예 |  | 권한에 따른 그룹사용자 검색결과 포함 결정 |
| `offset` | query | 예 |  | 조회할 시작 위치 |
| `limit` | query | 예 |  | 조회 할 목록 수 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/users`

- **요약**: 사용자 추가
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `UserID` | query | 예 |  | 추가 할 사용자 아이디 |
| `body` | body | 예 | AddUserInfo | 사용자 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/Duplicate`

- **요약**: Unique ID 중복 체크
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `UniqueID` | query | 예 |  | Unique ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/users/imagequalitycheck`

- **요약**: 이미지 퀄리티 체크
- **설명**: 이미지 사진을 전송하여 퀄리티 체크를 합니다. (사전에 Ubio-X Face, Ubio-X Face Pro, Ubio-X Face Premium, Ubio-X Pro2 단말기를 연결 후 사용해야 합니다.)
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | object | Base64로 인코딩 한 이미지 문자열 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/initUserInfo`

- **요약**: 등록가능한 사용자 아이디 가져오기
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `InitUserInfoResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}`

- **요약**: 사용자 정보 조회
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 조회할 사용자 아이디 |
| `fingerprint` | query | 아니오 |  | 사용자 지문 포함 여부 결정 (only false) |
| `face` | query | 아니오 |  | 사용자 얼굴 포함 여부 결정 (only false) |
| `picture` | query | 아니오 |  | 사용자 사진 포함 여부 결정 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}`

- **요약**: 사용자 정보 수정
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 사용자 아이디 |
| `body` | body | 예 | UpdateUserInfo | 수정할 사용자 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/users/{id}`

- **요약**: 사용자 삭제
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제할 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/FaceInfo`

- **요약**: 얼굴 정보 조회
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 얼굴 인증 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserFaceInfoResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/card`

- **요약**: 카드 정보 조회
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 카드 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserRFCardInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}/card`

- **요약**: 카드 정보 수정
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 사용자 아이디 |
| `body` | body | 예 | array<UserCardInfo> | 수정할 카드 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/users/{id}/card`

- **요약**: 사용자 RF 카드 삭제
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 삭제 할 사용자 ID |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/faceWTInfo`

- **요약**: 얼굴(faceWT) 정보 조회
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 얼굴(faceWT) 인증 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserFaceWTInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}/faceWTInfo`

- **요약**: 얼굴(faceWT) 정보 수정
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 사용자 아이디 |
| `body` | body | 예 | array<FaceWTInfo> | 수정할 얼굴(faceWT) 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/fingerPrint`

- **요약**: 사용자 지문정보 가져오기
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 등록된 사용자 지문정보 가져오기 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserFPInfoResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}/loginpassword`

- **요약**: 최초 로그인시 비밀번호 변경
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 사용자 아이디 |
| `body` | body | 예 | UserPasswordInfo | 수정할 로그인 패스워드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/picture`

- **요약**: 사용자 사진 조회
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사진 정보 가져올 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `UserPictureResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}/picture`

- **요약**: 사진 정보 수정
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 수정할 사용자 아이디 |
| `ImageData` | body | 예 | UserPicture | 수정할 사진 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/users/{id}/terminaluser`

- **요약**: 사용가능한 단말기 리스트 정보가져오기
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자 아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `TerminalUserTinyListResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/users/{id}/token`

- **요약**: 사용자 토큰 업데이트
- **태그**: users
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `id` | path | 예 |  | 사용자 ID |
| `body` | body | 예 | UserTokenInfo | 토큰 데이터 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/visit/login`

- **요약**: 방문객 관리자 로그인
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | VisitLogin |  |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/visit/logout`

- **요약**: 방문객 관리자 로그아웃
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/visit/visitApplication`

- **요약**: 방문신청 리스트 조회
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `Status` | query | 예 |  | -1 : 전체, 1 : 대기, 2 : 승인, 3 : 거부, 4 : 만료 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/visit/visitApplication/{visitIndex}/status`

- **요약**: 방문신청 승인, 거부
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `visitIndex` | path | 예 |  | 방문신청 번호 |
| `Status` | query | 예 |  | 2 : 승인, 3 : 거부 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/visit/visitApplication/{visitIndex}/visitor/{visitorIndex}`

- **요약**: 방문신청 등록
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `visitIndex` | path | 예 |  | 방문신청 번호 |
| `visitorIndex` | path | 예 |  | 방문객 번호 |
| `body` | body | 예 | AddVisitorInfo | 방문신청 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/visit/visitInvite`

- **요약**: 방문신청 메일 전송
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | VisitInvite |  |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/visitor/visitApplication`

- **요약**: 방문신청 조회
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `FirstName` | query | 아니오 |  | 이름 |
| `LastName` | query | 아니오 |  | 성 |
| `Mobile` | query | 아니오 |  | 생년월일 |
| `Password` | query | 아니오 |  | 비밀번호 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## POST `/v1/visitor/visitApplication`

- **요약**: 방문신청
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | VisitorInfomation | 방문신청 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/visitor/visitorApplication/{visitIndex}`

- **요약**: 방문신청 취소
- **태그**: visitor
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `visitIndex` | path | 예 |  | 방문신청 번호 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/web/notice`

- **요약**: Web 공지사항 목록 조회
- **태그**: web notice
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation/ | `WebNoticeResult` |
| `405` | Invalid input |  |

---

## POST `/v1/web/notice`

- **요약**: Web 공지사항 등록
- **태그**: web notice
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | WebNotice | Web 공지사항 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `Result` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/in`

- **요약**: wiegand in 목록 가져오기
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/wiegand/in`

- **요약**: wiegand in 등록
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | WiegandIn | wiegand in 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/wiegand/in/download`

- **요약**: wiegand in 정보 단말기로 다운로드
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | WiegandInToTerminalDownload | wiegand in 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/in/{code}`

- **요약**: wiegand in 정보 가져오기
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand in 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandInResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/wiegand/in/{code}`

- **요약**: wiegand in 정보 업데이트
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand in 코드 |
| `body` | body | 예 | WiegandIn | wiegand in 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/wiegand/in/{code}`

- **요약**: wiegand in 정보 업데이트
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand in 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/in/{terminalID}/terminal`

- **요약**: wiegand in 단말기 정보
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `terminalID` | path | 예 |  | 연결된 단말기아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandInResult` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/out`

- **요약**: wiegand out 목록 가져오기
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandListResult` |
| `405` | Invalid input |  |

---

## POST `/v1/wiegand/out`

- **요약**: wiegand out 등록
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | WiegandOut | wiegand out 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/wiegand/out/download`

- **요약**: wiegand in 정보 단말기로 다운로드
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `body` | body | 예 | WiegandInToTerminalDownload | wiegand in 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/out/{code}`

- **요약**: wiegand out 정보 가져오기
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand out 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandOutResult` |
| `405` | Invalid input |  |

---

## PUT `/v1/wiegand/out/{code}`

- **요약**: wiegand out 정보 업데이트
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand out 코드 |
| `body` | body | 예 | WiegandOut | wiegand out 정보 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## DELETE `/v1/wiegand/out/{code}`

- **요약**: wiegand out 정보 업데이트
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `code` | path | 예 |  | wiegand out 코드 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `ResponseResult` |
| `405` | Invalid input |  |

---

## GET `/v1/wiegand/out/{terminalID}/terminal`

- **요약**: wiegand out 단말기 정보
- **태그**: wiegand
- **consumes**: `application/json`
- **produces**: `application/json`

**파라미터**
| 이름 | 위치 | 필수 | 타입 | 설명 |
|------|------|------|------|------|
| `terminalID` | path | 예 |  | 연결된 단말기아이디 |

**응답**
| 코드 | 설명 | 스키마 |
|------|------|--------|
| `200` | successful operation | `WiegandOutResult` |
| `405` | Invalid input\ |  |

---

## 스키마 정의 (definitions)

아래는 모델/응답 구조입니다. API 경로 검색과 함께 참고하세요.

### 스키마 `APBAreaDetailInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AreaID` | integer |  | 영역 ID |
| `Name` | string |  | 영역 이름 |
| `In` | array<APBAreaTerminalInfo> |  | 입구 영역 정보 (단말기 & 영역 ID) |
| `Out` | array<APBAreaTerminalInfo> |  | 출구 영역 정보 (단말기 & 영역 ID) |

---

### 스키마 `APBAreaInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AreaID` | integer |  | 영역 ID(1000 ~ 9999) |
| `Name` | string |  | 영역 이름 |

---

### 스키마 `APBAreaTerminalInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 ID |
| `LinkedAreaID` | integer |  | 연결 된 영역 ID (입구 정보일 경우 설정 된 출구 영역 ID) |

---

### 스키마 `AccessArea`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 출입구역 아이디 |
| `Name` | string |  | 출입구역 이름 |
| `Timezone` | integer |  | 출입구역 타임존 |
| `Floore` | string |  | 출입구역 출입 층 |

---

### 스키마 `AccessAreaIDs`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | array<integer> |  | 출입구역 아이디 리스트 |

---

### 스키마 `AccessAreaPost`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | Access Area id |
| `Name` | string |  | Access Area name |
| `Floor` | string |  | Access Area name |
| `TID` | array<integer> |  | Access Area id |

---

### 스키마 `AccessGroup`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 출입 그룹 아이디 |
| `Name` | string |  | 출입그룹 이름 |
| `TimezoneID` | integer |  | 타임존 아이디 |
| `VisitEnable` | integer |  | 방문객 출입 허용 여부 |
| `ElevatorSetID` | integer |  | 출입층 아이디 |
| `AreaCodes` | array<integer> |  | 출입그룹에 포함된 출입구역 목록 |

---

### 스키마 `AccessGroupList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AccessGroupList` | array<AccessGroup> |  |  |

---

### 스키마 `AccessGroupUserID`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | array<string> |  | 출입그룹에 등록, 삭제 할 사용자 아이디 |
| `Source` | integer |  | 사용자 등록시 0, 삭제시 출입그룹 아이디 |
| `Target` | integer |  | 사용자 등록시 출입그룹 아이디, 삭제시 0 |

---

### 스키마 `AccessGroup_AllUsers`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `RegUsersTotal` | RegUsersTotal |  |  |
| `RegUsersInfo` | object |  |  |
| `UnRegUsersTotal` | UnRegUsersTotal |  |  |
| `UnRegUsersInfo` | UnRegUsersInfo |  |  |

---

### 스키마 `AccessGroup_Terminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AccessGroupID` | integer |  | 출입그룹 아이디 |
| `TerminalID` | string |  | 단말기 아이디 |

---

### 스키마 `AccessGroup_Terminal_Download`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 아이디 |

---

### 스키마 `AccessGroup_Terminal_Download_Res`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 아이디 |
| `Result` | integer |  | 전송 결과 |

---

### 스키마 `AccessGroup_User`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AccessGroupID` | integer |  | 출입그룹 아이디 |
| `UserID` | string |  | 사용자 아이디 |

---

### 스키마 `AccountInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `UniqueID` | string |  | 고유값 |
| `Uuid` | string |  | 고유값 |
| `Name` | string |  | 사용자 이름 |
| `LoginPW` | string |  | 패스워드 |
| `Privilege` | integer |  | 사용자 권한 |
| `FirstLoginFlag` | integer |  | 첫번째 로그인 flag |
| `ServerID` | integer |  |  |
| `LoginAllowed` | integer |  | 로그인 허용 flag |
| `LoginFailCount` | integer |  | 로그인 실패 횟수 |

---

### 스키마 `ActivationInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Mode` | integer |  |  |
| `ProductID` | integer |  |  |
| `SerialKey` | string |  |  |
| `CustomerID` | string |  |  |
| `CompanyName` | string |  |  |
| `ClientKey` | string |  |  |
| `LicenseKey` | string |  |  |

---

### 스키마 `AddUserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserInfo` | UserInfo |  |  |
| `UserFPInfo` | array<UserFPInfo> |  |  |
| `UserFaceInfo` | array<UserFaceInfo> |  |  |
| `UserCardInfo` | array<UserCardInfo> |  |  |
| `UserFaceWTInfo` | array<UserFaceWTInfo> |  |  |
| `UserIrisInfo` | array<UserIrisInfo> |  |  |

---

### 스키마 `AddVisitorInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserInfo` | VisitorInfo |  |  |
| `UserFPInfo` | array<UserFPInfo> |  |  |
| `UserFaceInfo` | array<UserFaceInfo> |  |  |
| `UserCardInfo` | array<UserCardInfo> |  |  |
| `UserFaceWTInfo` | array<UserFaceWTInfoVisitor> |  |  |

---

### 스키마 `AlarmConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Hour` | integer |  | 시 |
| `Minute` | integer |  | 분 |
| `Weekday` | integer |  | 주일 |
| `Duration` | integer |  | 지속 시간 |
| `Reserved` | integer |  | 예약 |

---

### 스키마 `AlarmOptionList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Alarms` | array<WebAlarm> |  |  |

---

### 스키마 `AlarmScheduleConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Hour` | integer |  | 시 HH |
| `Minute` | integer |  | 분 mm |
| `Weekday` | integer |  | Bit 연산 [7]일, [6]월, [5]화, [4]수, [3]목, [2]금, [1]토, [0]고유일 제외 |
| `Duration` | integer |  | 지속 시간 |
| `AutoArmPartition` | integer |  | 자동 셋트 설정 파티션 Bit 연산 [1],[2],[3],[4] |
| `AutoDisarmPartition` | integer |  | 자동 셋트 해제 파티션 Bit 연산 [1],[2],[3],[4] |
| `Output` | integer |  | 출력 Bit 연산 0~7 |

---

### 스키마 `ApiResponse`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `resultCode` | integer |  |  |
| `message` | string |  |  |

---

### 스키마 `AuditLog`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `EventTime` | string |  | 작업 발생 시각 |
| `UserID` | string |  | 관리자 아이디 |
| `Category` | integer |  | 작업 구분 |
| `Content` | integer |  | 작업 내용 |
| `Detail` | string |  | 작업 상세 |
| `Target` | string |  | 작업 대상 |
| `Action` | integer |  | 작업 처리 내용 |
| `Location` | integer |  | 작업 위치 |

---

### 스키마 `AuthInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Order01` | integer |  | 1번째 인증 타입 |
| `Order02` | integer |  | 2번째 인증 타입 |
| `Order03` | integer |  | 3번째 인증 타입 |
| `Order04` | integer |  | 4번째 인증 타입 |
| `Order05` | integer |  | 5번째 인증 타입 |
| `Order06` | integer |  | 6번째 인증 타입 |
| `Order07` | integer |  | 7번째 인증 타입 |
| `RequireIndex` | integer |  | 필수 인증 인덱스 (값이 2인경우 2번째 인증까지 필수인증, 이후는 선택 인증) |

---

### 스키마 `AuthLog`

기타 인증데이터 (ex. 온도)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `IndexKey` | integer |  | 로그정보 고유 키 |
| `TerminalID` | integer |  | 단말기 ID |
| `UserID` | string |  | 사용자 ID |
| `GroupCode` | integer |  | 사용자 그룹 코드 |
| `UserName` | string |  | 사용자 이름 |
| `EventTime` | string |  | 인증로그 시간 |
| `ServerRecordTime` | string |  | 서버에 저장 된 시간 |
| `AuthType` | integer |  | 인증 타입 |
| `AuthResult` | integer |  | 인증 결과 |
| `Func` | integer |  | 단말기 기능 |
| `FuncType` | integer |  | 단말기 기능 키 |
| `Card` | string |  | 카드 번호 |
| `UserType` | integer |  | 사용자 타입 |
| `IsPicture` | integer |  | 인증 로그 이미지 저장 여부 |
| `Property` | string |  | 인증 속성 |
| `Latitude` | integer |  | 위치 정보(위도) |
| `Longitude` | integer |  | 위치 정보 (경도) |
| `ReserveType` | integer |  | 기타 인증데이터 타입 (ex. 온도) |
| `ReserveData` | string |  |  |

---

### 스키마 `AuthLogDetail`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `IndexKey` | integer |  | 로그정보 고유 키 |
| `UserID` | string |  | 사용자 ID |
| `UserName` | string |  | 사용자 이름 |
| `EventTime` | string |  | 인증로그 시간 |
| `AuthResult` | integer |  | 인증결과 |
| `Func` | integer |  | 단말기 기능 |
| `FuncType` | integer |  | 단말기 기능 키 |
| `Card` | string |  | 카드 번호 |
| `UserImage` | string |  | 사용자 이미지 |
| `LogImage` | string |  | 로그 이미지 |

---

### 스키마 `AuthLogDetailResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `AuthLogList` | AuthLogDetail |  |  |

---

### 스키마 `AuthLogImage`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `LogImage` | string |  | 인증로그 이미지 |

---

### 스키마 `AuthLogImageResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `AuthLogImage` | AuthLogImage |  |  |

---

### 스키마 `AuthLogListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Total` | Total |  |  |
| `AuthLogList` | AuthLog |  |  |

---

### 스키마 `AuthLogsMonthlyStatistics`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TotalCount` | integer |  | 월별 전체 인증기록 갯수 |
| `SuccessResultCount` | integer |  | 월별 인증 성공 갯수 |
| `FailResultCount` | integer |  | 월별 인증 실패 갯수 |
| `CountbyAuthType` | CountbyAuthType |  |  |
| `TopFivebyTerminal` | array<TopFivebyTerminal> |  |  |
| `TopFivebyUser` | array<TopFivebyUser> |  |  |

---

### 스키마 `AuthLogsMonthlyStatisticsResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `AuthLogsMonthlyStatistics` | AuthLogsMonthlyStatistics |  |  |

---

### 스키마 `BrandType`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 브랜드 타입 |

---

### 스키마 `CardInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `CardNumber` | string |  | 카드 번호 |

---

### 스키마 `ClientKeyInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ClientKey` | string |  |  |

---

### 스키마 `ConvertFormat`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | DataType 설정 (0: Unused, 1: Binary, 2:Decimal String, 3:Hexa String) |
| `Digit` | integer |  | Digit Size 설정(4) |
| `Endian` | integer |  | Endian 설정 (0: (MSBit : MSByte), 1: (LSBit : MSByte), 2: (MSBit : LSByte), 3: (LSBit : LSByte) |
| `MaskBits` | string |  | Set Field 위치 지정 |

---

### 스키마 `CountByGroup`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `GroupID` | integer |  | 그룹 아이디 |
| `UserCount` | integer |  | 그룹에 속한 사용자 수 |

---

### 스키마 `CountResultData`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Count` | integer |  |  |

---

### 스키마 `CountbyAuthType`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AuthTypeFinger` | integer |  | 지문인증 시도 횟수 |
| `AuthTypeCard` | integer |  | 카드인증 시도 횟수 |
| `AuthTypePassword` | integer |  | 비밀번호 인증 시도 횟수 |
| `AuthTypeFace` | integer |  | 얼굴인증 시도 횟수 |

---

### 스키마 `CreateTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Name` | string |  | 단말기 이름 |
| `description` | string |  | 기타 사항 |

---

### 스키마 `DownloadInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Total` | integer |  |  |
| `Offset` | integer |  |  |

---

### 스키마 `DownloadInfoData`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `DownloadInfo` | DownloadInfo |  |  |

---

### 스키마 `ElevatorSetInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ElevatorSetID` | integer |  | ElevatorSetID |
| `ElevatorSetName` | string |  | ElevatorSetName |
| `AccessFloor` | array<integer> |  | Access Floor |

---

### 스키마 `ErrorCode00`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorNone` | 0x00000000 |  |  |
| `ErrorInvalidParameter` | 0x00000001 |  |  |
| `ErrorAuthorizeFailed` | 0x00000002 |  |  |
| `ErrorMismatched` | 0x00000003 |  |  |
| `ErrorDataNotExist` | 0x00000004 |  |  |
| `ErrorDataServerConnectionFailed` | 0x00000005 |  |  |
| `ErrorInternalServerError` | 0x00000006 |  |  |
| `ErrorNotPermission` | 0x00000007 |  |  |
| `ErrorPacketTimeout` | 0x00000008 |  |  |
| `ErrorProtoMarshalFail` | 0x00000009 |  |  |
| `ErrorProtoUnMarshalFail` | 0x0000000A |  |  |
| `ErrorSkip` | 0x0000000B |  |  |
| `ErrorNotLoginState` | 0x0000000C |  |  |
| `ErrorInvalidServerID` | 0x0000000D |  |  |
| `ErrorUserConnectionMaxExceed` | 0x0000000E |  |  |
| `ErrorUndefinedErrorCode` | 0x0000000F |  |  |
| `ErrorPackingFailed` | 0x00000010 |  |  |
| `ErrorParameter` | 0x00000011 |  |  |
| `ErrorOemVersion` | 0x00000012 |  |  |
| `ErrorNoAvailableASServer` | 0x00000013 |  |  |
| `ErrorSessionInfo` | 0x00000014 |  |  |
| `ErrorSessionTimeOut` | 0x00000015 |  |  |
| `ErrorInvalidPeriod` | 0x00000016 |  |  |
| `ErrorDatabase` | 0x00000017 |  |  |

---

### 스키마 `ErrorCode01`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorUserDuplicateID` | 0x01000001 |  |  |
| `ErrorUserNotExist` | 0x01000002 |  |  |
| `ErrorUserInvalidFPData` | 0x01000003 |  |  |
| `ErrorUserAuthenticationFailed` | 0x01000004 |  |  |
| `ErrorUserInvalidID` | 0x01000005 |  |  |
| `ErrorReDuplicateUniqueID` | 0x01000006 |  |  |
| `ErrorReDuplicateNotUniqueID` | 0x01000007 |  |  |
| `ErrorUserExist` | 0x01000008 |  |  |
| `ErrorUserNameInvalid` | 0x01000009 |  |  |
| `ErrorUserAuthTypeInvalid` | 0x0100000A |  |  |
| `ErrorUserUniqueIDInvalid` | 0x0100000B |  |  |
| `ErrorUserPasswordInvalid` | 0x0100000C |  |  |
| `ErrorUserSimilarFingerprint` | 0x0100000D |  |  |
| `ErrorUserOldLoginPasswordDuplicate` | 0x0100000E |  |  |
| `ErrorUserLoginPasswordExpirationDate` | 0x0100000F |  |  |
| `ErrorUserLoginFailCount` | 0x01000011 |  |  |
| `ErrorUserLoginPasswordWrongInput` | 0x01000012 |  |  |
| `ErrorUserRfCardDuplicate` | 0x01000013 |  |  |
| `ErrorUserSimilarFace` | 0x01000014 |  |  |
| `ErrorUserSimilarCard` | 0x01000015 |  |  |
| `ErrorUserInvalidUsePeriod` | 0x01000016 |  |  |
| `ErrorUserInvalidFAData` | 0x01000017 |  |  |
| `ErrorUserInvalidLoginPwd` | 0x01000018 |  |  |
| `ErrorUserInvalidLoginAllow` | 0x01000019 |  |  |
| `ErrorUserLoginPasswordDuplicate` | 0x0100001A |  |  |
| `ErrorUserBlackListStatus` | 0x0100001B |  |  |
| `ErrorUserInvalidFaceWTData` | 0x0100001C |  |  |

---

### 스키마 `ErrorCode02`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorTerminalInvalidStatus` | 0x02000001 |  |  |
| `ErrorTerminalIDDuplication` | 0x02000002 |  |  |
| `ErrorTerminalNotRegistered` | 0x02000003 |  |  |
| `ErrorTerminalNotConnected` | 0x02000004 |  |  |
| `ErrorTerminalAnotherProcess` | 0x02000005 |  |  |
| `ErrorTerminalNotSupportFunc` | 0x02000006 |  |  |
| `ErrorTerminalNotSupportTerminal` | 0x02000007 |  |  |
| `ErrorTerminalWorkingState` | 0x02000008 |  |  |
| `ErrorTerminalUserOccur` | 0x02000101 |  |  |
| `ErrorTerminalUserOccurButProceed` | 0x02000102 |  |  |
| `ErrorTerminalFpCaptuer` | 0x02000201 |  |  |
| `ErrorTerminalSaveUser` | 0x02000F01 |  |  |
| `ErrorTerminalLoadUser` | 0x02000F02 |  |  |
| `ErrorTerminalNoUser` | 0x02000F03 |  |  |
| `ErrorTerminalExistUser` | 0x02000F04 |  |  |
| `ErrorTerminalDeleteFP` | 0x02000F05 |  |  |
| `ErrorTerminalUserFull` | 0x02000F06 |  |  |
| `ErrorTerminalUpdateUser` | 0x02000F07 |  |  |
| `ErrorTerminalDuplicateRF` | 0x02000F08 |  |  |
| `ErrorFacewtNoFace` | 0x02000F09 |  |  |
| `ErrorFacewtMultiFace` | 0x02000F0A |  |  |
| `ErrorFacewtSmall` | 0x02000F0B |  |  |
| `ErrorFacewtLowScore` | 0x02000F0C |  |  |
| `ErrorFacewtSideFace` | 0x02000F0D |  |  |
| `ErrorFacewtVague` | 0x02000F0E |  |  |
| `ErrorFacewtTooFar` | 0x02000F0F |  |  |
| `ErrorFacewtRecogFail` | 0x02000F10 |  |  |
| `ErrorFacewtParam` | 0x02000F11 |  |  |
| `ErrorFacewtNoFile` | 0x02000F12 |  |  |
| `ErrorFacewtChip` | 0x02000F13 |  |  |
| `ErrorFacewtCertification` | 0x02000F14 |  |  |
| `ErrorFacewtMaxUser` | 0x02000F15 |  |  |
| `ErrorFacewtTimeout` | 0x02000F16 |  |  |
| `ErrorWearingMask` | 0x02000F17 |  |  |
| `ErrorImageBroken` | 0x02000F18 |  |  |

---

### 스키마 `ErrorCode03`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorGroupDuplicateID` | 0x03000001 |  |  |
| `ErrorGroupNotExistID` | 0x03000002 |  |  |
| `ErrorGroupNotExistParentID` | 0x03000003 |  |  |
| `ErrorGroupInvalidInfo` | 0x03000004 |  |  |
| `ErrorGroupInvalidID` | 0x03000005 |  |  |
| `ErrorGroupInvalidParentID` | 0x03000006 |  |  |
| `ErrorGroupDuplicateName` | 0x03000007 |  |  |
| `ErrorGroupCountMaxExceed` | 0x03000008 |  |  |
| `ErrorGroupNoSearchResult` | 0x03000101 |  |  |

---

### 스키마 `ErrorCode04`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorPrivilegeDuplicateID` | 0x04000001 |  |  |
| `ErrorPrivilegeNotExist` | 0x04000002 |  |  |
| `ErrorPrivilegeInvalidID` | 0x04000003 |  |  |
| `ErrorPrivilegeInvalidName` | 0x04000004 |  |  |
| `ErrorPrivilegeNotPermission` | 0x04000005 |  |  |
| `ErrorPrivilegeNotPermissionUser` | 0x04000006 |  |  |
| `ErrorPrivilegeNotPermissionTerminal` | 0x04000007 |  |  |
| `ErrorPrivilegeNotPermissionGroup` | 0x04000008 |  |  |

---

### 스키마 `ErrorCode05`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorTimezoneDuplicateID` | 0x05000001 |  |  |
| `ErrorTimezoneNotExist` | 0x05000002 |  |  |
| `ErrorTimezoneInvalidID` | 0x05000003 |  |  |
| `ErrorTimezoneInvalidName` | 0x05000004 |  |  |
| `ErrorTimezoneInvalidTime` | 0x05000005 |  |  |
| `ErrorTimezoneInvalidTimeFormat` | 0x05000006 |  |  |
| `ErrorTimezoneNotExistTime` | 0x05000007 |  |  |
| `ErrorTimezoneNotExistTimeline` | 0x05000008 |  |  |
| `ErrorTimezoneNotExistHoliday` | 0x05000009 |  |  |

---

### 스키마 `ErrorCode06`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorAPBNotExistTerminalID` | 0x06000001 |  |  |
| `ErrorAPBNotExistAreaID` | 0x06000002 |  |  |
| `ErrorAPBDuplicateTerminalID` | 0x06000003 |  |  |
| `ErrorAPBDuplicateAreaID` | 0x06000004 |  |  |
| `ErrorAPBInvalidTerminalID` | 0x06000005 |  |  |
| `ErrorAPBInvalidAreaID` | 0x06000006 |  |  |
| `ErrorAPBInvalidStatus` | 0x06000007 |  |  |
| `ErrorAPBAreaDuplicateID` | 0x06000101 |  |  |
| `ErrorAPBAreaNotExist` | 0x06000102 |  |  |
| `ErrorAPBAreaInvalidID` | 0x06000103 |  |  |
| `ErrorAPBAreaInvalidName` | 0x06000104 |  |  |
| `ErrorAPBTerminalFail` | 0x06000201 |  |  |

---

### 스키마 `ErrorCode07`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorPositionDuplicateID` | 0x07000001 |  |  |
| `ErrorPositionNotExist` | 0x07000002 |  |  |
| `ErrorPositionInvalidID` | 0x07000003 |  |  |
| `ErrorPositionInvalidName` | 0x07000004 |  |  |
| `ErrorPositionDuplicateName` | 0x07000005 |  |  |

---

### 스키마 `ErrorCode08`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorMessageDuplicateID` | 0x08000001 |  |  |
| `ErrorMessageNotExist` | 0x08000002 |  |  |
| `ErrorMessageInvalidID` | 0x08000003 |  |  |
| `ErrorMessageInvalidMessage` | 0x08000004 |  |  |

---

### 스키마 `ErrorCode09`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorNoticeDuplicateID` | 0x09000001 |  |  |
| `ErrorNoticeNotExist` | 0x09000002 |  |  |
| `ErrorNoticeInvalidID` | 0x09000003 |  |  |
| `ErrorNoticeInvalidMessage` | 0x09000004 |  |  |

---

### 스키마 `ErrorCode0A`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorWiegandDuplicateCode` | 0x0A000001 |  |  |
| `ErrorWiegandNotExist` | 0x0A000002 |  |  |
| `ErrorWiegandInvalidCode` | 0x0A000003 |  |  |
| `ErrorWiegandInvalidData` | 0x0A000004 |  |  |

---

### 스키마 `ErrorCode0B`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorLicenseInitializeFail` | 0x0B000001 |  |  |
| `ErrorLicenseNotAlpetaLicense` | 0x0B000002 |  |  |
| `ErrorLicenseDecryptFail` | 0x0B000003 |  |  |
| `ErrorLicenseInvalidStart` | 0x0B000004 |  |  |
| `ErrorLicenseExired` | 0x0B000005 |  |  |
| `ErrorTerminalNoLicense` | 0x0B000006 |  |  |
| `ErrorLicenseInvalidMac` | 0x0B000007 |  |  |
| `ErrorLicenseInvalidFunc` | 0x0B000008 |  |  |
| `ErrorSerialKeyCreateFail` | 0x0B000009 |  |  |
| `ErrorLicenseInsertFail` | 0x0B00000A |  |  |
| `ErrorLicenseServerError` | 0x0B00000B |  |  |
| `ErrorLicenseActivationResError` | 0x0B00000C |  |  |
| `ErrorLicenseInvalidExpireDate` | 0x0B00000D |  |  |
| `ErrorLicenseEncryptFailed` | 0x0B00000E |  |  |
| `ErrorLicenseSerialKeyInvalid` | 0x0B00000F |  |  |
| `ErrorLicenseNotIssueReadyState` | 0x0B000010 |  |  |
| `ErrorLicenseKeyCreateFail` | 0x0B000011 |  |  |
| `ErrorLicenseKeyInvalid` | 0x0B000012 |  |  |
| `ErrorLicenseCustomerIDInvalid` | 0x0B000013 |  |  |
| `ErrorLicenseMacaddressInvalid` | 0x0B000014 |  |  |
| `ErrorLicenseTypeInvalid` | 0x0B000015 |  |  |
| `ErrorLicenseSerialKeyNotExist` | 0x0B000016 |  |  |
| `ErrorLicenseNotMatched` | 0x0B000017 |  |  |
| `ErrorLicenseIssuedLicenseTryDelete` | 0x0B000018 |  |  |

---

### 스키마 `ErrorCode0C`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorAnotherTaskProcessing` | 0x0C000001 |  |  |

---

### 스키마 `ErrorCode0D`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorDB` | 0x0D000001 |  |  |
| `ErrorDBSelect` | 0x0D000002 |  |  |
| `ErrorDBCreate` | 0x0D00F001 |  |  |
| `ErrorDBConnectionFail` | 0x0D00F002 |  |  |
| `ErrorDBAleadyExist` | 0x0D00F003 |  |  |
| `ErrorDBAleadyExistUser` | 0x0D00F004 |  |  |
| `ErrorDBPackageNotFound` | 0x0D00F005 |  |  |
| `ErrorDBCreateFolderFailed` | 0x0D00F006 |  |  |
| `ErrorDBInstallFailed` | 0x0D00F007 |  |  |
| `ErrorDBUserCreateFailed` | 0x0D00F008 |  |  |
| `ErrorDBTableCreate` | 0x0D00F009 |  |  |
| `ErrorDBNotExist` | 0x0D00F00A |  |  |
| `ErrorDBServiceStartFail` | 0x0D00F00B |  |  |
| `ErrorOpenSCManagerFailed` | 0x0D00F00C |  |  |

---

### 스키마 `ErrorCode30`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ErrorVisitApplicationNotExist` | 0x30000001 |  |  |
| `ErrorVisitApplicationNotApproved` | 0x30000002 |  |  |
| `ErrorVisitApplicationExpired` | 0x30000003 |  |  |
| `ErrorVisitVisitorInfoNotExist` | 0x30000004 |  |  |
| `ErrorVisitVisitorAlreadyRegistered` | 0x30000005 |  |  |
| `ErrorVisitVisitorNotRegistWaitState` | 0x30000006 |  |  |
| `ErrorVisitVisitorAccessgroupNotExist` | 0x30000007 |  |  |

---

### 스키마 `EventLog`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `EventTime` | string |  | 이벤트 발생 시각 |
| `DeviceID` | integer |  | 단말기 아이디 |
| `UserID` | string |  | 관리자 아이디 |
| `Category` | integer |  | 작업 구분 |
| `Content` | integer |  | 작업 내용 |
| `Detail` | string |  | 작업 상세 |

---

### 스키마 `ExdbLoginAccountInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | string |  | id |
| `pw` | string |  | pw |

---

### 스키마 `FPInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | string |  | 사용자 ID |
| `FingerID` | integer |  | 지문위치 ID |
| `TotalSize` | integer |  | 지문데이터 사이즈 |
| `Template1` | string |  | 첫번째 지문 템플릿 |
| `Template2` | string |  | 두번째 지문 템플릿 |
| `ConvImage1` | string |  | 첫번째 지문 이미지 |
| `ConvImage2` | string |  | 두번째 지문 이미지 |

---

### 스키마 `FaceInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 ID |
| `Index` | integer |  | 얼굴등록 개수 (1,2) |
| `Type` | integer |  | 0: 간편등록(3장), 1: 일반등록(5장) |
| `SubIndex` | integer |  | 등록된 이미지 순번(1,2,3,4,5) |
| `TemplateSize` | integer |  | 등록 얼굴 템플릿 데이터 사이즈 |
| `TemplateData` | integer |  | 등록 얼굴 템플릿 데이터 |

---

### 스키마 `FaceWTInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TemplateType` | integer |  | 등록 얼굴 워크스루 템플릿 타입 (0: 템플릿타입, 1: 이미지 타입) |
| `TemplateSize` | integer |  | 등록 얼굴 템플릿 데이터 사이즈 |
| `TemplateData` | string |  | 등록 얼굴 워크스루 템플릿 데이터 |

---

### 스키마 `GetFaceInfoFromTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `FaceInfo` | array<FaceInfo> |  |  |

---

### 스키마 `GetFaceWtInfoFromTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserFaceWTInfo` | array<FaceWTInfo> |  |  |

---

### 스키마 `GetFpImageFromTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `FPInfo` | FPInfo |  |  |

---

### 스키마 `GroupIDList`

- **type**: `array`

---

### 스키마 `GroupInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `GroupID` | integer |  | 그룹 ID |
| `Parent` | integer |  | 상위 그룹 ID |
| `Name` | string |  | 그룹 이름 |
| `description` | string |  | 설명 |

---

### 스키마 `GroupInfoReq`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `GroupID` | integer |  | 그룹 ID |
| `Parent` | integer |  | 상위 그룹 ID |
| `Name` | string |  | 그룹 이름 |

---

### 스키마 `GroupListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `GroupInfo` | array<GroupInfo> |  |  |

---

### 스키마 `GroupResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `GroupInfo` | GroupInfo |  |  |

---

### 스키마 `HolidayConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Month` | integer |  | 월 |
| `Day` | integer |  | 일 |
| `Type` | integer |  | 휴일 타입 |

---

### 스키마 `HowCanErrorCodeConvert`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `HowCanErrorCodeConvert` | string |  | Please run the Calcalator for Programmer, Enter the result code (ex: 16777237) value in DEC, After checking the HEX value, find the corresponding code (ex: ErrorCode01) in the Error Code menu at the bottom. |

---

### 스키마 `ImageInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ImageType` | string |  | 이미지 타입 |
| `ImageData` | string |  | 이미지 데이터 |

---

### 스키마 `ImageInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `ImageInfo` | ImageInfo |  |  |

---

### 스키마 `InBasicInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | integer |  | 위겐드In 구분 코드 |
| `Name` | string |  | 위겐드In 명칭 |
| `Bits` | integer |  | Bit Length 와 Custom Size 설정값 (0: unused, 1~128: Custom Size, 129: St. 26bit, 130: St.34bit) |
| `Port` | integer |  | PortState (0: Active Low, 1: Active High) |
| `ParityCount` | integer |  | Set Field 활성화된 상태 갯수 |
| `IntervalTime` | integer |  | IntervalTime 설정값 |
| `WidthTime` | integer |  | WidthTime 설정값 |

---

### 스키마 `InitUserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | string |  | 등록 가능한 사용자 아이디 |

---

### 스키마 `InitUserInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `InitUserInfo` | InitUserInfo |  |  |

---

### 스키마 `ItemList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ItemType` | integer |  |  |
| `NameType` | integer |  |  |
| `Name` | string |  |  |
| `InOut` | integer |  |  |
| `SerialNum` | string |  |  |
| `Model` | string |  |  |
| `Purpose` | string |  |  |
| `Unit` | string |  |  |
| `Count` | integer |  |  |
| `Desc` | string |  |  |

---

### 스키마 `LicenseInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `LicenseType` | integer |  |  |
| `LicenseKey` | string |  |  |
| `SerialKey` | string |  |  |
| `CustomerID` | string |  |  |
| `CompanyName` | string |  |  |
| `MacAddress` | string |  |  |
| `ExpireAt` | string |  |  |
| `Status` | string |  |  |

---

### 스키마 `LockConfig`

열림 시간 3

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Lock1` | TimeHHmmHHmm |  | 잠금 시간 1 |
| `Lock2` | TimeHHmmHHmm |  | 잠금 시간 2 |
| `Lock3` | TimeHHmmHHmm |  | 잠금 시간 3 |
| `Open1` | TimeHHmmHHmm |  | 열림 시간 1 |
| `Open2` | TimeHHmmHHmm |  | 열림 시간 2 |
| `Open3` | TimeHHmmHHmm |  |  |

---

### 스키마 `Login`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `userId` | string |  | 사용자 ID |
| `password` | string |  | 암호 |
| `userType` | integer |  | 로그인 요청 타입 (0: 일반관리자, 1: UniqueID, 2: 마스터관리자) |

---

### 스키마 `LoginFailInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `RemindCount` | integer |  | 사용자 로그인 요청가능 횟수 |

---

### 스키마 `LoginResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `AccountInfo` | AccountInfo |  |  |
| `SystemInfo` | SystemInfo |  |  |
| `LoginFailInfo` | LoginFailInfo |  |  |

---

### 스키마 `MCP_AlarmScheduleOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Alarms` | array<AlarmScheduleConfig> |  | MCP 스케줄 목록 |

---

### 스키마 `MCP_HolidayOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Holidays` | array<HolidayConfig> |  | MCP 공휴일 옵션 (3) |

---

### 스키마 `MCP_InputOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 0:NOT USED, 1:EXIT BUTTON NC, 2:EXIT BUTTON NO, 3:FIRE NC, 4:FIRE NO, 5:SECURITY NC, 6:SECURITY NO |
| `Time` | integer |  | 발생시각 |
| `Parameter` | integer |  | 파라미터 0-255 |

---

### 스키마 `MCP_InputsOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Inputs` | array<MCP_InputOption> |  | MCP Output 옵션 목록 (4) |

---

### 스키마 `MCP_LockSetOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ZoneDoor` | integer |  | 존/도어 모니터 0-7, 0xff = N/A |
| `OpenWarnTime` | integer |  | 문열림 경고 0-255 |
| `ForceEnable` | integer |  | 강제 설정 0:미설정, 1:설정 |

---

### 스키마 `MCP_LockSetsOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `LockSets` | array<MCP_LockSetOption> |  | MCP 잠금 설정 옵션 목록 (4) |

---

### 스키마 `MCP_LocksOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Locks` | array<LockConfig> |  | MCP 잠금 옵션 목록 (4) |

---

### 스키마 `MCP_NetworkOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `NetType` | integer |  | 0:다음 IP주소로 사용, 1:자동으로 IP주소 받기 |
| `IP` | string |  | 단말기 IP주소 |
| `Subnet` | string |  | 서브넷 |
| `Gateway` | string |  | 게이트웨이 |
| `ServerIP` | string |  | 서버 IP주소 |
| `ServerPort` | integer |  | 서버 포트 |
| `DHCP_IP` | string |  | DHCP IP주소 |
| `DHCP_Subnet` | string |  | DHCP 서브넷 |
| `DHCP_Gateway` | string |  | DHCP 게이트웨이 |

---

### 스키마 `MCP_OutputOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 0:미사용, 1:AUTHORIZED, 2:UNAUTHORIZED, 3:SCHEDULE, 4:ALARM, 5:TROUBLE, 6:ARM STATUS, 7:FIRE, 8:SILENT, 9:OPEN TOO LONG, 10:FORCED |
| `Time` | integer |  | 발생 시각 activation time - 255 = toggle, 0-254 초 |
| `Parameter` | integer |  | 파라미터 door#, partition#, schedule# 0-255 |
| `Inverted` | integer |  | 인버트 0:미활성화, 1:활성화 |

---

### 스키마 `MCP_OutputsOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Outputs` | array<MCP_OutputOption> |  | MCP Output 옵션 목록 (8) |

---

### 스키마 `MCP_PartitionOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Name` | string |  | 파티션 이름 |
| `Account` | string |  | 계정 |
| `EntryDelay1` | integer |  | 입실 딜레이1 0~255초 |
| `EntryDelay2` | integer |  | 입실 딜레이2 0~255초 |
| `ExitDelay1` | integer |  | 퇴실 딜레이1 0~255초 |
| `ExitDelay2` | integer |  | 퇴실 딜레이2 0~255초 |
| `SirenTime` | integer |  | 사이렌 시간 1~65535초 |
| `AlarmCount` | integer |  | 알람 횟수 0~255 |
| `Enable` | integer |  | 0:미사용, 1:사용 |
| `Chime` | integer |  | 0:미사용, 1:사용 |
| `UnlockOnDisarm` | integer |  | 0:미사용, 1:사용 |

---

### 스키마 `MCP_PartitionsOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Partitions` | array<MCP_PartitionOption> |  | MCP 파티션 옵션 목록 (4) |

---

### 스키마 `MCP_ReaderInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 ID |
| `ReaderName0` | string |  | 리더기0 이름 |
| `ReaderName1` | string |  | 리더기1 이름 |
| `ReaderName2` | string |  | 리더기2 이름 |
| `ReaderName3` | string |  | 리더기3 이름 |
| `ReaderName4` | string |  | 리더기4 이름 |
| `ReaderName5` | string |  | 리더기5 이름 |
| `ReaderName6` | string |  | 리더기6 이름 |
| `ReaderName7` | string |  | 리더기7 이름 |
| `WiegandName1` | string |  | 위겐드1 이름 |
| `WiegandName2` | string |  | 위겐드2 이름 |
| `WiegandName3` | string |  | 위겐드3 이름 |
| `WiegandName4` | string |  | 위겐드4 이름 |

---

### 스키마 `MCP_ReaderOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ReaderType` | integer |  | Smart-RD, ACF100, 기타... |
| `Lock` | integer |  | 잠금 설정 bit 연산 6=0110 은 2번,3번 잠김 |
| `Partition` | integer |  | 파티션 설정 bit 연산 6=0110 은 2번,3번 잠김 |
| `Mode` | integer |  | 0:출입통제, 1:출입통제/경비, 2:모두 |
| `OpenTime` | integer |  | 문열림 시간 0:항상 잠김, 255:항상 열림, 기타 1~254 초 설정 가능 |
| `AccessMode` | integer |  | 0:Access, 1:Enter, 2:Exit, 3:Out, 4:In |
| `EnterZone` | integer |  | 안티패스백 구역 입구 |
| `ExitZone` | integer |  | 안티패스백 구역 출구 |
| `PassbackType` | integer |  | 안티패스백 타입  0:disabled, 1:hard, 2:soft, 3:timed |
| `LockoutDuration` | string |  | 락아웃 시간 HH:mm:ss |

---

### 스키마 `MCP_ReadersOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Readers` | array<MCP_ReaderOption> |  | MCP 리더 옵션 목록 (12) |

---

### 스키마 `MCP_SystemOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `FoceArm` | integer |  | 강제 세트 설정 0:미설정, 1:설정 |
| `EndOfLineResistors` | integer |  | 종단 저항 설정 0:미설정, 1:설정 |
| `TimeSync` | integer |  | 시간 동기화 설정  0:미설정, 1:설정 |
| `IndiseOpenLog` | integer |  | 인사이드 오픈 설정  0:미설정, 1:설정 |
| `ServerPassback` | integer |  | 서버 패스백 사용  0:미설정, 1:설정 |
| `DoorInterlocking` | integer |  | 0:미설정, 1:설정 |
| `TerminalID` | integer |  | 단말기 ID |
| `AuthenticationMode` | integer |  |  |
| `LineTestTime` | integer |  |  |

---

### 스키마 `MCP_ZoneOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Name` | string |  | Smart-RD, ACF100, 기타... |
| `Type` | integer |  | 0:UnUsed, 1:Exit1, 2:Exit2, 3:Instant, 4:Interior, 5:Emergency24, 6:SilentPanic, 7:Water, 8:Gas, 9:Armdis |
| `Response` | integer |  | 응답(100ms) 1:빠름, 0:느림 |
| `Double` | integer |  | 1:사용 0:미사용 (zone double) |
| `Partition` | integer |  | bit 연산 [0]partition1, [1]partition2, [2]partition3, [3]partition4 |

---

### 스키마 `MCP_ZonesOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Zones` | array<MCP_ZoneOption> |  | MCP 존 옵션 목록 (8) |

---

### 스키마 `MapAreaInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MapCode` | integer |  |  |
| `Name` | string |  | 맵 명칭 |
| `PosX` | integer |  |  |
| `PosY` | integer |  |  |
| `ImageType` | string |  | 이미지 타입 |
| `ImageData` | string |  | 이미지 데이터 |

---

### 스키마 `MapAreaListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Count` | CountResultData |  |  |
| `MapAreaList` | MapAreaInfo |  |  |

---

### 스키마 `MealDataInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | string |  | 끼니 코드 |
| `Name` | string |  | 끼니 명칭 |
| `Type` | integer |  | 끼니 종류 1: 조식, 2: 중식, 3: 석식, 4: 간식, 5: 야간간식 |
| `Limit` | integer |  | 끼니 횟수 제한 |
| `StartTime` | string |  | 끼니 시작 시간 |
| `EndTime` | string |  | 끼니 종료 시간 |
| `Menu1` | string |  | 메뉴1 명칭 |
| `Menu1Price` | string |  | 메뉴1가격 |
| `Menu2` | string |  | 메뉴2 명칭 |
| `Menu2Price` | string |  | 메뉴2가격 |
| `Menu3` | string |  | 메뉴3 명칭 |
| `Menu3Price` | string |  | 메뉴3가격 |
| `Menu4` | string |  | 메뉴4 명칭 |
| `Menu4Price` | string |  | 메뉴4가격 |
| `StartTimeflag` | integer |  | 시작시간 당일,내일 flag |
| `EndTimeflag` | integer |  | 종료시간 당일,내일 flag |

---

### 스키마 `MealDataListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `MealData` | array<MealDataInfo> |  | 식수 끼니 리스트 |

---

### 스키마 `MealInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | string |  | 식수 코드 |
| `Name` | string |  | 식수 코드명 |
| `DayLimit` | integer |  | 일 제한 |
| `MonthLimit` | integer |  | 월 제한 |
| `StartAt` | string |  | 기간 제한 설정 시작일 YYYY-MM-DD hh:mm:ss |
| `EndAt` | string |  | 기간 제한 설정 종료일 YYYY-MM-DD hh:mm:ss |
| `MealDataCode1` | string |  | 첫번째 끼니코드 |
| `MealDataCode2` | string |  | 두번째 끼니코드 |
| `MealDataCode3` | string |  | 세번째 끼니코드 |
| `MealDataCode4` | string |  | 네번째 끼니코드 |
| `MealDataCode5` | string |  | 다섯번째 끼니코드 |

---

### 스키마 `MealListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Meal` | array<MealInfo> |  | 식수정보 리스트 |

---

### 스키마 `MealProcessReq`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MealProcessSetting` | MealProcessSetting |  |  |
| `ID` | UserIDList |  |  |

---

### 스키마 `MealProcessResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `TaskID` | TaskIDData |  |  |

---

### 스키마 `MealProcessSetting`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TaskID` | integer |  | 작업 ID |
| `Total` | integer |  | 선택된 사용자 갯수 |
| `Process` | integer |  | 처리상태 |
| `StartAt` | string |  | 처리작업 시작 일자 |
| `EndAt` | string |  | 처리작업 종료 일자 |

---

### 스키마 `MealResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `DateTime` | string |  | 발생일자 |
| `TerminalID` | integer |  | 단말기 아이디 |
| `UserID` | integer |  | 사용자 아이디 |
| `Type` | integer |  | 끼니 타입 |
| `Menu` | string |  | 메뉴 명칭 |
| `Pay` | string |  | 식수 금액 |
| `Result` | integer |  | 인증결과 |
| `UpMode` | integer |  | 단말기에서 인증기록 올라온 모드 |

---

### 스키마 `MealResultListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Total` | Total |  |  |
| `MealResult` | array<MealResult> |  | 식수결과 리스트 |

---

### 스키마 `MealStatisticsDay`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Day` | string |  | 날짜 |
| `Type` | integer |  | 끼니 타입 |
| `Count` | integer |  | 끼니 별 카운트 |

---

### 스키마 `MealStatisticsResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `MealStatisticsDay` | array<MealStatisticsDay> |  | 일자별 결과 |

---

### 스키마 `MealTotalStatus`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Total` | integer |  | 총합 횟수 |
| `Success` | integer |  | 식수 인증성공 횟수 |
| `Fail` | integer |  | 식수 인증실패 횟수 |
| `Amount` | integer |  | 기간 동안 식사 총합금액 |
| `CountByGroup` | array<CountByGroup> |  | 그룹별 사용자 수 |
| `MealStatisticsDay` | array<MealStatisticsDay> |  | 일자별 결과 |

---

### 스키마 `MealTotalStatusResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `MealTotalStatus` | object |  | 종합현황 |

---

### 스키마 `MenuGroup`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuGroupID` | integer |  | 메뉴 그룹 아이디 |
| `UserID` | integer |  | 메뉴 그룹 사용 관리자 ID |
| `Name` | string |  | 메뉴 그룹 Name |
| `PosX` | integer |  | 메뉴 그룹 X좌표 |
| `PosY` | integer |  | 메뉴 그룹 Y좌표 |

---

### 스키마 `MenuGroupsInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuGroup` | array<MenuGroup> |  | 메뉴그룹 목록 |

---

### 스키마 `MenuInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuID` | integer |  | 메뉴아이디 |
| `ParentID` | integer |  | 상위메뉴 아이디 |
| `Name` | string |  |  |
| `PosX` | integer |  | icon X좌표 |
| `PosY` | integer |  | icon Y좌표 |
| `Src` | string |  |  |
| `Image` | string |  |  |
| `LicenseCode` | integer |  | LicenseCode |
| `description` | string |  | 메뉴 설졍 |

---

### 스키마 `MenuUser`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuID` | integer |  | 메뉴 아이디 |
| `UserID` | integer |  | 사용자  사용자 ID |
| `GroupID` | integer |  | 메뉴 그룹 ID |
| `PosX` | integer |  | 메뉴 그룹 X좌표 |
| `PosY` | integer |  | 메뉴 그룹 Y좌표 |
| `AutoRun` | integer |  | 자동 실행 설정 |

---

### 스키마 `MenuUsersInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuUser` | array<MenuUser> |  | 사용자 메뉴 목록 |

---

### 스키마 `MenusInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MenuList` | array<MenuInfo> |  | 전체 메뉴 목록 |
| `MenuUser` | array<MenuUser> |  | 로그인 사용자 메뉴 목록 |
| `MenuGroup` | array<MenuGroup> |  | 로그인 사용자 메뉴그룹 목록 |

---

### 스키마 `MessageInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MessageID` | integer |  | 메시지 ID |
| `Message` | string |  | 사용자 메시지 |

---

### 스키마 `NoticeInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `NoticeID` | integer |  | 공지사항 ID |
| `Type` | integer |  | Type |
| `StartDate` | string |  | 시작일자 |
| `EndDate` | string |  | 종료일자 |
| `StartTime` | string |  | 시작시간 |
| `EndTime` | string |  | 종료시간 |
| `Message` | string |  | 공지사항 내용 |

---

### 스키마 `NoticeListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `NoticeList` | array<NoticeInfo> |  |  |

---

### 스키마 `NoticeResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `NoticeInfo` | NoticeInfo |  |  |

---

### 스키마 `OptionAuthInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `FpOrder` | integer |  | User finger sort order |
| `FpRegMax` | integer |  | Max fingerprint enrollment |
| `FpLfdLevel` | integer |  | Counterfeit fingerprint security level (0~9, 0=Do not use counterfeit fingerprint) |
| `FpVerifyLevel` | integer |  | 1:1 auth level(1~9) |
| `FpIdentifyLevel` | integer |  | 1:N auth level(1~9) |
| `FpSimilarLevel` | integer |  | Similar fingerprint security level (0~9, 0=Do not use similar fingerprint) |
| `FpDownloadCount` | integer |  | Fp Download Count |
| `RfRegMax` | integer |  | Maximum number of card registrations(1~5) |
| `SimilarFpCheck` | integer |  | Similar Fp Check |
| `SimilarFaCheck` | integer |  | Similar Face Check |
| `UserAccessControl` | integer |  | User Access Control |
| `AuthLogImagePopup` | integer |  | AuthLog Image Popup(0=not used, 1=used) |
| `FpSearchUser` | integer |  | Whether to use 1:N authentication(0=not used, 1=used) |

---

### 스키마 `OptionAuthList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AuthList` | OptionAuthInfo |  |  |

---

### 스키마 `OptionDDNSInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Used` | integer |  | DDNS Used  (0:not Used, 1:Used) |
| `HostName` | string |  | Host Name |
| `ContractNo` | string |  | Contract No |
| `UpdateTerm` | integer |  | Update cycle 0: 10min,   1: 20min,   2: 1hour,   3: 2hour,   4: 5hour,   5: 12hour |

---

### 스키마 `OptionDDNSList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `DDNSList` | OptionDDNSInfo |  |  |

---

### 스키마 `OptionDashboard`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | User ID |
| `WedgetID` | integer |  | Wedget ID |
| `Layout` | string |  | Layout |
| `Index` | integer |  | Index |

---

### 스키마 `OptionDashboardInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `OptionDashboard` | array<OptionDashboard> |  |  |

---

### 스키마 `OptionElevator`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TotalFloorCount` | integer |  | Sets the total number of floors in the building. (ex: (Ground) 10 floors + (Underground) 4 floors = Total number of floors: 14.) |
| `FirstFloor` | integer |  | Set which floor as the 1st floor in the total number of floors.(Ex: If you set ‘5’ as the 1st starting point in the total 14 floors, it can set as 10 floors (Ground) and 4 floors. (Underground)) |

---

### 스키마 `OptionElevatorInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `OptionElevator` | OptionElevator |  |  |

---

### 스키마 `OptionLogInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `SaveAuthlogPeriod` | integer |  | Authentication log storage period (1~365(day)) |
| `SaveSyslogPeriod` | integer |  | System log storage period (1~365(day)) |
| `SaveTerminallogPeriod` | integer |  | Terminal log storage period (1~365(day)) |
| `SaveOnlySuccess` | integer |  | Save success log only (0=not used, 1=used) |
| `CheckAuthlogDuplicate` | integer |  | Confirmation of duplicate authentication log (0=not used, 1=used) |
| `SyslogFilterOption` | boolean |  | Whether to save the system log |
| `SyslogFilterLogin` | boolean |  | Whether to save the client login log |
| `SyslogFilterUser` | boolean |  | Whether to save the user log |
| `SyslogFilterTerminal` | boolean |  | Whether to save the terminal log |
| `SyslogFilterGroup` | boolean |  | Whether to save the group log |
| `SyslogFilterPrivilege` | boolean |  | Whether to save the permission log |
| `SyslogFilterTna` | boolean |  | Whether to save T&A log |
| `SyslogFilterMeal` | boolean |  | Whether to store drinking water logs |
| `TlogFilterOption` | boolean |  | System option log saving |
| `TlogFilterUser` | boolean |  | Whether to save the user log |
| `TlogFilterNetwork` | boolean |  | Whether to save the network log |
| `TlogFilterDoorControl` | boolean |  | Whether to save log related to door |
| `TlogFilterWarningError` | boolean |  | Whether to save warning related logs |

---

### 스키마 `OptionLogList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `LogList` | OptionLogInfo |  |  |

---

### 스키마 `OptionMailInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Flag` | integer |  | mail userd 0:Not Used, 1:Used |
| `Security` | integer |  | Security 0:Not Used, 1:TLS, 2:SSL |
| `Host` | string |  | Host (mail Server) |
| `Port` | integer |  | Port |
| `User` | string |  | User ID |
| `UserPassword` | string |  | User Password |
| `From` | string |  | From |
| `Sender` | string |  | Sender |
| `To` | string |  | To (Multiple selection, classification example: unioncomm@co.kr,unioncomm@co.kr) |
| `Cc` | string |  | Cc |
| `Bcc` | string |  | Bcc |
| `Disconnect` | integer |  | Disconnect |
| `CoverOpen` | integer |  | Cover Open |
| `DoorPick` | integer |  | Door Pick |
| `MatchingFail` | integer |  | Matching Fail |
| `NotClose` | integer |  | Not Close |
| `NoPermission` | integer |  | No Permission |
| `LockError` | integer |  | Lock Error |
| `Duress` | integer |  | Duress |
| `Emergency` | integer |  | Emergency |
| `ExtSignal` | integer |  | Ext Signal |
| `AttachPicture` | integer |  | Attach Picture |
| `Blacklist` | integer |  | Blacklist Authentication attempt |
| `Medical` | integer |  | MCP-040 Medical Alarms |
| `FireAlarms` | integer |  | MCP-040 Fire Alarms |
| `PanicAlarms` | integer |  | MCP-040 Panics Alarms |
| `BurglarAlarms` | integer |  | MCP-040 Burglar Alarms |
| `GeneralAlarms` | integer |  | MCP-040 General Alarms |
| `HourNonBurglary` | integer |  | 24 HOUR (AUXILIARY) Alarm-24 Hr. Non-Burg-# |
| `SystemPeripheralTroubles` | integer |  | System Peripheral |
| `SounderTroubles` | integer |  | Sounder/Relay Troubles |
| `SystemTroubles` | integer |  | System Trouble |
| `FireSupervisory` | integer |  | Fire Supervisory |
| `CommDisables` | integer |  | Communication disable |
| `SystemPeripheralDisables` | integer |  | System peripheral disable |
| `SounderDisables` | integer |  | Sounder/Relay Disable |
| `SystemDisables` | integer |  | System disable |
| `AccessControl` | integer |  | Access Control |
| `RemoteAccess` | integer |  | Remote Access |
| `OpenClose` | integer |  | Open/Close |
| `Sensor` | integer |  | Sensor Trouble - Global |
| `ProtectionLoop` | integer |  | Protection Loop |
| `CommTroubles` | integer |  | Communication trobles |
| `Miscellaneous` | integer |  | Miscellaneous |
| `SpecialCodes` | integer |  | Special codes |
| `PersonnelMonitoring` | integer |  | Personnel monitoring |
| `Scheduling` | integer |  | Scheduling |
| `EventLog` | integer |  | Event log |
| `TestMisc` | integer |  | Manual Test |
| `Bypasses` | integer |  | Zone/Sensor Bypass |
| `Expand` | integer |  | Acu Expand |

---

### 스키마 `OptionMailList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `MailList` | OptionMailInfo |  |  |

---

### 스키마 `OptionSystemInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `DBVersion` | integer |  | DB version |
| `BrandType` | integer |  | Brand Type |
| `APBLevel` | integer |  | AntiPassback level |
| `MasterPW` | string |  | Master Password |
| `UserIDLength` | integer |  | User ID Length |
| `GuestIDRangeMin` | integer |  | Guest ID Range Min |
| `GuestIDRangeMax` | integer |  | Guest ID Range Max |
| `UserInfoEncrypt` | integer |  | User basic Info Encrypt |
| `AuthDataEncrypt` | integer |  | User Auth Data Encrypt |
| `TerminalEncrypt` | integer |  | Using encrypted packets |

---

### 스키마 `OptionSystemList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `SystemList` | OptionSystemInfo |  |  |

---

### 스키마 `OptionTNAInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AutoProc` | integer |  | Automatic time and attendance processing setting |
| `AutoProcTime` | integer |  | Auto attendance processing time |
| `MoneyDigit` | integer |  | Amount Display Decimal Places |
| `TimeShape` | integer |  | Time display format |
| `MinuteDigit` | integer |  | Time display decimal places |
| `SumPeriodType` | integer |  | Sum Period Type (unit) |
| `SumStartDay` | integer |  | Sum Start (Day) |
| `LastResultDate` | string |  | Last TNA Result Date |
| `LastSumDate` | string |  | Last Sum Date |
| `LastSumWeek` | integer |  | Last Sum Week |

---

### 스키마 `OptionTNAList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TNAList` | OptionTNAInfo |  |  |

---

### 스키마 `OptionTerminalInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AccessDefaultRestrict` | integer |  | Restriction of unspecified access group (0:permit, 1:restrict) |
| `FireRange` | integer |  | Control range (0: no terminal control, 1: group terminal control, 2: all terminal control) |
| `FireOpen` | integer |  | Door opening (0: Not set, 1: Set) |
| `FireAlarm` | integer |  | Alarm occurrence (0: Not set, 1: Set) |
| `FireFinish` | integer |  | Automatic shutdown of control at the end of the situation (0: not set, 1: set) |
| `PanicRange` | integer |  | Control range (0: no terminal control, 1: group terminal control, 2: all terminal control) |
| `PanicOpen` | integer |  | Door opening (0: Not set, 1: Set) |
| `PanicAlarm` | integer |  | Alarm occurrence (0: Not set, 1: Set) |
| `PanicFinish` | integer |  | Automatic shutdown of control at the end of the situation (0: not set, 1: set) |
| `CrisisRange` | integer |  | Control range (0: no terminal control, 1: group terminal control, 2: all terminal control) |
| `CrisisOpen` | integer |  | Door opening (0: Not set, 1: Set) |
| `CrisisAlarm` | integer |  | Alarm occurrence (0: Not set, 1: Set) |
| `CrisisFinish` | integer |  | Automatic shutdown of control at the end of the situation (0: not set, 1: set) |

---

### 스키마 `OptionTerminalList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalList` | OptionTerminalInfo |  |  |

---

### 스키마 `OptionUserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalUserSync` | integer |  | Automatic Sync of Device Users (0=not used , 1=used) |
| `TerminalUserUploadOverwrite` | integer |  | Overwriting when the terminal user uploads (0=not used , 1=used) |
| `PasswordPeriod` | integer |  | Change User Password cycle (Unit-day, 0=not used) |
| `AuthFailCount` | integer |  | Continuous Authentication Failure Blocking (Unit-min, 0=not used) |
| `PwChangeFirst` | integer |  | Password change at first login (0=not used , 1=used) |
| `PwNotAllowOld` | integer |  | Whether to allow the use of old passwords (0=not used , 1=used) |
| `PwNotAllowDuplicateChar` | integer |  | Whether to allow the same character sequence when setting the password (0=not used , 1=used) |
| `PwNotAllowSameID` | integer |  | Whether to allow the same password as ID (0=not used , 1=used) |
| `PwRequiredUpper` | integer |  | Password contains uppercase letters (0=not used , 1=used) |
| `PwRequiredLower` | integer |  | Password contains lowercase letters (0=not used , 1=used) |
| `PwRequiredNum` | integer |  | Password contains numbers (0=not used , 1=used) |
| `PwRequiredSymbol` | integer |  | Password contains special characters (0=not used , 1=used) |

---

### 스키마 `OptionUserList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserList` | OptionUserInfo |  |  |

---

### 스키마 `OutBasicInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | integer |  | 위겐드Out 구분 코드 |
| `Name` | string |  | 위겐드OUt 명칭 |
| `Bits` | integer |  | Bit Length 와 Custom Size 설정값 (0: unused, 1~128: 기타 커스텀 사이즈, 129: 표준 26bit, 130: 표준 34bit) |
| `Port` | integer |  | PortState (0: Active Low(기본), 1: Active High) |
| `ParityCount` | integer |  | Bit 길이에서 커스텀 사이즈 선택 시 범위 지정 (범위: 1 ~ 128bit) |
| `SendFail` | integer |  | 인증성공 시 외 실패신호까지 전송 할 경우(0:Not Anything, 1:Send Fail Data, 2:Invert Parity 3:Card Serial) |
| `SendData` | integer |  | 0:사용자 아이디, 1:카드번호 |
| `PulseInterval` | integer |  | 0 (설정하지 않을 경우 보통 2ms) |
| `PulseWidth` | integer |  | 0 (설정하지 않을 경우 보통 50μs) |
| `SiteCode` | integer |  | 사용자 별도 지정이 필요 할 경우 설정 (단말기 설정 범위 : 0~255, UNIS에서는 그 외 범위 입력 가능) |
| `FailID` | integer |  | Send Fail 설정이 [Send Fail Data] 일 경우 실패신호 전송 데이터 포맷을 지정 |
| `MaskSiteCode` | string |  | SetField에 설정된 SiteCode 위치 |
| `MaskUserID` | string |  | SetField에 설정된 Data(ID) 위치 |
| `MaskFixed0` | string |  | SetField에 설정된 (Fixed 0) 위치 |
| `MaskFixed1` | string |  | SetField에 설정된 (Fixed 1) 위치 |

---

### 스키마 `Parity`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 1: "O(Odd Parity)", 2: "E(Even Parity)" |
| `Position` | integer |  | SetField 위치 |
| `MaskBits` | string |  | Set Perity 위치 지정 |

---

### 스키마 `PdaAuth`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `cardNum` | string |  |  |
| `picture` | string |  |  |

---

### 스키마 `PictureInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ImageType` | string |  | 이미지 타입 |
| `ImageData` | string |  | 이미지 데이터 (base64) |
| `Thumbnail` | string |  | 썸네일 이미지 데이터 (base64) |

---

### 스키마 `PositionInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `PositionID` | integer |  | 직급 ID |
| `Name` | string |  | 직급 이름 |

---

### 스키마 `PositionInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `PositionInfo` | PositionInfo |  |  |

---

### 스키마 `PositionsResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `PositionList` | array<PositionInfo> |  |  |

---

### 스키마 `PrivilegeAccessControl`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 출입그룹 관리 허용 |
| `Set` | integer |  | 출입그룹 설정 |

---

### 스키마 `PrivilegeBlacklist`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 블랙 리스트 관리 허용 |
| `Change` | integer |  | 블랙 리스트 변경 |
| `Release` | integer |  | 블랙 리스트 초기화 |
| `Update` | integer |  | 블랙 리스트 수정 |
| `Delete` | integer |  | 블랙 리스트 삭제 |
| `Apply` | integer |  | 블랙 리스트 적용 |

---

### 스키마 `PrivilegeGroup`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 그룹 관리 허용 |
| `Regist` | integer |  | 그룹 등록 |
| `Update` | integer |  | 그룹 수정 |
| `Delete` | integer |  | 그룹 삭제 |
| `User` | integer |  | 사용자 그룹 변경 |

---

### 스키마 `PrivilegeGuest`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 방문객 관리 허용 |
| `Regist` | integer |  | 방문객 등록 |
| `Update` | integer |  | 방문객 수정 |
| `Delete` | integer |  | 방문객 삭제 |

---

### 스키마 `PrivilegeInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `PrivilegeID` | integer |  | 권한 ID |
| `Name` | string |  | 권한 이름 |
| `description` | string |  | 설명 |
| `Monitoring` | PrivilegeMonitoring |  |  |
| `Terminal` | PrivilegeTerminal |  |  |
| `User` | PrivilegeUser |  |  |
| `Group` | PrivilegeGroup |  |  |
| `Guest` | PrivilegeGuest |  |  |
| `Blacklist` | PrivilegeBlacklist |  |  |
| `AccessControl` | PrivilegeAccessControl |  |  |
| `Map` | PrivilegeMap |  |  |
| `TNA` | PrivilegeTNA |  |  |
| `Log` | PrivilegeLog |  |  |
| `Meal` | PrivilegeMeal |  |  |
| `Option` | PrivilegeOption |  |  |

---

### 스키마 `PrivilegeLog`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 로그 관리 허용 |
| `Delete` | integer |  | 로그 삭제 |
| `BackupRestore` | integer |  | 로그 백업 및 복원 |

---

### 스키마 `PrivilegeMap`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 사이트맵 관리 허용 |
| `Set` | integer |  | 사이트맵 설정 |

---

### 스키마 `PrivilegeMeal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 식수 관리 허용 |
| `DeleteResult` | integer |  | 결과 삭제 |
| `ViewGroup` | integer |  | 그룹별 조회 |
| `ViewPersonal` | integer |  | 개인별 조회 |
| `Set` | integer |  | 식수 설정 |

---

### 스키마 `PrivilegeMonitoring`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 모니터링 권한 허용 |
| `Client` | integer |  | 클라이언트 모니터링 |
| `TerminalStatus` | integer |  | 단말기 상태 모니터링 |
| `Auth` | integer |  | 인증로그 모니터링 |
| `Event` | integer |  | 이벤트(시스템)로그 모니터링 |

---

### 스키마 `PrivilegeOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 옵션 관리 허용 |
| `Local` | integer |  | 클라이언트 관련 옵션 |
| `Server` | integer |  | 서버 관련 옵션 |
| `Password` | integer |  | 암호 관리 |
| `Mail` | integer |  | e-mail 관리 |
| `TNA` | integer |  | 근태 관리 |

---

### 스키마 `PrivilegeTNA`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 근태 관리 허용 |
| `Set` | integer |  | 근태 설정 |
| `Special` | integer |  | 특별근무 지정 |
| `Manage` | integer |  | 근태 관리 |
| `OutState` | integer |  | 근무 현황 조회 |
| `OutExcRecord` | integer |  | 제외 기록 조회 |
| `summary` | integer |  | 집계 관리 |
| `SendResult` | integer |  | 외부 전송 |
| `DeleteResult` | integer |  | 근태 결과 삭제 |

---

### 스키마 `PrivilegeTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 단말기 권한 허용 |
| `Regist` | integer |  | 단말기 등록 |
| `Update` | integer |  | 단말기 수정 |
| `Delete` | integer |  | 단말기 삭제 |
| `FW` | integer |  | 단말기 펌웨어 업데이트 |
| `Option` | integer |  | 단말기 옵션 수정 |
| `SetManager` | integer |  | 관리자 설정 |
| `UserFile` | integer |  | 단말기 사용자 파일 관리 |

---

### 스키마 `PrivilegeUser`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Permit` | integer |  | 사용자 관리 허용 |
| `Regist` | integer |  | 사용자 등록 |
| `Update` | integer |  | 사용자 수정 |
| `Delete` | integer |  | 사용자 삭제 |
| `TerminalUser` | integer |  | 단말기 사용자 관리 |
| `RegistAdmin` | integer |  | 관리자 등록 |

---

### 스키마 `PublicNotice`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `NoticeID` | integer |  | 공지 번호 |
| `Type` | integer |  | 0:설정, 1:초기화 |
| `StartDate` | string |  | 시작일 YYYYMMdd |
| `EndDate` | string |  | 종료일 YYYYMMdd |
| `StartTime` | string |  | 시작 시간 HH:mm |
| `EndTime` | string |  | 종료 시간 HH:mm |
| `Message` | string |  | 공지 문구 |
| `TerminalID` | array<integer> |  | 적용할 단말기 아이디 |

---

### 스키마 `RegUsersTotal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Count` | integer |  |  |

---

### 스키마 `ResponseResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |

---

### 스키마 `Result`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ResultCode` | integer |  |  |

---

### 스키마 `ResultClientKeyInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `LicenseInfo` | ClientKeyInfo |  |  |

---

### 스키마 `ResultLicenseInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `LicenseInfo` | LicenseInfo |  |  |

---

### 스키마 `SystemInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Version` | string |  | 서버 버전 정보 |
| `LicenseLevel` | integer |  | 라이센스 레벨 |
| `BrandType` | integer |  | 서버 브랜드 타입 |
| `TimezoneVersion` | integer |  | 타임존 버전 |
| `HTTPSFlag` | integer |  | HTTP Flag |

---

### 스키마 `TNA_Absenteeism`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 이름 |
| `UniqueID` | string |  | 고유값 |
| `GroupID` | integer |  | 그룹 코드 |
| `Position` | integer |  | 직급 코드 |
| `WorkDate` | string |  | 근무일 |
| `Day` | string |  | 요일 |
| `ShiftCode` | string |  | 근태 코드 |
| `ArrivalTime` | integer |  | 출근 시간 |
| `DepartureTime` | integer |  | 퇴근 시간 |

---

### 스키마 `TNA_EarlyDeparture`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 이름 |
| `UniqueID` | string |  | 고유값 |
| `GroupID` | integer |  | 그룹 코드 |
| `Position` | integer |  | 직급 코드 |
| `WorkDate` | string |  | 근무일 |
| `Day` | string |  | 요일 |
| `ShiftCode` | string |  | 근태 코드 |
| `ArrivalTime` | integer |  | 출근 시간 |
| `DepartureTime` | integer |  | 퇴근 시간 |
| `EarlyTime` | integer |  | 조퇴 시간 |

---

### 스키마 `TNA_LateArrival`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 이름 |
| `UniqueID` | string |  | 고유값 |
| `GroupID` | integer |  | 그룹 코드 |
| `Position` | integer |  | 직급 코드 |
| `WorkDate` | string |  | 근무일 |
| `Day` | string |  | 요일 |
| `ShiftCode` | string |  | 근태 코드 |
| `ArrivalTime` | integer |  | 출근 시간 |
| `DepartureTime` | integer |  | 퇴근 시간 |
| `LateTime` | integer |  | 지각 시간 |

---

### 스키마 `TNA_PaymentConfig`

초과근무

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | string |  | 지급액 코드 |
| `Name` | string |  | 지급액 명 |
| `Unit` | integer |  | 지급액 정산 단위 0:시간 단위, 1:30분 단위, 2:15분 단위, 3:10분 단위, 4:1분 단위 |
| `NormalTime` | integer |  | 기본근무 |
| `TimeBefore` | integer |  | 조기근무 |
| `Overtime1` | integer |  | 연장근무 |
| `Overtime2` | integer |  | 야간근무 |
| `OffDayHours` | integer |  | 휴일근무 |
| `Overtime3` | integer |  |  |

---

### 스키마 `TNA_Result`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `WorkDate` | string |  | 근무 날짜 |
| `UserID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 명 |
| `UniqueID` | string |  | 고유값 |
| `GroupID` | integer |  | 그룹 코드 |
| `ShiftCode` | string |  | 근태 코드 |
| `ShiftName` | string |  | 근태 코드명 |
| `Complete` | integer |  | 근태 처리 완료 여부 0:미완료, 1:완료 |
| `WorkState` | integer |  | 근태 타입 0:무시, 1:출근, 2:결근 |
| `InTime` | integer |  | 출근 시간 |
| `OutTime` | integer |  | 퇴근 시간 |
| `LateTime` | integer |  | 지각 시간 |
| `LackTime` | integer |  | 조퇴 시간 |
| `MultiRange` | integer |  | 다중 근태 시간 0:미적용, 1:적용 |
| `Worktime1In` | integer |  | 기본 시작 |
| `Worktime1Out` | integer |  | 기본 종료 |
| `Worktime1Late` | integer |  | 기본 지각 |
| `Worktime1Lack` | integer |  | 기본 조퇴 |
| `Worktime1Time` | integer |  | 기본 근무 |
| `Worktime2In` | integer |  | 조기 시작 |
| `Worktime2Out` | integer |  | 조기 종료 |
| `Worktime2Late` | integer |  | 조기 지각 |
| `Worktime2Lack` | integer |  | 조기 조퇴 |
| `Worktime2Time` | integer |  | 조기근무 |
| `Worktime3In` | integer |  | 연장 시작 |
| `Worktime3Out` | integer |  | 연장 종료 |
| `Worktime3Late` | integer |  | 연장 지각 |
| `Worktime3Lack` | integer |  | 연장 조퇴 |
| `Worktime3Time` | integer |  | 연장 근무 |
| `Worktime4In` | integer |  | 야간 시작 |
| `Worktime4Out` | integer |  | 야간 종료 |
| `Worktime4Late` | integer |  | 야간 지각 |
| `Worktime4Lack` | integer |  | 야간 조퇴 |
| `Worktime4Time` | integer |  | 야간 근무 |
| `Worktime5In` | integer |  | 휴일 시작 |
| `Worktime5Out` | integer |  | 휴일 종료 |
| `Worktime5Late` | integer |  | 휴일 지각 |
| `Worktime5Lack` | integer |  | 휴일 조퇴 |
| `Worktime5Time` | integer |  | 휴일 근무 |
| `Worktime6In` | integer |  | 초과 시작 |
| `Worktime6Out` | integer |  | 초과 종료 |
| `Worktime6Late` | integer |  | 초과 지각 |
| `Worktime6Lack` | integer |  | 초과 조퇴 |
| `Worktime6Time` | integer |  | 초과 근무 |
| `PayMoney` | integer |  | 금액 |
| `Modify` | integer |  | 수정 |
| `Remark` | string |  | 비고 |

---

### 스키마 `TNA_ScheduleConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | string |  | 근무 형태 등록 |
| `Name` | string |  | 근무 형태 이름 |
| `BasicDay` | string |  | 기준 일자 (YYYYMMDD) |
| `HolidayCode` | string |  | 공휴일 코드 |
| `HoliShift` | string |  | 공휴일 근무 코드 |
| `SpinCount` | integer |  | 설정 일수 (1..30) |
| `ShiftCode` | string |  | 요일별 근무 코드 지정 (4 * 30 days) |
| `WorkTime` | array<TNA_ScheduleWorkTime> |  | 근태 처리 시 상세 설정 |
| `SummTime` | array<TNA_ScheduleSummTime> |  | 집계 처리 시 상세 설정 |

---

### 스키마 `TNA_ScheduleSummTime`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 근무 타입 0:기본근무 상세 설정, 1:조기근무 상세 설정, 2:연장근무 상세 설정, 3:야간근무 상세 설정, 4:휴일근무 상세 설정, 5:초과근무 상세 설정 |
| `AddTime` | integer |  | 집계 시 추가 시간 (분) |
| `AddCondi` | integer |  | 추가 조건 최소 근무일수 |
| `DelTime` | integer |  | 집계 시 공제 시간 |
| `DelCondi` | integer |  | 공제 조건 최소 근무일수 |
| `Min` | integer |  | 집계 최소 시간 |
| `Max` | integer |  | 집계 최대 시간 |
| `Trans` | integer |  | 집계 시간 다른 근무시간에 합산 0:지정없음, 1:기본근무, 2:조기근무 3:연장근무 4:야근근무, 5:휴일근무, 6:초과근무 |

---

### 스키마 `TNA_ScheduleWorkTime`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 근무 타입 0:기본근무 상세 설정, 1:조기근무 상세 설정, 2:연장근무 상세 설정, 3:야간근무 상세 설정, 4:휴일근무 상세 설정, 5:초과근무 상세 설정 |
| `Unit` | integer |  | 시간 산출 단위 0:분단위 모두적용, 1: 10분단위 버림, 2:10분단위 반올림, 3:15분단위 버림, 4:15분단위 반올림, 5:30분단위 버림, 6:30분단위 반올림, 7:60분단위 버림, 8:60분단위 반올림 |
| `AddTime` | integer |  | 추가 시간 (분) |
| `AddCondi` | integer |  | 추가 조건 최소 근무 시간 (분) |
| `DelTime` | integer |  | 공제 시간 (분) |
| `DelCondi` | integer |  | 공제 조건 최소 근무 시간 (분) |
| `Min` | integer |  | 최소 시간 (분) |
| `Max` | integer |  | 최대 시간 예)99 시간은 5940 |
| `Rate` | integer |  | 시간 할증 |

---

### 스키마 `TNA_SepcialShift`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `WorkDate` | string |  | 근무일 (yyyyMMdd) |
| `UserID` | integer |  | 사용자 아이디 |
| `ShiftCode` | string |  | 근무 코드 |

---

### 스키마 `TNA_ShiftConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | string |  | 근무 시간 코드 |
| `Name` | string |  | 근무 시간 이름 |
| `InOutMode` | integer |  | 출퇴근 인증 모드 0:모든 기록 인정, 1:출퇴근 기록만 인정 |
| `WorkStartTime` | integer |  | 당일 근태 처리 구간 시작 시간 |
| `WorkEndTime` | integer |  | 당일 근태 처리 구간 종료 시간 |
| `IgnoreAbsent` | integer |  | 결근시 무시함(휴일에 적용) 0:미설정, 1:설정 |
| `LateTime` | integer |  | 지각 처리 시각 (-1:No, 0~4320) |
| `LackTime` | integer |  | 조퇴 처리 시각 (-1:No, 0~4320) |
| `AutoInTime` | integer |  | 출근 자동 생성 (-1: No, 0 ~ 4320: Insertion time) |
| `AutoOutTime` | integer |  | 퇴근 자동 생성 (-1: No, 0 ~ 4320: Insertion time) |
| `SetExceptTime` | TNA_ShiftExceptTime |  | 고정 제외 시간 설정 |
| `MultiRange` | integer |  | 다중 출퇴근 구간 적용 0:미사용 1:사용 |
| `SetMultiRange` | TNA_ShiftMultiRange |  | 다중 출퇴근 구간 설정 |
| `SetShiftTime` |  |  | 근무 시간 설정 |

---

### 스키마 `TNA_ShiftExceptTime`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ExceptExit` | integer |  | 외출 시간 제외 1 0:미사용 1:사용 |
| `ExceptReturnMode` | integer |  | 복귀 모드 (0:모든 기능 인정 1:복귀 기록만 인정) |
| `ExceptOut` | integer |  | 중퇴 시간 제외 0:미사용 1:사용 |
| `ExceptInMode` | integer |  | 출근 모드 (0:모든 기록 인정 1:출근 기록만 인정) |
| `Fixed1StartTime` | integer |  | 제외 1 시작 시간 |
| `Fixed1EndTime` | integer |  | 제외 1 종료 시간 |
| `Fixed2StartTime` | integer |  |  |
| `Fixed2EndTime` | integer |  |  |
| `Fixed3StartTime` | integer |  |  |
| `Fixed3EndTime` | integer |  |  |
| `Fixed4StartTime` | integer |  |  |
| `Fixed4EndTime` | integer |  |  |
| `Fixed5StartTime` | integer |  |  |
| `Fixed5EndTime` | integer |  |  |

---

### 스키마 `TNA_ShiftMultiRange`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Range1StartTime` | integer |  | 구간 1 시작 시간 |
| `Range1EndTime` | integer |  | 구간 2 종료 시간 |
| `Range2StartTime` | integer |  |  |
| `Range2EndTime` | integer |  |  |
| `Range3StartTime` | integer |  |  |
| `Range3EndTime` | integer |  |  |
| `Range4StartTime` | integer |  |  |
| `Range4EndTime` | integer |  |  |

---

### 스키마 `TNA_ShiftTime`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Work` | integer |  | 근무 지정 |
| `Type` | integer |  | 시간 지정 |
| `StartTime` | integer |  | 시작 시간 |
| `EndTime` | integer |  | 종료 시간 |
| `Range` | integer |  | 적용 구간 |
| `AutoOut` | integer |  | 구간내 퇴근 부재시 자동 처리 |
| `Unit` | integer |  | 시간 산출 단위 |
| `MinTime` | integer |  | 최소 시간 |
| `MaxTime` | integer |  | 최대 시간 |
| `Rate` | integer |  | 적용 구간 |

---

### 스키마 `TNA_SumResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `SumDate` | string |  | 집계 기간 (YYYY9999: 년 단위, YYYYMM99: 월 단위, YYYYMM9x: 주 단위) |
| `UserID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 이름 |
| `UniqueID` | string |  | 고유값 |
| `GroupID` | integer |  | 그룹 코드 |
| `ScheduleCode` | string |  | 근태 코드 |
| `ScheduleName` | string |  | 근태 코드명 |
| `StartDate` | string |  | 집계 시작일 |
| `EndDate` | string |  | 집게 종료일 |
| `LateTime` | integer |  | 지각 시간 |
| `LackTime` | integer |  | 조퇴 시간 |
| `SumTime1Late` | integer |  | 기본 지각 시간 |
| `SumTime1Lack` | integer |  | 기본 조퇴 시간 |
| `SumTime1Time` | integer |  | 기본 근무 시간 |
| `SumTime2Late` | integer |  | 조기 지각 시간 |
| `SumTime2Lack` | integer |  | 조기 조퇴 시간 |
| `SumTime2Time` | integer |  | 조기 근무 시간 |
| `SumTime3Late` | integer |  | 연장 지각 시간 |
| `SumTime3Lack` | integer |  | 연장 조퇴 시간 |
| `SumTime3Time` | integer |  | 연장 근무 시간 |
| `SumTime4Late` | integer |  | 야간 지각 시간 |
| `SumTime4Lack` | integer |  | 야간 조퇴 시간 |
| `SumTime4Time` | integer |  | 야간 근무 시간 |
| `SumTime5Late` | integer |  | 휴일 지각 시간 |
| `SumTime5Lack` | integer |  | 휴일 조퇴 시간 |
| `SumTime5Time` | integer |  | 휴일 근무 시간 |
| `SumTime6Late` | integer |  | 초과 지각 시간 |
| `SumTime6Lack` | integer |  | 초과 조퇴 시간 |
| `SumTime6Time` | integer |  | 초과 근무 시간 |
| `PayMoney` | integer |  | 금액 |
| `Modify` | integer |  | 수정 |
| `Remark` | integer |  | 비고 |

---

### 스키마 `TNA_WorkConfig`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `AutoProc` | integer |  | 0:미사용, 1:자동 근태 처리 |
| `AutoProcTime` | integer |  | 자동 근태 처리 시간 (0 ~ 4320 = 처리 ==> 시간 앞 표기에 따라 +:다음날 처리때 오늘 날짜로, -:어제 처리한 결과 오늘 날짜로) |
| `MoneyDigit` | integer |  | 금액 표시 소수점 자릿수 |
| `TimeShape` | integer |  | 시간 표시 형태 (0:시분 형태, 1:숫자 형태) |
| `MinuteDigit` | integer |  | 시간 표시 소수점 자리수, 숫자 형태 표시 시 입력 |
| `SumPeriodType` | integer |  | 집계 기간 단위 (0:월 단위, 1: 1주 단위, 2:2주 단위) |
| `SumStartDay` | integer |  | 집계 시작일 (월단위:일, 주단위: 1Sunday~7Saturday) |
| `LastResultDate` | string |  | 마지막 근태 처리일 (YYYYMMDD) |
| `LastSumDate` | string |  | 마지막 집계 처리일 (YYYYMMDD) |
| `LastSumWeek` | integer |  | 마지막 집계 처리 주 |
| `NeisUsed` | integer |  | Neis 연동 |
| `NeisSavePath` | string |  | Neis 파일 저장 위치 |

---

### 스키마 `TNA_WorkTimebyPeriodResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `WorkTimeList` | array<WorkTimeList> |  |  |

---

### 스키마 `TaskIDData`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 등록된 테스크 ID |

---

### 스키마 `TerminalAPBFullInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  |  |
| `AreaIn` | APBAreaInfo |  |  |
| `AreaOut` | APBAreaInfo |  |  |
| `SoftPassBack` | boolean |  |  |

---

### 스키마 `TerminalAPBInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 ID |
| `AreaIn` | integer |  | 입구 영역 ID |
| `AreaOut` | integer |  | 출구 영역 ID |
| `SoftPassBack` | boolean |  | soft-passback(anti-passback 확인을 하지만 인증 성공 시 무조건 출입 허용) 여부 |

---

### 스키마 `TerminalAdminSave`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | array<integer> |  | 관리자를 저장할 터미널 ID 목록 |
| `Mode` | integer |  | 모드 |

---

### 스키마 `TerminalAdmins`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | array<integer> |  | 단말기 목록 |
| `Mode` | integer |  |  |

---

### 스키마 `TerminalAlarmInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `AlarmOptionList` | array<WebAlarm> |  |  |

---

### 스키마 `TerminalAlarmOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Alarms` | array<AlarmConfig> |  |  |

---

### 스키마 `TerminalApbAreaInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `AreaIn` | integer |  | 안티패스백 구역 입구 |
| `AreaInName` | string |  | 안티패스백 구역입구 명칭 |
| `AreaOut` | integer |  | 안티패스백 구역출구 |
| `AreaOutName` | string |  | 안티패스백 구역출구 명칭 |
| `SoftPassback` | integer |  | 소프트패스백 사용/미사용 |

---

### 스키마 `TerminalBasicOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Bright` | integer |  | 단말기 밝기 |
| `Contrast` | integer |  | 단말기 대조 |
| `Gain` | integer |  |  |
| `UserKey` | integer |  |  |
| `UserIDLength` | integer |  | 사용자 아이디 길이 |
| `VerifyLevel` | integer |  | Verify 레벨 |
| `IdentifyLevel` | integer |  | Indetify 레벨 |
| `PassbackLevel` | integer |  | 안티패스백 레벨 |
| `LimitedLevel` | integer |  |  |
| `MicLevel` | integer |  | 마이크 레벨 |
| `Volume` | integer |  | 볼륨 |
| `AutoEnter` | integer |  | 자동 엔터키 사용 |
| `OperateMode` | integer |  |  |

---

### 스키마 `TerminalDoorControl`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Option` | integer |  | 0:일시개방, 1:계속 문열림, 2:잠금 |

---

### 스키마 `TerminalHolidayOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Holidays` | array<HolidayConfig> |  | 단말기 휴일 목록 |

---

### 스키마 `TerminalIDList`

- **type**: `array`

---

### 스키마 `TerminalIDs`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalIDs` | array<integer> |  | 단말기 아이디 목록 |

---

### 스키마 `TerminalImage`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `FileType` | string |  | 파일 확장자 |
| `FileSize` | integer |  | 파일 사이즈 |
| `ImageData` | string |  | 파일 데이터 |

---

### 스키마 `TerminalInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Name` | string |  | 단말기 이름 |
| `GroupID` | integer |  | 그룹 코드 |
| `State` | integer |  | 단말기 상태 |
| `Type` | integer |  | 단말기 모델명 |
| `FuncType` | integer |  | 기능 타입 0:출입통제, 1:근태, 2:식수 |
| `IPAddress` | string |  | 단말기 아이피 주소 |
| `MacAddress` | string |  | 단말기 맥주소 |
| `Version` | string |  | 단말기 펌웨어 버전 |
| `RemoteDoor` | integer |  | 출입문 원격 제어 범위 0:모두 허용, 1:모두 허용 안함, 2: 일시개방만 허용 |
| `UTCIndex` | integer |  | 타임존 |
| `description` | string |  | 기타 사항 |

---

### 스키마 `TerminalInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `TerminalInfo` | TerminalInfo |  |  |
| `TerminalApbAreaInfo` | TerminalApbAreaInfo |  |  |
| `TerminalImage` | TerminalImage |  |  |

---

### 스키마 `TerminalListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Total` | Total |  |  |
| `TerminalInfo` | array<TerminalInfo> |  |  |

---

### 스키마 `TerminalLockControl`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 아이디 |
| `Status` | integer |  | 0:열림, 1:잠금 |
| `Type` | integer |  | 0:기본, 1: 단말기 폐쇄 |

---

### 스키마 `TerminalLockOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Schedules` | array<LockConfig> |  | 단말기 락 스케줄 목록 |

---

### 스키마 `TerminalLockOptionResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `LockOptionInfo` | TerminalLockOption |  |  |

---

### 스키마 `TerminalMealInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `MealOptValue` | TerminalMealOption |  |  |

---

### 스키마 `TerminalMealOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `BStartHour` | integer |  | 조식 시작시간의 시간값 |
| `BStartMinute` | integer |  | 조식 시작시간의 분값 |
| `BEndHour` | integer |  | 조식 종료시간의 시간값 |
| `BEndMinute` | integer |  | 조식 종료시간의 분값 |
| `LStartHour` | integer |  | 중식 시작시간의 시간값 |
| `LStartMinute` | integer |  | 중식 시작시간의 분값 |
| `LEndHour` | integer |  | 중식 종료시간의 시간값 |
| `LEndMinute` | integer |  | 중식 종료시간의 분값 |
| `DStartHour` | integer |  | 중식 종료시간의 시간값 |
| `DStartMinute` | integer |  | 중식 종료시간의 분값 |
| `DEndHour` | integer |  | 석식 종료시간의 시간값 |
| `DEndMinute` | integer |  | 석식 종료시간의 분값 |
| `LsStartHour` | integer |  | 석식 시작시간의 시간값 |
| `LsStartMinute` | integer |  | 석식 시작시간의 분값 |
| `LsEndHour` | integer |  | 석식 종료시간의 시간값 |
| `LsEndMinute` | integer |  | 석식 종료시간의 분값 |
| `SStartHour` | integer |  | 석식 시작시간의 시간값 |
| `SStartMinute` | integer |  | 석식 시작시간의 분값 |
| `SEndHour` | integer |  | 석식 종료시간의 시간값 |
| `SEndMinute` | integer |  | 석식 종료시간의 분값 |
| `MonthLimit` | integer |  | 고정값 (0) |
| `DayLimit` | integer |  | 고정값 (0) |
| `Duplicate` | integer |  | 중복인증 허용 flag |
| `MealName` | string |  | 고정값 (') |

---

### 스키마 `TerminalNetworkOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 네트워크 타입 0:TCP, 1:UDP |
| `IP` | string |  | 아이피 주소 |
| `Subnet` | string |  | 서브넷 |
| `Gateway` | string |  | 게이트웨이 |
| `ServerIP` | string |  | 서버 아이피 주소 |
| `ServerPort` | integer |  | 서버 포트 |

---

### 스키마 `TerminalSetEmergency`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 아이디 |
| `Status` | integer |  | 0:설정, 1:종료 |
| `Type` | integer |  | 0:기본, 1:화재, 2:패닉, 3:응급 |

---

### 스키마 `TerminalSystemOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Language` | integer |  |  |
| `UseVoice` | integer |  |  |
| `UseBeep` | integer |  |  |
| `DoorOpenDuration` | integer |  |  |
| `DoorOpenWarning` | integer |  |  |
| `EncryptionType` | integer |  |  |
| `UseLog` | integer |  |  |
| `UseRF` | integer |  |  |
| `UseWiegand` | integer |  |  |
| `UseFunction` | integer |  |  |
| `TerminalMode` | integer |  |  |
| `NetworkTimeout` | integer |  |  |
| `TimezoneCode` | integer |  |  |
| `UseTimezone` | integer |  |  |
| `UseServerAuthentication` | integer |  |  |

---

### 스키마 `TerminalTinyInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Name` | string |  | 단말기 이름 |
| `Type` | integer |  | 단말기 타입 |

---

### 스키마 `TerminalTinyList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `total` | integer |  |  |
| `terminals` | array<TerminalTinyInfo> |  |  |

---

### 스키마 `TerminalUserCount`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TotalCount` | integer |  | 단말기 사용자 전체 카운트 |

---

### 스키마 `TerminalUserData`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Users` | array<UserInfo> |  | 단말기 사용자 목록 |

---

### 스키마 `TerminalUserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserInfos` | array<UserSimpleInfo> |  | 단말기 사용자 전체 데이터 |

---

### 스키마 `TerminalUserInfos`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalInfos` | array<TerminalsIdNameInfo> |  | 단말기 Simple info |
| `UserInfos` | array<UserSimpleInfo> |  | 사용자 Simple info |

---

### 스키마 `TerminalUserRequest`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Terminals` | array<integer> |  | 단말기 목록 |
| `Users` | array<string> |  | 사용자 목록 |
| `ForceType` | integer |  | 단말기 상태 오류 발생 시 처리 방법 (0=요청작업 진행하지 않음, 1=동기화 오류로 처리 후 다음 작업 진행, 2=단말기 상태가 정상으로 돌아오면 자동 동기화) |

---

### 스키마 `TerminalUserTinyInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Name` | string |  | 단말기 이름 |

---

### 스키마 `TerminalUserTinyListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `TerminalUserTinyList` | array<TerminalUserTinyInfo> |  |  |

---

### 스키마 `TerminalVoipOption`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `SvrAddress` | string |  | 서버 주소 |
| `AccountId` | string |  | 접속 계정(id) |
| `AccountPwd` | string |  | 접속 패스워드(password) |

---

### 스키마 `TerminalsIdNameInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 단말기 아이디 |
| `Name` | string |  | 단말기 이름 |

---

### 스키마 `TimeHHmmHHmm`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `StartHour` | integer |  | 시작일 시간 |
| `StartMinute` | integer |  | 시작일 분 |
| `EndHour` | integer |  | 종료일 시간 |
| `EndMinute` | integer |  | 종료일 분 |

---

### 스키마 `TimelinePutTimelineInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TimelineID` | integer |  |  |
| `Name` | string |  |  |
| `Type` | string |  |  |

---

### 스키마 `TimelinePutTimelineInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TimelineInfo` | TimelinePutTimelineInfo |  |  |
| `ValList` | array<TimelinePutValList> |  |  |

---

### 스키마 `TimelinePutValList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TimelineID` | integer |  |  |
| `Type` | integer |  |  |
| `ExtVal` | string |  |  |
| `StartTime` | integer |  |  |
| `EndTime` | integer |  |  |
| `Name` | string |  |  |
| `sts` | string |  |  |

---

### 스키마 `TimezoneHolidayInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `HolidayID` | integer |  | 공휴일 ID |
| `Name` | string |  | 공휴일 이름 |
| `RepeatYear` | integer |  | 설정 된 년까지 반복 |
| `Holidays` | array<integer> |  | 공휴일 목록(mmdd) |

---

### 스키마 `TimezoneHolidayToTerminalOptResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `HolidayOptionList` | array<HolidayConfig> |  | 단말기 휴일 목록 |

---

### 스키마 `TimezoneInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TimezoneID` | integer |  | 타임존 ID |
| `Name` | string |  | 타임존 이름 |
| `HolidayID` | integer |  | 공휴일 정보 ID |
| `Holiday` | integer |  | 공휴일에 설정 할 타임라인 ID |
| `Sunday` | integer |  | 일요일에 설정 할 타임라인 ID |
| `Monday` | integer |  | 월요일에 설정 할 타임라인 ID |
| `Tuesday` | integer |  | 화요일에 설정 할 타임라인 ID |
| `Wednesday` | integer |  | 수요일에 설정 할 타임라인 ID |
| `Thursday` | integer |  | 목요일에 설정 할 타임라인 ID |
| `Friday` | integer |  | 금요일에 설정 할 타임라인 ID |
| `Saturday` | integer |  | 토요일에 설정 할 타임라인 ID |

---

### 스키마 `TimezoneTimelineInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TimelineID` | integer |  | 타임라인 ID |
| `Name` | string |  | 타임라인 이름 |
| `Type` | integer |  | 타임라인 타입 (1=출입통제, 2=인증타임존, 3=혼합) |
| `TimezoneValues` | array<TimezoneValue> |  |  |

---

### 스키마 `TimezoneTimelinePutInfoValue`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `data` | TimelinePutTimelineInfoResult |  |  |

---

### 스키마 `TimezoneValue`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Type` | integer |  | 타입 (1=출입 허용, 2=출입불가, 3=인증) |
| `ExtVal` | integer |  | 타입에 따른 확장 값(타입이 인증일 경우 인증타입 값 설정) |
| `StartTime` | string |  | 시작 시간 |
| `EndTime` | string |  | 종료 시간 |

---

### 스키마 `TopFivebyTerminal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TerminalID` | integer |  | 단말기 아이디 |
| `AuthCount` | integer |  | 단말기 별 인증시도 횟수 |

---

### 스키마 `TopFivebyUser`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `AuthCount` | integer |  | 사용자 ID별 인증시도 횟수 |

---

### 스키마 `Total`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Count` | integer |  |  |

---

### 스키마 `UnRegUsersInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | string |  |  |
| `UniqueID` | string |  |  |
| `Name` | string |  |  |

---

### 스키마 `UnRegUsersTotal`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Count` | integer |  |  |

---

### 스키마 `UpdateUserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserInfo` | UserInfo |  |  |
| `UserFPInfo` | array<UserFPInfo> |  |  |
| `UserFaceInfo` | array<UserFaceInfo> |  |  |
| `UserCardInfo` | array<UserCardInfo> |  |  |
| `UserFaceWTInfo` | array<UserFaceWTInfo> |  |  |

---

### 스키마 `UserCardInfo`

카드번호

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `CardNum` | string |  |  |

---

### 스키마 `UserCountByGroups`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `GroupID` | integer |  | 그룹 코드 |
| `UserCount` | integer |  | UserCount |

---

### 스키마 `UserCountInGroupResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserCountByGroups` | array<UserCountByGroups> |  |  |

---

### 스키마 `UserFPInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `FingerID` | integer |  | 지문위치 정보 |
| `MinConvType` | integer |  | BSP Template Type |
| `TemplateIndex` | integer |  | 템플릿 순서 |
| `TemplateData` | string |  | 지문템플릿 데이터 |

---

### 스키마 `UserFPInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserFPInfo` | array<UserFPInfo> |  |  |

---

### 스키마 `UserFaceInfo`

지문템플릿 데이터

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자ID |
| `Index` | integer |  | 얼굴 index, (1,2) |
| `Type` | integer |  | 고정값 0 |
| `SubIndex` | integer |  | 등록 템플릿 순번 |
| `TemplateSize` | integer |  | 등록 템플릿 사이즈 |
| `TemplateData` | string |  |  |

---

### 스키마 `UserFaceInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserFaceInfo` | array<UserFaceInfo> |  |  |

---

### 스키마 `UserFacePhoto`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Photo` | string |  | 사용자 프로필 사진 데이터 |

---

### 스키마 `UserFaceWTInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 ID |
| `TemplateSize` | integer |  | 등록 얼굴 템플릿 데이터 사이즈 |
| `TemplateData` | string |  | 등록 얼굴 워크스루 템플릿 데이터 |
| `TemplateType` | integer |  | 등록 얼굴 워크스루 템플릿 타입 (0: 템플릿타입, 1: 이미지 타입) |

---

### 스키마 `UserFaceWTInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserFaceWTInfo` | array<UserFaceWTInfo> |  |  |

---

### 스키마 `UserFaceWTInfoVisitor`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `TemplateSize` | integer |  |  |
| `TemplateData` | string |  |  |
| `TemplateType` | string |  |  |

---

### 스키마 `UserIDList`

사용자 ID 목록

- **type**: `array`

---

### 스키마 `UserIDs`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | array<integer> |  |  |

---

### 스키마 `UserInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | string |  | 사용자 아이디 |
| `UniqueID` | string |  | 고유값 |
| `Name` | string |  | 사용자 이름 |
| `AuthInfo` | array<integer> |  | 인증방식 |
| `Privilege` | integer |  | 사용자 권한 |
| `CreateDate` | string |  | 생성일자 |
| `UsePeriodFlag` | integer |  | 사용자 사용 기간 사용 flag |
| `RegistDate` | string |  | 등록일 |
| `ExpireDate` | string |  | 만료일 |
| `Password` | string |  | 비밀번호 |
| `GroupCode` | integer |  | 그룹 코드 |
| `AccessGroupCode` | integer |  | 출입그룹 코드 |
| `UserType` | integer |  | 사용자 타입 |
| `TimezoneCode` | integer |  | 타임존 코드 |
| `BlackList` | integer |  | 블랙리스트 유무 |
| `FPIdentify` | integer |  | 지문 1:N |
| `FaceIdentify` | integer |  | 얼굴 1:N |
| `DuressFinger` | array<integer> |  | 협박 지문 |
| `Partition` | integer |  | ACU 파티션 |
| `APBExcept` | integer |  | 안티패스백 예외 적용 |
| `APBZone` | integer |  | 안태패스백 현재 위치 |
| `WorkCode` | string |  | 근태 코드 |
| `MealCode` | string |  | 식수 코드 |
| `MoneyCode` | string |  | 근태 지급액 코드 |
| `MessageCode` | integer |  | 사용자 메시지 코드 |
| `VerifyLevel` | integer |  | 인증 레벨 |
| `PositionCode` | integer |  | 직급 코드 |
| `Department` | string |  | 부서 코드 |
| `LoginPW` | string |  | 클라이언트 접속 비밀번호 |
| `LoginAllowed` | string |  | 클라이언트 접속 허용 여부 |
| `Picture` | string |  |  |
| `EmployeeNum` | string |  | 사원번호 |
| `Email` | string |  | 이메일 주소 |
| `Phone` | string |  | 전화 번호 |

---

### 스키마 `UserInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserInfo` | UserInfo |  |  |
| `UserCardInfo` | array<UserCardInfo> |  |  |

---

### 스키마 `UserIrisInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  |  |
| `EyeType` | integer |  |  |
| `TemplateSize` | integer |  |  |
| `TemplateData` | string |  |  |

---

### 스키마 `UserListInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | string |  | 사용자 ID |
| `UniqueID` | string |  | 고유값 |
| `Name` | string |  | 사용자 이름 |
| `AuthInfo` | array<integer> |  | 인증방식 |
| `Privilege` | integer |  | 사용자 권한 |
| `RegistDate` | string |  | 등록일 |
| `ExpireDate` | string |  | 만료일 |
| `GroupCode` | integer |  | 그룹 코드 |
| `AccessGroupCode` | integer |  | 출입그룹 코드 |
| `TimezoneCode` | integer |  | 타임존 코드 |
| `BlackList` | integer |  | 블랙리스트 유무 |
| `FPIdentify` | integer |  | 지문 1:N |
| `FaceIdentify` | integer |  | 얼굴 1:N |
| `APBZone` | integer |  | 안태패스백 현재 위치 |
| `EmployeeNum` | string |  | 사원번호 |

---

### 스키마 `UserListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Total` | Total |  |  |
| `UserList` | array<UserListInfo> |  |  |

---

### 스키마 `UserMessageListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserMessageList` | array<MessageInfo> |  |  |

---

### 스키마 `UserMessageResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserMessage` | array<MessageInfo> |  |  |

---

### 스키마 `UserPasswordInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 단말기 아이디 |
| `CurrentPassword` | string |  | 현재 비밀번호 |
| `NewPassword` | string |  | 새로운 비밀번호 |

---

### 스키마 `UserPicture`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ImageType` | string |  |  |
| `Picture` | string |  |  |

---

### 스키마 `UserPictureResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `PictureInfo` | UserPicture |  |  |

---

### 스키마 `UserRFCardInfoResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `UserCardInfo` | array<UserCardInfo> |  |  |

---

### 스키마 `UserSimpleInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | integer |  | 사용자 아이디 |
| `Name` | string |  | 사용자 이름 |

---

### 스키마 `UserTinyInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `ID` | string |  | 사용자 아이디 |
| `UniqueID` | string |  | 고유값 |
| `Name` | string |  | 사용자 이름 |

---

### 스키마 `UserTinyList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `total` | integer |  |  |
| `users` | array<UserTinyInfo> |  |  |

---

### 스키마 `UserTokenInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  |  |
| `Token` | string |  |  |
| `TokenType` | integer |  |  |

---

### 스키마 `VisitInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `StartTime` | string |  |  |
| `EndTime` | string |  |  |
| `Purpose` | string |  |  |
| `VisitTargetID` | integer |  |  |
| `VisitTargetUserName` | string |  |  |
| `VisitTargetPositionName` | string |  |  |
| `VisitTargetGroupName` | string |  |  |
| `Password` | string |  |  |

---

### 스키마 `VisitInvite`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `InviteType` | string |  |  |
| `VisitIndex` | string |  |  |
| `VisitorIndex` | string |  |  |
| `Email` | string |  |  |
| `Title` | string |  |  |
| `Message` | string |  |  |
| `AccessGroup` | integer |  |  |

---

### 스키마 `VisitLogin`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `userId` | string |  |  |
| `password` | string |  |  |

---

### 스키마 `VisitorInfo`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Name` | string |  |  |
| `AuthInfo` | array<integer> |  |  |
| `Privilege` | integer |  |  |
| `CreateDate` | string |  |  |
| `UsePeriodFlag` | integer |  |  |
| `RegistDate` | string |  |  |
| `ExpireDate` | string |  |  |
| `Password` | string |  |  |
| `GroupCode` | integer |  |  |
| `AccessGroupCode` | integer |  |  |
| `UserType` | integer |  |  |
| `TimezoneCode` | integer |  |  |
| `BlackList` | integer |  |  |
| `FPIdentify` | integer |  |  |
| `FaceIdentify` | integer |  |  |
| `DuressFinger` | array<integer> |  |  |
| `Partition` | integer |  |  |
| `APBExcept` | integer |  |  |
| `APBZone` | integer |  |  |
| `WorkCode` | string |  |  |
| `MealCode` | string |  |  |
| `MoneyCode` | string |  |  |
| `MessageCode` | integer |  |  |
| `VerifyLevel` | integer |  |  |
| `PositionCode` | integer |  |  |
| `Department` | string |  |  |
| `LoginPW` | string |  |  |
| `LoginAllowed` | string |  |  |
| `Picture` | string |  |  |
| `EmployeeNum` | string |  |  |
| `Email` | string |  |  |
| `Phone` | string |  |  |

---

### 스키마 `VisitorInfomation`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `VisitInfo` | VisitInfo |  |  |
| `VisitorList` | array<VisitorList> |  | 방문신청 고객 리스트 |
| `ItemList` | array<ItemList> |  | 반입물품 리스트 |

---

### 스키마 `VisitorList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `FirstName` | string |  |  |
| `LastName` | string |  |  |
| `Birthday` | string |  |  |
| `Mobile` | integer |  |  |
| `Company` | string |  |  |
| `CarNumber` | string |  |  |
| `Email` | string |  |  |
| `Photo` | string |  |  |

---

### 스키마 `WebAlarm`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Hour` | integer |  | 시 |
| `Minute` | integer |  | 분 |
| `Sunday` | integer |  | 일요일 |
| `Monday` | integer |  | 월요일 |
| `Tuesday` | integer |  | 화요일 |
| `Wednesday` | integer |  | 수요일 |
| `Thursday` | integer |  | 목요일 |
| `Friday` | integer |  | 금요일 |
| `Saturday` | integer |  | 토요일 |
| `Holiday` | integer |  | 공휴일 |
| `Duration` | integer |  | 지속시간 (최대:  60 초) |
| `Reserved1` | integer |  | 고정값 |
| `Reserved2` | integer |  | 고정값 |
| `Reserved3` | integer |  | 고정값 |
| `Reserved4` | integer |  | 고정값 |

---

### 스키마 `WebNotice`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Title` | string |  |  |
| `StartDate` | string |  |  |
| `EndDate` | string |  |  |
| `StartTime` | string |  |  |
| `EndTime` | string |  |  |
| `Message` | string |  |  |
| `IsPopup` | string |  |  |

---

### 스키마 `WebNoticeResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `WebNotice` | WebNotice |  |  |

---

### 스키마 `WiegandIn`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `InBasicInfo` | InBasicInfo |  |  |
| `Parity` | array<Parity> |  |  |
| `ConvertFormat` | array<ConvertFormat> |  |  |

---

### 스키마 `WiegandInResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `InBasicInfo` | InBasicInfo |  |  |
| `Parity` | array<Parity> |  |  |
| `ConvertFormat` | array<ConvertFormat> |  |  |

---

### 스키마 `WiegandInToTerminalDownload`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Parity` | array<Parity> |  |  |
| `InBasicInfo` | InBasicInfo |  |  |
| `ConvertFormat` | array<ConvertFormat> |  |  |
| `TerminalID` | array<string> |  |  |

---

### 스키마 `WiegandList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Code` | integer |  | 위겐드 코드 |
| `Name` | string |  | 위겐드 명칭 |

---

### 스키마 `WiegandListResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `Total` | Total |  |  |
| `WiegandList` | array<WiegandList> |  |  |

---

### 스키마 `WiegandOut`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `OutBasicInfo` | OutBasicInfo |  |  |
| `Parity` | array<Parity> |  |  |

---

### 스키마 `WiegandOutResult`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `Result` | Result |  |  |
| `OutBasicInfo` | OutBasicInfo |  |  |
| `Parity` | array<Parity> |  |  |

---

### 스키마 `WorkTimeList`

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `UserID` | integer |  | 사용자 아이디 |
| `BasicWorkTime` | string |  | 기본근무 시간 포멧 (ex. 04:27) |
| `OverWorkTime` | string |  | 연장근무 시간 포멧 (ex. 04:27) |
| `TotalWorkTime` | string |  | 전체근무 시간 포멧 (ex. 04:27) |

---
