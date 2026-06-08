from __future__ import annotations

import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.schemas import PredictedPhonemeScore, SyllableCandidateScore, TargetPhonemeScore


@dataclass(frozen=True)
class InferenceResult:
    raw_line: str
    decoder_score: float | None = None
    token_count: int | None = None
    score_source: str | None = None
    predicted_phoneme_scores: list[PredictedPhonemeScore] | None = None
    target_phoneme_scores: list[TargetPhonemeScore] | None = None
    syllable_candidate_scores: list[SyllableCandidateScore] | None = None


class InferenceBackend(Protocol):
    def predict(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        ...


def resolve_device(device: str) -> str:
    """Utility helper to resolve execution hardware target."""
    if device != "auto":
        return device
    
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class SubprocessInferenceBackend:
    def __init__(self, settings):
        self.settings = settings

    def predict(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        command = [
            sys.executable,
            self.settings.infer_script_path,
            str(manifest_dir),
            "--task",
            "audio_finetuning",
            "--nbest",
            "1",
            "--path",
            self.settings.model_path,
            "--gen-subset",
            "test",
            "--results-path",
            str(results_dir),
            "--w2l-decoder",
            "viterbi",
            "--criterion",
            "ctc",
            "--quiet",
            "--max-tokens",
            str(self.settings.max_tokens),
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "fairseq infer failed")

        result_file = results_dir / f"hypo.units-{Path(self.settings.model_path).name}-test.txt"
        if not result_file.exists():
            raise RuntimeError(f"Inference output file not found: {result_file}")
        lines = [line.strip() for line in result_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not lines:
            raise RuntimeError("Inference output file is empty.")
        return InferenceResult(raw_line=lines[0])


class InProcessFairseqBackend:
    def __init__(self, runner):
        self.runner = runner

    def predict(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        return self.runner.predict_units(manifest_dir)


class Wav2Vec2InferenceBackend:
    CHOSEONG = [
        "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]
    JUNGSEONG = [
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    ]
    JONGSEONG = [
        "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ",
        "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]

    def __init__(self, model_id: str, device: str = "auto"):
        # Import heavy ML libraries only inside initialization to enable safe lazy-loading
        import torch
        from g2pk2 import G2p
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

        self._device = resolve_device(device)
        self._processor = Wav2Vec2Processor.from_pretrained(model_id)
        self._model = Wav2Vec2ForCTC.from_pretrained(model_id).to(self._device)
        self._model.eval()
        self._g2p = G2p()
        self._lock = threading.Lock()

    def predict(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        import soundfile as sf
        import torch

        # TODO: Replace this hardcoded file convention with a structured manifest parser
        audio_path = manifest_dir.parent / "sound_16k" / "input.wav"
        if not audio_path.exists():
            raise FileNotFoundError(f"Target audio file not found: {audio_path}")

        samples, _ = sf.read(str(audio_path), dtype="float32")
        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        inputs = self._processor(samples, sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with self._lock:
            with torch.no_grad():
                logits = self._model(**inputs).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self._processor.decode(predicted_ids[0])

        transcription = transcription.strip()
        if not transcription:
            raise RuntimeError("wav2vec2 produced empty transcription.")

        transcription = self._normalize_asr_output(transcription)
        phonemes = self._to_phonemes(transcription)
        if not phonemes:
            raise RuntimeError("wav2vec2 transcription yielded no phonemes after G2P.")

        return InferenceResult(raw_line=phonemes)

    _ASR_NORMALIZATION = [
        ("주십시오", "줘"),
        ("하십시오", "해"),
        ("주세요", "줘"),
        ("하세요", "해"),
        ("보세요", "봐"),
        ("오세요", "와"),
        ("있어요", "있어"),
        ("없어요", "없어"),
        ("해요", "해"),
    ]

    def _normalize_asr_output(self, text: str) -> str:
        for formal, colloquial in self._ASR_NORMALIZATION:
            text = text.replace(formal, colloquial)
        return text

    def _to_phonemes(self, text: str) -> str:
        g2p_text = self._g2p(text)
        normalized = re.sub(r"\s+", "", g2p_text.strip())
        result: list[str] = []
        
        for char in normalized:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:
                syllable_index = code - 0xAC00
                cho = syllable_index // 588
                jung = (syllable_index % 588) // 28
                jong = syllable_index % 28
                
                result.append(self.CHOSEONG[cho])
                result.append(self.JUNGSEONG[jung])
                j = self.JONGSEONG[jong]
                if j:
                    result.append(j)
            elif 0x3131 <= code <= 0x318E:
                result.append(char)
        return "".join(result)