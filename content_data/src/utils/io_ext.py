import uuid

def generate_short_id() -> str:
    """Generates an 8-character long short UUID."""
    return uuid.uuid4().hex[:8]
