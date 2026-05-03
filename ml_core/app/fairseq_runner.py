from __future__ import annotations

import ast
import sys
import threading
from pathlib import Path

from app.inference_backend import InferenceResult
from app.schemas import PredictedPhonemeScore, TargetPhonemeScore


class FairseqInferenceRunner:
    def __init__(self, model_path: str, infer_script_path: str, max_tokens: int):
        from fairseq import checkpoint_utils, options, tasks, utils
        from fairseq.utils import apply_to_sample, move_to_cuda
        import torch

        infer_module = self._load_infer_module(infer_script_path)
        parser = options.get_generation_parser()
        parser = infer_module.add_asr_eval_argument(parser)
        args = options.parse_args_and_arch(
            parser,
            input_args=[
                "__BOOTSTRAP__",
                "--task",
                "audio_finetuning",
                "--nbest",
                "1",
                "--path",
                model_path,
                "--gen-subset",
                "test",
                "--w2l-decoder",
                "viterbi",
                "--criterion",
                "ctc",
                "--quiet",
                "--max-tokens",
                str(max_tokens),
            ],
        )

        self._apply_to_sample = apply_to_sample
        self._move_to_cuda = move_to_cuda
        self._args = args
        self._use_cuda = torch.cuda.is_available() and not args.cpu
        self._lock = threading.Lock()

        self._task = tasks.setup_task(args)
        self._models, self._saved_cfg, self._task = checkpoint_utils.load_model_ensemble_and_task(
            utils.split_paths(args.path, separator="\\"),
            arg_overrides=ast.literal_eval(args.model_overrides),
            task=self._task,
            suffix=args.checkpoint_suffix,
            strict=(args.checkpoint_shard_count == 1),
            num_shards=args.checkpoint_shard_count,
        )
        infer_module.optimize_models(args, self._use_cuda, self._models)
        self._tgt_dict = self._task.target_dictionary
        self._generator = self._build_generator(args, self._tgt_dict)

    @staticmethod
    def _load_infer_module(infer_script_path: str):
        import importlib.util

        infer_path = Path(infer_script_path)
        spec = importlib.util.spec_from_file_location("mdd_fairseq_infer", infer_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load fairseq infer module from {infer_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _build_generator(args, target_dictionary):
        w2l_decoder = getattr(args, "w2l_decoder", None)
        if w2l_decoder == "viterbi":
            from examples.speech_recognition.w2l_decoder import W2lViterbiDecoder

            return W2lViterbiDecoder(args, target_dictionary)
        if w2l_decoder == "kenlm":
            from examples.speech_recognition.w2l_decoder import W2lKenLMDecoder

            return W2lKenLMDecoder(args, target_dictionary)
        if w2l_decoder == "fairseqlm":
            from examples.speech_recognition.w2l_decoder import W2lFairseqLMDecoder

            return W2lFairseqLMDecoder(args, target_dictionary)
        raise RuntimeError(f"Unsupported decoder: {w2l_decoder}")

    def predict_units(self, manifest_dir: Path) -> InferenceResult:
        import torch

        with self._lock:
            self._args.data = str(manifest_dir)
            if hasattr(self._task, "cfg") and hasattr(self._task.cfg, "data"):
                self._task.cfg.data = str(manifest_dir)
            if hasattr(self._saved_cfg, "task") and hasattr(self._saved_cfg.task, "data"):
                self._saved_cfg.task.data = str(manifest_dir)
            self._task.load_dataset(self._args.gen_subset, task_cfg=self._saved_cfg.task)
            iterator = self._task.get_batch_iterator(
                dataset=self._task.dataset(self._args.gen_subset),
                max_tokens=self._args.max_tokens,
                max_sentences=self._args.batch_size,
                max_positions=(sys.maxsize, sys.maxsize),
                ignore_invalid_inputs=self._args.skip_invalid_size_inputs_valid_test,
                required_batch_size_multiple=self._args.required_batch_size_multiple,
                num_shards=self._args.num_shards,
                shard_id=self._args.shard_id,
                num_workers=self._args.num_workers,
                data_buffer_size=self._args.data_buffer_size,
            ).next_epoch_itr(shuffle=False)

            for sample in iterator:
                if self._use_cuda:
                    sample = self._move_to_cuda(sample)
                if self._args.fp16:
                    sample = self._apply_to_sample(
                        lambda t: t.to(dtype=torch.half) if t.dtype is torch.float32 else t,
                        sample,
                    )
                if "net_input" not in sample:
                    continue

                encoder_input = {
                    key: value
                    for key, value in sample["net_input"].items()
                    if key != "prev_output_tokens"
                }
                emissions = self._generator.get_emissions(self._models, encoder_input)
                hypos = self._generator.decode(emissions)
                if not hypos or not hypos[0]:
                    raise RuntimeError("Fairseq returned no hypotheses.")
                hypo = hypos[0][0]
                tokens = hypo["tokens"].int().cpu()
                decoder_score = self._score_to_float(hypo.get("score"))
                predicted_scores = self._predicted_phoneme_scores(emissions[0])
                canonical_units = self._read_canonical_units(manifest_dir)
                target_scores = self._target_phoneme_scores(canonical_units, predicted_scores, emissions[0])
                return InferenceResult(
                    raw_line=self._tgt_dict.string(tokens),
                    decoder_score=decoder_score,
                    token_count=int(tokens.numel()),
                    score_source="fairseq_hypothesis_score" if decoder_score is not None else None,
                    predicted_phoneme_scores=predicted_scores,
                    target_phoneme_scores=target_scores,
                )

        raise RuntimeError("No valid sample was produced for inference.")

    @staticmethod
    def _score_to_float(value) -> float | None:
        if value is None:
            return None
        if hasattr(value, "item"):
            return float(value.item())
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _predicted_phoneme_scores(self, emissions) -> list[PredictedPhonemeScore]:
        import torch

        probabilities = torch.softmax(emissions.float(), dim=-1)
        path = torch.argmax(emissions, dim=-1).int().cpu().tolist()
        blank = int(self._generator.blank)
        scores: list[PredictedPhonemeScore] = []
        cursor = 0
        predicted_index = 0
        while cursor < len(path):
            token_id = path[cursor]
            start = cursor
            while cursor < len(path) and path[cursor] == token_id:
                cursor += 1
            end = cursor
            if token_id == blank:
                continue
            frame_probs = probabilities[start:end, token_id]
            confidence = round(float(frame_probs.mean().item()), 4) if len(frame_probs) else 0.0
            scores.append(
                PredictedPhonemeScore(
                    phoneme=self._token_to_string(token_id),
                    predicted_index=predicted_index,
                    confidence=max(0.0, min(1.0, confidence)),
                    frame_start=start,
                    frame_end=end,
                    frame_count=end - start,
                )
            )
            predicted_index += 1
        return scores

    def _token_to_string(self, token_id: int) -> str:
        import torch

        return self._tgt_dict.string(torch.LongTensor([token_id])).replace(" ", "")

    @staticmethod
    def _read_canonical_units(manifest_dir: Path) -> list[str]:
        phn_path = manifest_dir / "test.phn"
        if not phn_path.exists():
            return []
        text = phn_path.read_text(encoding="utf-8").replace("|", "").strip()
        return [unit for unit in text.split() if unit]

    def _target_phoneme_scores(
        self,
        canonical_units: list[str],
        predicted_scores: list[PredictedPhonemeScore],
        emissions,
    ) -> list[TargetPhonemeScore]:
        import math
        import torch

        predicted_units = [score.phoneme for score in predicted_scores]
        pairs = self._align_units(canonical_units, predicted_units)
        probabilities = torch.softmax(emissions.float(), dim=-1)
        result: list[TargetPhonemeScore] = []
        for edit_type, expected, actual, expected_index, actual_index in pairs:
            if expected is None or expected_index is None:
                continue
            predicted_score = predicted_scores[actual_index] if actual_index is not None and actual_index < len(predicted_scores) else None
            if predicted_score is None:
                result.append(
                    TargetPhonemeScore(
                        phoneme=expected,
                        canonical_index=expected_index,
                        edit_type="deletion",
                        note="No predicted frame segment was aligned to this target phoneme.",
                    )
                )
                continue
            target_id = self._tgt_dict.index(expected)
            start = predicted_score.frame_start
            end = max(start + 1, predicted_score.frame_end)
            frame_probs = probabilities[start:end]
            target_posterior = float(frame_probs[:, target_id].mean().item()) if target_id >= 0 else 0.0
            competing = self._competing_posterior(frame_probs, target_id)
            gop_like = math.log(max(target_posterior, 1e-8)) - math.log(max(competing, 1e-8))
            result.append(
                TargetPhonemeScore(
                    phoneme=expected,
                    canonical_index=expected_index,
                    edit_type=edit_type,
                    predicted_phoneme=actual,
                    predicted_index=actual_index,
                    target_posterior=round(max(0.0, min(1.0, target_posterior)), 4),
                    competing_posterior=round(max(0.0, min(1.0, competing)), 4),
                    gop_like_score=round(gop_like, 4),
                    confidence=predicted_score.confidence,
                    note="GOP-like log posterior ratio over the aligned predicted Viterbi segment.",
                )
            )
        return result

    def _competing_posterior(self, frame_probs, target_id: int) -> float:
        import torch

        masked = frame_probs.clone()
        if 0 <= target_id < masked.size(1):
            masked[:, target_id] = 0.0
        blank = int(self._generator.blank)
        if 0 <= blank < masked.size(1):
            masked[:, blank] = 0.0
        return float(torch.max(masked, dim=-1).values.mean().item())

    @staticmethod
    def _align_units(
        canonical: list[str],
        predicted: list[str],
    ) -> list[tuple[str, str | None, str | None, int | None, int | None]]:
        rows = len(canonical) + 1
        cols = len(predicted) + 1
        dp = [[0] * cols for _ in range(rows)]
        back = [[""] * cols for _ in range(rows)]
        for i in range(1, rows):
            dp[i][0] = i
            back[i][0] = "delete"
        for j in range(1, cols):
            dp[0][j] = j
            back[0][j] = "insert"
        for i in range(1, rows):
            for j in range(1, cols):
                replace_cost = 0 if canonical[i - 1] == predicted[j - 1] else 2
                choices = [
                    (dp[i - 1][j - 1] + replace_cost, "match" if replace_cost == 0 else "substitution"),
                    (dp[i - 1][j] + 1, "deletion"),
                    (dp[i][j - 1] + 1, "insertion"),
                ]
                dp[i][j], back[i][j] = min(choices, key=lambda item: item[0])
        pairs = []
        i = len(canonical)
        j = len(predicted)
        while i > 0 or j > 0:
            if i == 0:
                pairs.append(("insertion", None, predicted[j - 1], None, j - 1))
                j -= 1
                continue
            if j == 0:
                pairs.append(("deletion", canonical[i - 1], None, i - 1, None))
                i -= 1
                continue
            op = back[i][j]
            if op in {"match", "substitution"}:
                pairs.append((op, canonical[i - 1], predicted[j - 1], i - 1, j - 1))
                i -= 1
                j -= 1
            elif op == "deletion":
                pairs.append((op, canonical[i - 1], None, i - 1, None))
                i -= 1
            else:
                pairs.append((op, None, predicted[j - 1], None, j - 1))
                j -= 1
        pairs.reverse()
        return pairs
