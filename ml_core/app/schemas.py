from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service_mode: str
    model_path: Optional[str] = None
    infer_script_path: Optional[str] = None
    inference_base_url: Optional[str] = None
    inference_status: Optional[str] = None
    aligner_base_url: Optional[str] = None
    aligner_status: Optional[str] = None
    aligner_model_id: Optional[str] = None
    gemini_model: Optional[str] = None
    gemini_status: Optional[str] = None


class PronunciationIssue(BaseModel):
    issue_type: Literal["substitution", "insertion", "deletion"]
    expected: str
    actual: str


class Summary(BaseModel):
    total_issues: int
    substitutions: int
    insertions: int
    deletions: int
    accuracy: float = Field(ge=0.0, le=1.0)


class ModelScoreSummary(BaseModel):
    decoder_score: Optional[float] = None
    normalized_decoder_score: Optional[float] = None
    token_count: Optional[int] = Field(default=None, ge=0)
    score_source: Optional[str] = None
    note: Optional[str] = None


class PredictedPhonemeScore(BaseModel):
    phoneme: str
    predicted_index: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    frame_start: int = Field(ge=0)
    frame_end: int = Field(ge=0)
    frame_count: int = Field(ge=0)


class TargetPhonemeScore(BaseModel):
    phoneme: str
    canonical_index: int = Field(ge=0)
    edit_type: Literal["match", "substitution", "deletion", "insertion"]
    predicted_phoneme: Optional[str] = None
    predicted_index: Optional[int] = Field(default=None, ge=0)
    target_posterior: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    competing_posterior: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    gop_like_score: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    note: Optional[str] = None


class SyllableCandidateScore(BaseModel):
    syllable: str
    syllable_index: int = Field(ge=0)
    start_phoneme_index: int = Field(ge=0)
    end_phoneme_index: int = Field(ge=0)
    target_sequence: list[str] = Field(default_factory=list)
    alternative_sequence: list[str] = Field(default_factory=list)
    target_ctc_logprob: Optional[float] = None
    alternative_ctc_logprob: Optional[float] = None
    logprob_margin: Optional[float] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    note: Optional[str] = None


class PredictResponse(BaseModel):
    script: str
    canonical_phonemes: str
    predicted_phonemes: str
    canonical_text: str
    predicted_text: str
    issues: list[PronunciationIssue]
    summary: Summary
    model_score: Optional[ModelScoreSummary] = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] = Field(default_factory=list)
    target_phoneme_scores: list[TargetPhonemeScore] = Field(default_factory=list)
    syllable_candidate_scores: list[SyllableCandidateScore] = Field(default_factory=list)
    raw_hypothesis_line: str
