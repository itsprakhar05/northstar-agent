import json
from typing import Any, Callable

from app.booking import calendar
from app.schemas import (
    BookSiteVisitArgs,
    EscalateArgs,
    OptOutArgs,
    ScheduleCallbackArgs,
)

_CALLBACKS: list[dict[str, Any]] = []
_OPT_OUTS: list[dict[str, Any]] = []
_ESCALATIONS: list[dict[str, Any]] = []


def book_site_visit(
    customer_name: str,
    phone: str,
    configuration: str,
    visit_date: str,
    visit_time: str,
) -> dict[str, Any]:
    result = calendar.book(configuration, visit_date, visit_time)
    payload = result.model_dump()
    payload["customer_name"] = customer_name
    payload["phone"] = phone
    return payload


def schedule_callback(
    customer_name: str, phone: str, when: str
) -> dict[str, Any]:
    record = {
        "ok": True,
        "customer_name": customer_name,
        "phone": phone,
        "when": when,
    }
    _CALLBACKS.append(record)
    return record


def opt_out(reason: str = "customer_request") -> dict[str, Any]:
    record = {"ok": True, "stopped": True, "reason": reason}
    _OPT_OUTS.append(record)
    return record


def escalate_to_human(
    reason: str, phone: str | None = None
) -> dict[str, Any]:
    record = {"ok": True, "escalated": True, "reason": reason, "phone": phone}
    _ESCALATIONS.append(record)
    return record


HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "book_site_visit": book_site_visit,
    "schedule_callback": schedule_callback,
    "opt_out": opt_out,
    "escalate_to_human": escalate_to_human,
}

ARG_MODELS = {
    "book_site_visit": BookSiteVisitArgs,
    "schedule_callback": ScheduleCallbackArgs,
    "opt_out": OptOutArgs,
    "escalate_to_human": EscalateArgs,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "book_site_visit",
            "description": "Book a Northstar One site visit after the customer confirms the slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "configuration": {
                        "type": "string",
                        "enum": ["2bhk", "3bhk"],
                    },
                    "visit_date": {
                        "type": "string",
                        "description": "YYYY-MM-DD",
                    },
                    "visit_time": {
                        "type": "string",
                        "description": "HH:MM 24-hour",
                    },
                },
                "required": [
                    "customer_name",
                    "phone",
                    "configuration",
                    "visit_date",
                    "visit_time",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_callback",
            "description": "Schedule a later call when the customer is busy or asks to be contacted later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "when": {"type": "string"},
                },
                "required": ["customer_name", "phone", "when"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "opt_out",
            "description": "Stop all further contact when the customer asks not to be contacted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Hand the lead to a human colleague only when the customer asks for a person. Omit phone if they have not given a number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "phone": {
                        "type": ["string", "null"],
                        "description": "Customer phone if known. Use null or omit when unknown. Never invent.",
                    },
                },
                "required": ["reason"],
            },
        },
    },
]


def run_tool(name: str, arguments_json: str) -> str:
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"ok": False, "reason": f"Unknown tool: {name}"})
    raw = json.loads(arguments_json or "{}")
    if not isinstance(raw, dict):
        return json.dumps({"ok": False, "reason": "Invalid tool arguments."})
    raw = {key: value for key, value in raw.items() if value is not None}
    args = ARG_MODELS[name].model_validate(raw)
    result = handler(**args.model_dump())
    return json.dumps(result)


ENDING_TOOLS = {"opt_out", "escalate_to_human"}
