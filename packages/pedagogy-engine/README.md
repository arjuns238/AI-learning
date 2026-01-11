# Manim Modeling: AI-Powered Learning System

An AI-powered learning platform that separates pedagogical reasoning from visualization to create effective educational content for complex technical topics.

## Quick Start

```bash
# Set up environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys

# Test the schema
python layer1/schema.py

# Analyze datasets (once you have them)
python analysis/analyze_datasets.py --dataset eedi --input data/raw/eedi.csv
```

## Project Structure

```
manim_modeling/
├── layer1/          # Topic → Pedagogical Intent
├── layer2/          # Pedagogical Intent → Storyboard
├── layer3/          # Storyboard → Scene Spec DSL
├── data/            # Exemplars and training data
├── prompts/         # Prompt templates
├── config/          # Configuration files
├── analysis/        # Dataset analysis tools
├── tests/           # Test suite
└── CLAUDE.md        # Guidance for Claude Code
```

## Current Phase: Month 0-1 Foundation

We're in the initial setup phase, focusing on:
1. ✅ Project structure created
2. ✅ Schema definition (layer1/schema.py)
3. ✅ Dataset analysis tools
4. 🔄 Hand-crafting 3-5 initial exemplars
5. ⏳ Building prompt template
6. ⏳ First generation tests

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete project documentation for AI assistance
- [Plan](/.claude/plans/cryptic-painting-seahorse.md) - Full modeling strategy and roadmap

## Next Steps

1. Download Eedi/Vanderbilt and AAAS datasets
2. Run dataset analysis to extract patterns
3. Hand-craft 3-5 high-quality exemplars
4. Build prompt template
5. Generate first 5-10 topics for expert review

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.
