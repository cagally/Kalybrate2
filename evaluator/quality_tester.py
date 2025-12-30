"""
Quality A/B testing - compares outputs with and without skills.
Measures token usage and uses LLM judge to determine quality improvement.
"""

import os
import time
from typing import List, Optional, Dict
from anthropic import Anthropic
from dotenv import load_dotenv

try:
    import tiktoken
except ImportError:
    tiktoken = None

from evaluator.models import QualityComparison
from evaluator.judges import QualityJudge


load_dotenv()


class QualityTester:
    """Tests quality improvement when using skills vs not using skills"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101"
    ):
        """
        Initialize quality tester.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.judge = QualityJudge(api_key=api_key)

        # Initialize tokenizer for counting tokens
        if tiktoken:
            try:
                self.encoding = tiktoken.encoding_for_model("gpt-4")
            except:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Token count (approximate if tiktoken not available)
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough approximation (1 token ~= 4 characters)
            return len(text) // 4

    def run_with_skill(self, prompt: str, skill_name: str) -> Dict[str, any]:
        """
        Run prompt WITH skill activated.

        Args:
            prompt: User prompt
            skill_name: Skill to use

        Returns:
            Dict with output and metadata
        """
        try:
            # Add skill context
            full_prompt = f"[Using skill: {skill_name}]\n\n{prompt}"

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": full_prompt}]
            )

            output = message.content[0].text if message.content else ""
            tokens = self.count_tokens(output)

            return {
                "output": output,
                "tokens": tokens,
                "error": None
            }

        except Exception as e:
            return {
                "output": "",
                "tokens": 0,
                "error": str(e)
            }

    def run_without_skill(self, prompt: str) -> Dict[str, any]:
        """
        Run prompt WITHOUT any skill.

        Args:
            prompt: User prompt

        Returns:
            Dict with output and metadata
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            output = message.content[0].text if message.content else ""
            tokens = self.count_tokens(output)

            return {
                "output": output,
                "tokens": tokens,
                "error": None
            }

        except Exception as e:
            return {
                "output": "",
                "tokens": 0,
                "error": str(e)
            }

    def run_quality_comparison(
        self,
        prompt: str,
        skill_name: str
    ) -> QualityComparison:
        """
        Run A/B comparison for a single prompt.

        Args:
            prompt: Prompt to test
            skill_name: Skill to compare

        Returns:
            QualityComparison with results and judge verdict
        """
        print(f"Running quality comparison for prompt: {prompt[:60]}...")

        # Run with skill
        print("  Testing WITH skill...")
        with_skill = self.run_with_skill(prompt, skill_name)

        # Run without skill
        print("  Testing WITHOUT skill...")
        without_skill = self.run_without_skill(prompt)

        # Judge quality
        print("  Judging quality...")
        if with_skill["output"] and without_skill["output"]:
            judgment = self.judge.judge_skill_comparison(
                prompt=prompt,
                with_skill_output=with_skill["output"],
                without_skill_output=without_skill["output"]
            )
            judge_verdict = judgment["verdict"]
            judge_reasoning = judgment["reasoning"]
        else:
            judge_verdict = "tie"
            judge_reasoning = "One or both outputs failed"

        print(f"  Verdict: {judge_verdict}")

        return QualityComparison(
            prompt=prompt,
            with_skill_output=with_skill["output"],
            without_skill_output=without_skill["output"],
            with_skill_tokens=with_skill["tokens"],
            without_skill_tokens=without_skill["tokens"],
            judge_verdict=judge_verdict,
            judge_reasoning=judge_reasoning
        )

    def run_quality_comparisons(
        self,
        prompts: List[str],
        skill_name: str
    ) -> List[QualityComparison]:
        """
        Run quality comparisons for multiple prompts.

        Args:
            prompts: List of prompts to test
            skill_name: Skill to compare

        Returns:
            List of QualityComparisons
        """
        comparisons = []

        for i, prompt in enumerate(prompts):
            print(f"\nQuality test {i+1}/{len(prompts)}")

            comparison = self.run_quality_comparison(prompt, skill_name)
            comparisons.append(comparison)

            # Brief pause between tests
            time.sleep(1)

        return comparisons

    def calculate_quality_metrics(
        self,
        comparisons: List[QualityComparison]
    ) -> Dict[str, float]:
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
                "skill_losses": 0,
                "ties": 0,
                "quality_improvement_rate": 0.0,
                "avg_tokens_with_skill": 0.0,
                "avg_tokens_without_skill": 0.0
            }

        wins = sum(1 for c in comparisons if c.judge_verdict == "with_skill")
        losses = sum(1 for c in comparisons if c.judge_verdict == "without_skill")
        ties = sum(1 for c in comparisons if c.judge_verdict == "tie")

        # Calculate improvement rate (wins / total)
        # Ties count as 0.5
        improvement_rate = (wins + (ties * 0.5)) / len(comparisons)

        # Calculate average tokens
        avg_with = sum(c.with_skill_tokens for c in comparisons) / len(comparisons)
        avg_without = sum(c.without_skill_tokens for c in comparisons) / len(comparisons)

        return {
            "total_comparisons": len(comparisons),
            "skill_wins": wins,
            "skill_losses": losses,
            "ties": ties,
            "quality_improvement_rate": improvement_rate,
            "avg_tokens_with_skill": avg_with,
            "avg_tokens_without_skill": avg_without
        }


def test_quality(skill_name: str, prompts: List[str]) -> dict:
    """
    Quick helper function to test quality improvement.

    Args:
        skill_name: Skill to test
        prompts: List of prompts for A/B testing

    Returns:
        Dict with quality metrics
    """
    tester = QualityTester()
    comparisons = tester.run_quality_comparisons(prompts, skill_name)
    metrics = tester.calculate_quality_metrics(comparisons)

    return metrics
