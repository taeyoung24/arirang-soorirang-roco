from __future__ import annotations

import ast
import sys
import threading
from pathlib import Path


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

    def predict_units(self, manifest_dir: Path) -> str:
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

                prefix_tokens = None
                if self._args.prefix_size > 0:
                    prefix_tokens = sample["target"][:, : self._args.prefix_size]

                hypos = self._task.inference_step(self._generator, self._models, sample, prefix_tokens)
                if not hypos or not hypos[0]:
                    raise RuntimeError("Fairseq returned no hypotheses.")
                return self._tgt_dict.string(hypos[0][0]["tokens"].int().cpu())

        raise RuntimeError("No valid sample was produced for inference.")
