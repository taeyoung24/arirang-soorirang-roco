from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class CategoryDB(Base):
    __tablename__ = "categories"

    category_id = Column(String, primary_key=True, index=True)
    name_ko = Column(String, nullable=False)
    name_en = Column(String, nullable=False)

    learning_sets = relationship("LearningSetDB", back_populates="category")


class LearningSetDB(Base):
    __tablename__ = "learning_sets"

    set_id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category_id = Column(
        String, ForeignKey("categories.category_id"), nullable=False, index=True
    )
    thumbnail_url = Column(String, nullable=True)

    category = relationship("CategoryDB", back_populates="learning_sets")
    quizzes = relationship("QuizDB", back_populates="learning_set")


class WordDB(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String, unique=True, nullable=False, index=True)


class MeaningDB(Base):
    __tablename__ = "meanings"

    meaning_id = Column(String, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True)
    definition = Column(Text, nullable=True)

    sentences = relationship("SentenceDB", back_populates="meaning")
    quizzes = relationship("QuizDB", back_populates="meaning")


class SentenceDB(Base):
    __tablename__ = "sentences"

    sentence_id = Column(String, primary_key=True, index=True)
    meaning_id = Column(
        String, ForeignKey("meanings.meaning_id"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    highlight = Column(String, nullable=True)

    meaning = relationship("MeaningDB", back_populates="sentences")


class QuizDB(Base):
    __tablename__ = "quizzes"

    card_id = Column(String, primary_key=True, index=True)
    meaning_id = Column(
        String, ForeignKey("meanings.meaning_id"), nullable=False, index=True
    )
    polysemy_word = Column(String, nullable=False)
    prompt_sentence = Column(Text, nullable=False)
    pronunciation_target = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    card_order = Column(Integer, nullable=False)
    set_id = Column(
        String, ForeignKey("learning_sets.set_id"), nullable=False, index=True
    )

    meaning = relationship("MeaningDB", back_populates="quizzes")
    learning_set = relationship("LearningSetDB", back_populates="quizzes")
    choices = relationship(
        "QuizChoiceDB", back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizChoiceDB(Base):
    __tablename__ = "quiz_choices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String, ForeignKey("quizzes.card_id"), nullable=False, index=True)
    choice_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    meaning_id = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    quiz = relationship("QuizDB", back_populates="choices")
