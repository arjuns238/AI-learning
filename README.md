# AI Learning Platform

An AI-powered learning system that separates pedagogical reasoning from visualization to create effective educational content for complex technical topics.

## Architecture

This monorepo contains four packages working together:

```
ai-learning/
├── packages/
│   ├── pedagogy-engine/    # Python - AI pedagogy generation (Layer 1)
│   ├── api/                # FastAPI - Backend bridge
│   ├── web/                # Next.js - Frontend UI
│   └── shared/             # TypeScript types (shared)
```

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment
cp packages/pedagogy-engine/.env.example packages/pedagogy-engine/.env
# Edit .env and add your OpenAI API key

# Install Python dependencies
cd packages/pedagogy-engine && pip install -r requirements.txt && cd ../..
cd packages/api && pip install -r requirements.txt && cd ../..

# Run everything
npm run dev
```

Visit:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Documentation

See [packages/pedagogy-engine/CLAUDE.md](packages/pedagogy-engine/CLAUDE.md) for complete documentation.
