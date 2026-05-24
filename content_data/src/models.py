import json
import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

from src.utils.logger import logger

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
os.makedirs(DATA_DIR, exist_ok=True)


class DataRepository:
    """Atomic Data Repository handling interdependent JSON files."""

    def __init__(self):
        self.files = {
            "words": DATA_DIR / "words.json",
            "meanings": DATA_DIR / "meanings.json",
            "sentences": DATA_DIR / "sentences.json",
            "quizzes": DATA_DIR / "quizzes.json",
        }
        self.cached_data = {}
        for key, path in self.files.items():
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    self.cached_data[key] = json.load(f)
                except json.JSONDecodeError:
                    self.cached_data[key] = []
                    logger.warning(
                        f"{key}.json was invalid or empty. Initialized to empty list."
                    )

    def get_all(self, collection: str):
        """Returns the list representing the given collection."""
        return self.cached_data.get(collection, [])

    def save_all(self):
        """Atomically saves all cached collections to disk, replacing original files safely."""
        tmp_files = {}
        for key, path in self.files.items():
            tmp_path = path.with_suffix(".json.tmp")
            tmp_files[key] = tmp_path
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.cached_data[key], f, ensure_ascii=False, indent=2)

        for key, path in self.files.items():
            tmp_path = tmp_files[key]
            if tmp_path.exists():
                tmp_path.replace(path)
        logger.info("JSON data saved atomically.")


class Word(BaseModel):
    word: str


class Meaning(BaseModel):
    id: str
    word: str
    definition: str


class Sentence(BaseModel):
    id: str
    meaning_id: str
    content: str
    highlight: str


class QuizChoice(BaseModel):
    choice_id: str
    text: str
    meaning_id: str


class Quiz(BaseModel):
    card_id: str
    meaning_id: str
    polysemy_word: str
    prompt_sentence: str
    choices: List[QuizChoice]
    correct_choice_id: str
    pronunciation_target: str
    image_url: str
    card_order: int
    set_id: str
