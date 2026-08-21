import json
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from app.config import PROMPTS_DIR
from app.llm import complete, model_text
from app.memory import SessionStore
from app.schemas import Analytics, Response

_EXTRACT_PATH = PROMPTS_DIR / "analytics_extract.md"
_CAPTURE_PATH = PROMPTS_DIR / "response_capture.md"


def extract_analytics(
    client: OpenAI, store: SessionStore, session_id: str
) -> Analytics:
    transcript = _transcript(store.history(session_id))
    prompt = Path(_EXTRACT_PATH).read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": transcript or "(empty conversation)"},
    ]
    try:
        response = complete(
            client, messages, temperature=0, json_object=True
        )
        raw = model_text(response.choices[0].message.content) or "{}"
    except Exception as exc:  # fallback if the API rejects json validation
        # try to extract any useful generated text from the exception
        failed = None
        try:
            failed = getattr(exc, "error", None) or getattr(exc, "errors", None)
            if isinstance(failed, dict):
                failed = failed.get("failed_generation") or failed.get("message")
        except Exception:
            failed = None

        if failed:
            raw = str(failed)
        else:
            # second attempt: ask for a plain-text completion and try to parse it
            try:
                fallback = complete(client, messages, temperature=0, json_object=False)
                raw = model_text(fallback.choices[0].message.content) or "{}"
            except Exception:
                return Analytics(notes="Could not parse analytics from this conversation.")
    try:
        return Analytics.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError):
        return Analytics(notes="Could not parse analytics from this conversation.")


def _transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for message in messages:
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = (message.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def capture_response(client: OpenAI, message: str) -> Response:
    """Extract key information from a single user message."""
    prompt = Path(_CAPTURE_PATH).read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": message},
    ]
    try:
        response = complete(
            client, messages, temperature=0, json_object=True
        )
        raw = model_text(response.choices[0].message.content) or "{}"
    except Exception as exc:
        # fallback if the API rejects json validation
        failed = None
        try:
            failed = getattr(exc, "error", None) or getattr(exc, "errors", None)
            if isinstance(failed, dict):
                failed = failed.get("failed_generation") or failed.get("message")
        except Exception:
            failed = None

        if failed:
            raw = str(failed)
        else:
            try:
                fallback = complete(client, messages, temperature=0, json_object=False)
                raw = model_text(fallback.choices[0].message.content) or "{}"
            except Exception:
                return Response(message=message, notes="Could not capture response data.")
    try:
        return Response.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError):
        return Response(message=message, notes="Could not parse response data.")
