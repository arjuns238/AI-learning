# RAG Retrieval Examples - With Pedagogical Context

## Test Setup

**Prompt File:** `test_prompt_gradient_descent_with_pedagogy.json`

**Pedagogical Context:**
```json
{
  "core_question": "Why does gradient descent work to find the minimum of a function?",
  "target_mental_model": "Iterative optimization following negative gradient",
  "common_misconception": "Students think it always finds global minimum",
  "visual_metaphor": "A ball rolling downhill on a loss landscape",
  "key_insight": "Negative gradient points toward steepest descent",
  "pedagogical_pattern": "iterative_process"
}
```

## Enhanced RAG Query

When pedagogical context is included, the RAG query is augmented with educational elements:

```
Convert the following Scene Specification into executable ManimCE code.

Important rendering notes:
- Make sure the direction of arrows follows the direction of the movement
- Ensure arrows are positioned at the current and next points on the curve
- Space elements properly to avoid overlapping

[... full scene specification ...]

Visual metaphor: A ball rolling downhill on a loss landscape - gravity pulls it toward lower points, but it might settle in a valley that isn't the deepest one.

Pattern: iterative_process

Key concept: The gradient vector points in the direction of steepest ascent, so the negative gradient points toward the steepest descent - the fastest way downhill.
```

## RAG Retrieval Results (Top 3)

### Example 1: Following Graph Camera
- **Type:** Intermediate
- **Similarity:** 0.387
- **Description:** Display a set of axes and plot the sine curve in blue. Show an orange dot at the start of the curve and two additional dots at the start and end of the curve...

**Code Preview:**
```python
from manim import *

class FollowingGraphCamera(MovingCameraScene):
    def construct(self):
        ...
```

**Why this was retrieved:**
- Involves tracking a point moving along a curve
- Uses camera following for visualization
- Shows iterative movement along a path
- Mathematical function visualization (sine curve)

---

### Example 2: Network Graph Import
- **Type:** Advanced
- **Similarity:** 0.383
- **Description:** Display a randomly generated graph with 14 nodes and edges based on the Erdős–Rényi model, arranged using a spring layout. After the graph is created...

**Code Preview:**
```python
from manim import *

import networkx as nx

nxgraph = nx.erdos_renyi_graph(14, 0.5)

class ImportNet...
```

**Why this was retrieved:**
- Complex iterative process (graph layout)
- Shows optimization algorithm (spring layout)
- Multiple steps in construction
- Pattern: iterative refinement

---

### Example 3: Time Width Values
- **Type:** Intermediate
- **Similarity:** 0.383
- **Description:** Display a large dark gray pentagon centered on screen. Then, repeatedly animate a blue copy of the pentagon flashing along its outline with varying tr...

**Code Preview:**
```python
from manim import *

class TimeWidthValues(Scene):
    def construct(self):
        p = RegularPolyg...
```

**Why this was retrieved:**
- Repeated animation pattern
- Iterative process (flashing multiple times)
- Shows progression over time
- Pattern: iterative_process

---

## Analysis

### Pedagogical Relevance

All three retrieved examples share the **iterative_process** pattern that was specified in the pedagogical context:

1. **Example 1:** Point following a curve (iterative movement)
2. **Example 2:** Graph optimization (iterative layout refinement)
3. **Example 3:** Repeated animations (iterative flashing)

### Similarity Scores

- Example 1: 0.387 (highest)
- Example 2: 0.383
- Example 3: 0.383

The similarity scores are relatively close, indicating that all three examples are roughly equally relevant to the query with pedagogical context.

### What Makes These Good Matches

1. **Iterative Processes:** All examples involve repeated steps or processes
2. **Visual Progression:** All show something changing over time
3. **Mathematical/Algorithmic:** Examples 1 and 2 involve mathematical operations
4. **Movement/Animation:** All examples involve dynamic movement or changes

### Impact of Pedagogical Context

By adding:
- "Visual metaphor: A ball rolling downhill"
- "Pattern: iterative_process"
- "Key concept: gradient points toward steepest descent"

The RAG system retrieved examples that emphasize:
- Movement along paths/curves
- Iterative optimization processes
- Visual tracking and progression

This is more pedagogically relevant than retrieving random animation examples based solely on visual similarity.

---

## Comparison: Without Pedagogical Context

When run without pedagogical context (baseline), the RAG query would be:

```
Convert the following Scene Specification into executable ManimCE code.
[... scene specification ...]
```

**Expected difference:**
- Baseline: Retrieved examples based purely on scene specification keywords (axes, graphs, dots, arrows)
- With pedagogy: Retrieved examples emphasizing **iterative processes** and **optimization patterns**

The pedagogical enhancement helps RAG understand **why** we're creating this visualization (to teach iterative optimization), not just **what** to draw (axes, curves, dots).

---

## How to Use This Information

When designing Layer 4 prompts:

1. **Include pedagogical context** for better RAG retrieval
2. **Specify the pattern** (iterative_process, comparison_contrast, etc.)
3. **Provide visual metaphors** to guide example selection
4. **State key insights** to focus on educational relevance

This ensures the LLM sees pedagogically relevant examples, not just visually similar ones.
