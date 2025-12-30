"""
Pydantic models for Kalybrate evaluation system.
Defines data structures for tasks, test cases, results, and scores.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(str, Enum):
    """Task difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Task(BaseModel):
    """A single evaluation task with success criteria"""
    id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="The prompt to send to the AI")
    difficulty: DifficultyLevel = Field(..., description="Task difficulty level")
    success_criteria: Dict[str, Any] = Field(
        ...,
        description="Dictionary of criteria that must ALL pass"
    )
    expected_file_type: Optional[str] = Field(
        None,
        description="Expected file extension (.xlsx, .docx, .pptx, etc.)"
    )

    class Config:
        use_enum_values = True


class SelectivityTest(BaseModel):
    """A negative test case - skill should NOT activate"""
    id: str = Field(..., description="Unique test identifier")
    prompt: str = Field(..., description="Prompt that should NOT trigger skill")
    description: str = Field(..., description="Why this should not activate skill")


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
    with_skill_tokens: int
    without_skill_tokens: int
    judge_verdict: Optional[str] = Field(
        None,
        description="'with_skill', 'without_skill', or 'tie'"
    )
    judge_reasoning: Optional[str] = None


class SkillScore(BaseModel):
    """Final score for a skill"""
    skill_name: str

    # Task completion metrics
    total_tasks: int
    tasks_passed: int
    task_pass_rate: float = Field(..., ge=0.0, le=1.0)
    tasks_by_difficulty: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Pass/fail counts by difficulty level"
    )

    # Selectivity metrics
    total_selectivity_tests: int
    selectivity_passed: int
    selectivity_rate: float = Field(..., ge=0.0, le=1.0)

    # Quality metrics
    total_quality_comparisons: int
    quality_wins: int
    quality_improvement_rate: float = Field(..., ge=0.0, le=1.0)

    # Overall score
    overall_score: float = Field(..., ge=0.0, le=100.0)
    grade: str = Field(..., description="Letter grade A-F")

    # Metadata
    avg_tokens_with_skill: Optional[float] = None
    avg_tokens_without_skill: Optional[float] = None
    execution_time: float = Field(..., description="Total evaluation time in seconds")

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


class BenchmarkSuite(BaseModel):
    """Complete benchmark suite for a skill"""
    skill_name: str
    skill_description: Optional[str] = None
    tasks: List[Task]
    selectivity_tests: List[SelectivityTest]
    quality_prompts: List[str] = Field(
        default_factory=list,
        description="Prompts for A/B quality testing"
    )

    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[Task]:
        """Get all tasks of a specific difficulty"""
        return [t for t in self.tasks if t.difficulty == difficulty]
