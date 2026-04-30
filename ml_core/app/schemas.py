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


class PredictResponse(BaseModel):
    script: str
    canonical_phonemes: str
    predicted_phonemes: str
    canonical_text: str
    predicted_text: str
    issues: list[PronunciationIssue]
    summary: Summary
    raw_hypothesis_line: str
