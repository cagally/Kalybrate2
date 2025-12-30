"""
Scoring system for calculating final skill ratings.
Combines task completion, selectivity, and quality metrics.
"""

import time
from typing import List, Dict
from evaluator.models import (
    TaskResult,
    SelectivityResult,
    QualityComparison,
    SkillScore,
    DifficultyLevel
)


class Scorer:
    """Calculate final scores for skills"""

    def __init__(
        self,
        task_weight: float = 0.50,
        selectivity_weight: float = 0.25,
        quality_weight: float = 0.25
    ):
        """
        Initialize scorer with custom weights.

        Args:
            task_weight: Weight for task completion (default 0.50)
            selectivity_weight: Weight for selectivity (default 0.25)
            quality_weight: Weight for quality improvement (default 0.25)
        """
        # Validate weights sum to 1.0
        total = task_weight + selectivity_weight + quality_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        self.task_weight = task_weight
        self.selectivity_weight = selectivity_weight
        self.quality_weight = quality_weight

    def calculate_task_metrics(
        self,
        task_results: List[TaskResult]
    ) -> Dict:
        """
        Calculate task completion metrics.

        Args:
            task_results: List of TaskResult objects

        Returns:
            Dict with task metrics
        """
        if not task_results:
            return {
                "total_tasks": 0,
                "tasks_passed": 0,
                "task_pass_rate": 0.0,
                "tasks_by_difficulty": {}
            }

        total = len(task_results)
        passed = sum(1 for r in task_results if r.passed)
        pass_rate = passed / total

        # Track by difficulty (if available)
        by_difficulty = {}
        # Note: TaskResult doesn't have difficulty, we'd need to track this separately
        # For now, just provide overall metrics

        return {
            "total_tasks": total,
            "tasks_passed": passed,
            "task_pass_rate": pass_rate,
            "tasks_by_difficulty": by_difficulty
        }

    def calculate_selectivity_metrics(
        self,
        selectivity_results: List[SelectivityResult]
    ) -> Dict:
        """
        Calculate selectivity metrics.

        Args:
            selectivity_results: List of SelectivityResult objects

        Returns:
            Dict with selectivity metrics
        """
        if not selectivity_results:
            return {
                "total_selectivity_tests": 0,
                "selectivity_passed": 0,
                "selectivity_rate": 0.0
            }

        total = len(selectivity_results)
        passed = sum(1 for r in selectivity_results if r.passed)
        rate = passed / total

        return {
            "total_selectivity_tests": total,
            "selectivity_passed": passed,
            "selectivity_rate": rate
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
                "quality_improvement_rate": 0.0,
                "avg_tokens_with_skill": None,
                "avg_tokens_without_skill": None
            }

        total = len(quality_comparisons)

        # Count wins (ties count as 0.5)
        wins = sum(1 for c in quality_comparisons if c.judge_verdict == "with_skill")
        ties = sum(1 for c in quality_comparisons if c.judge_verdict == "tie")
        improvement_rate = (wins + (ties * 0.5)) / total

        # Calculate average tokens
        avg_with = sum(c.with_skill_tokens for c in quality_comparisons) / total
        avg_without = sum(c.without_skill_tokens for c in quality_comparisons) / total

        return {
            "total_quality_comparisons": total,
            "quality_wins": wins,
            "quality_improvement_rate": improvement_rate,
            "avg_tokens_with_skill": avg_with,
            "avg_tokens_without_skill": avg_without
        }

    def calculate_overall_score(
        self,
        task_pass_rate: float,
        selectivity_rate: float,
        quality_improvement_rate: float
    ) -> float:
        """
        Calculate overall score from component rates.

        Formula:
        overall = (task_pass_rate * task_weight) +
                  (selectivity_rate * selectivity_weight) +
                  (quality_improvement_rate * quality_weight)

        Result is scaled to 0-100.

        Args:
            task_pass_rate: Task completion rate (0.0-1.0)
            selectivity_rate: Selectivity rate (0.0-1.0)
            quality_improvement_rate: Quality improvement rate (0.0-1.0)

        Returns:
            Overall score (0.0-100.0)
        """
        score = (
            task_pass_rate * self.task_weight +
            selectivity_rate * self.selectivity_weight +
            quality_improvement_rate * self.quality_weight
        )

        # Scale to 0-100
        return score * 100.0

    def assign_grade(self, overall_score: float) -> str:
        """
        Assign letter grade based on overall score.

        Args:
            overall_score: Score from 0-100

        Returns:
            Letter grade A-F
        """
        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"

    def create_skill_score(
        self,
        skill_name: str,
        task_results: List[TaskResult],
        selectivity_results: List[SelectivityResult],
        quality_comparisons: List[QualityComparison],
        execution_time: float
    ) -> SkillScore:
        """
        Create complete SkillScore from evaluation results.

        Args:
            skill_name: Name of the skill
            task_results: Task evaluation results
            selectivity_results: Selectivity test results
            quality_comparisons: Quality comparison results
            execution_time: Total evaluation time in seconds

        Returns:
            SkillScore with all metrics
        """
        # Calculate component metrics
        task_metrics = self.calculate_task_metrics(task_results)
        selectivity_metrics = self.calculate_selectivity_metrics(selectivity_results)
        quality_metrics = self.calculate_quality_metrics(quality_comparisons)

        # Calculate overall score
        overall_score = self.calculate_overall_score(
            task_pass_rate=task_metrics["task_pass_rate"],
            selectivity_rate=selectivity_metrics["selectivity_rate"],
            quality_improvement_rate=quality_metrics["quality_improvement_rate"]
        )

        # Assign grade
        grade = self.assign_grade(overall_score)

        # Create SkillScore
        return SkillScore(
            skill_name=skill_name,
            total_tasks=task_metrics["total_tasks"],
            tasks_passed=task_metrics["tasks_passed"],
            task_pass_rate=task_metrics["task_pass_rate"],
            tasks_by_difficulty=task_metrics["tasks_by_difficulty"],
            total_selectivity_tests=selectivity_metrics["total_selectivity_tests"],
            selectivity_passed=selectivity_metrics["selectivity_passed"],
            selectivity_rate=selectivity_metrics["selectivity_rate"],
            total_quality_comparisons=quality_metrics["total_quality_comparisons"],
            quality_wins=quality_metrics["quality_wins"],
            quality_improvement_rate=quality_metrics["quality_improvement_rate"],
            overall_score=overall_score,
            grade=grade,
            avg_tokens_with_skill=quality_metrics.get("avg_tokens_with_skill"),
            avg_tokens_without_skill=quality_metrics.get("avg_tokens_without_skill"),
            execution_time=execution_time
        )


def score_skill(
    skill_name: str,
    task_results: List[TaskResult],
    selectivity_results: List[SelectivityResult],
    quality_comparisons: List[QualityComparison],
    execution_time: float = 0.0
) -> SkillScore:
    """
    Quick helper function to score a skill.

    Args:
        skill_name: Skill name
        task_results: Task results
        selectivity_results: Selectivity results
        quality_comparisons: Quality comparisons
        execution_time: Total time

    Returns:
        SkillScore
    """
    scorer = Scorer()
    return scorer.create_skill_score(
        skill_name=skill_name,
        task_results=task_results,
        selectivity_results=selectivity_results,
        quality_comparisons=quality_comparisons,
        execution_time=execution_time
    )
