<<<<<<< HEAD
# my_chatbot_personas
This is persona based chatbot to cater to different needs.
=======
# PersonaChat

A full-stack chatbot with distinct AI personas, user accounts, and persistent conversation history. Built with FastAPI + Ollama + SQLite.

![Personas: Socrates, Hemingway, Ada Lovelace, Feynman](https://img.shields.io/badge/personas-Socrates%20%7C%20Hemingway%20%7C%20Ada%20%7C%20Feynman-gold)
![Stack: FastAPI + Ollama + SQLite](https://img.shields.io/badge/stack-FastAPI%20%2B%20Ollama%20%2B%20SQLite-blue)

## Features

- 🎭 **Multiple personas** — each with a distinct system prompt and voice
- 👤 **User accounts** — JWT auth, register/login
- 💾 **Persistent history** — conversations survive restarts, resumable by session ID
- 🏠 **Runs locally** — powered by Ollama (no OpenAI API costs)
- 🚀 **Cloud-ready** — one-click deploy to Railway or Render

## Quick start (local)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/persona-chat.git
cd persona-chat

# 2. Install dependencies
pip install -r requirements.txt
npm i jose

# 3. Start Ollama with llama3
ollama serve
ollama pull llama3

# 4. Configure environment
cp .env.example .env
# Edit .env — at minimum set a strong SECRET_KEY

# 5. Run
uvicorn backend.main:app --reload

# Open http://localhost:8000
```

## Deploy to Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Set environment variables in Railway dashboard:
   - `SECRET_KEY` — any long random string
   - `OLLAMA_BASE_URL` — URL of your hosted Ollama instance
   - `MODEL` — e.g. `llama3`
4. Deploy — Railway uses `railway.toml` automatically

## Deploy to Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — Render reads `render.yaml`
4. Set `OLLAMA_BASE_URL` in the Render dashboard
5. Deploy

> **Note on Ollama hosting**: Ollama runs locally by default. For cloud deployment you need a hosted Ollama instance. Options: [fly.io](https://fly.io), a VPS with GPU, or services like [Replicate](https://replicate.com).

## Adding a persona

Open `backend/main.py` and add an entry to `PERSONAS`:

```python
PERSONAS = {
    ...
    "your_key": {
        "name": "Display Name",
        "description": "One-line description shown in the UI",
        "avatar": "🎯",
        "system": "Your full system prompt. Be specific about voice and mannerisms.",
    },
}
```

No migrations needed — the database schema is persona-agnostic.

## Project structure

```
persona-chat/
├── backend/
│   └── main.py          # FastAPI app — routes, auth, DB, chat logic
├── frontend/
│   ├── templates/
│   │   └── index.html   # Single-page app shell
│   └── static/
│       ├── css/app.css  # All styles
│       └── js/app.js    # All frontend logic
├── requirements.txt
├── Dockerfile
├── railway.toml
├── render.yaml
└── .env.example
```

## API reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Get JWT token |
| GET | `/personas` | — | List personas |
| POST | `/sessions` | ✓ | Create session |
| GET | `/sessions` | ✓ | List user sessions |
| GET | `/sessions/{id}` | ✓ | Get session + history |
| DELETE | `/sessions/{id}` | ✓ | Delete session |
| POST | `/sessions/{id}/chat` | ✓ | Send message |

Interactive docs at `/docs` when running locally.

## Contributing

PRs welcome. Ideas for contributions:
- [ ] Streaming responses
- [ ] Markdown rendering in messages
- [ ] Export conversation as Markdown/PDF
- [ ] Custom persona builder in the UI
- [ ] Swap Ollama for Anthropic/OpenAI with env flag

## License

MIT
>>>>>>> 974e939 (inital commit)
