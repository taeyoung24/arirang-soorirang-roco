from __future__ import annotations

from app.acoustic_schemas import AudioQualitySummary, DiagnosticCandidate, PhonemeEdit, ProsodySummary, SegmentFeatureBundle
from app.schemas import SyllableCandidateScore


class DiagnosticEngine:
    VOWELS = {
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    }
    ASPIRATED_TO_LENIS = {"ㅋ": "ㄱ", "ㅌ": "ㄷ", "ㅍ": "ㅂ", "ㅊ": "ㅈ"}

    def build(
        self,
        canonical: str,
        predicted: str,
        phoneme_edits: list[PhonemeEdit],
        syllable_candidate_scores: list[SyllableCandidateScore],
        segment_features: list[SegmentFeatureBundle],
        prosody: ProsodySummary,
        quality: AudioQualitySummary,
    ) -> list[DiagnosticCandidate]:
        diagnostics = []
        diagnostics.extend(self._phoneme_mismatch_diagnostics(phoneme_edits, syllable_candidate_scores))
        diagnostics.extend(self._quality_diagnostics(quality))
        return sorted(diagnostics, key=lambda item: (self._severity_rank(item.severity), item.confidence), reverse=True)

    def _phoneme_mismatch_diagnostics(
        self,
        phoneme_edits: list[PhonemeEdit],
        syllable_candidate_scores: list[SyllableCandidateScore],
    ) -> list[DiagnosticCandidate]:
        diagnostics: list[DiagnosticCandidate] = []
        for edit in phoneme_edits:
            expected = edit.expected or ""
            observed = edit.actual or ""
            syllable_score = self._syllable_score_for_edit(edit, syllable_candidate_scores)
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
            return 0.72
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
