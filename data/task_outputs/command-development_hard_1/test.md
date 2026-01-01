---
name: Comprehensive Test Runner
description: Run tests with advanced validation and reporting
argument-hint: [test-type] [target-files] [coverage-threshold]
allowed-tools: Bash(git:*), Bash(npm:*), Read
---

# Validate and prepare test environment

# 1. Git Status Check
Git Repository Status: !`git status --porcelain`
$IF(git status --porcelain | grep -q .,
    Warn: Uncommitted changes detected. Recommend committing before testing.,
    Proceed with clean repository.
)

# 2. Environment Checks
Node Version: !`node --version`
NPM Version: !`npm --version`

$IF(! command -v npm &> /dev/null,
    Error: NPM is not installed. Cannot run tests.,
    Proceed with test setup.
)

# 3. Test Configuration Validation
Test Type: $1
Target Files: $2
Coverage Threshold: $3

# Validate required arguments
$IF($1,
    Proceeding with test type: $1,
    Error: Test type is required. Usage: /test [type] [files] [coverage]
)

$IF($3,
    Validate coverage threshold is numeric,
    Error: Coverage threshold must be provided
)

# 4. Test Execution
Test Command: !`npm run test:$1 $2 --coverage --coverageThreshold=$3`

# 5. Coverage Analysis
Total Coverage: !`npm run coverage:report`

# 6. Reporting
Analyze test results:
- Passed tests
- Failed tests
- Code coverage percentage
- Comparison to threshold

# 7. Recommendations
If coverage below threshold:
  - Identify uncovered code areas
  - Suggest additional test cases
  - Provide improvement strategies

# 8. Final Status
$IF(test coverage meets $3 threshold,
    Test Passed: All checks successful,
    Test Failed: Review detailed report
)
