'use strict';

/**
 * Interactive install wizard (shown when running in a terminal without --yes/--all).
 * Asks: AI tools → scope → skills → recommended companions → optional companions → confirm.
 * Every answer can also be given as a flag, which skips that question.
 */

const p = require('@clack/prompts');
const { c, PKG } = require('./util');
const { ADAPTERS } = require('./adapters');
const { SKILLS } = require('./skills');
const { COMPANIONS, planCompanions } = require('./companions');
const { validate, agentList, skillList } = require('./install');

function cancelled(value) {
  if (p.isCancel(value)) {
    p.cancel('Installation cancelled. Nothing was changed.');
    process.exit(0);
  }
  return value;
}

/**
 * @param {object} ctx  { tools: detectTools() result, stack, opts }
 * @returns {Promise<{tools: string[], global: boolean, skills: string[], companions: string[]|null}>}
 */
async function runWizard({ tools: detected, stack, opts }) {
  // Reject mistyped flag values before asking anything.
  const list = (v) => (v ? String(v).split(',').map((s) => s.trim()).filter(Boolean) : []);
  const flagSkills = opts.skills ? skillList(opts.skills) : null;
  validate({ tools: opts.agent ? agentList(opts.agent) : [], skills: flagSkills || [], companions: opts.noCompanions ? [] : list(opts.companions) });

  p.intro(c.bold(` Frontend System Design v${PKG.version} `));

  const found = Object.entries(detected).filter(([, why]) => why);
  p.note(
    [
      found.length ? `AI tools found: ${found.map(([id]) => ADAPTERS[id].label).join(', ')}` : 'No AI tools detected. Pick the ones you use.',
      stack ? `Project stack: ${stack}` : 'Project stack: none detected (fine for a new project)',
    ].join('\n'),
    'Detected'
  );

  const toolIds = opts.agent
    ? agentList(opts.agent)
    : cancelled(
        await p.multiselect({
          message: 'Which AI coding tools should get the skills?',
          options: Object.entries(ADAPTERS).map(([id, a]) => ({ value: id, label: a.label, hint: detected[id] || undefined })),
          initialValues: found.length ? found.map(([id]) => id) : ['claude'],
          required: true,
        })
      );
  validate({ tools: toolIds });

  let global = !!opts.global;
  if (!opts.global && !opts.dir && toolIds.some((id) => ADAPTERS[id].global)) {
    global = cancelled(
      await p.select({
        message: 'Where should Claude Code get them?',
        options: [
          { value: false, label: 'This project', hint: 'committed with the repo, shared with your team' },
          { value: true, label: 'Globally (~/.claude)', hint: 'available in every project on this machine' },
        ],
        initialValue: false,
      })
    );
  }

  const skills = flagSkills
    ? flagSkills
    : cancelled(
        await p.multiselect({
          message: 'Which skills?',
          options: SKILLS.map((s) => ({ value: s.id, label: s.label, hint: s.hint })),
          initialValues: SKILLS.map((s) => s.id),
          required: true,
        })
      );
  validate({ skills });

  let companions = [];
  if (!opts.noCompanions) {
    const available = COMPANIONS.filter((comp) => toolIds.some((t) => comp.agents[t]));
    if (opts.companions) companions = String(opts.companions).split(',').map((s) => s.trim());
    else {
      // Recommended companions first (pre-selected), then the optional extras (unselected).
      const option = (comp) => ({ value: comp.id, label: comp.name, hint: `${comp.license} · ${comp.purpose}` });
      const recommended = available.filter((comp) => comp.default);
      const optional = available.filter((comp) => !comp.default);
      if (recommended.length) {
        companions = cancelled(
          await p.multiselect({
            message: 'Recommended companion skills (third-party, via their official installers):',
            options: recommended.map(option),
            initialValues: recommended.map((comp) => comp.id),
            required: false,
          })
        );
      }
      if (optional.length) {
        companions = companions.concat(
          cancelled(
            await p.multiselect({
              message: 'Optional extras, for specific needs (space to select, enter to skip):',
              options: optional.map(option),
              initialValues: [],
              required: false,
            })
          )
        );
      }
    }
  }
  validate({ companions });

  // Show the exact third-party commands before the one confirmation that runs them.
  const commands = companions.length ? planCompanions(toolIds, { global, ids: companions }).flatMap((x) => x.commands) : [];
  p.note(
    [
      `${c.bold('Tools')}       ${toolIds.map((id) => ADAPTERS[id].label).join(', ')}`,
      `${c.bold('Scope')}       ${global ? 'global (~/.claude) + project for other tools' : 'this project'}`,
      `${c.bold('Skills')}      ${skills.join(', ')}`,
      `${c.bold('Companions')}  ${companions.length ? companions.join(', ') : 'none'}`,
      ...(commands.length ? ['', c.dim('Companion commands that will run (third-party code):'), ...commands.map((cmd) => c.dim(`  $ ${cmd}`))] : []),
    ].join('\n'),
    'Ready to install'
  );
  if (!opts.yes) {
    const ok = cancelled(await p.confirm({ message: 'Install now?', initialValue: true }));
    if (!ok) {
      p.cancel('Nothing was changed.');
      process.exit(0);
    }
  }
  return { tools: toolIds, global, skills, companions };
}

module.exports = { runWizard };
