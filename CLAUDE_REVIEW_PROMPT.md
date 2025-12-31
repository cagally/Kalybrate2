# Prompt for Claude Review

Copy everything below this line and paste it to Claude online:

---

## Context

I'm building **Kalybrate** - a rating platform for public AI agent skills (think "G2 for AI tools").

**Key constraint:** We evaluate and rate PUBLIC skills from SkillsMP.com and GitHub - we do NOT build our own skills.

## What's Built

1. **Discovery System**: Scrapes skills from SkillsMP.com, fetches SKILL.md files from GitHub
2. **Evaluator System**: Tests skills using task-based evaluation with binary pass/fail criteria
3. **Website**: React frontend to display skill ratings

## How Evaluation Works

1. Load a public skill's SKILL.md content
2. Include SKILL.md in system prompt when calling Claude API
3. Give Claude a task (e.g., "Create a PDF report")
4. Extract Python code from Claude's response
5. Execute the code to create files
6. Verify files meet success criteria (file exists, valid format, etc.)
7. Score: `(task_pass_rate × 50%) + (selectivity × 25%) + (quality_improvement × 25%)`

## Current Status

- 20 skills discovered from SkillsMP
- 15 skills have full SKILL.md content fetched from GitHub
- First evaluation complete: **PDF skill scored 69.4/100 (Grade D)**
  - Easy tasks: 3/3 passed
  - Medium tasks: 2/3 passed
  - Hard tasks: 0/3 passed (require charts/images we can't provide)

## The Problem

Most discovered skills are NOT file-creation skills. They're things like:
- `typescript-write` - coding conventions for Metabase
- `docstring` - PyTorch docstring format
- `hook-development` - Claude Code plugin development
- `frontend-design` - UI design patterns

Our current evaluator only works for skills that CREATE FILES (PDF, Excel, etc.). We can verify file creation. But how do we evaluate skills that:
- Give coding conventions/style guidance?
- Provide domain knowledge?
- Help with code review?

## Questions

1. **Are we on the right track?** Is task-based evaluation with file verification a good approach for rating skills?

2. **How should we evaluate non-file skills?** For skills like `typescript-write` that provide coding conventions, what would objective evaluation look like?

3. **Should we focus only on file-creation skills for MVP?** Or is there a way to evaluate knowledge/guidance skills objectively?

4. **What's the minimum viable set of benchmarks?** We have 15 skills but only 2 benchmark suites (PDF, MS Office). What's the fastest path to evaluating all 15?

5. **Any blind spots?** What are we missing or doing wrong?

## Constraints

- Must be objective/reproducible (not subjective quality judgments)
- Must work with public skills we don't control
- Budget-conscious (API calls cost money)
- Timeline: Want to launch with ratings for 15-20 skills

---

End of prompt. Please review and advise on the best path forward.
