import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent  # backend/fastapi
REPO_ROOT = BASE_DIR.parents[1]  # project root

# 루트 .env 먼저 로드
load_dotenv(REPO_ROOT / ".env")

# backend/fastapi/.env가 있으면 그 값으로 덮어쓰기 가능
load_dotenv(BASE_DIR / ".env", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL 환경변수가 설정되어 있지 않습니다.")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
