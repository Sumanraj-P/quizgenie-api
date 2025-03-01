import os
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from datetime import datetime
from firebase_config import get_user_ref
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Set it in .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize FastAPI
app = FastAPI()

class Answer(BaseModel):
    question: str
    user_answer: str

class QuizData(BaseModel):
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str

class QuizAttemptRequest(BaseModel):
    user_answers: List[Answer]
    quiz_data: List[QuizData]
    total_questions: int

def generate_quiz(topic: str, difficulty: str, num_questions: int):
    """Generates quiz questions using Google Gemini API."""
    prompt = f"""
    Create {num_questions} multiple-choice questions about {topic} with a {difficulty} difficulty level.
    - Each question should have four options labeled A, B, C, and D.
    - Clearly specify the correct answer.
    - Provide a short explanation for why the correct answer is right.
    - Ensure the difficulty level aligns with {difficulty} (Easy, Medium, or Hard).
    - Format the response as JSON: 
      [
        {{"question": "Q", "options": {{"A": "Opt1", "B": "Opt2", "C": "Opt3", "D": "Opt4"}}, "correct_answer": "A", "explanation": "Exp"}}
      ]
    """


    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        response = model.generate_content(prompt)

        if not response or not hasattr(response, "text"):
            raise ValueError("Invalid Gemini API response.")

        response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

        if not response_text.startswith("["):
            raise ValueError(f"Unexpected format: {response_text}")

        return json.loads(response_text)

    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None

@app.get("/quiz")
def get_quiz(topic: str, difficulty: str, num_questions: int):
    """Returns generated quiz without storing."""
    quiz_data = generate_quiz(topic, difficulty, num_questions)
    if quiz_data:
        return {"status": "success", "quiz": {"topic": topic, "difficulty": difficulty, "questions": quiz_data}}
    return {"status": "error", "message": "Failed to generate quiz"}

@app.get("/user/stats/{user_id}")
def get_user_stats(user_id: str):
    """Fetches user statistics including quiz history."""
    try:
        user_ref = get_user_ref(user_id)
        quizzes_ref = list(user_ref.collection("quizzes").stream())  # Ensure it's a list to avoid empty iteration

        total_quizzes = len(quizzes_ref)
        correct_answers = 0
        wrong_answers = 0
        daily_stats = {}
        quizzes_list = []

        for quiz in quizzes_ref:
            data = quiz.to_dict()
            correct_answers += data.get("correct_answers", 0)
            wrong_answers += data.get("wrong_answers", 0)

            date = data.get("timestamp", "").split("T")[0] if "timestamp" in data else "unknown"
            daily_stats[date] = daily_stats.get(date, 0) + 1

            quizzes_list.append({
                "quiz_id": quiz.id,
                "score": data.get("score", 0),
                "num_questions": data.get("num_questions", 0),
                "correct_answers": data.get("correct_answers", 0),
                "wrong_answers": data.get("wrong_answers", 0),
                "timestamp": data.get("timestamp", "N/A"),
            })

        return {
            "total_quizzes": total_quizzes,
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "daily_stats": daily_stats,
            "quizzes_list": sorted(quizzes_list, key=lambda x: x["timestamp"], reverse=True),
        }

    except Exception as e:
        print(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user statistics.")
