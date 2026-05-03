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
        )
