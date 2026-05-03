from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import Levenshtein
import soundfile
from g2pk2 import G2p

from app.config import Settings
from app.inference_backend import InferenceBackend, InferenceResult, SubprocessInferenceBackend
from app.schemas import ModelScoreSummary, PredictResponse, PronunciationIssue, Summary


class MDDInferenceError(RuntimeError):
    pass


class MDDPipeline:
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

    def __init__(self, settings: Settings, inference_backend: Optional[InferenceBackend] = None):
        self.settings = settings
        self.g2p = G2p()
        self.inference_backend = inference_backend or SubprocessInferenceBackend(settings)
        Path(self.settings.temp_root).mkdir(parents=True, exist_ok=True)

    @classmethod
    def decompose_hangul(cls, text: str) -> str:
        result: list[str] = []
        for char in text:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:
                syllable_index = code - 0xAC00
                choseong_index = syllable_index // 588
                jungseong_index = (syllable_index % 588) // 28
                jongseong_index = syllable_index % 28
                result.append(cls.CHOSEONG[choseong_index])
                result.append(cls.JUNGSEONG[jungseong_index])
                jong = cls.JONGSEONG[jongseong_index]
                if jong:
                    result.append(jong)
            else:
                    result.append(char)
        return "".join(result)

    @classmethod
    def decompose_hangul_for_target(cls, text: str) -> str:
        result: list[str] = []
        for char in text:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:
                syllable_index = code - 0xAC00
                choseong_index = syllable_index // 588
                jungseong_index = (syllable_index % 588) // 28
                jongseong_index = syllable_index % 28
                if cls.CHOSEONG[choseong_index] != "ㅇ":
                    result.append(cls.CHOSEONG[choseong_index])
                result.append(cls.JUNGSEONG[jungseong_index])
                jong = cls.JONGSEONG[jongseong_index]
                if jong:
                    result.append(jong)
            else:
                result.append(char)
        return "".join(result)

    @classmethod
    def compose_jamo(cls, phonemes: str) -> str:
        result: list[str] = []
        i = 0
        while i < len(phonemes):
            current = phonemes[i]
            if current not in cls.CHOSEONG or i + 1 >= len(phonemes) or phonemes[i + 1] not in cls.JUNGSEONG:
                result.append(current)
                i += 1
                continue

            choseong_index = cls.CHOSEONG.index(current)
            jungseong_index = cls.JUNGSEONG.index(phonemes[i + 1])
            jongseong_index = 0
            step = 2

            if i + 2 < len(phonemes) and phonemes[i + 2] in cls.JONGSEONG[1:]:
                next_is_vowel = i + 3 < len(phonemes) and phonemes[i + 3] in cls.JUNGSEONG
                if not next_is_vowel:
                    jongseong_index = cls.JONGSEONG.index(phonemes[i + 2])
                    step = 3

            syllable = chr(0xAC00 + (choseong_index * 588) + (jungseong_index * 28) + jongseong_index)
            result.append(syllable)
            i += step

        return "".join(result)

    @classmethod
    def normalize_canonical_phonemes(cls, raw_value: str) -> str:
        normalized = re.sub(r"\s+", "", raw_value.strip())
        normalized = "".join(char for char in normalized if cls._is_korean_or_jamo(char))
        if not normalized:
            raise ValueError("canonical_phonemes must not be empty.")
        return cls.decompose_hangul_for_target(normalized)

    @staticmethod
    def _is_korean_or_jamo(char: str) -> bool:
        code = ord(char)
        return 0xAC00 <= code <= 0xD7A3 or 0x3131 <= code <= 0x318E

    def script_to_canonical_phonemes(self, script: str) -> str:
        normalized_script = re.sub(r"\s+", " ", script.strip())
        if not normalized_script:
            raise ValueError("script must not be empty.")
        g2p_text = self.g2p(normalized_script)
        return self.normalize_canonical_phonemes(g2p_text)

    @staticmethod
    def phoneme_to_label_line(phonemes: str) -> str:
        return " ".join(list(phonemes)) + " |\n"

    def _build_workdir(self) -> Path:
        request_id = uuid.uuid4().hex
        workdir = Path(self.settings.temp_root) / request_id
        (workdir / "sound_16k").mkdir(parents=True, exist_ok=True)
        (workdir / "manifest").mkdir(parents=True, exist_ok=True)
        (workdir / "results").mkdir(parents=True, exist_ok=True)
        return workdir

    def _convert_audio(self, src_path: Path, dst_path: Path) -> int:
        if not shutil.which("sox"):
            raise MDDInferenceError("sox executable not found.")

        command = [
            "sox",
            "-G",
            "-v",
            "0.99",
            str(src_path),
            "-c",
            "1",
            "-b",
            "16",
            "-r",
            "16000",
            str(dst_path),
        ]
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode != 0:
            raise MDDInferenceError(f"sox failed: {process.stderr.strip()}")
        return soundfile.info(dst_path).frames

    def _prepare_manifest(self, workdir: Path, file_name: str, num_frames: int, canonical_phonemes: str) -> Path:
        manifest_dir = workdir / "manifest"
        sound_dir = workdir / "sound_16k"
        (manifest_dir / "test.tsv").write_text(
            f"{sound_dir}\n{file_name}\t{num_frames}\n",
            encoding="utf-8",
        )
        (manifest_dir / "test.wrd").write_text(canonical_phonemes + "\n", encoding="utf-8")
        (manifest_dir / "test.phn").write_text(self.phoneme_to_label_line(canonical_phonemes), encoding="utf-8")
        shutil.copyfile(self.settings.dict_path, manifest_dir / "dict.phn.txt")
        return manifest_dir

    def _run_inference(self, manifest_dir: Path, results_dir: Path) -> InferenceResult:
        try:
            return self.inference_backend.predict(manifest_dir, results_dir)
        except RuntimeError as exc:
            raise MDDInferenceError(str(exc)) from exc

    @staticmethod
    def _build_model_score(result: InferenceResult, predicted: str) -> ModelScoreSummary | None:
        if result.decoder_score is None:
            return ModelScoreSummary(
                note="Decoder score is not available from the configured inference backend.",
            )
        token_count = result.token_count or len(predicted)
        normalized = result.decoder_score / max(token_count, 1)
        return ModelScoreSummary(
            decoder_score=round(result.decoder_score, 4),
            normalized_decoder_score=round(normalized, 4),
            token_count=token_count,
            score_source=result.score_source,
            note=(
                "This is a decoder hypothesis score, not calibrated phoneme-level GOP. "
                "Use it as model evidence only after backend-specific calibration."
            ),
        )

    @staticmethod
    def _parse_prediction(raw_line: str) -> str:
        if "(None-" in raw_line:
            raw_line = raw_line.split("(None-", 1)[0]
        predicted = raw_line.replace("|", "").replace(" ", "").strip()
        if not predicted:
            raise MDDInferenceError("Predicted phoneme sequence is empty.")
        return predicted

    @staticmethod
    def _build_issues(canonical: str, predicted: str) -> tuple[list[PronunciationIssue], Summary]:
        edits = Levenshtein.editops(canonical, predicted)
        issues: list[PronunciationIssue] = []
        substitutions = 0
        insertions = 0
        deletions = 0

        for edit_type, canonical_index, predicted_index in edits:
            if edit_type == "replace":
                substitutions += 1
                issues.append(
                    PronunciationIssue(
                        issue_type="substitution",
                        expected=canonical[canonical_index],
                        actual=predicted[predicted_index],
                    )
                )
            elif edit_type == "insert":
                insertions += 1
                issues.append(
                    PronunciationIssue(
                        issue_type="insertion",
                        expected="",
                        actual=predicted[predicted_index],
                    )
                )
            else:
                deletions += 1
                issues.append(
                    PronunciationIssue(
                        issue_type="deletion",
                        expected=canonical[canonical_index],
                        actual="",
                    )
                )

        total_expected = max(1, len(canonical))
        summary = Summary(
            total_issues=len(issues),
            substitutions=substitutions,
            insertions=insertions,
            deletions=deletions,
            accuracy=round(max(0.0, 1.0 - (len(issues) / total_expected)), 4),
        )
        return issues, summary

    def predict(self, audio_bytes: bytes, original_filename: str, script: str) -> PredictResponse:
        normalized_script = re.sub(r"\s+", " ", script.strip())
        if not normalized_script:
            raise ValueError("script must not be empty.")
        g2p_text = self.g2p(normalized_script)
        normalized = self.normalize_canonical_phonemes(g2p_text)
        workdir = self._build_workdir()
        source_suffix = Path(original_filename or "input.wav").suffix or ".wav"
        source_path = workdir / f"input{source_suffix}"
        converted_name = "input.wav"
        converted_path = workdir / "sound_16k" / converted_name

        try:
            source_path.write_bytes(audio_bytes)
            num_frames = self._convert_audio(source_path, converted_path)
            manifest_dir = self._prepare_manifest(workdir, converted_name, num_frames, normalized)
            inference_result = self._run_inference(manifest_dir, workdir / "results")
            predicted = self._parse_prediction(inference_result.raw_line)
            issues, summary = self._build_issues(normalized, predicted)
            return PredictResponse(
                script=script,
                canonical_phonemes=normalized,
                predicted_phonemes=predicted,
                canonical_text=self.compose_jamo(normalized),
                predicted_text=self.compose_jamo(predicted),
                issues=issues,
                summary=summary,
                model_score=self._build_model_score(inference_result, predicted),
                raw_hypothesis_line=inference_result.raw_line,
            )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
