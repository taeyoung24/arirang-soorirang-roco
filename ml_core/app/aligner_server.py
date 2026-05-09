from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.acoustic_schemas import ForcedAlignmentItem, ForcedAlignmentResponse
from app.config import Settings
from app.schemas import HealthResponse

settings = Settings.from_env()
app = FastAPI(title="MDD Forced Aligner", version="0.1.0")

_aligner = None
_aligner_load_error: str | None = None


def _get_aligner():
    global _aligner, _aligner_load_error
    if _aligner is not None:
        return _aligner
    if _aligner_load_error is not None:
        raise RuntimeError(_aligner_load_error)
    try:
        import torch
        from qwen_asr import Qwen3ForcedAligner

        kwargs = {
            "dtype": torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            "device_map": "cuda:0" if torch.cuda.is_available() else "cpu",
        }
        _aligner = Qwen3ForcedAligner.from_pretrained(settings.aligner_model_id, **kwargs)
        return _aligner
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        _aligner_load_error = str(exc)
        raise RuntimeError(_aligner_load_error) from exc


@app.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    status = "configured"
    if _aligner_load_error is not None:
        status = "error"
    return HealthResponse(
        status="ok",
        service_mode="aligner",
        aligner_model_id=settings.aligner_model_id,
        aligner_status=status,
    )


@app.post("/align", response_model=ForcedAlignmentResponse)
async def align(
    text: str = Form(...),
    language: str = Form(...),
    audio: UploadFile = File(...),
) -> ForcedAlignmentResponse:
    if not text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty.")
    try:
        aligner = _get_aligner()
        suffix = Path(audio.filename or "input.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            temp_path = Path(tmp.name)
        try:
            results = aligner.align(
                audio=str(temp_path),
                text=text,
                language=language,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        first = results[0]
        items = []
        for item in first:
            items.append(
                ForcedAlignmentItem(
                    text=getattr(item, "text", ""),
                    start_ms=int(round(float(getattr(item, "start_time", 0.0)) * 1000)),
                    end_ms=int(round(float(getattr(item, "end_time", 0.0)) * 1000)),
                )
            )
        return ForcedAlignmentResponse(
            language=language,
            items=items,
            source_model=settings.aligner_model_id,
            resolution_ms=80,
        )
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise HTTPException(status_code=500, detail=f"forced alignment failed: {exc}") from exc
