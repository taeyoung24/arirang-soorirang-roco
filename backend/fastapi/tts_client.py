import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MDD_API_BASE_URL = os.getenv("MDD_API_BASE_URL", "").rstrip("/")
TTS_GENERATION_ENABLED = (
    os.getenv("BACKEND_TTS_GENERATION_ENABLED", "false").lower() == "true"
)
TTS_GENERATION_REQUIRED = (
    os.getenv("BACKEND_TTS_GENERATION_REQUIRED", "false").lower() == "true"
)
TTS_GENERATION_RETRIES = int(os.getenv("BACKEND_TTS_GENERATION_RETRIES", "5"))
TTS_GENERATION_RETRY_SECONDS = float(
    os.getenv("BACKEND_TTS_GENERATION_RETRY_SECONDS", "2")
)

def is_tts_generation_enabled():
    return TTS_GENERATION_ENABLED and bool(MDD_API_BASE_URL)


def generate_tts_url(text, language="Korean"):
    if not text or not is_tts_generation_enabled():
        return None

    payload = urlencode({"text": text, "language": language}).encode("utf-8")
    last_error = None
    for attempt in range(1, TTS_GENERATION_RETRIES + 1):
        request = Request(
            f"{MDD_API_BASE_URL}/tts-assets/generate",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                manifest = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < TTS_GENERATION_RETRIES:
                time.sleep(TTS_GENERATION_RETRY_SECONDS)
    else:
        if TTS_GENERATION_REQUIRED:
            raise RuntimeError(f"TTS asset generation failed: {last_error}") from last_error
        print(f"TTS asset generation skipped for text={text!r}: {last_error}")
        return None

    audio_url = manifest.get("audio_url")
    if not audio_url:
        if TTS_GENERATION_REQUIRED:
            raise RuntimeError("TTS asset generation response did not include audio_url")
        print(f"TTS asset generation response did not include audio_url for text={text!r}")
        return None

    return audio_url
