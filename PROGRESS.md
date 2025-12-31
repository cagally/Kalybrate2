# Kalybrate Development Progress

> Last updated: 2025-12-31 22:45 UTC
> Current phase: Phase 2 - First Evaluations Running
> Status: 🟢 Evaluator Working

## Project Goal

**Rate PUBLIC AI agent skills from SkillsMP.com** - NOT building our own skills.

Think "G2 for AI tools" - we discover skills, evaluate them objectively, and publish ratings.

---

## Current Status

### What Works
- Discovery: 20 skills scraped from SkillsMP, 15 with full SKILL.md content
- Evaluator: Task-based evaluation with code execution working
- First evaluation: PDF skill scored 69.4/100 (Grade D)

### What's Next
- Run evaluations on remaining 14 discovered skills
- Create benchmarks for more skill types
- Deploy website with real scores

---

## Completed

### Discovery System
- [x] SkillsMP Playwright scraper (handles JS-rendered pages)
- [x] GitHub raw URL fetcher for SKILL.md content
- [x] 20 skills discovered, 15 with full content

### Evaluator System
- [x] Task-based evaluation (binary pass/fail)
- [x] SKILL.md injection into system prompt
- [x] Python code extraction and execution
- [x] File verification (PDF, Excel, Word, PowerPoint)
- [x] Selectivity testing
- [x] Quality A/B testing with LLM judge
- [x] Scoring: `(tasks × 50%) + (selectivity × 25%) + (quality × 25%)`

### Website
- [x] React + Vite + Tailwind
- [x] Skill cards, search, filter, sort
- [x] Build verified

---

## First Evaluation Results

### PDF Skill (from anthropics/anthropic-quickstarts)

| Metric | Result |
|--------|--------|
| Task Completion | 55.6% (5/9) |
| Selectivity | 100% (5/5) |
| Quality Improvement | 66.7% (2/3) |
| **Overall Score** | **69.4/100** |
| **Grade** | **D** |

Tasks breakdown:
- Easy (3/3 PASS): Simple PDF creation
- Medium (2/3 PASS): Multi-page reports, invoices
- Hard (0/3 FAIL): Complex PDFs with charts/images

---

## Discovered Skills (15 with SKILL.md)

| Skill | Repository | Stars |
|-------|------------|-------|
| pdf | anthropics/anthropic-quickstarts | 11.1k |
| frontend-design | anthropics/anthropic-quickstarts | 11.1k |
| skill-writer | anthropics/anthropic-quickstarts | 11.1k |
| hook-development | anthropics/anthropic-quickstarts | 11.1k |
| agent-development | anthropics/anthropic-quickstarts | 11.1k |
| command-development | anthropics/anthropic-quickstarts | 11.1k |
| mcp-integration | anthropics/anthropic-quickstarts | 11.1k |
| writing-rules | anthropics/anthropic-quickstarts | 11.1k |
| docstring | pytorch/pytorch | 87.5k |
| add-uint-support | pytorch/pytorch | 87.5k |
| at-dispatch-v2 | pytorch/pytorch | 87.5k |
| typescript-write | metabase/metabase | 44.7k |
| typescript-review | metabase/metabase | 44.7k |
| clojure-write | metabase/metabase | 44.7k |
| payload | payloadcms/payload | 39.0k |

---

## Not Yet Done

### High Priority
- [ ] Create benchmarks for non-file-creating skills (code review, etc.)
- [ ] Run evaluations on all 15 discovered skills
- [ ] Fix hard task failures (missing chart/image dependencies)

### Medium Priority
- [ ] Improve code execution reliability
- [ ] Add error logging for debugging
- [ ] Deploy website publicly

### Out of Scope (for now)
- Building our own skills
- User authentication
- Skill submission system

---

## How to Run

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# List skills with benchmarks
python3 -m evaluator.main --list

# Run evaluation
python3 -m evaluator.main --skill pdf

# Build website
cd website && npm run build
```

---

## Key Architecture Decisions

1. **Evaluate PUBLIC skills only** - We rate skills from SkillsMP/GitHub, we don't create skills
2. **Task-based scoring** - Binary pass/fail on concrete tasks, not subjective quality
3. **SKILL.md in system prompt** - Include full skill content when testing
4. **Code execution** - Run Claude's generated code to verify file creation
5. **GitHub raw URLs** - Fetch SKILL.md directly, don't scrape JS-rendered pages

---

## Session History

### 2025-12-31 - Session 2
- Fixed evaluator code execution (OUTPUT_DIR handling)
- Fixed file keyword detection (added 'build', 'canvas', etc.)
- Fixed verify_file returning None for unknown types
- First successful evaluation: PDF skill = 69.4/100
- Updated PROGRESS.md

### 2024-12-30 - Session 1
- Cloned repository
- Built full MVP (evaluator, discovery, website)
- Scraped 20 skills from SkillsMP
- Fetched 15 SKILL.md files from GitHub
