# Original MDD Image Runtime Notes

Source image: `nia-13-nonnative-speech:sjr_mdd_231011_v2`

These notes were extracted from the restored local image to rebuild a closer equivalent on top of an official CUDA base.

## Key runtime facts

- Python: `3.9.12`
- Python executable: `/opt/conda/envs/main/bin/python`
- Conda env: `/opt/conda/envs/main`
- `sox`: `/usr/bin/sox`
- `fairseq`: editable install from commit `a075481d0de112aee2d79f40ac3ab0eca37214d8`
- `torch`: `1.10.1+cu111`
- `flashlight`: packaged as `flashlight-1.0.0-py3.9-linux-x86_64.egg`

## Important observations

- The original image does not set `PYTHONPATH` or `LD_LIBRARY_PATH` globally.
- `fairseq` lives at `/opt/fairseq`.
- `flashlight` is present as an egg directory under the conda env site-packages path.
- The original image was built around a conda environment, not a plain system Python install.

## Extracted environment inputs

- `pip freeze` from the original image is represented in `requirements.inference.runtime.txt`.
- Service-only additions in the rebuilt image still include FastAPI and Korean text-processing packages that were layered on later in this repo.
