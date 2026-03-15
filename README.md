# Lesson Loom

An adaptive learning system that generates personalized 
explanations of technical concepts **with animated 
visualizations** by reasoning about *how* to teach, not 
just what to say.

## Demo
<video src="https://github.com/user-attachments/assets/6c3a35d5-39d3-4d61-8110-c16e7113cb47" controls width="100%"></video>

Topics demonstrated: backpropagation, transformer attention, 
gradient descent.

---

## The problem with AI tutors

Most AI tutors are LLM wrappers: you ask a question, 
you get an explanation. The explanation quality depends 
entirely on what the LLM happens to generate. There's no 
reasoning about the learner, no pedagogical strategy, no 
structured progression from confusion to understanding.

---

## The approach

Separate pedagogical reasoning from content generation 
through a four-layer pipeline:

**Layer 1: Topic → Pedagogical Intent**  
Given a topic and what the learner already knows, decide 
*what understanding should change* and *why*. Determines 
learning objectives, identifies common misconceptions, 
and selects an explanatory strategy before any content 
is generated.

**Layer 2: Pedagogical Intent → Storyboard**  
Sequence the explanation: what concept comes first, what 
analogy sets up the harder idea, where the learner needs 
to verify understanding before moving on.

**Layer 3: Storyboard → Scene Spec DSL**  
Compile the storyboard into a structured visual spec — 
a domain-specific language describing animations in terms 
of learning primitives (reveal, contrast, transform, 
emphasize) rather than rendering primitives. Also 
generates structured Manim prompts with specific visual 
elements, motion descriptions, and timing.

**Layer 4: Scene Spec → Manim Animation**  
RAG retrieval over 1,000+ Manim examples → LLM generates 
Python code → AST validation → execution with ManimCE. 
This layer knows nothing about pedagogy — it just renders 
what it's given.

The key insight: by the time we reach Layer 4, all 
pedagogical decisions have already been made. The 
renderer is a pure function of the spec.

---

## How the agent decides when to animate

The system uses a LangGraph-orchestrated agent that 
autonomously decides when a visualization would genuinely 
help. It doesn't animate everything, only when it matters:

- Spatial or visual concepts (transformations, graphs, 
  geometric relationships)
- Explicit user visualization requests
- User confusion signals detected in conversation
- Processes that unfold over time (algorithms, 
  state machines)

When triggered, the animation pipeline runs end-to-end: 
Layer 3 generates a structured Manim prompt → Layer 4 
retrieves similar examples from ChromaDB, generates 
Python code, validates via AST, executes with ManimCE, 
uploads to Supabase Storage, and streams a signed video 
URL back to the frontend via SSE.

---

## Architecture
```
ai-learning/
├── packages/
│   ├── pedagogy-engine/   # Python — layers 1-3, 
│   │                      # LangGraph agent, ChromaDB RAG
│   ├── api/               # FastAPI — SSE streaming bridge
│   ├── web/               # Next.js — chat UI, 
│   │                      # KaTeX math, video rendering
│   └── shared/            # TypeScript types mirroring 
│                          # Python Pydantic schemas
```

Full-stack monorepo. The web frontend deploys independently 
of the Manim renderer - UI runs on Vercel, animation 
generation requires local setup due to Manim's 
system-level dependencies.

---

## Why this architecture

The naive approach entangles pedagogy with visualization: 
prompt the LLM to "explain X with visuals." Explanation 
quality and animation quality then fail together and 
improve together, impossible to iterate on either 
independently.

Separating them means:
- Pedagogy engine can be evaluated and improved without 
  touching the renderer
- Different renderers (Manim, Mermaid, plain text) can 
  consume the same scene spec
- The DSL acts as a stable interface between reasoning 
  and rendering
- RAG over Manim examples lives entirely in Layer 4.
  The pedagogy layers never need to know how animations 
  are generated

---

## On hosting

The Next.js frontend and FastAPI backend are 
straightforward to deploy - Vercel + any cloud backend. 
The constraint is Manim.

Manim requires LaTeX, ffmpeg, and Cairo as system-level 
dependencies to compile TeX and encode video frames. 
This rules out serverless platforms and makes 
containerized deployment the only clean option. A 
Dockerized setup with a render queue and Supabase for 
video storage is the right production architecture, but 
adds meaningful infrastructure cost for a personal 
project.

The demo video above was generated locally and shows 
the full end-to-end pipeline. Running it yourself takes 
about 10 minutes - the local experience is the real one.

---

## Stack

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
| Supabase | Video storage |

### Frontend
| Technology | Purpose |
|------------|---------|
| Next.js 16 | React framework |
| React 19 | UI library |
| TypeScript 5 | Type safety |
| Tailwind CSS v4 | Styling |
| KaTeX | Math rendering |
| ReactMarkdown | Content rendering |

---

## Quick start

### Prerequisites

- Node.js 18+
- Python 3.9+
- npm 9+
- [ManimCE](https://docs.manim.community/en/stable/installation.html) 
  (for video rendering — includes LaTeX, ffmpeg, Cairo)

### Installation
```bash
# Install Node dependencies
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
#   OPENAI_API_KEY=sk-...        (optional, for GPT models)
#   SUPABASE_URL=...             (optional, for video storage)
#   SUPABASE_KEY=...
```

### Running
```bash
# Run everything (recommended)
npm run dev

# Or individually:
npm run dev:web    # Next.js frontend → localhost:3000
npm run dev:api    # FastAPI backend  → localhost:8000
```

**Entry points:**
- Chat interface: `http://localhost:3000/chat`
- API docs: `http://localhost:8000/docs`

---

## API reference

### Chat endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/stream` | SSE streaming chat (primary) |
| `POST` | `/api/chat` | Non-streaming response |
| `POST` | `/api/chat/cancel` | Cancel in-progress request |
| `GET` | `/api/chat/session/:id` | Retrieve session history |
| `DELETE` | `/api/chat/session/:id` | Delete session |
| `POST` | `/api/chat/session/new` | Create new session |

### SSE event types
```typescript
{ type: "text",        content: "..." }
{ type: "tool_start",  tool: "generate_animation", id: "..." }
{ type: "tool_result", tool: "...", result: { video_url } }
{ type: "done",        session_id: "..." }
{ type: "cancelled",   session_id: "..." }
{ type: "error",       message: "..." }
```

---

## Development
```bash
# Testing
cd packages/pedagogy-engine
pytest                        # All tests
pytest tests/layer4/          # Animation pipeline only
pytest --cov=agent \
       --cov-report=html      # Coverage report

# Linting
npm run lint

# Build
npm run build
```
