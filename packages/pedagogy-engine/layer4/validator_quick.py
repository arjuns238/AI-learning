"""
Quick validator for Manim code examples (no execution).

This validator performs fast, non-execution checks:
- Syntax validation (AST parsing)
- Import validation
- API compatibility check
- Basic quality scoring

Used for quick experiments before full validation pipeline.
"""

import ast
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of quick validation"""
    is_valid_python: bool
    has_required_imports: bool
    scene_classes: List[str]
    api_issues: List[str]
    quality_score: float
    error_message: Optional[str] = None


class QuickValidator:
    """Lightweight validator for quick experiments (no execution)"""

    # Approved Manim imports (v0.18+)
    APPROVED_IMPORTS = {'manim'}

    # Deprecated imports to flag
    DEPRECATED_IMPORTS = {'manimlib'}

    # Approved Manim classes (v0.18+)
    APPROVED_CLASSES = {
        # Mobjects
        'Mobject', 'VMobject', 'Group', 'VGroup',
        'Text', 'MathTex', 'Tex', 'Code', 'Paragraph',
        'Circle', 'Square', 'Rectangle', 'Polygon', 'Triangle',
        'Arrow', 'Vector', 'Line', 'Dot', 'DashedLine',
        'Axes', 'NumberPlane', 'Graph', 'ComplexPlane',
        # Animations
        'Create', 'Write', 'FadeIn', 'FadeOut', 'Uncreate', 'Unwrite',
        'Transform', 'ReplacementTransform', 'TransformMatchingShapes',
        'Rotate', 'Indicate', 'Flash', 'Wiggle', 'Circumscribe',
        'AnimationGroup', 'Succession', 'LaggedStart',
        # Scenes
        'Scene', 'ThreeDScene', 'MovingCameraScene', 'ZoomedScene',
        # 3D
        'ThreeDAxes', 'Surface', 'Sphere', 'Cube', 'Cone', 'Cylinder',
    }

    # Deprecated API patterns (should not be used)
    DEPRECATED_PATTERNS = [
        'ShowCreation',      # Use Create
        'FadeInFrom',        # Use FadeIn with shift
        'FadeInFromDown',    # Use FadeIn with shift
        'FadeOutAndShift',   # Use FadeOut with shift
        'TextMobject',       # Use Text or Tex
        'TexMobject',        # Use Tex
        'ApplyMethod',       # Use animate syntax
        'Transform(',        # Often misused, ReplacementTransform is better
    ]

    # Common LLM hallucinations (non-existent methods)
    HALLUCINATED_METHODS = [
        'set_color_by_gradient',  # Correct: set_color or color_using_background_image
        'get_center_point',       # Correct: get_center
        'set_position',           # Correct: move_to or shift
        'add_animation',          # Correct: self.play(...)
        'set_background_color',   # Scene method is set_background
    ]

    def __init__(self):
        """Initialize quick validator"""
        pass

    def validate(self, code: str) -> ValidationResult:
        """
        Perform quick validation on Manim code.

        Args:
            code: Python code string

        Returns:
            ValidationResult object
        """
        # Check Python syntax
        is_valid_python, syntax_error = self._check_syntax(code)
        if not is_valid_python:
            return ValidationResult(
                is_valid_python=False,
                has_required_imports=False,
                scene_classes=[],
                api_issues=[],
                quality_score=0.0,
                error_message=syntax_error
            )

        # Parse AST
        try:
            tree = ast.parse(code)
        except Exception as e:
            return ValidationResult(
                is_valid_python=False,
                has_required_imports=False,
                scene_classes=[],
                api_issues=[],
                quality_score=0.0,
                error_message=str(e)
            )

        # Extract imports
        imports = self._extract_imports(tree)
        has_required_imports = self._check_imports(imports)

        # Extract scene classes
        scene_classes = self._extract_scene_classes(tree)

        # Check API compatibility
        api_issues = self._check_api_compatibility(code, imports)

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            code=code,
            has_required_imports=has_required_imports,
            scene_classes=scene_classes,
            api_issues=api_issues
        )

        return ValidationResult(
            is_valid_python=True,
            has_required_imports=has_required_imports,
            scene_classes=scene_classes,
            api_issues=api_issues,
            quality_score=quality_score,
            error_message=None
        )

    def _check_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Check Python syntax validity"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError: {e}"
        except Exception as e:
            return False, str(e)

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST"""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])  # Get base module
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports

    def _check_imports(self, imports: Set[str]) -> bool:
        """Check if required Manim imports are present"""
        # Should have manim import, not deprecated manimlib
        has_manim = any(imp in self.APPROVED_IMPORTS for imp in imports)
        has_deprecated = any(imp in self.DEPRECATED_IMPORTS for imp in imports)

        return has_manim and not has_deprecated

    def _extract_scene_classes(self, tree: ast.AST) -> List[str]:
        """Extract Scene class definitions"""
        scene_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from a Scene class
                for base in node.bases:
                    if isinstance(base, ast.Name) and 'Scene' in base.id:
                        scene_classes.append(node.name)
                        break
        return scene_classes

    def _check_api_compatibility(self, code: str, imports: Set[str]) -> List[str]:
        """Check for deprecated or hallucinated API usage"""
        issues = []

        # Check for deprecated imports
        for imp in imports:
            if imp in self.DEPRECATED_IMPORTS:
                issues.append(f"Deprecated import: {imp}")

        # Check for deprecated patterns
        for pattern in self.DEPRECATED_PATTERNS:
            if pattern in code:
                issues.append(f"Deprecated API: {pattern}")

        # Check for hallucinated methods
        for method in self.HALLUCINATED_METHODS:
            if method in code:
                issues.append(f"Hallucinated method: {method}")

        return issues

    def _calculate_quality_score(
        self,
        code: str,
        has_required_imports: bool,
        scene_classes: List[str],
        api_issues: List[str]
    ) -> float:
        """
        Calculate quality score (0-1).

        Scoring criteria:
        - Has required imports: 0.2
        - Has Scene classes: 0.2
        - No API issues: 0.2
        - Code length appropriate: 0.15
        - Has construct method: 0.1
        - Has animations: 0.1
        - Code cleanliness: 0.05
        """
        score = 0.0

        # Required imports (0.2)
        if has_required_imports:
            score += 0.2

        # Has Scene classes (0.2)
        if len(scene_classes) > 0:
            score += 0.2
        elif len(scene_classes) > 3:
            # Too many scene classes might be problematic
            score += 0.1

        # No API issues (0.2)
        if len(api_issues) == 0:
            score += 0.2
        elif len(api_issues) <= 2:
            score += 0.1

        # Code length appropriate (0.15)
        lines = len(code.split('\n'))
        if 30 <= lines <= 200:
            score += 0.15
        elif lines < 30:
            score += 0.05  # Too short, might be trivial
        else:
            score += 0.1  # Too long, might be too complex

        # Has construct method (0.1)
        if 'def construct(self)' in code:
            score += 0.1

        # Has animations (0.1)
        if 'self.play(' in code:
            score += 0.1

        # Code cleanliness (0.05)
        # Penalize bad practices
        cleanliness = 0.05
        if 'import *' in code:
            cleanliness -= 0.02
        if '# TODO' in code or '# FIXME' in code:
            cleanliness -= 0.01
        if code.count('\n\n\n') > 2:  # Too many blank lines
            cleanliness -= 0.01

        score += max(0, cleanliness)

        return round(score, 2)

    def validate_batch(self, examples: List[Dict]) -> List[Dict]:
        """
        Validate a batch of examples.

        Args:
            examples: List of example dicts with 'code' key

        Returns:
            List of examples with 'validation' key added
        """
        results = []
        for idx, example in enumerate(examples):
            code = example.get('code', example.get('text', ''))
            if not code:
                logger.warning(f"Example {idx} has no code, skipping")
                continue

            validation = self.validate(code)
            example['validation'] = asdict(validation)
            results.append(example)

        return results


def validate_dataset_quick(dataset_file: str, output_file: Optional[str] = None) -> Dict:
    """
    Quick validation of an entire dataset.

    Args:
        dataset_file: Path to dataset JSONL file
        output_file: Optional path to save results

    Returns:
        Summary statistics
    """
    import json
    from pathlib import Path

    logger.info(f"Quick validation of {dataset_file}")

    # Load dataset
    examples = []
    with open(dataset_file, 'r', encoding='utf-8') as f:
        for line in f:
            examples.append(json.loads(line))

    logger.info(f"Loaded {len(examples)} examples")

    # Validate
    validator = QuickValidator()
    validated = validator.validate_batch(examples)

    # Calculate statistics
    total = len(validated)
    syntax_valid = sum(1 for ex in validated if ex['validation']['is_valid_python'])
    has_imports = sum(1 for ex in validated if ex['validation']['has_required_imports'])
    has_scene = sum(1 for ex in validated if len(ex['validation']['scene_classes']) > 0)
    no_api_issues = sum(1 for ex in validated if len(ex['validation']['api_issues']) == 0)

    quality_scores = [ex['validation']['quality_score'] for ex in validated]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    # Quality distribution
    quality_bins = {'0.0-0.3': 0, '0.3-0.5': 0, '0.5-0.7': 0, '0.7-0.9': 0, '0.9-1.0': 0}
    for score in quality_scores:
        if score < 0.3:
            quality_bins['0.0-0.3'] += 1
        elif score < 0.5:
            quality_bins['0.3-0.5'] += 1
        elif score < 0.7:
            quality_bins['0.5-0.7'] += 1
        elif score < 0.9:
            quality_bins['0.7-0.9'] += 1
        else:
            quality_bins['0.9-1.0'] += 1

    summary = {
        'total_examples': total,
        'syntax_valid': syntax_valid,
        'syntax_valid_pct': round(syntax_valid / total * 100, 1),
        'has_required_imports': has_imports,
        'has_required_imports_pct': round(has_imports / total * 100, 1),
        'has_scene_class': has_scene,
        'has_scene_class_pct': round(has_scene / total * 100, 1),
        'no_api_issues': no_api_issues,
        'no_api_issues_pct': round(no_api_issues / total * 100, 1),
        'average_quality_score': round(avg_quality, 2),
        'quality_distribution': quality_bins
    }

    logger.info(f"Validation complete: {syntax_valid}/{total} syntax valid")

    # Save if requested
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': summary,
                'validated_examples': validated
            }, f, indent=2)
        logger.info(f"Results saved to {output_file}")

    return summary
