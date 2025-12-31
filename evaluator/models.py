"""
Pydantic models for Kalybrate evaluation system.
Defines data structures for tasks, test cases, results, and scores.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class DifficultyLevel(str, Enum):
    """Task difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class OutputType(str, Enum):
    """Expected output types from tasks"""
    FILE = "file"
    CODE = "code"
    TEXT = "text"


class Task(BaseModel):
    """A single evaluation task with success criteria"""
    id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="The prompt to send to the AI")
    difficulty: DifficultyLevel = Field(..., description="Task difficulty level")
    success_criteria: Dict[str, Any] = Field(
        ...,
        description="Dictionary of criteria that must ALL pass"
    )
    expected_output_type: OutputType = Field(
        default=OutputType.FILE,
        description="What type of output to expect"
    )
    expected_file_type: Optional[str] = Field(
        None,
        description="Expected file extension (.xlsx, .docx, .pdf, etc.)"
    )
    tests_claim: Optional[str] = Field(
        None,
        description="Which skill claim this task tests"
    )

    class Config:
        use_enum_values = True


class SelectivityTest(BaseModel):
    """A negative test case - skill should NOT activate"""
    id: str = Field(..., description="Unique test identifier")
    prompt: str = Field(..., description="Prompt that should NOT trigger skill")
    description: str = Field(..., description="Why this should not activate skill")


class TokenUsage(BaseModel):
    """Token usage for an API call"""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class TaskResult(BaseModel):
    """Result of running a single task"""
    task_id: str
    passed: bool
    criteria_results: Dict[str, bool] = Field(
        ...,
        description="Pass/fail for each criterion"
    )
    error: Optional[str] = None
    execution_time: float = Field(..., description="Time in seconds")
    files_created: List[str] = Field(
        default_factory=list,
        description="Paths to files created"
    )
    # Token tracking
    input_tokens: int = 0
    output_tokens: int = 0
    # Full response for logging
    response_text: str = Field(default="", description="Full model response")


class SelectivityResult(BaseModel):
    """Result of a selectivity test"""
    test_id: str
    passed: bool  # True if skill correctly did NOT activate
    files_created: List[str] = Field(
        default_factory=list,
        description="Files created (should be empty for pass)"
    )
    explanation: Optional[str] = None


class QualityComparison(BaseModel):
    """A/B comparison between with and without skill"""
    prompt: str
    with_skill_output: str
    without_skill_output: str
    # Token tracking for both runs
    with_skill_input_tokens: int = 0
    with_skill_output_tokens: int = 0
    without_skill_input_tokens: int = 0
    without_skill_output_tokens: int = 0
    # Judge result
    judge_verdict: Optional[str] = Field(
        None,
        description="'with_skill', 'without_skill', or 'tie'"
    )
    judge_reasoning: Optional[str] = None

    # Legacy fields for compatibility
    @property
    def with_skill_tokens(self) -> int:
        return self.with_skill_input_tokens + self.with_skill_output_tokens

    @property
    def without_skill_tokens(self) -> int:
        return self.without_skill_input_tokens + self.without_skill_output_tokens


class SkillScore(BaseModel):
    """Final score for a skill"""
    skill_name: str
    skill_description: Optional[str] = None

    # Task completion metrics (60% weight)
    total_tasks: int
    tasks_passed: int
    task_pass_rate: float = Field(..., ge=0.0, le=1.0)
    tasks_by_difficulty: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Pass/fail counts by difficulty level"
    )

    # Quality improvement metrics (40% weight)
    total_quality_comparisons: int
    quality_wins: int  # skill_better count
    quality_losses: int = 0  # baseline_better count
    quality_ties: int = 0
    quality_win_rate: Optional[float] = Field(default=None, description="None if not tested")

    # Overall score
    overall_score: float = Field(..., ge=0.0, le=100.0)
    grade: str = Field(..., description="Letter grade A-F, with * if incomplete")

    # Cost/Token metrics
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    avg_total_tokens: float = 0.0
    estimated_cost_per_use: str = "$0.00"

    # Metadata
    execution_time: float = Field(..., description="Total evaluation time in seconds")
    evaluated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp of evaluation"
    )
    model_used: str = "claude-sonnet-4-20250514"

    # Legacy compatibility
    @property
    def selectivity_rate(self) -> float:
        return 1.0  # No longer used

    @property
    def total_selectivity_tests(self) -> int:
        return 0

    @property
    def selectivity_passed(self) -> int:
        return 0

    @property
    def quality_improvement_rate(self) -> Optional[float]:
        return self.quality_win_rate

    def calculate_grade(self) -> str:
        """Calculate letter grade from overall score"""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


class GeneratedBenchmark(BaseModel):
    """Output from test_generator - auto-generated benchmark suite"""
    skill_name: str
    skill_claims: List[str] = Field(
        ...,
        description="What the skill claims to do (extracted from SKILL.md)"
    )
    tasks: List[Task]
    quality_prompts: List[str] = Field(
        default_factory=list,
        description="Prompts for A/B quality testing"
    )
    missing_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria types that were needed but don't exist"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class BenchmarkSuite(BaseModel):
    """Complete benchmark suite for a skill"""
    skill_name: str
    skill_description: Optional[str] = None
    skill_claims: List[str] = Field(
        default_factory=list,
        description="What the skill claims to do"
    )
    tasks: List[Task]
    selectivity_tests: List[SelectivityTest] = Field(
        default_factory=list,
        description="Deprecated - no longer used"
    )
    quality_prompts: List[str] = Field(
        default_factory=list,
        description="Prompts for A/B quality testing"
    )

    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[Task]:
        """Get all tasks of a specific difficulty"""
        return [t for t in self.tasks if t.difficulty == difficulty]


class SkillReport(BaseModel):
    """Full evaluation report for website display"""
    skill_name: str
    skill_description: Optional[str] = None
    overall_score: float
    grade: str

    task_completion: Dict[str, Any] = Field(
        ...,
        description="Task completion details"
    )
    quality_improvement: Dict[str, Any] = Field(
        ...,
        description="Quality comparison details"
    )
    cost: Dict[str, Any] = Field(
        ...,
        description="Token usage and cost estimates"
    )

    evaluated_at: str
    model_used: str
