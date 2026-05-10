from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import ForcedAlignmentResponse, PronunciationAnalysisResponse
from app.aligner_client import AlignerClient
from app.config import Settings
from app.gemini_client import GeminiFeedbackClient
from app.inference_client import InferenceClient
from app.pronunciation_analysis_service import PronunciationAnalysisService
from app.reference_cache import ReferenceCacheManifest, ReferenceCacheRequest, create_reference_cache_store
from app.schemas import HealthResponse, PredictResponse
from app.tts_reference import create_tts_reference_generator


settings = Settings.from_env()
client = InferenceClient(settings.inference_base_url, settings.inference_timeout_seconds)
aligner_client = AlignerClient(settings.aligner_base_url, settings.aligner_timeout_seconds)
reference_cache = create_reference_cache_store(settings)
tts_reference_generator = create_tts_reference_generator(settings)
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
    reference_cache_status, reference_cache_error = reference_cache.health()
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
        reference_cache_status=reference_cache_status,
        reference_cache_bucket=settings.object_storage_bucket if settings.object_storage_enabled else None,
        reference_cache_error=reference_cache_error,
        tts_provider=settings.tts_provider,
        tts_voice_id=settings.tts_voice_id,
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


@app.get(
    "/reference-cache/{cache_key}",
    response_model=ReferenceCacheManifest,
    response_model_exclude_none=True,
)
def get_reference_cache_manifest(cache_key: str) -> ReferenceCacheManifest:
    manifest = reference_cache.get_manifest(cache_key)
    if manifest is None:
        raise HTTPException(status_code=404, detail="reference cache entry not found")
    return manifest


@app.post(
    "/reference-cache",
    response_model=ReferenceCacheManifest,
    response_model_exclude_none=True,
)
async def put_reference_cache(
    script: str = Form(...),
    alignment_json: str = Form(...),
    language: str = Form("Korean"),
    tts_provider: str = Form("unknown"),
    tts_model: str = Form("unknown"),
    voice_id: str = Form("default"),
    speaking_rate: float = Form(1.0),
    audio_format: str = Form("wav_16khz_mono"),
    aligner_model_id: str = Form("Qwen/Qwen3-ForcedAligner-0.6B"),
    alignment_resolution_ms: int = Form(80),
    audio: UploadFile = File(...),
) -> ReferenceCacheManifest:
    try:
        alignment = ForcedAlignmentResponse.model_validate_json(alignment_json)
        request = ReferenceCacheRequest(
            script=script,
            language=language,
            tts_provider=tts_provider,
            tts_model=tts_model,
            voice_id=voice_id,
            speaking_rate=speaking_rate,
            audio_format=audio_format,
            aligner_model_id=aligner_model_id,
            alignment_resolution_ms=alignment_resolution_ms,
        )
        return reference_cache.put_reference(request, await audio.read(), alignment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post(
    "/reference-cache/generate",
    response_model=ReferenceCacheManifest,
    response_model_exclude_none=True,
)
def generate_reference_cache(
    script: str = Form(...),
    language: str | None = Form(None),
) -> ReferenceCacheManifest:
    try:
        return _get_or_create_tts_reference(script, language)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=_extract_upstream_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"aligner service unavailable: {exc}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post(
    "/analyze-pronunciation-basic",
    response_model=PronunciationAnalysisResponse,
    response_model_exclude_none=True,
)
async def analyze_pronunciation_basic(
    script: str = Form(...),
    language: str | None = Form(None),
    feedback_language: str = Form("ko"),
    reference_cache_key: str | None = Form(None),
    use_tts_reference: bool = Form(True),
    debug: bool = Form(False),
    audio: UploadFile = File(...),
) -> PronunciationAnalysisResponse:
    return await _analyze_pronunciation(
        script=script,
        language=language,
        feedback_language=feedback_language,
        reference_cache_key=reference_cache_key,
        use_tts_reference=use_tts_reference,
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
    reference_cache_key: str | None = Form(None),
    use_tts_reference: bool = Form(True),
    debug: bool = Form(False),
    audio: UploadFile = File(...),
) -> PronunciationAnalysisResponse:
    return await _analyze_pronunciation(
        script=script,
        language=language,
        feedback_language=feedback_language,
        reference_cache_key=reference_cache_key,
        use_tts_reference=use_tts_reference,
        debug=debug,
        audio=audio,
        include_llm_feedback=True,
    )


async def _analyze_pronunciation(
    script: str,
    language: str | None,
    feedback_language: str,
    reference_cache_key: str | None,
    use_tts_reference: bool,
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
        reference_alignment = None
        if reference_cache_key:
            reference_alignment = reference_cache.get_alignment(reference_cache_key)
            if reference_alignment is None:
                raise HTTPException(status_code=404, detail="reference cache alignment not found")
        elif use_tts_reference:
            reference_manifest = await asyncio.to_thread(_get_or_create_tts_reference, script, language)
            reference_alignment = reference_cache.get_alignment(reference_manifest.cache_key)
        response = analysis_service.analyze(
            payload,
            prediction,
            forced_alignment=forced_alignment,
            reference_alignment=reference_alignment,
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
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _get_or_create_tts_reference(script: str, language: str | None) -> ReferenceCacheManifest:
    request = ReferenceCacheRequest(
        script=script,
        language=language or settings.aligner_language,
        tts_provider=settings.tts_provider,
        tts_model=settings.tts_model,
        voice_id=settings.tts_voice_id,
        speaking_rate=settings.tts_speaking_rate,
        aligner_model_id=settings.aligner_model_id,
        alignment_resolution_ms=80,
    )
    manifest = reference_cache.get_manifest(request.cache_key())
    if manifest is not None:
        return manifest

    tts_audio = tts_reference_generator.generate(script)
    alignment = aligner_client.align(
        audio_bytes=tts_audio.audio_bytes,
        original_filename="tts-reference.wav",
        text=script,
        language=language or settings.aligner_language,
    )
    return reference_cache.put_reference(request, tts_audio.audio_bytes, alignment)


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
    has_prosodic_diagnostic = any(item.category == "prosodic" for item in response.diagnostic_candidates)
    has_reference_pause_level = response.prosody is not None and any(
        item.pause_level is not None for item in response.prosody.reference_pause_comparisons
    )
    if not has_prosodic_diagnostic and not has_reference_pause_level:
        response.prosody = None
    response.model_score = None


def _compact_alignments(alignments, target_units: set[str]):
    if not target_units:
        return [unit for unit in alignments if unit.unit_type == "word"][:6]
    result = [
        unit
        for unit in alignments
        if unit.unit_type in {"syllable", "word"} and (unit.label in target_units or unit.expected_label in target_units)
    ]
    return result[:8]
