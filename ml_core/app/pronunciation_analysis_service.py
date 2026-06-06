from __future__ import annotations

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import AcousticLLMFeedback, ForcedAlignmentResponse, PronunciationAnalysisResponse
from app.gemini_client import GeminiFeedbackClient
from app.llm_evidence_builder import LLMEvidenceBuilder
from app.schemas import PredictResponse


class PronunciationAnalysisService:
    def __init__(self, analyzer: AcousticAnalyzer, gemini_client: GeminiFeedbackClient):
        self.analyzer = analyzer
        self.gemini_client = gemini_client
        self.llm_evidence_builder = LLMEvidenceBuilder()

    def analyze(
        self,
        audio_bytes: bytes,
        prediction: PredictResponse,
        forced_alignment: ForcedAlignmentResponse | None = None,
        reference_alignment: ForcedAlignmentResponse | None = None,
        feedback_language: str = "ko",
    ) -> PronunciationAnalysisResponse:
        response, evidence = self.analyzer.analyze(
            audio_bytes=audio_bytes,
            prediction=prediction,
            forced_alignment=forced_alignment,
            reference_alignment=reference_alignment,
            include_llm_note=self.gemini_client.enabled,
            feedback_language=feedback_language,
        )
        if not self.gemini_client.enabled:
            response.notes.append("Gemini API key is not configured, so LLM feedback was skipped.")
            return response
        llm_evidence = self.llm_evidence_builder.build(evidence)
        if not llm_evidence.diagnostic_candidates:
            response.llm_feedback = AcousticLLMFeedback(
                summary="뚜렷한 발음 오류가 감지되지 않았습니다.",
                issues=[],
                overall_confidence="medium",
                next_practice_focus=[],
            )
            response.notes.append("LLM feedback used calibrated diagnostic candidates only; no candidate passed the evidence gate.")
            return response
        allowed_segmental_units = {
            candidate.target_unit
            for candidate in llm_evidence.diagnostic_candidates
            if candidate.category == "segmental" and candidate.target_unit
        }
        allowed_prosodic_units = {
            candidate.target_unit
            for candidate in llm_evidence.diagnostic_candidates
            if candidate.category == "prosodic" and candidate.target_unit
        }
        response.llm_feedback = self._filter_llm_feedback(
            self.gemini_client.generate_feedback(llm_evidence),
            allowed_segmental_units=allowed_segmental_units,
            allowed_prosodic_units=allowed_prosodic_units,
        )
        return response

    @staticmethod
    def _filter_llm_feedback(
        feedback: AcousticLLMFeedback,
        allowed_segmental_units: set[str],
        allowed_prosodic_units: set[str],
    ) -> AcousticLLMFeedback:
        feedback.issues = [
            issue
            for issue in feedback.issues
            if issue.unit is None
            or (issue.category == "segmental" and issue.unit in allowed_segmental_units)
            or (issue.category == "prosodic" and issue.unit in allowed_prosodic_units)
            or (issue.category == "quality")
        ]
        return feedback
