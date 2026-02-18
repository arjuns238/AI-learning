# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Powered Learning System (ML Lesson Loom)** - An educational platform that teaches complex technical concepts (ML, math, physics) through AI-generated pedagogical content and Manim animations.

**Core Philosophy:** Separate pedagogical reasoning (what/how to teach) from visualization (how content is rendered). This ensures learning quality is not entangled with animation or UI concerns.

---

## Architecture

### Monorepo Structure

```
/AI-learning/
├── packages/
│   ├── pedagogy-engine/     # Python - AI pedagogy + video generation
│   ├── api/                 # FastAPI - Backend bridge
│   ├── web/                 # Next.js - Frontend UI
│   └── shared/              # TypeScript - Shared types
├── package.json             # npm workspaces root
└── requirements.txt         # Python dependencies
```

### Agentic Architecture (Current - January 2026)

The platform uses an **agent-with-tools** architecture:

- **Layer 0 (Educational Agent)**: Conversational LLM tutor that IS the learning experience
- **Video as a tool**: Animation generation invoked when pedagogically useful
- **Streaming responses**: Token-by-token like ChatGPT via SSE
- **Session memory**: Conversation context preserved across messages
- **Adaptive**: Agent decides when visuals help (not always generated)

### Layer Pipeline (Used by Animation Tool)

```
Layer 1: Topic → PedagogicalIntent (LLM + few-shot)
Layer 3: PedagogicalSection → ManimPrompt (LLM)
Layer 4: ManimPrompt → Video (LLM + RAG + Manim execution)
```

---

## Key Files

### Backend (pedagogy-engine)

| Component | Path | Purpose |
|-----------|------|---------|
| Agent | `agent/educational_agent.py` | LLM orchestration + streaming |
| Animation Tool | `agent/tools/animation_tool.py` | Wraps Layer 3+4 as tool |
| Agent Schema | `agent/schema.py` | Events, messages, session |
| Layer 1 | `layer1/generator.py` | Topic → pedagogical intent |
| Layer 1 Schema | `layer1/schema.py` | PedagogicalIntent model |
| Layer 3 | `layer3/generator.py` | Section → Manim prompt |
| Layer 4 | `layer4/generator.py` | Prompt → video (RAG + Manim) |
| System Prompt | `prompts/agent_system_prompt.txt` | Agent behavior guidelines |
| Vector Store | `data/vectorstore/chroma.sqlite3` | RAG embeddings (41MB) |

### API

| Component | Path | Purpose |
|-----------|------|---------|
| Main | `api/main.py` | FastAPI app + CORS |
| Chat Routes | `api/routes/chat.py` | SSE streaming endpoint |
| Supabase | `api/supabase_client.py` | Storage + job tracking |

### Frontend (web)

| Component | Path | Purpose |
|-----------|------|---------|
| Chat Page | `src/app/chat/page.tsx` | Conversational interface |
| Main Page | `src/app/page.tsx` | Pipeline interface |
| Layout | `src/app/layout.tsx` | Root layout + fonts |
| Global CSS | `src/app/globals.css` | Design system + animations |
| useChat Hook | `src/hooks/useChat.ts` | SSE streaming logic |
| UI Components | `src/components/ui/` | Button, Card, Input, Badge |

---

## API Endpoints

```
Base: http://localhost:8000

POST /api/chat/stream     - SSE streaming chat (main endpoint)
POST /api/chat            - Non-streaming chat
GET  /api/chat/session/:id - Retrieve session

POST /api/generate        - Generate pedagogical intent
POST /api/pipeline/generate - Full pipeline (topic → video)
GET  /api/pipeline/status/:job_id - Check job status
GET  /api/pipeline/video/:job_id - Stream video
```

### SSE Event Types (chat/stream)

```json
{"type": "text", "content": "..."}          // Streamed text
{"type": "tool_start", "tool": "...", "id": "..."} // Animation started
{"type": "tool_result", "tool": "...", "result": {...}} // Animation ready
{"type": "done", "session_id": "..."}       // Stream complete
{"type": "error", "message": "..."}         // Error occurred
```

---

## Data Structures

### PedagogicalIntent (Layer 1 Output)

```json
{
  "topic": "Gradient Descent",
  "summary": "1-2 sentence overview",
  "domain": "machine_learning",
  "difficulty_level": 3,
  "sections": [{
    "title": "The Core Intuition",
    "content": "markdown content",
    "order": 1,
    "visual": {
      "should_animate": true,
      "animation_description": "A point sliding down a curve...",
      "duration_hint": 15
    },
    "steps": ["Step 1", "Step 2"],
    "math_expressions": ["\\nabla f(x)"]
  }]
}
```

### Chat Message

```typescript
{
  id: string,
  role: "user" | "assistant",
  content: string,
  timestamp: Date,
  animations?: string[],  // Video URLs
  isStreaming?: boolean
}
```

### Learner Context

```python
{
  "topics_explored": ["backpropagation", "gradient descent"],
  "concepts_struggled_with": ["chain rule"],
  "learning_preferences": {"prefers_visuals": true},
  "preferred_difficulty": 3
}
```

---

## Frontend Styling

### Design System

**CSS Framework:** Tailwind CSS v4 with PostCSS

**Configuration:** `packages/web/postcss.config.mjs`

### Color Palette (HSL Variables)

**Light Mode:**
```css
--background: 210 20% 99%     /* Nearly white base */
--foreground: 215 20% 14%     /* Deep blue-gray text */
--primary: 210 45% 45%        /* Steel blue (trust, clarity) */
--secondary: 210 12% 91%      /* Soft cool gray */
--card: 210 15% 97%           /* Blue-tinted surfaces */
--muted: 210 10% 93%          /* Disabled state */
--accent: 210 15% 94%         /* Hover/focus */
--destructive: 0 65% 55%      /* Alert red */
--border: 210 12% 89%         /* Dividers */
--user-bubble: 210 20% 94%    /* User message bg */
--assistant-bg: 210 20% 99%   /* Assistant message bg */
```

**Dark Mode:** Complete color remapping via `.dark` class

### Typography

**Primary Font:** DM Sans (Google Fonts)
- Weights: 400, 500, 600, 700
- CSS Variable: `--font-dm-sans`
- Usage: Body, prose, UI

**Serif Font:** Source Serif 4
- Weights: 400, 500, 600
- CSS Variable: `--font-source-serif`

**Monospace:** JetBrains Mono, SF Mono, Fira Code (code blocks)

### Border Radius Scale

```css
--radius: 0.75rem       /* 12px base */
--radius-sm: 8px
--radius-md: 10px
--radius-lg: 12px
--radius-xl: 16px
```

### Animation Keyframes

```css
@keyframes fade-in { /* 0.4s ease-out, translateY(8px) */ }
@keyframes fade-in-up { /* 0.5s ease-out, translateY(16px) */ }
@keyframes pulse-soft { /* 1.5s infinite, opacity pulse */ }
@keyframes shimmer { /* 2s infinite, loading gradient */ }
```

**Animation Classes:**
- `.animate-fade-in` - Quick appearance
- `.animate-fade-in-up` - Rising fade
- `.animate-pulse-soft` - Streaming cursor
- `.animate-shimmer` - Loading skeleton

### Component Patterns (CVA)

**Button Variants:**
- `default`: bg-primary, text-primary-foreground
- `destructive`: bg-destructive, text-white
- `outline`: border, bg-background
- `secondary`: bg-secondary
- `ghost`: hover:bg-accent
- `link`: text-primary, underline

**Button Sizes:**
- `default`: h-9, px-4
- `sm`: h-8, px-3
- `lg`: h-10, px-6
- `icon`: size-9

**Card:**
- Base: `bg-card rounded-xl border shadow-sm`
- Content padding: `px-6`

### Focus States

```css
.focus-ring {
  outline-none
  focus-visible:ring-2
  focus-visible:ring-primary/30
  focus-visible:ring-offset-2
}
```

### Custom Scrollbar

```css
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 4px;
}
```

### Layout Patterns

**Chat Page Structure:**
```tsx
<div className="h-screen flex flex-col">
  <header className="flex-shrink-0 border-b backdrop-blur-sm" />
  <main className="flex-1 overflow-hidden">
    <div className="max-w-3xl mx-auto px-6 py-8 pb-36">
      {/* Messages */}
    </div>
  </main>
  <div className="fixed bottom-0 left-0 right-0 z-10">
    {/* Input with gradient fade */}
  </div>
</div>
```

### UI Libraries

| Package | Purpose |
|---------|---------|
| `tailwindcss` v4 | CSS framework |
| `class-variance-authority` | Component variants |
| `clsx` + `tailwind-merge` | Class composition |
| `lucide-react` | Icons |
| `@radix-ui/react-*` | Accessible primitives |
| `react-katex` | Math rendering |
| `mermaid` | Diagrams |
| `recharts` | Charts |

---

## Development Commands

### Full Stack Development

```bash
npm install                  # Install all dependencies
npm run dev                  # Run web + api concurrently
npm run dev:web              # Next.js only (localhost:3000)
npm run dev:api              # FastAPI only (localhost:8000)
npm run build                # Build all packages
```

### Python Environment

```bash
cd packages/pedagogy-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate pedagogical intent
python -m layer1.generator --topic "quadratic formula"

# Run tests
pytest
pytest tests/layer1/
pytest --cov=layer1 --cov-report=html
```

### Environment Variables

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
```

---

## Technologies

### Backend
- **Python 3.9+**, FastAPI, Uvicorn
- **Pydantic 2.12+** - Data validation
- **OpenAI 2.15** / **Anthropic 0.76** - LLM APIs
- **Manim 0.19** - Animation engine
- **ChromaDB 1.4** - Vector database (RAG)
- **LangChain + LangGraph** - Agent framework
- **Supabase** - Database + file storage

### Frontend
- **React 19.2.3**, Next.js 16.1.1
- **TypeScript 5**
- **Tailwind CSS v4**
- **Radix UI** - Accessible components
- **KaTeX** - Math rendering
- **Mermaid** - Diagrams

---

## Key Design Principles

1. **Separation of Concerns**: Pedagogy (what to teach) vs Visualization (how to display)
2. **Transparency**: Each layer has inspectable outputs, avoid black-box
3. **Expert Review**: Quality gate + training data source
4. **Multi-Signal Evaluation**: Automated metrics + expert review + learner outcomes
5. **Gradual Automation**: Start with 100% review, reduce as quality stabilizes

---

## Success Metrics

**Current Phase (Months 0-3):**
- 50+ topics generated
- 80%+ expert approval rate
- Automated metrics correlate 0.7+ with expert ratings
- 100+ expert-reviewed examples

---

## Additional Notes

- Always use Context7 MCP when needing library/API documentation
- Use `/supabase/supabase` library for Supabase integration
- Agent decides when to generate animations (not always)
- Streaming uses SSE (Server-Sent Events) for real-time updates
