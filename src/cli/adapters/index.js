'use strict';

/**
 * AI-tool adapters. Each adapter maps the selected skills onto the files that tool reads.
 *
 *   id, label   identity shown in the wizard
 *   global      can install for the user (all projects) instead of one project
 *   outputs()   list of { path, content } or { path, block, heading } (see writer.js)
 *
 * Tools without native subagents get the same skills through a shared `.agents/skills/` copy
 * plus a pointer (rule, prompt file or managed block) that routes requests to them.
 */

const { SHARED_SKILLS_DIR, quote, withFrontmatter } = require('../util');
const { byId, localize, skillFiles, skillMd, agentFile, commandFile } = require('../skills');

const PROMPT_INPUTS = {
  design: '${input:product:Describe the product or problem}',
  docs: '${input:focus:What changed, or a docs file to focus on (default: all)}',
  audit: '${input:target:Path or URL (default: this project)}',
  learn: '${input:topic:Topic to learn, e.g. event loop}',
  copy: '${input:page:Page or screen, e.g. landing page hero}',
  commit: '${input:hint:Optional hint, e.g. fixes #42}',
  pr: '${input:base:Base branch or issue, e.g. main}',
  undo: '${input:problem:What went wrong, e.g. committed to main}',
  release: '${input:version:Version or bump (default: from commits)}',
};

const shared = (skills) => skills.flatMap((id) => skillFiles(id, `${SHARED_SKILLS_DIR}/${id}`));
const sharedPath = (id) => `${SHARED_SKILLS_DIR}/${id}/SKILL.md`;

/** Short routing text used inside AGENTS.md / GEMINI.md / copilot-instructions.md. */
function pointerBlock(skills, { title = 'Frontend System Design skills', commands = false } = {}) {
  const lines = [`## ${title}`, ''];
  // Always loaded by these tools, so keep it short: trigger → file to read → the one rule that must not wait.
  if (skills.includes('frontend-system-design')) {
    lines.push(`- **Designing, building or auditing any web, mobile or desktop UI or frontend architecture, or learning a frontend topic:** follow \`${sharedPath('frontend-system-design')}\`.`);
  }
  if (skills.includes('product-copywriting')) {
    lines.push(`- **Writing website or app copy** (pages, onboarding, empty states, errors, store text): follow \`${sharedPath('product-copywriting')}\`. Never invent facts.`);
  }
  if (skills.includes('git-workflow')) {
    lines.push(`- **Commits, branches, PRs, undoing git mistakes, releases, changelogs:** follow \`${sharedPath('git-workflow')}\`. Commit only after the user confirms; never push unless asked.`);
  }
  if (skills.includes('frontend-system-design') || skills.includes('product-copywriting')) {
    lines.push('- No subagents? Play each specialist role in turn.');
  }
  if (commands) {
    const cmds = skills.flatMap((id) => byId(id).commands).map((c) => `\`/fsd-${c}\``);
    lines.push(`- Prompt files: ${cmds.join(', ')}.`);
  }
  return lines.join('\n');
}

const ADAPTERS = {
  claude: {
    label: 'Claude Code',
    global: true,
    outputs({ skills, global }) {
      return skills.flatMap((id) => {
        const s = byId(id);
        const dir = `.claude/skills/${id}`;
        return [
          ...skillFiles(id, dir, global ? `~/${dir}` : dir),
          ...s.agents.map((a) => ({ path: `.claude/agents/${a}.md`, content: agentFile(a) })),
          ...s.commands.map((cmd) => {
            const f = commandFile(cmd);
            return { path: `.claude/commands/fsd/${cmd}.md`, content: f.raw + f.body };
          }),
        ];
      });
    },
  },

  cursor: {
    label: 'Cursor',
    outputs({ skills }) {
      return [
        ...shared(skills),
        ...skills.map((id) => {
          const s = skillMd(id);
          return {
            path: `.cursor/rules/${id}.mdc`,
            content: withFrontmatter({ description: quote(s.meta.description), globs: '', alwaysApply: 'false' }, localize(s.body, `${SHARED_SKILLS_DIR}/${id}`)),
          };
        }),
      ];
    },
  },

  copilot: {
    label: 'GitHub Copilot (VS Code)',
    outputs({ skills }) {
      const prompts = skills.flatMap((id) =>
        byId(id).commands.map((cmd) => {
          const f = commandFile(cmd);
          const body =
            `First read \`${sharedPath(id)}\` and follow it. Subagents are not available here: perform each specialist role yourself, in sequence.\n\n` +
            localize(f.body, `${SHARED_SKILLS_DIR}/${id}`).replace(/\$ARGUMENTS/g, PROMPT_INPUTS[cmd] || '${input:args}');
          return { path: `.github/prompts/fsd-${cmd}.prompt.md`, content: withFrontmatter({ description: quote(f.meta.description) }, body) };
        })
      );
      return [
        ...shared(skills),
        { path: '.github/copilot-instructions.md', heading: '# Copilot instructions', block: pointerBlock(skills, { commands: true }) },
        ...prompts,
      ];
    },
  },

  windsurf: {
    label: 'Windsurf',
    outputs({ skills }) {
      return [
        ...shared(skills),
        ...skills.map((id) => {
          const s = skillMd(id);
          return {
            path: `.windsurf/rules/${id}.md`,
            content: withFrontmatter(
              { trigger: 'model_decision', description: quote(s.meta.description) },
              `Read \`${sharedPath(id)}\` and follow its workflow. Its references, scripts and data live next to it in \`${SHARED_SKILLS_DIR}/${id}/\`.\n`
            ),
          };
        }),
      ];
    },
  },

  gemini: {
    label: 'Gemini CLI',
    outputs({ skills }) {
      return [...shared(skills), { path: 'GEMINI.md', heading: '# GEMINI.md', block: pointerBlock(skills) }];
    },
  },

  agents: {
    label: 'Codex & other AGENTS.md tools',
    outputs({ skills }) {
      return [...shared(skills), { path: 'AGENTS.md', heading: '# AGENTS.md', block: pointerBlock(skills) }];
    },
  },
};

module.exports = { ADAPTERS, pointerBlock };
