from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas import ModelScoreSummary, PredictedPhonemeScore, SyllableCandidateScore, TargetPhonemeScore


class TimeInterval(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PauseInterval(TimeInterval):
    duration_ms: int = Field(ge=0)
    source: Literal["forced", "acoustic"] = "forced"


class StretchedInterval(TimeInterval):
    label: str
    unit_type: Literal["syllable", "word"]
    ms_per_syllable: float = Field(ge=0.0)
    source: Literal["forced"] = "forced"


class ReferenceDurationComparison(TimeInterval):
    label: str
    unit_type: Literal["syllable", "word"]
    user_duration_ms: int = Field(ge=0)
    reference_duration_ms: int = Field(ge=0)
    duration_delta_ms: int
    duration_ratio: float = Field(ge=0.0)
    source: Literal["tts_reference"] = "tts_reference"


class ReferencePauseComparison(TimeInterval):
    user_duration_ms: int = Field(ge=0)
    reference_duration_ms: int = Field(ge=0)
    duration_delta_ms: int
    duration_ratio: Optional[float] = Field(default=None, ge=0.0)
    pause_level: Optional[Literal["medium", "high"]] = None
    previous_label: Optional[str] = None
    next_label: Optional[str] = None
    source: Literal["tts_reference"] = "tts_reference"


class AlignmentUnit(TimeInterval):
    label: str
    unit_type: Literal["phoneme", "syllable", "word"]
    expected_label: Optional[str] = None
    observed_label: Optional[str] = None
    source: Optional[Literal["forced", "heuristic"]] = None


class AudioQualitySummary(BaseModel):
    snr_db: Optional[float] = None
    clipping_detected: bool = False
    voiced_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    noise_floor_db: Optional[float] = None
    overall_reliability: Literal["high", "medium", "low"] = "medium"


class ProsodySummary(BaseModel):
    speech_rate_syllables_per_second: Optional[float] = None
    articulation_rate_syllables_per_second: Optional[float] = None
    expected_syllable_count: Optional[int] = Field(default=None, ge=0)
    aligned_speech_start_ms: Optional[int] = Field(default=None, ge=0)
    aligned_speech_end_ms: Optional[int] = Field(default=None, ge=0)
    speech_duration_ms: Optional[int] = Field(default=None, ge=0)
    leading_silence_ms: Optional[int] = Field(default=None, ge=0)
    trailing_silence_ms: Optional[int] = Field(default=None, ge=0)
    pause_count: int = Field(default=0, ge=0)
    pause_total_ms: int = Field(default=0, ge=0)
    interior_pause_count: int = Field(default=0, ge=0)
    interior_pause_total_ms: int = Field(default=0, ge=0)
    longest_interior_pause_ms: int = Field(default=0, ge=0)
    pause_intervals: list[PauseInterval] = Field(default_factory=list)
    slowest_aligned_unit: Optional[str] = None
    slowest_aligned_unit_ms_per_syllable: Optional[float] = Field(default=None, ge=0.0)
    stretched_intervals: list[StretchedInterval] = Field(default_factory=list)
    reference_speech_duration_ms: Optional[int] = Field(default=None, ge=0)
    speech_duration_ratio: Optional[float] = Field(default=None, ge=0.0)
    reference_duration_comparisons: list[ReferenceDurationComparison] = Field(default_factory=list)
    reference_pause_comparisons: list[ReferencePauseComparison] = Field(default_factory=list)
    timing_source: Literal["forced_alignment", "acoustic", "none"] = "acoustic"
    reference_timing_source: Optional[Literal["tts_reference"]] = None
    rate_reliability: Literal["high", "medium", "low"] = "low"
    notes: list[str] = Field(default_factory=list)


class DiagnosticCandidate(BaseModel):
    diagnosis_code: str
    category: Literal["segmental", "prosodic", "quality"]
    target_unit: Optional[str] = None
    severity: Literal["low", "medium", "high"] = "medium"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_keys: list[str] = Field(default_factory=list)
    rationale: str


class PhonemeEdit(BaseModel):
    edit_type: Literal["substitution", "insertion", "deletion"]
    expected: Optional[str] = None
    actual: Optional[str] = None
    expected_index: Optional[int] = Field(default=None, ge=0)
    actual_index: Optional[int] = Field(default=None, ge=0)
    context: Optional[str] = None
    syllable: Optional[str] = None
    syllable_index: Optional[int] = Field(default=None, ge=0)
    note: Optional[str] = None


class EvidencePolicy(BaseModel):
    language: str = "ko"
    feedback_style: Literal["pedagogical", "clinical", "concise"] = "pedagogical"
    avoid_overclaiming: bool = True
    suppress_low_reliability_feedback: bool = True


class AcousticEvidencePacket(BaseModel):
    script: str
    canonical_text: Optional[str] = None
    predicted_text: Optional[str] = None
    canonical_phonemes: str
    predicted_phonemes: Optional[str] = None
    model_score: Optional[ModelScoreSummary] = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] = Field(default_factory=list)
    target_phoneme_scores: list[TargetPhonemeScore] = Field(default_factory=list)
    syllable_candidate_scores: list[SyllableCandidateScore] = Field(default_factory=list)
    audio_quality: AudioQualitySummary
    phoneme_edits: list[PhonemeEdit] = Field(default_factory=list)
    alignments: list[AlignmentUnit] = Field(default_factory=list)
    prosody: Optional[ProsodySummary] = None
    diagnostic_candidates: list[DiagnosticCandidate] = Field(default_factory=list)
    policy: EvidencePolicy = Field(default_factory=EvidencePolicy)


class FeedbackIssue(BaseModel):
    unit: Optional[str] = None
    category: Literal["segmental", "prosodic", "quality"]
    diagnosis: str
    evidence: str
    likely_perception: Optional[str] = None
    coaching: str
    confidence: Literal["low", "medium", "high"] = "medium"


class AcousticLLMFeedback(BaseModel):
    summary: str
    issues: list[FeedbackIssue] = Field(default_factory=list)
    overall_confidence: Literal["low", "medium", "high"] = "medium"
    next_practice_focus: list[str] = Field(default_factory=list)


class PronunciationScore(BaseModel):
    overall: float = Field(ge=0.0, le=100.0)
    segmental: float = Field(ge=0.0, le=100.0)
    prosody: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    audio_quality: float = Field(ge=0.0, le=100.0)
    source: Literal["heuristic_v1"] = "heuristic_v1"
    note: str


class PronunciationAnalysisResponse(BaseModel):
    script: str
    canonical_phonemes: str
    predicted_phonemes: str
    pronunciation_score: PronunciationScore
    model_score: Optional[ModelScoreSummary] = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] = Field(default_factory=list)
    target_phoneme_scores: list[TargetPhonemeScore] = Field(default_factory=list)
    syllable_candidate_scores: list[SyllableCandidateScore] = Field(default_factory=list)
    audio_quality: AudioQualitySummary
    phoneme_edits: list[PhonemeEdit] = Field(default_factory=list)
    alignments: list[AlignmentUnit] = Field(default_factory=list)
    prosody: Optional[ProsodySummary] = None
    diagnostic_candidates: list[DiagnosticCandidate] = Field(default_factory=list)
    llm_feedback: Optional[AcousticLLMFeedback] = None
    notes: list[str] = Field(default_factory=list)


class ForcedAlignmentItem(BaseModel):
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)


class ForcedAlignmentResponse(BaseModel):
    language: str
    items: list[ForcedAlignmentItem] = Field(default_factory=list)
    source_model: str
    resolution_ms: int = Field(default=80, ge=1)
