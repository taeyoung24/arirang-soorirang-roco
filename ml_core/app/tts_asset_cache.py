from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel

from app.reference_cache import normalize_reference_script


class TTSAssetRequest(BaseModel):
    text: str
    language: str = "Korean"
    tts_provider: str = "edge"
    tts_model: str = "edge-tts"
    voice_id: str = "ko-KR-SunHiNeural"
    speaking_rate: float = 1.0
    audio_format: str = "wav_16khz_mono"
    cache_schema_version: str = "v1"

    @property
    def normalized_text(self) -> str:
        return normalize_reference_script(self.text)

    def cache_key(self) -> str:
        parts = [
            self.normalized_text,
            self.language,
            self.tts_provider,
            self.tts_model,
            self.voice_id,
            str(self.speaking_rate),
            self.audio_format,
            self.cache_schema_version,
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class TTSAssetManifest(BaseModel):
    cache_key: str
    status: Literal["cached", "generated"] = "generated"
    text: str
    normalized_text: str
    language: str
    tts_provider: str
    tts_model: str
    voice_id: str
    speaking_rate: float
    audio_format: str
    cache_schema_version: str
    object_bucket: str
    audio_object_key: str
    manifest_object_key: str
    created_at: str


@dataclass(frozen=True)
class TTSAssetObjectKeys:
    prefix: str
    audio: str
    manifest: str


class TTSAssetStore:
    def get_manifest(self, key: str) -> TTSAssetManifest | None:
        raise NotImplementedError

    def put_asset(self, request: TTSAssetRequest, audio_bytes: bytes) -> TTSAssetManifest:
        raise NotImplementedError


class DisabledTTSAssetStore(TTSAssetStore):
    def get_manifest(self, key: str) -> TTSAssetManifest | None:
        return None

    def put_asset(self, request: TTSAssetRequest, audio_bytes: bytes) -> TTSAssetManifest:
        raise RuntimeError("TTS asset storage is disabled")


class MinioTTSAssetStore(TTSAssetStore):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        from minio import Minio

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self.bucket = bucket

    def get_manifest(self, key: str) -> TTSAssetManifest | None:
        keys = self._keys(key)
        try:
            response = self.client.get_object(self.bucket, keys.manifest)
            try:
                payload = response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as exc:
            if self._is_not_found(exc):
                return None
            raise
        manifest = TTSAssetManifest.model_validate_json(payload)
        manifest.status = "cached"
        return manifest

    def put_asset(self, request: TTSAssetRequest, audio_bytes: bytes) -> TTSAssetManifest:
        self._ensure_bucket()
        key = request.cache_key()
        keys = self._keys(key)
        manifest = TTSAssetManifest(
            cache_key=key,
            status="generated",
            text=request.text,
            normalized_text=request.normalized_text,
            language=request.language,
            tts_provider=request.tts_provider,
            tts_model=request.tts_model,
            voice_id=request.voice_id,
            speaking_rate=request.speaking_rate,
            audio_format=request.audio_format,
            cache_schema_version=request.cache_schema_version,
            object_bucket=self.bucket,
            audio_object_key=keys.audio,
            manifest_object_key=keys.manifest,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        manifest_json = manifest.model_dump_json(exclude_none=True, indent=2).encode("utf-8")
        self._put_bytes(keys.audio, audio_bytes, "audio/wav")
        self._put_bytes(keys.manifest, manifest_json, "application/json")
        return manifest

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def _put_bytes(self, object_key: str, payload: bytes, content_type: str) -> None:
        self.client.put_object(
            self.bucket,
            object_key,
            io.BytesIO(payload),
            length=len(payload),
            content_type=content_type,
        )

    @staticmethod
    def _keys(cache_key: str) -> TTSAssetObjectKeys:
        prefix = f"tts-audio/{cache_key}"
        return TTSAssetObjectKeys(
            prefix=prefix,
            audio=f"{prefix}/audio.wav",
            manifest=f"{prefix}/manifest.json",
        )

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        code = getattr(exc, "code", None)
        response = getattr(exc, "response", None)
        status = getattr(response, "status", None)
        return code in {"NoSuchKey", "NoSuchBucket"} or status == 404


def create_tts_asset_store(settings: Any) -> TTSAssetStore:
    if not settings.object_storage_enabled:
        return DisabledTTSAssetStore()
    return MinioTTSAssetStore(
        endpoint=settings.object_storage_endpoint,
        access_key=settings.object_storage_access_key,
        secret_key=settings.object_storage_secret_key,
        bucket=settings.object_storage_bucket,
        secure=settings.object_storage_secure,
    )
