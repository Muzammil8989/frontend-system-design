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

- **Installer (`bin/cli.js`).** It writes files only inside the target project, or into `~/.claude` with `--global`. It refuses to write through a symlink (a file, or any folder above it) that is dangling or points outside the target folder. It runs third-party commands **only** for the companion skills listed in [`companions.json`](./companions.json), each pinned to an exact package version (CI enforces this). The commands are always printed first; the wizard shows them before you confirm, and `--yes` runs them only when you also pass `--companions <ids>` or `--all`. Use `--no-companions` to run nothing external, and `--dry-run` to preview.
- **Python scripts.** Standard library only. No network access, and nothing is executed from scanned projects; `audit_scan.py` only reads files.
- **Companion skills** are third-party projects. Report vulnerabilities in them to their maintainers. The links are in [THIRD_PARTY.md](./THIRD_PARTY.md).
