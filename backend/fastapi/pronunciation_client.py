import os
import subprocess
import tempfile

import httpx


MDD_API_BASE_URL = os.getenv("MDD_API_BASE_URL", "").rstrip("/")
PRONUNCIATION_ANALYSIS_ENDPOINT = os.getenv(
    "BACKEND_PRONUNCIATION_ANALYSIS_ENDPOINT",
    "/analyze-pronunciation-llm",
)
PRONUNCIATION_ANALYSIS_TIMEOUT_SECONDS = float(
    os.getenv("BACKEND_PRONUNCIATION_ANALYSIS_TIMEOUT_SECONDS", "180")
)


class PronunciationAnalysisError(RuntimeError):
    pass


def _convert_webm_to_wav(webm_bytes: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f_in:
        f_in.write(webm_bytes)
        input_path = f_in.name

    output_path = input_path.replace(".webm", ".wav")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", input_path,
                "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(output_path, "rb") as f_out:
            return f_out.read()
    finally:
        import os as _os
        _os.unlink(input_path)
        _os.unlink(output_path)


async def analyze_pronunciation(audio_bytes, filename, target_text):
    if not MDD_API_BASE_URL:
        raise PronunciationAnalysisError("MDD_API_BASE_URL 환경변수가 설정되어 있지 않습니다.")

    endpoint = PRONUNCIATION_ANALYSIS_ENDPOINT
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    # webm → wav 변환 (ml_core sox는 webm 미지원)
    actual_bytes = audio_bytes
    actual_filename = filename or "recording.wav"
    if actual_filename.lower().endswith(".webm"):
        actual_bytes = _convert_webm_to_wav(audio_bytes)
        actual_filename = actual_filename[:-5] + ".wav"

    data = {
        "script": target_text,
        "language": "Korean",
        "feedback_language": "ko",
        "use_tts_reference": "true",
        "debug": "false",
    }
    files = {
        "audio": (actual_filename, actual_bytes, "application/octet-stream"),
    }

    try:
        async with httpx.AsyncClient(timeout=PRONUNCIATION_ANALYSIS_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{MDD_API_BASE_URL}{endpoint}",
                data=data,
                files=files,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = _extract_detail(exc.response)
        raise PronunciationAnalysisError(f"ml_core 발음 분석 실패: {detail}") from exc
    except httpx.HTTPError as exc:
        raise PronunciationAnalysisError(f"ml_core 발음 분석 서비스 연결 실패: {exc}") from exc


def build_pronunciation_result(analysis):
    score = analysis.get("pronunciation_score", {}).get("overall")
    if score is None:
        raise PronunciationAnalysisError("ml_core 응답에 pronunciation_score.overall이 없습니다.")

    feedback = _extract_feedback(analysis)
    return int(round(max(0, min(100, float(score))))), feedback


def _extract_feedback(analysis):
    llm_feedback = analysis.get("llm_feedback") or {}
    if llm_feedback.get("summary"):
        return llm_feedback["summary"]

    diagnostics = analysis.get("diagnostic_candidates") or []
    if diagnostics:
        top = diagnostics[0]
        target = top.get("target_unit")
        rationale = top.get("rationale") or "발음에서 개선할 부분이 감지되었습니다."
        if target:
            return f"{target} 부분을 다시 연습해 보세요. {rationale}"
        return rationale

    score = analysis.get("pronunciation_score", {})
    if score.get("note"):
        return score["note"]

    return "발음 분석이 완료되었습니다."


def _extract_detail(response):
    try:
        payload = response.json()
    except ValueError:
        return response.text
    if isinstance(payload, dict) and "detail" in payload:
        return payload["detail"]
    return payload
