# Undo and recovery

Almost nothing in git is lost once it has been committed. The skill here is choosing the least destructive fix. The quick table is `data/git-recipes.csv`. This file explains how to diagnose a problem and how the tools behave.

## First, diagnose

```bash
git status                         # branch, staged/unstaged, in-progress merge/rebase
git log --oneline --graph -15      # where HEAD is, what's on top
git reflog -20                     # every place HEAD has been, even "lost" commits
git stash list
```

Then ask the one question that decides the fix: **has it been pushed or pulled by anyone?**

| | Not shared (only on this machine) | Shared (pushed, others may have it) |
|---|---|---|
| Change a commit | `--amend`, `rebase -i`, `reset` are fine | Add a new commit, or `git revert` |
| Remove a commit | `reset` | `revert` |
| Force-push | Not needed | Only on your own branch, with `--force-with-lease`, after asking |

## The safety net

Before anything risky:

```bash
git branch backup/before-fix          # pins the current commit
git stash push -u -m "before fix"     # saves uncommitted work, untracked files too
```

To undo the fix afterwards: `git reset --hard backup/before-fix`. Delete the backup when you're sure.

## reset, revert, restore, switch

| Command | Moves the branch? | Touches files? | Rewrites history? | Safe on shared branches? |
|---|---|---|---|---|
| `git restore <file>` | No | Discards edits to that file | No | Yes, but the edits are gone |
| `git restore --staged <file>` | No | Unstages only | No | Yes |
| `git switch <branch>` | Moves HEAD | Updates the working tree | No | Yes |
| `git reset --soft <sha>` | Yes | No (changes stay staged) | Yes | No |
| `git reset --mixed <sha>` (default) | Yes | No (changes stay unstaged) | Yes | No |
| `git reset --hard <sha>` | Yes | **Discards** uncommitted work | Yes | No |
| `git revert <sha>` | Adds a commit | Applies the inverse | No | **Yes** |

## Reflog: getting "lost" commits back

The reflog records where HEAD and each branch pointed, by default for about 90 days (30 for unreachable entries).

```bash
git reflog
# a1b2c3d HEAD@{0}: reset: moving to HEAD~3
# 9f8e7d6 HEAD@{1}: commit: feat(cart): save for later      ← the one you want
git branch rescue 9f8e7d6        # safest: new branch at the lost commit
git reset --hard 9f8e7d6         # or move the current branch back (after confirming)
```

Deleted a branch? `git reflog` shows its last commit. Then `git branch <name> <sha>`.

What can't be recovered: changes that were never committed or stashed and were then overwritten by `reset --hard`, `restore`, `checkout -- <file>` or `clean`. Some editors' local history may still have them.

## Rebase trouble

| Situation | Fix |
|---|---|
| Conflicts and you want out | `git rebase --abort` |
| One commit is no longer needed | `git rebase --skip` |
| Conflicts fixed | `git add <files>` then `git rebase --continue` |
| Finished, but the result is wrong | `git reset --hard ORIG_HEAD` straight away, or find the pre-rebase sha in `git reflog` |
| The same conflict keeps coming back | `git config rerere.enabled true` |

## Merge conflicts

1. `git status` lists the conflicted files.
2. Open each one and resolve every `<<<<<<<` / `=======` / `>>>>>>>` block. Keep the intent of both sides, not just one.
3. Search for leftover markers: `git diff --check`.
4. Build and run the tests. A conflict-free merge can still be broken.
5. `git add <files>`, then `git commit` (merge) or `git rebase --continue` (rebase).
6. To give up: `git merge --abort` or `git rebase --abort`.

Lockfiles: don't hand-merge them. Take one side, then re-run the package manager (`npm install`, `pnpm install`) and commit the result.

## Leaked secret

The order matters:

1. **Revoke or rotate the secret now.** Assume it's compromised from the moment it was pushed: bots scan public pushes within minutes. Cleaning history does not un-leak it.
2. Remove it from the code, load it from the environment or a secret manager, and add the file to `.gitignore`. Commit that.
3. If the repo is public, or the secret is high-value, purge it from history: `git filter-repo --replace-text replacements.txt` (or `--path <file> --invert-paths`), or BFG Repo-Cleaner. Then a coordinated force-push, and every collaborator re-clones. Ask the user before doing any of this.
4. Check the other places it may have spread: CI logs, forks, open PRs, caches and artifacts. On GitHub, ask support to purge cached views if needed.
5. Prevent a repeat: secret scanning or push protection on the host, and a pre-commit hook such as gitleaks.

## Force-pushing safely

- Only on a branch you own, and only after the user asks.
- `git push --force-with-lease` refuses if the remote has commits you haven't seen. Plain `--force` overwrites them.
- Never on `main`, `master`, `develop` or release branches without the team's agreement. Many repos protect these branches anyway.
- Afterwards, anyone else with the branch runs `git fetch && git reset --hard origin/<branch>`, after saving their own work.

## Finding the commit that broke something

```bash
git bisect start
git bisect bad                    # current commit is broken
git bisect good v2.3.0            # this one worked
# test each commit git checks out, then mark it: git bisect good / git bisect bad
git bisect run npm test           # or automate it with any command that exits non-zero on failure
git bisect reset                  # back to where you started
```

This is why atomic, building commits matter: bisect lands on the exact change.
