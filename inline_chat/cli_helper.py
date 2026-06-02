from persona import PERSONAS
import sqlite3
from openai import OpenAI
from chat import chat
from database import list_sessions

def pick_persona() -> str:
    print("\nAvailable personas:\n")
    keys = list(PERSONAS.keys())
    for i, key in enumerate(keys, 1):
        p = PERSONAS[key]
        print(f"  {i}. {p['name']:<16} — {p['description']}")
    print()
    while True:
        raw = input("Pick a persona (number or name): ").strip().lower()
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        if raw in PERSONAS:
            return raw
        print(f"  Not recognised. Enter a number 1–{len(keys)} or a name.")
 
 
def print_sessions(conn: sqlite3.Connection):
    rows = list_sessions(conn)
    if not rows:
        print("No sessions found.")
        return
    print(f"\n{'ID':<10} {'Persona':<14} {'Last active'}")
    print("─" * 44)
    for r in rows:
        persona_name = PERSONAS.get(r["persona_key"], {}).get("name", r["persona_key"])
        print(f"  {r['id']:<8} {persona_name:<14} {r['updated_at'][:16]}")
    print()
 
 
def run_repl(
    client: OpenAI,
    conn: sqlite3.Connection,
    session_id: str,
    persona_key: str,
):
    persona = PERSONAS[persona_key]
    msg_count = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
 
    print(f"\n{'─'*52}")
    print(f"  Persona  : {persona['name']}")
    print(f"  Session  : {session_id}")
    print(f"  History  : {msg_count // 2} prior exchanges loaded")
    print(f"  Quit     : type 'exit' or Ctrl-C")
    print(f"{'─'*52}\n")
 
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            break
 
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Session saved. Bye.")
            break
 
        try:
            reply = chat(client, conn, session_id, persona_key, user_input)
            print(f"\n{persona['name']}: {reply}\n")
        except Exception as e:
            print(f"\n[API error: {e}]\n")
 