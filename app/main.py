from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.agent import run_agent
from app.session import get_history, reset_history

app = FastAPI(title="Business Productivity Agent")


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    history = get_history(payload.user_id)
    history.append({"role": "user", "content": payload.message})
    reply = run_agent(history)
    return ChatResponse(reply=reply)


@app.post("/reset")
def reset(payload: dict):
    reset_history(payload["user_id"])
    return {"status": "reset"}


# Serves app/static/index.html at "/" — a zero-dependency browser chat widget
# that just calls /chat. Mounted last so it doesn't shadow the routes above.
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
