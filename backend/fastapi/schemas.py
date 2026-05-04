from typing import List, Optional
from pydantic import BaseModel


# =============================================================================
# Pydantic 모델 정의
# =============================================================================


class RecommendedSet(BaseModel):
    """
    추천 학습 세트 모델
    """

    set_id: str
    title: str
    thumbnail_url: str


class RecommendedResponse(BaseModel):
    """
    추천 학습 세트 목록 조회 Response 모델
    """

    success: bool
    data: List[RecommendedSet]
    message: Optional[str] = None


class RecentCard(BaseModel):
    """
    최근 학습 카드 모델
    """

    card_id: str
    word: str
    image_url: str
    last_viewed_at: str


class RecentResponse(BaseModel):
    """
    최근 학습 목록 조회 Response 모델
    """

    success: bool
    data: List[RecentCard]
    message: Optional[str] = None


class Category(BaseModel):
    """
    카테고리 모델
    """

    category_id: str
    name_ko: str
    name_en: str


class CategoriesResponse(BaseModel):
    """
    카테고리 목록 조회 Response 모델
    """

    success: bool
    data: List[Category]
    message: Optional[str] = None


class LearningSet(BaseModel):
    """
    학습 세트 모델
    """

    set_id: str
    title: str
    word_count: int
    words: List[str]


class CategorySetsResponse(BaseModel):
    """
    카테고리별 학습 세트 조회 Response 모델
    """

    success: bool
    data: List[LearningSet]
    message: Optional[str] = None


class Choice(BaseModel):
    """
    학습 카드 보기 모델
    """

    choice_id: str
    text: str


class LearningCard(BaseModel):
    """
    학습 카드 모델
    """

    card_id: str
    polysemy_word: str
    prompt_sentence: str
    choices: List[Choice]
    pronunciation_target: str
    image_url: str
    card_order: int


class SetCardsData(BaseModel):
    """
    학습 세트별 카드 목록 데이터 모델
    """

    set_id: str
    title: str
    cards: List[LearningCard]


class SetCardsResponse(BaseModel):
    """
    학습 카드 목록 조회 Response 모델
    """

    success: bool
    data: Optional[SetCardsData]
    message: Optional[str] = None


class AnswerSubmitRequest(BaseModel):
    """
    의미 테스트 답안 제출 Request 모델
    """

    choice_id: str


class AnswerResult(BaseModel):
    """
    의미 테스트 답안 제출 결과 모델
    """

    card_id: str
    is_correct: bool
    next_stage: str
    can_proceed: bool


class AnswerSubmitResponse(BaseModel):
    """
    의미 테스트 답안 제출 Response 모델
    """

    success: bool
    data: Optional[AnswerResult]
    message: Optional[str] = None


class PronunciationResult(BaseModel):
    """
    발음 평가 결과 모델
    """

    card_id: str
    score: int
    feedback: str
    pronunciation_status: str
    is_card_completed: bool


class PronunciationResponse(BaseModel):
    """
    발음 평가 Response 모델
    """

    success: bool
    data: Optional[PronunciationResult]
    message: Optional[str] = None


class SavedWord(BaseModel):
    """
    저장 단어 모델
    """

    saved_word_id: str
    word: str
    image_url: str


class SavedWordsResponse(BaseModel):
    """
    저장 단어 목록 조회 Response 모델
    """

    success: bool
    data: List[SavedWord]
    message: Optional[str] = None
