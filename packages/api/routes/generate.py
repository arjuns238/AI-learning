"""
Generation endpoints - create pedagogical intent from topics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from layer1.generator import PedagogicalIntentGenerator
from layer1.schema import PedagogicalIntentWithMetadata

router = APIRouter()


class GenerateRequest(BaseModel):
    topic: str
    domain: Optional[str] = None
    difficulty_level: Optional[int] = None


class BatchGenerateRequest(BaseModel):
    topics: List[str]
    domain: Optional[str] = None
    difficulty_level: Optional[int] = None


# Initialize generator (reuse across requests)
generator = None


def get_generator() -> PedagogicalIntentGenerator:
    """Lazy initialization of generator"""
    global generator
    if generator is None:
        generator = PedagogicalIntentGenerator()
    return generator


@router.post("/", response_model=PedagogicalIntentWithMetadata)
async def generate_pedagogical_intent(request: GenerateRequest):
    """
    Generate pedagogical intent for a single topic.

    Example:
        POST /api/generate
        {
            "topic": "Backpropagation in Neural Networks",
            "domain": "machine_learning",
            "difficulty_level": 4,
        }
    """
    try:
        gen = get_generator()
        result = gen.generate(
            topic=request.topic,
            domain=request.domain,
            difficulty_level=request.difficulty_level,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def generate_batch(request: BatchGenerateRequest):
    """
    Generate pedagogical intent for multiple topics.

    Returns list of results (some may have failed).
    """
    try:
        gen = get_generator()
        results = []
        errors = []

        for topic in request.topics:
            try:
                result = gen.generate(
                    topic=topic,
                    domain=request.domain,
                    difficulty_level=request.difficulty_level,
                )
                results.append({
                    "topic": topic,
                    "status": "success",
                    "data": result
                })
            except Exception as e:
                results.append({
                    "topic": topic,
                    "status": "error",
                    "error": str(e)
                })
                errors.append({"topic": topic, "error": str(e)})

        return {
            "results": results,
            "total": len(request.topics),
            "succeeded": len([r for r in results if r["status"] == "success"]),
            "failed": len(errors),
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
