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
                "Use script/canonical_text and predicted_text as the main utterance-level comparison.",
                "Use canonical_phonemes and predicted_phonemes to judge global phoneme-sequence similarity.",
                "If the predicted utterance is substantially different from the target, prioritize that over small local corrections.",
                "Use MDD phoneme mismatches as supporting evidence for local pronunciation errors.",
                "Use phoneme_edits as a local mismatch summary and supporting detail.",
                "If phoneme_edits shows one deletion or insertion, do not describe later aligned sounds as a cascade of substitutions.",
                "When the same phoneme appears multiple times, use phoneme_edits.expected_index, syllable, and context to identify the occurrence.",
                "Use acoustic measurements only as secondary context when they are explicitly supplied.",
                "Do not create specific local pronunciation errors beyond the supplied phoneme_edits and diagnostic_candidates.",
            ],
            "requirements": [
                "Use only the supplied evidence.",
                "Do not infer hidden measurements.",
                "Treat the full target/predicted utterance comparison as primary evidence.",
                "Treat MDD phoneme mismatch and phoneme edit alignment as supporting evidence for specific local issues.",
                "predicted_text and predicted_phonemes are model-decoded pronunciation evidence, not a guaranteed literal transcript.",
                "If canonical_text and predicted_text differ substantially, say the target sentence was pronounced very differently before giving local phoneme coaching.",
                "For foreign-accent feedback, describe the likely Korean listener perception, not medical or native-speaker claims.",
                "The learner may be a non-native Korean speaker; do not push native-speed delivery.",
                "If a long interior pause is present, describe the issue as pause/connection timing rather than general slow speech.",
                "For prosodic timing, frame coaching as smoother connection and intelligibility, not speaking as fast as the TTS reference.",
                "If diagnosis_code is stretched_aligned_unit, describe the target unit as held or stretched too long.",
                "For stretched_aligned_unit, set issue.unit to the diagnostic target_unit when it is present.",
                "Do not convert stretched_aligned_unit into a pause issue unless a reference_pause_comparison with pause_level medium or high is present.",
                "Reference pause comparisons may include pause_level medium or high.",
                "If pause_level is medium, describe it as a noticeable pause between words.",
                "If pause_level is high, prioritize it as a main prosodic issue.",
                "Do not describe medium pause_level as globally slow speech.",
                "If alignment source is heuristic or audio reliability is low, lower the confidence.",
                "If reliability is low, mention that uncertainty briefly.",
                "Prioritize the top 1-3 issues.",
                "If diagnostic_candidates is not empty, issues must contain at least one issue grounded in those diagnostics.",
                "issue.diagnosis must be a short learner-facing phrase, not a diagnostic code.",
                "Never copy snake_case values such as diagnosis_code into learner-facing fields.",
                "Coaching should be short, concrete, and pronounceable by a learner.",
                "For segmental issues, issue.unit must come from phoneme_edits.expected or phoneme_edits.actual.",
                "For prosodic issues such as slow speech rate or long pauses, issue.unit may be null.",
                f"Write all learner-facing text in this language code or language name: {feedback_language}.",
            ],
        }
        return (
            "You are a Korean pronunciation coach.\n"
            "Return JSON only and follow the provided schema.\n"
            f"Instruction:\n{json.dumps(instructions, ensure_ascii=False, indent=2)}\n"
            f"Evidence:\n{evidence_json}"
        )
