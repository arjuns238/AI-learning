# Pedagogy Engine Restructure Plan

## Problem Statement

Layer 1 is too rigid - forces 6 required fields (`core_question`, `target_mental_model`, `common_misconception`, `disambiguating_contrast`, `concrete_anchor`, `check_for_understanding`) that don't apply to every topic. Visual Planner is a separate step when it could be integrated into Layer 1.

## Design Decisions

- **Completely freeform sections** - LLM invents any section type/title needed
- **Eliminate Layer 2** - Already not being used; Visual Planner merges into Layer 1
- **Clean rewrite** - No backwards compatibility needed

---

## New Architecture

### New Pipeline Flow

```
Topic
  → Layer 1 (generates freeform sections + embedded visual hints)
  → Layer 3 (Manim prompts for sections with visuals)
  → Layer 4 (video generation)
  → Frontend (renders dynamic sections with embedded videos)
```

### New Layer 1 Schema (Freeform)

```python
class VisualHint(BaseModel):
    """Embedded visual opportunity - LLM identifies while generating content."""
    should_animate: bool
    animation_description: Optional[str]  # What to show (2-3 sentences)
    duration_hint: Optional[int]  # 10-30 seconds


class PedagogicalSection(BaseModel):
    """A single freeform pedagogical section."""
    title: str  # LLM-generated title (e.g., "The Core Intuition", "A Common Trap", "Step by Step")
    content: str  # Main content of the section (markdown supported)
    order: int  # Display order (1-based)
    visual: Optional[VisualHint]  # If this section benefits from animation

    # Optional structured content (LLM can use these when appropriate)
    steps: Optional[List[str]]  # For procedural content
    math_expressions: Optional[List[str]]  # For derivations (LaTeX)
    comparison: Optional[dict]  # For contrasts: {item_a: str, item_b: str, difference: str}


class FlexiblePedagogicalIntent(BaseModel):
    """New flexible schema - replaces rigid 6-field structure."""
    topic: str
    summary: str  # 1-2 sentence overview of the lesson
    sections: List[PedagogicalSection]  # 2-8 freeform sections

    # Optional metadata
    domain: Optional[str]
    difficulty_level: Optional[int]  # 1-5

    def get_visual_sections(self) -> List[PedagogicalSection]:
        """Extract sections that need video generation."""
        return [s for s in self.sections if s.visual and s.visual.should_animate]
```

### Updated Prompt Strategy

The new prompt tells the LLM to:
1. Analyze the topic and determine what pedagogical elements it needs
2. Create sections with appropriate titles (not from a fixed list)
3. For each section, decide if animation would help and describe it
4. Include structured content (steps, math, comparisons) when relevant

Example output for "Gradient Descent":
```json
{
  "topic": "Gradient Descent",
  "summary": "How an algorithm finds optimal parameters by iteratively following the steepest path downhill.",
  "sections": [
    {
      "title": "The Core Intuition",
      "content": "Imagine you're lost in dense fog on a mountainside...",
      "order": 1,
      "visual": {
        "should_animate": true,
        "animation_description": "Show a ball on a 3D surface, computing gradient arrows, rolling downhill step by step",
        "duration_hint": 15
      }
    },
    {
      "title": "The Algorithm Step-by-Step",
      "content": "Gradient descent follows a simple procedure...",
      "order": 2,
      "steps": [
        "Compute the gradient at current position",
        "Take a step in the negative gradient direction",
        "Repeat until convergence"
      ],
      "visual": null
    },
    {
      "title": "The Learning Rate Trap",
      "content": "A common mistake is setting the learning rate too high...",
      "order": 3,
      "visual": {
        "should_animate": true,
        "animation_description": "Show side-by-side: small learning rate converging vs large rate oscillating wildly",
        "duration_hint": 12
      }
    },
    {
      "title": "Check Your Understanding",
      "content": "You run gradient descent and it converges to a point, but the loss is still high. What might have happened?",
      "order": 4,
      "visual": null
    }
  ]
}
```

Example output for "What is a Matrix" (simpler topic):
```json
{
  "topic": "What is a Matrix",
  "summary": "A matrix is a rectangular grid of numbers that represents transformations or relationships.",
  "sections": [
    {
      "title": "Matrices as Grids",
      "content": "At its simplest, a matrix is just a rectangular arrangement of numbers...",
      "order": 1,
      "visual": null
    },
    {
      "title": "Why Matrices Matter",
      "content": "Matrices let us represent transformations compactly...",
      "order": 2,
      "visual": {
        "should_animate": true,
        "animation_description": "Show a 2D grid of points, then apply a matrix transformation to stretch/rotate them",
        "duration_hint": 10
      }
    }
  ]
}
```

### Frontend: Dynamic Rendering

Since sections are freeform, the frontend renders them generically:

```tsx
function DynamicSectionRenderer({ sections, clips }) {
  return (
    <div className="space-y-8">
      {sections.sort((a, b) => a.order - b.order).map(section => {
        const clip = clips?.find(c => c.section_order === section.order);

        return (
          <SectionCard key={section.order}>
            <h2 className="text-xl font-semibold">{section.title}</h2>
            <Markdown>{section.content}</Markdown>

            {section.steps && <StepsList steps={section.steps} />}
            {section.math_expressions && <MathBlock expressions={section.math_expressions} />}
            {section.comparison && <ComparisonTable {...section.comparison} />}

            {clip?.video_url && <VideoPlayer src={clip.video_url} />}
          </SectionCard>
        );
      })}
    </div>
  );
}
```

---

## Implementation Steps

### 1. Update Layer 1 Schema
**File:** [layer1/schema.py](packages/pedagogy-engine/layer1/schema.py)
- Add `VisualHint`, `PedagogicalSection`, `FlexiblePedagogicalIntent` classes
- Remove old `PedagogicalIntent` class (or keep for reference during transition)

### 2. Update Layer 1 Prompt
**File:** [prompts/pedagogical_intent.txt](packages/pedagogy-engine/prompts/pedagogical_intent.txt)
- Remove rigid 6-field structure
- Add guidance for freeform section generation
- Include visual identification instructions (merge visual_planner.txt)

### 3. Update Layer 1 Generator
**File:** [layer1/generator.py](packages/pedagogy-engine/layer1/generator.py)
- Update to parse new schema
- Remove dependence on fixed fields

### 4. Update Orchestrator
**File:** [orchestrator/pipeline.py](packages/pedagogy-engine/orchestrator/pipeline.py)
- Remove Visual Planner step (merged into Layer 1)
- Extract visual sections directly from Layer 1 output
- Pass visual sections to Layer 3/4

### 5. Update Layer 3
**File:** [layer3/generator.py](packages/pedagogy-engine/layer3/generator.py)
- Update `generate_for_visual()` to accept `PedagogicalSection` instead of `VisualOpportunity`

### 6. Update Orchestrator Schema
**File:** [orchestrator/schema.py](packages/pedagogy-engine/orchestrator/schema.py)
- Update `FullPipelineResponse` to use new section-based structure
- Remove storyboard references

### 7. Delete Unused Code
- Remove [layer2/](packages/pedagogy-engine/layer2/) directory entirely
- Remove [visual_planner/](packages/pedagogy-engine/visual_planner/) directory entirely

### 8. Update Frontend Types
**File:** [web/src/types/pipeline.ts](packages/web/src/types/pipeline.ts)
- Add TypeScript equivalents of new Python schemas

### 9. Update Frontend Components
- Create `DynamicSectionRenderer` component
- Update learn page to use new component
- Remove old fixed-section components

---

## Verification Plan

1. **Unit test Layer 1** - Generate output for 5+ diverse topics, verify sections are appropriate
2. **Schema validation** - Ensure output validates against new Pydantic schema
3. **Visual extraction** - Verify sections with `should_animate=true` are correctly identified
4. **Layer 3/4 integration** - Confirm Manim prompts generate from section visual hints
5. **End-to-end test** - Topic → Sections → Videos → Rendered page
6. **Edge cases** - Topics with no visual opportunities, math-heavy topics, simple topics

---

## Files Summary

| Action | File |
|--------|------|
| Modify | `packages/pedagogy-engine/layer1/schema.py` |
| Modify | `packages/pedagogy-engine/layer1/generator.py` |
| Modify | `packages/pedagogy-engine/prompts/pedagogical_intent.txt` |
| Modify | `packages/pedagogy-engine/orchestrator/pipeline.py` |
| Modify | `packages/pedagogy-engine/orchestrator/schema.py` |
| Modify | `packages/pedagogy-engine/layer3/generator.py` |
| Delete | `packages/pedagogy-engine/layer2/` (entire directory) |
| Delete | `packages/pedagogy-engine/visual_planner/` (entire directory) |
| Modify | `packages/web/src/types/pipeline.ts` |
| Create | `packages/web/src/components/lesson/DynamicSectionRenderer.tsx` |
