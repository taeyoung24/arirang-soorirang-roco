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
    DiagnosticCandidate,
    EvidencePolicy,
    ForcedAlignmentResponse,
    PronunciationScore,
    PronunciationAnalysisResponse,
    ProsodySummary,
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
        reference_alignment: Optional[ForcedAlignmentResponse] = None,
        reference_prediction: Optional[PredictResponse] = None,
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
            prediction.script,
            prediction.canonical_phonemes,
            prediction.predicted_phonemes,
            audio.duration_ms,
            forced_alignment,
            observed_by_expected,
        )
        reference_alignments = self._resolve_reference_alignments(
            prediction.script,
            prediction.canonical_phonemes,
            reference_alignment,
        )
        prosody = self.feature_extractor.extract_prosody(audio, alignments, reference_alignments)
        diagnostics = self.diagnostic_engine.build(
            prediction.canonical_phonemes,
            prediction.predicted_phonemes,
            phoneme_edits,
            prediction.syllable_candidate_scores,
            prediction.target_phoneme_scores,
            prediction.predicted_phoneme_scores,
            prosody,
            quality,
        )
        reference_diagnostics = self._reference_segmental_diagnostics(reference_prediction)
        diagnostics, uncertain_diagnostics = self._split_reference_artifacts(diagnostics, reference_diagnostics)
        pronunciation_score = self._score_pronunciation(
            canonical=prediction.canonical_phonemes,
            phoneme_edits=phoneme_edits,
            target_scores=prediction.target_phoneme_scores,
            prosody=prosody,
            quality=quality,
            diagnostic_count=len(diagnostics),
        )
        if not diagnostics:
            pronunciation_score = self._perfect_score_without_confirmed_diagnostics(pronunciation_score)
        if used_forced_alignment:
            notes = [
                "Word and syllable timings come from Qwen3 forced alignment.",
            ]
        else:
            notes = [
                "Alignment is heuristic and uniformly distributed because forced alignment is not available.",
            ]
        if include_llm_note:
            notes.append("LLM feedback is generated from structured evidence, not from raw audio.")
        if reference_alignment and reference_alignments:
            notes.append("Prosodic timing diagnostics compare learner speech against cached TTS reference alignment.")
        if uncertain_diagnostics:
            notes.append("Some segmental diagnostics were downgraded because the cached TTS reference produced the same model artifact.")
        elif used_forced_alignment:
            notes.append("No TTS reference alignment was supplied, so reference-based prosody diagnostics are unavailable.")

        evidence = AcousticEvidencePacket(
            script=prediction.script,
            canonical_text=prediction.canonical_text,
            predicted_text=prediction.predicted_text,
            canonical_phonemes=prediction.canonical_phonemes,
            predicted_phonemes=prediction.predicted_phonemes,
            model_score=prediction.model_score,
            predicted_phoneme_scores=prediction.predicted_phoneme_scores,
            target_phoneme_scores=prediction.target_phoneme_scores,
            syllable_candidate_scores=prediction.syllable_candidate_scores,
            audio_quality=quality,
            phoneme_edits=phoneme_edits,
            alignments=alignments,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            uncertain_diagnostic_candidates=uncertain_diagnostics,
            policy=EvidencePolicy(language=feedback_language),
        )
        display_status = "needs_attention" if diagnostics else "normal"
        has_segmental_diagnostic = any(item.category == "segmental" for item in diagnostics)
        display_predicted_text = prediction.predicted_text if has_segmental_diagnostic else prediction.script
        display_predicted_phonemes = prediction.predicted_phonemes if has_segmental_diagnostic else prediction.canonical_phonemes
        response = PronunciationAnalysisResponse(
            script=prediction.script,
            predicted_text=prediction.predicted_text,
            display_pronunciation_status=display_status,
            display_predicted_text=display_predicted_text,
            display_predicted_phonemes=display_predicted_phonemes,
            raw_predicted_text=prediction.predicted_text,
            canonical_phonemes=prediction.canonical_phonemes,
            predicted_phonemes=prediction.predicted_phonemes,
            pronunciation_score=pronunciation_score,
            model_score=prediction.model_score,
            predicted_phoneme_scores=prediction.predicted_phoneme_scores,
            target_phoneme_scores=prediction.target_phoneme_scores,
            syllable_candidate_scores=prediction.syllable_candidate_scores,
            audio_quality=quality,
            phoneme_edits=phoneme_edits,
            alignments=alignments,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            uncertain_diagnostic_candidates=uncertain_diagnostics,
            notes=notes,
        )
        return response, evidence

    def _reference_segmental_diagnostics(self, reference_prediction: PredictResponse | None) -> list[DiagnosticCandidate]:
        if reference_prediction is None:
            return []
        _observed_by_expected, reference_edits = align_phonemes(
            reference_prediction.canonical_phonemes,
            reference_prediction.predicted_phonemes,
        )
        diagnostics = self.diagnostic_engine.build(
            reference_prediction.canonical_phonemes,
            reference_prediction.predicted_phonemes,
            reference_edits,
            reference_prediction.syllable_candidate_scores,
            reference_prediction.target_phoneme_scores,
            reference_prediction.predicted_phoneme_scores,
            ProsodySummary(timing_source="none"),
            AudioQualitySummary(overall_reliability="high"),
        )
        return [item for item in diagnostics if item.category == "segmental"]

    @staticmethod
    def _split_reference_artifacts(
        diagnostics: list[DiagnosticCandidate],
        reference_diagnostics: list[DiagnosticCandidate],
    ) -> tuple[list[DiagnosticCandidate], list[DiagnosticCandidate]]:
        if not reference_diagnostics:
            return diagnostics, []
        reference_keys = {AcousticAnalyzer._diagnostic_calibration_key(item) for item in reference_diagnostics}
        confirmed = []
        uncertain = []
        for item in diagnostics:
            if item.category == "segmental" and AcousticAnalyzer._diagnostic_calibration_key(item) in reference_keys:
                uncertain.append(item)
            else:
                confirmed.append(item)
        return confirmed, uncertain

    @staticmethod
    def _diagnostic_calibration_key(item: DiagnosticCandidate) -> tuple[str, str | None]:
        return item.diagnosis_code, item.target_unit


    @staticmethod
    def _perfect_score_without_confirmed_diagnostics(score: PronunciationScore) -> PronunciationScore:
        return score.model_copy(
            update={
                "overall": 100.0,
                "segmental": 100.0,
                "prosody": 100.0,
                "note": score.note + " Display scoring is lenient: no confirmed diagnostic candidates yields a perfect score.",
            }
        )

    @staticmethod
    def _score_pronunciation(
        canonical: str,
        phoneme_edits,
        target_scores,
        prosody: ProsodySummary,
        quality: AudioQualitySummary,
        diagnostic_count: int,
    ) -> PronunciationScore:
        scored_targets = [score for score in target_scores if score.edit_type != "insertion"]
        if scored_targets:
            segmental = 100.0 * sum(AcousticAnalyzer._target_score_value(score) for score in scored_targets) / len(scored_targets)
        elif canonical:
            segmental = 100.0 * max(0, len(canonical) - len(phoneme_edits)) / len(canonical)
        else:
            segmental = 0.0

        prosody_score = AcousticAnalyzer._prosody_score(prosody)
        audio_quality_score = AcousticAnalyzer._audio_quality_score(quality)
        overall = 0.85 * segmental + 0.15 * prosody_score
        if diagnostic_count:
            overall -= min(12.0, diagnostic_count * 2.0)

        note = (
            "Heuristic 0-100 score from target phoneme confidence, timing/prosody evidence, "
            "and diagnostic penalties. Audio quality is reported separately and does not affect the score. "
            "It is not externally calibrated."
        )
        return PronunciationScore(
            overall=round(max(0.0, min(100.0, overall)), 1),
            segmental=round(max(0.0, min(100.0, segmental)), 1),
            prosody=round(max(0.0, min(100.0, prosody_score)), 1),
            audio_quality=round(audio_quality_score, 1),
            note=note,
        )

    @staticmethod
    def _target_score_value(score) -> float:
        if score.edit_type == "match":
            if score.confidence is None:
                return 1.0
            return max(0.85, score.confidence)
        if score.edit_type == "substitution":
            if score.target_posterior is not None:
                if score.gop_like_score is not None and score.gop_like_score > -0.25:
                    return max(0.65, score.target_posterior)
                if score.target_posterior >= 0.45:
                    return max(0.65, score.target_posterior)
                return max(0.0, min(0.6, score.target_posterior))
            return 0.35 * (score.confidence if score.confidence is not None else 0.5)
        if score.edit_type == "deletion":
            return 0.0
        return 0.0

    @staticmethod
    def _prosody_score(prosody: ProsodySummary) -> float:
        score = 100.0
        if prosody.speech_duration_ratio is not None:
            ratio = prosody.speech_duration_ratio
            if ratio > 1.15:
                score -= min(35.0, (ratio - 1.15) * 22.0)
        score -= min(25.0, prosody.interior_pause_total_ms / 160.0)
        score -= min(15.0, len(prosody.stretched_intervals) * 4.0)
        if prosody.rate_reliability == "low":
            score = max(score, 65.0)
        return score

    @staticmethod
    def _audio_quality_score(quality: AudioQualitySummary) -> float:
        base = {"high": 100.0, "medium": 92.0, "low": 75.0}[quality.overall_reliability]
        if quality.clipping_detected:
            base -= 8.0
        if quality.snr_db is not None and quality.snr_db < 6.0:
            base -= min(15.0, (6.0 - quality.snr_db) * 2.0)
        return max(0.0, min(100.0, base))

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
        script: str,
        canonical: str,
        predicted: str,
        duration_ms: int,
        forced_alignment: Optional[ForcedAlignmentResponse],
        observed_by_expected: list[str | None],
    ) -> tuple[list[AlignmentUnit], bool]:
        if forced_alignment and forced_alignment.items:
            return self._build_alignments_from_forced(
                script,
                canonical,
                predicted,
                forced_alignment,
                duration_ms,
                observed_by_expected,
            ), True
        return self._build_alignments_heuristic(canonical, predicted, duration_ms, observed_by_expected), False

    def _resolve_reference_alignments(
        self,
        script: str,
        canonical: str,
        reference_alignment: Optional[ForcedAlignmentResponse],
    ) -> list[AlignmentUnit]:
        if not reference_alignment or not reference_alignment.items:
            return []
        observed_by_expected, _ = align_phonemes(canonical, canonical)
        duration_ms = max((item.end_ms for item in reference_alignment.items), default=0)
        return self._build_alignments_from_forced(
            script,
            canonical,
            canonical,
            reference_alignment,
            duration_ms,
            observed_by_expected,
        )

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
        clipped_ratio = float(np.mean(np.abs(audio.samples) >= 0.999))
        clipping_detected = peak >= 0.999 and clipped_ratio >= 0.01
        rms = float(np.sqrt(np.mean(np.square(audio.samples)) + 1e-9))
        tail = audio.samples[-min(len(audio.samples), audio.sample_rate // 3 or 1) :]
        noise_floor = float(np.sqrt(np.mean(np.square(tail)) + 1e-9))
        snr_db = 20.0 * math.log10((rms + 1e-9) / (noise_floor + 1e-9))
        zero_cross = np.mean(np.abs(np.diff(np.signbit(audio.samples))).astype(np.float32))
        voiced_ratio = max(0.0, min(1.0, 1.0 - float(zero_cross)))
        reliability = "high"
        if snr_db < 6.0:
            reliability = "low"
        elif clipping_detected or snr_db < 12.0:
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
        script: str,
        canonical: str,
        predicted: str,
        forced_alignment: ForcedAlignmentResponse,
        duration_ms: int,
        observed_by_expected: list[str | None],
    ) -> list[AlignmentUnit]:
        alignments: list[AlignmentUnit] = []
        forced_items = [item for item in forced_alignment.items if item.text.strip()]

        syllable_alignments = self._forced_syllable_units(script, forced_items)
        if syllable_alignments:
            alignments.extend(syllable_alignments)
            alignments.extend(self._forced_word_units_from_syllables(script, syllable_alignments))
        else:
            alignments.extend(self._forced_word_units(forced_items))

        if not alignments:
            return self._build_alignments_heuristic(canonical, predicted, duration_ms, observed_by_expected)

        syllable_units = [unit for unit in alignments if unit.unit_type == "syllable"]
        word_units = [unit for unit in alignments if unit.unit_type == "word"]
        return syllable_units + word_units

    @classmethod
    def _forced_syllable_units(cls, script: str, forced_items) -> list[AlignmentUnit]:
        script_syllables = [char for char in script if cls._is_hangul_syllable(char)]
        if not script_syllables:
            return []
        syllable_items = [item for item in forced_items if cls._is_single_hangul_syllable(item.text.strip())]
        if not syllable_items:
            return []

        units: list[AlignmentUnit] = []
        for expected, item in zip(script_syllables, syllable_items):
            observed = item.text.strip()
            units.append(
                AlignmentUnit(
                    label=expected,
                    unit_type="syllable",
                    expected_label=expected,
                    observed_label=observed,
                    start_ms=item.start_ms,
                    end_ms=max(item.start_ms + 1, item.end_ms),
                    confidence=0.85,
                    source="forced",
                )
            )
        return units

    @staticmethod
    def _forced_word_units(forced_items) -> list[AlignmentUnit]:
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

    @classmethod
    def _forced_word_units_from_syllables(cls, canonical: str, syllable_units: list[AlignmentUnit]) -> list[AlignmentUnit]:
        words: list[AlignmentUnit] = []
        cursor = 0
        for word in cls._script_words(canonical):
            syllable_count = sum(1 for char in word if cls._is_hangul_syllable(char))
            if syllable_count <= 0:
                continue
            group = syllable_units[cursor : cursor + syllable_count]
            cursor += len(group)
            if len(group) != syllable_count:
                break
            words.append(
                AlignmentUnit(
                    label=word,
                    unit_type="word",
                    expected_label=word,
                    observed_label="".join(unit.observed_label or "" for unit in group),
                    start_ms=group[0].start_ms,
                    end_ms=group[-1].end_ms,
                    confidence=0.8,
                    source="forced",
                )
            )
        return words

    @staticmethod
    def _is_hangul_syllable(char: str) -> bool:
        return len(char) == 1 and 0xAC00 <= ord(char) <= 0xD7A3

    @classmethod
    def _is_single_hangul_syllable(cls, text: str) -> bool:
        return len(text) == 1 and cls._is_hangul_syllable(text)

    @staticmethod
    def _script_words(canonical: str) -> list[str]:
        return [word for word in canonical.split() if word]
