#!/usr/bin/env python3
"""
Analyze Manim datasets for quality, structure, and characteristics.

Usage:
    python analysis/analyze_manim_datasets.py --dataset smail_bespoke
    python analysis/analyze_manim_datasets.py --all  # Analyze all downloaded datasets
"""

import argparse
import json
import logging
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatasetStatistics:
    """Statistics for a Manim dataset"""
    dataset_name: str
    total_examples: int
    has_code_count: int
    has_instruction_count: int
    avg_code_length: float
    avg_instruction_length: float
    unique_imports: Set[str]
    manim_classes_used: Counter
    deprecated_api_count: int
    complexity_distribution: Dict[str, int]
    code_patterns: Dict[str, int]
    analysis_timestamp: str


class ManimDatasetAnalyzer:
    """Analyze Manim datasets for quality and characteristics"""

    # Manim imports we expect to see
    VALID_MANIM_IMPORTS = {
        'manim', 'manimlib'  # manimlib is deprecated but we want to detect it
    }

    # Deprecated APIs to flag
    DEPRECATED_PATTERNS = [
        'ShowCreation',      # Use Create instead
        'FadeInFrom',        # Use FadeIn with shift
        'TextMobject',       # Use Text or Tex
        'TexMobject',        # Use Tex
        'ApplyMethod',       # Use animate syntax
        'manimlib',          # Old import
    ]

    # Common Manim classes (to track usage)
    MANIM_CLASSES = [
        'Scene', 'ThreeDScene', 'MovingCameraScene',
        'Circle', 'Square', 'Rectangle', 'Polygon', 'Line', 'Arrow', 'Dot',
        'Text', 'MathTex', 'Tex', 'Code',
        'Axes', 'NumberPlane', 'Graph', 'VGroup', 'Group',
        'Create', 'Write', 'FadeIn', 'FadeOut', 'Transform',
        'ReplacementTransform', 'Rotate', 'Indicate', 'Flash'
    ]

    def __init__(self, data_dir: Path):
        """
        Initialize analyzer.

        Args:
            data_dir: Base directory containing downloaded datasets
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"

    def _parse_code_structure(self, code: str) -> Dict:
        """
        Parse Python code to extract structural information.

        Args:
            code: Python code string

        Returns:
            Dictionary with structural metrics
        """
        try:
            tree = ast.parse(code)

            # Count different node types
            classes = []
            functions = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            return {
                'parseable': True,
                'classes': classes,
                'functions': functions,
                'imports': imports,
                'num_classes': len(classes),
                'num_functions': len(functions),
                'num_imports': len(imports)
            }

        except SyntaxError:
            return {
                'parseable': False,
                'error': 'syntax_error'
            }
        except Exception as e:
            return {
                'parseable': False,
                'error': str(e)
            }

    def _extract_manim_usage(self, code: str) -> Dict:
        """
        Extract Manim-specific usage patterns.

        Args:
            code: Python code string

        Returns:
            Dictionary with Manim usage metrics
        """
        # Check for Manim imports
        has_manim_import = any(imp in code for imp in self.VALID_MANIM_IMPORTS)

        # Check for deprecated patterns
        deprecated_found = [pattern for pattern in self.DEPRECATED_PATTERNS if pattern in code]

        # Count Manim class usage
        class_usage = Counter()
        for manim_class in self.MANIM_CLASSES:
            # Match class name (case-sensitive, word boundaries)
            pattern = r'\b' + re.escape(manim_class) + r'\b'
            count = len(re.findall(pattern, code))
            if count > 0:
                class_usage[manim_class] = count

        # Check for construct method (required for Manim scenes)
        has_construct = 'def construct(self)' in code

        # Count self.play calls (animations)
        animation_count = len(re.findall(r'self\.play\(', code))

        return {
            'has_manim_import': has_manim_import,
            'deprecated_patterns': deprecated_found,
            'class_usage': class_usage,
            'has_construct_method': has_construct,
            'animation_count': animation_count
        }

    def _assess_complexity(self, code: str, structure: Dict) -> str:
        """
        Assess code complexity (simple, medium, complex).

        Args:
            code: Python code string
            structure: Parsed structure dictionary

        Returns:
            Complexity category string
        """
        lines = len(code.split('\n'))

        # Simple complexity heuristics
        if not structure.get('parseable'):
            return 'unparseable'

        num_classes = structure.get('num_classes', 0)
        num_functions = structure.get('num_functions', 0)

        # Simple: short, single class, few methods
        if lines < 50 and num_classes <= 1 and num_functions <= 3:
            return 'simple'

        # Complex: long, multiple classes, many methods
        if lines > 150 or num_classes > 2 or num_functions > 8:
            return 'complex'

        # Medium: everything else
        return 'medium'

    def _analyze_example(self, example: Dict) -> Dict:
        """
        Analyze a single example.

        Args:
            example: Dictionary with code/instruction

        Returns:
            Analysis results dictionary
        """
        # Extract code and instruction
        code = example.get('code', example.get('text', ''))
        instruction = example.get('instruction', example.get('prompt', ''))

        if not code:
            return {'has_code': False}

        # Basic metrics
        code_length = len(code)
        instruction_length = len(instruction) if instruction else 0

        # Parse code structure
        structure = self._parse_code_structure(code)

        # Extract Manim usage
        manim_usage = self._extract_manim_usage(code)

        # Assess complexity
        complexity = self._assess_complexity(code, structure)

        return {
            'has_code': True,
            'has_instruction': bool(instruction),
            'code_length': code_length,
            'instruction_length': instruction_length,
            'structure': structure,
            'manim_usage': manim_usage,
            'complexity': complexity
        }

    def analyze_dataset(self, dataset_name: str) -> DatasetStatistics:
        """
        Analyze a single dataset.

        Args:
            dataset_name: Name of the dataset to analyze

        Returns:
            DatasetStatistics object
        """
        logger.info(f"Analyzing dataset: {dataset_name}")

        # Load dataset
        dataset_dir = self.raw_dir / dataset_name
        data_file = dataset_dir / f"{dataset_name}_raw.jsonl"

        if not data_file.exists():
            raise FileNotFoundError(f"Dataset file not found: {data_file}")

        # Read examples
        examples = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                examples.append(json.loads(line))

        logger.info(f"Loaded {len(examples)} examples")

        # Analyze each example
        analyses = []
        for idx, example in enumerate(examples):
            if (idx + 1) % 50 == 0:
                logger.info(f"Analyzed {idx + 1}/{len(examples)} examples")

            analysis = self._analyze_example(example)
            analyses.append(analysis)

        # Aggregate statistics
        has_code_count = sum(1 for a in analyses if a.get('has_code'))
        has_instruction_count = sum(1 for a in analyses if a.get('has_instruction'))

        # Average lengths (only for examples with code/instruction)
        code_lengths = [a['code_length'] for a in analyses if a.get('has_code')]
        avg_code_length = sum(code_lengths) / len(code_lengths) if code_lengths else 0

        instruction_lengths = [a['instruction_length'] for a in analyses
                              if a.get('has_instruction') and a['instruction_length'] > 0]
        avg_instruction_length = sum(instruction_lengths) / len(instruction_lengths) if instruction_lengths else 0

        # Collect unique imports
        unique_imports = set()
        for a in analyses:
            if a.get('structure', {}).get('imports'):
                unique_imports.update(a['structure']['imports'])

        # Aggregate Manim class usage
        manim_classes_used = Counter()
        for a in analyses:
            if a.get('manim_usage', {}).get('class_usage'):
                manim_classes_used.update(a['manim_usage']['class_usage'])

        # Count deprecated API usage
        deprecated_api_count = sum(
            len(a.get('manim_usage', {}).get('deprecated_patterns', []))
            for a in analyses
        )

        # Complexity distribution
        complexity_distribution = Counter(
            a.get('complexity', 'unknown') for a in analyses
        )

        # Code patterns
        code_patterns = {
            'has_construct_method': sum(
                1 for a in analyses
                if a.get('manim_usage', {}).get('has_construct_method')
            ),
            'has_animations': sum(
                1 for a in analyses
                if a.get('manim_usage', {}).get('animation_count', 0) > 0
            ),
            'has_manim_import': sum(
                1 for a in analyses
                if a.get('manim_usage', {}).get('has_manim_import')
            ),
            'parseable': sum(
                1 for a in analyses
                if a.get('structure', {}).get('parseable')
            )
        }

        statistics = DatasetStatistics(
            dataset_name=dataset_name,
            total_examples=len(examples),
            has_code_count=has_code_count,
            has_instruction_count=has_instruction_count,
            avg_code_length=avg_code_length,
            avg_instruction_length=avg_instruction_length,
            unique_imports=unique_imports,
            manim_classes_used=manim_classes_used,
            deprecated_api_count=deprecated_api_count,
            complexity_distribution=dict(complexity_distribution),
            code_patterns=code_patterns,
            analysis_timestamp=datetime.now().isoformat()
        )

        logger.info(f"Analysis complete for {dataset_name}")
        return statistics

    def generate_report(self, statistics: DatasetStatistics, output_file: Optional[Path] = None) -> str:
        """
        Generate a markdown report from statistics.

        Args:
            statistics: Dataset statistics
            output_file: Optional file to save report

        Returns:
            Report text
        """
        report = f"""# Manim Dataset Analysis: {statistics.dataset_name}

**Analysis Date:** {statistics.analysis_timestamp}

## Overview

- **Total Examples:** {statistics.total_examples}
- **Examples with Code:** {statistics.has_code_count} ({statistics.has_code_count/statistics.total_examples*100:.1f}%)
- **Examples with Instructions:** {statistics.has_instruction_count} ({statistics.has_instruction_count/statistics.total_examples*100:.1f}%)

## Code Metrics

- **Average Code Length:** {statistics.avg_code_length:.0f} characters
- **Average Instruction Length:** {statistics.avg_instruction_length:.0f} characters

## Code Quality

- **Parseable:** {statistics.code_patterns.get('parseable', 0)} / {statistics.total_examples} ({statistics.code_patterns.get('parseable', 0)/statistics.total_examples*100:.1f}%)
- **Has Manim Import:** {statistics.code_patterns.get('has_manim_import', 0)} / {statistics.total_examples} ({statistics.code_patterns.get('has_manim_import', 0)/statistics.total_examples*100:.1f}%)
- **Has construct() Method:** {statistics.code_patterns.get('has_construct_method', 0)} / {statistics.total_examples} ({statistics.code_patterns.get('has_construct_method', 0)/statistics.total_examples*100:.1f}%)
- **Has Animations:** {statistics.code_patterns.get('has_animations', 0)} / {statistics.total_examples} ({statistics.code_patterns.get('has_animations', 0)/statistics.total_examples*100:.1f}%)

## API Issues

- **Deprecated API Usage:** {statistics.deprecated_api_count} instances found

## Complexity Distribution

"""
        for complexity, count in sorted(statistics.complexity_distribution.items()):
            percentage = count / statistics.total_examples * 100
            report += f"- **{complexity.capitalize()}:** {count} ({percentage:.1f}%)\n"

        report += "\n## Most Used Manim Classes\n\n"
        for manim_class, count in statistics.manim_classes_used.most_common(15):
            report += f"- **{manim_class}:** {count} occurrences\n"

        report += f"\n## Unique Imports ({len(statistics.unique_imports)})\n\n"
        for imp in sorted(statistics.unique_imports)[:20]:  # Show top 20
            report += f"- {imp}\n"

        report += "\n---\n*Generated by ManimDatasetAnalyzer*\n"

        # Save if output file specified
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {output_file}")

        return report


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Manim datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/manim_datasets',
        help='Data directory containing datasets (default: data/manim_datasets)'
    )

    parser.add_argument(
        '--dataset',
        type=str,
        help='Specific dataset to analyze'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all downloaded datasets'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/manim_datasets/metadata',
        help='Output directory for reports (default: data/manim_datasets/metadata)'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = ManimDatasetAnalyzer(data_dir=Path(args.data_dir))

    # Determine which datasets to analyze
    if args.all:
        # Find all datasets in raw directory
        raw_dir = Path(args.data_dir) / "raw"
        datasets = [d.name for d in raw_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(datasets)} datasets: {datasets}")
    elif args.dataset:
        datasets = [args.dataset]
    else:
        parser.error("Must specify either --dataset or --all")

    # Analyze each dataset
    output_dir = Path(args.output_dir)
    for dataset_name in datasets:
        try:
            statistics = analyzer.analyze_dataset(dataset_name)

            # Generate report
            report_file = output_dir / f"{dataset_name}_analysis.md"
            report = analyzer.generate_report(statistics, output_file=report_file)

            # Save JSON statistics
            json_file = output_dir / f"{dataset_name}_statistics.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                # Convert to dict, handling non-serializable types
                stats_dict = asdict(statistics)
                stats_dict['unique_imports'] = list(stats_dict['unique_imports'])
                stats_dict['manim_classes_used'] = dict(stats_dict['manim_classes_used'])
                json.dump(stats_dict, f, indent=2)

            logger.info(f"✅ Analysis complete for {dataset_name}")
            print(f"\n{report}\n")

        except Exception as e:
            logger.error(f"❌ Failed to analyze {dataset_name}: {e}", exc_info=True)


if __name__ == "__main__":
    main()
