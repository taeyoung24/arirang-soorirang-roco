from pydantic import SecretStr
from typing import Optional
from langchain_openai import ChatOpenAI
from settings import OPENROUTER_API_KEY


API_KEY = SecretStr(OPENROUTER_API_KEY)
BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {
    "HTTP-Referer": "https://arirang-soorirang.roco/",
    "X-Title": "Arirang Soorirang",
}

def get_standard_llm(
    *, 
    max_completion_tokens: Optional[int] = None,
    max_retries: Optional[int] = None,
    temperature: Optional[float] = None,
    verbose: bool = False,
) -> ChatOpenAI:
    return ChatOpenAI(
        model="google/gemini-3-flash-preview",
        api_key=API_KEY,
        base_url=BASE_URL,
        max_completion_tokens=max_completion_tokens,
        max_retries=max_retries,
        verbose=verbose,
        temperature=temperature,
        default_headers=HEADERS,
    )
