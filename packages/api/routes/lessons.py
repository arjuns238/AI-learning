"""
Lessons endpoints - contextual Q&A for lessons
"""

import json
import os
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()


# ============================================
# Q&A Types
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
# API Endpoints
# ============================================

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


