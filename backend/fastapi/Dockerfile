FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend/fastapi

COPY backend/fastapi/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/fastapi ./
COPY content_data/data /app/content_data/data
COPY frontend/public/sentence_images /app/frontend/public/sentence_images

EXPOSE 8000

CMD ["sh", "-c", "set -e; python migrate.py; python seed.py; exec uvicorn main:app --host 0.0.0.0 --port 8000"]
