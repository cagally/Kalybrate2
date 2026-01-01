"""
Scoring system for calculating final skill ratings.
Uses 60% task completion + 40% quality improvement formula.
Tracks token usage and estimates cost.
"""

from typing import List, Dict, Optional
from evaluator.models import (
    TaskResult,
    QualityComparison,
    SkillScore,
    Task,
    DifficultyLevel
)


# Anthropic API pricing (per 1M tokens) - Claude Sonnet 4
SONNET_INPUT_PRICE = 3.00   # $3.00 per 1M input tokens
SONNET_OUTPUT_PRICE = 15.00  # $15.00 per 1M output tokens


class Scorer:
    """Calculate final scores for skills using 60/40 formula"""

    def __init__(
        self,
        task_weight: float = 0.60,
        quality_weight: float = 0.40
    ):
        """
        Initialize scorer with weights.

        Args:
            task_weight: Weight for task completion (default 0.60)
            quality_weight: Weight for quality improvement (default 0.40)
        """
        # Validate weights sum to 1.0
        total = task_weight + quality_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        self.task_weight = task_weight
        self.quality_weight = quality_weight

    def calculate_task_metrics(
        self,
        task_results: List[TaskResult],
        tasks: Optional[List[Task]] = None
    ) -> Dict:
        """
        Calculate task completion metrics.
        Only counts VERIFIED criteria toward pass rate.

        Args:
            task_results: List of TaskResult objects
            tasks: Optional list of Task objects (for difficulty tracking)

        Returns:
            Dict with task metrics
        """
        if not task_results:
            return {
                "total_tasks": 0,
                "tasks_passed": 0,
                "task_pass_rate": 0.0,
                "tasks_by_difficulty": {},
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "verified_criteria_passed": 0,
                "verified_criteria_total": 0,
                "verification_summary": {
                    "full": 0,
                    "partial": 0,
                    "unverified": 0
                }
            }

        total = len(task_results)
        passed = sum(1 for r in task_results if r.passed)

        # Aggregate verified criteria across all tasks
        total_verified_passed = sum(r.verified_criteria_passed for r in task_results)
        total_verified_total = sum(r.verified_criteria_total for r in task_results)

        # Calculate pass rate based on VERIFIED criteria only
        if total_verified_total > 0:
            pass_rate = total_verified_passed / total_verified_total
        else:
            pass_rate = 0.0  # No verified criteria = 0%

        # Track total tokens from task runs
        total_input_tokens = sum(r.input_tokens for r in task_results)
        total_output_tokens = sum(r.output_tokens for r in task_results)

        # Track verification levels
        verification_summary = {
            "full": sum(1 for r in task_results if r.verification_level.value == "full"),
            "partial": sum(1 for r in task_results if r.verification_level.value == "partial"),
            "unverified": sum(1 for r in task_results if r.verification_level.value == "unverified")
        }

        # Track by difficulty if tasks provided
        by_difficulty = {
            "easy": {"total": 0, "passed": 0},
            "medium": {"total": 0, "passed": 0},
            "hard": {"total": 0, "passed": 0}
        }

        if tasks and len(tasks) == len(task_results):
            # Map task_id to difficulty
            task_difficulty_map = {t.id: t.difficulty for t in tasks}

            for result in task_results:
                difficulty = task_difficulty_map.get(result.task_id)
                if difficulty:
                    # Handle both enum and string
                    diff_str = difficulty.value if hasattr(difficulty, 'value') else str(difficulty)
                    if diff_str in by_difficulty:
                        by_difficulty[diff_str]["total"] += 1
                        if result.passed:
                            by_difficulty[diff_str]["passed"] += 1

        return {
            "total_tasks": total,
            "tasks_passed": passed,
            "task_pass_rate": pass_rate,
            "tasks_by_difficulty": by_difficulty,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "verified_criteria_passed": total_verified_passed,
            "verified_criteria_total": total_verified_total,
            "verification_summary": verification_summary
        }

    def calculate_quality_metrics(
        self,
        quality_comparisons: List[QualityComparison]
    ) -> Dict:
        """
        Calculate quality improvement metrics.

        Args:
            quality_comparisons: List of QualityComparison objects

        Returns:
            Dict with quality metrics
        """
        if not quality_comparisons:
            return {
                "total_quality_comparisons": 0,
                "quality_wins": 0,
                "quality_losses": 0,
                "quality_ties": 0,
                "quality_win_rate": None,  # None = not tested (don't fake 50%)
                "quality_tested": False,
                "avg_input_tokens_with_skill": 0.0,
                "avg_output_tokens_with_skill": 0.0,
                "avg_input_tokens_without_skill": 0.0,
                "avg_output_tokens_without_skill": 0.0
            }

        total = len(quality_comparisons)

        # Count wins, losses, ties
        wins = sum(1 for c in quality_comparisons if c.judge_verdict == "with_skill")
        losses = sum(1 for c in quality_comparisons if c.judge_verdict == "without_skill")
        ties = sum(1 for c in quality_comparisons if c.judge_verdict == "tie")

        # Win rate: wins / (wins + losses), ties don't count
        contested = wins + losses
        win_rate = wins / contested if contested > 0 else 0.5

        # Calculate average tokens
        avg_input_with = sum(c.with_skill_input_tokens for c in quality_comparisons) / total
        avg_output_with = sum(c.with_skill_output_tokens for c in quality_comparisons) / total
        avg_input_without = sum(c.without_skill_input_tokens for c in quality_comparisons) / total
        avg_output_without = sum(c.without_skill_output_tokens for c in quality_comparisons) / total

        return {
            "total_quality_comparisons": total,
            "quality_wins": wins,
            "quality_losses": losses,
            "quality_ties": ties,
            "quality_win_rate": win_rate,
            "quality_tested": True,
            "avg_input_tokens_with_skill": avg_input_with,
            "avg_output_tokens_with_skill": avg_output_with,
            "avg_input_tokens_without_skill": avg_input_without,
            "avg_output_tokens_without_skill": avg_output_without
        }

    def calculate_overall_score(
        self,
        task_pass_rate: float,
        quality_win_rate: Optional[float],
        quality_tested: bool
    ) -> float:
        """
        Calculate overall score from component rates.

        Formula:
        - If quality tested: overall = (task_pass_rate * 60%) + (quality_win_rate * 40%)
        - If NOT tested: overall = task_pass_rate * 60% (only the tested portion)

        Result is scaled to 0-100.

        Args:
            task_pass_rate: Task completion rate (0.0-1.0)
            quality_win_rate: Quality win rate (0.0-1.0) or None if not tested
            quality_tested: Whether quality tests were run

        Returns:
            Overall score (0.0-100.0)
        """
        if quality_tested and quality_win_rate is not None:
            # Full score with both components
            score = (
                task_pass_rate * self.task_weight +
                quality_win_rate * self.quality_weight
            )
        else:
            # Only task completion was tested - score out of 60 possible points
            score = task_pass_rate * self.task_weight

        # Scale to 0-100
        return score * 100.0

    def assign_grade(self, overall_score: float, quality_tested: bool) -> str:
        """
        Assign letter grade based on overall score.

        Args:
            overall_score: Score from 0-100
            quality_tested: Whether quality tests were run

        Returns:
            Letter grade A-F, with * suffix if incomplete
        """
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        # Mark as incomplete if quality not tested
        if not quality_tested:
            grade += "*"  # e.g., "B*" means incomplete

        return grade

    def estimate_cost(
        self,
        avg_input_tokens: float,
        avg_output_tokens: float
    ) -> str:
        """
        Estimate cost per use based on token usage.

        Args:
            avg_input_tokens: Average input tokens per use
            avg_output_tokens: Average output tokens per use

        Returns:
            Cost string like "$0.0045"
        """
        input_cost = (avg_input_tokens / 1_000_000) * SONNET_INPUT_PRICE
        output_cost = (avg_output_tokens / 1_000_000) * SONNET_OUTPUT_PRICE
        total_cost = input_cost + output_cost

        if total_cost < 0.01:
            return f"${total_cost:.4f}"
        else:
            return f"${total_cost:.2f}"

    def create_skill_score(
        self,
        skill_name: str,
        task_results: List[TaskResult],
        quality_comparisons: List[QualityComparison],
        execution_time: float,
        tasks: Optional[List[Task]] = None,
        skill_description: Optional[str] = None,
        model_used: str = "claude-sonnet-4-20250514"
    ) -> SkillScore:
        """
        Create complete SkillScore from evaluation results.

        Args:
            skill_name: Name of the skill
            task_results: Task evaluation results
            quality_comparisons: Quality comparison results
            execution_time: Total evaluation time in seconds
            tasks: Optional list of Task objects (for difficulty tracking)
            skill_description: Optional skill description
            model_used: Model used for evaluation

        Returns:
            SkillScore with all metrics
        """
        # Calculate component metrics
        task_metrics = self.calculate_task_metrics(task_results, tasks)
        quality_metrics = self.calculate_quality_metrics(quality_comparisons)

        # Check if quality was actually tested
        quality_tested = quality_metrics.get("quality_tested", False)

        # Calculate overall score using 60/40 formula
        overall_score = self.calculate_overall_score(
            task_pass_rate=task_metrics["task_pass_rate"],
            quality_win_rate=quality_metrics["quality_win_rate"],
            quality_tested=quality_tested
        )

        # Assign grade (with * suffix if incomplete)
        grade = self.assign_grade(overall_score, quality_tested)

        # Calculate average tokens across all operations
        total_input = task_metrics["total_input_tokens"]
        total_output = task_metrics["total_output_tokens"]
        num_task_runs = task_metrics["total_tasks"]

        # Add quality test tokens
        num_quality_runs = quality_metrics["total_quality_comparisons"]
        if num_quality_runs > 0:
            total_input += quality_metrics["avg_input_tokens_with_skill"] * num_quality_runs
            total_output += quality_metrics["avg_output_tokens_with_skill"] * num_quality_runs

        total_runs = num_task_runs + num_quality_runs
        avg_input = total_input / total_runs if total_runs > 0 else 0
        avg_output = total_output / total_runs if total_runs > 0 else 0

        # Estimate cost per use
        cost_estimate = self.estimate_cost(avg_input, avg_output)

        # Create SkillScore
        return SkillScore(
            skill_name=skill_name,
            skill_description=skill_description,
            total_tasks=task_metrics["total_tasks"],
            tasks_passed=task_metrics["tasks_passed"],
            task_pass_rate=task_metrics["task_pass_rate"],
            tasks_by_difficulty=task_metrics["tasks_by_difficulty"],
            total_quality_comparisons=quality_metrics["total_quality_comparisons"],
            quality_wins=quality_metrics["quality_wins"],
            quality_losses=quality_metrics["quality_losses"],
            quality_ties=quality_metrics["quality_ties"],
            quality_win_rate=quality_metrics["quality_win_rate"],
            overall_score=overall_score,
            grade=grade,
            avg_input_tokens=avg_input,
            avg_output_tokens=avg_output,
            avg_total_tokens=avg_input + avg_output,
            estimated_cost_per_use=cost_estimate,
            execution_time=execution_time,
            model_used=model_used
        )


def score_skill(
    skill_name: str,
    task_results: List[TaskResult],
    quality_comparisons: List[QualityComparison],
    execution_time: float = 0.0,
    tasks: Optional[List[Task]] = None,
    skill_description: Optional[str] = None
) -> SkillScore:
    """
    Quick helper function to score a skill.

    Args:
        skill_name: Skill name
        task_results: Task results
        quality_comparisons: Quality comparisons
        execution_time: Total time
        tasks: Optional tasks for difficulty tracking
        skill_description: Optional description

    Returns:
        SkillScore
    """
    scorer = Scorer()
    return scorer.create_skill_score(
        skill_name=skill_name,
        task_results=task_results,
        quality_comparisons=quality_comparisons,
        execution_time=execution_time,
        tasks=tasks,
        skill_description=skill_description
    )
