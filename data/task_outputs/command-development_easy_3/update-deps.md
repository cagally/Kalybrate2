---
name: update-deps
description: Analyze and suggest dependency updates
argument-hint: [optional-filter]
allowed-tools: Read, Bash(npm:*)
---

Current dependencies from package.json:
@package.json

Dependency Update Analysis:
1. Check for outdated packages: !`npm outdated --json`
2. Evaluate potential updates for each dependency

Recommendations:
$IF($1,
  Focus on updating dependencies matching "$1",
  Review all dependencies
)

Suggested Update Process:
- Review changes in latest versions
- Check compatibility
- Run tests after updating
- Recommend semantic versioning approach

Update Strategy:
- Minor version updates: Generally safe
- Major version updates: Requires careful review
- Consider using "npm update" for minor updates
- Use "npm-check-updates" for comprehensive dependency management

Safety Checks:
- Verify all tests pass after updates
- Review changelog for breaking changes
- Check CI/CD pipeline compatibility
