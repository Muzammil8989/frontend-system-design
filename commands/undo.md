---
description: Fix a git mistake safely - diagnose, then the least destructive fix first, with risk levels and a way back
argument-hint: "<what went wrong, e.g. 'committed to main', 'lost my changes after reset', 'rebase conflict'>"
---

Help me recover from this git problem: **$ARGUMENTS**

Follow the `git-workflow` skill, **Undo** mode with `data/git-recipes.csv`: diagnose first, then the safest fix with its risk and whether it rewrites history, the alternative, and how to undo the fix. Make a backup branch or stash before risky steps, and run each destructive command only after its own yes. For a leaked secret, revoke it first. Finish with `git status`.
