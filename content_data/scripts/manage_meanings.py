# 실행 명령어: uv run -m scripts.manage_meanings --action [create|read|update|delete] [--id <id>] [--word <word>] [--definition <definition>]
import argparse
from src.utils.logger import logger
from src.utils.io_ext import generate_short_id
from src.utils.cli_ext import prompt_if_missing
from src.models import Meaning, DataRepository

def main():
    parser = argparse.ArgumentParser(description="Manage Meaning data domain")
    parser.add_argument("--action", choices=["create", "read", "update", "delete"], required=True)
    parser.add_argument("--id", help="Target Meaning ID")
    parser.add_argument("--word", help="Referenced Word (PK)")
    parser.add_argument("--definition", help="Definition string")
    
    args = parser.parse_args()
    repo = DataRepository()
    words = repo.get_all("words")
    meanings = repo.get_all("meanings")
    
    if args.action == "create":
        w_val = prompt_if_missing(args.word, "Enter Word (PK)")
        if not any(w["word"] == w_val for w in words):
            logger.error(f"Word '{w_val}' does not exist. Cannot create Meaning.")
            return
            
        df = prompt_if_missing(args.definition, "Enter Meaning definition")
        m_id = generate_short_id()
        if w_val is None or df is None:
            logger.error("Word and definition are required to create a Meaning.")
            return
        
        model = Meaning(id=m_id, word=w_val, definition=df)
        meanings.append(model.model_dump())
        repo.save_all()
        logger.info(f"Created Meaning: {model.model_dump_json()}")
        
    elif args.action == "read":
        if args.id:
            found = next((m for m in meanings if m["id"] == args.id), None)
            if found: logger.info(f"Read: {found}")
            else: logger.error(f"Meaning with id {args.id} not found.")
        else:
            logger.info(f"All Meanings: {meanings}")
            
    elif args.action == "update":
        target_id = prompt_if_missing(args.id, "Enter Meaning ID to update")
        target = next((m for m in meanings if m["id"] == target_id), None)
        if not target or target_id is None:
            logger.error(f"Meaning with id {target_id} not found.")
            return
            
        w_val = args.word or target["word"]
        if args.word and not any(w["word"] == w_val for w in words):
            logger.error(f"Word '{w_val}' does not exist."); return
            
        df = prompt_if_missing(args.definition, f"Enter definition (current: {target['definition']})")
        if df is None:
            logger.error("Definition is required to update a Meaning.")
            return
        
        model = Meaning(id=target_id, word=w_val, definition=df)
        target.update(model.model_dump())
        repo.save_all()
        logger.info(f"Updated Meaning: {target}")
        
    elif args.action == "delete":
        target_id = prompt_if_missing(args.id, "Enter Meaning ID to delete")
        target = next((m for m in meanings if m["id"] == target_id), None)
        if not target:
            logger.error(f"Meaning with id {target_id} not found."); return
        
        sentences = repo.get_all("sentences")
        related_sentences = [s for s in sentences if s["meaning_id"] == target_id]
        
        if related_sentences:
            logger.warning(f"Cascading deletion: deleting {len(related_sentences)} associated Sentences.")
            
        meanings[:] = [m for m in meanings if m["id"] != target_id]
        sentences[:] = [s for s in sentences if s["meaning_id"] != target_id]
        
        repo.save_all()
        logger.info(f"Deleted Meaning {target_id} and its associated Sentences.")

if __name__ == "__main__":
    main()
