"""
Lessons endpoints - convert pedagogical intent to lesson format for web app
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal

from layer1.schema import PedagogicalIntent

router = APIRouter()


# These match the web app's Lesson type
class LessonVisual(BaseModel):
    type: Literal["plot", "diagram", "table", "attention_heatmap"]
    spec: dict  # Spec depends on type


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


def pedagogical_intent_to_lesson(intent: PedagogicalIntent) -> Lesson:
    """
    Convert PedagogicalIntent to Lesson format.

    Maps:
    - topic → title
    - target_mental_model → intuition
    - concrete_anchor → concrete_example
    - common_misconception → common_confusion
    - check_for_understanding → quiz question
    """

    # TODO: Generate visual spec from spatial_metaphor
    # For now, use a placeholder diagram
    visual = LessonVisual(
        type="diagram",
        spec={
            "title": f"{intent.topic} - Visualization",
            "mermaid": "graph LR\n    A[Concept] --> B[Understanding]"
        }
    )

    # Parse check_for_understanding into quiz format
    # TODO: Use LLM to generate multiple choice options from the question
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


@router.post("/from-intent", response_model=Lesson)
async def create_lesson_from_intent(intent: PedagogicalIntent):
    """
    Convert a PedagogicalIntent to Lesson format for the web app.

    This is Layer 1.5 - bridging pedagogy to visualization.
    """
    try:
        lesson = pedagogical_intent_to_lesson(intent)
        return lesson
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic}")
async def get_lesson_by_topic(topic: str):
    """
    Get a lesson by topic (if it exists in the database).

    TODO: Implement lesson storage and retrieval.
    """
    raise HTTPException(
        status_code=501,
        detail="Lesson storage not yet implemented. Use /from-intent endpoint."
    )
