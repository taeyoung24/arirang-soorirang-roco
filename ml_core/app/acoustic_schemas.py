from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas import ModelScoreSummary, PredictedPhonemeScore, TargetPhonemeScore


class TimeInterval(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AlignmentUnit(TimeInterval):
    label: str
    unit_type: Literal["phoneme", "syllable", "word"]
    expected_label: Optional[str] = None
    observed_label: Optional[str] = None
    source: Optional[Literal["forced", "heuristic"]] = None


class FeatureMeasurement(BaseModel):
    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    baseline_mean: Optional[float] = None
    baseline_std: Optional[float] = Field(default=None, ge=0.0)
    zscore: Optional[float] = None
    percentile: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    reliability: Literal["high", "medium", "low"] = "medium"
    note: Optional[str] = None


class SegmentFeatureBundle(BaseModel):
    label: str
    unit_type: Literal["phoneme", "syllable", "word"]
    interval: TimeInterval
    features: list[FeatureMeasurement] = Field(default_factory=list)


class AudioQualitySummary(BaseModel):
    snr_db: Optional[float] = None
    clipping_detected: bool = False
    voiced_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    noise_floor_db: Optional[float] = None
    overall_reliability: Literal["high", "medium", "low"] = "medium"


class ProsodySummary(BaseModel):
    speech_rate_syllables_per_second: Optional[float] = None
    articulation_rate_syllables_per_second: Optional[float] = None
    pause_count: int = Field(default=0, ge=0)
    pause_total_ms: int = Field(default=0, ge=0)
    utterance_f0_mean_hz: Optional[float] = None
    utterance_f0_range_semitones: Optional[float] = None
    phrase_final_f0_slope: Optional[float] = None
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
    canonical_phonemes: str
    predicted_phonemes: Optional[str] = None
    model_score: Optional[ModelScoreSummary] = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] = Field(default_factory=list)
    target_phoneme_scores: list[TargetPhonemeScore] = Field(default_factory=list)
    audio_quality: AudioQualitySummary
    phoneme_edits: list[PhonemeEdit] = Field(default_factory=list)
    alignments: list[AlignmentUnit] = Field(default_factory=list)
    segment_features: list[SegmentFeatureBundle] = Field(default_factory=list)
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


class PronunciationAnalysisResponse(BaseModel):
    script: str
    canonical_phonemes: str
    predicted_phonemes: str
    model_score: Optional[ModelScoreSummary] = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] = Field(default_factory=list)
    target_phoneme_scores: list[TargetPhonemeScore] = Field(default_factory=list)
    audio_quality: AudioQualitySummary
    phoneme_edits: list[PhonemeEdit] = Field(default_factory=list)
    alignments: list[AlignmentUnit] = Field(default_factory=list)
    segment_features: list[SegmentFeatureBundle] = Field(default_factory=list)
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
