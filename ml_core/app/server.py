from __future__ import annotations

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.config import Settings
from app.inference_client import InferenceClient
from app.schemas import HealthResponse, PredictResponse


settings = Settings.from_env()
client = InferenceClient(settings.inference_base_url, settings.inference_timeout_seconds)
app = FastAPI(title="MDD Service", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    inference_status, _ = client.health()
    return HealthResponse(
        status="ok",
        service_mode="api",
        inference_base_url=settings.inference_base_url,
        inference_status=inference_status,
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(
    script: str = Form(...),
    audio: UploadFile = File(...),
) -> PredictResponse:
    try:
        payload = await audio.read()
        return client.predict(payload, audio.filename or "input.wav", script)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"inference service unavailable: {exc}") from exc
