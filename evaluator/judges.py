"""
LLM judge for comparing quality of outputs with and without skills.
Uses Claude to determine which output is better.
"""

import os
from typing import Optional, Dict
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


class QualityJudge:
    """LLM judge for A/B quality comparisons"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929"  # Use Sonnet for cost efficiency
    ):
        """
        Initialize quality judge.

        Args:
            api_key: Anthropic API key
            model: Claude model to use for judging
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def judge_comparison(
        self,
        prompt: str,
        output_a: str,
        output_b: str,
        label_a: str = "Output A",
        label_b: str = "Output B"
    ) -> Dict[str, str]:
        """
        Judge which output is better.

        Args:
            prompt: Original user prompt
            output_a: First output to compare
            output_b: Second output to compare
            label_a: Label for output A (e.g., "With Skill")
            label_b: Label for output B (e.g., "Without Skill")

        Returns:
            Dict with 'verdict' ('a', 'b', or 'tie') and 'reasoning'
        """
        judge_prompt = f"""You are an expert judge evaluating AI assistant outputs.

Original user request:
{prompt}

---

{label_a}:
{output_a}

---

{label_b}:
{output_b}

---

Please evaluate both outputs based on:
1. Correctness - Does it properly address the request?
2. Completeness - Is the response thorough?
3. Quality - Is it well-structured and professional?
4. Usefulness - Would this be helpful to the user?

Respond in JSON format:
{{
  "verdict": "a" or "b" or "tie",
  "reasoning": "Brief explanation of your decision"
}}

If the outputs are substantially equivalent in quality, choose "tie".
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": judge_prompt}]
            )

            response_text = message.content[0].text if message.content else ""

            # Parse JSON response
            import json
            # Extract JSON from response (it might have markdown code blocks)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            result = json.loads(response_text)

            return {
                "verdict": result.get("verdict", "tie"),
                "reasoning": result.get("reasoning", "No reasoning provided")
            }

        except Exception as e:
            # If judging fails, default to tie
            return {
                "verdict": "tie",
                "reasoning": f"Error during judging: {str(e)}"
            }

    def judge_skill_comparison(
        self,
        prompt: str,
        with_skill_output: str,
        without_skill_output: str
    ) -> Dict[str, str]:
        """
        Judge quality comparison between with and without skill.

        Args:
            prompt: Original prompt
            with_skill_output: Output when using skill
            without_skill_output: Output without skill

        Returns:
            Dict with 'verdict' ('with_skill', 'without_skill', or 'tie') and 'reasoning'
        """
        result = self.judge_comparison(
            prompt=prompt,
            output_a=with_skill_output,
            output_b=without_skill_output,
            label_a="With Skill",
            label_b="Without Skill"
        )

        # Map 'a'/'b' to 'with_skill'/'without_skill'
        verdict_map = {
            "a": "with_skill",
            "b": "without_skill",
            "tie": "tie"
        }

        return {
            "verdict": verdict_map.get(result["verdict"], "tie"),
            "reasoning": result["reasoning"]
        }


def quick_judge(prompt: str, output_a: str, output_b: str) -> str:
    """
    Quick helper function to judge two outputs.

    Args:
        prompt: Original prompt
        output_a: First output
        output_b: Second output

    Returns:
        Verdict: 'a', 'b', or 'tie'
    """
    judge = QualityJudge()
    result = judge.judge_comparison(prompt, output_a, output_b)
    return result["verdict"]
