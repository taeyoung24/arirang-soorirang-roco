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
    VOWEL_BASELINES = {
        "ㅏ": {"f1": 750.0, "f2": 1400.0},
        "ㅓ": {"f1": 620.0, "f2": 1150.0},
        "ㅗ": {"f1": 430.0, "f2": 900.0},
        "ㅜ": {"f1": 360.0, "f2": 980.0},
        "ㅡ": {"f1": 380.0, "f2": 1350.0},
        "ㅣ": {"f1": 300.0, "f2": 2300.0},
        "ㅔ": {"f1": 470.0, "f2": 1900.0},
        "ㅐ": {"f1": 520.0, "f2": 1750.0},
    }

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
        formants = self._estimate_formants_lpc(segment, sample_rate)
        baseline = self.VOWEL_BASELINES.get(label)
        f1 = formants[0] if len(formants) >= 1 else None
        f2 = formants[1] if len(formants) >= 2 else None
        return [
            self._baseline_feature("f1_hz", f1, baseline["f1"] if baseline else None),
            self._baseline_feature("f2_hz", f2, baseline["f2"] if baseline else None),
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
    def _baseline_feature(name: str, value: float | None, baseline_mean: float | None) -> FeatureMeasurement:
        zscore = None
        if value is not None and baseline_mean is not None:
            zscore = round((value - baseline_mean) / max(baseline_mean * 0.15, 1.0), 3)
        return FeatureMeasurement(
            name=name,
            value=value,
            unit="Hz",
            baseline_mean=baseline_mean,
            zscore=zscore,
            reliability="medium" if value is not None else "low",
            note="LPC formant estimate; still sensitive to alignment and recording quality.",
        )

    @staticmethod
    def _estimate_formants_lpc(segment: np.ndarray, sample_rate: int) -> list[float]:
        if len(segment) < int(sample_rate * 0.03):
            return []
        signal = segment.astype(np.float64)
        signal = signal - np.mean(signal)
        if float(np.sqrt(np.mean(np.square(signal)) + 1e-9)) < 0.005:
            return []
        signal = np.append(signal[0], signal[1:] - 0.97 * signal[:-1])
        signal = signal * np.hamming(len(signal))
        order = min(12, max(4, int(sample_rate / 1000) + 2))
        autocorr = np.correlate(signal, signal, mode="full")[len(signal) - 1 : len(signal) + order]
        if len(autocorr) <= order or autocorr[0] <= 1e-9:
            return []
        matrix = np.empty((order, order), dtype=np.float64)
        for row in range(order):
            for col in range(order):
                matrix[row, col] = autocorr[abs(row - col)]
        try:
            coeffs = np.linalg.solve(matrix, -autocorr[1 : order + 1])
        except np.linalg.LinAlgError:
            return []
        roots = np.roots(np.concatenate(([1.0], coeffs)))
        roots = [root for root in roots if np.imag(root) >= 0.01]
        angles = np.arctan2(np.imag(roots), np.real(roots))
        freqs = sorted(float(angle * sample_rate / (2 * math.pi)) for angle in angles)
        return [round(freq, 2) for freq in freqs if 150.0 <= freq <= 4500.0][:3]

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


class PraatAcousticFeatureExtractor(StandardAcousticFeatureExtractor):
    def __init__(self):
        try:
            import parselmouth
        except ImportError as exc:
            raise RuntimeError("praat-parselmouth is not installed.") from exc
        self.parselmouth = parselmouth

    def _extract_vowel_features(self, label: str, segment: np.ndarray, sample_rate: int) -> list[FeatureMeasurement]:
        baseline = self.VOWEL_BASELINES.get(label)
        analysis_segment = self._center_window(segment, sample_rate)
        sound = self._sound(analysis_segment, sample_rate)
        formants = self._praat_formants(sound)
        pitch = self._praat_pitch(sound)
        intensity = self._praat_intensity(sound)
        centroid = self._spectral_centroid(analysis_segment, sample_rate)
        f1 = formants.get(1)
        f2 = formants.get(2)
        return [
            self._praat_baseline_feature("f1_hz", f1, baseline["f1"] if baseline else None),
            self._praat_baseline_feature("f2_hz", f2, baseline["f2"] if baseline else None),
            FeatureMeasurement(
                name="pitch_hz",
                value=pitch,
                unit="Hz",
                reliability="high" if pitch is not None else "low",
                note="Praat pitch estimate.",
            ),
            FeatureMeasurement(
                name="intensity_db",
                value=intensity,
                unit="dB",
                reliability="high" if intensity is not None else "low",
                note="Praat intensity estimate.",
            ),
            FeatureMeasurement(
                name="spectral_centroid_hz",
                value=centroid,
                unit="Hz",
                reliability="medium",
            ),
        ]

    def extract_prosody(self, audio: AudioBuffer) -> ProsodySummary:
        if len(audio.samples) == 0:
            return ProsodySummary(notes=["Empty audio input."])
        sound = self._sound(audio.samples, audio.sample_rate)
        try:
            pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=400)
            intensity = sound.to_intensity(time_step=0.01, minimum_pitch=75)
        except Exception:
            return super().extract_prosody(audio)

        pitch_values = pitch.selected_array["frequency"]
        voiced = [float(value) for value in pitch_values if value > 0]
        f0_mean = round(float(np.mean(voiced)), 2) if voiced else None
        f0_range = None
        if len(voiced) >= 2:
            f0_range = round(12.0 * math.log2(max(voiced) / max(min(voiced), 1e-6)), 2)
        phrase_final_slope = None
        if len(voiced) >= 4:
            tail = voiced[-4:]
            phrase_final_slope = round((tail[-1] - tail[0]) / max(len(tail) - 1, 1), 2)

        intensity_values = np.asarray(intensity.values).reshape(-1)
        finite_intensity = intensity_values[np.isfinite(intensity_values)]
        pause_count = 0
        pause_total_ms = 0
        if len(finite_intensity) > 0:
            threshold = float(np.percentile(finite_intensity, 20))
            in_pause = False
            frame_ms = 10
            for value in finite_intensity:
                is_pause = float(value) < threshold
                if is_pause and not in_pause:
                    pause_count += 1
                if is_pause:
                    pause_total_ms += frame_ms
                in_pause = is_pause

        speech_rate = round(1000.0 / max(audio.duration_ms, 1) * max(1, len(voiced) // 25), 2)
        return ProsodySummary(
            speech_rate_syllables_per_second=speech_rate,
            articulation_rate_syllables_per_second=speech_rate,
            pause_count=pause_count,
            pause_total_ms=pause_total_ms,
            utterance_f0_mean_hz=f0_mean,
            utterance_f0_range_semitones=f0_range,
            phrase_final_f0_slope=phrase_final_slope,
            notes=["Pitch and intensity are measured with Praat via parselmouth."],
        )

    def _sound(self, samples: np.ndarray, sample_rate: int):
        return self.parselmouth.Sound(samples.astype(np.float64), sampling_frequency=sample_rate)

    @staticmethod
    def _center_window(segment: np.ndarray, sample_rate: int) -> np.ndarray:
        min_samples = int(sample_rate * 0.04)
        if len(segment) <= min_samples:
            return segment
        start = int(len(segment) * 0.2)
        end = int(len(segment) * 0.8)
        if end - start < min_samples:
            midpoint = len(segment) // 2
            half = min_samples // 2
            start = max(0, midpoint - half)
            end = min(len(segment), midpoint + half)
        return segment[start:end]

    @staticmethod
    def _praat_baseline_feature(name: str, value: float | None, baseline_mean: float | None) -> FeatureMeasurement:
        zscore = None
        if value is not None and baseline_mean is not None:
            zscore = round((value - baseline_mean) / max(baseline_mean * 0.15, 1.0), 3)
        return FeatureMeasurement(
            name=name,
            value=value,
            unit="Hz",
            baseline_mean=baseline_mean,
            zscore=zscore,
            reliability="high" if value is not None else "low",
            note="Praat Burg formant estimate via parselmouth.",
        )

    @staticmethod
    def _median(values: list[float]) -> float | None:
        finite = [value for value in values if math.isfinite(value) and value > 0]
        if not finite:
            return None
        return round(float(np.median(finite)), 2)

    def _praat_formants(self, sound) -> dict[int, float]:
        try:
            formant = sound.to_formant_burg(
                time_step=0.005,
                max_number_of_formants=5,
                maximum_formant=5500,
                window_length=0.025,
                pre_emphasis_from=50,
            )
        except Exception:
            return {}
        duration = float(sound.duration)
        if duration <= 0:
            return {}
        times = [duration * ratio for ratio in (0.25, 0.5, 0.75)]
        result: dict[int, float] = {}
        for index in (1, 2, 3):
            values = [
                float(formant.get_value_at_time(index, time))
                for time in times
            ]
            value = self._median(values)
            if value is not None:
                result[index] = value
        return result

    def _praat_pitch(self, sound) -> float | None:
        try:
            pitch = sound.to_pitch(time_step=0.005, pitch_floor=75, pitch_ceiling=400)
        except Exception:
            return None
        values = pitch.selected_array["frequency"]
        return self._median([float(value) for value in values])

    def _praat_intensity(self, sound) -> float | None:
        try:
            intensity = sound.to_intensity(time_step=0.005, minimum_pitch=75)
        except Exception:
            return None
        values = np.asarray(intensity.values).reshape(-1)
        return self._median([float(value) for value in values])


def create_default_feature_extractor() -> AcousticFeatureExtractor:
    try:
        return PraatAcousticFeatureExtractor()
    except RuntimeError:
        return StandardAcousticFeatureExtractor()
