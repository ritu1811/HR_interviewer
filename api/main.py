from flask import Flask, request, jsonify, send_from_directory
from uuid import uuid4
import google.genai as genai
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "https://hrinterviewer.vercel.app"])

# 🔐 Gemini API Key (from Render environment variables or .env)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is required")

# 🤖 Initialize Gemini client
try:
    genai_client = genai.Client(api_key=api_key)
except Exception as e:
    raise RuntimeError(f"Failed to initialize GenAI client: {e}")

model_name = "gemini-2.5-flash"

# 🧠 Session storage
SESSIONS = {}

# 📋 Interview steps
INTERVIEW_STEPS = [
    {"id": "Introduction", "question": "Hi! I am your virtual HR interviewer. Can you please introduce yourself?"},
    {"id": "Experience", "question": "Can you summarize your most relevant experience?"},
    {"id": "Strength", "question": "What is your one strength and one weakness?"},
    {"id": "Challenge", "question": "Describe a challenge and how you solved it."},
    {"id": "Motivation", "question": "Why do you want this job?"},
    {"id": "Questions", "question": "Do you have any questions for us?"}
]

# 🧠 Prompt builder
def build_prompt(question, answer):
    return f"""
You are a professional HR interviewer.

Question: {question}
Candidate Answer: {answer}

Tasks:
1. Determine if the answer is valid.
2. If valid → start with [PASS], give score (1-10), 2 strengths, 2 improvements.
3. If invalid → start with [FAIL] and ask for proper answer.

Response MUST start with [PASS] or [FAIL].
"""

# 🌐 Serve frontend
@app.route("/")
def home():
    return "Backend is running"

# 🚀 Start interview
@app.route("/api/start", methods=["POST"])
def start():
    session_id = str(uuid4())

    SESSIONS[session_id] = {
        "step": 0,
        "answers": [],
        "completed": False
    }

    return jsonify({
        "session_id": session_id,
        "question": INTERVIEW_STEPS[0]["question"]
    })

# 💬 Chat endpoint
@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    data = request.get_json()

    session_id = data.get("session_id")
    message = data.get("message", "").strip()

    if not session_id or session_id not in SESSIONS:
        return jsonify({"error": "Invalid session"}), 400

    session = SESSIONS[session_id]

    if session["completed"]:
        return jsonify({"message": "Interview already completed"})

    if not message:
        return jsonify({"reply": "Please provide a valid answer."})

    step = session["step"]

    if step >= len(INTERVIEW_STEPS):
        session["completed"] = True
        return jsonify({"message": "Interview completed!"})

    question = INTERVIEW_STEPS[step]["question"]

    # 🤖 Gemini API call
    try:
        prompt = build_prompt(question, message)

        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        # Extract response text safely
        if hasattr(response, "text") and response.text:
            ai_reply = response.text
        elif hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            ai_reply = "".join([p.text for p in parts if hasattr(p, "text")])
        else:
            ai_reply = str(response)

    except Exception as e:
        print("🔥 ERROR:", e)
        ai_reply = "[PASS] Temporary issue, proceeding..."

    # 🧠 Process response
    passed = "[PASS]" in ai_reply
    clean_reply = ai_reply.replace("[PASS]", "").replace("[FAIL]", "").strip()

    if passed:
        session["answers"].append({
            "question": question,
            "answer": message,
            "feedback": clean_reply
        })

        session["step"] += 1

        if session["step"] >= len(INTERVIEW_STEPS):
            session["completed"] = True
            return jsonify({
                "message": "Interview completed!",
                "responses": session["answers"],
                "reply": clean_reply
            })

        next_q = INTERVIEW_STEPS[session["step"]]["question"]

        return jsonify({
            "reply": clean_reply,
            "next_question": next_q
        })

    else:
        return jsonify({
            "reply": clean_reply
        })


# 🚀 Render-compatible run
# if __name__ == "__main__":
#     app.run(
#         host="0.0.0.0",
#         port=int(os.environ.get("PORT", 5000))
#     )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))