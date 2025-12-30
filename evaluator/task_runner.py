"""
Task runner for executing evaluation tasks via Anthropic API.
Runs tasks with skills and verifies all success criteria.
"""

import os
import time
import json
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
import shutil

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import Task, TaskResult
from evaluator.verifiers import verify_file, find_created_files


# Load environment variables
load_dotenv()


class TaskRunner:
    """Executes tasks and verifies results"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101",
        timeout: int = 60
    ):
        """
        Initialize task runner.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            timeout: Timeout in seconds for each task
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.timeout = timeout
        self.work_dir = None

    def setup_work_directory(self) -> str:
        """Create a temporary working directory for file outputs"""
        if self.work_dir and os.path.exists(self.work_dir):
            return self.work_dir

        self.work_dir = tempfile.mkdtemp(prefix="kalybrate_task_")
        return self.work_dir

    def cleanup_work_directory(self):
        """Remove temporary working directory"""
        if self.work_dir and os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
            self.work_dir = None

    def run_task(
        self,
        task: Task,
        skill_name: Optional[str] = None,
        save_output: bool = False
    ) -> TaskResult:
        """
        Run a single task and verify results.

        Args:
            task: Task to execute
            skill_name: Optional skill name to activate (for WITH skill testing)
            save_output: Whether to save output files

        Returns:
            TaskResult with pass/fail and criteria results
        """
        start_time = time.time()

        # Setup working directory
        work_dir = self.setup_work_directory()

        try:
            # Construct the prompt
            prompt = task.prompt
            if skill_name:
                # Add skill context if needed
                prompt = f"[Using skill: {skill_name}]\n\n{prompt}"

            # Add instruction to save files to work directory
            prompt += f"\n\nPlease save any created files to: {work_dir}"

            # Call Anthropic API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract response
            response_text = message.content[0].text if message.content else ""

            # Find created files
            expected_ext = task.expected_file_type
            extensions = [expected_ext] if expected_ext else None
            created_files = find_created_files(work_dir, extensions=extensions)

            # Verify success criteria
            criteria_results = {}

            # Check file_created criterion
            if "file_created" in task.success_criteria:
                criteria_results["file_created"] = len(created_files) > 0

            # If files were created, verify them
            if created_files:
                primary_file = created_files[0]  # Most recent file

                # Verify file against remaining criteria
                file_verification = verify_file(primary_file, task.success_criteria)
                criteria_results.update(file_verification)

                # Save output if requested
                if save_output:
                    output_dir = Path("data/task_outputs") / task.id
                    output_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy(primary_file, output_dir / Path(primary_file).name)
            else:
                # No files created - fail all file-related criteria
                for criterion in task.success_criteria:
                    if criterion not in criteria_results:
                        criteria_results[criterion] = False

            # Overall pass: ALL criteria must pass
            all_passed = all(
                criteria_results.get(criterion, False)
                for criterion in task.success_criteria
            )

            execution_time = time.time() - start_time

            return TaskResult(
                task_id=task.id,
                passed=all_passed,
                criteria_results=criteria_results,
                error=None,
                execution_time=execution_time,
                files_created=created_files
            )

        except Exception as e:
            execution_time = time.time() - start_time
            # Task failed due to error
            criteria_results = {
                criterion: False for criterion in task.success_criteria
            }

            return TaskResult(
                task_id=task.id,
                passed=False,
                criteria_results=criteria_results,
                error=str(e),
                execution_time=execution_time,
                files_created=[]
            )

    def run_tasks(
        self,
        tasks: List[Task],
        skill_name: Optional[str] = None,
        save_output: bool = False
    ) -> List[TaskResult]:
        """
        Run multiple tasks.

        Args:
            tasks: List of tasks to execute
            skill_name: Optional skill name to activate
            save_output: Whether to save output files

        Returns:
            List of TaskResults
        """
        results = []

        for i, task in enumerate(tasks):
            print(f"Running task {i+1}/{len(tasks)}: {task.id}")

            result = self.run_task(task, skill_name=skill_name, save_output=save_output)
            results.append(result)

            # Clean up between tasks
            self.cleanup_work_directory()
            self.setup_work_directory()

            print(f"  Result: {'PASS' if result.passed else 'FAIL'}")
            if not result.passed:
                failed_criteria = [
                    k for k, v in result.criteria_results.items() if not v
                ]
                print(f"  Failed criteria: {failed_criteria}")

        return results

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup_work_directory()


def run_task_simple(
    prompt: str,
    expected_file_type: Optional[str] = None,
    skill_name: Optional[str] = None
) -> Dict:
    """
    Simple helper function to run a single task.

    Args:
        prompt: Task prompt
        expected_file_type: Expected file extension
        skill_name: Optional skill to use

    Returns:
        Dict with result information
    """
    runner = TaskRunner()

    task = Task(
        id="simple_task",
        prompt=prompt,
        difficulty="easy",
        expected_file_type=expected_file_type,
        success_criteria={"file_created": True}
    )

    result = runner.run_task(task, skill_name=skill_name)

    return {
        "passed": result.passed,
        "files_created": result.files_created,
        "error": result.error,
        "execution_time": result.execution_time
    }
