from persona import PERSONAS
from database import save_message, load_history
import sqlite3
from openai import OpenAI

MAX_HISTORY_MESSAGES = 20   # messages kept in context window per session
MODEL = "llama3.1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

def chat(
    client: OpenAI,
    conn: sqlite3.Connection,
    session_id: str,
    persona_key: str,
    user_message: str,
) -> str:
    """
    Send a message and return the assistant's reply.
    History is loaded from SQLite, the reply is saved back.
    """
    persona = PERSONAS[persona_key]
 
    # 1. Save the user message first so it's always in the DB
    save_message(conn, session_id, "user", user_message)
 
    # 2. Load recent history (includes the message we just saved)
    history = load_history(conn, session_id, MAX_HISTORY_MESSAGES)
 
    # 3. Prepend system message — OpenAI format uses messages list for system too
    messages = [{"role": "system", "content": persona["system"]}] + history
 
    # 4. Call Ollama via OpenAI-compatible endpoint
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
 
    reply = response.choices[0].message.content
 
    # 5. Save the assistant reply
    save_message(conn, session_id, "assistant", reply)
 
    return reply
 