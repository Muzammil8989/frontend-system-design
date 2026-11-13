# Releases and changelog

## Semantic Versioning

`MAJOR.MINOR.PATCH`. Spec: <https://semver.org/>.

| Bump | When | From commits |
|---|---|---|
| **MAJOR** | Breaking change to the public API, CLI flags, config format or supported runtimes | `!` or `BREAKING CHANGE:` |
| **MINOR** | New backwards-compatible capability | `feat` |
| **PATCH** | Backwards-compatible fix | `fix`, `perf`, `revert`, user-facing `build(deps)` |
| none | Docs, tests, CI, refactors, chores only | Usually no release |

- **Before 1.0.0** anything may change. Most tools treat a breaking change as a minor bump (0.4.1 → 0.5.0), and the checker does the same.
- **Pre-releases:** `2.0.0-beta.1`, `2.0.0-rc.1`. They sort before `2.0.0`. Publish them on a separate npm dist-tag (`npm publish --tag next`).
- **What counts as "public API"** is whatever users depend on: exported functions, HTTP routes, CLI flags, environment variables, file formats, and for apps, deep links and saved data.

Work out the bump from history:

```bash
python3 <skill-dir>/scripts/commit_check.py --range "$(git describe --tags --abbrev=0)..HEAD" --suggest-bump
```

Explain the decision with the commits that drove it. If the commits don't follow the convention, read them and decide by hand.

## Keep a Changelog

Format: <https://keepachangelog.com/en/1.1.0/>. One file, `CHANGELOG.md`, newest first, written for **users**, not copied from commit subjects.

```markdown
# Changelog

## [Unreleased]

## [1.5.0] - 2026-11-13

### Added
- Passkey sign-in on web and Android. Turn it on with the `passkeys` flag.

### Changed
- Sessions now refresh in the background, so long forms no longer fail on submit.

### Deprecated
- `GET /v1/search` will be removed in 2.0. Use `POST /v2/search`.

### Removed
- Node 16 support.

### Fixed
- Cart items no longer disappear after signing in (#482).

### Security
- Login redirects now reject external URLs.

[Unreleased]: https://github.com/owner/repo/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/owner/repo/compare/v1.4.2...v1.5.0
```

Rules:
- Sections in this order, and only the ones you need: Added, Changed, Deprecated, Removed, Fixed, Security.
- Each line says what changed **for the user** and, if it matters, what they should do.
- Leave out internal-only work (refactors, CI, tests) unless it affects users.
- Dates are ISO 8601 (`YYYY-MM-DD`). Use the real release date.
- Keep an `## [Unreleased]` section at the top, and move its entries into the new version at release time.
- Breaking changes go first in their section, with migration steps.

## Release checklist (no tooling)

Follow the repo's own process if it has one (CONTRIBUTING, a release workflow, scripts). Otherwise:

1. `git switch main && git pull`: the release is cut from an up-to-date, green `main`.
2. Decide the version (above).
3. Move `[Unreleased]` entries to `## [X.Y.Z] - YYYY-MM-DD` and update the compare links.
4. Bump the version files. For npm: `npm version X.Y.Z --no-git-tag-version`, which also updates the lockfile.
5. Commit: `chore(release): vX.Y.Z`.
6. Tag it, annotated: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
7. **Ask**, then push: `git push && git push origin vX.Y.Z`. The tag usually triggers the release workflow.
8. Create the release notes: `gh release create vX.Y.Z --notes-file notes.md` (or `--generate-notes`), unless CI does it.

## Release notes vs changelog

| | CHANGELOG | Release notes |
|---|---|---|
| Audience | Developers and power users | Everyone, including non-technical users |
| Tone | Factual list | A short story: the headline change first, why it matters, then the list |
| Where | Repo file | GitHub Release, app store "What's new", blog, email |

For app-store and marketing release notes, draft the facts here, then hand them to the **product-copywriting** skill if it is installed.

## Hotfixes

- Trunk-based: fix on `main`, release a patch from `main`.
- Release branches: branch `hotfix/X.Y.Z+1` from the release tag (or the `release/X.Y` branch), fix, tag, release, then merge or cherry-pick the fix back to `main` so it isn't lost.

## Automation options

| Tool | Approach |
|---|---|
| **release-please** (Google) | Opens a release PR from Conventional Commits; merging it tags and releases |
| **semantic-release** | Fully automatic: version, changelog, publish on every merge to `main` |
| **Changesets** | Contributors add a small changeset file per PR; good for monorepos |
| `npm version` + a tag-triggered workflow | Manual bump, automated publish |

Recommend one only when the user asks for automation, and match it to the repo: monorepo → Changesets; Conventional Commits already enforced → release-please.

## Tags

```bash
git tag -a v1.5.0 -m "v1.5.0"        # annotated: has author, date, message (use these)
git tag --sort=-v:refname | head     # latest tags by version
git describe --tags --abbrev=0       # most recent tag reachable from HEAD
git push origin v1.5.0               # push one tag (ask first)
git tag -d v1.5.0 && git push origin :refs/tags/v1.5.0   # delete: only if not yet consumed by anyone
```

Never move or reuse a published tag. If a release is bad, release a new patch.
