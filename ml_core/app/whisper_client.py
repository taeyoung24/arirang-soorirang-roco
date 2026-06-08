from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Optional


@dataclass
class WhisperSegment:
    text: str
    start_ms: int
    end_ms: int
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None


@dataclass
class WhisperTranscription:
    text: str
    language: Optional[str]
    language_probability: Optional[float]
    duration_ms: Optional[int]
    segments: list[WhisperSegment]
    model: str

    @property
    def confidence(self) -> Optional[float]:
        probabilities = [
            1.0 - segment.no_speech_prob
            for segment in self.segments
            if segment.no_speech_prob is not None
        ]
        if not probabilities:
            return self.language_probability
        return max(0.0, min(1.0, sum(probabilities) / len(probabilities)))


class WhisperClient:
    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        compute_type: str = "int8_float16",
        language: str = "ko",
        beam_size: int = 5,
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.beam_size = beam_size
        self._model = None

    def health(self) -> tuple[str, str | None]:
        try:
            import faster_whisper  # noqa: F401
        except ImportError as exc:
            return "unavailable", str(exc)
        return "configured", None

    def transcribe(self, audio_bytes: bytes, original_filename: str = "input.wav") -> WhisperTranscription:
        model = self._load_model()
        suffix = os.path.splitext(original_filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(prefix="whisper-input-", suffix=suffix) as audio_file:
            audio_file.write(audio_bytes)
            audio_file.flush()
            segments_iter, info = model.transcribe(
                audio_file.name,
                language=self.language or None,
                beam_size=self.beam_size,
                vad_filter=True,
            )
            segments = [
                WhisperSegment(
                    text=segment.text.strip(),
                    start_ms=int(round(segment.start * 1000)),
                    end_ms=int(round(segment.end * 1000)),
                    avg_logprob=getattr(segment, "avg_logprob", None),
                    no_speech_prob=getattr(segment, "no_speech_prob", None),
                )
                for segment in segments_iter
            ]
        return WhisperTranscription(
            text=" ".join(segment.text for segment in segments).strip(),
            language=getattr(info, "language", None),
            language_probability=getattr(info, "language_probability", None),
            duration_ms=int(round(getattr(info, "duration", 0.0) * 1000)) if getattr(info, "duration", None) is not None else None,
            segments=segments,
            model=self.model_name,
        )

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(f"faster-whisper or one of its runtime dependencies is unavailable: {exc}") from exc

        kwargs = self._model_kwargs(self.device, self.compute_type)
        try:
            self._model = WhisperModel(self.model_name, **kwargs)
        except Exception as exc:
            if self.device != "auto":
                raise
            fallback_kwargs = self._model_kwargs("cpu", "int8")
            try:
                self._model = WhisperModel(self.model_name, **fallback_kwargs)
            except Exception:
                raise exc
            self.device = "cpu"
            self.compute_type = "int8"
        return self._model

    @staticmethod
    def _model_kwargs(device: str, compute_type: str) -> dict[str, str]:
        kwargs = {"device": device}
        if compute_type and compute_type != "default":
            kwargs["compute_type"] = compute_type
        return kwargs
