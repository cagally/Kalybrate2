# Kalybrate - AI Skill Rating Platform

**G2 for AI Tools** - Objective, task-based evaluation of AI agent skills.

## Overview

Kalybrate provides transparent, reproducible ratings for AI agent skills using three key metrics:

1. **Task Completion (50%)** - Can the skill accomplish its intended tasks?
2. **Selectivity (25%)** - Does the skill only activate when appropriate?
3. **Quality Improvement (25%)** - Does the skill produce better outputs than baseline?

## Project Structure

```
Kalybrate2/
├── discovery/              # Skill discovery & fetching
│   ├── skillsmp_scraper.py
│   ├── github_fetcher.py
│   └── skill_parser.py
├── evaluator/             # Task-based evaluation engine
│   ├── models.py          # Pydantic data models
│   ├── verifiers.py       # File validation
│   ├── benchmarks.py      # Task definitions
│   ├── task_runner.py     # Task execution
│   ├── selectivity_tester.py
│   ├── quality_tester.py
│   ├── judges.py          # LLM judge
│   ├── scorer.py          # Scoring algorithm
│   └── main.py            # CLI entry point
├── website/               # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── data/
│   ├── discovered/        # Scraped skill metadata
│   ├── skills/            # SKILL.md files
│   ├── test_cases/        # Generated benchmarks
│   ├── results/           # Raw evaluation results
│   └── scores/            # Final scores (for website)
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Setup Environment

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install website dependencies
cd website
npm install
cd ..
```

### 2. Discover Skills (Optional)

```bash
# Option A: Scrape from SkillsMP
python -m discovery.skillsmp_scraper --pages 2

# Option B: Use mock data for testing
python -m discovery.skillsmp_scraper --mock

# Fetch SKILL.md files from GitHub
python -m discovery.github_fetcher --limit 20
```

### 3. Run Evaluation

```bash
# Generate test cases
python -m evaluator.main --generate-only --skill ms-office-suite

# Run evaluation for one skill
python -m evaluator.main --skill ms-office-suite

# Run all available skills
python -m evaluator.main --all
```

### 4. View Results

```bash
# Copy scores to website
cp data/scores/all_skills.json website/src/data/skills.json

# Start website
cd website
npm run dev
# Open http://localhost:5173
```

## Evaluation Methodology

### Task-Based Approach

Unlike fuzzy scoring systems, Kalybrate uses **binary pass/fail criteria** for each task:

```python
task = {
    "prompt": "Create Q4 sales report with SUM formulas",
    "success_criteria": {
        "file_created": True,      # File was created
        "file_valid": True,         # File opens without error
        "has_formula": True,        # Contains =SUM() or similar
        "min_columns": 6,           # At least 6 columns
    }
}
# PASS only if ALL criteria pass
```

### Verification

Files are actually opened and inspected:
- **Excel (.xlsx)**: Uses `openpyxl` to verify formulas, charts, row/column counts
- **Word (.docx)**: Uses `python-docx` to verify paragraphs, tables, images
- **PowerPoint (.pptx)**: Uses `python-pptx` to verify slides, charts, images
- **PDF**: Validates file integrity and structure

### Selectivity Testing

Skills should NOT activate on irrelevant prompts:

```python
# These should NOT create Excel files:
- "What's the weather today?"
- "Tell me a joke"
- "Explain quantum physics"

# Each test PASSES if NO files are created
```

### Quality A/B Testing

Same prompt tested WITH and WITHOUT skill:
- LLM judge compares outputs
- Token usage tracked
- Quality improvement rate calculated

### Scoring Formula

```python
overall_score = (
    task_pass_rate * 0.50 +          # 50% weight
    selectivity_rate * 0.25 +        # 25% weight
    quality_improvement_rate * 0.25  # 25% weight
) * 100
```

**Letter Grades:**
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: <60

## CLI Usage

### Evaluator Commands

```bash
# List available skills
python -m evaluator.main --list

# Generate test cases only (for review)
python -m evaluator.main --generate-only --skill ms-office-suite

# Evaluate single skill
python -m evaluator.main --skill pdf

# Evaluate all skills
python -m evaluator.main --all
```

### Discovery Commands

```bash
# Scrape SkillsMP
python -m discovery.skillsmp_scraper --pages 5 --output data/discovered/skills.json

# Fetch from GitHub
python -m discovery.github_fetcher --input data/discovered/skills.json --limit 50

# Parse SKILL.md files
python -m discovery.skill_parser --directory data/skills
```

## Adding New Skills

To add benchmarks for a new skill, edit `evaluator/benchmarks.py`:

```python
def get_my_skill_benchmarks() -> BenchmarkSuite:
    tasks = [
        # 3 EASY tasks
        Task(
            id="my_skill_easy_1",
            prompt="...",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".xyz",
            success_criteria={"file_created": True, "file_valid": True}
        ),
        # 3 MEDIUM tasks
        # 3 HARD tasks
    ]

    selectivity_tests = [
        # 5 negative tests
        SelectivityTest(
            id="my_skill_sel_1",
            prompt="What's 2+2?",
            description="Math question - should NOT activate"
        ),
    ]

    quality_prompts = [
        # 3-5 prompts for A/B testing
    ]

    return BenchmarkSuite(...)

# Register in BENCHMARK_REGISTRY
BENCHMARK_REGISTRY["my-skill"] = get_my_skill_benchmarks
```

## Development

### Running Tests

```bash
# Test file verification
python -c "from evaluator.verifiers import verify_xlsx_file; print(verify_xlsx_file('test.xlsx', {'file_valid': True}))"

# Test scoring
python -c "from evaluator.scorer import Scorer; s = Scorer(); print(s.calculate_overall_score(0.8, 0.9, 0.7))"
```

### Website Development

```bash
cd website
npm run dev        # Dev server
npm run build      # Production build
npm run preview    # Preview production build
```

## Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here  # Optional, for higher GitHub API limits
MAX_CONCURRENT_TESTS=3
TIMEOUT_SECONDS=60
```

### Customizing Weights

Edit `evaluator/scorer.py`:

```python
scorer = Scorer(
    task_weight=0.60,        # Emphasize task completion
    selectivity_weight=0.20,
    quality_weight=0.20
)
```

## File Formats

### Skill Score JSON

```json
{
  "skill_name": "ms-office-suite",
  "overall_score": 85.3,
  "grade": "B",
  "task_pass_rate": 0.89,
  "selectivity_rate": 0.80,
  "quality_improvement_rate": 0.83,
  "tasks_passed": 8,
  "total_tasks": 9,
  "selectivity_passed": 4,
  "total_selectivity_tests": 5,
  "execution_time": 142.7
}
```

## Roadmap

- [x] Task-based evaluation engine
- [x] File verification for Office formats
- [x] Selectivity testing
- [x] Quality A/B testing
- [x] React website with search/filter/sort
- [ ] SkillsMP scraper (real implementation)
- [ ] Support for more file types (CSV, JSON, etc.)
- [ ] Difficulty-weighted scoring
- [ ] Cost tracking per evaluation
- [ ] Public leaderboard
- [ ] API for programmatic access

## Contributing

Contributions welcome! Priority areas:

1. **Benchmarks** - Add task definitions for more skills
2. **Verifiers** - Support new file types
3. **Discovery** - Implement SkillsMP scraper
4. **Website** - Add detailed skill pages, charts

## License

MIT

## Credits

Built with:
- **Anthropic Claude** - Evaluation and judging
- **openpyxl** - Excel file verification
- **python-docx** - Word document verification
- **python-pptx** - PowerPoint verification
- **React + Vite** - Website
- **Tailwind CSS** - Styling
