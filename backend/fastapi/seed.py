import json
from pathlib import Path
from collections import defaultdict

from database import Base, SessionLocal, engine
from db_models import (
    CategoryDB,
    LearningSetDB,
    MeaningDB,
    QuizChoiceDB,
    QuizDB,
    RecentLearningRecordDB,
    SentenceDB,
    WordDB,
)
from tts_client import generate_tts_url

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "content_data" / "data"
SENTENCE_IMAGE_DIR = BASE_DIR / "frontend" / "public" / "sentence_images"

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
    "set_test_01": "일상 회화",
}

SET_THUMBNAIL_MAPPING = {
    "set_school_01": "word-image-write.png",
    "set_hospital_01": "word-image-write.png",
    "set_bank_01": "word-image-snow.png",
    "set_hanging_with_01": "word-image-snow.png",
    "set_cafe_01": "word-image-snow.png",
    "set_pc_game_01": "word-image-snow.png",
    "set_university_01": "word-image-snow.png",
    "set_test_01": "word-image-snow.png",
}

WORD_TO_SET = {
    "쓰다": "set_school_01",
    "눈": "set_test_01",
}

WORD_IMAGE_MAPPING = {
    "쓰다": "/assets/cards/bird-write.png",
    "눈": "/assets/cards/placeholder.png",
}

SENTENCE_IMAGE_BASE_URL = "/sentence_images"


def build_sentence_image_url(sentence_id):
    if not sentence_id:
        return None
    image_path = SENTENCE_IMAGE_DIR / f"{sentence_id}.png"
    if not image_path.exists():
        return None
    return f"{SENTENCE_IMAGE_BASE_URL}/{sentence_id}.png"


def load_json(filename):
    path = DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_tables():
    Base.metadata.create_all(bind=engine)


def validate_content_references(meanings, sentences, quiz_overrides):
    meaning_ids = {item.get("id") for item in meanings if item.get("id")}
    missing_sentence_refs = [
        (item.get("id"), item.get("meaning_id"), item.get("content"))
        for item in sentences
        if item.get("meaning_id") not in meaning_ids
    ]
    missing_quiz_refs = [
        (item.get("card_id"), item.get("meaning_id"), item.get("prompt_sentence"))
        for item in quiz_overrides
        if item.get("meaning_id") and item.get("meaning_id") not in meaning_ids
    ]

    if missing_sentence_refs or missing_quiz_refs:
        details = []
        if missing_sentence_refs:
            preview = ", ".join(
                f"sentence_id={sentence_id} meaning_id={meaning_id} content={content!r}"
                for sentence_id, meaning_id, content in missing_sentence_refs[:5]
            )
            details.append(f"sentences.json has missing meaning refs: {preview}")
        if missing_quiz_refs:
            preview = ", ".join(
                f"card_id={card_id} meaning_id={meaning_id} prompt={prompt!r}"
                for card_id, meaning_id, prompt in missing_quiz_refs[:5]
            )
            details.append(f"quizzes.json has missing meaning refs: {preview}")
        raise ValueError("Invalid content_data references. " + " ".join(details))


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
        thumbnail_url = SET_THUMBNAIL_MAPPING.get(set_id)
        if learning_set is None:
            session.add(
                LearningSetDB(
                    set_id=set_id,
                    title=SET_TITLE.get(set_id, "정보 없음"),
                    category_id=category_id,
                    thumbnail_url=thumbnail_url,
                )
            )
        else:
            learning_set.title = SET_TITLE.get(set_id, learning_set.title)
            learning_set.category_id = category_id
            learning_set.thumbnail_url = thumbnail_url


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
                    tts_url=item.get("tts_url"),
                )
            )
        else:
            sentence.meaning_id = item.get("meaning_id", sentence.meaning_id)
            sentence.content = item.get("content", sentence.content)
            sentence.highlight = item.get("highlight", sentence.highlight)
            if item.get("tts_url"):
                sentence.tts_url = item.get("tts_url")


def build_quizzes_from_sentences(meanings, sentences, quiz_overrides):
    meanings_by_id = {item.get("id"): item for item in meanings if item.get("id")}
    sentences_by_meaning = defaultdict(list)
    meanings_by_word = defaultdict(list)
    overrides_by_meaning = {}
    overrides_by_card_id = {}
    overrides_by_prompt = {}

    for meaning in meanings_by_id.values():
        meanings_by_word[meaning.get("word", "")].append(meaning)

    for sentence in sentences:
        meaning_id = sentence.get("meaning_id")
        if meaning_id in meanings_by_id:
            sentences_by_meaning[meaning_id].append(sentence)

    for item in quiz_overrides:
        if item.get("meaning_id") and item.get("meaning_id") not in overrides_by_meaning:
            overrides_by_meaning[item["meaning_id"]] = item
        if item.get("card_id"):
            overrides_by_card_id[item["card_id"]] = item
        if item.get("meaning_id") and item.get("prompt_sentence"):
            overrides_by_prompt[(item["meaning_id"], item["prompt_sentence"])] = item

    generated = []
    card_order_by_set = defaultdict(int)

    for prompt in sentences:
        prompt_id = prompt.get("id")
        meaning_id = prompt.get("meaning_id")
        meaning = meanings_by_id.get(meaning_id)
        if not prompt_id or not meaning:
            continue

        word = meaning.get("word", "")
        correct_pool = [
            sentence
            for sentence in sentences_by_meaning[meaning_id]
            if sentence.get("id") != prompt_id
        ]
        if not correct_pool:
            continue

        distractors = []
        for other_meaning in meanings_by_word[word]:
            other_meaning_id = other_meaning.get("id")
            if other_meaning_id == meaning_id:
                continue
            other_sentences = sentences_by_meaning.get(other_meaning_id, [])
            if other_sentences:
                distractors.append(other_sentences[0])

        if len(distractors) < 3:
            continue

        prompt_override = overrides_by_prompt.get((meaning_id, prompt.get("content", "")), {})
        card_id = prompt_override.get("card_id") or f"card_{prompt_id}"
        meaning_override = overrides_by_meaning.get(meaning_id, {})
        card_override = overrides_by_card_id.get(card_id, {})
        override = {**meaning_override, **prompt_override, **card_override}
        set_id = override.get("set_id") or WORD_TO_SET.get(word, "set_test_01")

        card_order_by_set[set_id] += 1
        choices = [correct_pool[0], *distractors[:3]]
        pronunciation_target = correct_pool[0].get("content", "")

        generated.append(
            {
                "card_id": card_id,
                "sentence_id": prompt_id,
                "meaning_id": meaning_id,
                "polysemy_word": word,
                "prompt_sentence": prompt.get("content", ""),
                "choices": [
                    {
                        "choice_id": f"c{index}",
                        "text": choice.get("content", ""),
                        "meaning_id": choice.get("meaning_id", ""),
                    }
                    for index, choice in enumerate(choices, start=1)
                ],
                "correct_choice_id": "c1",
                "pronunciation_target": pronunciation_target,
                "tts_url": correct_pool[0].get("tts_url"),
                "image_url": build_sentence_image_url(prompt_id)
                or override.get("image_url")
                or WORD_IMAGE_MAPPING.get(word, "/assets/cards/placeholder.png"),
                "card_order": card_order_by_set[set_id],
                "set_id": set_id,
            }
        )

    return generated


def seed_quizzes(session, quizzes):
    desired_card_ids = {item.get("card_id") for item in quizzes if item.get("card_id")}
    if desired_card_ids:
        existing_quizzes = session.query(QuizDB).all()
        stale_card_ids = [
            quiz.card_id for quiz in existing_quizzes if quiz.card_id not in desired_card_ids
        ]
        if stale_card_ids:
            (
                session.query(RecentLearningRecordDB)
                .filter(RecentLearningRecordDB.card_id.in_(stale_card_ids))
                .delete(synchronize_session=False)
            )
        for quiz in existing_quizzes:
            if quiz.card_id in stale_card_ids:
                session.delete(quiz)
        session.flush()

    for item in quizzes:
        card_id = item.get("card_id")
        if not card_id:
            continue

        quiz = session.get(QuizDB, card_id)
        target_text = item.get("pronunciation_target", "")
        target_changed = quiz is not None and quiz.pronunciation_target != target_text
        if not item.get("tts_url") and (quiz is None or not quiz.tts_url or target_changed):
            tts_url = generate_tts_url(target_text)
            if tts_url:
                item["tts_url"] = tts_url

        if quiz is None:
            quiz = QuizDB(
                card_id=card_id,
                sentence_id=item.get("sentence_id"),
                meaning_id=item.get("meaning_id", ""),
                polysemy_word=item.get("polysemy_word", ""),
                prompt_sentence=item.get("prompt_sentence", ""),
                pronunciation_target=item.get("pronunciation_target", ""),
                tts_url=item.get("tts_url"),
                image_url=item.get("image_url", ""),
                card_order=item.get("card_order", 0),
                set_id=item.get("set_id", ""),
            )
            session.add(quiz)
        else:
            quiz.sentence_id = item.get("sentence_id", quiz.sentence_id)
            quiz.meaning_id = item.get("meaning_id", quiz.meaning_id)
            quiz.polysemy_word = item.get("polysemy_word", quiz.polysemy_word)
            quiz.prompt_sentence = item.get("prompt_sentence", quiz.prompt_sentence)
            quiz.pronunciation_target = item.get(
                "pronunciation_target", quiz.pronunciation_target
            )
            if item.get("tts_url") or target_changed:
                quiz.tts_url = item.get("tts_url")
            quiz.image_url = item.get("image_url", quiz.image_url)
            quiz.card_order = item.get("card_order", quiz.card_order)
            quiz.set_id = item.get("set_id", quiz.set_id)

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
            else:
                existing_choice.text = choice_data.get("text", existing_choice.text)
                existing_choice.meaning_id = choice_data.get(
                    "meaning_id", existing_choice.meaning_id
                )
                existing_choice.is_correct = choice_id == item.get("correct_choice_id")


def main():
    create_tables()
    words = load_json("words.json")
    meanings = load_json("meanings.json")
    sentences = load_json("sentences.json")
    quiz_overrides = load_json("quizzes.json")
    validate_content_references(meanings, sentences, quiz_overrides)
    quizzes = build_quizzes_from_sentences(meanings, sentences, quiz_overrides)

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
