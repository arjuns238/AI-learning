"""
Chat API Routes: Streaming conversational interface for the educational agent

Provides SSE (Server-Sent Events) streaming for real-time chat with the agent.
"""

import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import EducationalAgent, Session, LearnerContext, MessageRole
from agent.schema import TextChunk, ToolCall, ToolResult, StreamDone


router = APIRouter()

# In-memory session store (replace with Supabase in production)
sessions: Dict[str, Session] = {}


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Non-streaming response format."""
    session_id: str
    response: str
    animations: list = []


def get_or_create_session(session_id: Optional[str] = None) -> Session:
    """Get existing session or create a new one."""
    if session_id and session_id in sessions:
        return sessions[session_id]

    # Create new session
    new_id = session_id or str(uuid.uuid4())
    session = Session(
        session_id=new_id,
        messages=[],
        learner_context=LearnerContext()
    )
    sessions[new_id] = session
    return session


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Event types:
    - text: Streamed text content {"type": "text", "content": "..."}
    - tool_start: Agent is calling a tool {"type": "tool_start", "tool": "...", "id": "..."}
    - tool_result: Tool completed {"type": "tool_result", "tool": "...", "result": {...}}
    - done: Stream complete {"type": "done", "session_id": "..."}
    - error: Error occurred {"type": "error", "message": "..."}
    """
    session = get_or_create_session(request.session_id)

    async def event_generator():
        try:
            agent = EducationalAgent()

            # Track the full response for session history
            full_response = ""
            animations = []

            async for event in agent.chat(
                message=request.message,
                conversation_history=session.messages,
                learner_context=session.learner_context,
                session=session
            ):
                if isinstance(event, TextChunk):
                    full_response += event.content
                    yield f"data: {json.dumps({'type': 'text', 'content': event.content})}\n\n"

                elif isinstance(event, ToolCall):
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': event.name, 'id': event.id, 'arguments': event.arguments})}\n\n"

                elif isinstance(event, ToolResult):
                    result_data = {
                        'type': 'tool_result',
                        'tool': event.name,
                        'id': event.id,
                        'success': event.success,
                        'result': event.result
                    }
                    if event.error:
                        result_data['error'] = event.error

                    # Track animations
                    if event.name == "generate_animation" and event.success:
                        animations.append(event.result.get("video_url"))

                    yield f"data: {json.dumps(result_data)}\n\n"

                elif isinstance(event, StreamDone):
                    # Save to session history
                    session.add_message(MessageRole.USER, request.message)
                    session.add_message(
                        MessageRole.ASSISTANT,
                        full_response,
                        animations=animations
                    )

                    yield f"data: {json.dumps({'type': 'done', 'session_id': session.session_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@router.post("")
async def chat_sync(request: ChatRequest) -> ChatResponse:
    """
    Non-streaming chat endpoint for simple requests.
    Returns complete response after processing.
    """
    session = get_or_create_session(request.session_id)

    try:
        agent = EducationalAgent()

        full_response = ""
        animations = []

        async for event in agent.chat(
            message=request.message,
            conversation_history=session.messages,
            learner_context=session.learner_context,
            session=session
        ):
            if isinstance(event, TextChunk):
                full_response += event.content
            elif isinstance(event, ToolResult):
                if event.name == "generate_animation" and event.success:
                    animations.append(event.result.get("video_url"))

        # Save to session
        session.add_message(MessageRole.USER, request.message)
        session.add_message(
            MessageRole.ASSISTANT,
            full_response,
            animations=animations
        )

        return ChatResponse(
            session_id=session.session_id,
            response=full_response,
            animations=animations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session details including conversation history."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return session.to_dict()


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions[session_id]
    return {"status": "deleted", "session_id": session_id}


@router.post("/session/new")
async def create_session():
    """Create a new session."""
    session = get_or_create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat()
    }
