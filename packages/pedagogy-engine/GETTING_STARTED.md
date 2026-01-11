# Getting Started with Layer 1 Generation

## Setup (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Verify Setup

```bash
# Test the schema
python layer1/schema.py

# Validate exemplars
python scripts/validate_exemplars.py
```

## Generate Your First Pedagogical Intent

### Single Topic

```bash
python layer1/generator.py --topic "Backpropagation in Neural Networks"
```

This will:
1. Load your 3 ML exemplars
2. Build a prompt with pedagogical principles
3. Call Claude Opus to generate pedagogical intent
4. Validate against schema
5. Save to `output/generated/backpropagation_in_neural_networks.json`

### Multiple Topics

```bash
python layer1/generator.py --topics "Learning Rate" "Batch Normalization" "Dropout"
```

### From File

```bash
# Create a topics file
cat > topics.txt << EOF
Attention Mechanisms
Batch Size Selection
Feature Engineering
Cross-Validation
EOF

# Generate for all topics
python layer1/generator.py --topics-file topics.txt
```

## Customize Generation

```bash
# Use more exemplars in prompt
python layer1/generator.py --topic "ReLU Activation" --num-exemplars 3

# Adjust temperature (higher = more creative)
python layer1/generator.py --topic "Batch Normalization" --temperature 0.9

# Use different model
python layer1/generator.py --topic "Dropout" --model claude-sonnet-4
```

## What Gets Generated

For each topic, you get a JSON file with:

```json
{
  "intent": {
    "topic": "...",
    "core_question": "...",
    "target_mental_model": "...",
    "common_misconception": "...",
    "disambiguating_contrast": "...",
    "concrete_anchor": "...",
    "check_for_understanding": "...",
    "spatial_metaphor": "..."
  },
  "metadata": {
    "model_name": "claude-opus-4-5",
    "temperature": 0.7,
    "exemplar_ids": ["ml_gradient_descent_01", ...],
    "generation_timestamp": "2026-01-10T..."
  },
  "needs_review": true
}
```

## Next Steps

### 1. Expert Review (Week 1)

After generating 5-10 topics:
1. Review each output for quality
2. Check pedagogical accuracy
3. Verify misconceptions are common
4. Ensure concrete anchors are visualizable

### 2. Dataset Analysis (Week 1)

```bash
# Download datasets
# - Eedi/Vanderbilt Math Misconceptions
# - AAAS Project 2061 Science Assessment

# Place in data/raw/
mkdir -p data/raw

# Run analysis
python analysis/analyze_datasets.py --dataset eedi --input data/raw/eedi.csv
python analysis/analyze_datasets.py --dataset aaas --input data/raw/aaas.csv

# Review findings in analysis/eedi_findings.md and analysis/aaas_findings.md
```

### 3. Iterate on Exemplars (Week 1-2)

Based on generated outputs and dataset analysis:
1. Identify gaps in exemplar coverage
2. Add 2-3 more exemplars to reach 5 total
3. Update exemplars based on what works/doesn't work
4. Re-validate with `python scripts/validate_exemplars.py`

### 4. Scale Generation (Week 2-4)

Once expert approval rate hits 80%:
1. Generate 50+ topics
2. Track which ones need revision
3. Build training dataset from approved examples
4. Analyze failure patterns

## Current Status

✅ **Completed (January 10, 2026):**
- Project structure created
- Schema definition with validation ([layer1/schema.py](layer1/schema.py))
- 3 ML exemplars created and validated ([data/exemplars.json](data/exemplars.json))
- Prompt template with pedagogical principles ([prompts/pedagogical_intent.txt](prompts/pedagogical_intent.txt))
- Generator implementation ([layer1/generator.py](layer1/generator.py))
- Dataset analysis tools ([analysis/analyze_datasets.py](analysis/analyze_datasets.py))

🔄 **In Progress:**
- Generate first 5-10 test topics
- Expert review of generated content
- Dataset analysis (Eedi/AAAS)

⏳ **Next Up:**
- Build evaluator with automated quality metrics
- Set up expert review interface
- Expand exemplar set to 5-10 based on findings

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Make sure you copied `.env.example` to `.env`
- Add your API key to `.env`
- Restart your terminal/shell

**"Exemplar file not found"**
- Make sure you're running from project root directory
- Check that `data/exemplars.json` exists

**"JSON parsing failed"**
- Model may have wrapped JSON in markdown
- Check `output/` directory for the raw response
- Try lowering temperature (more deterministic)

**Generated quality is poor**
- Try using more exemplars: `--num-exemplars 5`
- Review exemplar quality - are they strong examples?
- Check if topic is too vague - be more specific
