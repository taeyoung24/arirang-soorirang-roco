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
        evidence_json = evidence.model_dump_json(exclude_none=True, indent=2)
        feedback_language = evidence.policy.language
        instructions = {
            "task": "Generate learner-facing Korean pronunciation feedback from structured phonetic evidence.",
            "response_language": feedback_language,
            "scope": [
                "Use MDD phoneme mismatches as the primary error evidence.",
                "Use phoneme_edits as the canonical mismatch summary.",
                "If phoneme_edits shows one deletion or insertion, do not describe later aligned sounds as a cascade of substitutions.",
                "When the same phoneme appears multiple times, use phoneme_edits.expected_index, syllable, and context to identify the occurrence.",
                "Use Praat F1/F2, pitch, and intensity only as supporting measurements.",
                "Treat *_reference_signal diagnostics as possible hints, not confirmed errors.",
                "Do not create new pronunciation errors beyond the supplied diagnostic candidates.",
            ],
            "requirements": [
                "Use only the supplied evidence.",
                "Do not infer hidden measurements.",
                "Treat MDD phoneme mismatch as stronger evidence than formant-only diagnostics.",
                "For foreign-accent feedback, describe the likely Korean listener perception, not medical or native-speaker claims.",
                "If alignment source is heuristic or audio reliability is low, lower the confidence.",
                "If reliability is low, mention that uncertainty briefly.",
                "Prioritize the top 1-3 issues.",
                "Coaching should be short, concrete, and pronounceable by a learner.",
                "Every issue.unit must come from phoneme_edits.expected or phoneme_edits.actual.",
                f"Write all learner-facing text in this language code or language name: {feedback_language}.",
            ],
        }
        return (
            "You are a Korean pronunciation coach.\n"
            "Return JSON only and follow the provided schema.\n"
            f"Instruction:\n{json.dumps(instructions, ensure_ascii=False, indent=2)}\n"
            f"Evidence:\n{evidence_json}"
        )
