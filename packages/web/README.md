# ML Lesson Loom

A structured, visual-first learning interface for ML concepts. Enter a topic once, get intuition, a concrete example, one visual, and a mini quiz.

## Setup

1. Install dependencies:

```bash
npm install
```

2. Provide an OpenAI API key (and optional model):

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
```

3. Run the dev server:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Notes

- Lesson generation uses `src/app/api/lesson/route.ts` with a fixed teaching prompt.
- Visual rendering supports Recharts plots, Mermaid diagrams, and HTML tables.
