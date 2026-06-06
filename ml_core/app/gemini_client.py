from __future__ import annotations

import json

import httpx

from app.acoustic_schemas import AcousticEvidencePacket, AcousticLLMFeedback


class GeminiFeedbackClient:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model: str, timeout_seconds: float):
        self.api_key = api_key.strip()
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate_feedback(self, evidence: AcousticEvidencePacket) -> AcousticLLMFeedback:
        if not self.enabled:
            raise RuntimeError("Gemini API key is not configured.")
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._build_prompt(evidence),
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": AcousticLLMFeedback.model_json_schema(),
            },
        }
        url = f"{self.BASE_URL}/{self.model}:generateContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        parsed = response.json()
        try:
            text = parsed["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Gemini response shape: {parsed}") from exc
        return AcousticLLMFeedback.model_validate_json(text)

    @staticmethod
    def _build_prompt(evidence: AcousticEvidencePacket) -> str:
        evidence_json = json.dumps(
            GeminiFeedbackClient._compact_evidence(evidence),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        feedback_language = evidence.policy.language
        instructions = {
            "task": "Generate short learner-facing Korean pronunciation feedback from structured evidence.",
            "response_language": feedback_language,
            "requirements": [
                "Use only the supplied evidence.",
                "Base issues on diagnostic_candidates and phoneme_edits.",
                "Do not copy snake_case diagnosis codes into learner-facing fields.",
                "Return 1-3 concise issues with concrete coaching.",
                f"Write learner-facing text in {feedback_language}.",
            ],
        }
        return (
            "You are a Korean pronunciation coach.\n"
            "Return JSON only and follow the provided schema.\n"
            f"Instruction:\n{json.dumps(instructions, ensure_ascii=False, separators=(',', ':'))}\n"
            f"Evidence:\n{evidence_json}"
        )

    @staticmethod
    def _compact_evidence(evidence: AcousticEvidencePacket) -> dict:
        payload = {
            "target_text": evidence.script,
            "predicted_text": evidence.predicted_text,
            "target_phonemes": evidence.canonical_phonemes,
            "predicted_phonemes": evidence.predicted_phonemes,
            "phoneme_edits": [
                edit.model_dump(exclude_none=True)
                for edit in evidence.phoneme_edits[:3]
            ],
            "diagnostic_candidates": [
                item.model_dump(exclude_none=True)
                for item in evidence.diagnostic_candidates[:3]
            ],
            "feedback_language": evidence.policy.language,
        }
        if evidence.audio_quality.overall_reliability != "high":
            payload["audio_quality"] = evidence.audio_quality.model_dump(exclude_none=True)
        if evidence.prosody is not None:
            payload["prosody"] = evidence.prosody.model_dump(
                exclude_none=True,
                exclude={
                    "pause_intervals",
                    "stretched_intervals",
                    "reference_duration_comparisons",
                    "reference_pause_comparisons",
                },
            )
        return {key: value for key, value in payload.items() if value not in (None, [], {})}
