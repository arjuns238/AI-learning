"""
Storyboard endpoints - generate storyboards from pedagogical intent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from layer1.schema import PedagogicalIntent
from layer2.generator import StoryboardGenerator
from layer2.schema import StoryboardWithMetadata

router = APIRouter()


class StoryboardRequest(BaseModel):
    """Request to generate storyboard from pedagogical intent."""
    pedagogical_intent: PedagogicalIntent
    pattern_override: Optional[str] = None


# Initialize generator (reuse across requests)
generator = None


def get_generator() -> StoryboardGenerator:
    """Lazy initialization of storyboard generator"""
    global generator
    if generator is None:
        generator = StoryboardGenerator(
            strategy="hybrid",
            use_llm_sequencing=False  # Can be enabled via env var
        )
    return generator


@router.post("/from-intent", response_model=StoryboardWithMetadata)
async def generate_storyboard(request: StoryboardRequest):
    """
    Generate storyboard from pedagogical intent.

    Example:
        POST /api/storyboard/from-intent
        {
            "pedagogical_intent": {
                "topic": "Gradient Descent",
                "core_question": "How does an algorithm find the best parameters?",
                "target_mental_model": "Like navigating down a mountainside...",
                "common_misconception": "Always finds global minimum",
                "disambiguating_contrast": "Gradient descent vs exhaustive search",
                "concrete_anchor": "Training a house price model",
                "check_for_understanding": "What happens with multiple valleys?",
                "domain": "machine_learning",
                "difficulty_level": 3
            },
            "pattern_override": null
        }
    """
    try:
        gen = get_generator()
        result = gen.generate(
            pedagogical_intent=request.pedagogical_intent,
            pattern_override=request.pattern_override
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for storyboard service"""
    return {
        "status": "healthy",
        "service": "storyboard-generator",
        "version": "0.1.0"
    }
