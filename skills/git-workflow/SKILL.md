---
name: git-workflow
description: Clean, reviewable git history. Use to commit, write or fix commit messages, split or squash commits, name branches, write PR descriptions, undo or recover from git mistakes (wrong branch, lost work, bad rebase, merge conflict, leaked secret), bump versions, tag releases or write changelogs. Follows the repo's conventions, else Conventional Commits, SemVer and Keep a Changelog; lints messages with a bundled checker. Commits only after the user confirms; never pushes or rewrites shared history unless asked.
---

# Git Workflow

Leave history a reviewer, `git bisect` and a release tool can use: one logical change per commit, messages that say why, PRs small enough to review in one sitting, and the least destructive fix for every mistake. `<skill-dir>` = the folder containing this file.

## Always first: learn the repo's rules

Run `git status`, `git branch --show-current`, `git log --oneline -20`. Skim any `CONTRIBUTING*`, PR template, commitlint/husky/lefthook config, `.changeset/`, release-please config, `CHANGELOG.md` and the latest tag (`git describe --tags --abbrev=0`). **The repo's convention wins**; say which one you follow.

## Modes

| Mode | Steps | Read |
|---|---|---|
| **Commit** | 1. `git diff --cached --stat` then the diff; if nothing is staged, show `git status` and ask (never stage everything unseen). 2. Secret, key, token or `.env` in the diff → stop, don't commit. 3. Mixed concerns → propose a split (`git add -p`). 4. Write `type(scope)!: subject` (≤ 72 chars, imperative, no period), a body that says why, real footers only. 5. Lint it (below) until no errors, score ≥ 90. 6. Show files + message, ask "Commit this?". 7. On yes: `git commit -F <file>`, hooks on; if a hook fails, fix and commit again. 8. Don't push; give the push command | `references/conventional-commits.md`, `references/git-hygiene.md`, `data/commit-types.csv` |
| **PR** | 1. On the default branch? Propose `type/short-kebab-name` first. 2. Read the whole branch: `git log --oneline <base>..HEAD`, `git diff <base>...HEAD --stat`; lint the range. 3. Over ~400 changed lines or mixed concerns → suggest a split. 4. Title in commit-header format. 5. Description from the repo's template, else ours: what/why, how, tests actually run, risk/rollback, `[placeholder: screenshot]`, linked issues. 6. Offer `gh pr create …`; run only on yes | `references/branches-and-prs.md` |
| **Undo** | 1. Diagnose: `git status`, `git log --oneline --graph -15`, `git reflog -20`. 2. Ask only "pushed or shared?" if unknown. 3. Safest fix first, with risk and whether it rewrites history, then the alternative and how to undo the fix. 4. Backup branch or stash before anything medium/high risk. 5. Leaked secret: revoke/rotate **first**, then clean history | `data/git-recipes.csv`, `references/undo-and-recovery.md` |
| **Release** | 1. Follow the repo's release process if any. 2. Bump from commits since the last tag (`--suggest-bump`); breaking → major (minor before 1.0), feat → minor, else patch; name the driving commits. 3. Keep a Changelog entry written for users (Added, Changed, Deprecated, Removed, Fixed, Security), today's date. 4. Show the plan: version files, `chore(release): vX.Y.Z`, annotated tag. 5. Local steps on yes; push commit and tag only on a separate yes | `references/releases-and-changelog.md` |

## Checker

```bash
python3 <skill-dir>/scripts/commit_check.py "feat(cli): add --companions all"     # Windows: py or python
python3 <skill-dir>/scripts/commit_check.py --file .git/COMMIT_EDITMSG
python3 <skill-dir>/scripts/commit_check.py --range origin/main..HEAD             # every commit on the branch
python3 <skill-dir>/scripts/commit_check.py --range v1.2.0..HEAD --suggest-bump   # next version
```

`--range` lists only commits with issues (`--verbose` for all). Add `--json` for compact machine output, `--types a,b` for the repo's extra types.

## Hard rules

1. Never push, force-push, rewrite published history, delete branches or tags, or use `--no-verify` unless the user asks for that exact action.
2. Destructive commands (`reset --hard`, `clean -fd`, `push --force-with-lease`, `branch -D`, `stash drop`, `filter-repo`) each need an explicit yes. Never plain `--force`. If the `fsd-guard` hook denies a command, tell the user why; never work around it.
3. On shared branches prefer `revert` over `reset`; prefer `switch`/`restore` over `checkout`.
4. Never commit secrets, build output or large binaries; read the diff, not just file names.
5. Never invent issue numbers, versions, test results or reviewers.
6. One logical change per commit; formatting separate from behaviour.

## Output

Commit: `Proposed commit (n of m)` → files → full message → checker score → `Commit this? (yes / edit / skip)`.
Undo: **Situation** → **Safest fix** (commands · risk · rewrites history yes/no) → **Alternative** → **How to undo this fix**.

Pairs with: **frontend-system-design** (commit its output in slices: docs, tokens, components, tests) and **product-copywriting** (polish user-facing release notes).
