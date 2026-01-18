"""
Layer 4 Generator: Manim Prompt → Manim Code → Video

Takes Manim prompts from Layer 3, calls ChatGPT to generate
ManimCE Python code, validates it, and executes the code to produce video.
"""

import json
import os
import re
import subprocess
import tempfile
import time
import ast
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List
from dotenv import load_dotenv

from layer3.schema import ManimPromptWithMetadata
from .schema import (
    ManimCodeResponse,
    VideoExecutionResult,
    ManimExecutionWithMetadata,
)
from .manim_api_reference import get_relevant_manim_apis

# Load environment variables
load_dotenv()

# RAG imports (optional, will fail gracefully if not installed)
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


# ---------- Helpers ----------

def detect_scene_name(code: str) -> Optional[str]:
    match = re.search(r"class\s+(\w+)\(.*Scene.*\)", code)
    return match.group(1) if match else None


# ---------- RAG Vector Store ----------

class ManimVectorStore:
    """
    Vector store for ManimBench-v1 using Chroma.
    Stores embeddings persistently in the project data directory.
    """

    # Store vector database in project data directory
    VECTORSTORE_DIR = Path(__file__).parent.parent / "data" / "vectorstore"
    COLLECTION_NAME = "manimdench-v1"

    def __init__(self):
        self.client = None
        self.collection = None
        self.embedder = None
        self._initialized = False
        self._init_store()

    def _init_store(self):
        """Initialize Chroma vector store."""
        if not HAS_CHROMADB:
            print("⚠️  chromadb not installed. Install: pip install chromadb")
            return

        if not HAS_SENTENCE_TRANSFORMERS:
            print("⚠️  sentence-transformers not installed. Install: pip install sentence-transformers")
            return

        try:
            # Create vectorstore directory if it doesn't exist
            self.VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

            # Initialize Chroma client with persistent storage
            print(f"Initializing vector store at {self.VECTORSTORE_DIR}...")
            self.client = chromadb.PersistentClient(path=str(self.VECTORSTORE_DIR))

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

            # Initialize embedder
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

            self._initialized = True
            count = self.collection.count()
            if count > 0:
                print(f"✓ Vector store initialized with {count} embeddings")
            else:
                print("✓ Vector store initialized (empty - call build() to populate)")

        except Exception as e:
            print(f"⚠️  Failed to initialize vector store: {e}")
            self._initialized = False

    def _load_dataset_pandas(self) -> Optional['pd.DataFrame']:
        """
        Load ManimBench-v1 dataset using pandas from parquet format.
        Falls back to HuggingFace datasets if pandas fails.

        Returns:
            DataFrame with 'Code', 'Reviewed Description', 'Generated Description', 'Type' columns
        """
        if not HAS_PANDAS:
            print("⚠️  pandas not installed. Install: pip install pandas")
            return None

        try:
            print("Loading ManimBench-v1 dataset with pandas from HuggingFace...")

            # First, fetch the dataset info to get the correct split filename
            from huggingface_hub import hf_hub_url
            import requests

            # Get dataset info
            api_url = "https://huggingface.co/api/datasets/SuienR/ManimBench-v1"
            response = requests.get(api_url)
            dataset_info = response.json()

            # Find the train split file
            train_file = None
            if 'siblings' in dataset_info:
                for file in dataset_info['siblings']:
                    if 'train' in file['rfilename'] and file['rfilename'].endswith('.parquet'):
                        train_file = file['rfilename']
                        break

            if not train_file:
                # Fallback to common naming pattern
                train_file = "data/train-00000-of-00001.parquet"

            # Load using pandas with hf:// protocol
            hf_path = f"hf://datasets/SuienR/ManimBench-v1/{train_file}"
            print(f"  Reading from: {hf_path}")
            df = pd.read_parquet(hf_path)
            print(f"✓ Loaded {len(df)} examples via pandas")
            return df

        except Exception as e:
            print(f"⚠️  Failed to load via pandas with HuggingFace hub: {e}")

            # Try simpler direct path
            try:
                print("Trying direct parquet path...")
                df = pd.read_parquet("hf://datasets/SuienR/ManimBench-v1/data/train-00000-of-00001.parquet")
                print(f"✓ Loaded {len(df)} examples via pandas")
                return df
            except Exception as e2:
                print(f"⚠️  Direct path also failed: {e2}")

            # Fallback to HuggingFace datasets library
            if HAS_DATASETS:
                print("Falling back to HuggingFace datasets library...")
                try:
                    dataset = load_dataset("SuienR/ManimBench-v1", split="train")
                    df = dataset.to_pandas()
                    print(f"✓ Loaded {len(df)} examples via HuggingFace datasets")
                    return df
                except Exception as e3:
                    print(f"⚠️  HuggingFace datasets also failed: {e3}")
                    return None
            else:
                print("⚠️  datasets library not installed as fallback")
                return None

    def build(self, force_rebuild: bool = False):
        """
        Build the vector store from ManimBench-v1 dataset using pandas.

        Args:
            force_rebuild: If True, delete and rebuild the collection
        """
        if not self._initialized:
            print("⚠️  Vector store not initialized")
            return

        try:
            # Check if already populated
            existing_count = self.collection.count()
            if existing_count > 0 and not force_rebuild:
                print(f"✓ Vector store already populated with {existing_count} embeddings")
                return

            # Delete existing collection if force rebuild
            if force_rebuild and existing_count > 0:
                print(f"Deleting existing collection with {existing_count} embeddings...")
                self.client.delete_collection(name=self.COLLECTION_NAME)
                self.collection = self.client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )

            # Load dataset using pandas
            df = self._load_dataset_pandas()
            if df is None:
                print("⚠️  Failed to load dataset")
                return

            # Process in batches
            batch_size = 50
            total_examples = len(df)
            print(f"Computing embeddings and storing ({total_examples} total)...")

            for i in range(0, total_examples, batch_size):
                batch_df = df.iloc[i : min(i + batch_size, total_examples)]

                # Extract data from DataFrame
                ids = [f"example_{j}" for j in range(i, i + len(batch_df))]

                # Get descriptions (prefer Reviewed Description, fallback to Generated Description)
                descriptions = []
                for _, row in batch_df.iterrows():
                    if 'Reviewed Description' in row and pd.notna(row['Reviewed Description']):
                        descriptions.append(str(row['Reviewed Description']))
                    elif 'Generated Description' in row and pd.notna(row['Generated Description']):
                        descriptions.append(str(row['Generated Description']))
                    else:
                        descriptions.append("")

                codes = [str(code) for code in batch_df['Code'].tolist()]
                types = [str(t) if pd.notna(t) else "Unknown" for t in batch_df.get('Type', pd.Series(['Unknown'] * len(batch_df))).tolist()]

                # Compute embeddings
                embeddings = self.embedder.encode(descriptions).tolist()

                # Prepare metadata
                metadatas = [
                    {
                        "description": desc,
                        "type": type_,
                        "code_preview": code[:100] + "..." if len(code) > 100 else code
                    }
                    for desc, type_, code in zip(descriptions, types, codes)
                ]

                # Store in Chroma (documents for retrieval of full code)
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=codes,  # Full code stored here
                    metadatas=metadatas
                )

                print(f"  Processed {min(i + batch_size, total_examples)}/{total_examples} examples")

            print(f"✓ Vector store built successfully with {self.collection.count()} embeddings")

        except Exception as e:
            print(f"⚠️  Failed to build vector store: {e}")
            import traceback
            traceback.print_exc()

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """
        Retrieve top-k similar examples.
        
        Args:
            query: Query description or prompt
            top_k: Number of results to return
            
        Returns:
            List of dicts with 'description', 'code', 'type', 'similarity'
        """
        if not self._initialized or self.collection is None:
            return []

        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            output = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # Convert distance to similarity (cosine distance to similarity)
                    similarity = 1 - distance

                    output.append({
                        "description": metadata.get("description", ""),
                        "code": doc,
                        "type": metadata.get("type", "Unknown"),
                        "similarity": float(similarity)
                    })

            return output

        except Exception as e:
            print(f"⚠️  Error during retrieval: {e}")
            return []


# ---------- RAG Retriever ----------

class ManimBenchRetriever:
    """
    Retrieves relevant examples from ManimBench-v1 using vector store.
    """

    def __init__(self):
        self.vector_store = ManimVectorStore()
        self._initialized = self.vector_store._initialized

    def retrieve(self, query: str, top_k: int = 3) -> List[dict]:
        """Delegate to vector store."""
        return self.vector_store.retrieve(query, top_k)
        """
        Retrieve top-k most similar examples from ManimBench-v1.
        
        Args:
            query: Description or prompt to find similar examples for
            top_k: Number of examples to retrieve
            
        Returns:
            List of dicts with 'description' and 'code' keys
        """
        if not self._initialized or self.dataset is None:
            return []

        try:
            import numpy as np
            
            # Encode the query
            query_embedding = self.embedder.encode(query)
            
            # Compute similarities
            similarities = np.dot(self.embeddings, query_embedding)
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Retrieve examples
            results = []
            for idx in top_indices:
                example = self.dataset[int(idx)]
                results.append({
                    "description": example.get("Reviewed Description", example.get("Generated Description", "")),
                    "code": example.get("Code", ""),
                    "type": example.get("Type", "Unknown"),
                    "similarity": float(similarities[idx])
                })
            
            return results
        except Exception as e:
            print(f"⚠️  Error during retrieval: {e}")
            return []


# ---------- Code Generator ----------

class ManimCodeGenerator:
    """
    Calls an LLM API to generate ManimCE code from Layer 3 prompts.
    Supports: Anthropic Claude, OpenAI GPT
    Optionally uses RAG (Retrieval-Augmented Generation) with ManimBench-v1 examples.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        api_provider: str = "anthropic",
        use_rag: bool = True,
        rag_examples: int = 3
    ):
        self.api_provider = api_provider
        self.use_rag = use_rag
        self.rag_examples = rag_examples

        # Initialize RAG retriever if enabled
        self.retriever = None
        if self.use_rag:
            try:
                self.retriever = ManimBenchRetriever()
            except Exception as e:
                print(f"⚠️  RAG initialization failed: {e}. Continuing without RAG.")
                self.use_rag = False

        # Set default model based on provider
        if model_name:
            self.model_name = model_name
        else:
            default_models = {
                "anthropic": "claude-sonnet-4-5-20250929",
                "openai": "gpt-5",
                "deepseek": "deepseek-reasoner"
            }
            self.model_name = default_models.get(api_provider, "claude-sonnet-4-5-20250929")

        # Read temperature from env or use provided value or default to 0.0
        if temperature is not None:
            self.temperature = temperature
        else:
            self.temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.0"))

        if self.api_provider == "anthropic":
            self._init_anthropic()
        elif self.api_provider == "openai":
            self._init_openai()
        elif self.api_provider == "deepseek":
            self._init_deepseek()
        else:
            raise ValueError(f"Unsupported API provider: {api_provider}. Use 'anthropic', 'openai', or 'deepseek'")

    def _init_anthropic(self):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Run: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        self.client = Anthropic(api_key=api_key)
        print(f"✓ Anthropic Claude initialized: {self.model_name}")
        print(f"  Temperature: {self.temperature}")

    def _init_openai(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=api_key)
        print(f"✓ OpenAI initialized: {self.model_name}")
        if self.model_name == "gpt-5":
            print(" Temperature is managed internally for gpt-5; ignoring provided value.")
        else:
            print(f"  Temperature: {self.temperature}")

    def _init_deepseek(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run: pip install openai")

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment")

        # DeepSeek uses OpenAI-compatible API
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        print(f"✓ DeepSeek initialized: {self.model_name}")
        print(f"  Temperature: {self.temperature}")

    def _augment_prompt_with_rag(self, user_prompt: str, metadata: dict = None) -> str:
        """
        Augment the user prompt with similar examples from ManimBench-v1.
        Uses pedagogical context to improve retrieval relevance.
        """
        if not self.use_rag or not self.retriever:
            return user_prompt

        try:
            # Build enhanced query with pedagogical context
            query = user_prompt

            # Add pedagogical context to query if available
            if metadata and 'pedagogical_context' in metadata:
                ped_ctx = metadata['pedagogical_context']
                query_parts = [user_prompt]

                # Include key pedagogical elements in search
                if 'visual_metaphor' in ped_ctx:
                    query_parts.append(f"Visual metaphor: {ped_ctx['visual_metaphor']}")
                if 'pedagogical_pattern' in ped_ctx:
                    query_parts.append(f"Pattern: {ped_ctx['pedagogical_pattern']}")
                if 'key_insight' in ped_ctx:
                    query_parts.append(f"Key concept: {ped_ctx['key_insight']}")

                query = " ".join(query_parts)
                print(f"✓ RAG query enhanced with pedagogical context")
                print(f"\nEnhanced RAG Query (first 200 chars):\n{query[:200]}...\n")

            # Retrieve similar examples
            examples = self.retriever.retrieve(query, top_k=self.rag_examples)

            if not examples:
                return user_prompt

            # Print detailed retrieval results
            print(f"\n{'='*60}")
            print(f"RAG RETRIEVAL RESULTS (Top {len(examples)} examples)")
            print(f"{'='*60}")
            for i, example in enumerate(examples, 1):
                print(f"\n[Example {i}]")
                print(f"  Type: {example['type']}")
                print(f"  Similarity: {example['similarity']:.3f}")
                print(f"  Description: {example['description'][:150]}...")
                print(f"  Code preview: {example['code'][:100]}...")
            print(f"{'='*60}\n")

            # Build few-shot examples section
            examples_text = "\n\n## Similar Examples from ManimBench-v1:\n"

            for i, example in enumerate(examples, 1):
                examples_text += f"\n### Example {i} (Type: {example['type']}, Similarity: {example['similarity']:.2f})\n"
                examples_text += f"Description: {example['description']}\n\n"
                examples_text += f"Code:\n```python\n{example['code']}\n```\n"

            examples_text += "\n## Now generate code for the following task:\n\n"

            augmented_prompt = examples_text + user_prompt

            print(f"✓ RAG augmentation: Retrieved {len(examples)} similar examples")
            return augmented_prompt

        except Exception as e:
            print(f"⚠️  RAG augmentation failed: {e}. Using original prompt.")
            return user_prompt

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=8192,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # temperature=self.temperature,
            max_completion_tokens=8192
        )
        return response.choices[0].message.content

    def _call_deepseek(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=8192
        )
        return response.choices[0].message.content

    def extract_python_code(self, response: str) -> str:
        """
        Extract Python code from ChatGPT response.
        Handles raw code and markdown fences.
        """
        text = response.strip()
        blocks = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
        if blocks:
            # Pick largest code block
            text = max(blocks, key=len).strip()

        # Strip leading non-code lines
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.match(r"\s*(from|import|class)\s+", line):
                text = "\n".join(lines[i:])
                break

        return text.strip()

    def validate_code(self, code: str, scene_name: str) -> Tuple[bool, Optional[str]]:
        """
        Basic validation:
        - AST parse
        - Contains from manim import *
        - At least one Scene class
        - Scene class matches expected name
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        if "from manim import" not in code:
            return False, "Missing 'from manim import *'"

        scene_match = re.search(r"class\s+(\w+)\(.*Scene.*\)", code)
        if not scene_match:
            return False, "No Scene class found"

        if scene_name not in code:
            return False, f"Scene class '{scene_name}' not found"

        return True, None

    def generate(self, manim_prompt: ManimPromptWithMetadata) -> ManimCodeResponse:
        prompt = manim_prompt.prompt

        # Extract metadata for pedagogical context
        metadata = manim_prompt.metadata.model_dump() if hasattr(manim_prompt.metadata, 'model_dump') else manim_prompt.metadata.__dict__

        # Build pedagogical preamble if context available
        pedagogical_preamble = ""
        if 'pedagogical_context' in metadata and metadata['pedagogical_context']:
            ped_ctx = metadata['pedagogical_context']
            pedagogical_preamble = f"""
## Pedagogical Context

**Educational Goal:** This visualization helps learners understand: "{ped_ctx.get('core_question', 'N/A')}"

**Target Mental Model:** {ped_ctx.get('target_mental_model', 'N/A')}

**Common Misconception to Address:** {ped_ctx.get('common_misconception', 'N/A')}

**Visual Metaphor:** {ped_ctx.get('visual_metaphor', 'N/A')}

**Key Insight:** {ped_ctx.get('key_insight', 'N/A')}

**Design Guidance:** Create code that makes this mental model concrete and addresses the misconception visually.

"""
            print(f"✓ Including pedagogical context in prompt")

        # Get relevant Manim API reference based on scene specification
        api_reference = get_relevant_manim_apis(prompt.user_prompt)
        if api_reference:
            print(f"✓ Added contextual Manim API reference")

        # Augment user prompt with RAG examples (now includes pedagogical context in query)
        base_user_prompt = prompt.user_prompt
        if self.use_rag:
            base_user_prompt = self._augment_prompt_with_rag(base_user_prompt, metadata)

        # Build final prompt in order: Pedagogical Context → API Reference → RAG Examples → Scene Spec
        user_prompt = ""
        if pedagogical_preamble:
            user_prompt += pedagogical_preamble
        if api_reference:
            user_prompt += api_reference
        user_prompt += base_user_prompt

        system_prompt = prompt.system_instruction + """

CRITICAL OUTPUT RULES:
- Output ONLY executable Python code.
- Do NOT use markdown or backticks.
- Do NOT add explanations outside code comments.
- The first non-empty line must be: from manim import *
"""

        # Call the appropriate API based on provider
        if self.api_provider == "anthropic":
            full_response = self._call_anthropic(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        elif self.api_provider == "openai":
            full_response = self._call_openai(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        elif self.api_provider == "deepseek":
            full_response = self._call_deepseek(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        else:
            raise ValueError(f"Unknown API provider: {self.api_provider}")

        code = self.extract_python_code(full_response)

        return ManimCodeResponse(
            code=code,
            model=self.model_name,
            generation_timestamp=datetime.now().isoformat(),
            raw_response=full_response
        )


# ---------- Executor ----------

class ManimExecutor:
    """
    Executes generated Manim code and produces video output.
    """

    def __init__(
        self,
        resolution: str = "1080p60",
        quality: str = "high_quality",
        output_dir: str = "output/videos"
    ):
        self.resolution = resolution
        self.quality = quality
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._check_manim_installed()

    def _check_manim_installed(self):
        try:
            result = subprocess.run(
                ["manim", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Manim is installed: {result.stdout.strip()}")
            else:
                raise RuntimeError("Manim installation check failed")
        except FileNotFoundError:
            raise RuntimeError("Manim not found. Install with: pip install manim")

    def execute(
        self,
        code: str,
        scene_name: str = "EducationalAnimation",
        output_path: Optional[Path] = None
    ) -> VideoExecutionResult:
        print(f"\nExecuting Manim code for scene: {scene_name}")

        start_time = time.time()
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=str(self.output_dir)
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            resolution_flag = self._parse_resolution(self.resolution)
            # Only pass resolution flag; Manim uses it for quality internally
            cmd = [
                "manim",
                resolution_flag,
                temp_file,
                scene_name,
                "-o", scene_name
            ]

            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(self.output_dir),
                capture_output=True,
                text=True,
                timeout=600
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                video_path = self._find_video_file(scene_name)
                if video_path:
                    print(f"✓ Video generated successfully: {video_path}")

                    # Clean up partial movie files to save space
                    self._cleanup_partial_files(video_path)

                    return VideoExecutionResult(
                        success=True,
                        video_path=str(video_path),
                        resolution=self.resolution,
                        execution_time_seconds=execution_time,
                        output_log=result.stdout
                    )
                else:
                    return VideoExecutionResult(
                        success=False,
                        resolution=self.resolution,
                        execution_time_seconds=execution_time,
                        error_message="Video file not found after successful execution",
                        output_log=result.stdout + "\n" + result.stderr
                    )
            else:
                print(f"✗ Manim execution failed")
                return VideoExecutionResult(
                    success=False,
                    resolution=self.resolution,
                    execution_time_seconds=execution_time,
                    error_message=f"Manim execution failed with code {result.returncode}",
                    output_log=result.stdout + "\n" + result.stderr
                )

        finally:
            if Path(temp_file).exists():
                Path(temp_file).unlink()

    def _parse_resolution(self, resolution: str) -> str:
        mapping = {
            "1080p60": "-pqh",
            "1080p30": "-ph",
            "720p60": "-pqm",
            "720p30": "-pm",
            "480p30": "-pl",
            "480p15": "-pql"
        }
        return mapping.get(resolution, "-pqh")

    def _find_video_file(self, scene_name: str) -> Optional[Path]:
        """
        Find the generated video file.
        Manim creates videos in media/videos/<temp_file_name>/<resolution>/<scene_name>.mp4
        """
        # Resolution folder mapping
        resolution_folders = {
            "1080p60": "1080p60",
            "1080p30": "1080p30",
            "720p60": "720p60",
            "720p30": "720p30",
            "480p30": "480p30",
            "480p15": "480p15"
        }

        resolution_folder = resolution_folders.get(self.resolution, "1080p60")

        # Manim creates: output_dir/media/videos/<temp_script_name>/<resolution>/<scene>.mp4
        media_videos_dir = self.output_dir / "media" / "videos"

        if media_videos_dir.exists():
            # Search through all subdirectories (temp file names)
            for temp_dir in media_videos_dir.iterdir():
                if temp_dir.is_dir():
                    video_path = temp_dir / resolution_folder / f"{scene_name}.mp4"
                    if video_path.exists():
                        return video_path

        # Fallback: check old paths for backward compatibility
        fallback_paths = [
            self.output_dir / "videos" / resolution_folder / f"{scene_name}.mp4",
            self.output_dir / f"{scene_name}.mp4"
        ]
        for path in fallback_paths:
            if path.exists():
                return path

        return None

    def _cleanup_partial_files(self, video_path: Path):
        """
        Clean up Manim's partial movie files to save disk space.
        These are intermediate files created during rendering.
        """
        try:
            # video_path is like: output/videos/media/videos/tmpXXX/480p15/SceneName.mp4
            # partial_files are in: output/videos/media/videos/tmpXXX/480p15/partial_movie_files/
            partial_dir = video_path.parent / "partial_movie_files"

            if partial_dir.exists():
                import shutil
                shutil.rmtree(partial_dir)
                print(f"  Cleaned up partial movie files")
        except Exception as e:
            # Non-critical, just log and continue
            print(f"  Warning: Could not clean up partial files: {e}")


# ---------- Orchestrator ----------

class Layer4Generator:
    """
    Orchestrates: Prompt → Code → Validation → Execution
    Supports RAG (Retrieval-Augmented Generation) with ManimBench-v1 dataset.
    """

    def __init__(
        self,
        api_provider: str = "anthropic",
        code_model: Optional[str] = None,
        code_temperature: float = 0.0,
        manim_resolution: str = "1080p60",
        manim_quality: str = "high_quality",
        output_dir: str = "output/videos",
        use_rag: bool = True,
        rag_examples: int = 3
    ):
        self.code_generator = ManimCodeGenerator(
            api_provider=api_provider,
            model_name=code_model,
            temperature=code_temperature,
            use_rag=use_rag,
            rag_examples=rag_examples
        )
        self.executor = ManimExecutor(
            resolution=manim_resolution,
            quality=manim_quality,
            output_dir=output_dir
        )

    def generate(
        self,
        manim_prompt: ManimPromptWithMetadata,
        scene_name: str = "EducationalAnimation",
        output_file: Optional[Path] = None
        ) -> ManimExecutionWithMetadata:

        print("\n" + "="*60)
        print("Layer 4: Manim Code Generation & Video Execution")
        print("="*60)

        max_attempts = 3
        code_response = None
        execution_result = None

        for attempt in range(1, max_attempts + 1):
            print(f"\nAttempt {attempt}/{max_attempts}")

            # Step 1: Generate code from Layer 3 prompt
            code_response = self.code_generator.generate(manim_prompt)

            # Detect Scene name dynamically
            detected = detect_scene_name(code_response.code)
            if detected:
                scene_name = detected

            # Step 2: Static validation
            valid, validation_error = self.code_generator.validate_code(code_response.code, scene_name)
            if not valid:
                print(f"⚠️ Validation failed: {validation_error}")
                manim_prompt.prompt.user_prompt += f"""

The previous output was invalid and could not be executed.

Error:
{validation_error}

Fix the code.

REMEMBER:
- Output ONLY executable Python
- No markdown
- Exactly one Manim Scene
"""
                continue  # retry generation

            # Step 3: Execute the code
            execution_result = self.executor.execute(code_response.code, scene_name)

            if execution_result.success:
                print("✓ Code executed successfully")
                break  # exit loop
            else:
                print("⚠️ Runtime error during execution")
                print("--- MANIM OUTPUT LOG (truncated) ---")
                print(execution_result.output_log[:1000])
                print("--- END LOG ---\n")

                # Append runtime error to prompt for repair
                manim_prompt.prompt.user_prompt += f"""

The previous code failed to run in Manim.

Runtime Error:
{execution_result.output_log[:2000]}

Please fix the code so it executes successfully.
"""

        else:
            # Max attempts reached
            return ManimExecutionWithMetadata(
                code_response=code_response,
                execution_result=execution_result or VideoExecutionResult(
                    success=False,
                    resolution=self.executor.resolution,
                    execution_time_seconds=0.0,
                    error_message="Code execution failed after max attempts",
                    output_log=(execution_result.output_log if execution_result else "No execution attempted")
                ),
                metadata={}
            )

        # Step 4: Successful execution, create record
        result = ManimExecutionWithMetadata(
            code_response=code_response,
            execution_result=execution_result,
            metadata={
                "source_manim_prompt_title": manim_prompt.prompt.title,
                "source_storyboard_topic": manim_prompt.metadata.source_storyboard_topic,
                "pedagogical_pattern": manim_prompt.metadata.pedagogical_pattern,
                "source_layer2_id": manim_prompt.metadata.source_layer2_id
            }
        )

        # Step 5: Save execution record if requested
        if output_file:
            self._save_execution(result, output_file)

        return result

    def _save_execution(self, result: ManimExecutionWithMetadata, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result.model_dump(), f, indent=2)
        print(f"Saved execution record to: {output_path}")


# ---------- CLI ----------

import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Generate and execute Manim code from Layer 3 prompts"
    )

    parser.add_argument(
        "--prompt-file",
        type=str,
        required=True,
        help="Path to manim_prompt.json file from Layer 3"
    )
    parser.add_argument(
        "--scene-name",
        type=str,
        default="EducationalAnimation",
        help="Name of the Scene class to render"
    )
    parser.add_argument(
        "--api-provider",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai", "deepseek"],
        help="LLM API provider (default: anthropic)"
    )
    parser.add_argument(
        "--code-model",
        type=str,
        default=None,
        help="Model for code generation (default: claude-sonnet-4-5-20250929 for anthropic, gpt-4o for openai, deepseek-chat for deepseek)"
    )
    parser.add_argument(
        "--code-temperature",
        type=float,
        default=None,
        help="Temperature for code generation (default: reads DEFAULT_TEMPERATURE from .env, fallback to 0.0)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="1080p60",
        choices=["1080p60", "1080p30", "720p60", "720p30", "480p30", "480p15"],
        help="Video resolution and framerate"
    )
    parser.add_argument(
        "--quality",
        type=str,
        default="high_quality",
        choices=["low_quality", "medium_quality", "high_quality", "ultra_quality"],
        help="Manim rendering quality"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Path to save execution record JSON"
    )
    parser.add_argument(
        "--use-rag",
        action="store_true",
        default=True,
        help="Enable RAG (Retrieval-Augmented Generation) with ManimBench-v1 (default: True)"
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG augmentation"
    )
    parser.add_argument(
        "--rag-examples",
        type=int,
        default=3,
        help="Number of RAG examples to retrieve (default: 3)"
    )

    args = parser.parse_args()

    # Handle --no-rag flag
    use_rag = not args.no_rag if args.no_rag else args.use_rag

    with open(args.prompt_file, 'r') as f:
        data = json.load(f)
    manim_prompt = ManimPromptWithMetadata(**data)

    if not args.output_file:
        output_dir = Path(args.prompt_file).parent.parent / "output" / "videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / (Path(args.prompt_file).stem.replace("_manim_prompt", "_execution") + ".json")
    else:
        output_file = Path(args.output_file)

    generator = Layer4Generator(
        api_provider=args.api_provider,
        code_model=args.code_model,
        code_temperature=args.code_temperature,
        manim_resolution=args.resolution,
        manim_quality=args.quality,
        use_rag=use_rag,
        rag_examples=args.rag_examples
    )

    generator.generate(
        manim_prompt=manim_prompt,
        scene_name=args.scene_name,
        output_file=output_file
    )


if __name__ == "__main__":
    main()
