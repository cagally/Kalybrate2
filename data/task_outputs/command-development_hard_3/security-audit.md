---
name: security-audit
description: Perform comprehensive security audit with dynamic context
argument-hint: [environment]
allowed-tools: Read, Bash(git:*), Bash(*)
---

# Security Audit Workflow

# Validate environment argument
$IF(
  $OR(
    $EQ($1, "dev"),
    $EQ($1, "staging"),
    $EQ($1, "production")
  ),
  "Valid environment selected: $1",
  "Invalid environment. Use: /security-audit [dev|staging|production]"
)

# Gather Git Context
Current Branch: !`git rev-parse --abbrev-ref HEAD`
Last Commit: !`git log -1 --pretty=format:"%h - %an, %ar : %s"`
Git Status: !`git status -s`

# Dynamic Configuration Loading
Dev Config: @config/security-dev.json
Staging Config: @config/security-staging.json
Production Config: @config/security-production.json

# Environment-Specific Security Checks
$SWITCH($1,
  "dev", {
    Perform lightweight security scan
    Check development-specific vulnerabilities
    Review local environment configurations
  },
  "staging", {
    Enhanced security scan
    Validate pre-production security controls
    Check configuration drift
    Review network access rules
  },
  "production", {
    Comprehensive security audit
    Full vulnerability assessment
    Compliance and regulatory checks
    Advanced threat detection analysis
  }
)

# Common Security Checks Across All Environments

1. Code Repository Security
   - Check for sensitive data in git history
   - Validate branch protection rules
   - Review recent commit authors and changes

2. Dependency Vulnerability Scan
   - !`npm audit`
   - !`npm outdated`
   - Check for known security vulnerabilities in dependencies

3. Configuration Security
   - Scan configuration files for exposed secrets
   - Check for hardcoded credentials
   - Validate encryption settings

4. Access Control Review
   - Audit user permissions
   - Check role-based access control (RBAC) settings
   - Review authentication mechanisms

5. Network and Infrastructure Security
   - Verify firewall rules
   - Check open ports
   - Review network segmentation

# Reporting
Generate comprehensive security report with:
- Identified vulnerabilities
- Severity ratings
- Recommended remediation steps
- Compliance status

# Final Risk Assessment
Compile risk matrix based on discovered issues
Prioritize and categorize security findings

Provide actionable insights for security improvement.
