import json
import re

SAFE_REPLY = (
    "Mere paas sirf confirmed facts hain: Northstar One, Sector 79 Gurugram, "
    "2 BHK 1.35 crore onwards, 3 BHK 1.75 crore onwards. Baaki details invent nahi kar sakta. "
    "Kya main aapko colleague se connect karun?"
)

_ALLOWED_CRORE = {"1.35", "1.75"}
_SPECIAL_PRICE = re.compile(
    r"(\d+\s*%|\bspecial (price|rate|offer)\b|\blimited period\b|\boffer price\b)",
    re.I,
)
_POSSESSION_DATE = re.compile(
    r"\bpossession\b.{0,40}("
    r"20\d{2}|january|february|march|april|may|june|"
    r"july|august|september|october|november|december"
    r")",
    re.I,
)
_BOOKED = re.compile(r"\b(booked|confirmation id|confirm ho gaya|visit confirm)\b", re.I)
_CRORE = re.compile(r"(\d+(?:\.\d+)?)\s*crore", re.I)
_USER_NUMBER = re.compile(r"(\d+(?:\.\d+)?)")


def grounded_reply(reply: str, user_messages: list[str], booking_ok: bool) -> str:
    if _is_ungrounded(reply, user_messages, booking_ok):
        return SAFE_REPLY
    return reply


def _is_ungrounded(reply: str, user_messages: list[str], booking_ok: bool) -> bool:
    if _SPECIAL_PRICE.search(reply):
        return True
    if _POSSESSION_DATE.search(reply):
        return True
    if _BOOKED.search(reply) and not booking_ok:
        return True
    allowed = set(_ALLOWED_CRORE)
    for text in user_messages:
        allowed.update(_USER_NUMBER.findall(text))
    for amount in _CRORE.findall(reply):
        if amount not in allowed:
            return True
    return False


def booking_succeeded(messages: list[dict]) -> bool:
    for message in reversed(messages):
        if message.get("role") != "tool":
            continue
        try:
            payload = json.loads(message.get("content") or "{}")
        except json.JSONDecodeError:
            continue
        if payload.get("ok") and payload.get("confirmation_id"):
            return True
    return False
