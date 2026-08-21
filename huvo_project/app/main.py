from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import APIError

from app.agent import run_turn
from app.analytics import extract_analytics, capture_response
from app.config import STATIC_DIR
from app.llm import build_client
from app.memory import store
from app.schemas import Analytics, ChatReply, ChatRequest, EndRequest, ReopenSessionRequest, UpdateAnalyticsRequest, SessionDataResponse, EndConversationResponse

app = FastAPI(title="Northstar Homes sales bot")
_client = None


def get_client():
    global _client
    if _client is None:
        _client = build_client()
    return _client


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatReply)
def chat(request: ChatRequest) -> ChatReply:
    if store.is_ended(request.session_id):
        return ChatReply(
            reply="This conversation has already ended. Start a new chat to begin again.",
            ended=True,
        )
    try:
        # Capture information from this user message
        response_capture = capture_response(get_client(), request.message)
        store.add_response(request.session_id, response_capture.model_dump())
        
        reply, ended = run_turn(
            get_client(),
            store,
            request.session_id,
            request.message,
            request.channel,
        )
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=getattr(exc, "message", None) or str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if ended:
        store.mark_ended(request.session_id)
    return ChatReply(reply=reply, ended=ended)


@app.post("/end", response_model=EndConversationResponse)
def end_conversation(request: EndRequest) -> EndConversationResponse:
    """End conversation and generate analytics internally (not shown to user).
    
    Analytics are extracted from the conversation and saved to JSON file for backend use.
    The user does not see the analytics - they only receive a confirmation message.
    """
    store.mark_ended(request.session_id)
    try:
        analytics = extract_analytics(get_client(), store, request.session_id)
        # Save analytics to JSON file (internal use only, not shown to user)
        store.set_analytics(request.session_id, analytics.model_dump())
        return EndConversationResponse(
            message="Thank you for your time. We will be in touch soon.",
            session_id=request.session_id
        )
    except APIError as exc:
        raise HTTPException(
            status_code=502,
            detail=getattr(exc, "message", None) or str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/reopen-session")
def reopen_session(request: ReopenSessionRequest) -> dict[str, str]:
    """Reopen a closed session for continued conversation or information updates."""
    store.reopen_session(request.session_id)
    return {
        "message": f"Session {request.session_id} reopened. You can continue chatting or provide more information."
    }


@app.get("/session/{session_id}", response_model=SessionDataResponse)
def get_session_data(session_id: str) -> SessionDataResponse:
    """Retrieve saved session data including messages and analytics."""
    data = store.get_session_data(session_id)
    return SessionDataResponse(**data)


@app.post("/update-analytics", response_model=Analytics)
def update_analytics(request: UpdateAnalyticsRequest) -> Analytics:
    """Manually update analytics for a session."""
    # Merge with existing analytics if available
    existing = store._session(request.session_id).get("analytics") or {}
    updated = {**existing, **request.analytics}
    store.set_analytics(request.session_id, updated)
    return Analytics.model_validate(updated)
