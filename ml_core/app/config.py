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
        )
