from __future__ import annotations

from typing import Any, Optional

import httpx

from app.schemas import PredictResponse


class InferenceClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def predict(self, audio_bytes: bytes, original_filename: str, script: str) -> PredictResponse:
        files = {
            "audio": (original_filename, audio_bytes, "application/octet-stream"),
        }
        data = {"script": script}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/predict", data=data, files=files)
            response.raise_for_status()
            return PredictResponse.model_validate(response.json())

    def health(self) -> tuple[str, Optional[dict[str, Any]]]:
        try:
            with httpx.Client(timeout=min(self.timeout, 5.0)) as client:
                response = client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return "ok", response.json()
        except httpx.HTTPError:
            return "unreachable", None
