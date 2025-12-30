"""
Main CLI for Kalybrate evaluator.
Orchestrates the full evaluation pipeline.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Optional

from evaluator.benchmarks import get_benchmarks, list_available_skills, create_default_benchmarks
from evaluator.task_runner import TaskRunner
from evaluator.selectivity_tester import SelectivityTester
from evaluator.quality_tester import QualityTester
from evaluator.scorer import Scorer


def generate_test_cases(skill_name: str, output_dir: str = "data/test_cases"):
    """
    Generate and save test cases for a skill.

    Args:
        skill_name: Name of the skill
        output_dir: Directory to save test cases
    """
    print(f"\nGenerating test cases for: {skill_name}")

    try:
        benchmarks = get_benchmarks(skill_name)
    except ValueError as e:
        print(f"  No predefined benchmarks found. Using default template.")
        benchmarks = create_default_benchmarks(skill_name)

    output_path = Path(output_dir) / f"{skill_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to dict for JSON serialization
    data = {
        "skill_name": benchmarks.skill_name,
        "skill_description": benchmarks.skill_description,
        "tasks": [task.model_dump() for task in benchmarks.tasks],
        "selectivity_tests": [test.model_dump() for test in benchmarks.selectivity_tests],
        "quality_prompts": benchmarks.quality_prompts
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  Saved test cases to: {output_path}")
    print(f"  Tasks: {len(benchmarks.tasks)}")
    print(f"  Selectivity tests: {len(benchmarks.selectivity_tests)}")
    print(f"  Quality prompts: {len(benchmarks.quality_prompts)}")


def run_evaluation(skill_name: str, save_results: bool = True):
    """
    Run full evaluation for a skill.

    Args:
        skill_name: Name of the skill to evaluate
        save_results: Whether to save results to files
    """
    print(f"\n{'='*60}")
    print(f"EVALUATING SKILL: {skill_name}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # Load benchmarks
    print("Loading benchmarks...")
    try:
        benchmarks = get_benchmarks(skill_name)
    except ValueError:
        print(f"  No benchmarks found for '{skill_name}'. Using defaults.")
        benchmarks = create_default_benchmarks(skill_name)

    # Initialize components
    task_runner = TaskRunner()
    selectivity_tester = SelectivityTester()
    quality_tester = QualityTester()
    scorer = Scorer()

    # 1. Run task tests
    print(f"\n{'='*60}")
    print("PHASE 1: Task Completion Tests")
    print(f"{'='*60}\n")

    task_results = task_runner.run_tasks(
        tasks=benchmarks.tasks,
        skill_name=skill_name,
        save_output=save_results
    )

    passed = sum(1 for r in task_results if r.passed)
    print(f"\nTask Results: {passed}/{len(task_results)} passed")

    # 2. Run selectivity tests
    print(f"\n{'='*60}")
    print("PHASE 2: Selectivity Tests")
    print(f"{'='*60}\n")

    # Determine expected file extensions from tasks
    expected_extensions = list(set(
        task.expected_file_type
        for task in benchmarks.tasks
        if task.expected_file_type
    ))

    selectivity_results = selectivity_tester.run_selectivity_tests(
        tests=benchmarks.selectivity_tests,
        skill_name=skill_name,
        expected_file_extensions=expected_extensions or None
    )

    sel_passed = sum(1 for r in selectivity_results if r.passed)
    print(f"\nSelectivity Results: {sel_passed}/{len(selectivity_results)} passed")

    # 3. Run quality comparisons
    print(f"\n{'='*60}")
    print("PHASE 3: Quality A/B Tests")
    print(f"{'='*60}\n")

    quality_comparisons = []
    if benchmarks.quality_prompts:
        quality_comparisons = quality_tester.run_quality_comparisons(
            prompts=benchmarks.quality_prompts,
            skill_name=skill_name
        )

        wins = sum(1 for c in quality_comparisons if c.judge_verdict == "with_skill")
        print(f"\nQuality Results: {wins}/{len(quality_comparisons)} wins for skill")
    else:
        print("  No quality prompts defined. Skipping quality tests.")

    # 4. Calculate scores
    print(f"\n{'='*60}")
    print("PHASE 4: Scoring")
    print(f"{'='*60}\n")

    execution_time = time.time() - start_time

    skill_score = scorer.create_skill_score(
        skill_name=skill_name,
        task_results=task_results,
        selectivity_results=selectivity_results,
        quality_comparisons=quality_comparisons,
        execution_time=execution_time
    )

    # Display results
    print(f"\n{'='*60}")
    print("FINAL SCORE")
    print(f"{'='*60}\n")
    print(f"Skill: {skill_score.skill_name}")
    print(f"Grade: {skill_score.grade}")
    print(f"Overall Score: {skill_score.overall_score:.1f}/100")
    print()
    print(f"Task Completion: {skill_score.task_pass_rate*100:.1f}% ({skill_score.tasks_passed}/{skill_score.total_tasks})")
    print(f"Selectivity: {skill_score.selectivity_rate*100:.1f}% ({skill_score.selectivity_passed}/{skill_score.total_selectivity_tests})")
    print(f"Quality Improvement: {skill_score.quality_improvement_rate*100:.1f}% ({skill_score.quality_wins}/{skill_score.total_quality_comparisons})")
    print()
    print(f"Execution Time: {skill_score.execution_time:.1f}s")

    # Save results
    if save_results:
        # Save detailed results
        results_dir = Path("data/results") / skill_name
        results_dir.mkdir(parents=True, exist_ok=True)

        with open(results_dir / "task_results.json", 'w') as f:
            json.dump([r.model_dump() for r in task_results], f, indent=2)

        with open(results_dir / "selectivity_results.json", 'w') as f:
            json.dump([r.model_dump() for r in selectivity_results], f, indent=2)

        if quality_comparisons:
            with open(results_dir / "quality_comparisons.json", 'w') as f:
                json.dump([c.model_dump() for c in quality_comparisons], f, indent=2)

        # Save score
        scores_dir = Path("data/scores")
        scores_dir.mkdir(parents=True, exist_ok=True)

        with open(scores_dir / f"{skill_name}.json", 'w') as f:
            json.dump(skill_score.model_dump(), f, indent=2)

        print(f"\nResults saved to: data/results/{skill_name}/")
        print(f"Score saved to: data/scores/{skill_name}.json")

    return skill_score


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Kalybrate - AI Skill Evaluation Platform"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available skills with benchmarks"
    )

    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only generate test cases, don't run evaluation"
    )

    parser.add_argument(
        "--skill",
        type=str,
        help="Evaluate a specific skill"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all available skills"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/test_cases",
        help="Directory for test case output (default: data/test_cases)"
    )

    args = parser.parse_args()

    # List available skills
    if args.list:
        print("\nAvailable skills with predefined benchmarks:")
        for skill in list_available_skills():
            print(f"  - {skill}")
        return

    # Generate test cases only
    if args.generate_only:
        if args.skill:
            generate_test_cases(args.skill, args.output_dir)
        elif args.all:
            for skill in list_available_skills():
                generate_test_cases(skill, args.output_dir)
        else:
            print("Error: Specify --skill or --all with --generate-only")
        return

    # Run evaluation
    if args.skill:
        run_evaluation(args.skill)
    elif args.all:
        scores = []
        for skill in list_available_skills():
            score = run_evaluation(skill)
            scores.append(score)

        # Save combined scores
        scores_path = Path("data/scores/all_skills.json")
        scores_path.parent.mkdir(parents=True, exist_ok=True)

        with open(scores_path, 'w') as f:
            json.dump([s.model_dump() for s in scores], f, indent=2)

        print(f"\n\nAll scores saved to: {scores_path}")
    else:
        print("Error: Specify --skill or --all to run evaluation")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
