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
from typing import Optional, Tuple
from dotenv import load_dotenv

from layer3.schema import ManimPromptWithMetadata
from .schema import (
    ManimCodeResponse,
    VideoExecutionResult,
    ManimExecutionWithMetadata,
)

# Load environment variables
load_dotenv()


# ---------- Helpers ----------

def detect_scene_name(code: str) -> Optional[str]:
    match = re.search(r"class\s+(\w+)\(.*Scene.*\)", code)
    return match.group(1) if match else None


# ---------- Code Generator ----------

class ManimCodeGenerator:
    """
    Calls ChatGPT to generate ManimCE code from Layer 3 prompts.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        api_provider: str = "openai"
    ):
        self.api_provider = api_provider
        self.model_name = model_name or os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
        self.temperature = temperature

        if self.api_provider == "openai":
            self._init_openai()
        else:
            raise ValueError("Only 'openai' provider supported")

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

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
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

        system_prompt = prompt.system_instruction + """

CRITICAL OUTPUT RULES:
- Output ONLY executable Python code.
- Do NOT use markdown or backticks.
- Do NOT add explanations outside code comments.
- The first non-empty line must be: from manim import *
"""

        full_response = self._call_openai(
            system_prompt=system_prompt,
            user_prompt=prompt.user_prompt
        )

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
        #output_dir: str = "media/videos"
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
        search_paths = [
            self.output_dir / "videos" / "1080p60" / f"{scene_name}.mp4",
            self.output_dir / "videos" / "720p30" / f"{scene_name}.mp4",
            self.output_dir / "videos" / "480p15" / f"{scene_name}.mp4",
            self.output_dir / f"{scene_name}.mp4"
        ]
        for path in search_paths:
            if path.exists():
                return path
        return None


# ---------- Orchestrator ----------

class Layer4Generator:
    """
    Orchestrates: Prompt → Code → Validation → Execution
    """

    def __init__(
        self,
        code_model: Optional[str] = None,
        code_temperature: float = 0.0,
        manim_resolution: str = "1080p60",
        manim_quality: str = "high_quality",
        #output_dir: str = "media/videos"
        output_dir: str = "output/videos"
    ):
        self.code_generator = ManimCodeGenerator(
            model_name=code_model,
            temperature=code_temperature
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
        "--code-model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model for code generation"
    )
    parser.add_argument(
        "--code-temperature",
        type=float,
        default=0.0,
        help="Temperature for code generation (should be low)"
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

    args = parser.parse_args()

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
        code_model=args.code_model,
        code_temperature=args.code_temperature,
        manim_resolution=args.resolution,
        manim_quality=args.quality
    )

    generator.generate(
        manim_prompt=manim_prompt,
        scene_name=args.scene_name,
        output_file=output_file
    )


if __name__ == "__main__":
    main()
