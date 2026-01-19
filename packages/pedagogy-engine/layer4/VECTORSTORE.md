# ManimBench Vector Store

This directory contains the Layer 4 generator with integrated RAG (Retrieval-Augmented Generation) using a Chroma vector store.

## ✅ Implementation Status

**IMPLEMENTED** - Vector store now loads ManimBench-v1 dataset using pandas instead of HuggingFace datasets library.

## Setup

### 1. Install Dependencies

```bash
pip install chromadb sentence-transformers pandas pyarrow huggingface_hub requests
```

### 2. Initialize Vector Store

Before running the generator, initialize the vector store with ManimBench-v1 embeddings:

```bash
python layer4/init_vectorstore.py
```

This will:
- Load the ManimBench-v1 dataset (317 examples) using pandas from HuggingFace parquet
- Compute sentence embeddings for all descriptions
- Store embeddings persistently in `data/vectorstore/`

**First run takes ~2-3 minutes.** Subsequent runs are instant.

### 3. Check Vector Store Status

```bash
python layer4/init_vectorstore.py --status
```

Output:
```
Vector Store Status:
  Location: /path/to/data/vectorstore
  Collection: manimdench-v1
  Embeddings: 317
```

### 4. Rebuild Vector Store

To rebuild from scratch (delete old embeddings and recompute):

```bash
python layer4/init_vectorstore.py --rebuild
```

## Usage

Once initialized, the RAG system works automatically:

```bash
python -m layer4.generator \
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
python -m layer4.generator \
  --prompt-file path/to/prompt.json \
  --use-rag

# Disable RAG
python -m layer4.generator \
  --prompt-file path/to/prompt.json \
  --no-rag

# Control number of examples (default: 3)
python -m layer4.generator \
  --prompt-file path/to/prompt.json \
  --rag-examples 5
```

## Storage Details

Vector store location: `data/vectorstore/`

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
- **NEW**: Loads dataset using pandas from HuggingFace parquet files

### Dataset Loading Strategy
The system tries multiple approaches in order:
1. **Pandas + HuggingFace API**: Fetches dataset info from HF API, loads parquet with pandas
2. **Direct parquet path**: Falls back to direct path if API fails
3. **HuggingFace datasets**: Falls back to datasets library if pandas fails (optional)

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

## Dataset Details

- **Source**: SuienR/ManimBench-v1
- **Examples**: 317
- **Format**: Parquet (loaded via pandas)
- **Fields**:
  - `Code`: Full Manim code
  - `Reviewed Description` / `Generated Description`: Text descriptions
  - `Type`: Basic/Intermediate/Advanced classification

## Example Retrieval

Test the retrieval system:

```bash
python layer4/test_rag.py
```

Example output:
```
Query: 'Create a circle that moves from left to right'
  Result 1 (Similarity: 0.630)
  Type: Basic
  Description: Display a red circle with a red dot on its edge...
  Code: from manim import * ...
```

## Troubleshooting

**Vector store not found?**
```bash
python layer4/init_vectorstore.py
```

**Need to rebuild?**
```bash
python layer4/init_vectorstore.py --rebuild
```

**Import errors?**
```bash
pip install chromadb sentence-transformers pandas pyarrow huggingface_hub
```

**Pandas parquet errors?**
- Ensure `pyarrow` is installed: `pip install pyarrow`
- Check internet connection (downloads from HuggingFace)
- Try rebuilding: `python layer4/init_vectorstore.py --rebuild`

**Memory issues?**
- Chroma is lightweight (~50-100MB including documents)
- Vector store is stored on disk, not loaded into memory
- Only query embeddings are computed on-the-fly

## Implementation Notes

### Why Pandas Instead of Datasets Library?

The HuggingFace `datasets` library had compatibility issues with the ManimBench-v1 dataset. Using pandas with parquet files provides:
- More reliable loading
- Better error handling
- Simpler dependency management
- Same functionality for our use case

### Code Changes

Key changes in [generator.py](generator.py):
1. Added `HAS_PANDAS` import check
2. Implemented `_load_dataset_pandas()` method (lines 118-155)
3. Updated `build()` method to work with pandas DataFrames (lines 157-217)
4. Multi-fallback loading strategy for robustness

## See Also

- [RAG_USAGE.md](RAG_USAGE.md) - Detailed usage guide and examples
- [test_rag.py](test_rag.py) - RAG retrieval test script
- [init_vectorstore.py](init_vectorstore.py) - Vector store initialization script
