# Pixel - Multi-turn Coding Mentor Chatbot

A Flask + Gemini chatbot with per-conversation memory and context window management.

## Features
- Gemini API backend (`/api/chat`)
- Multi-turn memory per conversation (keyed by conversation id)
- Context management: keeps the last 6 messages and folds older ones into a running summary
- System prompt: "Pixel", a friendly beginner coding mentor
- Friendly error handling (rate limit, timeout, network, bad key)
- API key in `.env` (git-ignored)

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
# open .env and paste your key from https://aistudio.google.com/apikey
python test_connection.py       # optional: check the API works
python app.py                   # open http://127.0.0.1:5000
```

## How context management works
When history exceeds 10 messages, the oldest ones are summarised by the model and the
summary is added to the system prompt; only the 6 most recent messages are sent as-is.
If summarising fails, it falls back to simple truncation.

## Project structure
```
app.py            Flask routes
chatbot.py        LLM calls, memory, summarisation, errors
static/index.html Chat UI
test_connection.py  One-message API test
```
