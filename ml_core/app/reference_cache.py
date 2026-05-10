from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.acoustic_schemas import ForcedAlignmentResponse


def normalize_reference_script(script: str) -> str:
    return re.sub(r"\s+", " ", script.strip())


class ReferenceCacheRequest(BaseModel):
    script: str
    language: str = "Korean"
    tts_provider: str = "unknown"
    tts_model: str = "unknown"
    voice_id: str = "default"
    speaking_rate: float = 1.0
    audio_format: str = "wav_16khz_mono"
    aligner_model_id: str = "Qwen/Qwen3-ForcedAligner-0.6B"
    alignment_resolution_ms: int = Field(default=80, ge=1)
    cache_schema_version: str = "v2"

    @property
    def normalized_script(self) -> str:
        return normalize_reference_script(self.script)

    def cache_key(self) -> str:
        parts = [
            self.normalized_script,
            self.language,
            self.tts_provider,
            self.tts_model,
            self.voice_id,
            str(self.speaking_rate),
            self.audio_format,
            self.aligner_model_id,
            str(self.alignment_resolution_ms),
            self.cache_schema_version,
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class ReferenceCacheManifest(BaseModel):
    cache_key: str
    script: str
    normalized_script: str
    language: str
    tts_provider: str
    tts_model: str
    voice_id: str
    speaking_rate: float
    audio_format: str
    aligner_model_id: str
    alignment_resolution_ms: int
    cache_schema_version: str
    audio_object_key: str
    alignment_object_key: str
    created_at: str


@dataclass(frozen=True)
class ReferenceCacheObjectKeys:
    prefix: str
    audio: str
    alignment: str
    manifest: str


class ReferenceCacheStore:
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def get_manifest(self, key: str) -> ReferenceCacheManifest | None:
        raise NotImplementedError

    def get_alignment(self, key: str) -> ForcedAlignmentResponse | None:
        raise NotImplementedError

    def put_reference(
        self,
        request: ReferenceCacheRequest,
        audio_bytes: bytes,
        alignment: ForcedAlignmentResponse,
    ) -> ReferenceCacheManifest:
        raise NotImplementedError

    def health(self) -> tuple[str, str | None]:
        raise NotImplementedError


class DisabledReferenceCacheStore(ReferenceCacheStore):
    def exists(self, key: str) -> bool:
        return False

    def get_manifest(self, key: str) -> ReferenceCacheManifest | None:
        return None

    def get_alignment(self, key: str) -> ForcedAlignmentResponse | None:
        return None

    def put_reference(
        self,
        request: ReferenceCacheRequest,
        audio_bytes: bytes,
        alignment: ForcedAlignmentResponse,
    ) -> ReferenceCacheManifest:
        raise RuntimeError("reference cache is disabled")

    def health(self) -> tuple[str, str | None]:
        return "disabled", None


class MinioReferenceCacheStore(ReferenceCacheStore):
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

    def exists(self, key: str) -> bool:
        return self.get_manifest(key) is not None

    def get_manifest(self, key: str) -> ReferenceCacheManifest | None:
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
        return ReferenceCacheManifest.model_validate_json(payload)

    def get_alignment(self, key: str) -> ForcedAlignmentResponse | None:
        keys = self._keys(key)
        try:
            response = self.client.get_object(self.bucket, keys.alignment)
            try:
                payload = response.read()
            finally:
                response.close()
                response.release_conn()
        except Exception as exc:
            if self._is_not_found(exc):
                return None
            raise
        return ForcedAlignmentResponse.model_validate_json(payload)

    def put_reference(
        self,
        request: ReferenceCacheRequest,
        audio_bytes: bytes,
        alignment: ForcedAlignmentResponse,
    ) -> ReferenceCacheManifest:
        self._ensure_bucket()
        key = request.cache_key()
        keys = self._keys(key)
        alignment_json = alignment.model_dump_json(exclude_none=True, indent=2).encode("utf-8")
        manifest = ReferenceCacheManifest(
            cache_key=key,
            script=request.script,
            normalized_script=request.normalized_script,
            language=request.language,
            tts_provider=request.tts_provider,
            tts_model=request.tts_model,
            voice_id=request.voice_id,
            speaking_rate=request.speaking_rate,
            audio_format=request.audio_format,
            aligner_model_id=request.aligner_model_id,
            alignment_resolution_ms=request.alignment_resolution_ms,
            cache_schema_version=request.cache_schema_version,
            audio_object_key=keys.audio,
            alignment_object_key=keys.alignment,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        manifest_json = manifest.model_dump_json(exclude_none=True, indent=2).encode("utf-8")

        self._put_bytes(keys.audio, audio_bytes, "audio/wav")
        self._put_bytes(keys.alignment, alignment_json, "application/json")
        self._put_bytes(keys.manifest, manifest_json, "application/json")
        return manifest

    def health(self) -> tuple[str, str | None]:
        try:
            self._ensure_bucket()
        except Exception as exc:
            return "error", str(exc)
        return "ok", None

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
    def _keys(cache_key: str) -> ReferenceCacheObjectKeys:
        prefix = f"tts-reference/{cache_key}"
        return ReferenceCacheObjectKeys(
            prefix=prefix,
            audio=f"{prefix}/reference.wav",
            alignment=f"{prefix}/alignment.json",
            manifest=f"{prefix}/manifest.json",
        )

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        code = getattr(exc, "code", None)
        response = getattr(exc, "response", None)
        status = getattr(response, "status", None)
        return code in {"NoSuchKey", "NoSuchBucket"} or status == 404


def create_reference_cache_store(settings: Any) -> ReferenceCacheStore:
    if not settings.object_storage_enabled:
        return DisabledReferenceCacheStore()
    return MinioReferenceCacheStore(
        endpoint=settings.object_storage_endpoint,
        access_key=settings.object_storage_access_key,
        secret_key=settings.object_storage_secret_key,
        bucket=settings.object_storage_bucket,
        secure=settings.object_storage_secure,
    )
