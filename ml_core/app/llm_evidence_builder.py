from __future__ import annotations

from app.acoustic_schemas import (
    AcousticEvidencePacket,
    AlignmentUnit,
    DiagnosticCandidate,
    PhonemeEdit,
    SegmentFeatureBundle,
)


class LLMEvidenceBuilder:
    RELEVANT_FEATURES = {
        "duration_ms",
        "pitch_hz",
        "spectral_centroid_hz",
        "zero_cross_rate",
        "high_frequency_ratio",
        "burst_peak",
        "frication_ms",
    }

    def build(self, evidence: AcousticEvidencePacket, max_diagnostics: int = 3) -> AcousticEvidencePacket:
        diagnostics = self._top_diagnostics(evidence.diagnostic_candidates, max_diagnostics)
        target_units = {item.target_unit for item in diagnostics if item.target_unit}
        phoneme_edits = self._relevant_edits(evidence.phoneme_edits, target_units, max_diagnostics)
        return AcousticEvidencePacket(
            script=evidence.script,
            canonical_phonemes="",
            predicted_phonemes=None,
            model_score=None,
            predicted_phoneme_scores=[
                score
                for score in evidence.predicted_phoneme_scores
                if score.phoneme in target_units
            ][:max_diagnostics],
            target_phoneme_scores=[
                score
                for score in evidence.target_phoneme_scores
                if score.phoneme in target_units
            ][:max_diagnostics],
            syllable_candidate_scores=[
                score
                for score in evidence.syllable_candidate_scores
                if any(unit in target_units for unit in score.target_sequence)
            ][:max_diagnostics],
            audio_quality=evidence.audio_quality,
            phoneme_edits=phoneme_edits,
            alignments=self._relevant_alignments(evidence.alignments, target_units),
            segment_features=self._relevant_features(evidence.segment_features, target_units),
            prosody=None,
            diagnostic_candidates=diagnostics,
            policy=evidence.policy,
        )

    @staticmethod
    def _top_diagnostics(
        diagnostics: list[DiagnosticCandidate],
        max_diagnostics: int,
    ) -> list[DiagnosticCandidate]:
        severity_rank = {"low": 1, "medium": 2, "high": 3}
        evidence_rank = {
            "phoneme_edit_alignment": 2,
            "predicted_phoneme_mismatch": 2,
            "syllable_ctc_likelihood_comparison": 1,
        }
        ranked = sorted(
            diagnostics,
            key=lambda item: (
                max((evidence_rank.get(key, 0) for key in item.evidence_keys), default=0),
                severity_rank.get(item.severity, 0),
                item.confidence,
            ),
            reverse=True,
        )
        return ranked[:max_diagnostics]

    @staticmethod
    def _relevant_edits(
        edits: list[PhonemeEdit],
        target_units: set[str],
        max_edits: int,
    ) -> list[PhonemeEdit]:
        if not target_units:
            return edits[:max_edits]
        result = [
            edit
            for edit in edits
            if edit.expected in target_units or edit.actual in target_units
        ]
        return (result or edits)[:max_edits]

    @staticmethod
    def _relevant_alignments(
        alignments: list[AlignmentUnit],
        target_units: set[str],
    ) -> list[AlignmentUnit]:
        if not target_units:
            return [unit for unit in alignments if unit.unit_type == "word"][:6]
        result = [
            unit
            for unit in alignments
            if unit.unit_type in {"phoneme", "syllable"} and (unit.label in target_units or unit.expected_label in target_units)
        ]
        if result:
            return result[:12]
        return [unit for unit in alignments if unit.unit_type == "word"][:6]

    def _relevant_features(
        self,
        segment_features: list[SegmentFeatureBundle],
        target_units: set[str],
    ) -> list[SegmentFeatureBundle]:
        if not target_units:
            return []
        bundles = []
        for bundle in segment_features:
            if bundle.label not in target_units:
                continue
            filtered = [
                feature
                for feature in bundle.features
                if feature.name in self.RELEVANT_FEATURES and feature.value is not None
            ]
            if filtered:
                bundles.append(
                    SegmentFeatureBundle(
                        label=bundle.label,
                        unit_type=bundle.unit_type,
                        interval=bundle.interval,
                        features=filtered,
                    )
                )
        return bundles[:8]
