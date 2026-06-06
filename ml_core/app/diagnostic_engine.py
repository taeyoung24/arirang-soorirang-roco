from __future__ import annotations

from app.acoustic_schemas import AudioQualitySummary, DiagnosticCandidate, PhonemeEdit, ProsodySummary
from app.schemas import PredictedPhonemeScore, SyllableCandidateScore, TargetPhonemeScore


class DiagnosticEngine:
    VOWELS = {
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    }
    ASPIRATED_TO_LENIS = {"ㅋ": "ㄱ", "ㅌ": "ㄷ", "ㅍ": "ㅂ", "ㅊ": "ㅈ"}
    SLOW_SPEECH_DURATION_RATIO = 2.3
    VERY_SLOW_SPEECH_DURATION_RATIO = 2.9
    STRETCHED_SYLLABLE_DURATION_RATIO = 2.0
    STRETCHED_SYLLABLE_DELTA_MS = 150
    STRETCHED_WORD_DURATION_RATIO = 2.0
    STRETCHED_WORD_DELTA_MS = 450
    VERY_STRETCHED_DURATION_RATIO = 3.0
    VERY_STRETCHED_DELTA_MS = 300
    MEDIUM_INTERIOR_PAUSE_MS = 500
    HIGH_INTERIOR_PAUSE_MS = 1200
    ERROR_TARGET_POSTERIOR = 0.35
    ERROR_GOP_MARGIN = -0.5
    PLAUSIBLE_TARGET_POSTERIOR = 0.45
    PLAUSIBLE_GOP_MARGIN = -0.25
    DELETION_LOGPROB_MARGIN = 0.7
    INSERTION_MIN_CONFIDENCE = 0.75
    INSERTION_MIN_FRAME_COUNT = 2

    def build(
        self,
        canonical: str,
        predicted: str,
        phoneme_edits: list[PhonemeEdit],
        syllable_candidate_scores: list[SyllableCandidateScore],
        target_phoneme_scores: list[TargetPhonemeScore],
        predicted_phoneme_scores: list[PredictedPhonemeScore],
        prosody: ProsodySummary,
        quality: AudioQualitySummary,
    ) -> list[DiagnosticCandidate]:
        diagnostics = []
        diagnostics.extend(
            self._phoneme_mismatch_diagnostics(
                phoneme_edits,
                syllable_candidate_scores,
                target_phoneme_scores,
                predicted_phoneme_scores,
            )
        )
        diagnostics.extend(self._prosody_diagnostics(prosody, quality))
        diagnostics.extend(self._quality_diagnostics(quality))
        return sorted(diagnostics, key=lambda item: (self._severity_rank(item.severity), item.confidence), reverse=True)

    def _phoneme_mismatch_diagnostics(
        self,
        phoneme_edits: list[PhonemeEdit],
        syllable_candidate_scores: list[SyllableCandidateScore],
        target_phoneme_scores: list[TargetPhonemeScore],
        predicted_phoneme_scores: list[PredictedPhonemeScore],
    ) -> list[DiagnosticCandidate]:
        diagnostics: list[DiagnosticCandidate] = []
        target_scores_by_index = {score.canonical_index: score for score in target_phoneme_scores}
        predicted_scores_by_index = {score.predicted_index: score for score in predicted_phoneme_scores}
        for edit in phoneme_edits:
            expected = edit.expected or ""
            observed = edit.actual or ""
            syllable_score = self._syllable_score_for_edit(edit, syllable_candidate_scores)
            target_score = target_scores_by_index.get(edit.expected_index) if edit.expected_index is not None else None
            if edit.edit_type == "deletion":
                if not self._has_strong_deletion_evidence(syllable_score):
                    continue
            elif edit.edit_type == "substitution":
                if not self._has_strong_substitution_evidence(target_score):
                    continue
            elif edit.edit_type == "insertion":
                predicted_score = predicted_scores_by_index.get(edit.actual_index) if edit.actual_index is not None else None
                if not self._has_strong_insertion_evidence(predicted_score):
                    continue
            if expected in self.ASPIRATED_TO_LENIS and observed == self.ASPIRATED_TO_LENIS[expected]:
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="aspiration_insufficient",
                        category="segmental",
                        target_unit=expected,
                        severity="high",
                        confidence=0.82,
                        evidence_keys=["predicted_phoneme_mismatch"],
                        rationale=self._rationale(edit, f"Expected aspirated {expected}, but MDD decoded it closer to lenis {observed}."),
                    )
                )
            elif edit.edit_type == "deletion":
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="segmental_deletion",
                        category="segmental",
                        target_unit=expected,
                        severity="medium",
                        confidence=self._deletion_confidence(syllable_score),
                        evidence_keys=[
                            "phoneme_edit_alignment",
                            "predicted_phoneme_mismatch",
                            "syllable_ctc_likelihood_comparison",
                        ],
                        rationale=self._rationale(
                            edit,
                            self._deletion_rationale(expected, syllable_score),
                        ),
                    )
                )
            elif edit.edit_type == "insertion":
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="segmental_insertion",
                        category="segmental",
                        target_unit=observed,
                        severity="medium",
                        confidence=0.62,
                        evidence_keys=["phoneme_edit_alignment", "predicted_phoneme_mismatch"],
                        rationale=self._rationale(edit, f"MDD alignment found an extra {observed} sound."),
                    )
                )
            elif expected in self.VOWELS and observed in self.VOWELS:
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="vowel_quality_shift",
                        category="segmental",
                        target_unit=expected,
                        severity="medium",
                        confidence=0.7,
                        evidence_keys=["phoneme_edit_alignment", "predicted_phoneme_mismatch"],
                        rationale=self._rationale(edit, f"Expected vowel {expected}, but MDD decoded the vowel as {observed}."),
                    )
                )
            else:
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="segmental_substitution",
                        category="segmental",
                        target_unit=expected,
                        severity="medium",
                        confidence=0.65,
                        evidence_keys=["phoneme_edit_alignment", "predicted_phoneme_mismatch"],
                        rationale=self._rationale(edit, f"Expected {expected}, but MDD decoded {observed}."),
                    )
                )
        return diagnostics

    @staticmethod
    def _quality_diagnostics(quality: AudioQualitySummary) -> list[DiagnosticCandidate]:
        if quality.overall_reliability != "low":
            return []
        return [
            DiagnosticCandidate(
                diagnosis_code="audio_quality_limited",
                category="quality",
                target_unit=None,
                severity="medium",
                confidence=0.95,
                evidence_keys=["snr_db", "clipping_detected"],
                rationale="Audio quality limits the confidence of phonetic interpretation.",
            )
        ]

    def _prosody_diagnostics(
        self,
        prosody: ProsodySummary,
        quality: AudioQualitySummary,
    ) -> list[DiagnosticCandidate]:
        if prosody.timing_source != "forced_alignment":
            return []
        if quality.overall_reliability == "low" and prosody.rate_reliability != "high":
            return []

        diagnostics: list[DiagnosticCandidate] = []
        long_pauses = [
            item
            for item in prosody.reference_pause_comparisons
            if item.pause_level in {"medium", "high"}
        ][:3]
        for item in long_pauses:
            severity = "high" if item.pause_level == "high" else "medium"
            confidence = 0.82 if severity == "high" else 0.76
            diagnostics.append(
                DiagnosticCandidate(
                    diagnosis_code="long_interior_pause",
                    category="prosodic",
                    target_unit=None,
                    severity=severity,
                    confidence=confidence,
                    evidence_keys=[
                        "tts_reference_pause_delta",
                        "reference_pause_comparisons",
                    ],
                    rationale=(
                        "Learner pause is longer than the cached TTS reference pause: "
                        f"after={item.previous_label}, before={item.next_label}, "
                        f"user_pause_ms={item.user_duration_ms}, "
                        f"reference_pause_ms={item.reference_duration_ms}, "
                        f"delta_ms={item.duration_delta_ms}, "
                        f"pause_level={item.pause_level}."
                    ),
                )
            )

        if not long_pauses:
            raw_pauses = [
                item
                for item in prosody.pause_intervals
                if item.duration_ms >= self.MEDIUM_INTERIOR_PAUSE_MS
            ][:3]
            for item in raw_pauses:
                severity = "high" if item.duration_ms >= self.HIGH_INTERIOR_PAUSE_MS else "medium"
                diagnostics.append(
                    DiagnosticCandidate(
                        diagnosis_code="long_interior_pause",
                        category="prosodic",
                        target_unit=None,
                        severity=severity,
                        confidence=0.76 if severity == "high" else 0.7,
                        evidence_keys=[
                            "qwen_forced_alignment_word_gaps",
                            "pause_intervals",
                        ],
                        rationale=(
                            "Qwen forced alignment found an interior word gap: "
                            f"start_ms={item.start_ms}, "
                            f"end_ms={item.end_ms}, "
                            f"duration_ms={item.duration_ms}, "
                            f"threshold_ms={self.MEDIUM_INTERIOR_PAUSE_MS}."
                        ),
                    )
                )

        stretched_units = self._deduplicate_stretched_units([
            item
            for item in prosody.reference_duration_comparisons
            if self._is_stretched_unit(item)
        ])[:3]
        for item in stretched_units:
            severity = self._stretched_severity(item)
            diagnostics.append(
                DiagnosticCandidate(
                    diagnosis_code="stretched_aligned_unit",
                    category="prosodic",
                    target_unit=item.label,
                    severity=severity,
                    confidence=0.78 if severity == "high" else 0.7,
                    evidence_keys=[
                        "tts_reference_duration_ratio",
                        "reference_duration_comparisons",
                    ],
                    rationale=(
                        "Learner aligned syllable/word is longer than the cached TTS reference: "
                        f"unit={item.label}, "
                        f"unit_type={item.unit_type}, "
                        f"user_duration_ms={item.user_duration_ms}, "
                        f"reference_duration_ms={item.reference_duration_ms}, "
                        f"duration_ratio={item.duration_ratio}, "
                        f"ratio_threshold={self._stretched_ratio_threshold(item.unit_type)}, "
                        f"delta_threshold_ms={self._stretched_delta_threshold(item.unit_type)}."
                    ),
                )
            )

        speech_ratio = prosody.speech_duration_ratio
        if speech_ratio is not None and speech_ratio >= self.SLOW_SPEECH_DURATION_RATIO and not long_pauses and not stretched_units:
            severity = "high" if speech_ratio >= self.VERY_SLOW_SPEECH_DURATION_RATIO else "medium"
            confidence = 0.78 if severity == "high" else 0.7
            diagnostics.append(
                DiagnosticCandidate(
                    diagnosis_code="speech_rate_too_slow",
                    category="prosodic",
                    target_unit=None,
                    severity=severity,
                    confidence=confidence,
                    evidence_keys=[
                        "tts_reference_speech_duration_ratio",
                        "speech_duration_ms",
                        "reference_speech_duration_ms",
                    ],
                    rationale=(
                        "Learner speech is slower than the cached TTS reference: "
                        f"speech_duration_ratio={speech_ratio}, "
                        f"threshold={self.SLOW_SPEECH_DURATION_RATIO}, "
                        f"speech_duration_ms={prosody.speech_duration_ms}, "
                        f"reference_speech_duration_ms={prosody.reference_speech_duration_ms}."
                    ),
                )
            )

        if len(long_pauses) >= 2:
            severity = "high" if any(item.pause_level == "high" for item in long_pauses) else "medium"
            diagnostics.append(
                DiagnosticCandidate(
                    diagnosis_code="excessive_interior_pause",
                    category="prosodic",
                    target_unit=None,
                    severity=severity,
                    confidence=0.74 if severity == "high" else 0.72,
                    evidence_keys=[
                        "tts_reference_pause_delta",
                        "reference_pause_comparisons",
                    ],
                    rationale=(
                        "Learner has repeated pauses longer than the cached TTS reference: "
                        f"long_reference_based_pause_count={len(long_pauses)}."
                    ),
                )
            )

        return diagnostics

    def _is_stretched_unit(self, item) -> bool:
        return (
            item.duration_ratio >= self._stretched_ratio_threshold(item.unit_type)
            and item.duration_delta_ms >= self._stretched_delta_threshold(item.unit_type)
        )

    def _stretched_ratio_threshold(self, unit_type: str) -> float:
        if unit_type == "syllable":
            return self.STRETCHED_SYLLABLE_DURATION_RATIO
        return self.STRETCHED_WORD_DURATION_RATIO

    def _stretched_delta_threshold(self, unit_type: str) -> int:
        if unit_type == "syllable":
            return self.STRETCHED_SYLLABLE_DELTA_MS
        return self.STRETCHED_WORD_DELTA_MS

    def _stretched_severity(self, item) -> str:
        if item.duration_ratio >= self.VERY_STRETCHED_DURATION_RATIO and item.duration_delta_ms >= self.VERY_STRETCHED_DELTA_MS:
            return "high"
        return "medium"

    def _deduplicate_stretched_units(self, items: list) -> list:
        syllables = [item for item in items if item.unit_type == "syllable"]
        result = []
        for item in items:
            if item.unit_type == "word" and any(
                syllable.start_ms >= item.start_ms and syllable.end_ms <= item.end_ms for syllable in syllables
            ):
                continue
            result.append(item)
        return result

    @staticmethod
    def _severity_rank(severity: str) -> int:
        return {"low": 1, "medium": 2, "high": 3}.get(severity, 0)

    @staticmethod
    def _syllable_score_for_edit(
        edit: PhonemeEdit,
        syllable_candidate_scores: list[SyllableCandidateScore],
    ) -> SyllableCandidateScore | None:
        if edit.expected_index is None:
            return None
        for score in syllable_candidate_scores:
            if score.start_phoneme_index <= edit.expected_index < score.end_phoneme_index:
                return score
        return None

    @staticmethod
    def _deletion_confidence(score: SyllableCandidateScore | None) -> float:
        if score is None or score.confidence is None:
            return 0.58
        return round(max(0.5, min(0.95, score.confidence)), 4)

    @staticmethod
    def _deletion_rationale(expected: str, score: SyllableCandidateScore | None) -> str:
        base = f"Expected {expected}, but MDD edit alignment found it missing rather than shifted."
        if score is None or score.logprob_margin is None:
            return base
        return (
            f"{base} Syllable-level CTC comparison favored the deletion alternative "
            f"{score.alternative_sequence} over target {score.target_sequence} "
            f"with margin={score.logprob_margin}."
        )

    @staticmethod
    def _rationale(edit: PhonemeEdit, base: str) -> str:
        details = []
        if edit.expected_index is not None:
            details.append(f"expected_index={edit.expected_index}")
        if edit.syllable:
            details.append(f"syllable={edit.syllable}")
        if edit.context:
            details.append(f"context={edit.context}")
        if not details:
            return base
        return f"{base} ({', '.join(details)})"

    def _has_strong_substitution_evidence(self, score: TargetPhonemeScore | None) -> bool:
        if score is None:
            return True
        target_posterior = score.target_posterior
        gop = score.gop_like_score
        if target_posterior is None or gop is None:
            return True
        if target_posterior >= self.PLAUSIBLE_TARGET_POSTERIOR or gop > self.PLAUSIBLE_GOP_MARGIN:
            return False
        return target_posterior <= self.ERROR_TARGET_POSTERIOR and gop <= self.ERROR_GOP_MARGIN

    def _has_strong_deletion_evidence(self, score: SyllableCandidateScore | None) -> bool:
        if score is None or score.logprob_margin is None:
            return False
        return score.logprob_margin >= self.DELETION_LOGPROB_MARGIN

    def _has_strong_insertion_evidence(self, score: PredictedPhonemeScore | None) -> bool:
        if score is None:
            return True
        return score.confidence >= self.INSERTION_MIN_CONFIDENCE and score.frame_count >= self.INSERTION_MIN_FRAME_COUNT
