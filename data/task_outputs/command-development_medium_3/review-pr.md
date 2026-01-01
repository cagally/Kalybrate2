---
description: Quick pull request code review
model: haiku
allowed-tools: Read, Bash(git:*)
argument-hint: [pr-number]
---

Perform a quick review of pull request #$1:

1. Fetch PR details: !`gh pr view $1`

2. List changed files: !`gh pr diff $1 --name-only`

3. Rapid code review checks:
   - Basic syntax and style
   - Obvious logical errors
   - Potential security quick wins
   - Code complexity red flags

4. Summarize key findings:
   - Highlight critical issues
   - Suggest immediate improvements
   - Recommend areas for deeper review

Provide a concise report focusing on high-impact observations.
