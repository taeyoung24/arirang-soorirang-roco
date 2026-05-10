from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import (
    AcousticLLMFeedback,
    ForcedAlignmentResponse,
    PronunciationAnalysisResponse,
    SyllableStressResult,
)
from app.gemini_client import GeminiFeedbackClient
from app.llm_evidence_builder import LLMEvidenceBuilder
from app.schemas import PredictResponse
from app.stress_analyzer import StressAnalyzer
from app.tts_service import TTSService


class PronunciationAnalysisService:
    def __init__(
        self,
        analyzer: AcousticAnalyzer,
        gemini_client: GeminiFeedbackClient,
        tts_service: Optional[TTSService] = None,
        stress_analyzer: Optional[StressAnalyzer] = None,
    ):
        self.analyzer = analyzer
        self.gemini_client = gemini_client
        self.llm_evidence_builder = LLMEvidenceBuilder()
        self.tts_service = tts_service
        self.stress_analyzer = stress_analyzer or StressAnalyzer()

    def analyze(
        self,
        audio_bytes: bytes,
        prediction: PredictResponse,
        forced_alignment: ForcedAlignmentResponse | None = None,
        include_llm_feedback: bool = True,
        feedback_language: str = "ko",
    ) -> PronunciationAnalysisResponse:
        response, evidence = self.analyzer.analyze(
            audio_bytes=audio_bytes,
            prediction=prediction,
            forced_alignment=forced_alignment,
            include_llm_note=include_llm_feedback and self.gemini_client.enabled,
            feedback_language=feedback_language,
        )
        self._attach_stress_analysis(response, audio_bytes, prediction.script)
        if not include_llm_feedback:
            response.notes.append("LLM feedback was not requested for this endpoint.")
            return response
        if not self.gemini_client.enabled:
            response.notes.append("Gemini API key is not configured, so LLM feedback was skipped.")
            return response
        llm_evidence = self.llm_evidence_builder.build(evidence)
        response.llm_feedback = self._filter_llm_feedback(
            self.gemini_client.generate_feedback(llm_evidence),
            allowed_units={edit.expected for edit in llm_evidence.phoneme_edits if edit.expected}
            | {edit.actual for edit in llm_evidence.phoneme_edits if edit.actual},
        )
        return response

    def _attach_stress_analysis(
        self, response: PronunciationAnalysisResponse, user_audio: bytes, script: str
    ) -> None:
        if self.tts_service is None or not self.tts_service.has_api_key:
            response.notes.append("Stress analysis skipped: TTS API key is not configured.")
            return
        try:
            ref_audio = self.tts_service.synthesize_speech(script)
            results = self.stress_analyzer.analyze(user_audio, ref_audio, script)
            response.syllable_stress = [SyllableStressResult(**asdict(r)) for r in results]
        except Exception as exc:
            response.notes.append(f"Stress analysis skipped: {exc}")

    @staticmethod
    def _filter_llm_feedback(feedback: AcousticLLMFeedback, allowed_units: set[str]) -> AcousticLLMFeedback:
        if not allowed_units:
            return feedback
        feedback.issues = [
            issue
            for issue in feedback.issues
            if issue.unit is None or issue.unit in allowed_units
        ]
        return feedback
