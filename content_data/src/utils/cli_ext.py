from typing import Optional

def prompt_if_missing(value: Optional[str], prompt_msg: str, required: bool = True) -> Optional[str]:
    """Helper to prompt for missing CLI arguments interactively."""
    if value is not None and str(value).strip() != "":
        return str(value).strip()
    if required:
        while True:
            val = input(f"{prompt_msg} (Required): ").strip()
            if val:
                return val
    else:
        val = input(f"{prompt_msg} (Optional, press enter to skip): ").strip()
        return val if val else None

def prompt_for_list(values: Optional[list], prompt_msg: str) -> list:
    """Helper to prompt for a list (comma or space separated) interactively."""
    if values is not None and isinstance(values, list) and len(values) > 0:
        return [str(v).strip() for v in values if str(v).strip()]
    while True:
        val = input(f"{prompt_msg} (Space or comma separated): ").strip()
        if val:
            val = val.replace(',', ' ')
            items = [item for item in val.split(' ') if item]
            if items:
                return items
    return []
