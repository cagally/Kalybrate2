"""
Quality A/B testing - compares outputs with and without skills.
Tracks actual token usage from API and uses LLM judge to determine quality improvement.
Randomizes A/B order to avoid position bias.
"""

import os
import time
import random
from typing import List, Optional, Dict, Any

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import QualityComparison

load_dotenv()


class QualityTester:
    """Tests quality improvement when using skills vs not using skills"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-haiku-20241022",  # Haiku for cost-efficient execution
        judge_model: str = "claude-sonnet-4-20250514"  # Sonnet for quality judging
    ):
        """
        Initialize quality tester.

        Args:
            api_key: Anthropic API key
            model: Claude model for task execution
            judge_model: Claude model for judging (can be different)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.judge_model = judge_model

    def run_with_skill(
        self,
        prompt: str,
        skill_name: str,
        skill_md_content: str
    ) -> Dict[str, Any]:
        """
        Run prompt WITH skill (SKILL.md in system prompt).

        Args:
            prompt: User prompt
            skill_name: Skill name
            skill_md_content: Full SKILL.md content

        Returns:
            Dict with output, input_tokens, output_tokens
        """
        try:
            system_prompt = f"""You have access to a skill: {skill_name}

SKILL.md:
---
{skill_md_content}
---

Follow these instructions when relevant."""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            output = message.content[0].text if message.content else ""

            return {
                "output": output,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "error": None
            }

        except Exception as e:
            return {
                "output": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "error": str(e)
            }

    def run_without_skill(self, prompt: str) -> Dict[str, Any]:
        """
        Run prompt WITHOUT any skill (baseline).

        Args:
            prompt: User prompt

        Returns:
            Dict with output, input_tokens, output_tokens
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            output = message.content[0].text if message.content else ""

            return {
                "output": output,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "error": None
            }

        except Exception as e:
            return {
                "output": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "error": str(e)
            }

    def judge_comparison(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        a_is_skill: bool
    ) -> Dict[str, Any]:
        """
        Use LLM to judge which response is better.
        Randomizes position to avoid bias.

        Args:
            prompt: Original task prompt
            response_a: First response
            response_b: Second response
            a_is_skill: Whether A is the skill response

        Returns:
            Dict with winner ('with_skill', 'without_skill', 'tie') and reasoning
        """
        judge_prompt = f"""You are evaluating two AI responses to the same task.

Task: {prompt}

Response A:
---
{response_a[:2000]}
---

Response B:
---
{response_b[:2000]}
---

Which response better accomplishes the task? Consider:
- Does it complete the task correctly?
- Is the output higher quality?
- Is it more complete/thorough?
- Is it more useful to the user?

Respond with JSON only (no markdown):
{{"winner": "A" | "B" | "tie", "reasoning": "Brief explanation"}}"""

        try:
            message = self.client.messages.create(
                model=self.judge_model,
                max_tokens=256,
                temperature=0,  # Deterministic
                messages=[{"role": "user", "content": judge_prompt}]
            )

            response_text = message.content[0].text if message.content else ""

            # Parse JSON
            import json
            import re

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {"winner": "tie", "reasoning": "Could not parse judge response"}

            # Map winner back to skill/baseline based on position
            winner_raw = result.get("winner", "tie")
            if winner_raw == "A":
                winner = "with_skill" if a_is_skill else "without_skill"
            elif winner_raw == "B":
                winner = "without_skill" if a_is_skill else "with_skill"
            else:
                winner = "tie"

            return {
                "verdict": winner,
                "reasoning": result.get("reasoning", "")
            }

        except Exception as e:
            return {
                "verdict": "tie",
                "reasoning": f"Judge error: {str(e)}"
            }

    def run_quality_comparison(
        self,
        prompt: str,
        skill_name: str,
        skill_md_content: str
    ) -> QualityComparison:
        """
        Run A/B comparison for a single prompt.
        Randomizes order to avoid position bias.

        Args:
            prompt: Prompt to test
            skill_name: Skill name
            skill_md_content: Full SKILL.md content

        Returns:
            QualityComparison with results and judge verdict
        """
        print(f"  Testing prompt: {prompt[:50]}...")

        # Run with skill
        print("    Running WITH skill...")
        with_skill = self.run_with_skill(prompt, skill_name, skill_md_content)

        # Run without skill (baseline)
        print("    Running WITHOUT skill...")
        without_skill = self.run_without_skill(prompt)

        # Judge quality (randomize order to avoid position bias)
        print("    Judging...")
        if with_skill["output"] and without_skill["output"]:
            # Randomize which is A vs B
            skill_is_a = random.choice([True, False])

            if skill_is_a:
                response_a = with_skill["output"]
                response_b = without_skill["output"]
            else:
                response_a = without_skill["output"]
                response_b = with_skill["output"]

            judgment = self.judge_comparison(
                prompt=prompt,
                response_a=response_a,
                response_b=response_b,
                a_is_skill=skill_is_a
            )
            judge_verdict = judgment["verdict"]
            judge_reasoning = judgment["reasoning"]
        else:
            judge_verdict = "tie"
            judge_reasoning = "One or both outputs failed"

        print(f"    Verdict: {judge_verdict}")

        return QualityComparison(
            prompt=prompt,
            with_skill_output=with_skill["output"],  # Full response for logging
            without_skill_output=without_skill["output"],  # Full response for logging
            with_skill_input_tokens=with_skill["input_tokens"],
            with_skill_output_tokens=with_skill["output_tokens"],
            without_skill_input_tokens=without_skill["input_tokens"],
            without_skill_output_tokens=without_skill["output_tokens"],
            judge_verdict=judge_verdict,
            judge_reasoning=judge_reasoning
        )

    def run_quality_comparisons(
        self,
        prompts: List[str],
        skill_name: str,
        skill_md_content: Optional[str] = None
    ) -> List[QualityComparison]:
        """
        Run quality comparisons for multiple prompts.

        Args:
            prompts: List of prompts to test
            skill_name: Skill name
            skill_md_content: Full SKILL.md content

        Returns:
            List of QualityComparisons
        """
        if not skill_md_content:
            print("Warning: No SKILL.md content provided for quality testing")
            skill_md_content = f"Skill: {skill_name}"

        comparisons = []

        for i, prompt in enumerate(prompts):
            print(f"\nQuality test {i+1}/{len(prompts)}")

            comparison = self.run_quality_comparison(
                prompt, skill_name, skill_md_content
            )
            comparisons.append(comparison)

            # Brief pause between tests
            time.sleep(0.5)

        return comparisons

    def calculate_quality_metrics(
        self,
        comparisons: List[QualityComparison]
    ) -> Dict[str, Any]:
        """
        Calculate quality improvement metrics.

        Args:
            comparisons: List of quality comparisons

        Returns:
            Dict with metrics
        """
        if not comparisons:
            return {
                "total_comparisons": 0,
                "skill_wins": 0,
                "baseline_wins": 0,
                "ties": 0,
                "win_rate": 0.0,
                "avg_input_tokens_with_skill": 0.0,
                "avg_output_tokens_with_skill": 0.0,
                "avg_input_tokens_without_skill": 0.0,
                "avg_output_tokens_without_skill": 0.0
            }

        wins = sum(1 for c in comparisons if c.judge_verdict == "with_skill")
        losses = sum(1 for c in comparisons if c.judge_verdict == "without_skill")
        ties = sum(1 for c in comparisons if c.judge_verdict == "tie")

        # Win rate: wins / (wins + losses), ties don't count
        contested = wins + losses
        win_rate = wins / contested if contested > 0 else 0.5

        # Average tokens
        n = len(comparisons)

        return {
            "total_comparisons": n,
            "skill_wins": wins,
            "baseline_wins": losses,
            "ties": ties,
            "win_rate": win_rate,
            "avg_input_tokens_with_skill": sum(c.with_skill_input_tokens for c in comparisons) / n,
            "avg_output_tokens_with_skill": sum(c.with_skill_output_tokens for c in comparisons) / n,
            "avg_input_tokens_without_skill": sum(c.without_skill_input_tokens for c in comparisons) / n,
            "avg_output_tokens_without_skill": sum(c.without_skill_output_tokens for c in comparisons) / n
        }


def test_quality(
    skill_name: str,
    skill_md_content: str,
    prompts: List[str]
) -> Dict[str, Any]:
    """
    Quick helper function to test quality improvement.

    Args:
        skill_name: Skill to test
        skill_md_content: Full SKILL.md content
        prompts: List of prompts for A/B testing

    Returns:
        Dict with quality metrics
    """
    tester = QualityTester()
    comparisons = tester.run_quality_comparisons(prompts, skill_name, skill_md_content)
    metrics = tester.calculate_quality_metrics(comparisons)

    return metrics
