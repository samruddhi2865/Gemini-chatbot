# Pixel - Multi-turn Coding Mentor Chatbot 🤖

A beginner-friendly AI coding mentor built with **Flask and Google Gemini**. Pixel supports multi-turn conversations, remembers previous messages within a conversation, manages longer conversation context, and provides friendly coding guidance.

## ✨ Features

- 🤖 Gemini API-powered coding mentor
- 💬 Multi-turn conversational chat
- 🧠 Per-conversation memory using conversation IDs
- 🔄 Supports follow-up questions and instructions
- 📝 Context window management for longer conversations
- 📚 Automatically summarizes older conversation history
- 👨‍💻 Friendly system prompt designed for beginner programmers
- ⚠️ Friendly error handling for:
  - Rate limits
  - Timeouts
  - Network errors
  - Invalid API keys
  - Temporarily unavailable Gemini models
- 🔁 Fallback Gemini models when the primary model is unavailable
- 🔐 API key stored in `.env` and excluded from Git
- 🌐 Flask backend with `/api/chat` endpoint

## 📸 Chatbot Screenshots

### Screenshot 1

![Pixel Chatbot Screenshot 1](screenshots/Screenshot%201.png)

### Screenshot 2

![Pixel Chatbot Screenshot 2](screenshots/Screenshot%202.png)

### Screenshot 3

![Pixel Chatbot Screenshot 3](screenshots/Screenshot%203.png)

The screenshots demonstrate Pixel handling a multi-turn coding conversation and responding to follow-up instructions while maintaining conversation context.

## 🛠️ Technologies Used

- **Python**
- **Flask**
- **Google Gemini API**
- **HTML**
- **CSS**
- **JavaScript**

## 🧠 How Context Management Works

Pixel maintains conversation history separately for each conversation using a unique **conversation ID**.

When the conversation history exceeds **10 messages**:

1. The older messages are selected for summarization.
2. The Gemini model creates a short running summary.
3. The summary is added to the system prompt.
4. Only the **6 most recent messages** are kept as-is.
5. The older messages are removed from the active history.

If summarization fails, Pixel falls back to simple truncation so that the conversation can continue working.

This approach helps keep the amount of conversation context manageable while preserving important information from earlier messages.

## 🔄 Gemini Model Fallback

Pixel can use multiple Gemini models.

If the primary model is temporarily unavailable, times out, or encounters a rate limit, the application can retry the request and then attempt the configured fallback models.

This helps the chatbot handle temporary Gemini API availability problems more gracefully.

## 📁 Project Structure

```text
Pixel/
│
├── screenshots/
│   ├── Screenshot 1.png
│   ├── Screenshot 2.png
│   └── Screenshot 3.png
│
├── static/
│   └── index.html
│
├── venv/
│
├── .env
├── .gitignore
├── app.py
├── chatbot.py
├── README.md
├── requirements.txt
└── test_connection.py
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
