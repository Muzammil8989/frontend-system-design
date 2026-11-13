# Branches and pull requests

## Branch names

`type/short-kebab-description`, with the ticket key if the team uses one.

| Good | Weak | Why |
|---|---|---|
| `feat/passkey-sign-in` | `new-stuff` | Says what the branch is for |
| `fix/482-cart-empty-after-login` | `bugfix` | Links the issue, names the bug |
| `chore/bump-vite-5` | `muzammil-branch` | Owner is in the git metadata already |
| `docs/install-guide` | `Docs_Update_FINAL` | Lower case, hyphens, no "final" |
| `release/2.4.0`, `hotfix/2.4.1` | `rel` | Only if the repo uses release branches |

Rules: lower case, hyphens, no spaces, under about 50 characters. Use the same types as commits (`feat`, `fix`, `docs`, `chore`, `refactor`, `perf`, `test`, `ci`, `build`).

```bash
git switch -c feat/passkey-sign-in           # create and switch
git push -u origin feat/passkey-sign-in      # first push sets upstream (ask first)
git branch -m old-name new-name              # rename a local branch
```

## Branching strategies

| Strategy | How it works | Fits |
|---|---|---|
| **Trunk-based** (recommended default) | Short-lived branches (hours to 2 days) off `main`, merged behind feature flags. `main` is always releasable | Most product teams with CI and continuous deployment |
| **GitHub flow** | Branch → PR → review → merge to `main` → deploy | Small teams and open source; the same idea with less ceremony |
| **Release branches** | `main` plus `release/x.y` branches for stabilization and patches | Apps with app-store reviews, on-prem installs, several supported versions |
| **Git flow** | `develop`, `feature/*`, `release/*`, `hotfix/*`, `main` | Scheduled releases only. Heavy for web apps with continuous deployment |

Whatever the strategy: keep branches short-lived, rebase or merge from `main` often, and delete branches after merging.

## PR size

| Changed lines (excluding generated files, lockfiles, snapshots) | Review quality |
|---|---|
| Under 200 | Reviewed carefully, merged fast |
| 200-400 | Fine if it is one concern |
| Over 400 | Reviewers skim. Split it |

How to split:
- **By layer:** schema/API first, then UI, each behind a flag.
- **Prep refactor first:** a no-behaviour-change PR that makes the feature PR small.
- **Stacked PRs:** PR 2 targets PR 1's branch. Tools: `gh` with base branches, Graphite, `git town`, `spr`.
- **Mechanical changes alone:** renames, formatting and codemods get their own PR so reviewers can skim them safely.

## PR title

Same format as a commit header, because squash merges use the title as the commit:

```text
feat(auth): add passkey sign-in
```

## PR description template

Use the repo's `.github/PULL_REQUEST_TEMPLATE.md` when it exists. Otherwise:

```markdown
## What and why
<!-- 1-3 sentences: the user-visible change and the reason. Link the issue. -->
Adds passkey sign-in next to email links, so returning users can sign in
without waiting for an email. Closes #482.

## How
<!-- The approach and anything a reviewer should look at first. -->
- WebAuthn via the existing auth service; no new dependency.
- Feature-flagged as `passkeys` (off by default).

## How it was tested
<!-- Only what was actually run. -->
- [x] Unit tests for the challenge/verify handlers
- [x] Manual: Chrome 131 and Safari 18 on macOS, Android Chrome
- [ ] Not tested: Firefox on Windows

## Screenshots
<!-- UI changes only: before / after. -->
[placeholder: screenshot of the sign-in screen with the passkey button]

## Risk and rollback
<!-- What could break, who is affected, how to undo. -->
Low: behind a flag. Roll back by turning the flag off.

## Checklist
- [ ] Commit messages follow the convention
- [ ] CHANGELOG updated (if user-facing)
- [ ] Docs updated (if behaviour changed)
```

Rules: no invented test results, reviewers or numbers; tick only what was done; list what wasn't tested.

Create it from the command line after the user agrees:

```bash
gh pr create --base main --title "feat(auth): add passkey sign-in" --body-file pr.md
gh pr create --draft ...          # open early for feedback
```

## Reviewing and being reviewed

**As the author:**
- Review your own diff in the PR view before asking anyone.
- Leave comments on the tricky parts before reviewers find them.
- Answer every comment: fix it, or explain why not. Resolve threads only after the reviewer agrees, if that's the team norm.
- Push follow-ups as new commits during review so reviewers can see what changed. Squash at merge.

**As the reviewer:**
- Prefix comments so the author knows the weight: `blocking:`, `suggestion:`, `nit:`, `question:`.
- Comment on the code, not the person. Suggest, with an example.
- Approve with nits when the nits don't need another round.

## Merge strategies

| Strategy | Result | Use when |
|---|---|---|
| **Squash and merge** | One commit per PR on `main`; the PR title becomes the message | Most teams. Clean `main`, and PR history stays in the PR |
| **Rebase and merge** | Every PR commit lands on `main` linearly | Commits are already clean and atomic |
| **Merge commit** | All commits plus a merge commit | Long-lived branches and release merges, where the merge point matters |

Follow the repo setting. After merging, delete the branch (`git branch -d <name>`, `git fetch --prune`).

## Keeping a branch up to date

```bash
git fetch origin
git rebase origin/main        # private branch: linear history
git merge origin/main         # shared branch: never rewrite others' commits
git push --force-with-lease   # only after rebasing your own branch, and only when asked
```
