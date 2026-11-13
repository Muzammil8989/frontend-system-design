# Git hygiene

Habits that keep history readable and reviews fast. Use this file when splitting, squashing or cleaning up commits, and when setting up a repo.

## Atomic commits

One commit = one logical change that builds and passes tests on its own.

| Mixed commit | Split into |
|---|---|
| Feature + unrelated formatting | `style:` commit first, then `feat:` |
| Rename across 40 files + a bug fix | `refactor:` rename, then `fix:` |
| Dependency bump + code changes it needed | One commit is fine: they belong together |
| Two independent bug fixes | Two `fix:` commits |
| Feature + its tests + its docs | One `feat:` commit is fine |

Why it matters: `git revert`, `git bisect` and `git cherry-pick` work on whole commits. A commit that does two things can't be reverted for one of them.

## Staging only part of a change

```bash
git add -p <file>            # stage hunk by hunk: y, n, s (split), e (edit)
git add -p                   # every changed file
git restore --staged -p      # unstage hunk by hunk
git diff --cached            # review exactly what will be committed
git commit -v                # shows the diff in the editor while you write
```

To split the **last** commit (not pushed): `git reset HEAD~1`, then `git add -p` and commit each piece.

## Fixups while you work

Keep review rounds out of history without rewriting by hand:

```bash
git commit --fixup <sha>                 # "fixup! <original subject>"
git rebase -i --autosquash <base>        # folds every fixup into its target
git config --global rebase.autoSquash true
```

Only do this on branches nobody else has pulled. Once a PR is under review, some teams prefer plain follow-up commits and a squash merge. Follow the repo.

## Before you push

- `git diff --cached` (or `git show` after committing): no debug logs, commented-out code, `.only` in tests, or secrets.
- `git log --oneline <base>..HEAD`: every commit has a real message; no `wip`, `fixup!` or "address review".
- `python3 <skill-dir>/scripts/commit_check.py --range <base>..HEAD`: all pass.
- Tests and lint pass locally, or say clearly that they weren't run.

## What never goes in a commit

| Thing | Instead |
|---|---|
| `.env`, keys, tokens, certificates | `.env.example` with fake values; a secret manager |
| Build output (`dist/`, `build/`, `.next/`, `coverage/`) | `.gitignore`; CI builds it |
| Dependencies (`node_modules/`, `vendor/` unless intended) | Lockfile only |
| Large binaries, videos, datasets | Git LFS or external storage |
| Editor and OS files (`.DS_Store`, `.idea/`, `Thumbs.db`) | A global ignore: `git config --global core.excludesFile ~/.gitignore_global` |

Scan for secrets before the first push of a new repo: `gitleaks detect` or `trufflehog git file://.`. Many hosts (GitHub push protection) also block known token formats.

## .gitignore basics

```gitignore
# dependencies and build output
node_modules/
dist/
build/
.next/
coverage/

# env and secrets (keep the example)
.env
.env.*
!.env.example

# OS and editors
.DS_Store
Thumbs.db
.idea/
.vscode/*
!.vscode/extensions.json
```

An ignored file that is already tracked stays tracked. Remove it with `git rm --cached <file>` and commit.

## Line endings and big repos

- `.gitattributes` with `* text=auto eol=lf` stops CRLF/LF churn on mixed Windows/macOS teams. Add `*.png binary`-style rules for binaries.
- Large repos: `git clone --filter=blob:none` (partial clone), `git sparse-checkout`, and `git maintenance start`.

## Signing and identity

- Set identity per repo when you use more than one account: `git config user.email work@example.com`.
- Signed commits (`git config commit.gpgsign true`, with GPG or SSH: `gpg.format ssh`) show as Verified on GitHub. Some repos require them.
- `Signed-off-by:` (DCO) is different from signing: it's a statement about the right to contribute, added with `git commit -s`.

## Useful config

```bash
git config --global init.defaultBranch main
git config --global pull.rebase true          # rebase local commits on pull instead of merge bubbles
git config --global rebase.autoStash true
git config --global push.autoSetupRemote true # first push sets upstream
git config --global fetch.prune true          # forget deleted remote branches
git config --global rerere.enabled true       # remember conflict resolutions
git config --global diff.algorithm histogram
```

Suggest these; never change a user's global config without asking.
