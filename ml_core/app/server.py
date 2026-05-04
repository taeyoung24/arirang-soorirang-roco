from __future__ import annotations

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import PronunciationAnalysisResponse
from app.aligner_client import AlignerClient
from app.config import Settings
from app.gemini_client import GeminiFeedbackClient
from app.inference_client import InferenceClient
from app.pronunciation_analysis_service import PronunciationAnalysisService
from app.schemas import HealthResponse, PredictResponse


settings = Settings.from_env()
client = InferenceClient(settings.inference_base_url, settings.inference_timeout_seconds)
aligner_client = AlignerClient(settings.aligner_base_url, settings.aligner_timeout_seconds)
analysis_service = PronunciationAnalysisService(
    analyzer=AcousticAnalyzer(),
    gemini_client=GeminiFeedbackClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        timeout_seconds=settings.gemini_timeout_seconds,
    ),
)
app = FastAPI(title="MDD Service", version="0.1.0")


def _extract_upstream_detail(exc: httpx.HTTPStatusError):
    try:
        payload = exc.response.json()
    except ValueError:
        return exc.response.text
    if isinstance(payload, dict) and "detail" in payload:
        return payload["detail"]
    return payload


@app.get("/health", response_model=HealthResponse, response_model_exclude_none=True)
def healthcheck() -> HealthResponse:
    inference_status, _ = client.health()
    aligner_status, _ = aligner_client.health()
    return HealthResponse(
        status="ok",
        service_mode="api",
        inference_base_url=settings.inference_base_url,
        inference_status=inference_status,
        aligner_base_url=settings.aligner_base_url,
        aligner_status=aligner_status,
        aligner_model_id=settings.aligner_model_id,
        gemini_model=settings.gemini_model,
        gemini_status="configured" if settings.gemini_api_key else "disabled",
    )


@app.post("/predict", response_model=PredictResponse, response_model_exclude_none=True)
async def predict(
    script: str = Form(...),
    audio: UploadFile = File(...),
) -> PredictResponse:
    try:
        payload = await audio.read()
        return client.predict(payload, audio.filename or "input.wav", script)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=_extract_upstream_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"inference service unavailable: {exc}") from exc


@app.post(
    "/analyze-pronunciation-basic",
    response_model=PronunciationAnalysisResponse,
    response_model_exclude_none=True,
)
async def analyze_pronunciation_basic(
    script: str = Form(...),
    language: str | None = Form(None),
    feedback_language: str = Form("ko"),
    debug: bool = Form(False),
    audio: UploadFile = File(...),
) -> PronunciationAnalysisResponse:
    return await _analyze_pronunciation(
        script=script,
        language=language,
        feedback_language=feedback_language,
        debug=debug,
        audio=audio,
        include_llm_feedback=False,
    )


@app.post(
    "/analyze-pronunciation-llm",
    response_model=PronunciationAnalysisResponse,
    response_model_exclude_none=True,
)
async def analyze_pronunciation_llm(
    script: str = Form(...),
    language: str | None = Form(None),
    feedback_language: str = Form("ko"),
    debug: bool = Form(False),
    audio: UploadFile = File(...),
) -> PronunciationAnalysisResponse:
    return await _analyze_pronunciation(
        script=script,
        language=language,
        feedback_language=feedback_language,
        debug=debug,
        audio=audio,
        include_llm_feedback=True,
    )


async def _analyze_pronunciation(
    script: str,
    language: str | None,
    feedback_language: str,
    debug: bool,
    audio: UploadFile,
    include_llm_feedback: bool,
) -> PronunciationAnalysisResponse:
    try:
        payload = await audio.read()
        prediction = client.predict(payload, audio.filename or "input.wav", script)
        forced_alignment = None
        try:
            forced_alignment = aligner_client.align(
                audio_bytes=payload,
                original_filename=audio.filename or "input.wav",
                text=script,
                language=(language or settings.aligner_language),
            )
        except httpx.HTTPError:
            forced_alignment = None
        response = analysis_service.analyze(
            payload,
            prediction,
            forced_alignment=forced_alignment,
            include_llm_feedback=include_llm_feedback,
            feedback_language=feedback_language,
        )
        if not debug:
            _compact_analysis_response(response)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=_extract_upstream_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"inference service unavailable: {exc}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _compact_analysis_response(response: PronunciationAnalysisResponse) -> None:
    target_units = {item.target_unit for item in response.diagnostic_candidates[:3] if item.target_unit}
    response.diagnostic_candidates = response.diagnostic_candidates[:3]
    response.alignments = _compact_alignments(response.alignments, target_units)
    response.segment_features = []
    response.predicted_phoneme_scores = [
        score for score in response.predicted_phoneme_scores if score.phoneme in target_units
    ][:3]
    response.target_phoneme_scores = [
        score for score in response.target_phoneme_scores if score.phoneme in target_units
    ][:3]
    response.syllable_candidate_scores = [
        score
        for score in response.syllable_candidate_scores
        if any(unit in target_units for unit in score.target_sequence)
    ][:3]
    response.prosody = None
    response.model_score = None


def _compact_alignments(alignments, target_units: set[str]):
    if not target_units:
        return [unit for unit in alignments if unit.unit_type == "word"][:6]
    result = [
        unit
        for unit in alignments
        if unit.unit_type in {"phoneme", "syllable"} and (unit.label in target_units or unit.expected_label in target_units)
    ]
    return result[:8]
