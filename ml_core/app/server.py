from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import ForcedAlignmentResponse, PronunciationAnalysisResponse
from app.aligner_client import AlignerClient
from app.config import Settings
from app.gemini_client import GeminiFeedbackClient
from app.inference_client import InferenceClient
from app.pronunciation_analysis_service import PronunciationAnalysisService
from app.reference_cache import ReferenceCacheManifest, ReferenceCacheRequest, create_reference_cache_store
from app.schemas import HealthResponse
from app.tts_asset_cache import TTSAssetManifest, TTSAssetRequest, create_tts_asset_store
from app.tts_reference import EdgeTTSReferenceGenerator, create_tts_reference_generator


settings = Settings.from_env()
client = InferenceClient(settings.inference_base_url, settings.inference_timeout_seconds)
aligner_client = AlignerClient(settings.aligner_base_url, settings.aligner_timeout_seconds)
reference_cache = create_reference_cache_store(settings)
tts_asset_store = create_tts_asset_store(settings)
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


def _align_or_raise(audio_bytes: bytes, original_filename: str, text: str, language: str) -> ForcedAlignmentResponse:
    try:
        alignment = aligner_client.align(
            audio_bytes=audio_bytes,
            original_filename=original_filename,
            text=text,
            language=language,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=_extract_upstream_detail(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"aligner service unavailable: {exc}") from exc
    if not alignment.items:
        raise HTTPException(status_code=502, detail="forced alignment returned no timing items")
    return alignment


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


@app.get(
    "/tts-assets/{cache_key}",
    response_model=TTSAssetManifest,
    response_model_exclude_none=True,
)
def get_tts_asset_manifest(cache_key: str) -> TTSAssetManifest:
    manifest = tts_asset_store.get_manifest(cache_key)
    if manifest is None:
        raise HTTPException(status_code=404, detail="TTS asset not found")
    return _with_tts_audio_url(manifest)


@app.get("/tts-assets/{cache_key}/audio")
def get_tts_asset_audio(cache_key: str) -> Response:
    audio = tts_asset_store.get_audio(cache_key)
    if audio is None:
        raise HTTPException(status_code=404, detail="TTS asset audio not found")
    return Response(content=audio, media_type="audio/wav")


@app.post(
    "/tts-assets/generate",
    response_model=TTSAssetManifest,
    response_model_exclude_none=True,
)
def generate_tts_asset(
    text: str = Form(...),
    language: str | None = Form(None),
    tts_provider: str | None = Form(None),
    tts_model: str | None = Form(None),
    voice_id: str | None = Form(None),
    speaking_rate: float | None = Form(None),
    audio_format: str = Form("wav_16khz_mono"),
) -> TTSAssetManifest:
    try:
        manifest = _get_or_create_tts_asset(
            text=text,
            language=language,
            tts_provider=tts_provider,
            tts_model=tts_model,
            voice_id=voice_id,
            speaking_rate=speaking_rate,
            audio_format=audio_format,
        )
        return _with_tts_audio_url(manifest)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
    )


async def _analyze_pronunciation(
    script: str,
    language: str | None,
    feedback_language: str,
    reference_cache_key: str | None,
    use_tts_reference: bool,
    debug: bool,
    audio: UploadFile,
) -> PronunciationAnalysisResponse:
    try:
        payload = await audio.read()
        prediction = client.predict(payload, audio.filename or "input.wav", script)
        forced_alignment = _align_or_raise(
            audio_bytes=payload,
            original_filename=audio.filename or "input.wav",
            text=script,
            language=(language or settings.aligner_language),
        )
        reference_alignment = None
        if reference_cache_key:
            reference_alignment = reference_cache.get_alignment(reference_cache_key)
            if reference_alignment is None:
                if not use_tts_reference:
                    raise HTTPException(status_code=404, detail="reference cache alignment not found")
                reference_manifest = await asyncio.to_thread(_get_or_create_tts_reference, script, language)
                reference_alignment = reference_cache.get_alignment(reference_manifest.cache_key)
        elif use_tts_reference:
            reference_manifest = await asyncio.to_thread(_get_or_create_tts_reference, script, language)
            reference_alignment = reference_cache.get_alignment(reference_manifest.cache_key)
        response = analysis_service.analyze(
            payload,
            prediction,
            forced_alignment=forced_alignment,
            reference_alignment=reference_alignment,
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
    alignment = _align_or_raise(
        audio_bytes=tts_audio.audio_bytes,
        original_filename="tts-reference.wav",
        text=script,
        language=language or settings.aligner_language,
    )
    return reference_cache.put_reference(request, tts_audio.audio_bytes, alignment)


def _get_or_create_tts_asset(
    text: str,
    language: str | None,
    tts_provider: str | None,
    tts_model: str | None,
    voice_id: str | None,
    speaking_rate: float | None,
    audio_format: str,
) -> TTSAssetManifest:
    request = TTSAssetRequest(
        text=text,
        language=language or settings.aligner_language,
        tts_provider=tts_provider or settings.tts_provider,
        tts_model=tts_model or settings.tts_model,
        voice_id=voice_id or settings.tts_voice_id,
        speaking_rate=speaking_rate if speaking_rate is not None else settings.tts_speaking_rate,
        audio_format=audio_format,
    )
    manifest = tts_asset_store.get_manifest(request.cache_key())
    if manifest is not None:
        return manifest

    if request.tts_provider != "edge":
        raise RuntimeError(f"unsupported TTS provider: {request.tts_provider}")
    if request.audio_format != "wav_16khz_mono":
        raise RuntimeError(f"unsupported TTS audio format: {request.audio_format}")

    generator = EdgeTTSReferenceGenerator(
        voice_id=request.voice_id,
        speaking_rate=request.speaking_rate,
        model=request.tts_model,
    )
    tts_audio = generator.generate(request.text)
    return tts_asset_store.put_asset(request, tts_audio.audio_bytes)


def _with_tts_audio_url(manifest: TTSAssetManifest) -> TTSAssetManifest:
    audio_path = f"/tts-assets/{manifest.cache_key}/audio"
    if settings.tts_asset_public_base_url:
        audio_url = f"{settings.tts_asset_public_base_url}{audio_path}"
    else:
        audio_url = audio_path
    return manifest.model_copy(update={"audio_url": audio_url})


def _compact_analysis_response(response: PronunciationAnalysisResponse) -> None:
    target_units = {item.target_unit for item in response.diagnostic_candidates[:3] if item.target_unit}
    response.diagnostic_candidates = response.diagnostic_candidates[:3]
    response.alignments = _compact_alignments(response.alignments, target_units)
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
