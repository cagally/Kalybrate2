"""
Task runner for executing evaluation tasks via Anthropic API.
Runs tasks with skills and verifies all success criteria.
Tracks token usage for cost analysis.
"""

import os
import time
import json
import re
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import tempfile
import shutil

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import Task, TaskResult, OutputType
from evaluator.verifiers import verify_file, find_created_files

load_dotenv()


class TaskRunner:
    """Executes tasks and verifies results with token tracking"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-haiku-20241022",  # Haiku for cost-efficient task execution
        timeout: int = 60
    ):
        """
        Initialize task runner.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default Sonnet for cost efficiency)
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

    def _extract_code_blocks(self, response_text: str) -> List[Tuple[str, str]]:
        """
        Extract code blocks from response.

        Returns:
            List of (language, code) tuples
        """
        # Find ```language\ncode``` blocks
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, response_text, re.DOTALL)
        return [(lang or 'unknown', code) for lang, code in matches]

    def _execute_python_from_response(self, response_text: str, work_dir: str) -> bool:
        """
        Extract and execute Python code from Claude's response.
        Returns True if any code was executed successfully.
        """
        code_blocks = re.findall(r'```python\n(.*?)```', response_text, re.DOTALL)

        if not code_blocks:
            code_blocks = re.findall(r'```\n(.*?)```', response_text, re.DOTALL)

        executed = False
        for code in code_blocks:
            if len(code.strip()) < 50:
                continue

            file_keywords = ['save', 'write', 'open(', 'to_excel', 'savefig',
                           'pdfwriter', '.build(', 'canvas', 'workbook', 'document']
            if not any(kw in code.lower() for kw in file_keywords):
                continue

            try:
                script_path = os.path.join(work_dir, "_temp_script.py")

                # Remove OUTPUT_DIR redefinitions
                clean_code = re.sub(r'^OUTPUT_DIR\s*=.*$', '', code, flags=re.MULTILINE)
                clean_code = re.sub(r'OUTPUT_DIR\s*=\s*os\.environ\.get.*$', '', clean_code, flags=re.MULTILINE)

                full_code = f'''
import os
os.chdir("{work_dir}")
OUTPUT_DIR = "{work_dir}"

{clean_code}
'''

                with open(script_path, 'w') as f:
                    f.write(full_code)

                result = subprocess.run(
                    ['python3', script_path],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if os.path.exists(script_path):
                    os.remove(script_path)

                if result.returncode == 0:
                    executed = True

            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

        return executed

    def _verify_code_compiles(self, code: str, language: str) -> Tuple[bool, str]:
        """
        Verify that code compiles/is syntactically valid.

        Returns:
            (success, error_message)
        """
        if language in ['python', 'py']:
            try:
                compile(code, '<string>', 'exec')
                return True, ""
            except SyntaxError as e:
                return False, str(e)

        elif language in ['typescript', 'ts']:
            # Write to temp file and run tsc
            try:
                with tempfile.NamedTemporaryFile(suffix='.ts', delete=False) as f:
                    f.write(code.encode())
                    temp_path = f.name

                result = subprocess.run(
                    ['npx', 'tsc', '--noEmit', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                os.unlink(temp_path)

                if result.returncode == 0:
                    return True, ""
                return False, result.stderr[:200]

            except FileNotFoundError:
                return True, "TypeScript compiler not available"
            except Exception as e:
                return False, str(e)

        elif language in ['javascript', 'js']:
            # Basic syntax check with Node
            try:
                with tempfile.NamedTemporaryFile(suffix='.js', delete=False) as f:
                    f.write(code.encode())
                    temp_path = f.name

                result = subprocess.run(
                    ['node', '--check', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                os.unlink(temp_path)

                if result.returncode == 0:
                    return True, ""
                return False, result.stderr[:200]

            except FileNotFoundError:
                return True, "Node not available"
            except Exception as e:
                return False, str(e)

        # Unknown language - assume valid
        return True, ""

    def run_task(
        self,
        task: Task,
        skill_name: Optional[str] = None,
        skill_md_content: Optional[str] = None,
        save_output: bool = False
    ) -> TaskResult:
        """
        Run a single task and verify results.

        Args:
            task: Task to execute
            skill_name: Optional skill name to activate
            skill_md_content: The full SKILL.md content to include in system prompt
            save_output: Whether to save output files

        Returns:
            TaskResult with pass/fail, criteria results, and token usage
        """
        start_time = time.time()
        work_dir = self.setup_work_directory()

        input_tokens = 0
        output_tokens = 0

        try:
            # Build system prompt with SKILL.md content
            system_prompt = None
            if skill_name and skill_md_content:
                system_prompt = f"""You have access to a skill: {skill_name}

SKILL.md:
---
{skill_md_content}
---

Follow these instructions when relevant. When creating files, write Python code that saves files to the specified directory."""

            # Build user prompt based on expected output type
            prompt = task.prompt
            output_type = getattr(task, 'expected_output_type', OutputType.FILE)

            if output_type == OutputType.FILE:
                prompt += f"\n\nIMPORTANT: Save any files using the OUTPUT_DIR variable (do NOT redefine it). OUTPUT_DIR = \"{work_dir}\""
                prompt += "\n\nProvide complete, executable Python code that creates the requested file."
            elif output_type == OutputType.CODE:
                prompt += "\n\nProvide complete, working code with proper syntax."

            # Call Anthropic API
            api_params = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                api_params["system"] = system_prompt

            message = self.client.messages.create(**api_params)

            # Track token usage
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens

            response_text = message.content[0].text if message.content else ""

            # Verify based on output type
            criteria_results = {}

            if output_type == OutputType.FILE:
                # Execute Python code to create files
                self._execute_python_from_response(response_text, work_dir)

                # Find created files
                expected_ext = task.expected_file_type
                extensions = [expected_ext] if expected_ext else None
                created_files = find_created_files(work_dir, extensions=extensions)

                # Check file criteria
                if "file_created" in task.success_criteria:
                    criteria_results["file_created"] = len(created_files) > 0

                if created_files:
                    primary_file = created_files[0]
                    file_verification = verify_file(primary_file, task.success_criteria)
                    criteria_results.update(file_verification)

                    if save_output:
                        output_dir = Path("data/task_outputs") / task.id
                        output_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy(primary_file, output_dir / Path(primary_file).name)
                else:
                    for criterion in task.success_criteria:
                        if criterion not in criteria_results:
                            criteria_results[criterion] = False
                    created_files = []

            elif output_type == OutputType.CODE:
                # Extract and verify code
                code_blocks = self._extract_code_blocks(response_text)
                created_files = []

                if "code_extracted" in task.success_criteria:
                    criteria_results["code_extracted"] = len(code_blocks) > 0

                if "code_compiles" in task.success_criteria and code_blocks:
                    lang, code = code_blocks[0]
                    compiles, error = self._verify_code_compiles(code, lang)
                    criteria_results["code_compiles"] = compiles

                if "has_type_annotations" in task.success_criteria and code_blocks:
                    lang, code = code_blocks[0]
                    has_types = ':' in code and ('string' in code or 'number' in code or 'boolean' in code or ': ' in code)
                    criteria_results["has_type_annotations"] = has_types

                if "has_docstrings" in task.success_criteria and code_blocks:
                    lang, code = code_blocks[0]
                    has_docstrings = '"""' in code or "'''" in code
                    criteria_results["has_docstrings"] = has_docstrings

                # For response_relevant on code tasks - check code blocks exist and have content
                if "response_relevant" in task.success_criteria:
                    criteria_results["response_relevant"] = len(code_blocks) > 0 and len(code_blocks[0][1]) > 50

            else:  # TEXT output
                created_files = []

                if "response_exists" in task.success_criteria:
                    criteria_results["response_exists"] = len(response_text.strip()) > 0

                # For response_relevant, we'd need LLM judge - skip for now
                if "response_relevant" in task.success_criteria:
                    criteria_results["response_relevant"] = len(response_text.strip()) > 50

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
                files_created=created_files if output_type == OutputType.FILE else [],
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

        except Exception as e:
            execution_time = time.time() - start_time
            criteria_results = {
                criterion: False for criterion in task.success_criteria
            }

            return TaskResult(
                task_id=task.id,
                passed=False,
                criteria_results=criteria_results,
                error=str(e),
                execution_time=execution_time,
                files_created=[],
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )

    def run_tasks(
        self,
        tasks: List[Task],
        skill_name: Optional[str] = None,
        skill_md_content: Optional[str] = None,
        save_output: bool = False
    ) -> List[TaskResult]:
        """
        Run multiple tasks.

        Args:
            tasks: List of tasks to execute
            skill_name: Optional skill name to activate
            skill_md_content: SKILL.md content to include in system prompt
            save_output: Whether to save output files

        Returns:
            List of TaskResults with token usage tracked
        """
        results = []

        for i, task in enumerate(tasks):
            print(f"Running task {i+1}/{len(tasks)}: {task.id}")

            result = self.run_task(
                task,
                skill_name=skill_name,
                skill_md_content=skill_md_content,
                save_output=save_output
            )
            results.append(result)

            # Clean up between tasks
            self.cleanup_work_directory()
            self.setup_work_directory()

            status = 'PASS' if result.passed else 'FAIL'
            tokens = result.input_tokens + result.output_tokens
            print(f"  Result: {status} (tokens: {tokens})")

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
        "execution_time": result.execution_time,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens
    }
