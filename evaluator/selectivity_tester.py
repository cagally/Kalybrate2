"""
Selectivity testing - verifies that skills DON'T activate on irrelevant prompts.
A good skill should be selective and only activate when appropriate.
"""

import os
import time
import tempfile
import shutil
from typing import List, Optional
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import SelectivityTest, SelectivityResult
from evaluator.verifiers import find_created_files


load_dotenv()


class SelectivityTester:
    """Tests that skills don't over-activate on irrelevant prompts"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101",
        timeout: int = 30
    ):
        """
        Initialize selectivity tester.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            timeout: Timeout per test
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.timeout = timeout
        self.work_dir = None

    def setup_work_directory(self) -> str:
        """Create temporary working directory"""
        if self.work_dir and os.path.exists(self.work_dir):
            return self.work_dir

        self.work_dir = tempfile.mkdtemp(prefix="kalybrate_selectivity_")
        return self.work_dir

    def cleanup_work_directory(self):
        """Remove temporary working directory"""
        if self.work_dir and os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
            self.work_dir = None

    def run_selectivity_test(
        self,
        test: SelectivityTest,
        skill_name: str,
        expected_file_extensions: List[str] = None
    ) -> SelectivityResult:
        """
        Run a single selectivity test.

        A test PASSES if the skill does NOT create files.
        A test FAILS if the skill incorrectly creates files.

        Args:
            test: SelectivityTest to run
            skill_name: Skill being tested
            expected_file_extensions: File types that skill normally creates

        Returns:
            SelectivityResult
        """
        work_dir = self.setup_work_directory()

        try:
            # Construct prompt with skill context
            prompt = f"[Using skill: {skill_name}]\n\n{test.prompt}"
            prompt += f"\n\nWorking directory: {work_dir}"

            # Call API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            # Check for created files
            created_files = find_created_files(
                work_dir,
                extensions=expected_file_extensions
            )

            # Test PASSES if NO files were created (skill correctly did not activate)
            passed = len(created_files) == 0

            explanation = None
            if not passed:
                explanation = f"Skill incorrectly created {len(created_files)} file(s) for irrelevant prompt"

            return SelectivityResult(
                test_id=test.id,
                passed=passed,
                files_created=created_files,
                explanation=explanation
            )

        except Exception as e:
            return SelectivityResult(
                test_id=test.id,
                passed=False,
                files_created=[],
                explanation=f"Error during test: {str(e)}"
            )

        finally:
            self.cleanup_work_directory()

    def run_selectivity_tests(
        self,
        tests: List[SelectivityTest],
        skill_name: str,
        expected_file_extensions: List[str] = None
    ) -> List[SelectivityResult]:
        """
        Run multiple selectivity tests.

        Args:
            tests: List of selectivity tests
            skill_name: Skill being tested
            expected_file_extensions: File types the skill creates

        Returns:
            List of SelectivityResults
        """
        results = []

        for i, test in enumerate(tests):
            print(f"Running selectivity test {i+1}/{len(tests)}: {test.id}")
            print(f"  Prompt: {test.prompt[:60]}...")

            result = self.run_selectivity_test(
                test,
                skill_name=skill_name,
                expected_file_extensions=expected_file_extensions
            )

            results.append(result)

            status = "PASS (no files)" if result.passed else "FAIL (files created)"
            print(f"  Result: {status}")

            # Reset work directory
            self.setup_work_directory()

        return results

    def calculate_selectivity_rate(self, results: List[SelectivityResult]) -> float:
        """
        Calculate selectivity pass rate.

        Args:
            results: List of SelectivityResults

        Returns:
            Pass rate between 0.0 and 1.0
        """
        if not results:
            return 0.0

        passed = sum(1 for r in results if r.passed)
        return passed / len(results)

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup_work_directory()


def test_selectivity(
    skill_name: str,
    prompts: List[str],
    expected_extensions: List[str] = None
) -> dict:
    """
    Quick helper function to test selectivity.

    Args:
        skill_name: Skill to test
        prompts: List of prompts that should NOT trigger skill
        expected_extensions: File types skill creates

    Returns:
        Dict with results summary
    """
    tester = SelectivityTester()

    tests = [
        SelectivityTest(
            id=f"quick_test_{i}",
            prompt=prompt,
            description="Quick selectivity test"
        )
        for i, prompt in enumerate(prompts)
    ]

    results = tester.run_selectivity_tests(
        tests,
        skill_name=skill_name,
        expected_file_extensions=expected_extensions
    )

    rate = tester.calculate_selectivity_rate(results)

    return {
        "total_tests": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "selectivity_rate": rate,
        "grade": "A" if rate >= 0.9 else "B" if rate >= 0.8 else "C" if rate >= 0.7 else "F"
    }
