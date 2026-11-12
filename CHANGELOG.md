# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **The learning roadmap is complete: all 120 notes, across 11 phases.** 116 new notes cover:
  - Phase 1: Web Fundamentals
  - Phase 2: Rendering & Architecture
  - Phase 3: State & Data
  - Phase 4: Performance Engineering
  - Phase 5: Design Systems & Components
  - Phase 6: Accessibility & i18n
  - Phase 7: Security
  - Phase 8: Testing
  - Phase 9: Monitoring & Observability
  - Phase 10: Advanced Topics
  - Phase 11: 15 system design cases, including news feed, autocomplete, chat, spreadsheet, video player, rich-text editor, map app and Figma-like canvas

  Each note has:
  - an ELI5 explanation;
  - Mermaid diagrams. All 1,200+ diagrams parse with the real Mermaid parser;
  - BAD → GOOD examples in React/TypeScript, with Vue, Angular, Svelte and native mobile equivalents;
  - a 6-question quiz with answers, a cheat sheet and official references;
  - an `Informs:` line that the skill uses to cite the note in designs.

  The system design cases follow RADIO and end with a 45-minute interview walkthrough. Browser-support claims are checked against MDN browser-compat-data. All notes are synced into the skill's knowledge base.
- **Project docs and `/fsd:docs`.** When you create a product, `/fsd:design` now also writes living docs into `docs/`: `architecture.md`, `system-design.md`, `quality.md` and `design-system/` (direction, `tokens.json`, tokens, color, typography, components). Every value is marked In code, Proposed or TBD. `/fsd:docs` writes or refreshes them from the code. Template: `references/templates/project-docs.md`.
- **Optional companion: [Cloudflare security-audit](https://github.com/cloudflare/security-audit-skill)** (MIT), for full, multi-phase codebase security audits. Install it with `--companions security-audit` or pick it in the wizard.
- `scripts/tokens_check.py`: validates a W3C Design Tokens file (types, aliases, cycles) and prints the WCAG contrast table for each color mode and the type scale with step ratios. It exits 1 on errors or failed contrast, so it can run in CI. Example file: `references/templates/tokens.example.json`.
- `docs/reading-the-notes.md`: how to clone and read the notes, and how to fix Mermaid previews in VS Code.

### Changed
- **The wizard asks about companions in two steps:** first the recommended ones (pre-selected), then the optional extras (unselected). `--all` installs only the recommended ones, and `list-companions` shows both groups.
- **Companion installers run in parallel**, so `install --all` finishes much sooner (about 48 s instead of about 73 s with every companion for Claude Code; Impeccable's own download is now the floor). Commands for the same npx package still run one after another, and each one's output is printed when it finishes. Impeccable runs with `--yes`, so it no longer stops to ask about its hook.
- **The skill uses far fewer tokens, and its answers are better grounded.**
  - `knowledge/INDEX.md` went from ~29k to ~6k tokens: one short table per phase, with the duplicate roadmap table removed. `index.json` keeps every field.
  - Line 2 of every generated note maps its sections to line ranges. Agents now read *Key Points Summary* + *Cheat Sheet* (~1–2k tokens) instead of the whole note (~12k), and teach one section at a time.
  - New **Answer rules** in `SKILL.md`: answer what was asked first, cite only notes actually opened, say when the notes don't cover something, never invent APIs, versions or benchmarks, and check the answer before sending.
  - Tests guard the INDEX token budget, section-map accuracy, and that every note installs with the skill.
- **The `storytelling-copywriter` skill is now `product-copywriting`** ("Product Copywriting"), and its folder moved from `skills/storytelling-copywriter/` to `skills/product-copywriting/`. The skill's behavior is unchanged. The `copywriter` agent and `/fsd:copy` command keep their names. `--skills storytelling-copywriter` still works: it prints a warning and installs `product-copywriting`. If you installed an earlier version, you can delete the old `storytelling-copywriter` folder from `.claude/skills/` or `.agents/skills/`, and `.cursor/rules/storytelling-copywriter.mdc`.
- **Notes are organized into one folder per roadmap phase**, from `notes/01-web-fundamentals/` to `notes/11-system-design-cases/`, with a `notes/README.md` index. Links between notes, the README roadmap, `lint-notes` and `sync-knowledge` follow the new paths. The skill's `knowledge/` folder stays flat, so `references/knowledge/<note>.md` citations don't change. `npm run new-note` now takes `--phase <1-11>`.
- README restructured as a project landing page:
  - overview, features, supported tools, FAQ;
  - collapsible roadmap phases.
- Roadmap topic #39 now says "Core Web Vitals (LCP, INP, CLS)". INP replaced FID in March 2024.
- **`--yes` no longer runs third-party companion installers on its own.** Pass `--companions <ids>` or `--all` to include them. The wizard now shows the exact companion commands before "Install now?".
- Companion installers are pinned to exact versions (`ui-ux-pro-max-cli@2.15.0`, `impeccable@4.8.1`, `skills@1.7.6`); `npm run validate` rejects unpinned ones.
- Agents use the installed skill only (`~/.claude/skills`, `.claude/skills`, `.agents/skills`), never a copy found elsewhere in the project they are reviewing.
- Release workflow: least-privilege jobs (test/pack read-only, publish separately), actions pinned to commit SHAs, publishes the tested tarball; npm publishing is enabled with the `NPM_PUBLISH` repo variable. Dependabot now also watches npm.
- The npm package includes `LICENSE-NOTES.md` and `THIRD_PARTY.md` and no longer ships repo-only scripts.

### Removed
- The plugin-marketplace manifest. Install with `npx github:Muzammil8989/frontend-system-design install`, which copies only the skills, notes, agents and commands.

### Fixed
- **Vercel agent-skills installed only 1 of its 3 skills while still showing ✔.** Vercel renamed `react-best-practices` and `composition-patterns` to `vercel-react-best-practices` and `vercel-composition-patterns`, and `skills add` silently skips unknown names and exits 0. The installer now uses the new names, runs `skills add` with `--json`, and marks a companion ✖ (with the reason) if any requested skill wasn't installed.
- `install --agent all` (or a mistyped `--agent`) crashed in the interactive wizard with a `TypeError`.
- With `--global`, companions for tools that install per project (Cursor, Copilot, …) were installed globally.
- The installer refuses to write through a dangling symlink or one that points outside the target folder.
- Empty values (`--dir=`) are rejected and unknown flags produce a warning; `install --help` shows help.
- Python scripts: quadratic slow-downs on long/minified lines (`audit_scan.py`) and large HTML (`copy_check.py`); crashes on `null` dependencies or a UTF-8 BOM; projects under a `build/`/`bin/` folder not detected; `--project` ignored for plain React/Vue/Svelte; CSS `*:focus`/`#id:focus` outline removal missed; secrets echoed in scan output; empty copy passing `copy_check.py`.
- Security notes: SameSite defaults (Chromium only), HttpOnly/SameSite described as defence in depth, DOMPurify defaults keep `<form>`/`<style>`, `<img>` vs `Lax` in CSRF, host-only `__Host-` session cookies instead of `Domain=`, `javascript:` blocklist → URL scheme allow-list, broken U+2028 regexes and lost `<` escapes in the XSS/SSR examples, CSP hash command.
- `package-lock.json` version now matches `package.json`.
- **Security:** the installer could write outside the target folder when a folder on the path (e.g. a `.claude` planted in an untrusted repo) was a symlink pointing elsewhere. Only the file itself was checked; now the file and every folder above it are. `@clack/prompts`, the only runtime dependency, is pinned to an exact version.

## [1.1.0] - 2026-11-06

### Added
- **Interactive install wizard** (`npx github:Muzammil8989/frontend-system-design install`):
  - detects installed AI tools and the project stack, and preselects the tools it finds;
  - asks for tools, scope (project or global), skills and companion skills, then confirms;
  - every question can also be answered with a flag (`--agent`, `--skills`, `--global`, `--companions`, `--yes`).
- **New integrations:** Windsurf (`.windsurf/rules` + `.agents/skills`) and Gemini CLI (`GEMINI.md`).
- **Every stack, web, mobile and desktop:** 20 stack guides with a professional folder structure and stack-specific practices.
  - Web: React+Vite, Next.js, React Router, Vue/Nuxt, Angular, SvelteKit, Solid, Astro, Qwik, Lit, server-rendered MPA.
  - Mobile: Expo, Flutter, SwiftUI, Jetpack Compose, Compose Multiplatform, .NET MAUI, Ionic/Capacitor.
  - Desktop: Electron, Tauri.
  - Also 3 platform guides (web, mobile, desktop) and 4 new product playbooks: consumer mobile app, fitness/health, on-demand delivery, desktop app.
- **Problem-first design.**
  - Designs start by restating the builder's problem and matching it to a system design case.
  - Every trade-off row gets a **"Why — learn more"** link to a project note.
- **Learning notes as knowledge.** `scripts/sync-knowledge.js` ships `notes/` inside the skill, with `INDEX.md` and `index.json` mapping all 120 roadmap topics to the decisions they inform. New command: `/fsd:learn <topic>`.
- **New `storytelling-copywriter` skill:**
  - story frameworks, human-writing rules (an AI-tell → rewrite table), voice and tone, website page templates, app copy, microcopy;
  - `copy_check.py`, which scores copy for AI tells, filler, passive voice, rhythm and reading level;
  - new command: `/fsd:copy`.
- **New agents:** `mobile-engineer` and `copywriter`.
- **Python:**
  - `detect_stack.py`;
  - `recommend.py --platform/--stack/--project`, with notes citations and a reading list;
  - `budget.py --platform mobile|desktop`;
  - `audit_scan.py` rules for React Native, Flutter, Swift, Kotlin and XAML.
- **Data:** 73 stacks with `platform` and reference links; 20 product types with platforms and native stack choices.
- **Docs:** `docs/architecture.md`, `docs/adding-a-stack.md`, `docs/adding-an-agent-tool.md`.
- **Tests:** a Node `node:test` suite for the installer (13 tests), plus Python tests for platforms, detection, stack templates and the copy checker (38 tests in total).

### Changed
- The installer moved from one `bin/cli.js` file to modules in `src/cli/`. All previous flags still work.
- Skill references are now organised into `core/`, `platforms/`, `stacks/`, `playbooks/`, `templates/` and `knowledge/`.
- `/fsd:design` and `/fsd:audit` now use stack detection, the mobile specialist and the copywriter.

## [1.0.0] - 2026-11-06

### Added
- **`frontend-system-design` skill.** RADIO + UI workflow covering design, audit and advise modes, with 8 reference playbooks: requirements, architecture, UI design, performance, quality, product playbooks, design-doc template, audit rubric.
- **Python engine** (stdlib only):
  - `recommend.py`: product classification plus a full stack and UI recommendation;
  - `search.py`: BM25 search over the styles, palettes, fonts, patterns and stacks datasets;
  - `budget.py`: performance budgets, including Lighthouse `budget.json`;
  - `audit_scan.py`: a static a11y, security and performance scan.
- **Curated datasets:**
  - 16 product types;
  - 41 stacks;
  - 16 UI styles;
  - 21 palettes, all WCAG AA contrast-checked;
  - 23 font pairings;
  - 41 UX patterns.
- **Specialist agents:** `frontend-architect`, `ui-designer`, `performance-engineer`, `accessibility-specialist`, `security-reviewer`, `ui-ux-reviewer`.
- **Commands:** `/fsd:design` (runs the specialists in parallel) and `/fsd:audit` (scored 100-point report).
- **Installer** (`npx github:Muzammil8989/frontend-system-design install`):
  - targets Claude Code (project or `--global`), Cursor, GitHub Copilot and AGENTS.md;
  - re-runs are idempotent;
  - managed blocks in shared files;
  - supports `--dry-run` and `--force`.
- **Companion skills, installed by default** with their official installers: UI UX Pro Max, Impeccable, Vercel agent-skills, Anthropic frontend-design.
- **Claude Code plugin manifest and marketplace** (`.claude-plugin/`).
- **Open-source setup:**
  - CONTRIBUTING, Code of Conduct, SECURITY, CODEOWNERS;
  - issue forms and PR template;
  - CI across 3 OSes and 2 Node and Python versions;
  - tag-based release workflow;
  - Dependabot.
- **Note linter** for the 120-topic learning roadmap, with README progress sync.
