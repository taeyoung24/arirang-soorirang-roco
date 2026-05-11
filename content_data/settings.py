import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.environ["OPENROUTER_API_KEY"]
