# Agentic Learning Platform Architecture

## Overview

This platform uses an **agent-with-tools** architecture where an educational AI assistant (Layer 0) is the core experience. Video generation is one tool among potentially many that the agent can invoke when pedagogically useful.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│              EDUCATIONAL ASSISTANT AGENT (Layer 0)               │
│                                                                  │
│  A conversational LLM that:                                      │
│  - Streams responses naturally (like ChatGPT)                    │
│  - Maintains conversation context (memory built-in)              │
│  - Understands pedagogy (how people learn)                       │
│  - Has access to TOOLS it can invoke when needed                 │
│                                                                  │
│  Tools available:                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ generate_animation(concept, context, focus_area)        │    │
│  │ → Layer 3 (prompt) → Layer 4 (render) → video URL       │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ (future) generate_quiz(topic, difficulty)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ (future) get_learner_profile()                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    User sees streamed response
                              +
                    Video appears when ready (async)
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Streaming protocol | SSE (Server-Sent Events) | Simpler than WebSocket, works with existing infra |
| Tool execution | Async (non-blocking) | Video renders while agent continues responding |
| LLM for agent | Claude with tool use | Native tool calling, good instruction following |
| Session storage | In-memory (TODO: Supabase) | Simple for now, needs persistence for production |

## Why This Architecture (vs. the old pipeline)

| Old Approach | New Approach |
|--------------|--------------|
| Pipeline: topic → layers → output | Agent decides what to do |
| Video always generated | Video only when pedagogically useful |
| No memory between messages | Conversation context preserved |
| Structured output only | Natural conversation + structured tools |
| Fixed flow | Adaptive based on user needs |

## File Structure

```
packages/pedagogy-engine/agent/
├── __init__.py                 # Package exports
├── schema.py                   # Event types, Message, Session, LearnerContext
├── educational_agent.py        # Core agent with streaming + tool use
└── tools/
    ├── __init__.py             # Tool registry
    └── animation_tool.py       # Wraps Layer 3+4 as a tool

packages/api/routes/
└── chat.py                     # SSE streaming endpoint /api/chat/stream

packages/web/src/
├── hooks/useChat.ts            # React hook for SSE streaming
└── app/chat/page.tsx           # Chat interface at /chat
```

## API Endpoints

### POST /api/chat/stream
Streaming chat endpoint using Server-Sent Events.

**Request:**
```json
{
  "message": "Explain gradient descent",
  "session_id": "optional-session-id"
}
```

**SSE Events:**
```
data: {"type": "text", "content": "Gradient descent is..."}
data: {"type": "tool_start", "tool": "generate_animation", "id": "call_123"}
data: {"type": "tool_result", "tool": "generate_animation", "id": "call_123", "success": true, "result": {"video_url": "/api/agent/video/abc123"}}
data: {"type": "done", "session_id": "uuid-here"}
```

### POST /api/chat
Non-streaming endpoint for simple requests.

## Event Types

The agent yields these events during streaming:

- `TextChunk(content)` - Streamed text
- `ToolCall(id, name, arguments)` - Agent is calling a tool
- `ToolResult(id, name, result, success)` - Tool completed
- `StreamDone()` - Stream finished

## The Animation Tool

When the agent decides a visual would help, it calls `generate_animation`:

```python
class GenerateAnimationTool:
    name = "generate_animation"

    parameters = {
        "concept": "The specific concept to visualize",
        "context": "What the user is trying to understand",
        "focus_area": "Optional: specific part to emphasize",
        "duration_hint": "'short' (5-10s) or 'detailed' (15-30s)"
    }

    async def execute(self, concept, context, focus_area=None, duration_hint=None):
        # Creates minimal PedagogicalIntent/Section
        # Calls Layer 3 → Layer 4
        # Returns AnimationResult with video_url
```

## Session & Learner Context

Sessions track:
- `messages[]` - Conversation history
- `learner_context` - Builds over time:
  - `topics_explored[]`
  - `concepts_struggled_with[]`
  - `learning_preferences{}`
  - `current_topic`

The agent's system prompt includes learner context to personalize responses.

## Frontend Integration

The `useChat` hook handles:
1. Sending messages via fetch POST
2. Parsing SSE events from response stream
3. Updating React state as text streams in
4. Tracking pending animations (loading states)
5. Adding video URLs when tools complete

```typescript
const { messages, isStreaming, pendingAnimations, sendMessage } = useChat();
```

## Future Roadmap

With the agent framework in place:

1. **More tools**: Quiz generation, code sandbox, practice problems
2. **Learner profiles**: Long-term memory of what user knows/struggles with
3. **Adaptive difficulty**: Adjust explanations based on user's level
4. **Supabase sessions**: Persist sessions for logged-in users
5. **Multi-modal**: Voice input/output, interactive diagrams

## Running the System

1. Start the API:
   ```bash
   cd packages/api
   uvicorn main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd packages/web
   npm run dev
   ```

3. Visit `http://localhost:3000/chat` for the new agent-based chat interface.

## Testing

1. **Streaming test**: Send a message, see text appear token-by-token
2. **Tool invocation test**: Ask "explain gradient descent visually" → agent streams response + calls animation tool → video appears
3. **No-tool test**: Ask "what is 2+2" → agent responds without generating unnecessary animation
4. **Memory test**: Send follow-up questions and verify agent uses previous context
