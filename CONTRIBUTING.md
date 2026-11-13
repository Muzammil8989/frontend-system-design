# Contributing

Thanks for helping make **Frontend System Design** better! It's two things in one repo, and both welcome contributions:

1. **The AI skills.** `frontend-system-design` gives coding agents staff-level judgement on frontend and app architecture and UI, for web, mobile and desktop. `product-copywriting` writes human-sounding website and app copy. `git-workflow` keeps commits, PRs and releases clean and fixes git mistakes safely. All three live in `skills/`, `agents/`, `commands/`, `src/cli/` and `companions.json`.
2. **The learning roadmap.** 120 deep-dive notes on frontend system design, in `notes/`. They also ship inside the skill as its knowledge base: agents cite them in designs, and `/fsd:learn` teaches from them.

- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Repository layout](#repository-layout)
- [Contributing to the skill](#contributing-to-the-skill)
- [Contributing a learning note](#contributing-a-learning-note)
- [Commits, PRs and reviews](#commits-prs-and-reviews)
- [Releases](#releases)
- [License](#license)

---

## Ways to contribute

| You want to… | Start here |
|---|---|
| Fix a wrong or outdated recommendation | [Skill improvement issue](https://github.com/Muzammil8989/frontend-system-design/issues/new?template=skill-improvement.yml), or a PR to `references/` or `data/` |
| Add or improve a **stack guide** (any framework, mobile or desktop) | [docs/adding-a-stack.md](./docs/adding-a-stack.md) |
| Add a product playbook, palette, font pairing or UX pattern | PR to `skills/frontend-system-design/data/*.csv` and `references/playbooks/product-playbooks.md` |
| Improve the copywriting rules or the AI-tell list | PR to `skills/product-copywriting/references/` or `data/ai-tells.csv` |
| Improve the git rules, or add an undo recipe | PR to `skills/git-workflow/references/` or `data/git-recipes.csv` (keep the safest fix first, with an honest risk level) |
| Improve an agent or command | PR to `agents/` or `commands/` |
| Support another AI tool, or add a companion skill | [docs/adding-an-agent-tool.md](./docs/adding-an-agent-tool.md); open an issue first |
| Write a roadmap note | Claim it with a [New topic issue](https://github.com/Muzammil8989/frontend-system-design/issues/new?template=new-topic.yml) |
| Fix a note | [Correction issue](https://github.com/Muzammil8989/frontend-system-design/issues/new?template=correction.yml), or a direct PR |

Good first issues are labelled [`good first issue`](https://github.com/Muzammil8989/frontend-system-design/labels/good%20first%20issue).

---

## Development setup

Requirements: **Node.js ≥ 18** (≥ 22.20 to test the `npx skills` companions), **Python ≥ 3.9**, and **Git**. The Python scripts use only the standard library. The installer has one runtime dependency.

```bash
git clone https://github.com/<you>/frontend-system-design.git
cd frontend-system-design

npm ci                       # one small dependency (@clack/prompts, for the install wizard)
npm test                     # note lint, knowledge sync, skill validation, Node and Python tests (same as CI)

# Try your local copy in a scratch project
node bin/cli.js install --dir ../scratch                             # interactive wizard
node bin/cli.js install --all --yes --dir ../scratch --no-companions # no questions
node bin/cli.js install --all --dir ../scratch --dry-run             # preview, including companion commands

# Use the Python engine directly
python skills/frontend-system-design/scripts/recommend.py "real-time analytics dashboard"
python skills/frontend-system-design/scripts/search.py --domain palettes "fintech dark"
```

> On Windows, use `py` instead of `python` if `python` isn't on your PATH.

---

## Repository layout

```text
skills/
├── frontend-system-design/        Architect skill (copied as-is by the installer)
│   ├── SKILL.md                   Workflow + triggers (keep under ~500 lines)
│   ├── references/core/           requirements, architecture, ui-design, performance, quality
│   ├── references/platforms/      web, mobile, desktop
│   ├── references/stacks/         one guide per stack (shared template, enforced by the validator)
│   ├── references/playbooks/      product playbooks
│   ├── references/templates/      design-doc template, audit rubric
│   ├── references/knowledge/      GENERATED from notes/ by `npm run sync:knowledge`; don't edit
│   ├── scripts/*.py               recommend, detect_stack, search, budget, audit_scan, tokens_check (stdlib only)
│   └── data/*.csv                 curated datasets
├── product-copywriting/           SKILL.md · references/ · scripts/copy_check.py · data/
└── git-workflow/                  SKILL.md · references/ · scripts/commit_check.py · data/{commit-types,git-recipes}.csv
agents/  commands/                 Specialist subagents and slash commands
src/cli/                           Installer: index · install · wizard · detect · adapters/ · writer · companions
bin/cli.js                         npx entry point
notes/                             Learning notes (source of truth): one folder per roadmap phase + _TEMPLATE.md
scripts/                           Repo tooling: lint-notes, sync-knowledge, validate-skills, run-python-tests
tests/node/  tests/python/         Installer tests · engine, token, copy-checker and commit-checker tests
docs/                              architecture, adding a stack, adding an AI tool
```

---

## Contributing to the skill

### Quality bar
- **Evidence over opinion.** Every recommendation should trace back to official docs (MDN, web.dev, specs, framework docs) or a measurement. Don't invent benchmarks.
- **Fit over fashion.** Recommend the simplest thing that meets the requirements, and say when to switch.
- **Version-safe wording.** Describe capabilities ("supports streaming SSR"), not version numbers you haven't verified.
- **Concise.** Agents read these files on every run. Prefer tables and checklists to prose, and keep `SKILL.md` lean; detail belongs in `references/`.

### Datasets (`data/*.csv`)

| File | Rules |
|---|---|
| `product-types.csv` | `stacks`, `ui_styles` and `patterns` must reference existing ids (`;`-separated). `playbook` must match a `## heading` in `references/playbooks/product-playbooks.md`. Add rich `keywords` so classification works |
| `palettes.csv` | Must pass **WCAG AA**, which the tests enforce: text/bg and muted/bg ≥ 4.5:1, on-primary/primary ≥ 4.5:1, and primary and semantic colors on bg ≥ 3:1 |
| `font-pairings.csv` | Freely licensed fonts only (e.g. Google Fonts), with exact family names |
| `ux-patterns.csv`, `ui-styles.csv`, `stacks.csv` | Include `a11y` notes and anti-patterns or trade-offs; links must be official docs |

After any data change, run `npm run test:py` and check that the classification tests still pass. If you add a product type, add a test case to `RecommendTest.CASES` in `tests/python/test_engine.py`.

### Agents and commands
- The `name` frontmatter must match the file name. Keep `description` specific, because it decides when the agent is used.
- Claude Code subagents can't spawn other subagents. Orchestration belongs in `commands/`, specialists in `agents/`.
- Reviewer agents stay **read-only**: no `Write` or `Edit` in their tools.

### Installer and companions
- The installer (`bin/cli.js` → `src/cli/`) has one runtime dependency, `@clack/prompts`, used only by the interactive wizard. Don't add more. It must stay **idempotent**: a second run reports no changes. CI checks this on Linux, macOS and Windows.
- A companion must be a public GitHub project with an OSI or clear license and an **official** installer command. Verify the command against its README, add it to `companions.json` (pinned to an exact package version: `npx --yes <package>@x.y.z …`; `npm run validate` enforces this) and `THIRD_PARTY.md`, and never vendor its files. Review upstream changes before bumping a pinned version.

Then run `npm run validate`.

---

## Contributing a learning note

1. **Claim a topic** with a [New topic issue](https://github.com/Muzammil8989/frontend-system-design/issues/new?template=new-topic.yml) so no one else picks it up.
2. **Scaffold** it: `npm run new-note -- <slug> --phase <1-11> --title "<Title>"` (lower-case, hyphenated slug). The note lands in its phase folder, e.g. `notes/03-state-and-data/<slug>.md`.
3. **Fill every section of the template** in order:
   1. ELI5
   2. Core Concept (with Mermaid diagrams)
   3. Real-World Examples
   4. Key Points Summary
   5. Test Your Understanding (3 or more questions with `<details>` answers)
   6. Cheat Sheet
   7. References

   Every code fence declares a language.
4. **Update the README:**
   - mark the topic `✅ [Title](./notes/<NN-phase>/<slug>.md)`;
   - update the phase **Done** count, the **Total** row, and the progress badge;
   - fix the prev/next links in the neighbouring notes.
5. **Run** `npm run lint:notes`. It must report 0 errors.
6. **Sync the knowledge base:** `npm run sync:knowledge`. This copies your note into the skill and updates `knowledge/INDEX.md`. Add an `> **Informs:** …` line to the note's metadata listing the design decisions it explains, e.g. "offline-first, token storage". CI fails if you forget to sync.

Tip: install the skill into your clone (`npm run skills:install -- --agent claude --no-companions`) and ask your agent to fact-check the note against MDN and the specs before you open the PR.

---

## Commits, PRs and reviews

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Example |
|---|---|
| `feat(skill)` | `feat(skill): add booking marketplace playbook` |
| `fix(data)` | `fix(data): raise muted contrast in health-calm palette` |
| `feat(agents)` | `feat(agents): add i18n-specialist agent` |
| `feat(cli)` / `fix(cli)` | `feat(cli): support Windsurf rules` |
| `feat(notes)` / `fix(notes)` | `feat(notes): add DOM & Virtual DOM note` |
| `docs`, `chore(ci)`, `test` | `chore(ci): cache setup-python` |

Check your messages before you push. If the git-workflow skill is installed in your agent, `/fsd:commit` writes and checks them for you:

```bash
python skills/git-workflow/scripts/commit_check.py --range origin/main..HEAD
```

The workflow:
- Keep each PR focused on one concern, and fill in the PR template.
- Add your change under **Unreleased** in [`CHANGELOG.md`](./CHANGELOG.md).
- CI must be green. Maintainers aim to review within a week; expect suggestions, because that's how quality stays high.
- PRs are squash-merged, and you're credited in the commit.

Be kind and constructive. This project follows the [Code of Conduct](./CODE_OF_CONDUCT.md).

---

## Releases

Maintainers only:
1. Bump the version in `package.json` and `package-lock.json` (`npm version <x.y.z> --no-git-tag-version`). Move the **Unreleased** changelog entries under the new version.
2. Commit with `chore(release): vX.Y.Z`, then tag and push: `git tag vX.Y.Z && git push --tags`.
3. The [Release workflow](./.github/workflows/release.yml) then:
   - verifies that all the versions match;
   - runs the full suite;
   - packs the package and creates a GitHub Release with generated notes;
   - publishes to npm if an `NPM_TOKEN` secret is configured.

---

## License

- Code, tooling, skill, agents and data: [MIT](./LICENSE).
- Learning notes in `notes/`: [CC BY 4.0](./LICENSE-NOTES.md).
- Companion skills belong to their authors. See [THIRD_PARTY.md](./THIRD_PARTY.md).

By contributing, you agree that your contributions are licensed under these terms.
