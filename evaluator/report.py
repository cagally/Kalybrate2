"""
Report generator for Kalybrate evaluation results.
Generates JSON reports for website consumption.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from evaluator.models import (
    SkillScore,
    TaskResult,
    QualityComparison,
    Task,
    SkillReport
)


class ReportGenerator:
    """Generates JSON reports from evaluation results"""

    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_skill_report(
        self,
        score: SkillScore,
        task_results: List[TaskResult],
        quality_comparisons: List[QualityComparison],
        tasks: Optional[List[Task]] = None
    ) -> SkillReport:
        """
        Generate a full skill report.

        Args:
            score: SkillScore with final metrics
            task_results: Individual task results
            quality_comparisons: Quality comparison results
            tasks: Optional task definitions

        Returns:
            SkillReport for website display
        """
        # Build task completion details
        task_completion = {
            "total": score.total_tasks,
            "passed": score.tasks_passed,
            "pass_rate": round(score.task_pass_rate * 100, 1),
            "by_difficulty": score.tasks_by_difficulty,
            "details": []
        }

        # Add individual task results
        task_map = {t.id: t for t in tasks} if tasks else {}
        for result in task_results:
            task = task_map.get(result.task_id)
            task_completion["details"].append({
                "id": result.task_id,
                "passed": result.passed,
                "difficulty": task.difficulty if task else None,
                "criteria": result.criteria_results,
                "execution_time": round(result.execution_time, 2),
                "tokens": result.input_tokens + result.output_tokens
            })

        # Build quality improvement details
        quality_improvement = {
            "total_comparisons": score.total_quality_comparisons,
            "wins": score.quality_wins,
            "losses": score.quality_losses,
            "ties": score.quality_ties,
            "win_rate": round(score.quality_win_rate * 100, 1),
            "details": []
        }

        # Add individual comparison results
        for comp in quality_comparisons:
            quality_improvement["details"].append({
                "prompt": comp.prompt[:100] + "..." if len(comp.prompt) > 100 else comp.prompt,
                "verdict": comp.judge_verdict,
                "reasoning": comp.judge_reasoning,
                "tokens_with_skill": comp.with_skill_input_tokens + comp.with_skill_output_tokens,
                "tokens_without_skill": comp.without_skill_input_tokens + comp.without_skill_output_tokens
            })

        # Build cost details
        cost = {
            "avg_input_tokens": round(score.avg_input_tokens),
            "avg_output_tokens": round(score.avg_output_tokens),
            "avg_total_tokens": round(score.avg_total_tokens),
            "estimated_per_use": score.estimated_cost_per_use
        }

        return SkillReport(
            skill_name=score.skill_name,
            skill_description=score.skill_description,
            overall_score=round(score.overall_score, 1),
            grade=score.grade,
            task_completion=task_completion,
            quality_improvement=quality_improvement,
            cost=cost,
            evaluated_at=score.evaluated_at,
            model_used=score.model_used
        )

    def save_report(
        self,
        report: SkillReport,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save report to JSON file.

        Args:
            report: SkillReport to save
            filename: Optional filename (defaults to skill_name.json)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"{report.skill_name}.json"

        output_path = self.output_dir / filename

        # Convert to dict and save
        report_dict = report.model_dump()
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        return output_path

    def save_score_summary(
        self,
        score: SkillScore,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save just the score summary (smaller file).

        Args:
            score: SkillScore to save
            filename: Optional filename

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"{score.skill_name}_score.json"

        output_path = self.output_dir / filename

        summary = {
            "skill_name": score.skill_name,
            "skill_description": score.skill_description,
            "overall_score": round(score.overall_score, 1),
            "grade": score.grade,
            "task_pass_rate": round(score.task_pass_rate * 100, 1),
            "quality_win_rate": round(score.quality_win_rate * 100, 1),
            "estimated_cost": score.estimated_cost_per_use,
            "evaluated_at": score.evaluated_at,
            "model_used": score.model_used
        }

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        return output_path

    def generate_leaderboard(
        self,
        scores: List[SkillScore]
    ) -> List[Dict[str, Any]]:
        """
        Generate leaderboard data from multiple skill scores.

        Args:
            scores: List of SkillScore objects

        Returns:
            Sorted list of skill summaries for leaderboard
        """
        leaderboard = []

        for score in scores:
            leaderboard.append({
                "rank": 0,  # Will be set after sorting
                "skill_name": score.skill_name,
                "overall_score": round(score.overall_score, 1),
                "grade": score.grade,
                "task_pass_rate": round(score.task_pass_rate * 100, 1),
                "quality_win_rate": round(score.quality_win_rate * 100, 1),
                "estimated_cost": score.estimated_cost_per_use,
                "evaluated_at": score.evaluated_at
            })

        # Sort by overall score descending
        leaderboard.sort(key=lambda x: x["overall_score"], reverse=True)

        # Assign ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return leaderboard

    def save_leaderboard(
        self,
        scores: List[SkillScore],
        filename: str = "leaderboard.json"
    ) -> Path:
        """
        Generate and save leaderboard.

        Args:
            scores: List of SkillScore objects
            filename: Output filename

        Returns:
            Path to saved file
        """
        leaderboard = self.generate_leaderboard(scores)

        output_path = self.output_dir / filename

        data = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_skills": len(leaderboard),
            "skills": leaderboard
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return output_path


def generate_report(
    score: SkillScore,
    task_results: List[TaskResult],
    quality_comparisons: List[QualityComparison],
    tasks: Optional[List[Task]] = None,
    save: bool = True
) -> SkillReport:
    """
    Convenience function to generate and optionally save a report.

    Args:
        score: SkillScore with final metrics
        task_results: Individual task results
        quality_comparisons: Quality comparison results
        tasks: Optional task definitions
        save: Whether to save to file

    Returns:
        SkillReport
    """
    generator = ReportGenerator()
    report = generator.generate_skill_report(
        score=score,
        task_results=task_results,
        quality_comparisons=quality_comparisons,
        tasks=tasks
    )

    if save:
        path = generator.save_report(report)
        print(f"Report saved to: {path}")

    return report
