# 실행 명령어: uv run -m scripts.generate_sentences --meaning-id <meaning_id> [--batch-size <size>] [--iterations <count>] [--category <keyword>]
import sys
import argparse
import asyncio
import random
from typing import List, cast
from pydantic import BaseModel, Field

from src.utils.logger import logger
from src.utils.io_ext import generate_short_id
from src.models import DataRepository, Sentence

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.output_parsers import RetryWithErrorOutputParser
from src.common import get_standard_llm


class GeneratedSentence(BaseModel):
    content: str = Field(description="생성된 자연스러운 한국어 예문 전체 (**매우 중요: 공백 포함 20자 이내로 절대 제한**)")
    highlight: str = Field(description="문장 내에서 주어진 단어가 실제로 활용(변형)되어 쓰인 정확한 어절 (예: '일기를 써요' -> '써요')")

class SentenceBatchResult(BaseModel):
    sentences: List[GeneratedSentence] = Field(description="생성된 예문 목록")


SYSTEM_INSTRUCTION = """
당신은 한국어 언어 전문가입니다. 
주어진 단어(Word)와 그 의미(Definition)를 바탕으로, 자연스럽고 활용도 높은 예문들을 생성해야 합니다.
반드시 요청받은 개수({batch_size}개)만큼 예문을 작성하세요.
{category_instruction}
{tone_instruction}

[데이터 생성 지침]
1. content: 주어진 단어와 의미에 부합하는 자연스러운 전체 문장입니다. (※ 절대 규칙: 문장의 길이는 공백을 포함하여 무조건 20자를 넘지 않아야 합니다.
2. highlight: 문장 내에서 대상 단어가 변형되거나 활용되어 쓰인 '정확한 어절'입니다. 포함된 띄어쓰기나 구두점 없이 해당 어절만 추출하세요.

{format_instructions}
"""

HUMAN_TEMPLATE = """
[단어]
{word}

[의미]
{definition}
"""


def generate_sentences_with_llm(
    word: str, 
    definition: str, 
    batch_size: int, 
    category: str | None = None,
    tone: str | None = None,
    random_words: List[str] | None = None,
) -> List[GeneratedSentence]:
    """주어진 단어와 의미를 바탕으로 LLM을 활용해 예문 배치를 생성합니다."""
    llm = get_standard_llm(max_retries=3, temperature=0.7)
    
    parser = PydanticOutputParser(pydantic_object=SentenceBatchResult)
    retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=llm, max_retries=3)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_INSTRUCTION),
        ("human", HUMAN_TEMPLATE),
    ])

    # 고정 카테고리와 동적 랜덤 단어를 결합한 지침 생성
    cat_text = f"주어진 키워드('{category}') 상황이나 배경" if category else "다양한 상황이나 배경"
    word_text = f" 특히, 다음 단어들에서 영감을 받아 문장의 소재를 다채롭게 확장하세요: [{', '.join(random_words)}]" if random_words else ""
    cat_instruction = f"\n[상황/배경 및 소재 지침]\n{cat_text}에 자연스럽게 등장할 법한 문장으로 생성하세요.{word_text}"
    tone_instruction = f"\n[문체/톤 지침]\n반드시 '{tone}' 스타일로 작성하여 문장의 다양성을 높이세요." if tone else ""

    prompt_value = prompt.invoke({
        "word": word,
        "definition": definition,
        "batch_size": batch_size,
        "category_instruction": cat_instruction,
        "tone_instruction": tone_instruction,
        "format_instructions": parser.get_format_instructions(),
    })
    
    response = llm.invoke(prompt_value)
    
    # Retry Logic with explicit prompt passing
    final_data = retry_parser.parse_with_prompt(cast(str, response.content), prompt_value)
    
    return cast(SentenceBatchResult, final_data).sentences


def main():
    parser = argparse.ArgumentParser(description="Generate sentences from meanings")
    parser.add_argument("--meaning-id", required=True, help="Target Meaning ID")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of sentences to generate per batch")
    parser.add_argument("--iterations", type=int, default=1, help="Number of times to repeat the batch generation")
    parser.add_argument("--category", type=str, default=None, help="문장 생성 상황/배경 키워드 (선택)")
    
    args = parser.parse_args()

    # Repository 초기화 및 데이터 로드
    repo = DataRepository()
    meanings = repo.get_all("meanings")
    sentences = repo.get_all("sentences")

    # Target Meaning 조회
    target_meaning = next((m for m in meanings if m["id"] == args.meaning_id), None)
    if not target_meaning:
        logger.error(f"Meaning with id '{args.meaning_id}' not found.")
        sys.exit(1)

    word = target_meaning.get("word")
    definition = target_meaning.get("definition")
    
    logger.info(f"Target Meaning Found - Word: '{word}', Definition: '{definition}'")
    logger.info(f"Configuration - Batch Size: {args.batch_size}, Iterations: {args.iterations}")

    total_generated = 0
    all_generated_words = set() # 이전 생성 문장 누적용 리스트
    
    # 다양성을 위한 문체/톤 풀(Pool)
    tones = ["공손한 존댓말(~습니다/요)", "친밀한 반말(~어/야)", "뉴스/다큐 보도 스타일(~다/음)", "감성적인 에세이 투", "비즈니스 이메일투", "냉소적인 독백", "의문문/질문형", "청유형/명령형"]

    # 지정된 반복 횟수(iterations)만큼 배치 단위 문장 생성
    for i in range(args.iterations):
        logger.info(f"--- Starting Iteration {i+1}/{args.iterations} ---")

        # 이번 이터레이션에 사용할 랜덤 톤 선택
        # current_tone = random.choice(tones)
        current_tone = tones[0]
        logger.info(f"Selected Tone for this iteration: {current_tone}")

        # 누적된 단어 풀에서 최대 5개를 무작위 추출
        word_pool = list(all_generated_words)
        sampled_words = random.sample(word_pool, min(5, len(word_pool))) if word_pool else []
        logger.info(f"Sampled Words for this iteration: {sampled_words}")
        
        try:
            generated_items = generate_sentences_with_llm(
                word=word, 
                definition=definition, 
                batch_size=args.batch_size,
                category=args.category,
                tone=current_tone,
                random_words=sampled_words
            )
            
            new_sentences = []
            for item in generated_items:
                # Sentence 모델을 통해 데이터 구조 및 타입 검증
                sentence_model = Sentence(
                    id=generate_short_id(),
                    meaning_id=args.meaning_id,
                    content=item.content,
                    highlight=item.highlight
                )
                new_sentences.append(sentence_model.model_dump())

                # 생성된 문장을 띄어쓰기 단위로 분리하여 단어 풀에 추가
                all_generated_words.update(item.content.split())
            
            # Repository 메모리에 추가 후 파일에 원자적(Atomic) 저장
            sentences.extend(new_sentences)
            repo.save_all()
            
            batch_count = len(new_sentences)
            total_generated += batch_count
            logger.info(f"Iteration {i+1} completed: {batch_count} sentences generated and saved.")
            
        except Exception as e:
            logger.error(f"Error during sentence generation at iteration {i+1}: {e}")

    logger.info(f"Process complete. A total of {total_generated} sentences were generated for meaning-id '{args.meaning_id}'.")


if __name__ == "__main__":
    main()
