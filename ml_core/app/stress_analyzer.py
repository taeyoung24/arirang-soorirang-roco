from __future__ import annotations

import io
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np
import soundfile as sf
from scipy.signal import correlate, resample_poly

from app.acoustic_feature_extractor import AudioBuffer


@dataclass
class SyllableStressResult:
    syllable: str
    index: int
    user_f0: Optional[float]
    ref_f0: Optional[float]
    user_energy: float
    ref_energy: float
    is_stressed_ref: bool
    is_stressed_user: bool
    is_mismatch: bool


class StressAnalyzer:
    F0_STRESS_THRESHOLD = 1.15    # 15% above utterance mean = stressed
    ENERGY_STRESS_THRESHOLD = 1.2  # 20% above utterance mean = stressed

    def analyze(
        self,
        user_audio_bytes: bytes,
        ref_audio_bytes: bytes,
        script: str,
    ) -> list[SyllableStressResult]:
        syllables = self._extract_syllables(script)
        if not syllables:
            return []

        user_audio = self._load_audio(user_audio_bytes)
        ref_audio = self._load_audio(ref_audio_bytes)

        user_features = self._extract_syllable_features(user_audio, len(syllables))
        ref_features = self._extract_syllable_features(ref_audio, len(syllables))

        results = []
        for i, syllable in enumerate(syllables):
            user_f0_norm, user_energy_norm = user_features[i]
            ref_f0_norm, ref_energy_norm = ref_features[i]

            is_stressed_ref = self._is_stressed(ref_f0_norm, ref_energy_norm)
            is_stressed_user = self._is_stressed(user_f0_norm, user_energy_norm)

            results.append(SyllableStressResult(
                syllable=syllable,
                index=i,
                user_f0=user_f0_norm,
                ref_f0=ref_f0_norm,
                user_energy=user_energy_norm,
                ref_energy=ref_energy_norm,
                is_stressed_ref=is_stressed_ref,
                is_stressed_user=is_stressed_user,
                is_mismatch=is_stressed_ref != is_stressed_user,
            ))

        return results

    def _is_stressed(self, f0_norm: Optional[float], energy_norm: float) -> bool:
        f0_stressed = f0_norm is not None and f0_norm >= self.F0_STRESS_THRESHOLD
        energy_stressed = energy_norm >= self.ENERGY_STRESS_THRESHOLD
        return f0_stressed or energy_stressed

    def _extract_syllable_features(
        self, audio: AudioBuffer, num_syllables: int,
    ) -> list[tuple[Optional[float], float]]:
        frames_per_syllable = max(1, len(audio.samples) // num_syllables)
        raw: list[tuple[Optional[float], float]] = []

        for i in range(num_syllables):
            start = i * frames_per_syllable
            end = len(audio.samples) if i == num_syllables - 1 else (i + 1) * frames_per_syllable
            segment = audio.samples[start:end]
            f0 = self._estimate_pitch(segment, audio.sample_rate)
            energy = float(np.sqrt(np.mean(np.square(segment)) + 1e-9))
            raw.append((f0, energy))

        voiced_f0s = [f0 for f0, _ in raw if f0 is not None]
        energies = [e for _, e in raw]
        mean_f0 = float(np.mean(voiced_f0s)) if voiced_f0s else 1.0
        mean_energy = float(np.mean(energies)) if energies else 1.0

        normalized = []
        for f0, energy in raw:
            f0_norm = round(f0 / max(mean_f0, 1e-6), 4) if f0 is not None else None
            energy_norm = round(energy / max(mean_energy, 1e-6), 4)
            normalized.append((f0_norm, energy_norm))

        return normalized

    @staticmethod
    def _extract_syllables(script: str) -> list[str]:
        return [ch for ch in script if "\uAC00" <= ch <= "\uD7A3"]

    @staticmethod
    def _load_audio(audio_bytes: bytes) -> AudioBuffer:
        with sf.SoundFile(io.BytesIO(audio_bytes)) as f:
            samples = f.read(dtype="float32")
            sr = int(f.samplerate)
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)
        if sr != 16000 and sr > 0:
            gcd = math.gcd(sr, 16000)
            samples = resample_poly(samples, 16000 // gcd, sr // gcd).astype(np.float32)
            sr = 16000
        return AudioBuffer(samples=samples.astype(np.float32), sample_rate=sr)

    @staticmethod
    def _estimate_pitch(segment: np.ndarray, sample_rate: int) -> Optional[float]:
        if len(segment) < sample_rate // 50:
            return None
        segment = segment.astype(np.float64) - np.mean(segment)
        if float(np.sqrt(np.mean(np.square(segment)) + 1e-9)) < 0.01:
            return None
        corr = correlate(segment, segment, mode="full")
        corr = corr[len(corr) // 2:]
        if corr[0] <= 1e-9:
            return None
        corr = corr / corr[0]
        min_lag = max(1, sample_rate // 400)
        max_lag = max(min_lag + 1, sample_rate // 75)
        window = corr[min_lag:max_lag]
        if len(window) == 0:
            return None
        best = int(np.argmax(window))
        if window[best] < 0.3:
            return None
        return round(sample_rate / (best + min_lag), 2)
