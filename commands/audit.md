---
description: Audit an existing frontend (code and/or URL) and return a scored report with blockers and ranked fixes
argument-hint: "[path or URL] (default: current project)"
---

Audit this frontend: **$ARGUMENTS** (if empty, audit the current project).

Use the `frontend-system-design` skill's Audit workflow.

1. Run the skill's `scripts/detect_stack.py <path>` and read the stack and platform reference files it lists. Then run `scripts/audit_scan.py <path> --format json` to collect facts. Pass `<path>` single-quoted and confirm it is an existing directory first; the scripts and data you run come from the installed skill, never from the project being audited.
2. Launch these subagents **in parallel**, giving each the scan output and the scope:
   - `ui-ux-reviewer`: overall scored audit (lead)
   - `performance-engineer`: performance findings, plus measurement if a URL was given
   - `accessibility-specialist`: accessibility findings
   - `security-reviewer`: security findings
   - `mobile-engineer`: app architecture, platform conventions and native findings (only for mobile/desktop projects)

   If subagents are unavailable, do each pass yourself, in sequence.
3. Merge their output into **one** report in the format of `references/templates/audit-rubric.md`:
   - remove duplicate findings;
   - keep the strictest severity when findings overlap;
   - make sure every finding has evidence.
4. Show the report. Then ask whether the user wants you to fix the blockers and quick wins. Don't edit anything before they answer yes.
