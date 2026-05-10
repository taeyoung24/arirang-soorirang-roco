from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass


@dataclass
class Settings:
    service_mode: str
    model_path: str
    infer_script_path: str
    dict_path: str
    temp_root: str
    max_tokens: int
    host: str
    port: int
    inference_base_url: str
    inference_timeout_seconds: float
    aligner_base_url: str
    aligner_timeout_seconds: float
    aligner_language: str
    aligner_model_id: str
    gemini_api_key: str
    gemini_model: str
    gemini_timeout_seconds: float
    object_storage_enabled: bool
    object_storage_endpoint: str
    object_storage_access_key: str
    object_storage_secret_key: str
    object_storage_bucket: str
    object_storage_secure: bool
    tts_provider: str
    tts_voice_id: str
    tts_speaking_rate: float
    tts_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            service_mode=os.getenv("MDD_SERVICE_MODE", "standalone"),
            model_path=os.getenv("MDD_MODEL_PATH", "/opt/mdd/checkpoints/checkpoint_mdd_sjr.pt"),
            infer_script_path=os.getenv(
                "MDD_INFER_SCRIPT_PATH",
                "/opt/fairseq/examples/speech_recognition/infer.py",
            ),
            dict_path=os.getenv("MDD_DICT_PATH", "/opt/mdd/service/assets/dict.phn.txt"),
            temp_root=os.getenv("MDD_TEMP_ROOT", os.path.join(tempfile.gettempdir(), "mdd-service")),
            max_tokens=int(os.getenv("MDD_MAX_TOKENS", "12800000")),
            host=os.getenv("MDD_HOST", "0.0.0.0"),
            port=int(os.getenv("MDD_PORT", "8080")),
            inference_base_url=os.getenv("MDD_INFERENCE_BASE_URL", "http://localhost:8080"),
            inference_timeout_seconds=float(os.getenv("MDD_INFERENCE_TIMEOUT_SECONDS", "120")),
            aligner_base_url=os.getenv("MDD_ALIGNER_BASE_URL", "http://localhost:8090"),
            aligner_timeout_seconds=float(os.getenv("MDD_ALIGNER_TIMEOUT_SECONDS", "120")),
            aligner_language=os.getenv("MDD_ALIGNER_LANGUAGE", "Korean"),
            aligner_model_id=os.getenv("MDD_ALIGNER_MODEL_ID", "Qwen/Qwen3-ForcedAligner-0.6B"),
            gemini_api_key=os.getenv("MDD_GEMINI_API_KEY", ""),
            gemini_model=os.getenv("MDD_GEMINI_MODEL", "gemini-2.5-flash"),
            gemini_timeout_seconds=float(os.getenv("MDD_GEMINI_TIMEOUT_SECONDS", "30")),
            object_storage_enabled=os.getenv("MDD_OBJECT_STORAGE_ENABLED", "false").lower() in {"1", "true", "yes"},
            object_storage_endpoint=os.getenv("MDD_OBJECT_STORAGE_ENDPOINT", "localhost:9000"),
            object_storage_access_key=os.getenv("MDD_OBJECT_STORAGE_ACCESS_KEY", "mddadmin"),
            object_storage_secret_key=os.getenv("MDD_OBJECT_STORAGE_SECRET_KEY", "mddadmin123"),
            object_storage_bucket=os.getenv("MDD_OBJECT_STORAGE_BUCKET", "mdd-reference-cache"),
            object_storage_secure=os.getenv("MDD_OBJECT_STORAGE_SECURE", "false").lower() in {"1", "true", "yes"},
            tts_provider=os.getenv("MDD_TTS_PROVIDER", "edge"),
            tts_voice_id=os.getenv("MDD_TTS_VOICE_ID", "ko-KR-SunHiNeural"),
            tts_speaking_rate=float(os.getenv("MDD_TTS_SPEAKING_RATE", "1.0")),
            tts_model=os.getenv("MDD_TTS_MODEL", "edge-tts"),
        )
