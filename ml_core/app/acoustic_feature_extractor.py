from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

import numpy as np

from app.acoustic_schemas import (
    AlignmentUnit,
    PauseInterval,
    ProsodySummary,
    ReferenceDurationComparison,
    ReferencePauseComparison,
    StretchedInterval,
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
    def extract_prosody(
        self,
        audio: AudioBuffer,
        alignments: Iterable[AlignmentUnit] | None = None,
        reference_alignments: Iterable[AlignmentUnit] | None = None,
    ) -> ProsodySummary:
        ...


class StandardAcousticFeatureExtractor:
    MIN_FORCED_PAUSE_MS = 240

    def extract_prosody(
        self,
        audio: AudioBuffer,
        alignments: Iterable[AlignmentUnit] | None = None,
        reference_alignments: Iterable[AlignmentUnit] | None = None,
    ) -> ProsodySummary:
        if len(audio.samples) == 0:
            return ProsodySummary(notes=["Empty audio input."])
        alignment_units = list(alignments or [])
        reference_units = list(reference_alignments or [])
        frame_length = max(1, int(audio.sample_rate * 0.04))
        hop_length = max(1, int(audio.sample_rate * 0.01))
        rms_values: list[float] = []
        for start in range(0, max(1, len(audio.samples) - frame_length), hop_length):
            frame = audio.samples[start : start + frame_length]
            rms_values.append(float(np.sqrt(np.mean(np.square(frame)) + 1e-9)))
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

        speech_rate = round(1000.0 / max(audio.duration_ms, 1) * max(1, len(rms_values) // 24), 2)

        forced_summary = self._forced_alignment_prosody(audio, alignment_units, reference_units)
        if forced_summary is not None:
            forced_summary.notes.append(
                "Speech rate and interior pauses use Qwen3 forced alignment word/syllable timings."
            )
            return forced_summary

        return ProsodySummary(
            speech_rate_syllables_per_second=speech_rate,
            articulation_rate_syllables_per_second=speech_rate,
            pause_count=pause_count,
            pause_total_ms=pause_total_ms,
            timing_source="acoustic",
            rate_reliability="low",
            notes=["Prosody uses frame-level acoustic measurements; syllable nuclei are not model-detected yet."],
        )

    def _forced_alignment_prosody(
        self,
        audio: AudioBuffer,
        alignments: list[AlignmentUnit],
        reference_alignments: list[AlignmentUnit],
    ) -> ProsodySummary | None:
        forced_words = sorted(
            [unit for unit in alignments if unit.source == "forced" and unit.unit_type == "word"],
            key=lambda unit: (unit.start_ms, unit.end_ms),
        )
        forced_syllables = [
            unit for unit in alignments if unit.source == "forced" and unit.unit_type == "syllable"
        ]
        if not forced_words or not forced_syllables:
            return None

        speech_start = max(0, min(unit.start_ms for unit in forced_words))
        speech_end = min(audio.duration_ms, max(unit.end_ms for unit in forced_words))
        speech_duration_ms = max(0, speech_end - speech_start)
        if speech_duration_ms <= 0:
            return None

        pause_intervals: list[PauseInterval] = []
        for current, next_unit in zip(forced_words, forced_words[1:]):
            gap_ms = next_unit.start_ms - current.end_ms
            if gap_ms < self.MIN_FORCED_PAUSE_MS:
                continue
            pause_intervals.append(
                PauseInterval(
                    start_ms=current.end_ms,
                    end_ms=next_unit.start_ms,
                    duration_ms=gap_ms,
                    confidence=min(current.confidence or 0.8, next_unit.confidence or 0.8),
                    source="forced",
                )
            )

        syllable_count = len(forced_syllables)
        pause_total_ms = sum(interval.duration_ms for interval in pause_intervals)
        articulation_duration_ms = max(1, speech_duration_ms - pause_total_ms)
        speech_rate = round(syllable_count / max(speech_duration_ms / 1000.0, 1e-3), 2)
        articulation_rate = round(syllable_count / max(articulation_duration_ms / 1000.0, 1e-3), 2)
        trailing_silence_ms = max(0, audio.duration_ms - speech_end)
        stretched_intervals = self._stretched_intervals(forced_syllables, forced_words)
        slowest_unit = self._slowest_aligned_unit(stretched_intervals)
        reference_comparison = self._reference_comparison(
            forced_words=forced_words,
            forced_syllables=forced_syllables,
            speech_duration_ms=speech_duration_ms,
            reference_alignments=reference_alignments,
        )

        return ProsodySummary(
            speech_rate_syllables_per_second=speech_rate,
            articulation_rate_syllables_per_second=articulation_rate,
            expected_syllable_count=syllable_count,
            aligned_speech_start_ms=speech_start,
            aligned_speech_end_ms=speech_end,
            speech_duration_ms=speech_duration_ms,
            leading_silence_ms=speech_start,
            trailing_silence_ms=trailing_silence_ms,
            pause_count=len(pause_intervals),
            pause_total_ms=pause_total_ms,
            interior_pause_count=len(pause_intervals),
            interior_pause_total_ms=pause_total_ms,
            longest_interior_pause_ms=max((interval.duration_ms for interval in pause_intervals), default=0),
            pause_intervals=pause_intervals,
            slowest_aligned_unit=slowest_unit[0],
            slowest_aligned_unit_ms_per_syllable=slowest_unit[1],
            stretched_intervals=stretched_intervals,
            reference_speech_duration_ms=reference_comparison["reference_speech_duration_ms"],
            speech_duration_ratio=reference_comparison["speech_duration_ratio"],
            reference_duration_comparisons=reference_comparison["duration_comparisons"],
            reference_pause_comparisons=reference_comparison["pause_comparisons"],
            timing_source="forced_alignment",
            reference_timing_source=reference_comparison["reference_timing_source"],
            rate_reliability="medium",
        )

    def _reference_comparison(
        self,
        forced_words: list[AlignmentUnit],
        forced_syllables: list[AlignmentUnit],
        speech_duration_ms: int,
        reference_alignments: list[AlignmentUnit],
    ) -> dict:
        empty = {
            "reference_speech_duration_ms": None,
            "speech_duration_ratio": None,
            "duration_comparisons": [],
            "pause_comparisons": [],
            "reference_timing_source": None,
        }
        reference_words = sorted(
            [unit for unit in reference_alignments if unit.source == "forced" and unit.unit_type == "word"],
            key=lambda unit: (unit.start_ms, unit.end_ms),
        )
        reference_syllables = sorted(
            [unit for unit in reference_alignments if unit.source == "forced" and unit.unit_type == "syllable"],
            key=lambda unit: (unit.start_ms, unit.end_ms),
        )
        if not reference_words or not reference_syllables:
            return empty

        reference_start = min(unit.start_ms for unit in reference_words)
        reference_end = max(unit.end_ms for unit in reference_words)
        reference_speech_duration_ms = max(1, reference_end - reference_start)
        duration_comparisons = self._duration_comparisons(
            forced_syllables,
            reference_syllables,
            unit_type="syllable",
        )
        duration_comparisons.extend(
            self._duration_comparisons(
                forced_words,
                reference_words,
                unit_type="word",
            )
        )
        duration_comparisons = sorted(duration_comparisons, key=lambda item: item.duration_ratio, reverse=True)[:8]

        return {
            "reference_speech_duration_ms": reference_speech_duration_ms,
            "speech_duration_ratio": round(speech_duration_ms / reference_speech_duration_ms, 3),
            "duration_comparisons": duration_comparisons,
            "pause_comparisons": self._pause_comparisons(forced_words, reference_words),
            "reference_timing_source": "tts_reference",
        }

    def _duration_comparisons(
        self,
        user_units: list[AlignmentUnit],
        reference_units: list[AlignmentUnit],
        unit_type: str,
    ) -> list[ReferenceDurationComparison]:
        comparisons: list[ReferenceDurationComparison] = []
        for user, reference in zip(user_units, reference_units):
            if user.label != reference.label:
                continue
            user_duration = max(0, user.end_ms - user.start_ms)
            reference_duration = max(1, reference.end_ms - reference.start_ms)
            comparisons.append(
                ReferenceDurationComparison(
                    label=user.label,
                    unit_type=unit_type,
                    start_ms=user.start_ms,
                    end_ms=user.end_ms,
                    confidence=min(user.confidence or 0.8, reference.confidence or 0.8),
                    user_duration_ms=user_duration,
                    reference_duration_ms=reference_duration,
                    duration_delta_ms=user_duration - reference_duration,
                    duration_ratio=round(user_duration / reference_duration, 3),
                )
            )
        return comparisons

    def _pause_comparisons(
        self,
        user_words: list[AlignmentUnit],
        reference_words: list[AlignmentUnit],
    ) -> list[ReferencePauseComparison]:
        comparisons: list[ReferencePauseComparison] = []
        for user_prev, user_next, reference_prev, reference_next in zip(
            user_words,
            user_words[1:],
            reference_words,
            reference_words[1:],
        ):
            if user_prev.label != reference_prev.label or user_next.label != reference_next.label:
                continue
            user_gap = max(0, user_next.start_ms - user_prev.end_ms)
            reference_gap = max(0, reference_next.start_ms - reference_prev.end_ms)
            duration_delta = user_gap - reference_gap
            ratio = round(user_gap / reference_gap, 3) if reference_gap > 0 else None
            comparisons.append(
                ReferencePauseComparison(
                    start_ms=user_prev.end_ms,
                    end_ms=user_next.start_ms,
                    confidence=min(user_prev.confidence or 0.8, user_next.confidence or 0.8),
                    user_duration_ms=user_gap,
                    reference_duration_ms=reference_gap,
                    duration_delta_ms=duration_delta,
                    duration_ratio=ratio,
                    pause_level=self._pause_level(user_gap, duration_delta),
                    previous_label=user_prev.label,
                    next_label=user_next.label,
                )
            )
        return sorted(comparisons, key=lambda item: item.duration_delta_ms, reverse=True)[:5]

    @staticmethod
    def _pause_level(user_pause_ms: int, duration_delta_ms: int) -> str | None:
        if user_pause_ms >= 1200 and duration_delta_ms >= 800:
            return "high"
        if user_pause_ms >= 500 and duration_delta_ms >= 300:
            return "medium"
        return None

    def _stretched_intervals(
        self,
        forced_syllables: list[AlignmentUnit],
        forced_words: list[AlignmentUnit],
    ) -> list[StretchedInterval]:
        intervals: list[StretchedInterval] = []
        seen: set[tuple[str, int, int]] = set()
        for unit in [*forced_syllables, *forced_words]:
            duration_ms = max(0, unit.end_ms - unit.start_ms)
            syllable_count = 1 if unit.unit_type == "syllable" else self._count_text_syllables(unit.label)
            if syllable_count <= 0 or duration_ms <= 0:
                continue
            identity = (unit.label, unit.start_ms, unit.end_ms)
            if identity in seen:
                continue
            seen.add(identity)
            ms_per_syllable = round(duration_ms / syllable_count, 2)
            intervals.append(
                StretchedInterval(
                    label=unit.label,
                    unit_type=unit.unit_type,
                    start_ms=unit.start_ms,
                    end_ms=unit.end_ms,
                    confidence=unit.confidence,
                    ms_per_syllable=ms_per_syllable,
                    source="forced",
                )
            )
        return sorted(intervals, key=lambda item: item.ms_per_syllable, reverse=True)[:5]

    @staticmethod
    def _slowest_aligned_unit(stretched_intervals: list[StretchedInterval]) -> tuple[str | None, float | None]:
        if not stretched_intervals:
            return None, None
        slowest = stretched_intervals[0]
        return slowest.label, slowest.ms_per_syllable

    @staticmethod
    def _count_text_syllables(text: str) -> int:
        hangul_syllables = sum(1 for char in text if 0xAC00 <= ord(char) <= 0xD7A3)
        if hangul_syllables:
            return hangul_syllables
        return sum(1 for char in text if not char.isspace())


def create_default_feature_extractor() -> AcousticFeatureExtractor:
    return StandardAcousticFeatureExtractor()
