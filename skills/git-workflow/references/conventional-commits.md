# Conventional Commits

The default message format when a repo has no convention of its own. It is short to learn, tools can read it (changelogs, version bumps, release notes), and reviewers can scan a log of it quickly. Spec: <https://www.conventionalcommits.org/en/v1.0.0/>.

## Shape

```text
type(scope)!: subject            ← header: 72 characters or fewer
                                 ← blank line
Body: why the change was needed, what the
trade-offs were, anything a reviewer or a
future reader should know. Wrap at 72-100.
                                 ← blank line
BREAKING CHANGE: what breaks and how to migrate
Refs #123
Co-authored-by: Name <email@example.com>
```

| Part | Rule | Example |
|---|---|---|
| `type` | Lower case, from the list below | `feat` |
| `(scope)` | Optional. One short noun for the area: package, module, feature | `(auth)`, `(cli)`, `(deps)` |
| `!` | Optional. Marks a breaking change | `feat(api)!:` |
| `subject` | Imperative mood, lower case start, no period, says *what* | `add passkey sign-in` |
| body | Optional but expected for anything non-obvious. Says *why* | |
| footers | `Token: value` lines at the end | `Closes #42` |

## Types

| Type | Use for | Version bump | CHANGELOG section |
|---|---|---|---|
| `feat` | A new capability for users | minor | Added |
| `fix` | A bug fix | patch | Fixed |
| `perf` | Faster or lighter, same behaviour | patch | Changed |
| `refactor` | Restructure with no behaviour change | none | (hidden) |
| `docs` | Documentation only | none | (hidden) |
| `style` | Formatting only | none | (hidden) |
| `test` | Tests only | none | (hidden) |
| `build` | Build system, dependencies | patch | Changed |
| `ci` | CI configuration | none | (hidden) |
| `chore` | Maintenance outside src and tests | none | (hidden) |
| `revert` | Undo an earlier commit | patch | Fixed |

Any type plus `!` or a `BREAKING CHANGE:` footer → **major**. The full list, with the extra `security` and `deprecate` types some repos use, is in `data/commit-types.csv`.

**Choosing between close types:**
- Did users get something they couldn't do before? `feat`. Did something that should have worked start working? `fix`.
- A refactor that also fixes a bug is two commits, or one `fix` whose body mentions the refactor.
- Updating a dependency to fix a vulnerability: `fix(deps):` (or `security(deps):` if the repo uses it), not `chore`. Users care about it.
- A test added *with* the feature belongs in the `feat` commit. `test:` is for test-only changes.

## Writing the subject

Read it as "If applied, this commit will **…**".

| Weak | Strong | Why |
|---|---|---|
| `fix: bug` | `fix(cart): keep items after sign-in` | Says which behaviour changed |
| `feat: Added dark mode.` | `feat(ui): add dark mode` | Imperative, lower case, no period |
| `chore: updates` | `build(deps): bump vite to 5.4.8` | Names the actual change |
| `fix: fixed the issue where the modal would sometimes not close when clicking outside of it on mobile` | `fix(modal): close on outside tap on mobile` | Detail goes in the body |
| `refactor: refactor code` | `refactor(api): extract retry into a shared helper` | Says what moved where |
| `feat: address review comments` | Squash it into the commit it fixes | Review rounds aren't history |

## Writing the body

Explain the **why**. The diff already shows the what.

```text
fix(auth): refresh the token before it expires, not after

Requests made in the last 30 seconds of a token's life failed with 401
because the refresh only started after the first failure. Refreshing at
80% of the lifetime removes the failed request and the retry flash.

Refs #318
```

Include, when true:
- the problem or user impact;
- why this approach and not the obvious alternative;
- anything surprising: a workaround, a known limitation, a follow-up;
- how to verify it, if that isn't obvious from the tests.

Leave out: a file-by-file list of changes, "this commit…", apologies, and anything that only makes sense in the context of the PR conversation.

## Breaking changes

Either `!` in the header, a `BREAKING CHANGE:` footer, or both. The footer must be upper case and exact. Say what breaks and how to migrate:

```text
feat(api)!: require an API key on every request

BREAKING CHANGE: anonymous requests now return 401. Create a key under
Settings → API and send it as the `x-api-key` header.
```

## Footers

| Footer | Meaning |
|---|---|
| `Closes #12` / `Fixes #12` | Closes the issue when merged (GitHub, GitLab) |
| `Refs #12` | Links without closing |
| `BREAKING CHANGE: …` | Major bump; shown in release notes |
| `Co-authored-by: Name <email>` | Credits a co-author (GitHub shows both) |
| `Reviewed-by:`, `Signed-off-by:` | Only if the repo requires them (DCO: `git commit -s`) |

Never invent an issue number. Use one from the user, the branch name or the PR.

## Scopes

- Pick scopes from what the repo already uses: `git log --format=%s | grep -oE '^\w+\(([^)]+)\)' | sort | uniq -c | sort -rn | head`.
- Monorepos: the package name (`feat(web):`, `fix(ui-kit):`).
- Leave the scope out rather than inventing a vague one like `(misc)` or `(core)`.

## Enforcing it

| Tool | What it does |
|---|---|
| `scripts/commit_check.py` | This skill's checker; no install, Python stdlib only |
| commitlint + `@commitlint/config-conventional` | The common Node linter, run in a `commit-msg` hook |
| husky / lefthook | Run hooks such as commitlint on commit |
| commitizen (`cz`) | Interactive prompt that writes the message |
| PR title check (e.g. `amannn/action-semantic-pull-request`) | Enforces the format on squash-merge titles |

If a repo already uses one of these, follow its config: extra types, scope lists and case rules override the defaults here. Pass extra types to the checker with `--types release,deps`.
