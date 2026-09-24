"""Flask backend. Run:  python app.py  then open http://127.0.0.1:5000"""
from flask import Flask, jsonify, request, send_from_directory
import chatbot

app = Flask(__name__, static_folder="static")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    cid = data.get("conversation_id")
    if not cid:
        return jsonify(error="Missing conversation_id."), 400
    try:
        reply = chatbot.chat(cid, data.get("message"))
        return jsonify(reply=reply)
    except chatbot.ChatbotError as e:
        return jsonify(error=e.message), e.status


@app.post("/api/reset")
def api_reset():
    data = request.get_json(silent=True) or {}
    chatbot.reset(data.get("conversation_id", ""))
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True)
