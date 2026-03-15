# Lesson Loom

An adaptive learning system that generates personalized 
explanations of technical concepts **with animated 
visualizations** by reasoning about *how* to teach, not 
just what to say.

## Demo
<video src="https://github.com/user-attachments/assets/6c3a35d5-39d3-4d61-8110-c16e7113cb47" controls width="100%"></video>


Topics demonstrated: backpropagation, transformer attention, 
gradient descent.

## The problem with AI tutors

Most AI tutors are LLM wrappers: you ask a question, 
you get an explanation. The explanation quality depends 
entirely on what the LLM happens to generate. There's no 
reasoning about the learner, no pedagogical strategy, no 
structured progression from confusion to understanding.

## The approach

Separate pedagogical reasoning from content generation 
through a four-layer pipeline:

**Layer 1 — Topic → Pedagogical Intent**  
Given a topic and what the learner already knows, decide 
*what understanding should change* and *why*. This is the 
reasoning layer — it determines learning objectives, 
identifies common misconceptions, and selects an 
explanatory strategy before any content is generated.

**Layer 2 — Pedagogical Intent → Storyboard**  
Sequence the explanation: what concept comes first, what 
analogy sets up the harder idea, where does the learner 
need to verify understanding before moving on.

**Layer 3 — Storyboard → Scene Spec DSL**  
Compile the storyboard into a structured visual spec — 
a domain-specific language that describes animations in 
terms of learning primitives (reveal, contrast, 
transform, emphasize) rather than rendering primitives.

**Layer 4 — Scene Spec → Manim Animation**  
Render the scene spec into actual animations using Manim. 
This layer knows nothing about pedagogy — it just renders 
what it's given.

The key insight: by the time we reach Layer 4, all 
pedagogical decisions have already been made. The 
renderer is a pure function of the spec.

## Architecture
```
ai-learning/
├── packages/
│   ├── pedagogy-engine/   # Python — layers 1-3
│   ├── api/               # FastAPI — bridge layer
│   ├── web/               # Next.js — UI + lesson rendering
│   └── shared/            # TypeScript types mirroring 
│                          # Python Pydantic schemas
```

Full-stack monorepo. The web frontend is deployable 
independently of the Manim renderer — UI runs on Vercel, 
animation generation requires local setup (Manim has 
system-level dependencies that make serverless hosting 
expensive).

## Why this architecture

The naive approach entangles pedagogy with visualization: 
prompt the LLM to "explain X with visuals." This means 
explanation quality and animation quality fail together 
and improve together, making it impossible to iterate 
on either independently.

Separating them means:
- Pedagogy engine can be evaluated and improved without 
  touching the renderer
- Different renderers (Manim, Mermaid, plain text) can 
  consume the same scene spec
- The DSL acts as a stable interface between reasoning 
  and rendering

## Stack

Python · FastAPI · Next.js · TypeScript · Manim · 
OpenAI/Claude API · Pydantic · Tailwind CSS

## Running locally

[existing setup instructions — keep these]
