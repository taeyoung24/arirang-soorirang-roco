# 실행 명령어: uv run -m scripts.manage_sentences --action [create|read|update|delete] [--id <id>] [--meaning-id <meaning-id>] [--content <content>] [--highlight <highlight>]
import argparse
from src.utils.logger import logger
from src.utils.io_ext import generate_short_id
from src.utils.cli_ext import prompt_if_missing
from src.models import Sentence, DataRepository

def main():
    parser = argparse.ArgumentParser(description="Manage Sentence data domain")
    parser.add_argument("--action", choices=["create", "read", "update", "delete"], required=True)
    parser.add_argument("--id", help="Target ID")
    parser.add_argument("--meaning-id", dest="meaning_id", help="Referenced Meaning ID")
    parser.add_argument("--content", help="Sentence content")
    parser.add_argument("--highlight", help="Highlighted part of the sentence")
    
    args = parser.parse_args()
    repo = DataRepository()
    meanings = repo.get_all("meanings")
    sentences = repo.get_all("sentences")
    
    if args.action == "create":
        m_id = prompt_if_missing(args.meaning_id, "Enter Meaning ID")
        if not any(m["id"] == m_id for m in meanings):
            logger.error(f"Meaning with id {m_id} does not exist.")
            return
            
        ct = prompt_if_missing(args.content, "Enter Sentence content")
        hl = prompt_if_missing(args.highlight, "Enter Highlight part")
        s_id = generate_short_id()
        model = Sentence(id=s_id, meaning_id=m_id, content=ct, highlight=hl)
        sentences.append(model.model_dump())
        repo.save_all()
        logger.info(f"Created Sentence: {model.model_dump_json()}")
        
    elif args.action == "read":
        if args.id:
            found = next((s for s in sentences if s["id"] == args.id), None)
            if found: logger.info(f"Read: {found}")
            else: logger.error(f"Sentence with id {args.id} not found.")
        else:
            logger.info(f"All Sentences: {sentences}")
            
    elif args.action == "update":
        target_id = prompt_if_missing(args.id, "Enter Sentence ID to update")
        target = next((s for s in sentences if s["id"] == target_id), None)
        if not target:
            logger.error(f"Sentence with id {target_id} not found."); return
            
        m_id = args.meaning_id or target["meaning_id"]
        if args.meaning_id and not any(m["id"] == m_id for m in meanings):
            logger.error(f"Meaning with id {m_id} does not exist."); return
            
        ct = prompt_if_missing(args.content, f"Enter content (current: {target['content']})")
        hl = prompt_if_missing(args.highlight, f"Enter highlight (current: {target['highlight']})")
        
        model = Sentence(id=target_id, meaning_id=m_id, content=ct, highlight=hl)
        target.update(model.model_dump())
        repo.save_all()
        logger.info(f"Updated Sentence: {target}")
        
    elif args.action == "delete":
        target_id = prompt_if_missing(args.id, "Enter Sentence ID to delete")
        target = next((s for s in sentences if s["id"] == target_id), None)
        if not target:
            logger.error(f"Sentence with id {target_id} not found."); return
            
        sentences[:] = [s for s in sentences if s["id"] != target_id]
        repo.save_all()
        logger.info(f"Deleted Sentence {target_id}.")

if __name__ == "__main__":
    main()
