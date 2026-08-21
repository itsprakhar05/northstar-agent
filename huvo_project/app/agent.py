from pathlib import Path

from openai import OpenAI

from app.config import (
    CHAT_TEMPERATURE,
    MAX_HISTORY_MESSAGES,
    MAX_TOOL_ROUNDS,
    PROMPTS_DIR,
)
from app.guardrails import booking_succeeded, grounded_reply
from app.llm import complete, model_text
from app.memory import SessionStore
from app.schemas import Channel
from app.tools import ENDING_TOOLS, TOOL_SCHEMAS, run_tool

_PROMPT_PATH = PROMPTS_DIR / "northstar_sales_agent.md"
FALLBACK_REPLY = (
    "I am having a little trouble right now. I can connect you to a colleague if you share a number."
)


def load_system_prompt(channel: Channel) -> str:
    text = Path(_PROMPT_PATH).read_text(encoding="utf-8")
    return text.replace("{{CHANNEL}}", channel)


def run_turn(
    client: OpenAI,
    store: SessionStore,
    session_id: str,
    user_text: str,
    channel: Channel,
) -> tuple[str, bool]:
    store.set_channel(session_id, channel)
    store.append(session_id, {"role": "user", "content": user_text})
    messages = _build_messages(store, session_id, channel)
    for _ in range(MAX_TOOL_ROUNDS):
        response = complete(
            client, messages, tools=TOOL_SCHEMAS, temperature=CHAT_TEMPERATURE
        )
        choice = response.choices[0].message
        tool_calls = choice.tool_calls or []
        if not tool_calls:
            reply = model_text(choice.content) or FALLBACK_REPLY
            reply = grounded_reply(
                reply, _user_texts(store, session_id), booking_succeeded(messages)
            )
            store.append(session_id, {"role": "assistant", "content": reply})
            return reply, store.is_ended(session_id)
        assistant_msg = _assistant_tool_message(choice)
        store.append(session_id, assistant_msg)
        messages.append(assistant_msg)
        for call in tool_calls:
            result = run_tool(call.function.name, call.function.arguments)
            tool_msg = {
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            }
            store.append(session_id, tool_msg)
            messages.append(tool_msg)
            # Agent can call ending tools (escalate_to_human, opt_out), but 
            # conversation only ends when user explicitly clicks /end button
    reply = _final_reply(client, messages)
    reply = grounded_reply(
        reply, _user_texts(store, session_id), booking_succeeded(messages)
    )
    store.append(session_id, {"role": "assistant", "content": reply})
    return reply, store.is_ended(session_id)


def _user_texts(store: SessionStore, session_id: str) -> list[str]:
    return [
        message["content"]
        for message in store.history(session_id)
        if message.get("role") == "user" and message.get("content")
    ]


def _build_messages(
    store: SessionStore, session_id: str, channel: Channel
) -> list[dict]:
    history = store.history(session_id)[-MAX_HISTORY_MESSAGES:]
    return [
        {"role": "system", "content": load_system_prompt(channel)},
        *history,
    ]


def _assistant_tool_message(choice) -> dict:
    return {
        "role": "assistant",
        "content": choice.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in choice.tool_calls
        ],
    }


def _final_reply(client: OpenAI, messages: list[dict]) -> str:
    response = complete(client, messages, temperature=CHAT_TEMPERATURE)
    return model_text(response.choices[0].message.content) or FALLBACK_REPLY
