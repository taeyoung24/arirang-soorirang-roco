from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Protocol

import numpy as np
from scipy.signal import correlate

from app.acoustic_schemas import (
    AlignmentUnit,
    FeatureMeasurement,
    ProsodySummary,
    SegmentFeatureBundle,
    TimeInterval,
)


@dataclass(frozen=True)
class AudioBuffer:
    samples: np.ndarray
    sample_rate: int

    @property
    def duration_ms(self) -> int:
        if self.sample_rate <= 0:
            return 0
        return int(round(len(self.samples) * 1000 / self.sample_rate))


class AcousticFeatureExtractor(Protocol):
    def extract_segment_features(
        self,
        audio: AudioBuffer,
        alignments: Iterable[AlignmentUnit],
    ) -> list[SegmentFeatureBundle]:
        ...

    def extract_prosody(self, audio: AudioBuffer) -> ProsodySummary:
        ...


class StandardAcousticFeatureExtractor:
    VOWELS = {
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    }
    ASPIRATED_TO_LENIS = {"ㅋ": "ㄱ", "ㅌ": "ㄷ", "ㅍ": "ㅂ", "ㅊ": "ㅈ"}
    TENSE = {"ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"}
    def extract_segment_features(
        self,
        audio: AudioBuffer,
        alignments: Iterable[AlignmentUnit],
    ) -> list[SegmentFeatureBundle]:
        features: list[SegmentFeatureBundle] = []
        for unit in alignments:
            if unit.unit_type != "phoneme":
                continue
            start = max(0, int(unit.start_ms * audio.sample_rate / 1000))
            end = min(len(audio.samples), int(unit.end_ms * audio.sample_rate / 1000))
            segment = audio.samples[start:end]
            if len(segment) == 0:
                continue
            interval = TimeInterval(
                start_ms=unit.start_ms,
                end_ms=unit.end_ms,
                confidence=unit.confidence,
            )
            measurements = [
                FeatureMeasurement(
                    name="duration_ms",
                    value=float(unit.end_ms - unit.start_ms),
                    unit="ms",
                    reliability="medium" if unit.source == "forced" else "low",
                ),
                FeatureMeasurement(
                    name="rms_energy",
                    value=round(float(np.sqrt(np.mean(np.square(segment)) + 1e-9)), 5),
                    reliability="medium",
                ),
            ]
            if unit.label in self.VOWELS:
                measurements.extend(self._extract_vowel_features(unit.label, segment, audio.sample_rate))
            else:
                measurements.extend(self._extract_consonant_features(unit.label, segment, audio.sample_rate))
            features.append(
                SegmentFeatureBundle(
                    label=unit.label,
                    unit_type=unit.unit_type,
                    interval=interval,
                    features=measurements,
                )
            )
        return features

    def _extract_vowel_features(self, label: str, segment: np.ndarray, sample_rate: int) -> list[FeatureMeasurement]:
        pitch = self._estimate_pitch(segment, sample_rate)
        centroid = self._spectral_centroid(segment, sample_rate)
        return [
            FeatureMeasurement(
                name="pitch_hz",
                value=pitch,
                unit="Hz",
                reliability="medium" if pitch is not None else "low",
                note="Normalized autocorrelation estimate.",
            ),
            FeatureMeasurement(
                name="spectral_centroid_hz",
                value=centroid,
                unit="Hz",
                reliability="medium",
            ),
        ]

    def _extract_consonant_features(self, label: str, segment: np.ndarray, sample_rate: int) -> list[FeatureMeasurement]:
        duration_ms = len(segment) * 1000.0 / sample_rate
        centroid = self._spectral_centroid(segment, sample_rate)
        zero_cross_rate = float(np.mean(np.abs(np.diff(np.signbit(segment))).astype(np.float32)))
        high_freq_ratio = self._high_frequency_ratio(segment, sample_rate)
        measurements = [
            FeatureMeasurement(name="spectral_centroid_hz", value=centroid, unit="Hz", reliability="medium"),
            FeatureMeasurement(name="zero_cross_rate", value=round(zero_cross_rate, 5), reliability="medium"),
            FeatureMeasurement(name="high_frequency_ratio", value=high_freq_ratio, reliability="medium"),
        ]
        if label in self.ASPIRATED_TO_LENIS or label in self.TENSE:
            measurements.append(
                FeatureMeasurement(
                    name="burst_peak",
                    value=self._burst_peak(segment),
                    reliability="medium",
                    note="Peak energy within the aligned consonant window.",
                )
            )
        if duration_ms > 25:
            measurements.append(
                FeatureMeasurement(
                    name="frication_ms",
                    value=round(duration_ms, 2),
                    unit="ms",
                    reliability="low",
                    note="Duration proxy; true frication boundaries need a dedicated segmenter.",
                )
            )
        return measurements

    def extract_prosody(self, audio: AudioBuffer) -> ProsodySummary:
        if len(audio.samples) == 0:
            return ProsodySummary(notes=["Empty audio input."])
        frame_length = max(1, int(audio.sample_rate * 0.04))
        hop_length = max(1, int(audio.sample_rate * 0.01))
        rms_values: list[float] = []
        pitches: list[float | None] = []
        for start in range(0, max(1, len(audio.samples) - frame_length), hop_length):
            frame = audio.samples[start : start + frame_length]
            rms_values.append(float(np.sqrt(np.mean(np.square(frame)) + 1e-9)))
            pitches.append(self._estimate_pitch(frame, audio.sample_rate))
        if not rms_values:
            return ProsodySummary(notes=["Audio too short for frame analysis."])

        threshold = max(0.005, float(np.percentile(rms_values, 20)) * 0.85)
        pause_count = 0
        pause_total_ms = 0
        in_pause = False
        for rms in rms_values:
            is_pause = rms < threshold
            if is_pause and not in_pause:
                pause_count += 1
            if is_pause:
                pause_total_ms += int(round(hop_length * 1000 / audio.sample_rate))
            in_pause = is_pause

        voiced_pitches = [pitch for pitch in pitches if pitch is not None]
        f0_mean = round(float(np.mean(voiced_pitches)), 2) if voiced_pitches else None
        f0_range = None
        if len(voiced_pitches) >= 2:
            f0_range = round(12.0 * math.log2(max(voiced_pitches) / max(min(voiced_pitches), 1e-6)), 2)
        speech_rate = round(1000.0 / max(audio.duration_ms, 1) * max(1, len(rms_values) // 24), 2)
        phrase_final_slope = None
        if len(voiced_pitches) >= 4:
            tail = voiced_pitches[-4:]
            phrase_final_slope = round((tail[-1] - tail[0]) / max(len(tail) - 1, 1), 2)
        return ProsodySummary(
            speech_rate_syllables_per_second=speech_rate,
            articulation_rate_syllables_per_second=speech_rate,
            pause_count=pause_count,
            pause_total_ms=pause_total_ms,
            utterance_f0_mean_hz=f0_mean,
            utterance_f0_range_semitones=f0_range,
            phrase_final_f0_slope=phrase_final_slope,
            notes=["Prosody uses frame-level acoustic measurements; syllable nuclei are not model-detected yet."],
        )

    @staticmethod
    def _spectral_centroid(segment: np.ndarray, sample_rate: int) -> float | None:
        if len(segment) == 0:
            return None
        window = np.hanning(len(segment))
        spectrum = np.abs(np.fft.rfft(segment * window))
        if not np.any(spectrum):
            return None
        freqs = np.fft.rfftfreq(len(segment), d=1.0 / sample_rate)
        centroid = float(np.sum(freqs * spectrum) / np.sum(spectrum))
        return round(centroid, 2)

    @staticmethod
    def _high_frequency_ratio(segment: np.ndarray, sample_rate: int) -> float | None:
        spectrum = np.abs(np.fft.rfft(segment * np.hanning(len(segment))))
        if len(spectrum) == 0:
            return None
        freqs = np.fft.rfftfreq(len(segment), d=1.0 / sample_rate)
        total = float(np.sum(spectrum)) + 1e-9
        high = float(np.sum(spectrum[freqs >= 3000]))
        return round(high / total, 5)

    @staticmethod
    def _burst_peak(segment: np.ndarray) -> float:
        return round(float(np.max(np.abs(segment))), 5)

    @staticmethod
    def _estimate_pitch(segment: np.ndarray, sample_rate: int) -> float | None:
        if len(segment) < sample_rate // 50:
            return None
        segment = segment.astype(np.float64) - np.mean(segment)
        energy = float(np.sqrt(np.mean(np.square(segment)) + 1e-9))
        if energy < 0.01:
            return None
        corr = correlate(segment, segment, mode="full")
        corr = corr[len(corr) // 2 :]
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
        lag = best + min_lag
        return round(sample_rate / lag, 2)


def create_default_feature_extractor() -> AcousticFeatureExtractor:
    return StandardAcousticFeatureExtractor()
