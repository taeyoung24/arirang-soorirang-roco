# 실행 명령어: uv run -m scripts.fetch_meanings --word <word>
import sys
import argparse
import requests
from bs4 import BeautifulSoup

from src.utils.logger import logger
from src.utils.io_ext import generate_short_id
from src.models import Meaning, Word, DataRepository

def fetch_definitions(word: str) -> list:
    url = "https://stdict.korean.go.kr/search/searchResult.do"
    definitions = []
    page_index = 1
    
    while True:
        payload = {
            "board_no": "",
            "pageSize": "50",
            "pageIndex": str(page_index),
            "focus_name": "",
            "searchKeyword": word
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"네트워크 요청 중 오류가 발생했습니다 (페이지 {page_index}): {e}")
            sys.exit(1)
            
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            result_ul = soup.find("ul", class_="result")
            
            if not result_ul:
                break # 결과 없음 또는 구조 다름
                
            items = result_ul.find_all("li", recursive=False)
            if not items:
                break # 리스트 비어있음
                
            for li in items:
                data_line = li.find("font", class_="dataLine")
                if data_line:
                    definitions.append(data_line.get_text(strip=True))
                    
            # 가져온 개수가 요청한 pageSize(50)보다 적으면 마지막 페이지로 간주
            if len(items) < 50:
                break
                
            page_index += 1
            
        except Exception as e:
            logger.error(f"HTML 파싱 중 오류가 발생했습니다 (페이지 {page_index}): {e}")
            sys.exit(1)
            
    return definitions

def main():
    parser = argparse.ArgumentParser(description="Fetch meanings from National Institute of Korean Language")
    parser.add_argument("--word", required=True, help="Target word to search and insert")
    
    args = parser.parse_args()
    
    # 사전에 단어가 존재하는지 먼저 검증 (오타 방지)
    repo = DataRepository()
    words = repo.get_all("words")
    
    if not any(w["word"] == args.word for w in words):
        logger.error(f"오류: 검색하려는 단어 '{args.word}'(이)가 기초 데이터베이스에 존재하지 않습니다.")
        logger.info(f"해결: 'uv run -m scripts.manage_words --action create --word \"{args.word}\"' 명령어로 먼저 단어를 등록해 주세요.")
        sys.exit(1)
    
    logger.info(f"'{args.word}' 단어의 뜻을 국립국어원에서 검색합니다...")
    definitions = fetch_definitions(args.word)
    
    if not definitions:
        logger.warning(f"검색된 결과가 없습니다: '{args.word}'")
        sys.exit(0)
        
    logger.info(f"총 {len(definitions)}개의 뜻을 찾았습니다.")
    
    try:
        # 데이터 원본 수정은 마지막에 일괄적으로 처리 (원자성 보장)
        meanings = repo.get_all("meanings")
            
        new_meanings_count = 0
        for df in definitions:
            m_id = generate_short_id()
            model = Meaning(id=m_id, word=args.word, definition=df)
            meanings.append(model.model_dump())
            new_meanings_count += 1
            
        repo.save_all()
        logger.info(f"총 {new_meanings_count}개의 새로운 Meaning 데이터가 일괄 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터베이스 저장 중 오류가 발생했습니다: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
