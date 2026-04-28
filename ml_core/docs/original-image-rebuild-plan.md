# Original Image Rebuild Plan

Goal: rebuild `nia-13-nonnative-speech:sjr_mdd_231011_v2` on top of an official CUDA base without losing inference quality.

## Inputs

- Model checkpoint: `ml_core/models/checkpoint_mdd_sjr.pt`
- Original local image tar
- Runtime dump from `scripts/extract-original-runtime.ps1`

## Process

1. Restore the original image from tar and keep it as the quality baseline.
2. Run `extract-original-runtime.ps1` to dump the original runtime into `docs/original-image-dump/`.
3. Rebuild the environment on an official `nvidia/cuda` base:
   - conda env layout
   - Python version
   - `fairseq` commit
   - `flashlight` binary layout
   - core Python packages
4. Compare outputs for the same audio/script pair:
   - `raw_hypothesis_line`
   - `predicted_phonemes`
   - aggregate summary
5. Only after output parity is stable, trim non-essential packages.

## Current constraints

- The original `pip freeze` contains packages that are not directly reinstallable.
- Service-layer packages added in this repo can conflict with the original image lockfile.
- The practical target is not byte-identical reproduction, but stable inference parity.
