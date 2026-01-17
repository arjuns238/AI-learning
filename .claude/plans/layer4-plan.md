# Manim Code Generation Strategy (Layer 4)

## Executive Summary

Layer 4 supports **two complementary approaches** for generating Manim code from Layer 3 prompts:

### Approach 1: ChatGPT API (Quick Start) ✅ IMPLEMENTED
- **Status:** Production-ready
- **Method:** GPT-4o-mini with self-repair retry logic
- **Timeline:** Immediate (already implemented)
- **Cost:** ~$0.01-0.05 per video (API calls)
- **Target:** 60-80% execution success rate (empirical)
- **Pros:** Zero setup, fast iteration, good for prototyping
- **Cons:** API costs scale with usage, no fine-tuning control

### Approach 2: Custom Model Training (Long-term) 📋 PLANNED
- **Method:** Multi-stage QLoRA training on DeepSeek-Coder-33B-base
- **Training Pipeline:** DAPT → Step-level SFT → Scene-level SFT
- **Timeline:** 4-6 weeks
- **Cost:** $875-1,175 (one-time training)
- **Target:** 70%+ execution success rate
- **Pros:** Full control, no runtime API costs, domain-optimized
- **Cons:** Upfront time/cost, requires GPU infrastructure

**Current Focus:** Approach 1 for immediate results, Approach 2 for future optimization

---

# Approach 1: ChatGPT API Implementation (Current)

## Architecture

```
Layer 3 Prompt → ChatGPT API → Code Generation → Validation → Manim Execution → Video
                      ↑                                ↓
                      └────── Error Feedback (retry) ──┘
```

## Implementation: [generator.py](../packages/pedagogy-engine/layer4/generator.py)

### Core Components

**1. ManimCodeGenerator**
- Calls OpenAI GPT-4o-mini with Layer 3 prompts
- Extracts Python code from markdown/text responses
- Static validation: AST parsing, import checks, scene class detection
- Default temperature: 0.0 (deterministic)

**2. ManimExecutor**
- Executes generated code via Manim CLI in subprocess
- Configurable resolution (1080p60, 720p30, etc.)
- Timeout protection (600s default)
- Video path detection and verification

**3. Layer4Generator (Orchestrator)**
- Retry logic: up to 3 attempts
- Self-repair: feeds validation/runtime errors back to ChatGPT
- Tracks metadata: source prompts, execution time, success/failure
- Saves execution records as JSON

## Configuration

```python
generator = Layer4Generator(
    code_model="gpt-4o-mini",      # or "gpt-4" for higher quality
    code_temperature=0.0,           # deterministic
    manim_resolution="1080p60",     # video quality
    output_dir="output/videos"      # where videos are saved
)
```

## Self-Repair Strategy

When code fails:
1. **Validation error** → Append error message to prompt, ask ChatGPT to fix
2. **Runtime error** → Include Manim output log (truncated to 2000 chars), request correction
3. **Max 3 attempts** → Prevents infinite loops

## Current Limitations

- No dataset validation yet (scripts exist but not run)
- No systematic evaluation metrics
- Prompt engineering is basic (system + user prompt)
- No caching or deduplication of similar prompts

## Quick Start

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Run with Layer 3 prompt
python -m layer4.generator \
    --prompt-file data/layer3/gradient_descent_manim_prompt.json \
    --code-model gpt-4o-mini \
    --resolution 1080p60 \
    --output-file output/videos/gradient_descent_execution.json
```

---

# Approach 2: Custom Model Training (Planned)

## 1. Base Model & Infrastructure

**Selected Model:** `deepseek-ai/deepseek-coder-33b-base`
- **Why:** Best HumanEval score (75.0%), 338 language support, 10.2T tokens (60% code), strong Python/API knowledge
- **Alternative:** CodeLlama-34B-base (74.4% HumanEval) if DeepSeek unavailable

**Training Method:** QLoRA (4-bit quantization)
- **Benefits:** 79% memory reduction, fits in 24GB VRAM, 50% cost savings
- **Config:** NormalFloat4 quantization, double quantization, bfloat16 compute

**Hardware:** 1x A100 40GB GPU via cloud services (Thunder Compute @ $0.78/hr)

**LoRA Configuration:**
```python
{
    'r': 64,                    # Rank - higher for code generation
    'lora_alpha': 128,          # 2x rank scaling
    'target_modules': ['q_proj', 'k_proj', 'v_proj', 'o_proj',
                       'gate_proj', 'up_proj', 'down_proj'],
    'lora_dropout': 0.05-0.1,   # 0.05 for DAPT, 0.1 for SFT
    'use_rslora': True          # Rank-stabilized LoRA
}
```

---

## 2. Dataset Strategy

### 2.1 Dataset Inventory (Total: ~2.5K-25K examples)

1. **Pure Manim Code** (3Blue1Brown, clean repos) → 5K-10K files
2. **Step-by-step Instructions** (brick-by-brick) → 1K-2K examples (may need synthesis)
3. **High-level Instructions** (ManimBench, bespoke-manim) → 1.5K-3K examples

### 2.2 Quality Audit Pipeline (Week 1)

**Critical Filters:**
- ✅ **MUST execute successfully** (render without errors)
- ✅ Syntax validity (AST parsing)
- ✅ No deprecated Manim APIs (v0.18+ only)
- ✅ No hallucinated methods (validate against Manim API whitelist)
- ✅ De-duplication (>0.95 similarity threshold)

**Audit Script:**
```python
def audit_manim_example(code: str, instruction: str = None) -> dict:
    return {
        'syntax_valid': check_ast_parse(code),
        'imports_valid': verify_manim_imports(code),
        'api_correctness': check_manim_api_usage(code),
        'execution_success': can_render(code),  # CRITICAL
        'instruction_quality': rate_instruction(instruction),
        'complexity_score': measure_complexity(code),
    }
```

**Expected Yield After Filtering:**
- Dataset 1: 3K-6K clean code examples
- Dataset 2: 500-1K step-by-step examples
- Dataset 3: 1K-2K high-level examples

### 2.3 Data Formatting

**Phase 1 - DAPT (Causal LM on pure code):**
```python
{"text": "<|begin_of_code|>\nfrom manim import *\n\nclass Scene(Scene):\n..."}
```

**Phase 2 - Step-level SFT (Multi-turn instruction-following):**
```python
{
    "instruction": "Create gradient descent scene",
    "steps": [
        {"step": 1, "description": "Create 3D surface", "code": "..."},
        {"step": 2, "description": "Add initial point", "code": "..."},
    ],
    "full_code": "..."
}
```

**Phase 3 - Scene-level SFT (Single-turn synthesis):**
```python
{
    "instruction": "Animate gradient descent with ball rolling down loss landscape",
    "code": "from manim import *\n\nclass GradientDescentScene...",
    "metadata": {"pattern": "iterative_process", "complexity": "intermediate"}
}
```

---

## 3. Three-Phase Training Pipeline

### Phase 1: Domain-Adaptive Continued Pretraining (DAPT)

**Purpose:** Teach Manim API fluency before instruction following

**Objective:** Causal LM next-token prediction on pure Manim code

**Configuration:**
- Data: 3K-6K pure code examples
- Context length: 2048 tokens
- Batch size: 8 (global 32-64 with 4-8x gradient accumulation)
- Learning rate: 2e-4 (higher than SFT)
- LR schedule: Cosine decay, 10% warmup
- Epochs: 2-3
- Duration: 8-12 hours
- Cost: $6-10

**Success Criteria:**
- Validation perplexity <2.5
- Code completion 80%+ syntactically valid
- Training loss plateau

**Output:** base_v1 checkpoint (DAPT adapter merged into base model)

---

### Phase 2: Step-Level Supervised Fine-Tuning

**Purpose:** Teach instruction following with explicit ordered steps

**Objective:** Multi-turn instruction → incremental code generation

**Why step-level first?**
- Explicit decomposition reduces complexity
- Teaches compositional building blocks
- Easier debugging (identify which step fails)

**Configuration:**
- Data: 500-1K step-by-step examples
- Batch size: 4 (longer sequences)
- Learning rate: 1e-4 (lower than DAPT)
- LR schedule: Linear decay, 5% warmup
- Epochs: 3-5
- Duration: 4-6 hours
- Cost: $3-5

**Success Criteria:**
- >80% step execution success rate
- Step ordering coherence (manual review)
- API hallucination rate <5%

**Output:** base_v2 checkpoint (Step-SFT adapter merged)

---

### Phase 3: Scene-Level Supervised Fine-Tuning

**Purpose:** Teach high-level intent → complete scene synthesis

**Objective:** Single-turn instruction → full Manim code

**Configuration:**
- Data: 1K-2K high-level examples
- Batch size: 4
- Learning rate: 5e-5 (lowest, final specialization)
- LR schedule: Cosine decay, 3% warmup
- Epochs: 3-4
- Duration: 6-10 hours
- Cost: $5-8

**Success Criteria:**
- >70% execution success on test set
- Instruction adherence >75%
- Human eval: 3.5/5 average on instruction match

**Output:** final_v1 model (production-ready)

---

## 4. Evaluation Strategy

### 4.1 During Training (Every 200 steps)

**Automated Metrics:**
```python
{
    'val_loss': float,
    'val_perplexity': float,
    'execution_success_rate': float,  # % that render successfully
    'runtime_error_rate': float,
    'syntax_valid_rate': float,
    'api_hallucination_rate': float,  # <5% threshold
    'instruction_adherence': float,   # Phases 2-3 only
}
```

### 4.2 Structural Validation

**AST Parsing:** Syntax correctness
**Import Validation:** Correct Manim imports (no deprecated `manimlib`)
**API Whitelist:** Detect hallucinated methods (compare to Manim v0.18 docs)

### 4.3 Execution-Based Validation (CRITICAL)

**Docker-based Manim execution sandbox:**
```python
class ManimExecutor:
    def execute(self, code: str, timeout=30) -> dict:
        # Run in isolated Docker container
        # Return: {'success': bool, 'video_path': str, 'error': str}
```

**Error Categories:**
- Syntax errors (AST catches)
- Runtime errors (AttributeError, TypeError)
- Infinite loops (timeout after 30s)
- Empty/blank output (video validation)

### 4.4 Visual Validation

**Automated:** Frame count check, non-blank frames, file size validation
**Human Eval:** 50 samples, rate instruction match (1-5 Likert scale)
**CLIP Similarity (experimental):** Text instruction vs. key frame embedding

### 4.5 Test Set

**Held-out:** 20% of each dataset (600-1000 examples total)
**Composition:**
- 40% ManimBench (high quality, human-reviewed)
- 40% 3Blue1Brown corpus
- 20% bespoke-manim (synthetic diversity)
**Stratified by:** Complexity (simple/medium/complex), pedagogical pattern

---

## 5. Risks & Mitigation Strategies

| Risk | Mitigation | Detection |
|------|-----------|-----------|
| **Hallucinated APIs** | DAPT on real code, API whitelist validation, constrained decoding | AST + API documentation comparison |
| **Brittle Code** | Diverse training data, augmentation, aggressive dropout (0.1) | Test execution rate vs train execution rate gap >15% |
| **Instruction Drift** | Step-level training, attribute adherence checks, negative examples | Automated attribute extraction and matching |
| **Style Collapse** | Multiple coding styles in data, temperature 0.7-0.9, top-p sampling | Embedding-based clustering, flag if >80% in 2-3 clusters |
| **Execution Failures** | Tiered validation (syntax → import → execution), reward shaping | Execution pipeline with categorized error types |
| **Visual Mismatch** | Human eval, CLIP similarity, pedagogical alignment checks | Manual review + multimodal validation |

---

## 6. Integration with Pedagogy-Engine (Layers 1-3)

### Current Architecture
```
Layer 1 (Pedagogical Intent) → Layer 2 (Storyboard) → Layer 3 (Scene Spec DSL) → Layer 4 (Manim Code)
```

### Layer 3 Output Format (To Be Designed)

**Scene Spec DSL Schema:**
```json
{
  "topic": "Gradient Descent",
  "scene_class_name": "GradientDescentScene",
  "beats": [
    {
      "beat_id": 1,
      "purpose": "set_context",
      "description": "Show loss landscape",
      "visual_elements": [
        {
          "type": "3d_surface",
          "id": "loss_surface",
          "properties": {"function": "u**2 + v**2", "color": "BLUE_E"}
        }
      ],
      "animations": [
        {"type": "Create", "target": "loss_surface", "duration": 2.0}
      ]
    }
  ]
}
```

**Layer 4 receives this structured spec and generates Manim code.**

**Design Philosophy:**
- **Layer 3 = deterministic** (WHAT to show, easy to debug)
- **Layer 4 = learned** (HOW to code it, handles Manim API nuances)

---

## 7. Implementation Timeline

### Week 1: Data Preparation
- Download datasets (ManimBench, bespoke-manim, 3B1B)
- Run quality audit pipeline
- Manual review of 200 samples
- Create train/val/test splits (70/10/20)
- Format for each training phase
- **Deliverable:** Clean, filtered datasets ready for training

### Week 2: Phase 1 - DAPT
- Set up QLoRA training pipeline (Axolotl or Unsloth)
- Train DAPT adapter (8-12 hours GPU)
- Evaluate perplexity and code completion
- Merge adapter into base model
- **Deliverable:** base_v1 checkpoint

### Week 3: Phase 2 - Step-SFT
- Format step-by-step dataset
- Train Step-SFT adapter on base_v1 (4-6 hours GPU)
- Evaluate execution success on step-level tasks
- Merge adapter
- **Deliverable:** base_v2 checkpoint

### Week 4: Phase 3 - Scene-SFT
- Train Scene-SFT adapter on base_v2 (6-10 hours GPU)
- Comprehensive evaluation on test set
- Human eval (50 samples)
- Error analysis and failure categorization
- **Deliverable:** final_v1 model

### Weeks 5-6: Iteration & Integration
- Analyze v1 failures, collect additional data
- Focused retraining on weak areas
- Build Layer 3 Scene Spec compiler (deterministic rules)
- Integrate Layer 1 → 2 → 3 → 4 pipeline
- End-to-end test with video rendering
- **Deliverable:** Production-ready system

---

## 8. Cost Breakdown

| Item | Hours | Rate | Cost |
|------|-------|------|------|
| DAPT training | 10 | $0.78/hr | $8 |
| Step-SFT training | 5 | $0.78/hr | $4 |
| Scene-SFT training | 8 | $0.78/hr | $6 |
| Evaluation & testing | 10 | $0.78/hr | $8 |
| **GPU subtotal** | 33 | | **$26** |
| Iterations (3-5 runs) | | | **$75-175** |
| Human time (40 hrs) | | | **$800-1000** |
| **Total** | | | **$875-1,175** |

---

## 9. Critical Files to Implement

### New Files (Layer 4 infrastructure)

1. **`layer3/scene_spec.py`** - Define Scene Spec DSL schema (bridge Layer 2 → Layer 4)
   - `SceneSpec`, `BeatSpec`, `VisualPrimitive`, `AnimationSpec` Pydantic models

2. **`layer3/scene_spec_compiler.py`** - Deterministic compiler (Storyboard → Scene Spec)
   - Rule-based mapping: beat purpose → visual primitives

3. **`layer4/trainer.py`** - 3-phase training pipeline
   - QLoRA config, adapter merging, evaluation hooks

4. **`layer4/dataset_builder.py`** - Dataset preparation
   - Audit, filter, format, split datasets

5. **`layer4/validator.py`** - Manim execution validator
   - Docker sandbox, AST parsing, API hallucination detection

6. **`layer4/generator.py`** - Inference interface
   - Scene Spec → Manim code generation, post-processing

---

## 10. Success Criteria

### Phase-Specific Targets

**DAPT:**
- ✅ Validation perplexity <2.5
- ✅ Code completion 80%+ syntactically valid
- ✅ No regression on general Python

**Step-SFT:**
- ✅ 80%+ execution success on step-level tasks
- ✅ API hallucination rate <5%
- ✅ Step ordering coherence 90%+

**Scene-SFT:**
- ✅ 70%+ execution success on scene-level test set
- ✅ Instruction adherence 75%+
- ✅ Human eval: 3.5/5 on instruction match

### v1 Launch Criteria (Must-Have)

- Execution success rate ≥70% on held-out test set
- API hallucination rate <5%
- Zero crashes on valid Layer 3 scene specs
- Integration with Layer 1-3 pipeline functional

### v2+ Goals (Nice-to-Have)

- Execution success rate ≥85%
- Human eval scores ≥4.0/5
- Visual-instruction alignment via CLIP >0.75
- Self-repair capability (debug own code)

---

## 11. Iteration Strategy (v1 → v2)

**Failure Analysis → Targeted Improvements:**

- **If execution rate <70%:** More DAPT data (10K examples), increase LoRA rank to 128, add self-repair
- **If hallucination >5%:** Constrained decoding, aggressive filtering, RAG with API docs
- **If instruction drift:** Attribute-specific training, reward shaping, refined step decomposition
- **If visual quality poor:** CLIP-based rewards (RLHF), aesthetic guidelines, human-in-the-loop

**Iteration cycle:** 2-3 weeks per version (1 week training, 1 week eval, 1 week fixes)

---

## 12. Key Insights & Design Decisions

### Why Multi-Stage Training?

1. **DAPT builds foundation:** Model learns Manim API vocabulary before instruction following
2. **Step-level teaches composition:** Explicit decomposition prevents overwhelming complexity
3. **Scene-level enables synthesis:** Once building blocks are known, full scene generation works

**Evidence:** Domain adaptation reduces hallucination, step-wise training improves instruction adherence

### Why QLoRA?

- 79% memory reduction enables 33B models on consumer/mid-tier GPUs
- 50% cost savings with minimal accuracy loss (96-98% retention)
- Faster experimentation (more iterations within budget)

### Why Execution-Based Evaluation?

- **Gold standard:** Code that doesn't render is worthless
- **Early signal:** Catch API misuse, syntax errors immediately
- **Scalable:** Automated, no human required
- **Objective:** Binary success/failure, no ambiguity

### Bottom-Up Approach Justifies Itself

By designing Layer 4 first, we now know **exactly** what Layer 3 should output:
- Structured beat-by-beat visual primitives
- Animation specifications with timing
- Deterministic, debuggable format

This informs Layer 3 design and prevents mismatched interfaces.

---

## Next Steps

1. **Download and audit datasets** (Week 1)
2. **Set up training infrastructure** (Axolotl + Docker validator)
3. **Run Phase 1 (DAPT)** (Week 2)
4. **Iterate through phases 2-3** (Weeks 3-4)
5. **Build Layer 3 Scene Spec compiler** (Week 5)
6. **End-to-end integration test** (Week 6)

**Ready to proceed?** This plan is opinionated, realistic, and executable. First concrete action: Download ManimBench and run the audit pipeline.
