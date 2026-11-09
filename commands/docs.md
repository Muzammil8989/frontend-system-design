---
description: Write or refresh the project's docs — architecture, system design, design tokens, color, typography, components and quality — from the code and the design doc
argument-hint: "[what changed, or a docs file to focus on] (default: the whole set)"
---

Write or refresh the project docs for this project. Focus: **$ARGUMENTS** (if empty, the whole set).

Use the `frontend-system-design` skill and follow `references/templates/project-docs.md`: its rules, layout and file skeletons.

1. **Gather facts (read only).**
   - Run the skill's `scripts/detect_stack.py .` and read the stack and platform files it lists. Use `python3`, or `py`/`python` on Windows.
   - Read `docs/frontend-system-design.md` if it exists. It holds the decisions and their reasons.
   - Find the real values in the code: theme or Tailwind config, CSS custom properties, any token file, font loading, routes, the data layer, `package.json` (or the platform's manifest) versions, and the folder tree.
   - List the existing files under `docs/`.
2. **Tokens first.**
   - If the project has its own token file, document that file. Otherwise write `docs/design-system/tokens.json` in the format of `references/templates/tokens.example.json`, filled with the project's real values, or with the design doc's proposed values marked **Proposed**.
   - Run `scripts/tokens_check.py <token file>` and fix any contrast failure before you document it. If the fix changes a color, say which one and why.
3. **Write the docs.**
   - Fill each file from the template. Mark every row **In code** (with `path:line`), **Proposed** or **TBD**.
   - Paste the contrast and type-scale tables from `tokens_check.py`, and the budget table from `scripts/budget.py --from '<product>'`. Pass the user's text as one single-quoted argument.
   - Use Mermaid for the context diagram and the key flows.
   - When a file already exists, update the sections you own, keep the user's other text, and ask before replacing anything you would lose.
4. **Report.**
   - List the files you created or updated.
   - List the gaps: values the docs mark TBD, and places where the code and the design doc disagree.
   - Name 1–3 project notes from `references/knowledge/INDEX.md` worth reading next (for example `design-tokens.md` for tokens).
