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

현재는 UI 연동 확인을 위한 더미 데이터 기반으로 동작합니다.
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles

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
    AnswerResult,
    AnswerSubmitResponse,
    PronunciationResult,
    PronunciationResponse,
    SavedWord,
    SavedWordsResponse,
)


# =============================================================================
# FastAPI 앱 초기화
# =============================================================================

app = FastAPI(
    title="아리랑 수리랑 API",
    description="다의어 학습용 세로 스와이프 피드 기반 학습 플로우 API",
    version="0.1.0",
)

# 실행 위치: backend/fastapi
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


# =============================================================================
# 이미지 경로 상수
# =============================================================================

CARD_IMAGE_BIRD_WRITE = "/assets/cards/bird-write.png"
CARD_IMAGE_PLACEHOLDER = "/assets/cards/placeholder.png"
CARD_IMAGE_TIGER_CAP = "/assets/cards/tiger-cap.png"
CARD_IMAGE_TIGER_SNOW = "/assets/cards/tiger-snow.png"

CATEGORY_IMAGE_BANK = "/assets/categories/bank.png"
CATEGORY_IMAGE_HOSPITAL = "/assets/categories/hospital.png"
CATEGORY_IMAGE_SCHOOL = "/assets/categories/school.png"


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
async def get_recommended_contents():
    """
    추천 학습 세트 목록 조회 API

    홈 화면의 추천 콘텐츠 영역에 표시할 학습 세트 목록을 반환합니다.
    현재는 UI 확인용 더미 데이터를 반환합니다.
    """

    recommended_sets = [
        RecommendedSet(
            set_id="set_hospital_01",
            title="병원",
            thumbnail_url=CATEGORY_IMAGE_HOSPITAL,
        ),
        RecommendedSet(
            set_id="set_school_01",
            title="고등학교",
            thumbnail_url=CATEGORY_IMAGE_SCHOOL,
        ),
        RecommendedSet(
            set_id="set_bank_01",
            title="은행",
            thumbnail_url=CATEGORY_IMAGE_BANK,
        ),
    ]

    return RecommendedResponse(
        success=True,
        data=recommended_sets,
        message=None,
    )


# =============================================================================
# 2. 최근 학습 목록 조회
# =============================================================================


@app.get("/api/v1/contents/recent", response_model=RecentResponse)
async def get_recent_contents():
    """
    최근 학습 목록 조회 API

    홈 화면의 최근 기록 영역에 표시할 최근 학습 카드 목록을 반환합니다.
    현재는 UI 확인용 더미 데이터를 반환합니다.
    """

    recent_cards = [
        RecentCard(
            card_id="card_001",
            word="쓰다",
            image_url=CARD_IMAGE_BIRD_WRITE,
            last_viewed_at="2026-04-25T11:00:00",
        ),
        RecentCard(
            card_id="card_002",
            word="보다",
            image_url=CARD_IMAGE_PLACEHOLDER,
            last_viewed_at="2026-04-25T11:05:00",
        ),
        RecentCard(
            card_id="card_006",
            word="맞다",
            image_url=CARD_IMAGE_PLACEHOLDER,
            last_viewed_at="2026-04-25T11:10:00",
        ),
    ]

    return RecentResponse(
        success=True,
        data=recent_cards,
        message=None,
    )


# =============================================================================
# 3. 카테고리 목록 조회
# =============================================================================


@app.get("/api/v1/categories", response_model=CategoriesResponse)
async def get_categories():
    """
    카테고리 목록 조회 API

    카테고리/검색 화면에 표시할 카테고리 칩 목록을 반환합니다.
    현재 UI에 표시된 카테고리 기준으로 더미 데이터를 구성합니다.
    """

    categories = [
        Category(
            category_id="hospital",
            name_ko="병원",
            name_en="Hospital",
        ),
        Category(
            category_id="school",
            name_ko="고등학교",
            name_en="High school",
        ),
        Category(
            category_id="hanging_with",
            name_ko="친구와 놀기",
            name_en="Hanging with",
        ),
        Category(
            category_id="bank",
            name_ko="은행",
            name_en="Bank",
        ),
        Category(
            category_id="cafe",
            name_ko="카페",
            name_en="Cafe",
        ),
        Category(
            category_id="pc_game",
            name_ko="PC 게임",
            name_en="Video games",
        ),
        Category(
            category_id="university",
            name_ko="대학교",
            name_en="University",
        ),
    ]

    return CategoriesResponse(
        success=True,
        data=categories,
        message=None,
    )


# =============================================================================
# 4. 카테고리별 학습 세트 조회
# =============================================================================


@app.get("/api/v1/categories/{category_id}/sets", response_model=CategorySetsResponse)
async def get_category_sets(category_id: str):
    """
    카테고리별 학습 세트 조회 API

    선택한 카테고리에 포함된 학습 세트 목록을 반환합니다.
    현재는 category_id에 따라 UI 확인용 더미 데이터를 반환합니다.
    """

    if category_id == "hospital":
        sets = [
            LearningSet(
                set_id="set_hospital_01",
                title="병원",
                word_count=5,
                words=["맞다", "나다", "보다", "재다", "받다"],
            ),
        ]

    elif category_id == "school":
        sets = [
            LearningSet(
                set_id="set_school_01",
                title="고등학교",
                word_count=5,
                words=["보다", "풀다", "맞다", "쓰다", "듣다"],
            ),
        ]

    elif category_id == "bank":
        sets = [
            LearningSet(
                set_id="set_bank_01",
                title="은행",
                word_count=5,
                words=["보다", "들다", "찾다", "넣다", "빠지다"],
            ),
        ]

    elif category_id == "hanging_with":
        sets = [
            LearningSet(
                set_id="set_hanging_with_01",
                title="친구와 놀기",
                word_count=5,
                words=["보다", "들다", "맞다", "나다", "먹다"],
            ),
        ]

    elif category_id == "cafe":
        sets = [
            LearningSet(
                set_id="set_cafe_01",
                title="카페",
                word_count=5,
                words=["내리다", "쓰다", "들다", "시키다", "타다"],
            ),
        ]

    elif category_id == "pc_game":
        sets = [
            LearningSet(
                set_id="set_pc_game_01",
                title="PC 게임",
                word_count=5,
                words=["맞다", "잡다", "먹다", "들다", "보다"],
            ),
        ]

    elif category_id == "university":
        sets = [
            LearningSet(
                set_id="set_university_01",
                title="대학교",
                word_count=5,
                words=["보다", "듣다", "잡다", "쓰다", "내다"],
            ),
        ]

    else:
        sets = []

    return CategorySetsResponse(
        success=True,
        data=sets,
        message=None,
    )


# =============================================================================
# 5. 학습 카드 목록 조회
# =============================================================================


@app.get("/api/v1/sets/{set_id}/cards", response_model=SetCardsResponse)
async def get_set_cards(set_id: str):
    """
    학습 카드 목록 조회 API

    특정 학습 세트에 포함된 학습 카드 목록을 반환합니다.
    학습 피드 화면은 이 API의 cards 배열을 기반으로 구성됩니다.

    현재는 UI 연동 확인용 더미 데이터를 반환합니다.
    """

    if set_id == "set_school_01":
        cards = [
            LearningCard(
                card_id="card_001",
                polysemy_word="쓰다",
                prompt_sentence="저는 매일 저녁에 일기를 써요.",
                choices=[
                    Choice(choice_id="c1", text="글씨 쓰는 연습을 하세요."),
                    Choice(choice_id="c2", text="어제 쓴 우산을 말리고 있어요."),
                    Choice(choice_id="c3", text="모자 쓴 사람을 보았어요."),
                    Choice(choice_id="c4", text="이 소스는 조금 쓰네요."),
                ],
                pronunciation_target="쓰는",
                image_url=CARD_IMAGE_BIRD_WRITE,
                card_order=1,
            ),
            LearningCard(
                card_id="card_002",
                polysemy_word="보다",
                prompt_sentence="오늘 국어 시험을 봤어요.",
                choices=[
                    Choice(choice_id="c1", text="친구와 영화를 봤어요."),
                    Choice(choice_id="c2", text="오늘 수학 시험을 봤어요."),
                    Choice(choice_id="c3", text="창밖을 보았어요."),
                    Choice(choice_id="c4", text="의사가 환자를 봤어요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_003",
                polysemy_word="풀다",
                prompt_sentence="수학 문제를 풀고 있어요.",
                choices=[
                    Choice(choice_id="c1", text="친구의 오해를 풀었어요."),
                    Choice(choice_id="c2", text="운동화 끈을 풀었어요."),
                    Choice(choice_id="c3", text="어려운 문제를 풀었어요."),
                    Choice(choice_id="c4", text="긴장을 풀고 쉬었어요."),
                ],
                pronunciation_target="풀다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_004",
                polysemy_word="맞다",
                prompt_sentence="이 문제의 답이 맞았어요.",
                choices=[
                    Choice(choice_id="c1", text="비를 맞아서 옷이 젖었어요."),
                    Choice(choice_id="c2", text="친구에게 공을 맞았어요."),
                    Choice(choice_id="c3", text="그 답은 맞아요."),
                    Choice(choice_id="c4", text="주사를 맞았어요."),
                ],
                pronunciation_target="맞다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_005",
                polysemy_word="듣다",
                prompt_sentence="수업을 집중해서 들었어요.",
                choices=[
                    Choice(choice_id="c1", text="음악을 들었어요."),
                    Choice(choice_id="c2", text="선생님 수업을 들었어요."),
                    Choice(choice_id="c3", text="약이 잘 들어요."),
                    Choice(choice_id="c4", text="부탁을 들어주었어요."),
                ],
                pronunciation_target="듣다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_school_01",
            title="고등학교",
            cards=cards,
        )

    elif set_id == "set_hospital_01":
        cards = [
            LearningCard(
                card_id="card_006",
                polysemy_word="맞다",
                prompt_sentence="병원에서 주사를 맞았어요.",
                choices=[
                    Choice(choice_id="c1", text="정답이 맞았어요."),
                    Choice(choice_id="c2", text="비를 맞아서 옷이 젖었어요."),
                    Choice(choice_id="c3", text="병원에서 주사를 맞았어요."),
                    Choice(choice_id="c4", text="그 말이 맞는 것 같아요."),
                ],
                pronunciation_target="맞다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_007",
                polysemy_word="나다",
                prompt_sentence="열이 나서 병원에 갔어요.",
                choices=[
                    Choice(choice_id="c1", text="좋은 생각이 났어요."),
                    Choice(choice_id="c2", text="창문에서 소리가 났어요."),
                    Choice(choice_id="c3", text="열이 나서 병원에 갔어요."),
                    Choice(choice_id="c4", text="길이 나 있어서 쉽게 갔어요."),
                ],
                pronunciation_target="나다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_008",
                polysemy_word="보다",
                prompt_sentence="의사 선생님이 환자를 봐 주셨어요.",
                choices=[
                    Choice(choice_id="c1", text="영화를 봤어요."),
                    Choice(choice_id="c2", text="창밖을 보았어요."),
                    Choice(choice_id="c3", text="의사가 환자를 봐 주셨어요."),
                    Choice(choice_id="c4", text="시험을 보았어요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_009",
                polysemy_word="재다",
                prompt_sentence="간호사가 체온을 재고 있어요.",
                choices=[
                    Choice(choice_id="c1", text="체온을 재고 있어요."),
                    Choice(choice_id="c2", text="길이를 재고 있어요."),
                    Choice(choice_id="c3", text="시간을 재고 있어요."),
                    Choice(choice_id="c4", text="키를 재고 있어요."),
                ],
                pronunciation_target="재다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_010",
                polysemy_word="받다",
                prompt_sentence="병원에서 진료를 받았어요.",
                choices=[
                    Choice(choice_id="c1", text="친구에게 선물을 받았어요."),
                    Choice(choice_id="c2", text="병원에서 진료를 받았어요."),
                    Choice(choice_id="c3", text="전화를 받았어요."),
                    Choice(choice_id="c4", text="공을 받았어요."),
                ],
                pronunciation_target="받다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_hospital_01",
            title="병원",
            cards=cards,
        )

    elif set_id == "set_bank_01":
        cards = [
            LearningCard(
                card_id="card_011",
                polysemy_word="찾다",
                prompt_sentence="은행에서 돈을 찾았어요.",
                choices=[
                    Choice(choice_id="c1", text="잃어버린 지갑을 찾았어요."),
                    Choice(choice_id="c2", text="은행에서 돈을 찾았어요."),
                    Choice(choice_id="c3", text="친구 집을 찾았어요."),
                    Choice(choice_id="c4", text="인터넷에서 정보를 찾았어요."),
                ],
                pronunciation_target="찾다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_012",
                polysemy_word="넣다",
                prompt_sentence="통장에 돈을 넣었어요.",
                choices=[
                    Choice(choice_id="c1", text="가방에 책을 넣었어요."),
                    Choice(choice_id="c2", text="통장에 돈을 넣었어요."),
                    Choice(choice_id="c3", text="컵에 얼음을 넣었어요."),
                    Choice(choice_id="c4", text="상자에 옷을 넣었어요."),
                ],
                pronunciation_target="넣다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_013",
                polysemy_word="들다",
                prompt_sentence="적금을 들었어요.",
                choices=[
                    Choice(choice_id="c1", text="손에 가방을 들었어요."),
                    Choice(choice_id="c2", text="새 적금을 들었어요."),
                    Choice(choice_id="c3", text="방에 들어갔어요."),
                    Choice(choice_id="c4", text="마음에 들었어요."),
                ],
                pronunciation_target="들다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_014",
                polysemy_word="빠지다",
                prompt_sentence="계좌에서 돈이 빠져나갔어요.",
                choices=[
                    Choice(choice_id="c1", text="물에 빠졌어요."),
                    Choice(choice_id="c2", text="수업에 빠졌어요."),
                    Choice(choice_id="c3", text="계좌에서 돈이 빠져나갔어요."),
                    Choice(choice_id="c4", text="살이 빠졌어요."),
                ],
                pronunciation_target="빠지다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_015",
                polysemy_word="보다",
                prompt_sentence="계좌 잔액을 확인해 봤어요.",
                choices=[
                    Choice(choice_id="c1", text="영화를 봤어요."),
                    Choice(choice_id="c2", text="계좌 잔액을 확인해 봤어요."),
                    Choice(choice_id="c3", text="시험을 봤어요."),
                    Choice(choice_id="c4", text="환자를 봤어요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_bank_01",
            title="은행",
            cards=cards,
        )

    elif set_id == "set_hanging_with_01":
        cards = [
            LearningCard(
                card_id="card_016",
                polysemy_word="보다",
                prompt_sentence="친구와 영화를 봤어요.",
                choices=[
                    Choice(choice_id="c1", text="친구와 영화를 봤어요."),
                    Choice(choice_id="c2", text="시험을 봤어요."),
                    Choice(choice_id="c3", text="의사가 환자를 봤어요."),
                    Choice(choice_id="c4", text="상황을 봐야 해요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_017",
                polysemy_word="들다",
                prompt_sentence="그 친구가 마음에 들었어요.",
                choices=[
                    Choice(choice_id="c1", text="손에 우산을 들었어요."),
                    Choice(choice_id="c2", text="그 친구가 마음에 들었어요."),
                    Choice(choice_id="c3", text="적금을 들었어요."),
                    Choice(choice_id="c4", text="방에 들었어요."),
                ],
                pronunciation_target="들다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_018",
                polysemy_word="먹다",
                prompt_sentence="친구들과 밥을 먹었어요.",
                choices=[
                    Choice(choice_id="c1", text="친구들과 밥을 먹었어요."),
                    Choice(choice_id="c2", text="욕을 먹었어요."),
                    Choice(choice_id="c3", text="나이를 먹었어요."),
                    Choice(choice_id="c4", text="겁을 먹었어요."),
                ],
                pronunciation_target="먹다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_019",
                polysemy_word="맞다",
                prompt_sentence="친구 말이 맞았어요.",
                choices=[
                    Choice(choice_id="c1", text="공에 맞았어요."),
                    Choice(choice_id="c2", text="비를 맞았어요."),
                    Choice(choice_id="c3", text="친구 말이 맞았어요."),
                    Choice(choice_id="c4", text="주사를 맞았어요."),
                ],
                pronunciation_target="맞다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_020",
                polysemy_word="나다",
                prompt_sentence="친구와 이야기하다가 웃음이 났어요.",
                choices=[
                    Choice(choice_id="c1", text="상처가 났어요."),
                    Choice(choice_id="c2", text="길이 났어요."),
                    Choice(choice_id="c3", text="친구와 이야기하다가 웃음이 났어요."),
                    Choice(choice_id="c4", text="소리가 났어요."),
                ],
                pronunciation_target="나다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_hanging_with_01",
            title="친구와 놀기",
            cards=cards,
        )

    elif set_id == "set_cafe_01":
        cards = [
            LearningCard(
                card_id="card_021",
                polysemy_word="내리다",
                prompt_sentence="카페 직원이 커피를 내려 주었어요.",
                choices=[
                    Choice(choice_id="c1", text="비가 내렸어요."),
                    Choice(choice_id="c2", text="버스에서 내렸어요."),
                    Choice(choice_id="c3", text="커피를 내려 마셨어요."),
                    Choice(choice_id="c4", text="열이 내렸어요."),
                ],
                pronunciation_target="내리다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_022",
                polysemy_word="쓰다",
                prompt_sentence="커피가 너무 써서 설탕을 넣었어요.",
                choices=[
                    Choice(choice_id="c1", text="편지를 썼어요."),
                    Choice(choice_id="c2", text="모자를 썼어요."),
                    Choice(choice_id="c3", text="커피 맛이 너무 써요."),
                    Choice(choice_id="c4", text="우산을 썼어요."),
                ],
                pronunciation_target="쓰다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_023",
                polysemy_word="시키다",
                prompt_sentence="친구가 커피를 시켰어요.",
                choices=[
                    Choice(choice_id="c1", text="동생에게 심부름을 시켰어요."),
                    Choice(choice_id="c2", text="친구가 커피를 시켰어요."),
                    Choice(choice_id="c3", text="선생님이 발표를 시켰어요."),
                    Choice(choice_id="c4", text="아이를 조용히 시켰어요."),
                ],
                pronunciation_target="시키다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_024",
                polysemy_word="타다",
                prompt_sentence="따뜻한 커피를 타서 마셨어요.",
                choices=[
                    Choice(choice_id="c1", text="버스를 탔어요."),
                    Choice(choice_id="c2", text="피부가 탔어요."),
                    Choice(choice_id="c3", text="커피를 타서 마셨어요."),
                    Choice(choice_id="c4", text="상을 탔어요."),
                ],
                pronunciation_target="타다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_025",
                polysemy_word="들다",
                prompt_sentence="이 카페 분위기가 마음에 들었어요.",
                choices=[
                    Choice(choice_id="c1", text="손에 컵을 들었어요."),
                    Choice(choice_id="c2", text="적금을 들었어요."),
                    Choice(choice_id="c3", text="카페 분위기가 마음에 들었어요."),
                    Choice(choice_id="c4", text="방에 들었어요."),
                ],
                pronunciation_target="들다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_cafe_01",
            title="카페",
            cards=cards,
        )

    elif set_id == "set_pc_game_01":
        cards = [
            LearningCard(
                card_id="card_026",
                polysemy_word="맞다",
                prompt_sentence="게임에서 공격을 맞고 캐릭터가 쓰러졌어요.",
                choices=[
                    Choice(choice_id="c1", text="정답이 맞았어요."),
                    Choice(choice_id="c2", text="공격을 맞았어요."),
                    Choice(choice_id="c3", text="그 말이 맞아요."),
                    Choice(choice_id="c4", text="비를 맞았어요."),
                ],
                pronunciation_target="맞다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_027",
                polysemy_word="잡다",
                prompt_sentence="친구와 함께 몬스터를 잡았어요.",
                choices=[
                    Choice(choice_id="c1", text="손으로 공을 잡았어요."),
                    Choice(choice_id="c2", text="약속을 잡았어요."),
                    Choice(choice_id="c3", text="몬스터를 잡았어요."),
                    Choice(choice_id="c4", text="마음을 잡았어요."),
                ],
                pronunciation_target="잡다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_028",
                polysemy_word="먹다",
                prompt_sentence="게임에서 아이템을 먹었어요.",
                choices=[
                    Choice(choice_id="c1", text="밥을 먹었어요."),
                    Choice(choice_id="c2", text="욕을 먹었어요."),
                    Choice(choice_id="c3", text="아이템을 먹었어요."),
                    Choice(choice_id="c4", text="겁을 먹었어요."),
                ],
                pronunciation_target="먹다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_029",
                polysemy_word="들다",
                prompt_sentence="캐릭터가 새 무기를 들었어요.",
                choices=[
                    Choice(choice_id="c1", text="무기를 들었어요."),
                    Choice(choice_id="c2", text="마음에 들었어요."),
                    Choice(choice_id="c3", text="적금을 들었어요."),
                    Choice(choice_id="c4", text="방에 들었어요."),
                ],
                pronunciation_target="들다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_030",
                polysemy_word="보다",
                prompt_sentence="게임 화면을 보면서 친구와 이야기했어요.",
                choices=[
                    Choice(choice_id="c1", text="게임 화면을 봤어요."),
                    Choice(choice_id="c2", text="시험을 봤어요."),
                    Choice(choice_id="c3", text="환자를 봤어요."),
                    Choice(choice_id="c4", text="상황을 봐야 해요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_pc_game_01",
            title="PC 게임",
            cards=cards,
        )

    elif set_id == "set_university_01":
        cards = [
            LearningCard(
                card_id="card_031",
                polysemy_word="보다",
                prompt_sentence="이번 주에 중간고사를 봤어요.",
                choices=[
                    Choice(choice_id="c1", text="영화를 봤어요."),
                    Choice(choice_id="c2", text="중간고사를 봤어요."),
                    Choice(choice_id="c3", text="환자를 봤어요."),
                    Choice(choice_id="c4", text="창밖을 봤어요."),
                ],
                pronunciation_target="보다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=1,
            ),
            LearningCard(
                card_id="card_032",
                polysemy_word="듣다",
                prompt_sentence="전공 수업을 듣고 있어요.",
                choices=[
                    Choice(choice_id="c1", text="음악을 들었어요."),
                    Choice(choice_id="c2", text="전공 수업을 들었어요."),
                    Choice(choice_id="c3", text="부탁을 들어주었어요."),
                    Choice(choice_id="c4", text="약이 잘 들어요."),
                ],
                pronunciation_target="듣다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=2,
            ),
            LearningCard(
                card_id="card_033",
                polysemy_word="잡다",
                prompt_sentence="다음 학기 시간표를 잡았어요.",
                choices=[
                    Choice(choice_id="c1", text="손으로 연필을 잡았어요."),
                    Choice(choice_id="c2", text="시간표를 잡았어요."),
                    Choice(choice_id="c3", text="몬스터를 잡았어요."),
                    Choice(choice_id="c4", text="마음을 잡았어요."),
                ],
                pronunciation_target="잡다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=3,
            ),
            LearningCard(
                card_id="card_034",
                polysemy_word="쓰다",
                prompt_sentence="수업 시간에 보고서를 썼어요.",
                choices=[
                    Choice(choice_id="c1", text="보고서를 썼어요."),
                    Choice(choice_id="c2", text="모자를 썼어요."),
                    Choice(choice_id="c3", text="커피가 써요."),
                    Choice(choice_id="c4", text="우산을 썼어요."),
                ],
                pronunciation_target="쓰다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=4,
            ),
            LearningCard(
                card_id="card_035",
                polysemy_word="내다",
                prompt_sentence="교수님께 과제를 냈어요.",
                choices=[
                    Choice(choice_id="c1", text="소리를 냈어요."),
                    Choice(choice_id="c2", text="돈을 냈어요."),
                    Choice(choice_id="c3", text="과제를 냈어요."),
                    Choice(choice_id="c4", text="문제를 냈어요."),
                ],
                pronunciation_target="내다",
                image_url=CARD_IMAGE_PLACEHOLDER,
                card_order=5,
            ),
        ]

        data = SetCardsData(
            set_id="set_university_01",
            title="대학교",
            cards=cards,
        )

    else:
        data = SetCardsData(
            set_id=set_id,
            title="정보 없음",
            cards=[],
        )

    return SetCardsResponse(
        success=True,
        data=data,
        message=None,
    )


# =============================================================================
# 6. 의미 테스트 답안 제출
# =============================================================================


@app.post("/api/v1/cards/{card_id}/answer", response_model=AnswerSubmitResponse)
async def submit_card_answer(card_id: str, request: AnswerSubmitRequest):
    """
    의미 테스트 답안 제출 API

    사용자가 선택한 보기의 정답 여부를 판정합니다.
    정답이면 발음 교정 단계로 이동할 수 있고,
    오답이면 현재 문제 단계에 머무릅니다.
    """

    answer_key = {
        "card_001": "c1",
        "card_002": "c2",
        "card_003": "c3",
        "card_004": "c3",
        "card_005": "c2",
        "card_006": "c3",
        "card_007": "c3",
        "card_008": "c3",
        "card_009": "c1",
        "card_010": "c2",
        "card_011": "c2",
        "card_012": "c2",
        "card_013": "c2",
        "card_014": "c3",
        "card_015": "c2",
        "card_016": "c1",
        "card_017": "c2",
        "card_018": "c1",
        "card_019": "c3",
        "card_020": "c3",
        "card_021": "c3",
        "card_022": "c3",
        "card_023": "c2",
        "card_024": "c3",
        "card_025": "c3",
        "card_026": "c2",
        "card_027": "c3",
        "card_028": "c3",
        "card_029": "c1",
        "card_030": "c1",
        "card_031": "c2",
        "card_032": "c2",
        "card_033": "c2",
        "card_034": "c1",
        "card_035": "c3",
    }

    correct_choice_id = answer_key.get(card_id)

    if correct_choice_id is None:
        return AnswerSubmitResponse(
            success=False,
            data=None,
            message="존재하지 않는 카드입니다.",
        )

    is_correct = request.choice_id == correct_choice_id

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
# 7. 발음 평가 요청
# =============================================================================


@app.post("/api/v1/cards/{card_id}/pronunciation", response_model=PronunciationResponse)
async def evaluate_pronunciation(
    card_id: str,
    target_text: str = Form(...),
    audio_file: UploadFile = File(...),
):
    """
    발음 평가 요청 API

    사용자가 녹음한 음성 파일과 발음 대상 텍스트를 전송하면
    발음 점수와 피드백을 반환합니다.

    현재는 실제 음성 분석 모델 없이 고정 더미 결과를 반환합니다. (추후 AI 모델 연동 예정)
    """

    allowed_card_ids = {f"card_{i:03d}" for i in range(1, 36)}

    if card_id not in allowed_card_ids:
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

    data = PronunciationResult(
        card_id=card_id,
        score=89,
        feedback="전반적인 발음은 정확하나, 일부 음절 연결이 다소 부자연스럽습니다.",
        pronunciation_status="DONE",
        is_card_completed=True,
    )

    return PronunciationResponse(
        success=True,
        data=data,
        message=None,
    )


# =============================================================================
# 8. 저장 단어 목록 조회
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
