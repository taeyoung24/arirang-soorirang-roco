import json
from pathlib import Path

from database import Base, SessionLocal, engine
from db_models import (
    CategoryDB,
    LearningSetDB,
    MeaningDB,
    QuizChoiceDB,
    QuizDB,
    SentenceDB,
    WordDB,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "content_data" / "data"

CATEGORY_INFO = {
    "school": {"name_ko": "고등학교", "name_en": "High school"},
    "hospital": {"name_ko": "병원", "name_en": "Hospital"},
    "bank": {"name_ko": "은행", "name_en": "Bank"},
    "hanging_with": {"name_ko": "친구와 놀기", "name_en": "Hanging with"},
    "cafe": {"name_ko": "카페", "name_en": "Cafe"},
    "pc_game": {"name_ko": "PC 게임", "name_en": "Video games"},
    "university": {"name_ko": "대학교", "name_en": "University"},
}

SET_TO_CATEGORY = {
    "set_school_01": "school",
    "set_hospital_01": "hospital",
    "set_bank_01": "bank",
    "set_hanging_with_01": "hanging_with",
    "set_cafe_01": "cafe",
    "set_pc_game_01": "pc_game",
    "set_university_01": "university",
    "set_test_01": "school",
}

SET_TITLE = {
    "set_school_01": "고등학교",
    "set_hospital_01": "병원",
    "set_bank_01": "은행",
    "set_hanging_with_01": "친구와 놀기",
    "set_cafe_01": "카페",
    "set_pc_game_01": "PC 게임",
    "set_university_01": "대학교",
    "set_test_01": "테스트",
}

SET_THUMBNAIL_MAPPING = {
    "set_school_01": "/assets/categories/school.png",
    "set_hospital_01": "/assets/categories/hospital.png",
    "set_bank_01": "/assets/categories/bank.png",
    "set_hanging_with_01": "/assets/cards/placeholder.png",
    "set_cafe_01": "/assets/cards/placeholder.png",
    "set_pc_game_01": "/assets/cards/placeholder.png",
    "set_university_01": "/assets/cards/placeholder.png",
    "set_test_01": "/assets/cards/placeholder.png",
}


def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_categories(session):
    for category_id, meta in CATEGORY_INFO.items():
        category = session.get(CategoryDB, category_id)
        if category is None:
            session.add(
                CategoryDB(
                    category_id=category_id,
                    name_ko=meta["name_ko"],
                    name_en=meta["name_en"],
                )
            )


def seed_learning_sets(session):
    for set_id, category_id in SET_TO_CATEGORY.items():
        learning_set = session.get(LearningSetDB, set_id)
        if learning_set is None:
            session.add(
                LearningSetDB(
                    set_id=set_id,
                    title=SET_TITLE.get(set_id, "정보 없음"),
                    category_id=category_id,
                    thumbnail_url=SET_THUMBNAIL_MAPPING.get(set_id),
                )
            )


def seed_words(session, words):
    for item in words:
        word_text = item.get("word")
        if not word_text:
            continue
        existing = session.query(WordDB).filter_by(word=word_text).one_or_none()
        if existing is None:
            session.add(WordDB(word=word_text))


def seed_meanings(session, meanings):
    for item in meanings:
        meaning_id = item.get("id")
        if not meaning_id:
            continue
        meaning = session.get(MeaningDB, meaning_id)
        if meaning is None:
            session.add(
                MeaningDB(
                    meaning_id=meaning_id,
                    word=item.get("word", ""),
                    definition=item.get("definition", ""),
                )
            )


def seed_sentences(session, sentences):
    for item in sentences:
        sentence_id = item.get("id")
        if not sentence_id:
            continue
        sentence = session.get(SentenceDB, sentence_id)
        if sentence is None:
            session.add(
                SentenceDB(
                    sentence_id=sentence_id,
                    meaning_id=item.get("meaning_id", ""),
                    content=item.get("content", ""),
                    highlight=item.get("highlight", ""),
                )
            )


def seed_quizzes(session, quizzes):
    for item in quizzes:
        card_id = item.get("card_id")
        if not card_id:
            continue

        quiz = session.get(QuizDB, card_id)
        if quiz is None:
            quiz = QuizDB(
                card_id=card_id,
                meaning_id=item.get("meaning_id", ""),
                polysemy_word=item.get("polysemy_word", ""),
                prompt_sentence=item.get("prompt_sentence", ""),
                pronunciation_target=item.get("pronunciation_target", ""),
                image_url=item.get("image_url", ""),
                card_order=item.get("card_order", 0),
                set_id=item.get("set_id", ""),
            )
            session.add(quiz)

        for choice_data in item.get("choices", []):
            choice_id = choice_data.get("choice_id")
            if not choice_id:
                continue
            existing_choice = (
                session.query(QuizChoiceDB)
                .filter_by(card_id=card_id, choice_id=choice_id)
                .one_or_none()
            )
            if existing_choice is None:
                session.add(
                    QuizChoiceDB(
                        card_id=card_id,
                        choice_id=choice_id,
                        text=choice_data.get("text", ""),
                        meaning_id=choice_data.get("meaning_id", ""),
                        is_correct=choice_id == item.get("correct_choice_id"),
                    )
                )


def main():
    create_tables()
    words = load_json("words.json")
    meanings = load_json("meanings.json")
    sentences = load_json("sentences.json")
    quizzes = load_json("quizzes.json")

    with SessionLocal() as session:
        seed_categories(session)
        seed_learning_sets(session)
        seed_words(session, words)
        seed_meanings(session, meanings)
        seed_sentences(session, sentences)
        seed_quizzes(session, quizzes)
        session.commit()

    print("Seed 완료: PostgreSQL 데이터베이스에 콘텐츠가 채워졌습니다.")


if __name__ == "__main__":
    main()
