from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from quiz_service import generate_quiz, get_user_stats
from typing import List, Dict

app = FastAPI()

class QuizRequest(BaseModel):
    user_id: str
    topic: str
    difficulty: str
    num_questions: int

class UserAnswersRequest(BaseModel):
    quiz_data: List[Dict]
    user_answers: List[Dict]

@app.get("/")
def home():
    """Root endpoint to check if the API is running."""
    return {"message": "QuizGenie API is running!"}

@app.post("/generate-quiz")
def generate_quiz_api(request: QuizRequest):
    """API endpoint to generate a quiz."""
    quiz_data = generate_quiz(request.topic, request.difficulty, request.num_questions)
    if not quiz_data:
        raise HTTPException(status_code=500, detail="Failed to generate quiz.")

    return {
        "user_id": request.user_id,
        "quiz_data": quiz_data
    }

@app.get("/user-stats/{user_id}")
def user_stats_api(user_id: str):
    """API endpoint to fetch user statistics."""
    return get_user_stats(user_id)
