---
description: Write a clean, checked commit for the staged changes (splits mixed changes, commits only after you confirm)
argument-hint: "[optional hint, e.g. 'fixes #42' or 'split into two commits']"
---

Commit the current changes. Extra instructions: **$ARGUMENTS**

Follow the `git-workflow` skill, **Commit** mode, end to end: read the repo's rules, review the staged diff, stop on secrets, split mixed changes, lint every message with `scripts/commit_check.py`, then show the files and message and ask **"Commit this?"**. Run `git commit` only after a yes. Never push.
