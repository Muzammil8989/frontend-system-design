---
description: Prepare a pull request - branch name, title, description and size check - from the current branch
argument-hint: "[base branch, issue or focus, e.g. 'main' or 'closes #482']"
---

Prepare a pull request for the current branch. Extra context: **$ARGUMENTS**

Follow the `git-workflow` skill, **PR** mode: read every commit since the base (the one given above, or the default branch), lint the range with `scripts/commit_check.py`, check the size, then give the title and description in a copyable block. Offer `gh pr create`, and run it or push only after a yes.
