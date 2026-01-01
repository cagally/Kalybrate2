---
name: deploy
description: Deploy a service to a specific environment after git status check
argument-hint: [environment] [service]
allowed-tools: Bash(git:*), Read
---

# Validate git working directory is clean
Git Status Check: !`git status --porcelain`

$IF($BASH_OUTPUT,
    # If there are uncommitted changes, halt deployment
    Deployment Blocked: Uncommitted changes exist in repository.
    
    Uncommitted changes detected:
    $BASH_OUTPUT
    
    Please commit or stash changes before deploying.
    
    Suggested actions:
    1. Commit changes: git commit -m "Description of changes"
    2. Stash changes: git stash
    3. Discard changes: git reset --hard

,
    # No uncommitted changes, proceed with deployment
    Deploying $2 to $1 environment:

    1. Confirm deployment target:
       - Environment: $1
       - Service: $2

    2. Pull latest changes
       !`git pull origin main`

    3. Deploy steps:
       !`./deploy.sh $1 $2`

    4. Verify deployment
       Checking deployment status...
       !`./check-deployment.sh $1 $2`

    Deployment Summary:
    - Target Environment: $1
    - Service Deployed: $2
    - Timestamp: !`date`
)
