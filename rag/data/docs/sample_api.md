# SampleCorp Public API

가상 API 문서입니다. 실제 서비스 스펙이 아닙니다.

## POST /v1/streams/{STREAM_ID}/add

스트림을 추가합니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| name | string | 스트림 이름 |
| bitrate | integer | kbps |

응답 스키마 `StreamInfo`:

| 필드 | 타입 |
|------|------|
| id | string |
| status | string |

## GET /v1/users/{id}/badge

사용자 배지 정보를 조회합니다.

스키마 `BadgeInfo`:

| 필드 | 타입 |
|------|------|
| BadgeType | integer |
| BadgeData | string |
