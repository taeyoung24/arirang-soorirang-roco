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

## 디렉토리 구조 및 실행 방식
본 프로젝트는 독립된 CLI 대신, 격리된 파이썬 환경(`uv`) 내에서 모듈 단위로 스크립트를 직접 실행하는 구조를 가집니다.

### 디렉토리 구조
프로젝트 루트 기준 `content_data` 디렉토리 구성은 다음과 같습니다.
```test
content_data/            <-- uv 파이썬 환경이 초기화된 루트
├── data/                <-- 정규화된 JSON 파일 보관
│   ├── words.json
│   ├── meanings.json
│   ├── sentences.json
│   └── quizzes.json
├── scripts/             <-- 직접 실행할 개별 스크립트 모듈들
│   ├── validate_ids.py
│   └── create_quiz.py
└── src/                 <-- 스크립트들이 공통으로 참조할 소스 (모델, 파일 I/O, 헬퍼 등)
    └── utils.py
```

### 스크립트 실행
스크립트를 실행할 때는 `content_data` 디렉토리 내에서 `uv run -m` 명령을 사용하여 파이썬 모듈 단위로 실행합니다.
이렇게 하면 `scripts/` 내의 파일들이 `src/` 폴더의 공통 로직을 문제없이 `import`하여 사용할 수 있습니다.

> [!IMPORTANT]
> **스크립트 작성 규칙:** `scripts/` 폴더 하위에 생성하는 모든 파이썬 파일은 파일 최상단에 주석으로 **실행 내용**과 **실행 명령어**를 필수로 명시해야 합니다. 만약 스크립트 실행에 필요한 **파라미터**가 있다면 함께 작성해야 합니다.
> 예시: `# 실행 명령어: uv run -m scripts.파일이름 --param1 value1`

**실행 명령어 예시:**
```bash
# content_data 디렉토리 내부에서 실행
uv run -m scripts.validate_ids
uv run -m scripts.create_quiz
```
