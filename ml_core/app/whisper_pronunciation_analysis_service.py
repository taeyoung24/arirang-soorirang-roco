from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.acoustic_analysis import AcousticAnalyzer
from app.acoustic_schemas import (
    AcousticEvidencePacket,
    AcousticLLMFeedback,
    DiagnosticCandidate,
    EvidencePolicy,
    ForcedAlignmentResponse,
    PhonemeEdit,
    PronunciationAnalysisResponse,
    PronunciationScore,
)
from app.diagnostic_engine import DiagnosticEngine
from app.gemini_client import GeminiFeedbackClient
from app.llm_evidence_builder import LLMEvidenceBuilder
from app.schemas import ModelScoreSummary
from app.whisper_client import WhisperTranscription


NO_DIAGNOSTIC_SUMMARY = {
    "ko": "뚜렷한 발음 오류가 감지되지 않았습니다.",
    "en": "No clear pronunciation errors were detected.",
    "ru": "Явных ошибок произношения не обнаружено.",
}


def _normalize_feedback_language(value: str) -> str:
    language = (value or "ko").strip().lower().split("-", 1)[0]
    return language if language in NO_DIAGNOSTIC_SUMMARY else "ko"


def _no_diagnostic_summary(feedback_language: str) -> str:
    return NO_DIAGNOSTIC_SUMMARY[_normalize_feedback_language(feedback_language)]


class WhisperPronunciationAnalysisService:
    def __init__(
        self,
        analyzer: AcousticAnalyzer,
        diagnostic_engine: DiagnosticEngine,
        gemini_client: GeminiFeedbackClient,
    ):
        self.analyzer = analyzer
        self.diagnostic_engine = diagnostic_engine
        self.gemini_client = gemini_client
        self.llm_evidence_builder = LLMEvidenceBuilder()

    def analyze(
        self,
        audio_bytes: bytes,
        script: str,
        transcription: WhisperTranscription,
        forced_alignment: ForcedAlignmentResponse | None = None,
        reference_alignment: ForcedAlignmentResponse | None = None,
        feedback_language: str = "ko",
    ) -> PronunciationAnalysisResponse:
        audio = self.analyzer._load_audio(audio_bytes)
        quality = self.analyzer._analyze_audio_quality(audio)
        canonical_phonemes = self.analyzer._decompose_hangul(script)
        predicted_phonemes = self.analyzer._decompose_hangul(transcription.text)
        transcript_match = self._transcript_match(script, transcription.text)
        edits = [] if transcript_match["status"] == "pass" else self._character_edits(script, transcription.text)
        observed_by_expected = list(canonical_phonemes)
        alignments, used_forced_alignment = self.analyzer._resolve_alignments(
            script,
            canonical_phonemes,
            canonical_phonemes,
            audio.duration_ms,
            forced_alignment,
            observed_by_expected,
        )
        reference_alignments = self.analyzer._resolve_reference_alignments(script, canonical_phonemes, reference_alignment)
        prosody = self.analyzer.feature_extractor.extract_prosody(audio, alignments, reference_alignments)
        diagnostics = self.diagnostic_engine.build(
            canonical_phonemes,
            canonical_phonemes,
            [],
            [],
            [],
            [],
            prosody,
            quality,
        )
        if transcript_match["status"] == "fail":
            diagnostics.insert(0, self._asr_mismatch_diagnostic(script, transcription.text, transcript_match["cer"]))
        elif transcript_match["status"] == "uncertain":
            diagnostics.insert(0, self._asr_uncertain_diagnostic(script, transcription.text, transcript_match["cer"]))

        score = self._score(transcript_match["cer"], transcript_match["status"], prosody, quality, diagnostics)
        display_status = "needs_attention" if diagnostics else "normal"
        display_predicted_text = transcription.text.strip() or script
        notes = [
            "Segmental pronunciation is inferred from Whisper ASR transcript agreement, not from the removed MDD phoneme decoder.",
            f"Whisper transcript match status: {transcript_match['status']} (CER={transcript_match['cer']:.3f}).",
        ]
        if used_forced_alignment:
            notes.append("Word and syllable timings come from Qwen3 forced alignment.")
        if reference_alignment and reference_alignments:
            notes.append("Prosodic timing diagnostics compare learner speech against cached TTS reference alignment.")
        if self.gemini_client.enabled:
            notes.append("LLM feedback is generated from structured Whisper/prosody evidence, not from raw audio.")

        evidence = AcousticEvidencePacket(
            script=script,
            canonical_text=script,
            predicted_text=transcription.text,
            canonical_phonemes=canonical_phonemes,
            predicted_phonemes=predicted_phonemes,
            model_score=ModelScoreSummary(
                normalized_decoder_score=transcription.confidence,
                score_source="faster_whisper",
                note="Whisper confidence proxy; not calibrated as pronunciation confidence.",
            ),
            audio_quality=quality,
            phoneme_edits=edits,
            alignments=alignments,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            policy=EvidencePolicy(language=feedback_language),
        )
        response = PronunciationAnalysisResponse(
            script=script,
            predicted_text=transcription.text,
            display_pronunciation_status=display_status,
            display_predicted_text=display_predicted_text,
            display_predicted_phonemes=predicted_phonemes if transcription.text.strip() else canonical_phonemes,
            raw_predicted_text=transcription.text,
            canonical_phonemes=canonical_phonemes,
            predicted_phonemes=predicted_phonemes,
            pronunciation_score=score,
            model_score=evidence.model_score,
            audio_quality=quality,
            phoneme_edits=edits,
            alignments=alignments,
            prosody=prosody,
            diagnostic_candidates=diagnostics,
            notes=notes,
        )
        self._attach_llm_feedback(response, evidence)
        return response

    def _attach_llm_feedback(self, response: PronunciationAnalysisResponse, evidence: AcousticEvidencePacket) -> None:
        if not self.gemini_client.enabled:
            response.notes.append("Gemini API key is not configured, so LLM feedback was skipped.")
            return
        llm_evidence = self.llm_evidence_builder.build(evidence)
        if not llm_evidence.diagnostic_candidates:
            response.llm_feedback = AcousticLLMFeedback(
                summary=_no_diagnostic_summary(evidence.policy.language),
                issues=[],
                overall_confidence="medium",
                next_practice_focus=[],
            )
            return
        response.llm_feedback = self.gemini_client.generate_feedback(llm_evidence)

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^0-9a-zA-Z가-힣]", "", text).lower()

    @classmethod
    def _transcript_match(cls, script: str, transcript: str) -> dict[str, float | str]:
        target = cls._normalize(script)
        observed = cls._normalize(transcript)
        if not target:
            return {"cer": 1.0, "status": "fail"}
        if not observed:
            return {"cer": 1.0, "status": "fail"}
        similarity = SequenceMatcher(a=target, b=observed).ratio()
        cer = max(0.0, min(1.0, 1.0 - similarity))
        if cer <= 0.12:
            status = "pass"
        elif cer <= 0.32:
            status = "uncertain"
        else:
            status = "fail"
        return {"cer": cer, "status": status}

    @staticmethod
    def _score(cer: float, status: str, prosody, quality, diagnostics: list[DiagnosticCandidate]) -> PronunciationScore:
        if status == "pass":
            segmental = 100.0
        elif status == "uncertain":
            segmental = max(70.0, 92.0 - cer * 100.0)
        else:
            segmental = max(35.0, 85.0 - cer * 120.0)
        prosody_score = AcousticAnalyzer._prosody_score(prosody)
        audio_quality_score = AcousticAnalyzer._audio_quality_score(quality)
        overall = 0.78 * segmental + 0.22 * prosody_score
        overall -= min(10.0, len(diagnostics) * 1.5)
        return PronunciationScore(
            overall=round(max(0.0, min(100.0, overall)), 1),
            segmental=round(max(0.0, min(100.0, segmental)), 1),
            prosody=round(max(0.0, min(100.0, prosody_score)), 1),
            audio_quality=round(audio_quality_score, 1),
            note=(
                "Heuristic 0-100 score from Whisper transcript agreement and timing/prosody evidence. "
                "Audio quality is reported separately and does not affect the score. It is not externally calibrated."
            ),
        )

    @staticmethod
    def _asr_mismatch_diagnostic(script: str, transcript: str, cer: float) -> DiagnosticCandidate:
        return DiagnosticCandidate(
            diagnosis_code="asr_transcript_mismatch",
            category="segmental",
            target_unit=None,
            severity="high",
            confidence=max(0.7, min(0.95, 0.65 + cer)),
            evidence_keys=["whisper_transcript_agreement"],
            rationale=f"Whisper transcript differs from the target script: target={script!r}, transcript={transcript!r}.",
        )

    @staticmethod
    def _asr_uncertain_diagnostic(script: str, transcript: str, cer: float) -> DiagnosticCandidate:
        return DiagnosticCandidate(
            diagnosis_code="asr_transcript_uncertain",
            category="segmental",
            target_unit=None,
            severity="medium",
            confidence=max(0.5, min(0.75, 0.45 + cer)),
            evidence_keys=["whisper_transcript_agreement"],
            rationale=f"Whisper transcript partially differs from the target script: target={script!r}, transcript={transcript!r}.",
        )

    @classmethod
    def _character_edits(cls, script: str, transcript: str) -> list[PhonemeEdit]:
        target = cls._normalize(script)
        observed = cls._normalize(transcript)
        matcher = SequenceMatcher(a=target, b=observed)
        edits: list[PhonemeEdit] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace":
                for offset in range(max(i2 - i1, j2 - j1)):
                    expected = target[i1 + offset] if i1 + offset < i2 else None
                    actual = observed[j1 + offset] if j1 + offset < j2 else None
                    edits.append(PhonemeEdit(edit_type="substitution", expected=expected, actual=actual, expected_index=i1 + offset if expected else None, actual_index=j1 + offset if actual else None, note="character-level ASR transcript difference"))
            elif tag == "delete":
                for index in range(i1, i2):
                    edits.append(PhonemeEdit(edit_type="deletion", expected=target[index], expected_index=index, note="character missing from Whisper transcript"))
            elif tag == "insert":
                for index in range(j1, j2):
                    edits.append(PhonemeEdit(edit_type="insertion", actual=observed[index], actual_index=index, note="extra character in Whisper transcript"))
        return edits[:12]
