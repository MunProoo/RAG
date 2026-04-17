Open WebUI / Pipelines에서 Markdown 이미지로 참조할 정적 파일은 `rag/data/assets/`에 두세요.

Docker Compose의 `imageserver` 서비스(nginx)가 이 폴더를 웹 루트로 서빙합니다.

- 호스트 브라우저: `http://localhost:8090/<파일명>`
- 다른 Docker 서비스에서: `http://imageserver/<파일명>`
