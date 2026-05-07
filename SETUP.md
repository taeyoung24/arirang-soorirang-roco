# 아리랑 수리랑 백엔드 설정 가이드

## 프로젝트 구조
- `backend/fastapi/` - FastAPI 백엔드 서버
- `content_data/` - JSON 기반 학습 데이터
- `docker-compose.yml` - PostgreSQL 컨테이너 구성

## 사전 요구사항
- Python 3.14+
- Docker & Docker Compose
- Git

## 설정 단계

### 1. 환경 변수 설정
```bash
# 루트 디렉터리에서
cp .env.example .env
```
`.env` 파일이 생성되며, 기본값으로 로컬 PostgreSQL 연결이 설정됩니다.

### 2. 가상 환경 생성 및 활성화
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 필수 패키지 설치
```bash
cd backend/fastapi
pip install -r requirements.txt
cd ../..
```

설치되는 패키지:
- `fastapi`, `uvicorn` - FastAPI 웹 프레임워크
- `sqlalchemy==2.0.49` - ORM
- `psycopg[binary]` - PostgreSQL 드라이버
- `alembic==1.13.0` - DB 마이그레이션 도구
- `python-dotenv` - 환경 변수 로드

### 4. PostgreSQL 시작
```bash
docker compose up -d
```
- PostgreSQL 컨테이너가 `localhost:5433`에서 실행됩니다
- 데이터베이스: `arirang`
- 사용자: `arirang_user`
- 비밀번호: `arirang_password`

### 5. DB 마이그레이션 적용
```bash
cd backend/fastapi
../../.venv/bin/alembic -c alembic.ini upgrade head
cd ../..
```

### 6. 시드 데이터 로드
```bash
cd backend/fastapi
source ../../.venv/bin/activate
python seed.py
cd ../..
```
`content_data/data/` 폴더의 JSON 파일들이 PostgreSQL에 로드됩니다.

### 7. FastAPI 서버 실행
```bash
cd backend/fastapi
source ../../.venv/bin/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

서버는 `http://127.0.0.1:8000`에서 실행됩니다.

## API 엔드포인트

### DB 기반 API (실제 데이터)
- `GET /api/v1/categories` - 카테고리 목록
- `GET /api/v1/categories/{category_id}/sets` - 카테고리별 학습 세트
- `GET /api/v1/sets/{set_id}/cards` - 학습 카드 목록
- `GET /api/v1/contents/recommended` - 추천 세트
- `POST /api/v1/cards/{card_id}/answer` - 정답 판정

### 더미 데이터 API (UI 확인용)
- `GET /api/v1/contents/recent` - 최근 학습
- `GET /api/v1/saved-words` - 저장 단어
- `POST /api/v1/cards/{card_id}/pronunciation` - 발음 평가

## 데이터베이스 스키마

### 주요 테이블
- `categories` - 학습 카테고리
- `learning_sets` - 학습 세트
- `quizzes` - 학습 카드/퀴즈
- `quiz_choices` - 퀴즈 선택지
- `meanings` - 단어 의미
- `sentences` - 예제 문장
- `words` - 단어 목록

## 문제 해결

### PostgreSQL 연결 실패
```bash
# 컨테이너 상태 확인
docker compose ps

# 컨테이너 로그 확인
docker compose logs db
```

### Alembic 마이그레이션 오류
```bash
# 마이그레이션 상태 확인
alembic current
alembic heads

# 마이그레이션 기록 조회
alembic history --verbose
```

### Seed 데이터 로드 실패
- `content_data/data/` 폴더에 JSON 파일이 있는지 확인
- PostgreSQL이 실행 중인지 확인
- 환경 변수 설정 확인

## 개발 팁

### --reload 모드로 서버 실행 (재시작 시 자동 리로드)
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
**주의**: 포트가 이미 사용 중이면 실패합니다. 다른 Uvicorn 프로세스가 없는지 확인하세요.

### 포트 8000 점유 확인 및 해제
```bash
lsof -i :8000
kill -9 <PID>
```

## 커밋 전 체크리스트
- [ ] `.env` 파일은 `.gitignore`에 포함되어 있음
- [ ] `requirements.txt`가 최신 상태
- [ ] Alembic 마이그레이션 파일 커밋
- [ ] `seed.py`가 정상 실행됨
- [ ] `docker-compose.yml` 검증
- [ ] README 업데이트

