아래 그대로 `SETUP.md` 최종본으로 쓰면 된다.

````markdown
# 아리랑 수리랑 백엔드 설정 가이드

## 프로젝트 구조

- `backend/fastapi/` - FastAPI 백엔드 서버
- `content_data/` - JSON 기반 학습 데이터
- `docker-compose.yml` - PostgreSQL 컨테이너 구성
- `.env.example` - 로컬 환경 변수 예시 파일

## 사전 요구사항

- Python 3.12+
- Docker & Docker Compose
- Git

## 설정 단계

### 1. 환경 변수 설정

```bash
# 루트 디렉터리에서
cp .env.example .env
````

`.env` 파일이 생성됩니다. 로컬 실행 전 `POSTGRES_PASSWORD`와 `DATABASE_URL` 값을 확인하고, 필요한 경우 로컬 환경에 맞게 수정합니다.

예시:

```env
POSTGRES_DB=arirang
POSTGRES_USER=arirang_user
POSTGRES_PASSWORD=change_me
DATABASE_URL=postgresql+psycopg://arirang_user:change_me@localhost:5433/arirang
```

> `.env` 파일은 민감한 로컬 설정 정보를 포함하므로 Git에 커밋하지 않습니다.

---

### 2. 가상 환경 생성 및 활성화

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. 필수 패키지 설치

```bash
cd backend/fastapi
pip install -r requirements.txt
cd ../..
```

설치되는 주요 패키지:

* `fastapi`, `uvicorn` - FastAPI 웹 프레임워크
* `sqlalchemy` - ORM
* `psycopg[binary]` - PostgreSQL 드라이버
* `alembic` - DB 마이그레이션 도구
* `python-dotenv` - 환경 변수 로드

---

### 4. PostgreSQL 시작

```bash
docker compose up -d
```

* PostgreSQL 컨테이너가 `localhost:5433`에서 실행됩니다.
* 데이터베이스: `.env`의 `POSTGRES_DB` 값 사용
* 사용자: `.env`의 `POSTGRES_USER` 값 사용
* 비밀번호: `.env`의 `POSTGRES_PASSWORD` 값 사용

컨테이너 상태 확인:

```bash
docker compose ps
```

---

### 5. DB 마이그레이션 적용

```bash
cd backend/fastapi
alembic upgrade head
cd ../..
```

마이그레이션은 `backend/fastapi/alembic/versions/` 아래에 있는 revision 파일을 기준으로 PostgreSQL 테이블을 생성합니다.

---

### 6. 시드 데이터 로드

```bash
cd backend/fastapi
python seed.py
cd ../..
```

`content_data/data/` 폴더의 JSON 파일들이 PostgreSQL에 로드됩니다.

로드 대상:

* `words.json`
* `meanings.json`
* `sentences.json`
* `quizzes.json`

---

### 7. FastAPI 서버 실행

```bash
cd backend/fastapi
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

서버는 아래 주소에서 실행됩니다.

```text
http://127.0.0.1:8000
```

Swagger UI는 아래 주소에서 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

---

## API 엔드포인트

### DB 기반 API

아래 API는 PostgreSQL 데이터를 조회해서 응답합니다.

* `GET /api/v1/contents/recommended` - 추천 학습 세트 조회
* `GET /api/v1/categories` - 카테고리 목록 조회
* `GET /api/v1/categories/{category_id}/sets` - 카테고리별 학습 세트 조회
* `GET /api/v1/sets/{set_id}/cards` - 학습 카드 목록 조회
* `POST /api/v1/cards/{card_id}/answer` - 의미 테스트 정답 판정

### 더미 데이터 API

아래 API는 현재 UI 확인용 더미 데이터를 반환합니다.

* `GET /api/v1/contents/recent` - 최근 학습 목록 조회
* `GET /api/v1/saved-words` - 저장 단어 목록 조회
* `POST /api/v1/cards/{card_id}/pronunciation` - 발음 평가 요청

---

## 데이터베이스 스키마

### 주요 테이블

* `categories` - 학습 카테고리
* `learning_sets` - 학습 세트
* `words` - 단어 목록
* `meanings` - 단어 의미
* `sentences` - 예제 문장
* `quizzes` - 학습 카드/퀴즈
* `quiz_choices` - 퀴즈 선택지

### 관계 요약

```text
categories 1 ─ N learning_sets
learning_sets 1 ─ N quizzes
meanings 1 ─ N sentences
meanings 1 ─ N quizzes
quizzes 1 ─ N quiz_choices
```

현재 `words` 테이블은 독립 테이블로 관리되며, `meanings`와 직접 FK 관계는 없습니다.

---

## 문제 해결

### PostgreSQL 연결 실패

```bash
docker compose ps
docker compose logs db
```

확인할 것:

* Docker 컨테이너가 실행 중인지 확인
* `.env`의 `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` 값 확인
* `.env`의 `DATABASE_URL` 포트가 `5433`인지 확인

---

### 비밀번호 변경 후 연결 실패

PostgreSQL은 최초 생성 시점의 환경 변수로 DB 사용자를 초기화합니다.
이미 생성된 volume이 있으면 `.env`의 비밀번호만 바꿔도 기존 DB에는 반영되지 않을 수 있습니다.

로컬 개발 환경에서는 아래 명령으로 volume을 삭제하고 DB를 다시 생성할 수 있습니다.

```bash
docker compose down -v
docker compose up -d

cd backend/fastapi
alembic upgrade head
python seed.py
cd ../..
```

---

### Alembic 마이그레이션 오류

```bash
cd backend/fastapi
alembic current
alembic heads
alembic history --verbose
```

확인할 것:

* PostgreSQL 컨테이너가 실행 중인지 확인
* `.env`의 `DATABASE_URL`이 올바른지 확인
* `backend/fastapi/alembic/env.py`에서 `DATABASE_URL`을 정상적으로 읽는지 확인

---

### Seed 데이터 로드 실패

확인할 것:

* `content_data/data/` 폴더에 JSON 파일이 있는지 확인
* PostgreSQL이 실행 중인지 확인
* 마이그레이션이 먼저 적용되었는지 확인
* `.env`의 `DATABASE_URL` 값이 올바른지 확인

---

## 개발 팁

### `--reload` 모드로 서버 실행

```bash
cd backend/fastapi
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

`--reload` 모드는 코드 변경 시 서버를 자동 재시작합니다.
다만 프로세스 재시작 과정에서 환경 변수 또는 경로 문제가 발생할 수 있으므로, 문제가 생기면 일반 실행 방식으로 확인합니다.

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

---

### 포트 8000 점유 확인 및 해제

```bash
lsof -i :8000
kill -9 <PID>
```

---

### 민감 정보 포함 여부 확인

커밋 전 아래 명령어로 민감한 DB 연결 정보가 Git 추적 파일에 포함되어 있는지 확인합니다.

```bash
git grep -E "POSTGRES_PASSWORD=|DATABASE_URL=.*:.*@"

아무 결과도 나오지 않아야 합니다.

DB URL 형식 확인:

```bash
git grep "postgresql+psycopg://"
```

`.env.example`의 `change_me` 예시만 나오는 것은 허용됩니다. 실제 비밀번호가 포함되면 안 됩니다.

---

## 커밋 전 체크리스트

* [ ] `.env` 파일은 `.gitignore`에 포함되어 있음
* [ ] 민감한 DB 연결 정보가 코드나 문서에 직접 포함되지 않음
* [ ] `requirements.txt`가 최신 상태
* [ ] Alembic 마이그레이션 파일이 포함되어 있음
* [ ] `alembic upgrade head`가 정상 실행됨
* [ ] `seed.py`가 정상 실행됨
* [ ] `docker-compose.yml`이 환경변수 기반으로 동작함
* [ ] FastAPI 서버가 정상 실행됨
* [ ] 주요 API가 Swagger UI(`/docs`)에서 정상 응답함

```
```
