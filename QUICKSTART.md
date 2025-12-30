# Kalybrate Quick Start Guide

## 1. Install Dependencies (5 minutes)

```bash
# Install Python packages
pip install -r requirements.txt

# Set up API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# Install website dependencies
cd website
npm install
cd ..
```

## 2. Test the System (2 minutes)

```bash
# List available skills
python3 -m evaluator.main --list

# Generate test cases for review
python3 -m evaluator.main --generate-only --skill ms-office-suite

# Check generated test cases
cat data/test_cases/ms-office-suite.json
```

## 3. Run First Evaluation (10-15 minutes)

```bash
# Evaluate one skill
python3 -m evaluator.main --skill ms-office-suite

# Check results
cat data/scores/ms-office-suite.json
cat data/results/ms-office-suite/task_results.json
```

## 4. View in Website (1 minute)

```bash
# Copy scores
cp data/scores/ms-office-suite.json website/src/data/skills.json

# Start dev server
cd website
npm run dev
```

Open http://localhost:5173

## 5. Evaluate More Skills (optional)

```bash
# Run all predefined skills
python3 -m evaluator.main --all

# Copy all scores
cp data/scores/all_skills.json website/src/data/skills.json
```

## Understanding the Output

### Task Results (Pass/Fail)
Each task has explicit success criteria. ALL must pass:
- `file_created`: True if file exists
- `file_valid`: True if file opens without error
- `has_formula`: True if Excel contains formulas
- `min_columns`: True if enough columns present

### Selectivity Results (True/False)
Tests PASS if skill correctly does NOT activate:
- True = No files created (correct behavior)
- False = Files created (incorrect activation)

### Quality Comparison (with_skill/without_skill/tie)
LLM judge compares outputs:
- `with_skill` = Skill output is better
- `without_skill` = Baseline output is better
- `tie` = Both roughly equivalent

### Final Score (0-100)
```
Overall = (task_pass_rate × 0.50) +
          (selectivity_rate × 0.25) +
          (quality_improvement_rate × 0.25)
```

Letter grade: A (90+), B (80-89), C (70-79), D (60-69), F (<60)

## Adding Your Own Skill Benchmarks

Edit `evaluator/benchmarks.py`:

```python
def get_my_skill_benchmarks() -> BenchmarkSuite:
    tasks = [
        # 3 EASY tasks
        Task(
            id="my_skill_easy_1",
            prompt="Simple task description",
            difficulty=DifficultyLevel.EASY,
            expected_file_type=".txt",
            success_criteria={
                "file_created": True,
                "file_valid": True,
            }
        ),
        # ... 3 MEDIUM, 3 HARD
    ]

    selectivity_tests = [
        # 5 tests that should NOT activate skill
        SelectivityTest(
            id="my_skill_sel_1",
            prompt="What's the weather?",
            description="Irrelevant question"
        ),
        # ... 4 more
    ]

    quality_prompts = [
        "Prompt for A/B testing",
        "Another prompt",
        "Third prompt",
    ]

    return BenchmarkSuite(
        skill_name="my-skill",
        skill_description="What my skill does",
        tasks=tasks,
        selectivity_tests=selectivity_tests,
        quality_prompts=quality_prompts
    )

# Register it
BENCHMARK_REGISTRY["my-skill"] = get_my_skill_benchmarks
```

Then run:
```bash
python3 -m evaluator.main --skill my-skill
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install -r requirements.txt
```

### "ANTHROPIC_API_KEY not set"
```bash
cp .env.example .env
# Edit .env and add your API key
```

### Website won't build
```bash
cd website
npm install
npm run build
```

### No skills found
```bash
python3 -m evaluator.main --list
# Should show: ms-office-suite, pdf
```

## Cost Estimates

Per skill evaluation (9 tasks + 5 selectivity + 3 quality):
- Task tests: ~15,000 tokens
- Selectivity tests: ~5,000 tokens
- Quality tests: ~10,000 tokens
- Judge calls: ~3,000 tokens
- **Total: ~33,000 tokens ≈ $0.30-0.50 per skill**

(Estimates using Claude Opus; use Sonnet for cheaper evaluations)

## Next Steps

1. Run evaluations on your skills
2. Add more benchmark definitions
3. Customize scoring weights
4. Deploy website publicly
5. Build skill leaderboard
