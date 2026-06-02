import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from groq import Groq
from .personas import PERSONAS
from .database import init_db, get_db
from .auth import hash_password, create_access_token, verify_password, get_current_user

 
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "ollama3.1")
MODEL = os.getenv("MODEL", "llama3.1")
GROQ_API_KEY = os.getenv("GROQ", "")
MAX_HISTORY = 20

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
 
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
 
class CreateSessionRequest(BaseModel):
    persona_key: str
    title: str | None = None
 
class ChatRequest(BaseModel):
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
 
app = FastAPI(title="Persona Chatbot API", lifespan=lifespan)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# Serve frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if (frontend_path / "static").exists():
    app.mount("/static", StaticFiles(directory=frontend_path / "static"), name="static")

###### Auth Routes ######
@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE email=? OR username=?", (req.email, req.username)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email or username already taken")
 
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO users (id, email, username, hashed_pw, created_at) VALUES (?,?,?,?,?)",
        (user_id, req.email, req.username, hash_password(req.password), now),
    )
    conn.commit()
    conn.close()
    return TokenResponse(access_token=create_access_token(user_id), username=req.username)

@app.post("/auth/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email=? OR username=?",
        (form.username, form.username),
    ).fetchone()
    conn.close()
    if not user or not verify_password(form.password, user["hashed_pw"]):
        raise HTTPException(status_code=401, detail="Incorrect email/username or password")
    return TokenResponse(
        access_token=create_access_token(user["id"]),
        username=user["username"],
    )

@app.post("/auth/guest", response_model=TokenResponse)
def guest_login():
    """Create a temporary guest account. Sessions persist for the token lifetime."""
    conn = get_db()
    guest_id = str(uuid.uuid4())
    username = f"guest_{guest_id[:6]}"
    now = datetime.utcnow().isoformat()
    # Guests have no email/password — store empty hashed_pw sentinel
    conn.execute(
        "INSERT INTO users (id, email, username, hashed_pw, created_at) VALUES (?,?,?,?,?)",
        (guest_id, f"{guest_id}@guest", username, "", now),
    )
    conn.commit()
    conn.close()
    return TokenResponse(access_token=create_access_token(guest_id), username=username)
 

@app.get("/personas")
def list_personas():
    return [
        {"key": k, "name": v["name"], "description": v["description"], "avatar": v["avatar"]}
        for k, v in PERSONAS.items()
    ]

@app.post("/sessions", status_code=201)
def create_session(req: CreateSessionRequest, user=Depends(get_current_user)):
    if req.persona_key not in PERSONAS:
        raise HTTPException(status_code=400, detail="Unknown persona")
    conn = get_db()
    session_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    title = req.title or f"Chat with {PERSONAS[req.persona_key]['name']}"
    conn.execute(
        "INSERT INTO sessions (id, user_id, persona_key, title, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (session_id, user["id"], req.persona_key, title, now, now),
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "persona_key": req.persona_key, "title": title, "created_at": now}
 
 
@app.get("/sessions")
def list_sessions(user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE user_id=? ORDER BY updated_at DESC",
        (user["id"],),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
 
 
@app.get("/sessions/{session_id}")
def get_session(session_id: str, user=Depends(get_current_user)):
    conn = get_db()
    session = conn.execute(
        "SELECT * FROM sessions WHERE id=? AND user_id=?", (session_id, user["id"])
    ).fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    messages = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return {**dict(session), "messages": [dict(m) for m in messages]}
 
 
@app.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, user=Depends(get_current_user)):
    conn = get_db()
    session = conn.execute(
        "SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user["id"])
    ).fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
 

@app.post("/sessions/{session_id}/chat")
def chat(session_id: str, req: ChatRequest, user=Depends(get_current_user)):
    conn = get_db()
    session = conn.execute(
        "SELECT * FROM sessions WHERE id=? AND user_id=?", (session_id, user["id"])
    ).fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")
 
    persona = PERSONAS[session["persona_key"]]
    now = datetime.utcnow().isoformat()
 
    # Save user message
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
        (session_id, "user", req.message, now),
    )
    conn.commit()
 
    # Load recent history
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, MAX_HISTORY),
    ).fetchall()
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
 
    # Call Ollama
    try:
        client = Groq(api_key = GROQ_API_KEY)
        messages=[{"role": "system", "content": persona["system"]}] + history

        completion = client.chat.completions.create(
            model= "llama-3.1-8b-instant", # same model, hosted by Groq
            messages=messages,
        )

        #client = OpenAI(base_url=OLLAMA_BASE_URL, api_key=OLLAMA_API_KEY)
        # response = client.chat.completions.create(
        #     model=MODEL,
        #     messages=[{"role": "system", "content": persona["system"]}] + history,
        # )
        reply = completion.choices[0].message.content #response.choices[0].message.content
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=502, detail=f"Model error: {str(e)}")
 
    # Save assistant reply
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?,?,?,?)",
        (session_id, "assistant", reply, datetime.utcnow().isoformat()),
    )
    conn.execute(
        "UPDATE sessions SET updated_at=? WHERE id=?",
        (datetime.utcnow().isoformat(), session_id),
    )
    conn.commit()
    conn.close()
 
    return {"reply": reply}
 

@app.get("/", include_in_schema=False)
def serve_frontend():
    index = frontend_path / "templates" / "main.html"
    if index.exists():
        return FileResponse(index)
    return {"detail": "Frontend not found", "frontend":frontend_path}


 