from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TTSReferenceAudio:
    audio_bytes: bytes
    provider: str
    model: str
    voice_id: str
    speaking_rate: float
    audio_format: str = "wav_16khz_mono"


class TTSReferenceGenerator:
    def generate(self, text: str) -> TTSReferenceAudio:
        raise NotImplementedError


class DisabledTTSReferenceGenerator(TTSReferenceGenerator):
    def generate(self, text: str) -> TTSReferenceAudio:
        raise RuntimeError("TTS reference generation is disabled")


class EdgeTTSReferenceGenerator(TTSReferenceGenerator):
    def __init__(self, voice_id: str, speaking_rate: float = 1.0, model: str = "edge-tts"):
        self.voice_id = voice_id
        self.speaking_rate = speaking_rate
        self.model = model

    def generate(self, text: str) -> TTSReferenceAudio:
        if not text.strip():
            raise ValueError("text must not be empty")
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg executable not found")

        with tempfile.TemporaryDirectory(prefix="mdd-tts-") as tmp_dir:
            tmp_path = Path(tmp_dir)
            mp3_path = tmp_path / "reference.mp3"
            wav_path = tmp_path / "reference.wav"
            asyncio.run(self._write_mp3(text, mp3_path))
            self._convert_to_wav(mp3_path, wav_path)
            return TTSReferenceAudio(
                audio_bytes=wav_path.read_bytes(),
                provider="edge",
                model=self.model,
                voice_id=self.voice_id,
                speaking_rate=self.speaking_rate,
            )

    async def _write_mp3(self, text: str, output_path: Path) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice_id,
            rate=self._edge_rate(),
        )
        await communicate.save(str(output_path))

    def _edge_rate(self) -> str:
        percent = int(round((self.speaking_rate - 1.0) * 100))
        if percent == 0:
            return "+0%"
        sign = "+" if percent > 0 else ""
        return f"{sign}{percent}%"

    @staticmethod
    def _convert_to_wav(src_path: Path, dst_path: Path) -> None:
        command = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(src_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(dst_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "ffmpeg failed to convert TTS audio")


def create_tts_reference_generator(settings: Any) -> TTSReferenceGenerator:
    if settings.tts_provider == "edge":
        return EdgeTTSReferenceGenerator(
            voice_id=settings.tts_voice_id,
            speaking_rate=settings.tts_speaking_rate,
            model=settings.tts_model,
        )
    return DisabledTTSReferenceGenerator()
