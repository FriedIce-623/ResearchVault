import asyncio
import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.claude_service import ask_question, ask_question_stream
from app.services.embeddings import retrieve

router = APIRouter(prefix="/api", tags=["Ask"])

# session_id -> list of {"role": ..., "content": ...} message dicts
_sessions: dict[str, list] = {}
_MAX_HISTORY = 10


class AskRequest(BaseModel):
    question: str
    session_id: str | None = None


@router.post("/ask")
async def ask(req: AskRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = _sessions.get(session_id, [])
    chunks = await retrieve(req.question)

    result = await asyncio.to_thread(ask_question, req.question, chunks, history)

    updated = history + [
        {"role": "user", "content": req.question},
        {"role": "assistant", "content": result["answer"]},
    ]
    _sessions[session_id] = updated[-_MAX_HISTORY:]

    return {**result, "session_id": session_id}


@router.post("/ask/stream")
async def ask_stream(req: AskRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = _sessions.get(session_id, [])
    chunks = await retrieve(req.question)

    def _generate():
        gen = ask_question_stream(req.question, chunks, history)
        full_answer = ""
        try:
            while True:
                event = next(gen)
                yield event
        except StopIteration as e:
            full_answer = e.value or ""

        updated = history + [
            {"role": "user", "content": req.question},
            {"role": "assistant", "content": full_answer},
        ]
        _sessions[session_id] = updated[-_MAX_HISTORY:]
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")
