from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.config import Settings
from app.fairseq_runner import FairseqInferenceRunner
from app.inference_backend import InProcessFairseqBackend
from app.pipeline import MDDInferenceError, MDDPipeline
from app.schemas import HealthResponse, PredictResponse


settings = Settings.from_env()
runner = FairseqInferenceRunner(settings.model_path, settings.infer_script_path, settings.max_tokens)
pipeline = MDDPipeline(settings, inference_backend=InProcessFairseqBackend(runner))
app = FastAPI(title="MDD Inference Service", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service_mode="inference",
        model_path=settings.model_path,
        infer_script_path=settings.infer_script_path,
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(
    script: str = Form(...),
    audio: UploadFile = File(...),
) -> PredictResponse:
    try:
        payload = await audio.read()
        return pipeline.predict(payload, audio.filename or "input.wav", script)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MDDInferenceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
