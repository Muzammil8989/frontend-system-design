# Security Policy

## Supported versions

Only the latest release on `main` receives fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Report them privately through [GitHub Security Advisories](https://github.com/Muzammil8989/frontend-system-design/security/advisories/new).

Include:
- what is affected (installer, Python scripts, skill content, or a companion integration);
- steps to reproduce;
- the impact you expect.

You'll get an acknowledgement within 7 days.

## Scope notes

- **Installer (`bin/cli.js`).** It writes files only inside the target project, or into `~/.claude` with `--global`. It refuses to write through a symlink (a file, or any folder above it) that is dangling or points outside the target folder. It runs third-party commands **only** for the companion skills listed in [`companions.json`](./companions.json), each pinned to an exact package version (CI enforces this). The commands are always printed first; the wizard shows them before you confirm, and `--yes` runs them only when you also pass `--all` or `--companions <ids|all>`. Companions with extra risk (Cloudflare security-audit runs parallel subagents and should audit code only in a sandbox) print a warning before they run. Use `--no-companions` to run nothing external, and `--dry-run` to preview.
- **Python scripts.** Standard library only. No network access, and nothing is executed from scanned projects; `audit_scan.py` only reads files. `commit_check.py --range` runs `git log` with list-form arguments (no shell) and rejects ranges that start with `-`.
- **Guardrail hooks (`--hooks`, opt-in).** `hooks/fsd-guard.js` is a Claude Code PreToolUse hook. It reads the proposed shell command, denies force-push, `--no-verify` and commits of likely secret files, and asks the user before other risky git commands. It runs only `git diff --name-only` (argument array, no shell) to see staged files, makes no network calls, and **fails open**: on any error it lets the command through, so a guard bug never blocks work. The settings file is merged, never replaced. The git `commit-msg` hook is skipped when another hook manager or hook is present.
- **MCP server (`mcp`).** Local stdio only; no network calls of its own. Tools read only inside the folder given with `--dir` (default: the working directory): paths are resolved, symlinks included, and anything outside is refused. Scripts run with an argument array (no shell), with option values placed after `--`, a 60-second timeout and capped output. `--mcp` only merges our own server entry into existing config files and refuses files it cannot parse.
- **Git workflow skill.** It instructs agents never to push, force-push, rewrite shared history, delete branches or skip hooks without an explicit request, never to commit secrets, and to revoke a leaked secret before cleaning history.
- **Companion skills** are third-party projects. Report vulnerabilities in them to their maintainers. The links are in [THIRD_PARTY.md](./THIRD_PARTY.md).
