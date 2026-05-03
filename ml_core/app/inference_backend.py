from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class InferenceResult:
    raw_line: str
    decoder_score: float | None = None
    token_count: int | None = None
    score_source: str | None = None


class InferenceBackend(Protocol):
    def predict(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        ...


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
