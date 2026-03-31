from flask import Flask, render_template, request, jsonify, session
import os
import requests
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "rrb-railway-secret-2025")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

SYSTEM_PROMPT = """You are an expert RRB Railway Exam Assistant for Indian railway recruitment exams including RRB NTPC, Group D, ALP, JE, and other RRB exams.
Your role:
- Provide accurate, concise answers about exam syllabus, pattern, eligibility, and preparation
- Give math and reasoning shortcut tricks clearly with examples
- Share important GK, current affairs, and science topics relevant to RRB exams
- Motivate and guide aspirants with study strategies
- Use bullet points, numbered lists, and clear formatting in answers
- Keep answers focused and practical
- Respond in English (or Hindi if the user writes in Hindi)"""

@app.route("/")
def index():
    session.setdefault("history", [])
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    api_key = data.get("api_key", GROQ_API_KEY).strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if not api_key:
        return jsonify({"error": "No API key provided. Please enter your Groq API key."}), 401

    # Maintain history in session
    if "history" not in session:
        session["history"] = []

    session["history"].append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + session["history"]

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            },
            timeout=30
        )

        result = response.json()

        if not response.ok:
            error_msg = result.get("error", {}).get("message", f"API error {response.status_code}")
            return jsonify({"error": error_msg}), response.status_code

        reply = result["choices"][0]["message"]["content"]
        session["history"].append({"role": "assistant", "content": reply})
        session.modified = True

        return jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear", methods=["POST"])
def clear():
    session["history"] = []
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    print("\n🚆 RRB Railway Exam Chatbot")
    print("=" * 40)
    print("➜  Open http://localhost:5000 in your browser")
    print("=" * 40 + "\n")
    app.run(debug=True, port=5000)