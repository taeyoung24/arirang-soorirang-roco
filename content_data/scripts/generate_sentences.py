# 실행 명령어: uv run -m scripts.generate_sentences --meaning-id <meaning_id>
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Generate sentences from meanings")
    parser.add_argument("--meaning-id", required=True, help="Meaning ID")
    args = parser.parse_args()

    pass

if __name__ == "__main__":
    main()
