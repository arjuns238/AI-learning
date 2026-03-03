# AI Learning Platform

An AI-powered learning system that separates pedagogical reasoning from visualization to create effective educational content for complex technical topics.

## Architecture

This monorepo contains four packages working together:

```
ai-learning/
├── packages/
│   ├── pedagogy-engine/    # Python - AI pedagogy generation (Layer 1-3)
│   ├── api/                # FastAPI - Backend bridge
│   ├── web/                # Next.js - Frontend UI
│   └── shared/             # TypeScript types (shared across packages)
└── MONOREPO_MIGRATION.md   # Migration history and details
```

## Core Philosophy

Separate pedagogical reasoning (how people learn) from visualization (how content is displayed). This decomposition ensures learning quality is not entangled with animation or UI concerns.

### Four-Layer Design

1. **Layer 1: Topic → Pedagogical Intent** - Decide what understanding should change in the learner
2. **Layer 2: Pedagogical Intent → Storyboard** - Sequence the explanation
3. **Layer 3: Storyboard → Scene Spec DSL** - Compile into visual primitives
4. **Layer 4: Scene Spec → Renderable Output** - Convert to Manim animations

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm 9+

### Installation

```bash
# Install Node dependencies
npm install

# Set up Python environment for pedagogy engine
cd packages/pedagogy-engine
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
cd ../..

# Set up Python environment for API
cd packages/api
pip install -r requirements.txt
cd ../..

# Configure OpenAI API keys
cp packages/pedagogy-engine/.env.example packages/pedagogy-engine/.env
cp packages/web/.env.example packages/web/.env.local
# Edit both .env files and add your OPENAI_API_KEY
```

### Running the System

```bash
npm run dev
```

Visit:
- **Web App**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Generate Pedagogical Intent (CLI)

```bash
cd packages/pedagogy-engine
source venv/bin/activate
python -m layer1.generator --topic "Backpropagation in Neural Networks"
```

## Package Overview

### packages/pedagogy-engine
The core AI system for generating pedagogical content. Contains:
- **layer1/** - Pedagogical intent generation (OpenAI/Claude integration)
- **layer2/** - Storyboard generation (planned)
- **layer3/** - Scene spec DSL (planned)
- **data/exemplars.json** - Few-shot learning exemplars
- **prompts/** - Prompt templates
- **output/** - Generated pedagogical intents

See [packages/pedagogy-engine/CLAUDE.md](packages/pedagogy-engine/CLAUDE.md) for detailed documentation.

### packages/api
FastAPI backend that bridges the Python pedagogy engine with the TypeScript web frontend.

**Endpoints:**
- `POST /api/generate` - Generate pedagogical intent from topic
- `POST /api/generate/batch` - Batch generation
- `POST /api/lessons/from-intent` - Convert PedagogicalIntent → Lesson format

### packages/web
Next.js web application with interactive visualizations.

**Features:**
- Lesson rendering with multiple visual types (plots, diagrams, attention heatmaps)
- Interactive quizzes
- Mermaid diagram support
- Responsive UI with Tailwind CSS

### packages/shared
Shared TypeScript type definitions that mirror Python Pydantic schemas.
- `pedagogical-intent.ts` - Matches layer1/schema.py
- `lesson.ts` - Web app lesson format

## Development Commands

```bash
# Install dependencies
npm install

# Build all packages
npm run build

# Run tests
npm run test

# Run linting
npm run lint

# Clean all build artifacts
npm run clean
```

## Documentation

- [CLAUDE.md](packages/pedagogy-engine/CLAUDE.md) - Complete project documentation
- [STATUS.md](packages/pedagogy-engine/STATUS.md) - Current status and next steps
- [GETTING_STARTED.md](packages/pedagogy-engine/GETTING_STARTED.md) - Getting started guide
- [MONOREPO_MIGRATION.md](MONOREPO_MIGRATION.md) - Migration history

## Project Status

Currently in **Phase 1** (Months 0-3):
- Layer 1 (Pedagogical Intent Generation) is operational
- Using prompt engineering + few-shot exemplars with GPT-4/Claude
- Building expert review pipeline
- Targeting 50+ high-quality topics with 80%+ expert approval

## License

Private project
