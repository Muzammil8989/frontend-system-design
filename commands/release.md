---
description: Cut a release - pick the semver bump from commits, write the CHANGELOG entry, tag and release notes
argument-hint: "[version or bump, e.g. '2.1.0', 'minor', 'prerelease rc'] (default: decided from commits)"
---

Prepare a release. Requested version or bump: **$ARGUMENTS**

Follow the `git-workflow` skill, **Release** mode: follow the repo's own release process if it has one, decide the version with `scripts/commit_check.py --range <last-tag>..HEAD --suggest-bump` (warn if a requested version contradicts the commits), write the CHANGELOG entry and release notes for users, then show the plan. Commit and tag only after a yes; push only after a separate yes.
