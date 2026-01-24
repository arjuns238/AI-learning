"""
Lessons endpoints - convert pedagogical intent to lesson format for web app
Includes enhanced quiz generation and contextual Q&A
"""

import json
import os
from typing import Optional, List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from layer1.schema import PedagogicalIntent

# Load environment variables
load_dotenv()

router = APIRouter()


# ============================================
# Original Lesson Types (kept for compatibility)
# ============================================

class LessonVisual(BaseModel):
    type: Literal["plot", "diagram", "table", "attention_heatmap"]
    spec: dict


class Quiz(BaseModel):
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str


class Lesson(BaseModel):
    title: str
    intuition: str
    concrete_example: str
    common_confusion: str
    visual: LessonVisual
    quiz: Quiz


# ============================================
# Enhanced Quiz Types (Phase 1)
# ============================================

class QuizOption(BaseModel):
    text: str
    is_correct: bool
    misconception_hint: Optional[str] = None


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[QuizOption]
    explanation: str
    related_beat_index: Optional[int] = None


class EnhancedQuiz(BaseModel):
    questions: List[QuizQuestion]
    passing_score: int = 2


# ============================================
# Q&A Types (Phase 1)
# ============================================

class QARequest(BaseModel):
    lesson_id: str
    question: str


class QAResponse(BaseModel):
    answer: str
    suggested_followups: List[str]
    related_section: Optional[str] = None


# ============================================
# Lesson Context (for Q&A)
# ============================================

class LessonContext(BaseModel):
    topic: str
    core_question: str
    target_mental_model: str
    common_misconception: str
    disambiguating_contrast: str
    concrete_anchor: str


# In-memory storage for lesson contexts (Phase 1)
# In Phase 2, this will move to Supabase
_lesson_contexts: dict[str, LessonContext] = {}


# ============================================
# LLM Client Helper
# ============================================

def get_llm_client():
    """Get LLM client based on environment."""
    api_provider = os.getenv("API_PROVIDER", "openai")

    if api_provider == "openai":
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return OpenAI(api_key=api_key), "openai", os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    else:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return anthropic.Anthropic(api_key=api_key), "anthropic", os.getenv("DEFAULT_MODEL", "claude-sonnet-4-20250514")


def call_llm(prompt: str, system: str = "") -> str:
    """Call LLM with prompt."""
    client, provider, model = get_llm_client()

    if provider == "openai":
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    else:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=0.7,
            system=system if system else "You are a helpful educational assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


# ============================================
# Quiz Generator
# ============================================

class QuizGenerator:
    """Generates enhanced quizzes from pedagogical intent."""

    @staticmethod
    def generate(intent: PedagogicalIntent, num_questions: int = 3) -> EnhancedQuiz:
        """
        Generate an enhanced quiz with multiple questions and adaptive hints.

        Uses the pedagogical intent to create questions that test understanding
        and provide targeted feedback based on common misconceptions.
        """

        system_prompt = """You are an expert educational assessment designer.
Generate quiz questions that test deep understanding, not just recall.
Each wrong answer should represent a common misconception or error.
Provide helpful hints that guide learners toward the correct understanding."""

        user_prompt = f"""Create {num_questions} multiple choice questions to test understanding of: {intent.topic}

Context:
- Core Question: {intent.core_question}
- Key Mental Model: {intent.target_mental_model}
- Common Misconception: {intent.common_misconception}
- Key Distinction: {intent.disambiguating_contrast}
- Concrete Example: {intent.concrete_anchor}
- Check for Understanding: {intent.check_for_understanding}

For each question, provide:
1. A clear question that tests understanding (not just recall)
2. Four options (A, B, C, D) where:
   - One is correct
   - Others represent plausible misconceptions
3. For each wrong option, a "misconception_hint" explaining why it's wrong and guiding toward correct understanding
4. An explanation for the correct answer

Return as JSON with this exact structure:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "The question text",
      "options": [
        {{"text": "Option A text", "is_correct": true}},
        {{"text": "Option B text", "is_correct": false, "misconception_hint": "Why this is wrong..."}},
        {{"text": "Option C text", "is_correct": false, "misconception_hint": "Why this is wrong..."}},
        {{"text": "Option D text", "is_correct": false, "misconception_hint": "Why this is wrong..."}}
      ],
      "explanation": "Why the correct answer is correct"
    }}
  ]
}}

Make sure:
- Questions progress from basic to more nuanced understanding
- At least one question addresses the common misconception directly
- Hints are educational, not just "this is wrong"
"""

        try:
            response = call_llm(user_prompt, system_prompt)

            # Parse JSON from response
            json_text = response
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()

            data = json.loads(json_text)

            # Convert to QuizQuestion objects
            questions = []
            for q in data.get("questions", []):
                options = [
                    QuizOption(
                        text=opt["text"],
                        is_correct=opt.get("is_correct", False),
                        misconception_hint=opt.get("misconception_hint")
                    )
                    for opt in q.get("options", [])
                ]
                questions.append(QuizQuestion(
                    id=q.get("id", f"q{len(questions)+1}"),
                    question=q["question"],
                    options=options,
                    explanation=q.get("explanation", "")
                ))

            return EnhancedQuiz(
                questions=questions,
                passing_score=max(1, len(questions) - 1)
            )

        except Exception as e:
            print(f"Quiz generation failed: {e}")
            # Fallback to basic quiz from intent
            return QuizGenerator._fallback_quiz(intent)

    @staticmethod
    def _fallback_quiz(intent: PedagogicalIntent) -> EnhancedQuiz:
        """Generate a basic quiz without LLM (fallback)."""
        return EnhancedQuiz(
            questions=[
                QuizQuestion(
                    id="q1",
                    question=intent.check_for_understanding,
                    options=[
                        QuizOption(
                            text=intent.target_mental_model.split(".")[0] + ".",
                            is_correct=True
                        ),
                        QuizOption(
                            text=intent.common_misconception,
                            is_correct=False,
                            misconception_hint=f"This is a common misconception. {intent.disambiguating_contrast}"
                        ),
                        QuizOption(
                            text="None of the above applies.",
                            is_correct=False,
                            misconception_hint="The concept does have clear applications."
                        ),
                        QuizOption(
                            text="All options are equally valid.",
                            is_correct=False,
                            misconception_hint="One answer is more accurate than the others."
                        ),
                    ],
                    explanation=intent.target_mental_model
                )
            ],
            passing_score=1
        )


# ============================================
# Q&A Handler
# ============================================

class QAHandler:
    """Handles contextual Q&A about lessons."""

    @staticmethod
    def answer(lesson_id: str, question: str) -> QAResponse:
        """
        Answer a question about a specific lesson.
        Uses lesson context to provide scoped, relevant answers.
        """

        # Get lesson context
        context = _lesson_contexts.get(lesson_id)
        if not context:
            # If no context stored, provide a generic educational response
            return QAHandler._generic_answer(question)

        system_prompt = f"""You are a helpful tutor answering questions about: {context.topic}

You have this context about the lesson:
- Core Question: {context.core_question}
- Key Mental Model: {context.target_mental_model}
- Common Misconception to avoid: {context.common_misconception}
- Key Distinction: {context.disambiguating_contrast}
- Concrete Example: {context.concrete_anchor}

Rules:
1. Only answer questions related to this topic
2. If asked about something unrelated, politely redirect
3. Use the concrete example when helpful
4. Correct misconceptions gently
5. Keep answers concise but educational"""

        user_prompt = f"""Student question: {question}

Provide:
1. A clear, educational answer (2-4 sentences)
2. 2-3 follow-up questions they might find helpful

Return as JSON:
{{
  "answer": "Your answer here",
  "suggested_followups": ["Follow-up 1?", "Follow-up 2?"]
}}"""

        try:
            response = call_llm(user_prompt, system_prompt)

            # Parse JSON
            json_text = response
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()

            data = json.loads(json_text)

            return QAResponse(
                answer=data.get("answer", "I'm not sure how to answer that."),
                suggested_followups=data.get("suggested_followups", []),
                related_section=None
            )

        except Exception as e:
            print(f"Q&A failed: {e}")
            return QAResponse(
                answer="I apologize, but I'm having trouble processing your question. Could you try rephrasing it?",
                suggested_followups=[
                    f"What is {context.topic}?",
                    f"Can you give an example of {context.topic}?"
                ]
            )

    @staticmethod
    def _generic_answer(question: str) -> QAResponse:
        """Provide a generic response when no context is available."""
        return QAResponse(
            answer="I don't have enough context about this lesson to answer your question. Please generate a lesson first, then ask questions about it.",
            suggested_followups=[]
        )


# ============================================
# Helper Functions
# ============================================

def pedagogical_intent_to_lesson(intent: PedagogicalIntent) -> Lesson:
    """
    Convert PedagogicalIntent to Lesson format.
    """
    visual = LessonVisual(
        type="diagram",
        spec={
            "title": f"{intent.topic} - Visualization",
            "mermaid": "graph LR\n    A[Concept] --> B[Understanding]"
        }
    )

    quiz = Quiz(
        question=intent.check_for_understanding,
        options=[
            "Option A - To be generated",
            "Option B - To be generated",
            "Option C - To be generated",
            "Option D - To be generated"
        ],
        correct_answer_index=0,
        explanation="Explanation to be generated based on the answer"
    )

    return Lesson(
        title=intent.topic,
        intuition=intent.target_mental_model,
        concrete_example=intent.concrete_anchor,
        common_confusion=intent.common_misconception,
        visual=visual,
        quiz=quiz
    )


def store_lesson_context(lesson_id: str, intent: PedagogicalIntent):
    """Store lesson context for Q&A."""
    _lesson_contexts[lesson_id] = LessonContext(
        topic=intent.topic,
        core_question=intent.core_question,
        target_mental_model=intent.target_mental_model,
        common_misconception=intent.common_misconception,
        disambiguating_contrast=intent.disambiguating_contrast,
        concrete_anchor=intent.concrete_anchor
    )


# ============================================
# API Endpoints
# ============================================

@router.post("/from-intent", response_model=Lesson)
async def create_lesson_from_intent(intent: PedagogicalIntent):
    """
    Convert a PedagogicalIntent to Lesson format for the web app.
    """
    try:
        lesson = pedagogical_intent_to_lesson(intent)
        return lesson
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/generate", response_model=EnhancedQuiz)
async def generate_quiz(intent: PedagogicalIntent, num_questions: int = 3):
    """
    Generate an enhanced quiz from pedagogical intent.
    """
    try:
        quiz = QuizGenerator.generate(intent, num_questions)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qa/{lesson_id}", response_model=QAResponse)
async def ask_question(lesson_id: str, request: QARequest):
    """
    Answer a contextual question about a specific lesson.
    """
    try:
        response = QAHandler.answer(lesson_id, request.question)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context/{lesson_id}")
async def store_context(lesson_id: str, intent: PedagogicalIntent):
    """
    Store lesson context for Q&A. Called after lesson generation.
    """
    try:
        store_lesson_context(lesson_id, intent)
        return {"status": "stored", "lesson_id": lesson_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic}")
async def get_lesson_by_topic(topic: str):
    """
    Get a lesson by topic (if it exists in the database).
    """
    raise HTTPException(
        status_code=501,
        detail="Lesson storage not yet implemented. Use /from-intent endpoint."
    )
