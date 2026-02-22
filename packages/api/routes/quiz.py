"""
Quiz generation endpoints - create quizzes from pedagogical intent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from quiz.generator import QuizGenerator
from quiz.schema import EnhancedQuiz
from layer1.schema import PedagogicalIntentWithMetadata

router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz from pedagogical intent."""
    pedagogical_intent: PedagogicalIntentWithMetadata
    num_questions: Optional[int] = None
    api_provider: Optional[str] = None
    model_name: Optional[str] = None


class QuizGenerateResponse(BaseModel):
    """Response with generated quiz."""
    quiz: EnhancedQuiz
    generation_model: str
    generation_time_ms: Optional[float] = None


class BatchQuizGenerateRequest(BaseModel):
    """Request to generate quizzes for multiple pedagogical intents."""
    intents: List[PedagogicalIntentWithMetadata]
    api_provider: Optional[str] = None
    model_name: Optional[str] = None


class BatchQuizGenerateResponse(BaseModel):
    """Response with multiple generated quizzes."""
    quizzes: List[EnhancedQuiz]
    generation_model: str
    total_questions: int
    generation_time_ms: Optional[float] = None


# ============================================
# Global Generator Instance
# ============================================

_generator = None


def get_quiz_generator(
    model_name: Optional[str] = None,
    api_provider: Optional[str] = None
) -> QuizGenerator:
    """
    Get or create a quiz generator instance.
    
    Args:
        model_name: Optional LLM model name
        api_provider: Optional API provider (openai or anthropic)
    
    Returns:
        QuizGenerator instance
    """
    global _generator
    
    # If specific providers requested, create new instance
    if model_name or api_provider:
        return QuizGenerator(model_name=model_name, api_provider=api_provider)
    
    # Otherwise use cached global instance
    if _generator is None:
        _generator = QuizGenerator()
    
    return _generator


# ============================================
# Endpoints
# ============================================

@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generate a quiz from pedagogical intent.
    
    Takes the output from Layer 1 (pedagogical intent with sections)
    and generates a conceptual multiple-choice quiz.
    
    Example:
        POST /api/quiz/generate
        {
            "pedagogical_intent": {
                "intent": {
                    "topic": "Backpropagation",
                    "summary": "...",
                    "sections": [...]
                },
                "metadata": {...}
            }
        }
    
    Returns:
        QuizGenerateResponse with EnhancedQuiz containing questions
    """
    import time
    
    try:
        start_time = time.time()
        
        # Get generator with specified model/provider if given
        generator = get_quiz_generator(
            model_name=request.model_name,
            api_provider=request.api_provider
        )
        
        # Generate quiz from pedagogical intent
        quiz = generator.generate(request.pedagogical_intent)
        
        generation_time_ms = (time.time() - start_time) * 1000
        
        return QuizGenerateResponse(
            quiz=quiz,
            generation_model=generator.model_name,
            generation_time_ms=generation_time_ms
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quiz generation failed: {str(e)}"
        )


@router.post("/batch-generate", response_model=BatchQuizGenerateResponse)
async def batch_generate_quizzes(request: BatchQuizGenerateRequest):
    """
    Generate quizzes for multiple pedagogical intents.
    
    Takes a list of Layer 1 outputs and generates a quiz for each.
    
    Example:
        POST /api/quiz/batch-generate
        {
            "intents": [
                {"intent": {...}, "metadata": {...}},
                {"intent": {...}, "metadata": {...}},
            ]
        }
    
    Returns:
        BatchQuizGenerateResponse with list of quizzes
    """
    import time
    
    try:
        start_time = time.time()
        
        if not request.intents:
            raise ValueError("No intents provided for batch generation")
        
        # Get generator
        generator = get_quiz_generator(
            model_name=request.model_name,
            api_provider=request.api_provider
        )
        
        # Generate quiz for each intent
        quizzes = []
        for intent in request.intents:
            quiz = generator.generate(intent)
            quizzes.append(quiz)
        
        total_questions = sum(len(quiz.questions) for quiz in quizzes)
        generation_time_ms = (time.time() - start_time) * 1000
        
        return BatchQuizGenerateResponse(
            quizzes=quizzes,
            generation_model=generator.model_name,
            total_questions=total_questions,
            generation_time_ms=generation_time_ms
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch quiz generation failed: {str(e)}"
        )


@router.get("/info")
async def quiz_generation_info():
    """
    Get information about the quiz generation service.
    
    Returns:
        Information about available models and configuration
    """
    import os
    
    generator = get_quiz_generator()
    
    return {
        "service": "Quiz Generation",
        "current_model": generator.model_name,
        "api_provider": generator.api_provider,
        "description": "Generates conceptual multiple-choice quizzes from pedagogical intent (Layer 1 output)",
        "supported_providers": ["openai", "anthropic"],
        "endpoints": {
            "generate": "POST /api/quiz/generate - Single quiz generation",
            "batch_generate": "POST /api/quiz/batch-generate - Batch quiz generation",
            "info": "GET /api/quiz/info - This endpoint"
        }
    }
