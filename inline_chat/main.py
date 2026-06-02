import argparse
from database import init_db, clear_session, load_session, create_session
from persona import PERSONAS
from cli_helper import print_sessions, run_repl, pick_persona
from openai import OpenAI
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "history.db"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


def main():
    parser = argparse.ArgumentParser(description="Persona chatbot with persistent SQLite history")
    parser.add_argument("--list-personas", action="store_true", help="Show all personas")
    parser.add_argument("--list-sessions", action="store_true", help="Show past sessions")
    parser.add_argument("--session", metavar="ID", help="Resume an existing session by ID")
    parser.add_argument("--clear-session", metavar="ID", help="Delete a session and its history")
    parser.add_argument("--persona", metavar="KEY", help="Start with this persona (skip picker)")
    args = parser.parse_args()
 
    conn = init_db(DB_PATH)
 
    if args.list_personas:
        for key, p in PERSONAS.items():
            print(f"  {key:<14} — {p['description']}")
        return
 
    if args.list_sessions:
        print_sessions(conn)
        return
 
    if args.clear_session:
        clear_session(conn, args.clear_session)
        print(f"Session {args.clear_session} cleared.")
        return
 
    # Ollama exposes an OpenAI-compatible API — no API key needed
    try:
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    except Exception as e:
        print(f"Could not initialise Ollama client: {e}")
        print(f"Make sure Ollama is running: ollama serve")
        sys.exit(1)
 
    if args.session:
        # Resume existing session
        session = load_session(conn, args.session)
        if not session:
            print(f"Session '{args.session}' not found. Run --list-sessions to see available sessions.")
            sys.exit(1)
        session_id = session["id"]
        persona_key = session["persona_key"]
    else:
        # New session
        persona_key = args.persona if args.persona in PERSONAS else pick_persona()
        session_id = create_session(conn, persona_key)
        print(f"\nNew session created: {session_id}")
 
    run_repl(client, conn, session_id, persona_key)
    conn.close()
 
 
if __name__ == "__main__":
    main()
 