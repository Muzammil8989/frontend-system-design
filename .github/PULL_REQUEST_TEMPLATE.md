## Summary

<!-- What does this PR change and why? Link the issue. -->

Closes #

## Type

- [ ] Skill: references or playbooks (`skills/frontend-system-design/references/`)
- [ ] Skill: data (`skills/frontend-system-design/data/*.csv`)
- [ ] Skill: product-copywriting or git-workflow (`skills/product-copywriting/`, `skills/git-workflow/`)
- [ ] Skill: Python scripts or tests
- [ ] Agents or commands (`agents/`, `commands/`)
- [ ] Installer, companions or CI (`bin/`, `companions.json`, `.github/`)
- [ ] Learning note (`notes/`)
- [ ] Docs

## Checklist

- [ ] `npm test` passes locally (note lint, skill validation, Python tests)
- [ ] Recommendations are backed by official docs or measurements; no invented numbers
- [ ] New palettes pass WCAG AA (the test suite checks contrast automatically)
- [ ] New product types reference existing stacks, styles and patterns, and a playbook heading
- [ ] Installer changes: tested `node bin/cli.js install --all --dir <tmp> --no-companions`, and the re-run reports no changes
- [ ] Learning notes: every template section is filled in, and the README progress and badge are updated
- [ ] `CHANGELOG.md` updated under **Unreleased**
- [ ] Commit messages and the PR title follow Conventional Commits (`python skills/git-workflow/scripts/commit_check.py --range origin/main..HEAD`)

## Example output (for skill or script changes)

<details>
<summary>Before / after</summary>

<!-- e.g. python skills/frontend-system-design/scripts/recommend.py "..." -->

</details>
