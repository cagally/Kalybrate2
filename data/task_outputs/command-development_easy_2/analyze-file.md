---
description: Analyze a specific file for code quality and insights
argument-hint: [file-path]
allowed-tools: Read, Bash(*)
---

# Validate file existence
$IF(!test -f $1,
  File $1 does not exist. Please provide a valid file path.,
  Continue with analysis
)

# Basic file information
File Path: $1
File Type: !`file $1`
File Size: !`du -h $1`
Line Count: !`wc -l $1`

# Language Detection
Language: !`which highlight && highlight -O ansi $1 | head -n 1 || echo "Could not detect language"`

# Content Analysis
1. Perform initial code scan:
   - Check for potential code smells
   - Identify complexity indicators
   - Look for possible security issues

2. Detailed file insights:
   - Coding style consistency
   - Potential performance bottlenecks
   - Documentation and comment quality
   - Naming conventions
   - Structural patterns

3. Recommendations:
   Provide actionable suggestions for improving the file based on the analysis.
