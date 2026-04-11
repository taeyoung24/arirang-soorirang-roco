from typing import List
from pydantic import BaseModel, Field

class Word(BaseModel):
    id: int
    word: str

class Meaning(BaseModel):
    id: int
    word_id: int
    definition: str

class Sentence(BaseModel):
    id: int
    meaning_id: int
    content: str
    highlight: str

class Quiz(BaseModel):
    id: int
    instruction: str
    target_id: int
    option_ids: List[int]
