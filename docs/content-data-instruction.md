# Content Data 세팅 가이드 (uv)

## 개발 환경 구축
`content_data` 디렉토리 내의 Python 프로젝트 환경을 설정하려면 아래 명령어를 순서대로 실행하세요.

```bash
# 1. 디렉토리 이동
cd content_data

# 2. uv 설치 (아직 설치되지 않은 경우)
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 프로젝트 동기화 (Python 3.12 및 의존성 자동 설치)
uv sync
```
