import os
from openai import OpenAI


def is_available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", "placeholder"),
    )
