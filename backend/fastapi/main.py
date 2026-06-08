"""
아리랑 수리랑 백엔드 API 서버

다의어 학습용 세로 스와이프 피드 기반 학습 플로우를 위한
FastAPI 백엔드 서버입니다.

주요 기능:
- 추천 학습 세트 조회
- 최근 학습 목록 조회
- 카테고리 목록 조회
- 카테고리별 학습 세트 조회
- 학습 카드 목록 조회
- 의미 테스트 답안 제출
- 발음 평가 요청
- 저장 단어 목록 조회

현재 카테고리/세트/카드/추천/최근 기록/보기에 대한 정답 판정 API는
PostgreSQL DB 기반으로 동작하며, 발음/저장 단어 API는 아직 UI 확인용 더미
데이터 기반으로 동작합니다.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from schemas import (
    RecommendedSet,
    RecommendedResponse,
    RecentCard,
    RecentResponse,
    Category,
    CategoriesResponse,
    LearningSet,
    CategorySetsResponse,
    Choice,
    LearningCard,
    SetCardsData,
    SetCardsResponse,
    AnswerSubmitRequest,
    TtsUrlUpdateRequest,
    AnswerResult,
    AnswerSubmitResponse,
    PronunciationResult,
    PronunciationResponse,
    SavedWord,
    SavedWordsResponse,
)

from database import get_db
from db_models import (
    CategoryDB,
    LearningSetDB,
    QuizDB,
    QuizChoiceDB,
    SentenceDB,
    RecentLearningRecordDB,
)
from pronunciation_client import (
    PronunciationAnalysisError,
    analyze_pronunciation,
    build_pronunciation_result,
)

# =============================================================================
# FastAPI 앱 초기화
# =============================================================================

app = FastAPI(
    title="아리랑 수리랑 API",
    description="다의어 학습용 세로 스와이프 피드 기반 학습 플로우 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 실행 위치: backend/fastapi
app.mount(
    "/assets/categories",
    StaticFiles(directory="categories"),
    name="category_assets",
)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# =============================================================================
# 이미지 식별자
# =============================================================================

FRONTEND_ASSET_WRITE = "word-image-write.png"
FRONTEND_ASSET_SNOW = "word-image-snow.png"

CARD_IMAGE_BIRD_WRITE = FRONTEND_ASSET_WRITE
CARD_IMAGE_PLACEHOLDER = FRONTEND_ASSET_SNOW
CARD_IMAGE_TIGER_CAP = FRONTEND_ASSET_SNOW
CARD_IMAGE_TIGER_SNOW = FRONTEND_ASSET_SNOW

CATEGORY_IMAGE_BANK = FRONTEND_ASSET_SNOW
CATEGORY_IMAGE_HOSPITAL = FRONTEND_ASSET_WRITE
CATEGORY_IMAGE_SCHOOL = FRONTEND_ASSET_WRITE

SET_THUMBNAIL_MAPPING = {
    "set_school_01": CATEGORY_IMAGE_SCHOOL,
    "set_hospital_01": CATEGORY_IMAGE_HOSPITAL,
    "set_bank_01": CATEGORY_IMAGE_BANK,
    "set_hanging_with_01": CARD_IMAGE_PLACEHOLDER,
    "set_cafe_01": CARD_IMAGE_PLACEHOLDER,
    "set_pc_game_01": CARD_IMAGE_PLACEHOLDER,
    "set_university_01": CARD_IMAGE_PLACEHOLDER,
    "set_test_01": CARD_IMAGE_PLACEHOLDER,
}


# =============================================================================
# 헬퍼 함수들
# =============================================================================


def get_categories_from_db(db: Session):
    categories = db.query(CategoryDB).order_by(CategoryDB.category_id).all()
    return [
        Category(
            category_id=category.category_id,
            name_ko=category.name_ko,
            name_en=category.name_en,
        )
        for category in categories
    ]


def get_learning_sets_for_category(db: Session, category_id: str):
    learning_sets = (
        db.query(LearningSetDB)
        .filter(LearningSetDB.category_id == category_id)
        .order_by(LearningSetDB.set_id)
        .all()
    )

    sets = []
    for learning_set in learning_sets:
        words = sorted({quiz.polysemy_word for quiz in learning_set.quizzes})
        sets.append(
            LearningSet(
                set_id=learning_set.set_id,
                title=learning_set.title,
                word_count=len(words),
                words=words,
            )
        )

    return sets


def get_cards_for_set(db: Session, set_id: str):
    learning_set = db.query(LearningSetDB).filter(LearningSetDB.set_id == set_id).one_or_none()
    if learning_set is None:
        return None

    set_quizzes = (
        db.query(QuizDB)
        .filter(QuizDB.set_id == set_id)
        .order_by(QuizDB.card_order)
        .all()
    )

    title_mapping = {
        "set_school_01": "고등학교",
        "set_hospital_01": "병원",
        "set_bank_01": "은행",
        "set_hanging_with_01": "친구와 놀기",
        "set_cafe_01": "카페",
        "set_pc_game_01": "PC 게임",
        "set_university_01": "대학교",
        "set_test_01": "테스트",
    }

    cards = []
    for quiz in set_quizzes:
        choices = [
            Choice(choice_id=choice.choice_id, text=choice.text)
            for choice in sorted(quiz.choices, key=lambda choice: choice.choice_id)
        ]
        cards.append(
            LearningCard(
                card_id=quiz.card_id,
                sentence_id=quiz.sentence_id,
                polysemy_word=quiz.polysemy_word,
                prompt_sentence=quiz.prompt_sentence,
                choices=choices,
                pronunciation_target=quiz.pronunciation_target,
                tts_url=quiz.tts_url,
                image_url=quiz.image_url,
                card_order=quiz.card_order,
            )
        )

    return SetCardsData(
        set_id=set_id,
        title=title_mapping.get(set_id, learning_set.title),
        cards=cards,
    )


def get_recommended_sets_from_db(db: Session):
    learning_sets = (
        db.query(LearningSetDB)
        .join(QuizDB, LearningSetDB.set_id == QuizDB.set_id)
        .group_by(LearningSetDB.set_id)
        .order_by(LearningSetDB.set_id)
        .all()
    )
    return [
        RecommendedSet(
            set_id=learning_set.set_id,
            title=learning_set.title,
            thumbnail_url=(
                learning_set.thumbnail_url
                or SET_THUMBNAIL_MAPPING.get(
                    learning_set.set_id, CARD_IMAGE_PLACEHOLDER
                )
            ),
        )
        for learning_set in learning_sets
    ]


def touch_recent_learning_record(db: Session, card_id: str):
    record = (
        db.query(RecentLearningRecordDB)
        .filter(RecentLearningRecordDB.card_id == card_id)
        .one_or_none()
    )
    now = datetime.now(timezone.utc)

    if record is None:
        db.add(RecentLearningRecordDB(card_id=card_id, last_viewed_at=now))
    else:
        record.last_viewed_at = now


def get_recent_cards_from_db(db: Session):
    records = (
        db.query(RecentLearningRecordDB)
        .join(QuizDB, RecentLearningRecordDB.card_id == QuizDB.card_id)
        .order_by(RecentLearningRecordDB.last_viewed_at.desc())
        .limit(6)
        .all()
    )

    if records:
        return [
                RecentCard(
                    card_id=record.quiz.card_id,
                    set_id=record.quiz.set_id,
                    word=record.quiz.polysemy_word,
                    image_url=record.quiz.image_url or CARD_IMAGE_PLACEHOLDER,
                    last_viewed_at=record.last_viewed_at.isoformat(),
                )
            for record in records
        ]

    quizzes = db.query(QuizDB).order_by(QuizDB.card_id).limit(6).all()
    return [
            RecentCard(
                card_id=quiz.card_id,
                set_id=quiz.set_id,
                word=quiz.polysemy_word,
                image_url=quiz.image_url or CARD_IMAGE_PLACEHOLDER,
                last_viewed_at=datetime.now(timezone.utc).isoformat(),
            )
        for quiz in quizzes
    ]


# =============================================================================
# 기본 테스트 엔드포인트
# =============================================================================


@app.get("/")
async def root():
    """
    서버 상태 확인용 루트 엔드포인트
    """
    return {"message": "아리랑 수리랑 API 서버가 실행 중입니다."}


@app.get("/munang")
async def munang():
    """
    테스트용 엔드포인트
    """
    return {"message": "무냉"}


# =============================================================================
# 1. 추천 학습 세트 조회
# =============================================================================


@app.get("/api/v1/contents/recommended", response_model=RecommendedResponse)
async def get_recommended_contents(db: Session = Depends(get_db)):
    """
    추천 학습 세트 목록 조회 API

    홈 화면의 추천 콘텐츠 영역에 표시할 학습 세트 목록을 반환합니다.
    실제 데이터에서 동적으로 생성된 세트 목록을 반환합니다.
    """

    recommended_sets = get_recommended_sets_from_db(db)

    return RecommendedResponse(
        success=True,
        data=recommended_sets,
        message=None,
    )


# =============================================================================
# 2. 최근 학습 목록 조회
# =============================================================================


@app.get("/api/v1/contents/recent", response_model=RecentResponse)
async def get_recent_contents(db: Session = Depends(get_db)):
    """
    최근 학습 목록 조회 API

    홈 화면의 최근 기록 영역에 표시할 최근 학습 카드 목록을 반환합니다.
    학습 기록이 있으면 최근 기록 테이블에서, 아직 기록이 없으면 카드 DB에서
    기본 목록을 반환합니다.
    """

    recent_cards = get_recent_cards_from_db(db)

    return RecentResponse(
        success=True,
        data=recent_cards,
        message=None,
    )


# =============================================================================
# 3. 카테고리 목록 조회
# =============================================================================


@app.get("/api/v1/categories", response_model=CategoriesResponse)
async def get_categories(db: Session = Depends(get_db)):
    """
    카테고리 목록 조회 API

    카테고리/검색 화면에 표시할 카테고리 칩 목록을 반환합니다.
    실제 데이터에서 동적으로 생성합니다.
    """

    categories = get_categories_from_db(db)

    return CategoriesResponse(
        success=True,
        data=categories,
        message=None,
    )


# =============================================================================
# 4. 카테고리별 학습 세트 조회
# =============================================================================


@app.get("/api/v1/categories/{category_id}/sets", response_model=CategorySetsResponse)
async def get_category_sets(category_id: str, db: Session = Depends(get_db)):
    """
    카테고리별 학습 세트 조회 API

    선택한 카테고리에 포함된 학습 세트 목록을 반환합니다.
    실제 데이터에서 동적으로 생성합니다.
    """

    sets = get_learning_sets_for_category(db, category_id)

    return CategorySetsResponse(
        success=True,
        data=sets,
        message=None,
    )


# =============================================================================
# 5. 학습 카드 목록 조회
# =============================================================================


@app.get("/api/v1/sets/{set_id}/cards", response_model=SetCardsResponse)
async def get_set_cards(set_id: str, db: Session = Depends(get_db)):
    """
    학습 카드 목록 조회 API

    특정 학습 세트에 포함된 학습 카드 목록을 반환합니다.
    학습 피드 화면은 이 API의 cards 배열을 기반으로 구성됩니다.

    실제 데이터에서 동적으로 생성합니다.
    """

    data = get_cards_for_set(db, set_id)

    if data is None:
        return SetCardsResponse(
            success=False,
            data=None,
            message="존재하지 않는 세트입니다.",
        )

    return SetCardsResponse(
        success=True,
        data=data,
        message=None,
    )


# =============================================================================
# 6. TTS URL 갱신
# =============================================================================


@app.patch("/api/v1/sentences/{sentence_id}/tts-url")
async def update_sentence_tts_url(
    sentence_id: str,
    request: TtsUrlUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    문장 TTS URL 갱신 API

    AI가 TTS 파일을 Object Storage에 업로드한 뒤 받은 URL을 전달하면,
    문장과 해당 문장을 프롬프트로 사용하는 카드에 URL을 저장합니다.
    """

    sentence = (
        db.query(SentenceDB).filter(SentenceDB.sentence_id == sentence_id).one_or_none()
    )
    if sentence is None:
        return {
            "success": False,
            "data": None,
            "message": "존재하지 않는 문장입니다.",
        }

    sentence.tts_url = request.tts_url
    updated_cards = db.query(QuizDB).filter(QuizDB.sentence_id == sentence_id).all()
    for quiz in updated_cards:
        quiz.tts_url = request.tts_url

    db.commit()

    return {
        "success": True,
        "data": {
            "sentence_id": sentence_id,
            "tts_url": request.tts_url,
            "updated_card_count": len(updated_cards),
        },
        "message": None,
    }


# =============================================================================
# 7. 의미 테스트 답안 제출
# =============================================================================


@app.post("/api/v1/cards/{card_id}/answer", response_model=AnswerSubmitResponse)
async def submit_card_answer(
    card_id: str,
    request: AnswerSubmitRequest,
    db: Session = Depends(get_db),
):
    """
    의미 테스트 답안 제출 API

    사용자가 선택한 보기의 정답 여부를 판정합니다.
    정답이면 발음 교정 단계로 이동할 수 있고,
    오답이면 현재 문제 단계에 머무릅니다.
    """

    quiz = db.query(QuizDB).filter(QuizDB.card_id == card_id).one_or_none()
    if quiz is None:
        return AnswerSubmitResponse(
            success=False,
            data=None,
            message="존재하지 않는 카드입니다.",
        )

    selected_choice = (
        db.query(QuizChoiceDB)
        .filter(
            QuizChoiceDB.card_id == card_id,
            QuizChoiceDB.choice_id == request.choice_id,
        )
        .one_or_none()
    )

    if selected_choice is None:
        return AnswerSubmitResponse(
            success=False,
            data=None,
            message="존재하지 않는 선택지입니다.",
        )

    touch_recent_learning_record(db, card_id)
    db.commit()

    is_correct = selected_choice.is_correct
    if is_correct:
        data = AnswerResult(
            card_id=card_id,
            is_correct=True,
            next_stage="pronunciation",
            can_proceed=True,
        )
    else:
        data = AnswerResult(
            card_id=card_id,
            is_correct=False,
            next_stage="quiz",
            can_proceed=False,
        )

    return AnswerSubmitResponse(
        success=True,
        data=data,
        message=None,
    )


# =============================================================================
# 8. 발음 평가 요청
# =============================================================================


@app.post("/api/v1/cards/{card_id}/pronunciation", response_model=PronunciationResponse)
async def evaluate_pronunciation(
    card_id: str,
    target_text: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    발음 평가 요청 API

    사용자가 녹음한 음성 파일과 발음 대상 텍스트를 전송하면
    발음 점수와 피드백을 반환합니다.

    백엔드는 프론트용 응답 형식을 유지하고, 실제 분석은 ml_core API에 위임합니다.
    """

    quiz = db.query(QuizDB).filter(QuizDB.card_id == card_id).one_or_none()
    if quiz is None:
        return PronunciationResponse(
            success=False,
            data=None,
            message="존재하지 않는 카드입니다.",
        )

    if audio_file.filename == "":
        return PronunciationResponse(
            success=False,
            data=None,
            message="업로드된 음성 파일이 없습니다.",
        )

    audio_bytes = await audio_file.read()
    if not audio_bytes:
        return PronunciationResponse(
            success=False,
            data=None,
            message="업로드된 음성 파일이 비어 있습니다.",
        )

    try:
        analysis = await analyze_pronunciation(
            audio_bytes=audio_bytes,
            filename=audio_file.filename or f"{card_id}.webm",
            target_text=target_text,
        )
        (
            score,
            feedback,
            heard_text,
            display_pronunciation_status,
            raw_heard_text,
            raw_predicted_phonemes,
            feedback_issues,
            next_practice_focus,
        ) = build_pronunciation_result(analysis)
    except PronunciationAnalysisError as exc:
        return PronunciationResponse(
            success=False,
            data=None,
            message=str(exc),
        )

    touch_recent_learning_record(db, card_id)
    db.commit()

    data = PronunciationResult(
        card_id=card_id,
        score=score,
        feedback=feedback,
        heard_text=heard_text,
        display_pronunciation_status=display_pronunciation_status,
        raw_heard_text=raw_heard_text,
        raw_predicted_phonemes=raw_predicted_phonemes,
        feedback_issues=feedback_issues,
        next_practice_focus=next_practice_focus,
        pronunciation_status="DONE",
        is_card_completed=True,
    )

    return PronunciationResponse(
        success=True,
        data=data,
        message=None,
    )


# =============================================================================
# 9. 저장 단어 목록 조회
# =============================================================================


@app.get("/api/v1/saved-words", response_model=SavedWordsResponse)
async def get_saved_words():
    """
    저장 단어 목록 조회 API

    저장 단어 화면에 표시할 단어 목록을 반환합니다.
    현재는 UI 확인용 더미 데이터를 반환합니다.
    """

    saved_words = [
        SavedWord(
            saved_word_id="saved_001",
            word="쓰다",
            image_url=CARD_IMAGE_BIRD_WRITE,
        ),
        SavedWord(
            saved_word_id="saved_002",
            word="눈",
            image_url=CARD_IMAGE_TIGER_SNOW,
        ),
        SavedWord(
            saved_word_id="saved_003",
            word="쓰다",
            image_url=CARD_IMAGE_BIRD_WRITE,
        ),
        SavedWord(
            saved_word_id="saved_004",
            word="쓰다",
            image_url=CARD_IMAGE_BIRD_WRITE,
        ),
    ]

    return SavedWordsResponse(
        success=True,
        data=saved_words,
        message=None,
    )
