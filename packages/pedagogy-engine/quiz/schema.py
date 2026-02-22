from pydantic import BaseModel
from typing import List

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str
    section_id: str | None = None  # optional grounding

class EnhancedQuiz(BaseModel):
    topic: str
    questions: List[QuizQuestion]
