from __future__ import annotations

import json
import os
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models import FeedbackEvent, RecommendRequest, RecommendResponse
from app.pipeline import RecommenderPipeline
from app.utils import data_dir, new_session_id


app = FastAPI(title="VinFast Car Recommender", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = RecommenderPipeline()


class TitleRequest(BaseModel):
    text: str


class TitleResponse(BaseModel):
    title: str


class StreamChatRequest(BaseModel):
    id: str
    messages: list[dict[str, Any]]
    modelId: Optional[str] = None
    hints: Optional[dict[str, Any]] = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/title", response_model=TitleResponse)
def api_v1_title(req: TitleRequest) -> TitleResponse:
    collapsed = " ".join(str(req.text or "").split()).strip()
    title = collapsed[:80] if collapsed else "New Chat"
    return TitleResponse(title=title)


@app.post("/api/v1/chat/stream")
def api_v1_chat_stream(req: StreamChatRequest) -> StreamingResponse:
    try:
        resp = pipeline.chat(ui_messages=req.messages, session_id=req.id, top_k=3)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    assistant_text = str(resp.assistant_message or "")

    def gen() -> Any:
        usage = {"trace": resp.meta.get("trace", []), "next_step": resp.next_step.value}
        yield f"data: {json.dumps({'type': 'usage', 'data': usage}, ensure_ascii=False)}\n\n"
        for i in range(0, len(assistant_text), 24):
            chunk = assistant_text[i : i + 24]
            payload = json.dumps({"type": "text-delta", "data": chunk}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: {\"type\":\"finish\"}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )



@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest) -> RecommendResponse:
    state: dict[str, Any] = dict(req.state or {})
    if not state.get("session_id"):
        state["session_id"] = new_session_id()
    ui_messages: list[dict[str, Any]] = []
    if req.messages:
        ui_messages = [{"role": m.role.value, "content": m.content} for m in req.messages if m.content.strip()]
    elif req.question and str(req.question).strip():
        ui_messages = [{"role": "user", "content": str(req.question).strip()}]
    if not ui_messages:
        raise HTTPException(status_code=400, detail="question/messages is required")
    try:
        return pipeline.chat(ui_messages=ui_messages, state=state, top_k=req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/feedback")
def feedback(event: FeedbackEvent) -> dict[str, str]:
    out = data_dir() / "feedback.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("", encoding="utf-8") if not out.exists() else None
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
    return {"status": "ok"}


def _cli_run() -> None:
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    _cli_run()
