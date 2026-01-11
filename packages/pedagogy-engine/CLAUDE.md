# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI-Powered Learning System** focused on teaching complex technical concepts (ML, math, etc.) through a layered pedagogical approach.

**Core Philosophy:** Separate pedagogical reasoning (how people learn) from visualization/rendering (how content is displayed). This decomposition ensures learning quality is not entangled with animation or UI concerns.

## Architecture: Four-Layer Design

### Layer 1: Topic → Pedagogical Intent (LEARNED/PROMPTED)
- **Purpose:** Decide what understanding should change in the learner
- **Output Schema:**
  ```json
  {
    "core_question": "What the learner is trying to understand",
    "target_mental_model": "The conceptual framework to build",
    "common_misconception": "A typical wrong understanding",
    "disambiguating_contrast": "A comparison that clarifies the concept",
    "concrete_anchor": "A specific example to ground understanding",
    "check_for_understanding": "A question to verify comprehension"
  }
  ```
- **Implementation:** Start with prompt engineering + few-shot exemplars → transition to fine-tuned model
- **Critical Files:**
  - [layer1/generator.py](layer1/generator.py) - Generation logic, prompt templates, API calls
  - [layer1/schema.py](layer1/schema.py) - Pydantic models, validation rules
  - [layer1/evaluator.py](layer1/evaluator.py) - Automated quality metrics
  - [data/exemplars.json](data/exemplars.json) - Few-shot exemplar database
  - [prompts/pedagogical_intent.txt](prompts/pedagogical_intent.txt) - Master prompt template

### Layer 2: Pedagogical Intent → Storyboard (RULE-BASED initially)
- **Purpose:** Sequence the explanation (beats, contrasts, understanding checks)
- **Implementation:** Start with deterministic patterns, possibly learned later
- **Critical Files:** [layer2/storyboard.py](layer2/storyboard.py)

### Layer 3: Storyboard → Scene Spec DSL (DETERMINISTIC)
- **Purpose:** Compile storyboard into structured visual primitives (axes, points, transformations)
- **Implementation:** Deterministic compiler for reliability and validation
- **Critical Files:** [layer3/scene_spec.py](layer3/scene_spec.py)

### Layer 4: Scene Spec → Renderable Output (DETERMINISTIC)
- **Purpose:** Convert DSL to concrete outputs (Manim code/video)
- **Implementation:** Treated as a compiler, not a learned model

## Development Commands

### Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate  # On Windows

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt
```

### Running Layer 1 Generation
```bash
# Generate pedagogical intent for a topic
python -m layer1.generator --topic "quadratic formula" --output output.json

# Validate output against schema
python -m layer1.schema --validate output.json

# Run quality evaluation
python -m layer1.evaluator --input output.json
```

### Testing
```bash
# Run all tests
pytest

# Run Layer 1 tests only
pytest tests/layer1/

# Run integration tests (full pipeline)
pytest tests/integration/

# Run with coverage
pytest --cov=layer1 --cov-report=html
```

### Expert Review Workflow
```bash
# Generate batch of topics for review
python -m layer1.generator --batch topics.txt --output-dir review/

# Launch expert review interface (once implemented)
python -m layer1.review_interface --input-dir review/
```

## Key Design Principles

### 1. Separation of Concerns
Keep Layer 1 focused on *what to teach* and *how learners think*, NOT *how to animate it*. Pedagogy ≠ Visualization.

### 2. Expert Review as Data Generation
Expert reviews are dual-purpose:
- Quality gate for production content
- Training data source (approved examples, preference pairs, negative signals)

Design all review interfaces to capture rich, structured feedback.

### 3. Transparency Over Black-Box
Prefer explainable, debuggable systems. Each layer has inspectable outputs. Avoid end-to-end neural approaches that can't be debugged.

### 4. Gradual Automation
**Phase 1 (Months 0-3):** 100% expert review, prompt + exemplars
**Phase 2 (Months 3-6):** 50-100% expert review, transition to fine-tuning
**Phase 3 (Months 6+):** 10-20% expert review, preference optimization with learner feedback

### 5. Multi-Signal Evaluation
Combine three signal types:
- **Automated metrics:** Schema validation, specificity, novelty, coherence
- **Expert evaluation:** 5-dimension rubric (accuracy, relevance, clarity, concreteness, assessment)
- **Learner outcomes:** Comprehension success, time-to-understanding, satisfaction

Watch for disagreements between signals - these are the most informative cases.

### 6. Forward Compatibility
Design Layer 1 outputs with Layer 2/3 in mind. The `concrete_anchor` field must be visualization-friendly. Consider adding optional fields like `spatial_metaphor` or `visual_hint` if needed.

### 7. Provenance and Safety
Track where every piece of content came from. Required for:
- Commercial viability (IP safety)
- Quality debugging (attribution of failures)
- Continuous improvement (A/B testing, feedback loops)

## Modeling Strategy

### Current Phase: Prompt Engineering + Few-Shot Exemplars

**Why this approach?**
- Pure prompting is too inconsistent (wastes expert time)
- Early fine-tuning is premature (don't know what "good" looks like yet)
- Few-shot exemplars encode principles explicitly while building training data

**Implementation:**
1. Maintain 10-15 high-quality exemplars spanning diverse pedagogical patterns
2. Use explicit prompt template with pedagogical principles (clarity, relevance, contrast, grounding, validity)
3. Generate with Claude Opus 4.5 or similar frontier model
4. Validate with automated metrics
5. 100% expert review initially

### Transition to Fine-Tuning (Months 3-6)

**Trigger conditions:**
- 100-200 expert-reviewed outputs accumulated
- Expert approval rate consistently >80%
- Automated metrics correlate >0.7 with expert ratings

**Approach:**
- Supervised Fine-Tuning (SFT) on expert-approved examples
- Use smaller, faster model (Claude Sonnet-class)
- A/B test against prompt baseline
- Reduce expert review to 50% sampling

### Preference Optimization (Months 6+)

**With learner feedback data:**
- DPO/RLHF using comprehension outcomes
- Multi-objective: `Loss = α·expert_loss + β·learner_outcome_loss`
- Gradually shift weight from expert (α) to learner (β) signals
- Maintain 10-20% expert review as safety net

## Data Collection

### Three Data Artifacts per Expert Review

1. **Positive Examples (SFT):**
   - Expert-approved outputs (as-is or after minor edits)
   - Store: `(topic, generated_output, expert_edit, final_approved)`

2. **Preference Pairs (DPO):**
   - Expert revisions: `(topic, AI_version, expert_version)`
   - Expert ratings: create ranked pairs from scores

3. **Negative Signals:**
   - Rejected outputs + reasoning
   - Common failure patterns
   - Use for filtering, hard negatives, critiques

### Metadata to Capture
- Topic domain, difficulty level
- Expert reviewer ID (track inter-rater variation)
- Generation strategy (which exemplars, which model)
- Time spent on review (quality proxy)
- Timestamp (track model improvements)

## Testing Strategy

### Unit Tests
- Layer 1: Schema compliance, quality heuristics pass/fail
- Validation: Edge cases (empty fields, overly long text, non-specific language)
- Exemplar system: Selection logic (domain matching, diversity)

### Integration Tests
- L1→L2: Does pedagogical intent map to valid storyboard?
- L1→L2→L3: Do "golden path" examples render correctly?
- Failure attribution: Which layer is responsible when pipeline breaks?

### Human Evaluation
- Expert review cadence: Weekly for first 3 months
- Inter-rater reliability: Cohen's kappa >0.6 required
- Calibration: Compare expert predictions to learner outcomes

### Learner Outcomes (when available)
- Pre/post comprehension tests
- A/B testing of pedagogical strategies
- Retention tests (1 week, 1 month)
- Progression: Does understanding enable subsequent learning?

## Common Pitfalls to Avoid

### 1. Over-Learning Expert Biases
**Risk:** Model learns reviewer idiosyncrasies, not generalizable pedagogy.
**Mitigation:** Require 2-3 expert approvals for training data, track inter-rater reliability, weight learner outcomes over time.

### 2. Layer Boundary Mismatch
**Risk:** Pedagogical intent works in isolation but doesn't map to visualizations.
**Mitigation:** Ensure `concrete_anchor` is spatial/visual, add integration tests, maintain 20-30 "golden path" examples.

### 3. Data Contamination / IP Risk
**Risk:** Model memorizes existing educational content.
**Mitigation:** Novelty checks, source documentation, require transformation, watermark all outputs.

### 4. Insufficient Learner Feedback
**Risk:** Feedback is sparse, noisy, or confounded (maybe Layer 3 is bad, not Layer 1).
**Mitigation:** Design for multiple feedback modes, don't over-index early data, use causal attribution via partial pipeline tests.

## Configuration

### Layer 1 Config ([config/layer1_config.yaml](config/layer1_config.yaml))
```yaml
model:
  provider: "anthropic"  # or "openai"
  model_name: "claude-opus-4-5"
  temperature: 0.7

exemplars:
  count: 5  # Number of exemplars to include in prompt
  selection_strategy: "domain_diverse"  # or "random", "similarity"

quality_thresholds:
  specificity_min: 0.6
  novelty_min: 0.4  # Similarity to exemplars should be < 0.85
  coherence_min: 0.7

expert_review:
  sampling_rate: 1.0  # 100% initially, reduce over time
  require_approval_count: 1  # Increase to 2-3 for training data
```

## Success Metrics by Phase

### Months 0-3 (Current Phase)
- Volume: 50+ topics generated
- Quality: 80%+ expert approval rate
- Consistency: Automated metrics correlate 0.7+ with expert ratings
- Diversity: Exemplars span 5+ pedagogical patterns
- Data: 100+ expert-reviewed examples in training database

### Months 4-6
- Volume: 100+ topics total
- Quality: Fine-tuned model matches or beats prompt baseline
- Efficiency: Expert review reduced to 50%
- Integration: Learner feedback pipeline operational
- Pipeline: Full L1→L2→L3 works for 20+ golden examples

### Months 6+
- Volume: 50-100 topics with learner data
- Outcomes: Measurable comprehension improvements
- Automation: 80%+ auto-approved, 20% flagged for review
- Feedback: Multi-objective model deployed
- Business: Clear path to commercialization (IP clean, quality proven)

## Immediate Priorities

### What to Start With (Month 0-1)
1. Create 10-15 high-quality exemplars (THIS IS THE BOTTLENECK)
2. Build prompt template with explicit pedagogical principles
3. Set up expert review interface (Airtable is fine initially)
4. Generate first 20 topics, iterate on exemplars based on feedback
5. Research public datasets (1 week max) - extract patterns, don't copy

### What NOT to Do Yet
- Fine-tuning (wait until 100+ approved examples)
- Complex tooling (start simple, iterate based on actual needs)
- Layer 2/3 implementation (focus on L1 quality first)
- Large-scale generation (quality over quantity in early stages)

### Success Signal to Scale
When expert approval rate hits 80%+ AND automated metrics correlate 0.7+ with expert ratings, you're ready to scale and consider fine-tuning.

## Why Layered vs End-to-End

This project uses a layered architecture instead of end-to-end "topic → animation" because:

**Robustness:** Errors isolated per layer vs failure anywhere breaks everything
**Debuggability:** Can inspect each layer's output vs black box
**Iteration Speed:** Update one layer quickly vs retrain entire model
**Scalability:** Parallelize layer improvements vs scale entire pipeline
**Expert Oversight:** Clear review points per stage vs no intermediate verification
**Commercialization:** Clear provenance per component vs harder IP verification

The only advantage of end-to-end (theoretical joint optimization) is impractical given:
- Sparse learner feedback (takes months to accumulate)
- Difficulty attributing success/failure to specific decisions
- Need for expert oversight (can't rely purely on outcomes)

## Additional Resources

- Full modeling strategy: See approved plan in `.claude/plans/cryptic-painting-seahorse.md`
- Pedagogical research: Concept inventories, learning progressions literature
- Public datasets: Khan Academy, OpenStax, ASSISTments (use for pattern extraction, not copying)
