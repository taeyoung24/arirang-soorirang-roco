# 실행 명령어: uv run -m scripts.manage_quizzes --action [create|read|update|delete] [--id <id>] [--instruction <instruction>] [--target-id <target-id>] [--option-ids <id1> <id2> ...]
import argparse
from src.utils.logger import logger
from src.utils.io_ext import generate_short_id
from src.utils.cli_ext import prompt_if_missing, prompt_for_list
from src.models import Quiz, DataRepository

def main():
    parser = argparse.ArgumentParser(description="Manage Quiz data domain")
    parser.add_argument("--action", choices=["create", "read", "update", "delete"], required=True)
    parser.add_argument("--id", help="Target ID")
    parser.add_argument("--instruction", help="Quiz instruction/question")
    parser.add_argument("--target-id", dest="target_id", help="Target answer ID")
    parser.add_argument("--option-ids", dest="option_ids", nargs='+', help="List of option IDs")
    
    args = parser.parse_args()
    repo = DataRepository()
    quizzes = repo.get_all("quizzes")
    
    if args.action == "create":
        inst = prompt_if_missing(args.instruction, "Enter Quiz instruction")
        t_id = prompt_if_missing(args.target_id, "Enter Target ID")
        op_ids = prompt_for_list(args.option_ids, "Enter Option IDs")
        
        q_id = generate_short_id()
        if inst is None or t_id is None or not op_ids:
            logger.error("Instruction, target ID, and at least one option ID are required to create a Quiz.")
            return
        
        model = Quiz(id=q_id, instruction=inst, target_id=t_id, option_ids=op_ids)
        quizzes.append(model.model_dump())
        repo.save_all()
        logger.info(f"Created Quiz: {model.model_dump_json()}")
        
    elif args.action == "read":
        if args.id:
            found = next((q for q in quizzes if q["id"] == args.id), None)
            if found: logger.info(f"Read: {found}")
            else: logger.error(f"Quiz with id {args.id} not found.")
        else:
            logger.info(f"All Quizzes: {quizzes}")
            
    elif args.action == "update":
        target_id = prompt_if_missing(args.id, "Enter Quiz ID to update")
        target = next((q for q in quizzes if q["id"] == target_id), None)
        if not target or target_id is None:
            logger.error(f"Quiz with id {target_id} not found."); return
            
        inst = prompt_if_missing(args.instruction, f"Enter instruction (current: {target['instruction']})")
        t_id = prompt_if_missing(args.target_id, f"Enter target ID (current: {target['target_id']})")
        # Ensure we prompt correctly for options if not passed
        if args.option_ids is not None and len(args.option_ids) > 0:
            op_ids = args.option_ids
        else:
            op_ids = prompt_for_list(None, f"Enter Option IDs (current: {target['option_ids']})")

        if inst is None or t_id is None:
            logger.error("Instruction, target ID, and at least one option ID are required to update a Quiz.")
            return
            
        model = Quiz(id=target_id, instruction=inst, target_id=t_id, option_ids=op_ids)
        target.update(model.model_dump())
        repo.save_all()
        logger.info(f"Updated Quiz: {target}")
        
    elif args.action == "delete":
        target_id = prompt_if_missing(args.id, "Enter Quiz ID to delete")
        target = next((q for q in quizzes if q["id"] == target_id), None)
        if not target:
            logger.error(f"Quiz with id {target_id} not found."); return
            
        quizzes[:] = [q for q in quizzes if q["id"] != target_id]
        repo.save_all()
        logger.info(f"Deleted Quiz {target_id}.")

if __name__ == "__main__":
    main()
