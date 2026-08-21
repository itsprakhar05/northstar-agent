from time import sleep
import re

from openai import OpenAI, RateLimitError

from app.config import GROQ_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, require_api_key

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def build_client() -> OpenAI:
    require_api_key()
    return OpenAI(api_key=GROQ_API_KEY, base_url=OPENAI_BASE_URL)


def complete(
    client: OpenAI,
    messages: list[dict],
    *,
    tools: list[dict] | None = None,
    temperature: float = 0.6,
    json_object: bool = False,
):
    kwargs: dict = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if json_object:
        kwargs["response_format"] = {"type": "json_object"}
    last_error: RateLimitError | None = None
    for attempt in range(3):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as exc:
            last_error = exc
            sleep(2**attempt)
    raise last_error


def model_text(content: str | None) -> str:
    return _THINK_BLOCK.sub("", content or "").strip()
