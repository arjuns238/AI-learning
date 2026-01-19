# RAG Implementation for Layer 4

## Overview

The Layer 4 generator now includes a RAG (Retrieval-Augmented Generation) system using ChromaDB and pandas to load the ManimBench-v1 dataset. This augments the LLM-based code generation with similar examples from the dataset.

## Implementation Summary

### What Was Done

1. **Added pandas support**: The `ManimVectorStore` can now load the ManimBench-v1 dataset using pandas from HuggingFace parquet files
2. **ChromaDB integration**: Vector embeddings are stored persistently in `/Users/asri/Projects/AI-learning/packages/pedagogy-engine/data/vectorstore/`
3. **Automatic retrieval**: When RAG is enabled, the generator automatically retrieves top-k similar examples and includes them in the prompt

### Key Components

- **ManimVectorStore** ([generator.py:60-240](generator.py#L60-L240)): Manages vector embeddings and retrieval
  - Uses `all-MiniLM-L6-v2` sentence transformer for embeddings
  - Stores 317 examples from ManimBench-v1
  - Supports cosine similarity search

- **ManimBenchRetriever** ([generator.py:244-294](generator.py#L244-L294)): Thin wrapper for easy retrieval
  - `retrieve(query, top_k=3)` method returns similar examples

- **Integration with ManimCodeGenerator** ([generator.py:380-413](generator.py#L380-L413)): Augments prompts with retrieved examples

## Usage

### 1. Initialize Vector Store (One-Time Setup)

```bash
# Build the vector store from ManimBench-v1
python layer4/init_vectorstore.py

# Check status
python layer4/init_vectorstore.py --status

# Rebuild if needed
python layer4/init_vectorstore.py --rebuild
```

### 2. Generate Code with RAG

```bash
# Enable RAG (default)
python -m layer4.generator \
  --prompt-file layer4/test_prompt_gradient_descent.json \
  --api-provider anthropic \
  --use-rag \
  --rag-examples 3

# Disable RAG
python -m layer4.generator \
  --prompt-file layer4/test_prompt_gradient_descent.json \
  --api-provider anthropic \
  --no-rag

# Use more examples
python -m layer4.generator \
  --prompt-file layer4/test_prompt_gradient_descent.json \
  --api-provider anthropic \
  --use-rag \
  --rag-examples 5
```

### 3. Programmatic Usage

```python
from layer4.generator import Layer4Generator, ManimVectorStore
from layer3.schema import ManimPromptWithMetadata
import json

# Initialize generator with RAG enabled
generator = Layer4Generator(
    api_provider="anthropic",
    code_model="claude-sonnet-4-5-20250929",
    use_rag=True,
    rag_examples=3
)

# Load prompt
with open("layer4/test_prompt_gradient_descent.json") as f:
    prompt_data = json.load(f)
prompt = ManimPromptWithMetadata(**prompt_data)

# Generate code (RAG automatically retrieves similar examples)
result = generator.generate(prompt)
```

### 4. Test RAG Retrieval

```bash
# Test the RAG system
python layer4/test_rag.py
```

## How It Works

1. **Prompt received**: User provides a Layer 3 prompt describing the animation
2. **Embedding**: The prompt is converted to a vector embedding using `all-MiniLM-L6-v2`
3. **Retrieval**: Top-k most similar examples are retrieved from the vector store
4. **Augmentation**: Retrieved examples are added to the prompt as few-shot examples
5. **Generation**: The augmented prompt is sent to the LLM (Claude/GPT)
6. **Execution**: Generated code is validated and executed by Manim

## Performance

| Operation | Time |
|-----------|------|
| Vector store initialization | ~2-3 minutes (first time) |
| Vector store loading | <100ms (subsequent) |
| Retrieval per query | 10-50ms |
| Total overhead per generation | ~50-100ms |

## Dataset Statistics

- **Source**: ManimBench-v1 (SuienR/ManimBench-v1)
- **Examples loaded**: 317
- **Fields used**:
  - `Code`: Full Manim code
  - `Reviewed Description` / `Generated Description`: Text description
  - `Type`: Basic/Intermediate/Advanced classification

## Example Retrieval Results

### Query: "Create a circle that moves from left to right"

Top result (Similarity: 0.630):
```python
from manim import *

class TracedPathExample(Scene):
    def construct(self):
        circ = Circle(color=RED).shift(4*LEFT)
        dot = Dot(color=RED)
        dot.move_to(circ.point_from_proportion(0))
        self.add(dot)

        trace = TracedPath(dot.get_center, dissipating_time=0.8, stroke_opacity=[0, 1])
        self.add(trace)
        self.play(MoveAlongPath(dot, circ, rate_func=linear, run_time=2))
```

### Query: "Draw a graph with axes"

Top result (Similarity: 0.602):
```python
from manim import *

class GetHorizontalLineExample(Scene):
    def construct(self):
        ax = Axes().add_coordinates()
        point = ax @ (-4, 1.5)

        dot = Dot(point)
        line = ax.get_horizontal_line(point, line_config={"dashed_ratio": 0.85})

        self.add(ax, line, dot)
```

## Benefits

1. **Better code quality**: LLM sees working examples similar to the task
2. **Fewer errors**: Examples demonstrate correct Manim API usage
3. **Consistency**: Generated code follows patterns from the dataset
4. **No training required**: Works with any LLM (Claude, GPT) without fine-tuning

## Dependencies

```bash
pip install chromadb sentence-transformers pandas pyarrow huggingface_hub requests
```

## Troubleshooting

**Vector store not initialized:**
```bash
python layer4/init_vectorstore.py
```

**ChromaDB errors:**
```bash
pip install --upgrade chromadb
```

**Pandas read_parquet errors:**
```bash
pip install --upgrade pandas pyarrow huggingface_hub
```

## Future Improvements

1. **Larger dataset**: Add more examples from other sources (3blue1brown, etc.)
2. **Better embeddings**: Use larger models (e.g., `all-mpnet-base-v2`)
3. **Hybrid search**: Combine semantic search with keyword matching
4. **Dynamic top_k**: Adjust number of examples based on query complexity
5. **Feedback loop**: Track which retrieved examples lead to successful generations
