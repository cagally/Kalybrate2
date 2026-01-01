"""
Data logger for saving detailed evaluation results.
Creates structured data for debugging and website transparency.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class DataLogger:
    """Saves detailed evaluation data for each skill"""

    def __init__(self, base_dir: str = "data/evaluations"):
        self.base_dir = Path(base_dir)

    def setup_skill_dir(self, skill_name: str) -> Path:
        """Create evaluation directory for a skill"""
        skill_dir = self.base_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (skill_dir / "task_results").mkdir(exist_ok=True)
        (skill_dir / "quality_comparisons").mkdir(exist_ok=True)

        return skill_dir

    def save_skill_md(self, skill_name: str, skill_md_content: str):
        """Save copy of SKILL.md content"""
        skill_dir = self.setup_skill_dir(skill_name)
        skill_md_path = skill_dir / "skill.md"

        with open(skill_md_path, 'w') as f:
            f.write(skill_md_content)

    def save_generated_tests(
        self,
        skill_name: str,
        skill_claims: List[str],
        tasks: List[Dict],
        quality_prompts: List[str],
        model: str = "claude-sonnet-4-20250514"
    ):
        """Save the generated benchmark tests"""
        skill_dir = self.setup_skill_dir(skill_name)
        tests_path = skill_dir / "generated_tests.json"

        data = {
            "skill_claims": skill_claims,
            "tasks": tasks,
            "quality_prompts": quality_prompts,
            "generated_at": datetime.utcnow().isoformat(),
            "model": model
        }

        with open(tests_path, 'w') as f:
            json.dump(data, f, indent=2)

    def save_task_result(
        self,
        skill_name: str,
        task_id: str,
        prompt: str,
        difficulty: str,
        model: str,
        response: str,
        criteria_results: Dict[str, bool],
        verification_notes: Dict[str, str],
        verification_level: str,
        verified_criteria_passed: int,
        verified_criteria_total: int,
        passed: bool,
        input_tokens: int,
        output_tokens: int,
        execution_time: float,
        error: Optional[str] = None
    ):
        """Save detailed result for a single task"""
        skill_dir = self.setup_skill_dir(skill_name)
        result_path = skill_dir / "task_results" / f"{task_id}.json"

        data = {
            "task_id": task_id,
            "prompt": prompt,
            "difficulty": difficulty,
            "model": model,
            "response": response,  # Full response - don't truncate
            "criteria_results": criteria_results,
            "verification_notes": verification_notes,
            "verification_level": verification_level,
            "verified_criteria": {
                "passed": verified_criteria_passed,
                "total": verified_criteria_total
            },
            "passed": passed,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "execution_time": execution_time,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        with open(result_path, 'w') as f:
            json.dump(data, f, indent=2)

    def save_quality_comparison(
        self,
        skill_name: str,
        comparison_index: int,
        prompt: str,
        baseline_response: str,
        baseline_input_tokens: int,
        baseline_output_tokens: int,
        skill_response: str,
        skill_input_tokens: int,
        skill_output_tokens: int,
        judge_verdict: str,
        judge_reasoning: str,
        judge_model: str = "claude-sonnet-4-20250514"
    ):
        """Save detailed result for a quality A/B comparison"""
        skill_dir = self.setup_skill_dir(skill_name)
        result_path = skill_dir / "quality_comparisons" / f"{comparison_index}.json"

        data = {
            "prompt": prompt,
            "baseline_response": baseline_response,  # Full response
            "baseline_tokens": {
                "input": baseline_input_tokens,
                "output": baseline_output_tokens,
                "total": baseline_input_tokens + baseline_output_tokens
            },
            "skill_response": skill_response,  # Full response
            "skill_tokens": {
                "input": skill_input_tokens,
                "output": skill_output_tokens,
                "total": skill_input_tokens + skill_output_tokens
            },
            "judge_verdict": judge_verdict,
            "judge_reasoning": judge_reasoning,
            "judge_model": judge_model,
            "timestamp": datetime.utcnow().isoformat()
        }

        with open(result_path, 'w') as f:
            json.dump(data, f, indent=2)

    def save_summary(
        self,
        skill_name: str,
        overall_score: float,
        grade: str,
        tasks_passed: int,
        tasks_total: int,
        task_pass_rate: float,
        verified_criteria_passed: int,
        verified_criteria_total: int,
        verification_summary: Dict[str, int],
        quality_wins: int,
        quality_losses: int,
        quality_ties: int,
        quality_win_rate: Optional[float],
        avg_tokens: float,
        estimated_cost: str,
        task_model: str,
        judge_model: str,
        execution_time: float
    ):
        """Save evaluation summary"""
        skill_dir = self.setup_skill_dir(skill_name)
        summary_path = skill_dir / "summary.json"

        data = {
            "skill_name": skill_name,
            "overall_score": overall_score,
            "grade": grade,
            "task_completion": {
                "passed": tasks_passed,
                "total": tasks_total,
                "rate": task_pass_rate * 100,
                "verified_criteria": {
                    "passed": verified_criteria_passed,
                    "total": verified_criteria_total
                },
                "verification_levels": verification_summary
            },
            "quality_improvement": {
                "wins": quality_wins,
                "losses": quality_losses,
                "ties": quality_ties,
                "win_rate": quality_win_rate * 100 if quality_win_rate is not None else None,
                "tested": quality_win_rate is not None
            },
            "cost": {
                "avg_tokens": round(avg_tokens),
                "estimated_per_use": estimated_cost
            },
            "evaluated_at": datetime.utcnow().isoformat(),
            "execution_time": execution_time,
            "models_used": {
                "task_execution": task_model,
                "quality_judge": judge_model
            }
        }

        with open(summary_path, 'w') as f:
            json.dump(data, f, indent=2)

        return data

    def update_leaderboard(self, skill_summary: Dict):
        """Update the global leaderboard with a skill's results"""
        leaderboard_path = self.base_dir.parent / "leaderboard.json"

        # Load existing leaderboard
        if leaderboard_path.exists():
            with open(leaderboard_path) as f:
                leaderboard = json.load(f)
        else:
            leaderboard = {
                "updated_at": None,
                "skills": []
            }

        # Remove existing entry for this skill if present
        leaderboard["skills"] = [
            s for s in leaderboard["skills"]
            if s.get("skill_name") != skill_summary["skill_name"]
        ]

        # Add new entry
        leaderboard["skills"].append({
            "skill_name": skill_summary["skill_name"],
            "overall_score": skill_summary["overall_score"],
            "grade": skill_summary["grade"],
            "task_pass_rate": skill_summary["task_completion"]["rate"],
            "quality_win_rate": skill_summary["quality_improvement"]["win_rate"],
            "quality_tested": skill_summary["quality_improvement"]["tested"],
            "estimated_cost": skill_summary["cost"]["estimated_per_use"],
            "evaluated_at": skill_summary["evaluated_at"]
        })

        # Sort by overall score descending
        leaderboard["skills"].sort(
            key=lambda x: x["overall_score"],
            reverse=True
        )

        # Add ranks
        for i, skill in enumerate(leaderboard["skills"]):
            skill["rank"] = i + 1

        leaderboard["updated_at"] = datetime.utcnow().isoformat()
        leaderboard["total_skills"] = len(leaderboard["skills"])

        # Save
        with open(leaderboard_path, 'w') as f:
            json.dump(leaderboard, f, indent=2)

        return leaderboard
