# Layer 4: Manim Code Generation & Validation

This directory implements Manim code generation from Layer 3 prompts using **two complementary approaches**:

## Approaches

### Approach 1: ChatGPT API (Current) ✅ PRODUCTION READY
- Uses OpenAI GPT-4o-mini to generate Manim code
- Includes self-repair retry logic (up to 3 attempts)
- **Status:** Fully implemented and tested
- **Cost:** ~$0.01-0.05 per video
- **Success Rate:** 60-80% (empirical)
- **See:** [generator.py](generator.py)

### Approach 2: Custom Model Training (Planned) 📋
- Train a custom DeepSeek-Coder-33B model via QLoRA
- Three-phase training: DAPT → Step-level SFT → Scene-level SFT
- **Status:** Planned, dataset infrastructure implemented
- **Cost:** $875-1,175 (one-time)
- **Target:** 70%+ execution success
- **See:** [layer4-plan.md](../../.claude/plans/layer4-plan.md)

---

## Quick Start (Approach 1: ChatGPT)

### Prerequisites
```bash
# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Or add to .env file
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Generate a Video

```bash
# From packages/pedagogy-engine directory
python -m layer4.generator \
    --prompt-file layer4/test_prompt_gradient_descent.json \
    --code-model gpt-4o-mini \
    --resolution 480p15 \
    --output-file output/videos/test_execution.json
```

### Example Output
```
✓ OpenAI initialized: gpt-4o-mini
✓ Manim is installed: Manim Community v0.19.1
============================================================
Layer 4: Manim Code Generation & Video Execution
============================================================

Attempt 1/3
✓ Video generated successfully: output/videos/media/videos/.../GradientDescent.mp4
✓ Code executed successfully
Saved execution record to: output/videos/test_execution.json
```

### Output Structure
- **Video file:** `output/videos/media/videos/<temp>/480p15/<SceneName>.mp4`
- **Execution record (JSON):**
  - `code_response`: Generated code, model name, timestamp
  - `execution_result`: Success status, video path, execution time, logs
  - `metadata`: Source prompt info, traceability

---

## Implementation Details (Approach 1)

### Architecture
```
Layer 3 Prompt → ChatGPT API → Code Generation → Validation → Manim Execution → Video
                      ↑                                ↓
                      └────── Error Feedback (retry) ──┘
```

### Core Components

1. **ManimCodeGenerator** ([generator.py:40](generator.py#L40))
   - Calls OpenAI API with Layer 3 prompts
   - Extracts Python code from responses
   - Validates syntax, imports, scene classes

2. **ManimExecutor** ([generator.py:159](generator.py#L159))
   - Executes code via Manim CLI subprocess
   - Supports multiple resolutions (1080p60, 720p30, 480p15)
   - Detects and returns video file paths

3. **Layer4Generator** ([generator.py:290](generator.py#L290))
   - Orchestrates generation → validation → execution
   - Retry logic: up to 3 attempts with error feedback
   - Self-repair: feeds errors back to ChatGPT for fixes

### Self-Repair Strategy
- **Validation error** → Append error to prompt, ask for fix
- **Runtime error** → Include Manim logs (2000 chars), request correction
- **Max attempts:** 3 (prevents infinite loops)

---

## Dataset Infrastructure (Approach 2)

### Overview (Training Prep)

## Quick Start

### Phase 1: Quick Experiment (100 examples per dataset)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the quick experiment
python scripts/run_quick_experiment.py

# This will:
# - Download 100 examples from each of 4 HuggingFace datasets
# - Validate syntax and API usage
# - Analyze dataset characteristics
# - Generate summary report
```

### Individual Tools

**Download datasets:**
```bash
# Quick experiment (100 examples each)
python scripts/download_manim_datasets.py --limit 100

# Full download
python scripts/download_manim_datasets.py

# Specific datasets
python scripts/download_manim_datasets.py --datasets smail_bespoke suienr_manimbench

# List available datasets
python scripts/download_manim_datasets.py --list
```

**Analyze datasets:**
```bash
# Analyze specific dataset
python analysis/analyze_manim_datasets.py --dataset smail_bespoke

# Analyze all
python analysis/analyze_manim_datasets.py --all
```

**Quick validation:**
```python
from layer4.validator_quick import validate_dataset_quick

summary = validate_dataset_quick(
    dataset_file="data/manim_datasets/raw/smail_bespoke/smail_bespoke_raw.jsonl",
    output_file="data/manim_datasets/metadata/smail_bespoke_validation.json"
)

print(f"Syntax valid: {summary['syntax_valid_pct']}%")
print(f"Average quality: {summary['average_quality_score']}")
```

## Datasets

Four HuggingFace datasets are validated:

| Dataset | HF ID | Type | Priority |
|---------|-------|------|----------|
| Smail/bespoke-manim | `Smail/bespoke-manim-preprocessed` | Scene-level | High |
| ManimBench | `SuienR/ManimBench-v1` | Step-level | High |
| Manim Code | `thanhkt/manim_code` | Scene-level | Medium |
| 3Blue1Brown | `BibbyResearch/3blue1brown-manim` | Step-level | High |

## Directory Structure

```
layer4/
├── README.md                         # This file
├── __init__.py
├── validator_quick.py                # Fast validation (no execution)
├── validators/                       # Full validation modules
│   ├── __init__.py
│   ├── syntax_validator.py          # AST parsing, API checks
│   ├── quality_scorer.py            # Multi-dimensional scoring
│   └── deduplicator.py              # Duplicate detection
├── formatters/                       # Data formatting
│   ├── __init__.py
│   └── training_formatter.py        # Convert to DAPT/SFT formats
├── docker/                           # Docker configs
│   └── Dockerfile.manim             # Manim execution environment
└── training/                         # Training scripts
    ├── __init__.py
    └── Dockerfile.training          # Training environment
```

## Data Directory Structure

```
data/manim_datasets/
├── raw/                              # Original downloads
│   ├── smail_bespoke/
│   │   ├── smail_bespoke_raw.jsonl
│   │   └── smail_bespoke_metadata.json
│   └── ...
├── validated/                        # Post-validation
│   ├── dapt_candidates/             # For DAPT training
│   ├── step_level/                  # For step-level SFT
│   └── scene_level/                 # For scene-level SFT
└── metadata/                         # Analysis reports
    ├── validation_reports/
    ├── execution_logs/
    └── quality_scores/
```

## Validation Criteria

### Quick Validation (Phase 1)
- **Syntax**: AST parsing (must be valid Python)
- **Imports**: Must import from `manim` (not deprecated `manimlib`)
- **API Compatibility**: No deprecated or hallucinated methods
- **Quality Score**: 0-1 based on:
  - Has required imports (0.2)
  - Has Scene classes (0.2)
  - No API issues (0.2)
  - Code length appropriate (0.15)
  - Has construct method (0.1)
  - Has animations (0.1)
  - Code cleanliness (0.05)

### Full Validation (Phase 2)
- All quick validation checks
- **Execution Success**: Actually runs Manim in Docker sandbox
- **Visual Validation**: Generates valid video output
- **Deduplication**: Near-duplicate detection (>85% similarity)

## Quality Score Distribution

Examples with quality scores:
- **0.7-1.0**: High quality, ready for training
- **0.5-0.7**: Medium quality, may need filtering
- **0.0-0.5**: Low quality, likely unusable

## API Compatibility

### Approved (Manim v0.18+)
- **Mobjects**: Circle, Square, Text, MathTex, etc.
- **Animations**: Create, Write, FadeIn, Transform, etc.
- **Scenes**: Scene, ThreeDScene, MovingCameraScene

### Deprecated (will be flagged)
- ShowCreation → Use `Create`
- TextMobject → Use `Text` or `Tex`
- FadeInFrom → Use `FadeIn` with shift
- manimlib import → Use `manim`

### Hallucinated (common LLM mistakes)
- `set_color_by_gradient` → Use `set_color`
- `get_center_point` → Use `get_center`
- `set_position` → Use `move_to` or `shift`

## Next Steps

After Phase 1 (Quick Experiment):

1. **Review Results**: Check `data/manim_datasets/metadata/quick_experiment_summary.md`
2. **Adjust Thresholds**: Based on quality distribution
3. **Phase 2**: Implement full validation pipeline with Docker sandbox
4. **Phase 3**: Curated collection (3K-6K examples)
5. **Phase 4**: GPU training (DAPT → Step-SFT → Scene-SFT)

## Dependencies

```
datasets>=2.14.0       # HuggingFace datasets
manim>=0.18.0          # Manim rendering engine
docker>=6.0.0          # Container execution (Phase 2+)
pydantic>=2.0.0        # Data validation
```

## Development Status

- ✅ Phase 1: Quick Experiment - **IMPLEMENTED**
- ⏳ Phase 2: Full Validation Pipeline - **PLANNED**
- ⏳ Phase 3: Curated Collection - **PLANNED**
- ⏳ Phase 4: GPU Training - **PLANNED**

## Contributing

When adding new validation logic:

1. Follow existing patterns (Pydantic schemas, unit tests)
2. Update this README
3. Add tests in `tests/layer4/`
4. Run validation on test dataset before committing

## Support

For issues or questions about Layer 4 implementation:
- Check the main plan: `.claude/plans/jolly-doodling-church.md`
- Review existing layer patterns in `layer1/` and `layer2/`
- See integration tests in `tests/integration/`
