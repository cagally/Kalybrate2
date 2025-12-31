"""
Main CLI for Kalybrate evaluator.
Orchestrates the full evaluation pipeline:
1. Load/generate benchmarks from SKILL.md
2. Run task completion tests
3. Run quality A/B tests
4. Calculate scores (60% task + 40% quality)
5. Generate reports
"""

import argparse
import json
import time
from pathlib import Path
from typing import Optional, List

from evaluator.test_generator import TestGenerator
from evaluator.task_runner import TaskRunner
from evaluator.quality_tester import QualityTester
from evaluator.scorer import Scorer
from evaluator.report import ReportGenerator
from evaluator.data_logger import DataLogger
from evaluator.models import BenchmarkSuite, Task, SkillScore


def load_skill_md_content(skill_name: str) -> Optional[str]:
    """
    Load SKILL.md content from discovered skills.

    Args:
        skill_name: Name of the skill

    Returns:
        SKILL.md content or None if not found
    """
    # Try discovered skills directory
    skill_dirs = [
        Path(f"data/discovered/skills/{skill_name}"),
        Path(f"data/skills/{skill_name}"),
    ]

    for skill_dir in skill_dirs:
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            return skill_md_path.read_text()

    # Try skills.json
    skills_json = Path("data/discovered/skills.json")
    if skills_json.exists():
        with open(skills_json) as f:
            data = json.load(f)
            for skill in data.get('skills', []):
                name = skill.get('name', '').replace('.md', '')
                if name == skill_name and skill.get('skill_md_content'):
                    return skill['skill_md_content']

    return None


def load_or_generate_benchmarks(
    skill_name: str,
    skill_md_content: Optional[str],
    force_generate: bool = False
) -> BenchmarkSuite:
    """
    Load existing benchmarks or generate new ones from SKILL.md.

    Args:
        skill_name: Name of the skill
        skill_md_content: SKILL.md content
        force_generate: Force regeneration even if cached

    Returns:
        BenchmarkSuite ready for evaluation
    """
    cache_path = Path(f"data/test_cases/{skill_name}.json")

    # Try to load cached benchmarks
    if not force_generate and cache_path.exists():
        print(f"  Loading cached benchmarks from: {cache_path}")
        with open(cache_path) as f:
            data = json.load(f)

        tasks = []
        for task_data in data.get("tasks", []):
            tasks.append(Task(**task_data))

        return BenchmarkSuite(
            skill_name=data.get("skill_name", skill_name),
            skill_claims=data.get("skill_claims", []),
            tasks=tasks,
            quality_prompts=data.get("quality_prompts", [])
        )

    # Generate new benchmarks from SKILL.md
    if not skill_md_content:
        print("  Warning: No SKILL.md content available for benchmark generation")
        # Return minimal benchmarks
        return BenchmarkSuite(
            skill_name=skill_name,
            skill_claims=[],
            tasks=[],
            quality_prompts=[]
        )

    print("  Generating benchmarks from SKILL.md...")
    generator = TestGenerator()
    benchmark = generator.generate_benchmarks(
        skill_name=skill_name,
        skill_md_content=skill_md_content,
        save_to_file=True
    )

    return generator.to_benchmark_suite(benchmark)


def list_discovered_skills() -> List[str]:
    """List all discovered skills with SKILL.md content"""
    skills = []

    # Check skills.json
    skills_json = Path("data/discovered/skills.json")
    if skills_json.exists():
        with open(skills_json) as f:
            data = json.load(f)
            for skill in data.get('skills', []):
                name = skill.get('name', '').replace('.md', '')
                if skill.get('skill_md_content'):
                    skills.append(name)

    # Check skills directories
    skills_dir = Path("data/discovered/skills")
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                if (skill_dir / "SKILL.md").exists():
                    if skill_dir.name not in skills:
                        skills.append(skill_dir.name)

    return sorted(skills)


def list_evaluated_skills() -> List[str]:
    """List all skills with existing benchmarks"""
    skills = []
    benchmarks_dir = Path("data/test_cases")
    if benchmarks_dir.exists():
        for json_file in benchmarks_dir.glob("*.json"):
            skills.append(json_file.stem)
    return sorted(skills)


def run_evaluation(
    skill_name: str,
    save_results: bool = True,
    force_generate: bool = False,
    skip_quality: bool = False
) -> SkillScore:
    """
    Run full evaluation for a skill.

    Args:
        skill_name: Name of the skill to evaluate
        save_results: Whether to save results to files
        force_generate: Force regeneration of benchmarks
        skip_quality: Skip quality A/B tests (faster)

    Returns:
        SkillScore with final metrics
    """
    print(f"\n{'='*60}")
    print(f"EVALUATING SKILL: {skill_name}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # Initialize data logger
    data_logger = DataLogger()

    # Load SKILL.md content
    print("Loading SKILL.md...")
    skill_md_content = load_skill_md_content(skill_name)
    if skill_md_content:
        print(f"  Loaded: {len(skill_md_content):,} chars")
        # Save SKILL.md copy
        if save_results:
            data_logger.save_skill_md(skill_name, skill_md_content)
    else:
        print("  Warning: No SKILL.md content found")

    # Load or generate benchmarks
    print("\nLoading benchmarks...")
    benchmarks = load_or_generate_benchmarks(
        skill_name=skill_name,
        skill_md_content=skill_md_content,
        force_generate=force_generate
    )

    if not benchmarks.tasks:
        print("  Error: No tasks in benchmark suite")
        # Return empty score
        return SkillScore(
            skill_name=skill_name,
            total_tasks=0,
            tasks_passed=0,
            task_pass_rate=0.0,
            total_quality_comparisons=0,
            quality_wins=0,
            quality_win_rate=None,
            overall_score=0.0,
            grade="F*",
            execution_time=time.time() - start_time
        )

    print(f"  Tasks: {len(benchmarks.tasks)}")
    print(f"  Quality prompts: {len(benchmarks.quality_prompts)}")
    print(f"  Skill claims: {len(benchmarks.skill_claims)}")

    # Save generated tests
    if save_results:
        data_logger.save_generated_tests(
            skill_name=skill_name,
            skill_claims=benchmarks.skill_claims,
            tasks=[t.model_dump() for t in benchmarks.tasks],
            quality_prompts=benchmarks.quality_prompts
        )

    # Initialize components
    task_runner = TaskRunner()
    quality_tester = QualityTester()
    scorer = Scorer()
    reporter = ReportGenerator()

    # Phase 1: Task Completion Tests
    print(f"\n{'='*60}")
    print("PHASE 1: Task Completion Tests")
    print(f"{'='*60}\n")

    task_results = task_runner.run_tasks(
        tasks=benchmarks.tasks,
        skill_name=skill_name,
        skill_md_content=skill_md_content,
        save_output=save_results
    )

    # Save individual task results
    if save_results:
        task_map = {t.id: t for t in benchmarks.tasks}
        for result in task_results:
            task = task_map.get(result.task_id)
            data_logger.save_task_result(
                skill_name=skill_name,
                task_id=result.task_id,
                prompt=task.prompt if task else "",
                difficulty=task.difficulty if task else "unknown",
                model=task_runner.model,
                response=result.response_text,
                criteria_results=result.criteria_results,
                passed=result.passed,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                execution_time=result.execution_time,
                error=result.error
            )

    passed = sum(1 for r in task_results if r.passed)
    total_task_tokens = sum(r.input_tokens + r.output_tokens for r in task_results)
    print(f"\nTask Results: {passed}/{len(task_results)} passed")
    print(f"Total tokens: {total_task_tokens:,}")

    # Phase 2: Quality A/B Tests
    print(f"\n{'='*60}")
    print("PHASE 2: Quality A/B Tests")
    print(f"{'='*60}\n")

    quality_comparisons = []
    if not skip_quality and benchmarks.quality_prompts and skill_md_content:
        quality_comparisons = quality_tester.run_quality_comparisons(
            prompts=benchmarks.quality_prompts,
            skill_name=skill_name,
            skill_md_content=skill_md_content
        )

        # Save individual quality comparisons
        if save_results:
            for i, comp in enumerate(quality_comparisons):
                data_logger.save_quality_comparison(
                    skill_name=skill_name,
                    comparison_index=i,
                    prompt=comp.prompt,
                    baseline_response=comp.without_skill_output,
                    baseline_input_tokens=comp.without_skill_input_tokens,
                    baseline_output_tokens=comp.without_skill_output_tokens,
                    skill_response=comp.with_skill_output,
                    skill_input_tokens=comp.with_skill_input_tokens,
                    skill_output_tokens=comp.with_skill_output_tokens,
                    judge_verdict=comp.judge_verdict or "unknown",
                    judge_reasoning=comp.judge_reasoning or "",
                    judge_model=quality_tester.judge_model
                )

        wins = sum(1 for c in quality_comparisons if c.judge_verdict == "with_skill")
        losses = sum(1 for c in quality_comparisons if c.judge_verdict == "without_skill")
        ties = sum(1 for c in quality_comparisons if c.judge_verdict == "tie")
        print(f"\nQuality Results: {wins} wins, {losses} losses, {ties} ties")
    else:
        if skip_quality:
            print("  Skipping quality tests (--skip-quality flag)")
        elif not benchmarks.quality_prompts:
            print("  No quality prompts defined. Skipping.")
        else:
            print("  No SKILL.md content. Skipping quality tests.")

    # Phase 3: Scoring
    print(f"\n{'='*60}")
    print("PHASE 3: Scoring")
    print(f"{'='*60}\n")

    execution_time = time.time() - start_time

    skill_score = scorer.create_skill_score(
        skill_name=skill_name,
        task_results=task_results,
        quality_comparisons=quality_comparisons,
        execution_time=execution_time,
        tasks=benchmarks.tasks,
        skill_description=benchmarks.skill_description
    )

    # Display results
    print(f"\n{'='*60}")
    print("FINAL SCORE")
    print(f"{'='*60}\n")
    print(f"Skill: {skill_score.skill_name}")
    print(f"Grade: {skill_score.grade}")
    print(f"Overall Score: {skill_score.overall_score:.1f}/100")
    print()
    print(f"Task Completion (60%): {skill_score.task_pass_rate*100:.1f}% ({skill_score.tasks_passed}/{skill_score.total_tasks})")
    print(f"  By difficulty: {skill_score.tasks_by_difficulty}")
    print()
    quality_rate = skill_score.quality_win_rate * 100 if skill_score.quality_win_rate is not None else "N/A"
    print(f"Quality Improvement (40%): {quality_rate}{'%' if isinstance(quality_rate, float) else ''}")
    print(f"  Wins: {skill_score.quality_wins}, Losses: {skill_score.quality_losses}, Ties: {skill_score.quality_ties}")
    print()
    print(f"Cost Estimate: {skill_score.estimated_cost_per_use}/use")
    print(f"Avg Tokens: {skill_score.avg_total_tokens:.0f} (in: {skill_score.avg_input_tokens:.0f}, out: {skill_score.avg_output_tokens:.0f})")
    print(f"Execution Time: {skill_score.execution_time:.1f}s")

    # Save results
    if save_results:
        # Save summary and update leaderboard
        summary = data_logger.save_summary(
            skill_name=skill_name,
            overall_score=skill_score.overall_score,
            grade=skill_score.grade,
            tasks_passed=skill_score.tasks_passed,
            tasks_total=skill_score.total_tasks,
            task_pass_rate=skill_score.task_pass_rate,
            quality_wins=skill_score.quality_wins,
            quality_losses=skill_score.quality_losses,
            quality_ties=skill_score.quality_ties,
            quality_win_rate=skill_score.quality_win_rate,
            avg_tokens=skill_score.avg_total_tokens,
            estimated_cost=skill_score.estimated_cost_per_use,
            task_model=task_runner.model,
            judge_model=quality_tester.judge_model,
            execution_time=execution_time
        )

        # Update leaderboard after each skill
        leaderboard = data_logger.update_leaderboard(summary)
        print(f"\nLeaderboard updated: {leaderboard['total_skills']} skills ranked")

        # Also save to old locations for compatibility
        results_dir = Path("data/results") / skill_name
        results_dir.mkdir(parents=True, exist_ok=True)

        # Generate and save report
        report = reporter.generate_skill_report(
            score=skill_score,
            task_results=task_results,
            quality_comparisons=quality_comparisons,
            tasks=benchmarks.tasks
        )
        report_path = reporter.save_report(report)

        print(f"\nData saved to: data/evaluations/{skill_name}/")
        print(f"Report saved to: {report_path}")

    return skill_score


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Kalybrate - AI Skill Evaluation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List discovered skills
  python -m evaluator.main --list

  # Evaluate a specific skill
  python -m evaluator.main --skill pdf

  # Regenerate benchmarks for a skill
  python -m evaluator.main --skill pdf --regenerate

  # Generate benchmarks only (no evaluation)
  python -m evaluator.main --skill pdf --generate-only

  # Evaluate all skills
  python -m evaluator.main --all
        """
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all discovered skills"
    )

    parser.add_argument(
        "--skill",
        type=str,
        help="Evaluate a specific skill"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all discovered skills"
    )

    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate benchmarks, don't run evaluation"
    )

    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Force regeneration of benchmarks from SKILL.md"
    )

    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip quality A/B tests (faster evaluation)"
    )

    args = parser.parse_args()

    # List available skills
    if args.list:
        print("\nDiscovered skills with SKILL.md:")
        discovered = list_discovered_skills()
        for skill in discovered:
            print(f"  - {skill}")

        print("\nSkills with cached benchmarks:")
        evaluated = list_evaluated_skills()
        for skill in evaluated:
            print(f"  - {skill}")
        return

    # Generate benchmarks only
    if args.generate_only:
        if args.skill:
            skill_md = load_skill_md_content(args.skill)
            if skill_md:
                generator = TestGenerator()
                generator.generate_benchmarks(args.skill, skill_md)
            else:
                print(f"Error: No SKILL.md found for '{args.skill}'")
        elif args.all:
            for skill in list_discovered_skills():
                print(f"\nGenerating benchmarks for: {skill}")
                skill_md = load_skill_md_content(skill)
                if skill_md:
                    generator = TestGenerator()
                    generator.generate_benchmarks(skill, skill_md)
                else:
                    print(f"  Skipping: No SKILL.md content")
        else:
            print("Error: Specify --skill or --all with --generate-only")
        return

    # Run evaluation
    if args.skill:
        run_evaluation(
            args.skill,
            force_generate=args.regenerate,
            skip_quality=args.skip_quality
        )
    elif args.all:
        scores = []
        skills = list_discovered_skills()

        if not skills:
            print("No skills found. Run discovery first or check data/discovered/")
            return

        for skill in skills:
            try:
                score = run_evaluation(
                    skill,
                    force_generate=args.regenerate,
                    skip_quality=args.skip_quality
                )
                scores.append(score)
            except Exception as e:
                print(f"\nError evaluating {skill}: {e}")
                continue

        # Generate and save leaderboard
        if scores:
            reporter = ReportGenerator()
            leaderboard_path = reporter.save_leaderboard(scores)
            print(f"\n\nLeaderboard saved to: {leaderboard_path}")

            # Display leaderboard
            print("\n" + "="*60)
            print("LEADERBOARD")
            print("="*60 + "\n")
            print(f"{'Rank':<6}{'Skill':<25}{'Score':<10}{'Grade':<8}")
            print("-"*50)
            for i, score in enumerate(sorted(scores, key=lambda s: s.overall_score, reverse=True)):
                print(f"{i+1:<6}{score.skill_name:<25}{score.overall_score:<10.1f}{score.grade:<8}")
    else:
        print("Error: Specify --skill or --all to run evaluation")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
