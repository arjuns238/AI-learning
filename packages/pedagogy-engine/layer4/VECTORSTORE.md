# ManimBench Vector Store

This directory contains the Layer 4 generator with integrated RAG (Retrieval-Augmented Generation) using a Chroma vector store.

## Setup

### 1. Install Dependencies

```bash
pip install chromadb sentence-transformers datasets
```

### 2. Initialize Vector Store

Before running the generator, initialize the vector store with ManimBench-v1 embeddings:

```bash
python packages/pedagogy-engine/layer4/init_vectorstore.py
```

This will:
- Download the ManimBench-v1 dataset (832 examples)
- Compute sentence embeddings for all descriptions
- Store embeddings persistently in `packages/pedagogy-engine/data/vectorstore/`

**First run takes ~2-3 minutes.** Subsequent runs are instant.

### 3. Check Vector Store Status

```bash
python packages/pedagogy-engine/layer4/init_vectorstore.py --status
```

Output:
```
Vector Store Status:
  Location: /path/to/packages/pedagogy-engine/data/vectorstore
  Collection: manimdench-v1
  Embeddings: 832
```

### 4. Rebuild Vector Store

To rebuild from scratch (delete old embeddings and recompute):

```bash
python packages/pedagogy-engine/layer4/init_vectorstore.py --rebuild
```

## Usage

Once initialized, the RAG system works automatically:

```bash
python -m packages.pedagogy_engine.layer4.generator \
  --prompt-file path/to/prompt.json \
  --use-rag
```

The generator will:
1. Load cached embeddings instantly
2. Retrieve top-3 similar examples from ManimBench-v1
3. Include them as few-shot examples in the prompt
4. Generate better Manim code with real working examples

### Control RAG Behavior

```bash
# Enable RAG (default)
python -m packages.pedagogy_engine.layer4.generator \
  --prompt-file path/to/prompt.json \
  --use-rag

# Disable RAG
python -m packages.pedagogy_engine.layer4.generator \
  --prompt-file path/to/prompt.json \
  --no-rag

# Control number of examples (default: 3)
python -m packages.pedagogy_engine.layer4.generator \
  --prompt-file path/to/prompt.json \
  --rag-examples 5
```

## Storage Details

Vector store location: `packages/pedagogy-engine/data/vectorstore/`

**Files created:**
- `manimdench-v1/` - Chroma collection directory with HNSW index
  - Contains embeddings, metadata, and full code documents
  - **Size**: ~50-100MB (vectorstore + documents)

## Architecture

### ManimVectorStore
- Persistent Chroma client with local disk storage
- Uses `all-MiniLM-L6-v2` sentence embeddings (fast, lightweight)
- HNSW index for fast cosine similarity search
- Batch processing of 50 examples at a time

### ManimBenchRetriever
- Thin wrapper around ManimVectorStore
- Provides `retrieve(query, top_k)` interface
- Handles graceful fallback if dependencies missing

### Integration
- Automatically initialized when `use_rag=True`
- Augments prompts with similar code examples before sending to LLM
- Examples include: description, code snippet, complexity type, similarity score

## Performance

| Operation | Time |
|-----------|------|
| First initialization | 2-3 minutes |
| Subsequent init | <100ms (cached) |
| Query/retrieval | 10-50ms |
| Vector embedding | 200-300ms |

## Troubleshooting

**Vector store not found?**
```bash
python packages/pedagogy-engine/layer4/init_vectorstore.py
```

**Need to rebuild?**
```bash
python packages/pedagogy-engine/layer4/init_vectorstore.py --rebuild
```

**Import errors?**
```bash
pip install chromadb sentence-transformers datasets
```

**Memory issues?**
- Chroma is lightweight (~50-100MB including documents)
- If needed, can rebuild with subset of dataset
