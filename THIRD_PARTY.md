# Third-party companion skills

`npx github:Muzammil8989/frontend-system-design install` can also install these skills. Each one is installed with **its own official installer**, straight from its source. None of their code is copied into or redistributed by this repository. Each is governed by its own license.

| Companion | What it adds | License | Source | Install command used |
|---|---|---|---|---|
| UI UX Pro Max | Searchable UI styles, palettes, font pairings, UX guidelines | MIT | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `npx ui-ux-pro-max-cli init --ai <agent>` |
| Impeccable | Design polish, critique and audit commands, anti-pattern detection | Apache-2.0 | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | `npx impeccable install --providers=… --scope=…` |
| Vercel agent-skills | `vercel-react-best-practices`, `web-design-guidelines`, `vercel-composition-patterns` | MIT | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | `npx skills add vercel-labs/agent-skills --skill … --agent …` |
| Anthropic frontend-design | Distinctive, intentional visual direction for new UI | See upstream `LICENSE.txt` | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | `npx skills add anthropics/skills --skill frontend-design --agent …` |
| Cloudflare security-audit (optional) | Multi-phase codebase security audits with independently verified, machine-readable findings | MIT | [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) | `npx skills add cloudflare/security-audit-skill --skill security-audit --agent …` |

The first four are **recommended**: the wizard pre-selects them and `--all` installs them. **Optional** companions are offered in a second step, unselected. Cloudflare security-audit expects an agent with parallel subagents, and its README asks for an OS-enforced sandbox before it runs any of the audited project's code.

Supported tools per companion follow each project's documentation. UI UX Pro Max and the `npx skills` packs also cover Windsurf and Gemini CLI. Impeccable is mapped to Claude Code, Cursor and Codex. The skills.sh CLI (`npx skills`) requires Node.js ≥ 22.20. On older Node versions the installer skips those companions and tells you how to install them later.

To opt out, pass `--no-companions`. To choose specific ones, pass `--companions ui-ux-pro-max,impeccable,security-audit`. The source of truth is [`companions.json`](./companions.json). To propose adding or removing a companion, open a [Skill improvement issue](https://github.com/Muzammil8989/frontend-system-design/issues/new?template=skill-improvement.yml).
