from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from typing_extensions import Annotated

from app.config import Settings
from app.pipeline import MDDInferenceError, MDDPipeline
from app.schemas import HealthResponse, PredictResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Dynamically isolates and resolves backends and dependencies during context startup."""
    settings = Settings.from_env()
    
    if settings.mdd_backend == "wav2vec2":
        from app.inference_backend import Wav2Vec2InferenceBackend
        backend = Wav2Vec2InferenceBackend(
            model_id=settings.wav2vec2_model_id,
            device=settings.mdd_device,
        )
    else:
        from app.fairseq_runner import FairseqInferenceRunner
        from app.inference_backend import InProcessFairseqBackend
        
        runner = FairseqInferenceRunner(
            settings.model_path, settings.infer_script_path, settings.max_tokens
        )
        backend = InProcessFairseqBackend(runner)
        
    app.state.settings = settings
    app.state.pipeline = MDDPipeline(settings, inference_backend=backend)
    yield


app = FastAPI(title="MDD Inference Service", version="0.1.0", lifespan=lifespan)


def get_settings() -> Settings:
    return app.state.settings


def get_pipeline() -> MDDPipeline:
    return app.state.pipeline


@app.get("/health", response_model=HealthResponse, response_model_exclude_none=True)
def healthcheck(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service_mode="inference",
        model_path=getattr(settings, "model_path", None),
        infer_script_path=getattr(settings, "infer_script_path", None),
    )


@app.post("/predict", response_model=PredictResponse, response_model_exclude_none=True)
def predict(
    script: str = Form(...),
    audio: UploadFile = File(...),
    pipeline: Annotated[MDDPipeline, Depends(get_pipeline)] = None,
) -> PredictResponse:
    try:
        payload = audio.file.read()
        return pipeline.predict(payload, audio.filename or "input.wav", script)
        
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MDDInferenceError as exc:
        message = str(exc)
        if message == "Predicted phoneme sequence is empty.":
            raise HTTPException(
                status_code=422,
                detail="No recognizable speech was detected in the audio.",
            ) from exc
        raise HTTPException(status_code=500, detail=message) from exc