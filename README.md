# Lesson Loom

An AI-powered learning assistant that teaches complex technical concepts through conversation and **dynamically generated visual animations**. Ask about machine learning, math, or physics — get clear explanations with custom Manim animations rendered on-the-fly.

![Lesson Loom Demo](media/demo-placeholder.png)

## Why This Project

Most AI tutors generate text. Lesson Loom generates **videos**.

The system uses an agentic architecture where an LLM tutor autonomously decides when a concept needs visual demonstration, then generates and renders a custom Manim animation in real-time. This required solving several interesting problems:

- **Agentic tool use** — LangChain agent that invokes animation generation as a tool
- **RAG-powered code generation** — Vector search over 1000+ Manim examples to improve code quality
- **Real-time streaming** — SSE-based token streaming with concurrent video generation
- **Graceful cancellation** — Interrupt in-progress LLM calls and subprocess execution

**Example interaction:** Ask "How does gradient descent work?" and receive:
1. A conversational explanation with LaTeX math rendering
2. An auto-generated animation showing optimization on a loss surface
3. Follow-up Q&A with full conversation context

## Features

- **Conversational Interface** — ChatGPT-style streaming responses via Server-Sent Events
- **AI-Generated Animations** — Manim videos created on-demand when pedagogically useful
- **Intelligent Tool Use** — Agent autonomously decides when visuals help understanding
- **RAG-Enhanced Generation** — ChromaDB vector store improves Manim code quality
- **Session Persistence** — Conversation context preserved across messages
- **Request Cancellation** — Cancel in-flight requests including video rendering subprocesses
- **Math Rendering** — LaTeX equations via KaTeX

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Next.js Frontend                        │
│              (React 19 · Tailwind v4 · KaTeX)                │
└────────────────────────────┬────────────────────────────────┘
                             │ SSE Streaming
┌────────────────────────────▼────────────────────────────────┐
│                      FastAPI Backend                         │
│            (Session Management · Request Cancellation)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                   Educational Agent (LangGraph)              │
│                                                              │
│   ┌────────────────────────────────────────────────────┐    │
│   │              Animation Generation Tool              │    │
│   │                                                     │    │
│   │   Layer 3: Concept → Structured Manim Prompt       │    │
│   │   Layer 4: Prompt → Code (RAG + LLM) → Video       │    │
│   │                                                     │    │
│   │   ChromaDB ──► Code Generation ──► ManimCE         │    │
│   └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    Supabase Storage
                   (Video file hosting)
```

### Monorepo Structure

```
packages/
├── pedagogy-engine/     # Python — AI agent + animation pipeline
│   ├── agent/           # LangGraph educational agent
│   ├── layer3/          # Concept → Manim prompt generation
│   ├── layer4/          # RAG + code generation + execution
│   └── data/vectorstore # ChromaDB embeddings (Manim examples)
├── api/                 # FastAPI — Streaming endpoints
├── web/                 # Next.js — Chat interface
└── shared/              # TypeScript type definitions
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- npm 9+
- [ManimCE](https://docs.manim.community/en/stable/installation.html) (for video rendering)

### Installation

```bash
# Install Node dependencies (npm workspaces)
npm install

# Set up Python environment for pedagogy engine
cd packages/pedagogy-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..

# Install API dependencies
cd packages/api
pip install -r requirements.txt
cd ../..

# Configure environment variables
cp .env.example .env
# Edit .env and add:
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENAI_API_KEY=sk-...  (optional, for GPT models)
#   SUPABASE_URL=...       (optional, for video storage)
#   SUPABASE_KEY=...
```

### Running the Application

```bash
# Run everything (recommended)
npm run dev

# Or run individually:
npm run dev:web      # Next.js frontend (http://localhost:3000)
npm run dev:api      # FastAPI backend (http://localhost:8000)
```

**URLs:**
- **Chat Interface:** http://localhost:3000/chat
- **API Documentation:** http://localhost:8000/docs

## API Reference

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/stream` | SSE streaming chat (primary endpoint) |
| `POST` | `/api/chat` | Non-streaming chat response |
| `POST` | `/api/chat/cancel` | Cancel in-progress request |
| `GET` | `/api/chat/session/:id` | Retrieve session history |
| `DELETE` | `/api/chat/session/:id` | Delete session |
| `POST` | `/api/chat/session/new` | Create new session |

### SSE Event Types

```typescript
{ type: "text", content: "..." }                    // Streamed text token
{ type: "tool_start", tool: "generate_animation", id: "..." }  // Animation started
{ type: "tool_result", tool: "...", result: { video_url } }    // Animation ready
{ type: "done", session_id: "..." }                 // Stream complete
{ type: "cancelled", session_id: "..." }            // Request cancelled
{ type: "error", message: "..." }                   // Error occurred
```

## How Animation Generation Works

When the agent determines a visual would help understanding:

1. **Layer 3 (Prompt Generation)** — Converts concept + context into a structured Manim prompt with specific visual elements, motion descriptions, and timing

2. **Layer 4 (Code Generation)** — RAG retrieval over 1000+ Manim examples → LLM generates Python code → AST validation → execution with ManimCE

3. **Delivery** — Video uploaded to Supabase Storage → signed URL streamed to frontend

**The agent autonomously decides when to invoke this tool based on:**
- Spatial/visual concepts (transformations, graphs, geometric relationships)
- User confusion signals in conversation
- Explicit visualization requests
- Processes that unfold over time (algorithms, state machines)

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.9+ | Runtime |
| FastAPI | REST API + SSE streaming |
| LangChain / LangGraph | Agent orchestration |
| Claude Sonnet 4.5 | Primary LLM (configurable) |
| ManimCE | Animation rendering |
| ChromaDB | Vector store for RAG |
| Sentence Transformers | Embeddings |
| Supabase | Video storage + (planned) auth |

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 16 | React framework |
| React 19 | UI library |
| TypeScript 5 | Type safety |
| Tailwind CSS v4 | Styling |
| KaTeX | Math rendering |
| ReactMarkdown | Content rendering |

## Development

### Commands

```bash
# Development
npm run dev           # Run web + api concurrently
npm run dev:web       # Next.js only (localhost:3000)
npm run dev:api       # FastAPI only (localhost:8000)

# Build
npm run build         # Build all packages

# Testing
cd packages/pedagogy-engine
pytest                # Run all tests
pytest tests/layer4/  # Test animation pipeline
pytest --cov=agent --cov-report=html  # Coverage report

# Linting
npm run lint
```

### Project Structure Deep Dive

```
packages/pedagogy-engine/
├── agent/
│   ├── educational_agent.py   # LangGraph agent with tool calling
│   ├── schema.py              # Pydantic models for events/messages
│   └── tools/
│       └── animation_tool.py  # Wraps Layer 3+4 as LangChain tool
├── layer3/
│   └── generator.py           # Concept → Manim prompt
├── layer4/
│   ├── generator.py           # RAG + LLM → Manim code → video
│   └── manim_api_reference.py # Curated API docs for prompting
├── prompts/
│   └── agent_system_prompt.txt # Educational agent behavior
└── data/
    └── vectorstore/           # ChromaDB with Manim examples
```

## Roadmap

- [x] Streaming conversational agent (LangGraph)
- [x] Animation generation as agentic tool
- [x] RAG over Manim examples (ChromaDB)
- [x] Session persistence with context
- [x] Request cancellation (including subprocesses)
- [x] SSE streaming with tool call events
- [ ] User authentication (Supabase Auth)
- [ ] Conversation history persistence
- [ ] Fine-tuned pedagogy model
- [ ] Learner progress tracking
- [ ] Multi-modal input (diagrams, images)

## License

Private project
