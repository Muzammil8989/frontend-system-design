---
description: Design a professional frontend/app system for your problem — web, mobile or desktop, any stack — with a parallel team of specialist agents
argument-hint: "<your problem or product, e.g. 'offline-first field-service app for 2k technicians'>"
---

Design the frontend system for this problem: **$ARGUMENTS**

Use the `frontend-system-design` skill. You are the lead architect and you orchestrate the team.

1. **Understand the problem (you).**
   - Restate the problem in 2–3 lines: who has it, what they need to get done, and what makes it hard.
   - If there is a codebase, run the skill's `scripts/detect_stack.py .` and read the stack and platform files it lists.
   - Run `scripts/recommend.py '<the problem>'`, adding `--project .` when code exists. Use `python3`, or `py`/`python` on Windows. Pass the user's text as one single-quoted argument (escape any `'` inside it); never put it in double quotes, where `$(…)` and backticks would run.
   - Match the problem to the closest **system design case** in `references/knowledge/INDEX.md` and the closest product playbook, and use them as the starting pattern.
   - Ask only the 3–5 questions that would change the architecture. Otherwise state your assumptions.
   - Write the **Requirements summary** from `references/core/requirements.md`, including the **platform**: web, mobile, desktop, or cross-platform.
2. **Specialists, in parallel.** Launch these subagents in a single message, giving each the requirements summary, the recommend.py output and the detected stack:
   - `ui-designer`: UI system (direction, tokens, components, key screens and their states)
   - `performance-engineer`: budgets per platform, LCP/INP/CLS or startup/frame plan, loading strategy
   - `accessibility-specialist`: WCAG 2.2 AA plan (plus VoiceOver/TalkBack for apps)
   - `security-reviewer`: client security model
   - `mobile-engineer`: **only if the platform includes mobile or desktop.** Covers the native vs cross-platform decision, app architecture, offline and sync, and release.
   - `copywriter`: hero, onboarding and empty-state copy that tells the product's story, **if** the `product-copywriting` skill is installed

   If subagents are unavailable, do each role yourself, in sequence.
3. **Architecture (you, while the specialists work).** Cover:
   - rendering or app model per route or screen;
   - stack, chosen with `references/stacks/<stack>.md`;
   - the **project folder structure**, taken from that stack file and tailored to this problem;
   - the state split, data and API, real-time, and the trade-off tables.
4. **Ground every decision.**
   - Each trade-off row gets a **"Why — learn more"** cell citing the project note behind it (`references/knowledge/<note>.md`), or the reference section when no note exists yet.
   - Read the note before citing it, by section: line 2 of each note maps its sections to line ranges, so read *Key Points Summary* and *Cheat Sheet*, not the whole file.
   - Don't state versions, benchmarks or browser support you haven't verified. If no note or reference covers a decision, say so in the cell.
5. **Synthesize.**
   - Merge everything into one doc using `references/templates/design-doc-template.md`.
   - Resolve conflicts between specialists explicitly.
   - Add the phased rollout and the risks.
6. **Deliver.**
   - Save the doc to `docs/frontend-system-design.md`. Ask before overwriting an existing file.
   - Write the **project docs** next to it, following `references/templates/project-docs.md`: `docs/README.md`, `architecture.md`, `system-design.md`, `quality.md` and `docs/design-system/` (README, `tokens.json`, tokens, color, typography, components). Values come from the design doc and stay marked **Proposed** until they are built. Run `scripts/tokens_check.py docs/design-system/tokens.json` and fix any contrast failure before you save.
   - Show a summary: the headline decisions, 3 decisions for the user to confirm, and the notes to read to understand the design.
   - Offer to scaffold phase 1 using the folder structure. Later, `/fsd:docs` refreshes the project docs from the code.
