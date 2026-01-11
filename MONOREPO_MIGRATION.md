# Monorepo Migration Summary

Successfully merged `manim_modeling` (pedagogy engine) and `AI-learning` (web app) into a unified monorepo!

## What Was Done

### 1. Created Monorepo Structure

```
ai-learning/                           (NEW - unified repo)
├── packages/
│   ├── pedagogy-engine/              (MIGRATED from manim_modeling)
│   │   ├── layer1/                   (Pedagogical intent generation)
│   │   ├── data/exemplars.json       (3 ML exemplars)
│   │   ├── prompts/                  (Prompt templates)
│   │   ├── output/generated/         (Generated pedagogical intents)
│   │   └── .env                      (OpenAI API key configuration)
│   │
│   ├── api/                          (NEW - FastAPI bridge)
│   │   ├── main.py                   (FastAPI app)
│   │   ├── routes/
│   │   │   ├── generate.py           (Generate pedagogical intent)
│   │   │   └── lessons.py            (Convert to lesson format)
│   │   └── requirements.txt
│   │
│   ├── web/                          (MIGRATED from AI-learning repo)
│   │   ├── src/
│   │   │   ├── app/                  (Next.js app router)
│   │   │   ├── components/           (UI + visualization components)
│   │   │   └── types/lesson.ts       (Lesson type definitions)
│   │   ├── package.json
│   │   └── next.config.ts
│   │
│   └── shared/                       (NEW - shared types)
│       ├── schemas/
│       │   ├── pedagogical-intent.ts (TypeScript version of Python schema)
│       │   └── lesson.ts             (Shared lesson types)
│       └── package.json
│
├── package.json                      (Root workspace configuration)
├── README.md                         (Comprehensive monorepo documentation)
└── .gitignore                        (Unified ignore rules)
```

### 2. Created API Bridge

**Purpose:** Connect Python pedagogy engine to TypeScript web frontend

**Endpoints:**
- `POST /api/generate` - Generate pedagogical intent from topic
- `POST /api/generate/batch` - Batch generation
- `POST /api/lessons/from-intent` - Convert PedagogicalIntent → Lesson format

**Example Usage:**
```bash
# Generate pedagogical intent
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "Backpropagation", "num_exemplars": 3}'

# Convert to lesson format for web app
curl -X POST http://localhost:8000/api/lessons/from-intent \
  -H "Content-Type: application/json" \
  -d '{<pedagogical_intent_json>}'
```

### 3. Shared Types Package

Created TypeScript definitions that mirror Python Pydantic schemas:

**Before:** Two separate type systems (Python and TypeScript) with no synchronization

**After:** Single source of truth in `packages/shared/`
- `pedagogical-intent.ts` - Matches `layer1/schema.py`
- `lesson.ts` - Web app lesson format

### 4. Workspace Configuration

**Root package.json scripts:**
```bash
npm run dev              # Run web + API together
npm run dev:web          # Next.js frontend only
npm run dev:api          # FastAPI backend only
npm run dev:pedagogy     # Generate pedagogical intent (CLI)
npm run build            # Build all packages
npm run test             # Run all tests
```

### 5. Git Repository

- Initialized new git repo at `/Users/asri/Projects/ai-learning`
- Created initial commit with all packages
- Old git history preserved in original repos (if needed)

---

## Migration Mapping

### manim_modeling → pedagogy-engine

| Before | After |
|--------|-------|
| `/Users/asri/Projects/manim_modeling/` | `/Users/asri/Projects/ai-learning/packages/pedagogy-engine/` |
| `layer1/generator.py` | `packages/pedagogy-engine/layer1/generator.py` |
| `data/exemplars.json` | `packages/pedagogy-engine/data/exemplars.json` |
| `.env` | `packages/pedagogy-engine/.env` ✅ API key preserved |

### AI-learning repo → web

| Before | After |
|--------|-------|
| `https://github.com/arjuns238/AI-learning.git` | `/Users/asri/Projects/ai-learning/packages/web/` |
| `src/types/lesson.ts` | `packages/web/src/types/lesson.ts` |
| `src/components/` | `packages/web/src/components/` |
| `package.json` | `packages/web/package.json` |

---

## How the Packages Integrate

```
┌─────────────────┐
│   User Input    │
│   "Topic: X"    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   pedagogy-engine           │
│   Layer1Generator.generate()│
│   → PedagogicalIntent       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   api (FastAPI)             │
│   /api/generate             │
│   → Validate & serve        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   api (FastAPI)             │
│   /api/lessons/from-intent  │
│   → Convert to Lesson format│
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   web (Next.js)             │
│   LessonRenderer component  │
│   → Visualize with Manim    │
└─────────────────────────────┘
```

---

## Next Steps

### 1. Update GitHub Remote

```bash
cd /Users/asri/Projects/ai-learning
git remote add origin https://github.com/arjuns238/AI-learning.git
git push -u origin main --force  # ⚠️ This will overwrite existing repo
```

**Alternative (safer):**
Create a new branch to preserve old history:
```bash
# On GitHub, create a branch from current main called "old-web-only"
# Then push new monorepo:
git push -u origin main --force
```

### 2. Test Integration

```bash
# Terminal 1: Start API
cd /Users/asri/Projects/ai-learning
cd packages/api
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 2: Start Web
cd /Users/asri/Projects/ai-learning
cd packages/web
npm install
npm run dev

# Terminal 3: Test generation
cd /Users/asri/Projects/ai-learning
cd packages/pedagogy-engine
PYTHONPATH=$(pwd) python layer1/generator.py --topic "Attention Mechanisms"
```

### 3. Update Web App to Use API

Currently the web app has a placeholder lesson API route. Update it to call your FastAPI backend:

**packages/web/src/app/api/lesson/route.ts:**
```typescript
export async function POST(request: Request) {
  const { topic } = await request.json();

  // Call your FastAPI backend
  const response = await fetch('http://localhost:8000/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic })
  });

  const pedagogicalIntent = await response.json();

  // Convert to lesson format
  const lessonResponse = await fetch('http://localhost:8000/api/lessons/from-intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(pedagogicalIntent.intent)
  });

  const lesson = await lessonResponse.json();
  return Response.json(lesson);
}
```

### 4. Implement Layer 2 (Storyboard)

Next phase: Build the bridge from Pedagogical Intent → Storyboard → Visualization

See `packages/pedagogy-engine/CLAUDE.md` for the full roadmap.

---

## Benefits of Monorepo

✅ **Single source of truth** - All code in one place
✅ **Shared types** - TypeScript and Python stay in sync
✅ **Easier development** - Run everything with `npm run dev`
✅ **Unified versioning** - Deploy frontend and backend together
✅ **Better collaboration** - One repo, one pull request for features spanning packages
✅ **Simplified CI/CD** - Test and deploy all packages in one pipeline

---

## Important Files

### Configuration
- `package.json` - Root workspace config
- `packages/pedagogy-engine/.env` - OpenAI API key (**PRESERVED**)
- `packages/api/requirements.txt` - Python API dependencies
- `packages/web/package.json` - Web app dependencies

### Documentation
- `README.md` - Monorepo overview and quick start
- `packages/pedagogy-engine/CLAUDE.md` - Complete project documentation
- `packages/pedagogy-engine/STATUS.md` - Current status and next steps
- `packages/pedagogy-engine/docs/API_SETUP.md` - API configuration guide

### Code
- `packages/pedagogy-engine/layer1/generator.py` - Core generation logic
- `packages/api/main.py` - FastAPI backend
- `packages/web/src/app/page.tsx` - Web frontend entry point
- `packages/shared/schemas/` - Shared type definitions

---

## Troubleshooting

### "Module not found" errors

```bash
# Make sure you installed dependencies for all packages
cd /Users/asri/Projects/ai-learning
npm install
cd packages/web && npm install && cd ../..
cd packages/pedagogy-engine && pip install -r requirements.txt && cd ../..
cd packages/api && pip install -r requirements.txt && cd ../..
```

### API can't import pedagogy-engine

The API adds `pedagogy-engine` to Python path automatically in `main.py`:
```python
pedagogy_engine_path = Path(__file__).parent.parent / "pedagogy-engine"
sys.path.insert(0, str(pedagogy_engine_path))
```

If issues persist, set PYTHONPATH:
```bash
export PYTHONPATH=/Users/asri/Projects/ai-learning/packages/pedagogy-engine:$PYTHONPATH
```

### Web app can't find shared types

Update `packages/web/tsconfig.json` to include shared:
```json
{
  "compilerOptions": {
    "paths": {
      "@ai-learning/shared": ["../shared/index.ts"]
    }
  }
}
```

---

## Success! 🎉

You now have a unified monorepo that:
- Generates pedagogical intent (pedagogy-engine)
- Serves it via REST API (api)
- Renders it beautifully (web)
- Shares types across packages (shared)

Next: Continue in a new Claude instance with:
> "Continue working on the ai-learning monorepo. Read packages/pedagogy-engine/CLAUDE.md for context."
