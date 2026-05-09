from __future__ import annotations

import io
import math
from typing import Optional

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from app.acoustic_schemas import (
    AcousticEvidencePacket,
    AlignmentUnit,
    AudioQualitySummary,
    EvidencePolicy,
    ForcedAlignmentResponse,
    PronunciationAnalysisResponse,
)
from app.acoustic_feature_extractor import AcousticFeatureExtractor, AudioBuffer, create_default_feature_extractor
from app.diagnostic_engine import DiagnosticEngine
from app.phoneme_edits import align_phonemes
from app.schemas import PredictResponse


class AcousticAnalyzer:
    CHOSEONG = [
        "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]
    JUNGSEONG = [
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    ]
    JONGSEONG = [
        "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ",
        "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]
    VOWELS = set(JUNGSEONG)
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

    def __init__(
        self,
        feature_extractor: AcousticFeatureExtractor | None = None,
        diagnostic_engine: DiagnosticEngine | None = None,
    ):
        self.feature_extractor = feature_extractor or create_default_feature_extractor()
        self.diagnostic_engine = diagnostic_engine or DiagnosticEngine()

    def analyze(
        self,
        audio_bytes: bytes,
        prediction: PredictResponse,
        forced_alignment: Optional[ForcedAlignmentResponse] = None,
        include_llm_note: bool = False,
        feedback_language: str = "ko",
    ) -> tuple[PronunciationAnalysisResponse, AcousticEvidencePacket]:
        audio = self._load_audio(audio_bytes)
        quality = self._analyze_audio_quality(audio)
        observed_by_expected, phoneme_edits = align_phonemes(
            prediction.canonical_phonemes,
            prediction.predicted_phonemes,
        )
        alignments, used_forced_alignment = self._resolve_alignments(
            prediction.canonical_phonemes,
            prediction.predicted_phonemes,
            audio.duration_ms,
            forced_alignment,
            observed_by_expected,
        )
        segment_features = self.feature_extractor.extract_segment_features(audio, alignments)
        prosody = self.feature_extractor.extract_prosody(audio)
        diagnostics = self.diagnostic_engine.build(
            prediction.canonical_phonemes,
            prediction.predicted_phonemes,
            phoneme_edits,
            prediction.syllable_candidate_scores,
            segment_features,
            prosody,
            quality,
        )
        if used_forced_alignment:
            notes = [
                "Word and syllable timings come from Qwen3 forced alignment.",
                "Phoneme timings are subdivided within the aligned syllable span and remain approximate.",
            ]
        else:
            notes = [
                "Alignment is heuristic and uniformly distributed because forced alignment is not available.",
                "Segment-level confidence should be treated as low until the aligner service is reachable.",
            ]
        if include_llm_note:
            notes.append("LLM feedback is generated from structured evidence, not from raw audio.")

        evidence = AcousticEvidencePacket(
            script=prediction.script,
            canonical_phonemes=prediction.canonical_phonemes,
            predicted_phonemes=prediction.predicted_phonemes,
            model_score=prediction.model_score,
            predicted_phoneme_scores=prediction.predicted_phoneme_scores,
            target_phoneme_scores=prediction.target_phoneme_scores,
            syllable_candidate_scores=prediction.syllable_candidate_scores,
            audio_quality=quality,
            phoneme_edits=phoneme_edits,
            alignments=alignments,
            segment_features=segment_features,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            policy=EvidencePolicy(language=feedback_language),
        )
        response = PronunciationAnalysisResponse(
            script=prediction.script,
            canonical_phonemes=prediction.canonical_phonemes,
            predicted_phonemes=prediction.predicted_phonemes,
            model_score=prediction.model_score,
            predicted_phoneme_scores=prediction.predicted_phoneme_scores,
            target_phoneme_scores=prediction.target_phoneme_scores,
            syllable_candidate_scores=prediction.syllable_candidate_scores,
            audio_quality=quality,
            phoneme_edits=phoneme_edits,
            alignments=alignments,
            segment_features=segment_features,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            notes=notes,
        )
        return response, evidence

    @classmethod
    def _decompose_hangul(cls, text: str) -> str:
        result: list[str] = []
        for char in text:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:
                syllable_index = code - 0xAC00
                choseong_index = syllable_index // 588
                jungseong_index = (syllable_index % 588) // 28
                jongseong_index = syllable_index % 28
                result.append(cls.CHOSEONG[choseong_index])
                result.append(cls.JUNGSEONG[jungseong_index])
                jong = cls.JONGSEONG[jongseong_index]
                if jong:
                    result.append(jong)
            else:
                result.append(char)
        return "".join(result)

    @classmethod
    def _compose_jamo(cls, phonemes: str) -> str:
        result: list[str] = []
        i = 0
        while i < len(phonemes):
            current = phonemes[i]
            if current not in cls.CHOSEONG or i + 1 >= len(phonemes) or phonemes[i + 1] not in cls.JUNGSEONG:
                result.append(current)
                i += 1
                continue
            choseong_index = cls.CHOSEONG.index(current)
            jungseong_index = cls.JUNGSEONG.index(phonemes[i + 1])
            jongseong_index = 0
            step = 2
            if i + 2 < len(phonemes) and phonemes[i + 2] in cls.JONGSEONG[1:]:
                next_is_vowel = i + 3 < len(phonemes) and phonemes[i + 3] in cls.JUNGSEONG
                if not next_is_vowel:
                    jongseong_index = cls.JONGSEONG.index(phonemes[i + 2])
                    step = 3
            syllable = chr(0xAC00 + (choseong_index * 588) + (jungseong_index * 28) + jongseong_index)
            result.append(syllable)
            i += step
        return "".join(result)

    def _resolve_alignments(
        self,
        canonical: str,
        predicted: str,
        duration_ms: int,
        forced_alignment: Optional[ForcedAlignmentResponse],
        observed_by_expected: list[str | None],
    ) -> tuple[list[AlignmentUnit], bool]:
        if forced_alignment and forced_alignment.items:
            return self._build_alignments_from_forced(
                canonical,
                predicted,
                forced_alignment,
                duration_ms,
                observed_by_expected,
            ), True
        return self._build_alignments_heuristic(canonical, predicted, duration_ms, observed_by_expected), False

    def _load_audio(self, audio_bytes: bytes) -> AudioBuffer:
        with sf.SoundFile(io.BytesIO(audio_bytes)) as audio_file:
            samples = audio_file.read(dtype="float32")
            sample_rate = int(audio_file.samplerate)
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)
        if sample_rate != 16000 and sample_rate > 0:
            gcd = math.gcd(sample_rate, 16000)
            samples = resample_poly(samples, 16000 // gcd, sample_rate // gcd).astype(np.float32)
            sample_rate = 16000
        return AudioBuffer(samples=samples.astype(np.float32), sample_rate=sample_rate)

    def _analyze_audio_quality(self, audio: AudioBuffer) -> AudioQualitySummary:
        if len(audio.samples) == 0:
            return AudioQualitySummary(overall_reliability="low")
        peak = float(np.max(np.abs(audio.samples)))
        clipping_detected = peak >= 0.999
        rms = float(np.sqrt(np.mean(np.square(audio.samples)) + 1e-9))
        tail = audio.samples[-min(len(audio.samples), audio.sample_rate // 3 or 1) :]
        noise_floor = float(np.sqrt(np.mean(np.square(tail)) + 1e-9))
        snr_db = 20.0 * math.log10((rms + 1e-9) / (noise_floor + 1e-9))
        zero_cross = np.mean(np.abs(np.diff(np.signbit(audio.samples))).astype(np.float32))
        voiced_ratio = max(0.0, min(1.0, 1.0 - float(zero_cross)))
        reliability = "high"
        if clipping_detected or snr_db < 12.0:
            reliability = "low"
        elif snr_db < 20.0:
            reliability = "medium"
        return AudioQualitySummary(
            snr_db=round(snr_db, 2),
            clipping_detected=clipping_detected,
            voiced_ratio=round(voiced_ratio, 3),
            noise_floor_db=round(20.0 * math.log10(noise_floor + 1e-9), 2),
            overall_reliability=reliability,
        )

    def _build_alignments_heuristic(
        self,
        canonical: str,
        predicted: str,
        duration_ms: int,
        observed_by_expected: list[str | None],
    ) -> list[AlignmentUnit]:
        if not canonical or duration_ms <= 0:
            return []
        weights = [2.0 if char in self.VOWELS else 1.0 for char in canonical]
        total_weight = sum(weights) or 1.0
        cursor_ms = 0
        alignments: list[AlignmentUnit] = []
        for index, (char, weight) in enumerate(zip(canonical, weights)):
            span_ms = max(20, int(round(duration_ms * weight / total_weight)))
            end_ms = duration_ms if index == len(canonical) - 1 else min(duration_ms, cursor_ms + span_ms)
            observed = observed_by_expected[index] if index < len(observed_by_expected) else None
            alignments.append(
                AlignmentUnit(
                    label=char,
                    unit_type="phoneme",
                    expected_label=char,
                    observed_label=observed,
                    start_ms=cursor_ms,
                    end_ms=max(cursor_ms + 1, end_ms),
                    confidence=0.25,
                    source="heuristic",
                )
            )
            cursor_ms = end_ms

        syllable_cursor = 0
        syllables = list(self._compose_jamo(canonical))
        for syllable in syllables:
            length = len(self._decompose_hangul(syllable))
            if syllable_cursor >= len(alignments):
                break
            group = alignments[syllable_cursor : syllable_cursor + length]
            syllable_cursor += len(group)
            alignments.append(
                AlignmentUnit(
                    label=syllable,
                    unit_type="syllable",
                    expected_label=syllable,
                    observed_label=self._compose_jamo("".join(unit.observed_label or "" for unit in group)),
                    start_ms=group[0].start_ms,
                    end_ms=group[-1].end_ms,
                    confidence=0.2,
                    source="heuristic",
                )
            )
        return alignments

    def _build_alignments_from_forced(
        self,
        canonical: str,
        predicted: str,
        forced_alignment: ForcedAlignmentResponse,
        duration_ms: int,
        observed_by_expected: list[str | None],
    ) -> list[AlignmentUnit]:
        alignments: list[AlignmentUnit] = []
        syllable_chars = [char for char in self._compose_jamo(canonical) if not char.isspace()]
        forced_items = [item for item in forced_alignment.items if item.text.strip()]

        canonical_groups = self._canonical_syllable_groups(canonical)
        phoneme_index = 0
        syllable_index = 0

        for item in forced_items:
            token_syllables = [char for char in item.text if not char.isspace()]
            if not token_syllables:
                continue
            remaining = len(canonical_groups) - syllable_index
            if remaining <= 0:
                break
            take = min(len(token_syllables), remaining)
            token_duration = max(1, item.end_ms - item.start_ms)
            local_cursor = item.start_ms
            for local_idx in range(take):
                group = canonical_groups[syllable_index]
                syllable_label = syllable_chars[syllable_index] if syllable_index < len(syllable_chars) else token_syllables[local_idx]
                syllable_end = item.end_ms if local_idx == take - 1 else min(
                    item.end_ms,
                    item.start_ms + int(round(token_duration * (local_idx + 1) / take)),
                )
                alignments.append(
                    AlignmentUnit(
                        label=syllable_label,
                        unit_type="syllable",
                        expected_label=syllable_label,
                        observed_label=token_syllables[local_idx],
                        start_ms=local_cursor,
                        end_ms=max(local_cursor + 1, syllable_end),
                        confidence=0.85,
                        source="forced",
                    )
                )
                group_weights = [2.0 if ch in self.VOWELS else 1.0 for ch in group]
                total_weight = sum(group_weights) or 1.0
                phoneme_cursor = local_cursor
                for offset, (char, weight) in enumerate(zip(group, group_weights)):
                    span_ms = max(10, int(round((syllable_end - local_cursor) * weight / total_weight)))
                    phoneme_end = syllable_end if offset == len(group) - 1 else min(syllable_end, phoneme_cursor + span_ms)
                    observed = observed_by_expected[phoneme_index] if phoneme_index < len(observed_by_expected) else None
                    alignments.append(
                        AlignmentUnit(
                            label=char,
                            unit_type="phoneme",
                            expected_label=char,
                            observed_label=observed,
                            start_ms=phoneme_cursor,
                            end_ms=max(phoneme_cursor + 1, phoneme_end),
                            confidence=0.6,
                            source="forced",
                        )
                    )
                    phoneme_cursor = phoneme_end
                    phoneme_index += 1
                local_cursor = syllable_end
                syllable_index += 1

        if not alignments:
            return self._build_alignments_heuristic(canonical, predicted, duration_ms)

        alignments.extend(self._append_forced_word_units(forced_items))
        phoneme_units = [unit for unit in alignments if unit.unit_type == "phoneme"]
        syllable_units = [unit for unit in alignments if unit.unit_type == "syllable"]
        word_units = [unit for unit in alignments if unit.unit_type == "word"]
        return phoneme_units + syllable_units + word_units

    @classmethod
    def _canonical_syllable_groups(cls, canonical: str) -> list[list[str]]:
        groups: list[list[str]] = []
        index = 0
        while index < len(canonical):
            start = index
            if canonical[index] not in cls.CHOSEONG or index + 1 >= len(canonical):
                groups.append([canonical[index]])
                index += 1
                continue
            if canonical[index + 1] not in cls.JUNGSEONG:
                groups.append([canonical[index]])
                index += 1
                continue
            index += 2
            if index < len(canonical) and canonical[index] in cls.JONGSEONG[1:]:
                next_is_vowel = index + 1 < len(canonical) and canonical[index + 1] in cls.JUNGSEONG
                if not next_is_vowel:
                    index += 1
            groups.append(list(canonical[start:index]))
        return groups

    @staticmethod
    def _append_forced_word_units(forced_items) -> list[AlignmentUnit]:
        words: list[AlignmentUnit] = []
        for item in forced_items:
            words.append(
                AlignmentUnit(
                    label=item.text,
                    unit_type="word",
                    expected_label=item.text,
                    observed_label=item.text,
                    start_ms=item.start_ms,
                    end_ms=item.end_ms,
                    confidence=0.8,
                    source="forced",
                )
            )
        return words
