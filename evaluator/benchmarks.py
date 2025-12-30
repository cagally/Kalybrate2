"""
Benchmark task definitions for evaluating AI skills.
Each skill type has 9 tasks (3 easy, 3 medium, 3 hard) with explicit success criteria.
"""

from typing import Dict, List
from evaluator.models import Task, SelectivityTest, BenchmarkSuite, DifficultyLevel


def get_ms_office_suite_benchmarks() -> BenchmarkSuite:
    """Benchmarks for MS Office Suite skill (Excel, Word, PowerPoint)"""

    tasks = [
        # EASY TASKS (3)
        Task(
            id="ms_office_easy_1",
            prompt="Create a simple Excel spreadsheet with sales data for 3 products across 4 months",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".xlsx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "min_rows": 4,
                "min_columns": 4,
            }
        ),
        Task(
            id="ms_office_easy_2",
            prompt="Create a Word document with a short business report (3 paragraphs)",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".docx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "min_paragraphs": 3,
                "min_words": 100,
            }
        ),
        Task(
            id="ms_office_easy_3",
            prompt="Create a PowerPoint presentation with 3 slides about product launch",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".pptx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "min_slides": 3,
            }
        ),

        # MEDIUM TASKS (3)
        Task(
            id="ms_office_medium_1",
            prompt="Create an Excel Q4 sales report with SUM formulas calculating totals",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".xlsx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "has_formula": True,
                "min_rows": 5,
                "min_columns": 5,
            }
        ),
        Task(
            id="ms_office_medium_2",
            prompt="Create a Word document with a table showing project timeline and milestones",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".docx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "has_table": True,
                "min_paragraphs": 2,
            }
        ),
        Task(
            id="ms_office_medium_3",
            prompt="Create a PowerPoint presentation with 5 slides including at least one image",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".pptx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "min_slides": 5,
                "has_image": True,
            }
        ),

        # HARD TASKS (3)
        Task(
            id="ms_office_hard_1",
            prompt="Create a comprehensive Excel financial dashboard with formulas and a chart showing revenue trends",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".xlsx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "has_formula": True,
                "has_chart": True,
                "min_rows": 10,
                "min_columns": 6,
            }
        ),
        Task(
            id="ms_office_hard_2",
            prompt="Create a detailed Word business proposal with tables, multiple sections, and at least 500 words",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".docx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "has_table": True,
                "min_paragraphs": 8,
                "min_words": 500,
            }
        ),
        Task(
            id="ms_office_hard_3",
            prompt="Create a professional PowerPoint investor pitch deck with 10 slides, charts, and images",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".pptx",
            success_criteria={
                "file_created": True,
                "file_valid": True,
                "min_slides": 10,
                "has_chart": True,
                "has_image": True,
            }
        ),
    ]

    selectivity_tests = [
        SelectivityTest(
            id="ms_office_sel_1",
            prompt="What's the weather like today?",
            description="Weather question - should NOT create Office files"
        ),
        SelectivityTest(
            id="ms_office_sel_2",
            prompt="Tell me a joke",
            description="Entertainment request - should NOT create Office files"
        ),
        SelectivityTest(
            id="ms_office_sel_3",
            prompt="Explain quantum physics",
            description="Educational question - should NOT create Office files"
        ),
        SelectivityTest(
            id="ms_office_sel_4",
            prompt="Write some Python code",
            description="Code request - should NOT create Office files"
        ),
        SelectivityTest(
            id="ms_office_sel_5",
            prompt="Help me debug this error message",
            description="Technical support - should NOT create Office files"
        ),
    ]

    quality_prompts = [
        "Create a quarterly budget spreadsheet",
        "Make a project status report document",
        "Build a team meeting presentation",
    ]

    return BenchmarkSuite(
        skill_name="ms-office-suite",
        skill_description="Create and manipulate Microsoft Office files (Excel, Word, PowerPoint)",
        tasks=tasks,
        selectivity_tests=selectivity_tests,
        quality_prompts=quality_prompts
    )


def get_pdf_benchmarks() -> BenchmarkSuite:
    """Benchmarks for PDF creation/manipulation skill"""

    tasks = [
        # EASY TASKS
        Task(
            id="pdf_easy_1",
            prompt="Create a simple PDF document with text content",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_easy_2",
            prompt="Generate a PDF receipt",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_easy_3",
            prompt="Create a PDF letter",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),

        # MEDIUM TASKS
        Task(
            id="pdf_medium_1",
            prompt="Create a PDF report with multiple pages and sections",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_medium_2",
            prompt="Generate a PDF invoice with table layout",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_medium_3",
            prompt="Create a PDF form with fields",
            difficulty=DifficultyLevel.MEDIUM,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),

        # HARD TASKS
        Task(
            id="pdf_hard_1",
            prompt="Create a professional PDF portfolio with images and formatted text",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_hard_2",
            prompt="Generate a multi-page PDF contract with headers, footers, and page numbers",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        Task(
            id="pdf_hard_3",
            prompt="Create a comprehensive PDF annual report with charts and tables",
            difficulty=DifficultyLevel.HARD,
            expected_file_type=".pdf",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
    ]

    selectivity_tests = [
        SelectivityTest(
            id="pdf_sel_1",
            prompt="What time is it?",
            description="Time question - should NOT create PDF"
        ),
        SelectivityTest(
            id="pdf_sel_2",
            prompt="Calculate 15% of 200",
            description="Math question - should NOT create PDF"
        ),
        SelectivityTest(
            id="pdf_sel_3",
            prompt="Translate 'hello' to Spanish",
            description="Translation - should NOT create PDF"
        ),
        SelectivityTest(
            id="pdf_sel_4",
            prompt="Summarize this article: [article text]",
            description="Summarization - should NOT create PDF"
        ),
        SelectivityTest(
            id="pdf_sel_5",
            prompt="Write a haiku",
            description="Creative writing - should NOT create PDF"
        ),
    ]

    quality_prompts = [
        "Create a business proposal PDF",
        "Generate a meeting notes PDF",
        "Make a product catalog PDF",
    ]

    return BenchmarkSuite(
        skill_name="pdf",
        skill_description="Create and manipulate PDF documents",
        tasks=tasks,
        selectivity_tests=selectivity_tests,
        quality_prompts=quality_prompts
    )


# Registry of all benchmark suites
BENCHMARK_REGISTRY: Dict[str, callable] = {
    "ms-office-suite": get_ms_office_suite_benchmarks,
    "pdf": get_pdf_benchmarks,
}


def get_benchmarks(skill_name: str) -> BenchmarkSuite:
    """
    Get benchmark suite for a skill.

    Args:
        skill_name: Name of the skill

    Returns:
        BenchmarkSuite for the skill

    Raises:
        ValueError: If skill not found in registry
    """
    if skill_name not in BENCHMARK_REGISTRY:
        raise ValueError(
            f"No benchmarks found for skill '{skill_name}'. "
            f"Available: {list(BENCHMARK_REGISTRY.keys())}"
        )

    return BENCHMARK_REGISTRY[skill_name]()


def list_available_skills() -> List[str]:
    """List all skills with defined benchmarks"""
    return list(BENCHMARK_REGISTRY.keys())


def create_default_benchmarks(skill_name: str, skill_description: str = None) -> BenchmarkSuite:
    """
    Create a default benchmark suite for a skill not in the registry.
    This is a fallback for skills we haven't created custom benchmarks for yet.

    Args:
        skill_name: Name of the skill
        skill_description: Optional description

    Returns:
        A basic BenchmarkSuite with generic tasks
    """
    tasks = [
        Task(
            id=f"{skill_name}_easy_1",
            prompt=f"Use the {skill_name} skill to complete a simple task",
            difficulty=DifficultyLevel.EASY,
            success_criteria={"file_created": True}
        ),
        Task(
            id=f"{skill_name}_medium_1",
            prompt=f"Use the {skill_name} skill to complete a moderate task",
            difficulty=DifficultyLevel.MEDIUM,
            success_criteria={"file_created": True}
        ),
        Task(
            id=f"{skill_name}_hard_1",
            prompt=f"Use the {skill_name} skill to complete a complex task",
            difficulty=DifficultyLevel.HARD,
            success_criteria={"file_created": True}
        ),
    ]

    selectivity_tests = [
        SelectivityTest(
            id=f"{skill_name}_sel_1",
            prompt="What's 2+2?",
            description="Math question"
        ),
        SelectivityTest(
            id=f"{skill_name}_sel_2",
            prompt="Tell me about yourself",
            description="General conversation"
        ),
    ]

    return BenchmarkSuite(
        skill_name=skill_name,
        skill_description=skill_description or f"Generic benchmarks for {skill_name}",
        tasks=tasks,
        selectivity_tests=selectivity_tests,
        quality_prompts=[]
    )
