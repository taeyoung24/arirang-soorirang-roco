from app.acoustic_schemas import AudioQualitySummary, PhonemeEdit, ProsodySummary
from app.diagnostic_engine import DiagnosticEngine
from app.schemas import PredictedPhonemeScore, SyllableCandidateScore, TargetPhonemeScore


def _prosody() -> ProsodySummary:
    return ProsodySummary(timing_source="forced_alignment", rate_reliability="high")


def _quality() -> AudioQualitySummary:
    return AudioQualitySummary(overall_reliability="high")


def test_substitution_is_suppressed_when_target_phoneme_is_plausible():
    diagnostics = DiagnosticEngine().build(
        canonical="ㄱㅏ",
        predicted="ㅋㅏ",
        phoneme_edits=[
            PhonemeEdit(
                edit_type="substitution",
                expected="ㄱ",
                actual="ㅋ",
                expected_index=0,
                actual_index=0,
            )
        ],
        syllable_candidate_scores=[],
        target_phoneme_scores=[
            TargetPhonemeScore(
                phoneme="ㄱ",
                canonical_index=0,
                edit_type="substitution",
                predicted_phoneme="ㅋ",
                predicted_index=0,
                target_posterior=0.52,
                competing_posterior=0.48,
                gop_like_score=-0.08,
                confidence=0.9,
            )
        ],
        predicted_phoneme_scores=[],
        prosody=_prosody(),
        quality=_quality(),
    )

    assert diagnostics == []


def test_substitution_is_reported_when_target_phoneme_evidence_is_weak():
    diagnostics = DiagnosticEngine().build(
        canonical="ㅋㅏ",
        predicted="ㄱㅏ",
        phoneme_edits=[
            PhonemeEdit(
                edit_type="substitution",
                expected="ㅋ",
                actual="ㄱ",
                expected_index=0,
                actual_index=0,
            )
        ],
        syllable_candidate_scores=[],
        target_phoneme_scores=[
            TargetPhonemeScore(
                phoneme="ㅋ",
                canonical_index=0,
                edit_type="substitution",
                predicted_phoneme="ㄱ",
                predicted_index=0,
                target_posterior=0.18,
                competing_posterior=0.72,
                gop_like_score=-1.38,
                confidence=0.88,
            )
        ],
        predicted_phoneme_scores=[],
        prosody=_prosody(),
        quality=_quality(),
    )

    assert [item.diagnosis_code for item in diagnostics] == ["aspiration_insufficient"]


def test_deletion_requires_ctc_margin_evidence():
    weak = DiagnosticEngine().build(
        canonical="ㅎㅏ",
        predicted="ㅏ",
        phoneme_edits=[PhonemeEdit(edit_type="deletion", expected="ㅎ", expected_index=0)],
        syllable_candidate_scores=[],
        target_phoneme_scores=[],
        predicted_phoneme_scores=[],
        prosody=_prosody(),
        quality=_quality(),
    )
    strong = DiagnosticEngine().build(
        canonical="ㅎㅏ",
        predicted="ㅏ",
        phoneme_edits=[PhonemeEdit(edit_type="deletion", expected="ㅎ", expected_index=0)],
        syllable_candidate_scores=[
            SyllableCandidateScore(
                syllable="하",
                syllable_index=0,
                start_phoneme_index=0,
                end_phoneme_index=2,
                target_sequence=["ㅎ", "ㅏ"],
                alternative_sequence=["ㅏ"],
                logprob_margin=0.9,
                confidence=0.71,
            )
        ],
        target_phoneme_scores=[],
        predicted_phoneme_scores=[],
        prosody=_prosody(),
        quality=_quality(),
    )

    assert weak == []
    assert [item.diagnosis_code for item in strong] == ["segmental_deletion"]


def test_short_low_confidence_insertion_is_suppressed():
    diagnostics = DiagnosticEngine().build(
        canonical="ㅗㅅㅡ",
        predicted="ㅂㅗㅅㅡ",
        phoneme_edits=[PhonemeEdit(edit_type="insertion", actual="ㅂ", actual_index=0)],
        syllable_candidate_scores=[],
        target_phoneme_scores=[],
        predicted_phoneme_scores=[
            PredictedPhonemeScore(
                phoneme="ㅂ",
                predicted_index=0,
                confidence=0.6028,
                frame_start=10,
                frame_end=11,
                frame_count=1,
            )
        ],
        prosody=_prosody(),
        quality=_quality(),
    )

    assert diagnostics == []
