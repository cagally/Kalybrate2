"""
Test Generator - Automatically create benchmarks from SKILL.md files.

Reads a SKILL.md file and uses Claude to:
1. Extract what the skill claims to do
2. Generate 9 realistic test tasks (3 easy, 3 medium, 3 hard)
3. Define success criteria for each task
4. Generate quality comparison prompts
"""

import os
import json
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import (
    Task, DifficultyLevel, OutputType,
    GeneratedBenchmark, BenchmarkSuite
)

load_dotenv()


# Available success criteria that can be used
AVAILABLE_CRITERIA = {
    # File outputs
    "file_created": "A file with the expected extension exists",
    "file_valid": "The file opens without errors",
    "file_has_content": "The file is not empty/has meaningful content",
    "file_has_multiple_pages": "For PDFs/docs with multiple pages expected",
    "has_formula": "For spreadsheets, contains formulas",
    "has_images": "Contains embedded images",
    "has_table": "Contains a table",
    "has_chart": "Contains a chart",
    "min_rows": "Spreadsheet has minimum rows",
    "min_columns": "Spreadsheet has minimum columns",
    "min_slides": "Presentation has minimum slides",
    "min_paragraphs": "Document has minimum paragraphs",

    # Code outputs
    "code_extracted": "Code block was found in response",
    "code_compiles": "Code compiles/runs without syntax errors",
    "has_type_annotations": "TypeScript has type annotations",
    "has_docstrings": "Python has docstrings",

    # Text outputs
    "response_exists": "A non-empty response was generated",
    "response_relevant": "Response addresses the prompt (LLM judge)",
}


GENERATION_PROMPT = """Read this SKILL.md and generate evaluation tasks for testing this skill.

SKILL.md:
---
{skill_md_content}
---

Instructions:
1. First, list the key capabilities this skill claims to have (what it says it can do)
2. For each capability, generate realistic prompts that would test it
3. Prompts should sound like REAL user requests, NOT "use this skill to..."
4. Generate 9 total tasks: 3 easy, 3 medium, 3 hard
5. Also generate 5 quality comparison prompts (for A/B testing skill vs no-skill)

Bad prompt examples (don't do these):
- "Use the PDF skill to create a PDF document"
- "Apply the skill to generate a spreadsheet"

Good prompt examples:
- "I need to send my client a proposal for the website redesign project. Can you draft something up?"
- "Create a quarterly sales report with charts showing our growth"
- "Write a Python function that calculates compound interest with proper docstrings"

For success criteria, ONLY use these available types:
{criteria_list}

If a task would need a criterion that doesn't exist, note it in missing_criteria.

Determine the expected output type for each task:
- "file" - Creates a file (PDF, Excel, Word, etc.)
- "code" - Returns code that should compile/run
- "text" - Returns text/explanation

Output as JSON (no markdown, just raw JSON):
{{
  "skill_claims": ["claim 1", "claim 2", ...],
  "tasks": [
    {{
      "id": "easy_1",
      "difficulty": "easy",
      "prompt": "realistic user prompt here",
      "tests_claim": "which claim this tests",
      "expected_output_type": "file" | "code" | "text",
      "expected_file_extension": ".pdf" (if file type, null otherwise),
      "success_criteria": {{
        "criterion_name": true,
        ...
      }}
    }},
    ...
  ],
  "quality_prompts": [
    "prompt for A/B comparison 1",
    "prompt for A/B comparison 2",
    ...
  ],
  "missing_criteria": ["description of any needed criteria that don't exist"]
}}"""


class TestGenerator:
    """Generates test benchmarks from SKILL.md files using Claude"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def generate_benchmarks(
        self,
        skill_name: str,
        skill_md_content: str,
        save_to_file: bool = True
    ) -> GeneratedBenchmark:
        """
        Generate benchmarks from SKILL.md content.

        Args:
            skill_name: Name of the skill
            skill_md_content: Full content of SKILL.md
            save_to_file: Whether to save the generated benchmark to data/test_cases/

        Returns:
            GeneratedBenchmark with tasks and criteria
        """
        print(f"Generating benchmarks for: {skill_name}")

        # Build the prompt with available criteria
        criteria_list = "\n".join(
            f"- {name}: {desc}"
            for name, desc in AVAILABLE_CRITERIA.items()
        )

        prompt = GENERATION_PROMPT.format(
            skill_md_content=skill_md_content[:8000],  # Limit size
            criteria_list=criteria_list
        )

        # Call Claude to generate benchmarks
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,  # Deterministic
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        # Parse JSON response
        try:
            # Try to extract JSON if wrapped in markdown
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {response_text[:500]}")
            raise

        # Convert to Task objects
        tasks = []
        for task_data in data.get("tasks", []):
            # Map difficulty string to enum
            difficulty_str = task_data.get("difficulty", "easy").lower()
            difficulty = DifficultyLevel(difficulty_str)

            # Map output type
            output_type_str = task_data.get("expected_output_type", "file").lower()
            try:
                output_type = OutputType(output_type_str)
            except ValueError:
                output_type = OutputType.TEXT

            # Get success criteria
            criteria = task_data.get("success_criteria", {})
            if not criteria:
                # Default criteria based on output type
                if output_type == OutputType.FILE:
                    criteria = {"file_created": True, "file_valid": True}
                elif output_type == OutputType.CODE:
                    criteria = {"code_extracted": True, "code_compiles": True}
                else:
                    criteria = {"response_exists": True}

            task = Task(
                id=f"{skill_name}_{task_data.get('id', f'task_{len(tasks)}')}",
                prompt=task_data.get("prompt", ""),
                difficulty=difficulty,
                expected_output_type=output_type,
                expected_file_type=task_data.get("expected_file_extension"),
                tests_claim=task_data.get("tests_claim"),
                success_criteria=criteria
            )
            tasks.append(task)

        # Create GeneratedBenchmark
        benchmark = GeneratedBenchmark(
            skill_name=skill_name,
            skill_claims=data.get("skill_claims", []),
            tasks=tasks,
            quality_prompts=data.get("quality_prompts", []),
            missing_criteria=data.get("missing_criteria", [])
        )

        # Save to file if requested
        if save_to_file:
            self._save_benchmark(skill_name, benchmark)

        print(f"  Generated {len(tasks)} tasks")
        print(f"  Skill claims: {len(benchmark.skill_claims)}")
        print(f"  Quality prompts: {len(benchmark.quality_prompts)}")
        if benchmark.missing_criteria:
            print(f"  Missing criteria: {benchmark.missing_criteria}")

        return benchmark

    def _save_benchmark(self, skill_name: str, benchmark: GeneratedBenchmark):
        """Save generated benchmark to data/test_cases/"""
        output_dir = Path("data/test_cases")
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{skill_name}.json"

        # Convert to dict for JSON serialization
        data = {
            "skill_name": benchmark.skill_name,
            "skill_claims": benchmark.skill_claims,
            "tasks": [task.model_dump() for task in benchmark.tasks],
            "quality_prompts": benchmark.quality_prompts,
            "missing_criteria": benchmark.missing_criteria,
            "generated_at": benchmark.generated_at
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"  Saved to: {output_path}")

    def load_benchmark(self, skill_name: str) -> Optional[GeneratedBenchmark]:
        """Load a previously generated benchmark from file"""
        benchmark_path = Path(f"data/test_cases/{skill_name}.json")

        if not benchmark_path.exists():
            return None

        with open(benchmark_path) as f:
            data = json.load(f)

        tasks = [Task(**task_data) for task_data in data.get("tasks", [])]

        return GeneratedBenchmark(
            skill_name=data.get("skill_name", skill_name),
            skill_claims=data.get("skill_claims", []),
            tasks=tasks,
            quality_prompts=data.get("quality_prompts", []),
            missing_criteria=data.get("missing_criteria", []),
            generated_at=data.get("generated_at", "")
        )

    def to_benchmark_suite(self, benchmark: GeneratedBenchmark) -> BenchmarkSuite:
        """Convert GeneratedBenchmark to BenchmarkSuite for compatibility"""
        return BenchmarkSuite(
            skill_name=benchmark.skill_name,
            skill_claims=benchmark.skill_claims,
            tasks=benchmark.tasks,
            selectivity_tests=[],  # Deprecated
            quality_prompts=benchmark.quality_prompts
        )


def generate_benchmarks_for_skill(
    skill_name: str,
    skill_md_content: str
) -> BenchmarkSuite:
    """
    Convenience function to generate benchmarks for a skill.

    Args:
        skill_name: Name of the skill
        skill_md_content: Full SKILL.md content

    Returns:
        BenchmarkSuite ready for evaluation
    """
    generator = TestGenerator()
    benchmark = generator.generate_benchmarks(skill_name, skill_md_content)
    return generator.to_benchmark_suite(benchmark)


if __name__ == "__main__":
    # Test with a sample SKILL.md
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmarks from SKILL.md")
    parser.add_argument("--skill", required=True, help="Skill name")
    parser.add_argument("--skill-md", help="Path to SKILL.md file")
    args = parser.parse_args()

    # Load SKILL.md
    if args.skill_md:
        skill_md_path = Path(args.skill_md)
    else:
        # Try default locations
        skill_md_path = Path(f"data/discovered/skills/{args.skill}/SKILL.md")

    if not skill_md_path.exists():
        print(f"Error: SKILL.md not found at {skill_md_path}")
        exit(1)

    skill_md_content = skill_md_path.read_text()

    # Generate benchmarks
    generator = TestGenerator()
    benchmark = generator.generate_benchmarks(args.skill, skill_md_content)

    print("\n=== Generated Benchmark ===")
    print(f"Skill: {benchmark.skill_name}")
    print(f"Claims: {benchmark.skill_claims}")
    print(f"\nTasks:")
    for task in benchmark.tasks:
        print(f"  [{task.difficulty}] {task.id}: {task.prompt[:60]}...")
    print(f"\nQuality prompts: {benchmark.quality_prompts}")
