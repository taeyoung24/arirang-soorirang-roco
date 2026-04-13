# 실행 명령어: uv run -m scripts.manage_words --action [create|read|update|delete] [--word <word>] [--new-word <new-word>]
import argparse
from src.utils.logger import logger
from src.utils.cli_ext import prompt_if_missing
from src.models import Word, DataRepository

def main():
    parser = argparse.ArgumentParser(description="Manage Word data domain")
    parser.add_argument("--action", choices=["create", "read", "update", "delete"], required=True, help="CRUD action to perform")
    parser.add_argument("--word", help="Target word (PK)")
    parser.add_argument("--new-word", dest="new_word", help="New word string for update")
    
    args = parser.parse_args()
    
    repo = DataRepository()
    words = repo.get_all("words")
    
    if args.action == "create":
        word_val = prompt_if_missing(args.word, "Enter new word")
        
        # Check uniqueness
        if any(w["word"] == word_val for w in words):
            logger.error(f"Word '{word_val}' already exists.")
            return
            
        new_word = Word(word=word_val)
        words.append(new_word.model_dump())
        repo.save_all()
        logger.info(f"Created new Word: {new_word.model_dump_json()}")
        
    elif args.action == "read":
        if args.word:
            found = [w for w in words if w["word"] == args.word]
            if found:
                logger.info(f"Read Word: {found[0]}")
            else:
                logger.error(f"Word '{args.word}' not found.")
        else:
            logger.info(f"All Words: {words}")
            
    elif args.action == "update":
        target_word = prompt_if_missing(args.word, "Enter target Word to update")
        target = next((w for w in words if w["word"] == target_word), None)
        if not target:
            logger.error(f"Word '{target_word}' not found.")
            return
            
        new_val = prompt_if_missing(args.new_word, f"Enter new word to replace '{target_word}'")
        
        # Uniqueness check for new_val
        if target_word != new_val and any(w["word"] == new_val for w in words):
            logger.error(f"Word '{new_val}' already exists. Cannot rename.")
            return
        
        target["word"] = new_val
        
        # Cascade Update on Meanings
        meanings = repo.get_all("meanings")
        affected_meanings = [m for m in meanings if m["word"] == target_word]
        for m in affected_meanings:
            m["word"] = new_val
            
        if affected_meanings:
            logger.warning(f"Cascading update: changed word in {len(affected_meanings)} associated Meanings.")
            
        repo.save_all()
        logger.info(f"Updated Word from '{target_word}' to '{new_val}'.")
        
    elif args.action == "delete":
        target_word = prompt_if_missing(args.word, "Enter target Word to delete")
        target = next((w for w in words if w["word"] == target_word), None)
        if not target:
            logger.error(f"Word '{target_word}' not found.")
            return
            
        meanings = repo.get_all("meanings")
        sentences = repo.get_all("sentences")
        
        related_meanings = [m for m in meanings if m["word"] == target_word]
        meaning_ids = [m["id"] for m in related_meanings]
        
        if related_meanings:
            logger.warning(f"Cascading deletion: deleting {len(related_meanings)} associated Meanings and their Sentences.")
            
        words[:] = [w for w in words if w["word"] != target_word]
        meanings[:] = [m for m in meanings if m["word"] != target_word]
        sentences[:] = [s for s in sentences if s["meaning_id"] not in meaning_ids]
        
        repo.save_all()
        logger.info(f"Deleted Word '{target_word}' and its associated entities.")

if __name__ == "__main__":
    main()
