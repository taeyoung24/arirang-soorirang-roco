from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import Settings
from app.pipeline import MDDPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the original MDD model on a single utterance.")
    parser.add_argument("audio", type=Path, help="Input audio path")
    parser.add_argument("script", help="Original Korean script")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.audio.exists():
        print(f"Audio file not found: {args.audio}")
        return 1

    pipeline = MDDPipeline(Settings.from_env())
    result = pipeline.predict(
        audio_bytes=args.audio.read_bytes(),
        original_filename=args.audio.name,
        script=args.script,
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
