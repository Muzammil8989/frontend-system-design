'use strict';

/** `install` command: resolve choices (wizard or flags), write files, run companions, print next steps. */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { c, fail, SHARED_SKILLS_DIR } = require('./util');
const { ADAPTERS } = require('./adapters');
const { SKILLS, byId } = require('./skills');
const { COMPANIONS, planCompanions, runCompanions } = require('./companions');
const { detectTools, detectStack } = require('./detect');
const { writeOutput } = require('./writer');

const ICON = { created: '+', appended: '+', updated: '~', overwritten: '!', unchanged: '=', skipped: '-', refused: '!' };
const COLOR = { created: c.green, appended: c.green, updated: c.cyan, overwritten: c.yellow, unchanged: c.dim, skipped: c.yellow, refused: c.red };

const csv = (v) => String(v).split(',').map((s) => s.trim()).filter(Boolean);

/** `--agent claude,cursor` → ids; `all` anywhere in the list means every adapter. */
const agentList = (v) => (csv(v).includes('all') ? Object.keys(ADAPTERS) : csv(v));

// Renamed skills: old id → current id, so existing scripts and docs keep working.
const LEGACY_SKILLS = { 'storytelling-copywriter': 'product-copywriting' };

/** `--skills a,b` → current ids, warning once per renamed id. */
function skillList(v) {
  return [...new Set(csv(v).map((id) => {
    if (!LEGACY_SKILLS[id]) return id;
    console.error(c.yellow(`warning: skill "${id}" was renamed to "${LEGACY_SKILLS[id]}"; installing that instead`));
    return LEGACY_SKILLS[id];
  }))];
}

/**
 * Validates flag values and fills defaults for non-interactive runs.
 * Third-party companions only run when asked for (--companions <ids> or --all); --yes alone never runs them.
 */
function choicesFromFlags(opts, detected) {
  let tools;
  if (opts.all) tools = Object.keys(ADAPTERS);
  else if (opts.agent) tools = agentList(opts.agent);
  else {
    tools = Object.keys(detected).filter((id) => detected[id]);
    if (!tools.length) tools = ['claude', 'agents'];
  }
  const skills = opts.skills ? skillList(opts.skills) : SKILLS.map((s) => s.id);
  let companions = [];
  if (opts.noCompanions) companions = [];
  else if (opts.companions) companions = csv(opts.companions);
  else if (opts.all) companions = COMPANIONS.filter((x) => x.default).map((x) => x.id);
  return { tools, global: !!opts.global, skills, companions };
}

function validate({ tools = [], skills = [], companions = [] }) {
  const badTools = tools.filter((t) => !ADAPTERS[t]);
  if (badTools.length) fail(`unknown tool(s): ${badTools.join(', ')} — choose from ${Object.keys(ADAPTERS).join(', ')}, all`);
  const badSkills = skills.filter((s) => !byId(s));
  if (badSkills.length) fail(`unknown skill(s): ${badSkills.join(', ')} — choose from ${SKILLS.map((s) => s.id).join(', ')}`);
  const badComp = companions.filter((id) => !COMPANIONS.some((x) => x.id === id));
  if (badComp.length) fail(`unknown companion(s): ${badComp.join(', ')} — see list-companions`);
}

/** Writes all files for the chosen tools. Returns per-tool results. */
function writeAll({ tools, skills, global }, { projectRoot, force, dryRun, log }) {
  const written = new Map(); // path+root → result (shared .agents/skills is written once)
  const report = [];
  for (const id of tools) {
    const adapter = ADAPTERS[id];
    const root = global && adapter.global ? os.homedir() : projectRoot;
    const rows = [];
    for (const out of adapter.outputs({ skills, global: global && adapter.global })) {
      const key = `${root}::${out.path}`;
      const cached = written.get(key);
      const r = cached || writeOutput(root, out, { force, dryRun });
      written.set(key, r);
      rows.push(cached ? { ...r, shared: true } : r);
    }
    report.push({ id, label: adapter.label, root, rows });
  }

  // Human-friendly summary: collapse skill folders into one line each
  for (const { label, root, rows } of report) {
    log(`\n${c.bold(label)} ${c.dim(`→ ${root === os.homedir() ? '~' : root}`)}`);
    const groups = new Map();
    for (const r of rows) {
      const m = r.path.match(/^(.*?skills\/[^/]+)\//);
      if (m) {
        const g = groups.get(m[1]) || { files: 0, changed: 0, skipped: 0, shared: false };
        g.files++;
        if (r.shared) g.shared = true;
        if (r.action === 'skipped' || r.action === 'refused') g.skipped++;
        else if (r.action !== 'unchanged') g.changed++;
        groups.set(m[1], g);
      } else {
        log(`  ${COLOR[r.action](ICON[r.action])} ${r.path} ${c.dim(r.action + (r.reason ? ` (${r.reason})` : '') + (r.dryRun ? ' (dry run)' : ''))}`);
      }
    }
    for (const [dir, g] of groups) {
      if (g.shared) {
        log(`  ${c.dim('=')} ${dir}/ ${c.dim('skill — shared with the tools above')}`);
        continue;
      }
      const state = g.changed ? c.green('+') : g.skipped ? c.yellow('-') : c.dim('=');
      log(`  ${state} ${dir}/ ${c.dim(`skill — ${g.files} files${g.changed ? '' : g.skipped ? `, ${g.skipped} kept (local changes)` : ', unchanged'}`)}`);
    }
  }
  return report;
}

async function confirmCompanions(plan, opts, log) {
  const runnable = plan.filter((x) => x.commands.length);
  log(`\n${c.bold('Companion skills')} ${c.dim('(third-party, official installers)')}`);
  for (const x of plan) {
    log(`  ${x.skip ? c.yellow('-') : c.cyan('•')} ${x.name} ${c.dim(`· ${x.license} · ${x.repo}`)}`);
    if (x.skip) log(`      ${c.yellow(`skipped: ${x.skip}`)}`);
    for (const cmd of x.commands) log(`      ${c.dim('$ ' + cmd)}`);
  }
  if (!runnable.length || opts.dryRun) {
    if (opts.dryRun && runnable.length) log(c.dim('  Dry run: commands not executed.'));
    return false;
  }
  if (opts.yes || opts.confirmedInWizard) return true;
  if (!process.stdin.isTTY) {
    log(c.yellow('  Skipped (no terminal to confirm). Re-run with --yes to install them, or --no-companions.'));
    return false;
  }
  const p = require('@clack/prompts');
  const ok = await p.confirm({ message: `Run these ${runnable.reduce((n, x) => n + x.commands.length, 0)} command(s)?`, initialValue: true });
  return ok === true;
}

function nextSteps(tools, skills, global, log) {
  const fsd = skills.includes('frontend-system-design');
  const copy = skills.includes('product-copywriting');
  log(`\n${c.bold('Try it')}`);
  if (tools.includes('claude')) {
    log(`  Claude Code   ${[fsd && '/fsd:design "your product"', fsd && '/fsd:audit', fsd && '/fsd:learn event loop', copy && '/fsd:copy landing page'].filter(Boolean).map(c.cyan).join(' · ')}`);
  }
  if (tools.includes('copilot')) log(`  Copilot Chat  ${skills.flatMap((s) => byId(s).commands).map((x) => c.cyan(`/fsd-${x}`)).join(' · ')}`);
  for (const t of ['cursor', 'windsurf', 'gemini', 'agents'].filter((x) => tools.includes(x))) {
    log(`  ${(t === 'agents' ? 'Codex / other' : ADAPTERS[t].label).padEnd(13)} just ask, e.g. "design the frontend for a booking app" or "rewrite our hero copy"`);
  }
  if (fsd) {
    const dir = tools.includes('claude') ? `${global ? '~/' : ''}.claude/skills/frontend-system-design` : `${SHARED_SKILLS_DIR}/frontend-system-design`;
    log(`  Python        ${c.cyan(`python3 ${dir}/scripts/recommend.py "your product"`)}`);
  }
}

async function install(opts) {
  const log = opts.quiet ? () => {} : console.log;
  const projectRoot = path.resolve(opts.dir || process.cwd());
  if (!fs.existsSync(projectRoot)) fail(`target directory does not exist: ${projectRoot}`);

  const detected = detectTools(projectRoot);
  const interactive = process.stdin.isTTY && process.stdout.isTTY && !opts.yes && !opts.all && !opts.ci;
  let choices;
  if (interactive) {
    const { runWizard } = require('./wizard');
    choices = await runWizard({ tools: detected, stack: detectStack(projectRoot), opts });
    opts.confirmedInWizard = true;
  } else {
    choices = choicesFromFlags(opts, detected);
  }
  validate(choices);

  if (!interactive) log(`${c.bold('Frontend System Design')} → ${choices.tools.map((t) => ADAPTERS[t].label).join(', ')}${opts.dryRun ? c.yellow('  (dry run)') : ''}`);

  const report = writeAll(choices, { projectRoot, force: !!opts.force, dryRun: !!opts.dryRun, log });
  const rows = report.flatMap((r) => r.rows);
  const skipped = rows.filter((r) => r.action === 'skipped').length;
  if (skipped) log(c.yellow(`\n${skipped} file(s) have local changes and were kept — re-run with --force to overwrite.`));
  const refused = rows.filter((r) => r.action === 'refused');
  for (const r of refused) log(c.red(`\n✖ Not written: ${r.path} (${r.reason}). Check where that link points, remove it, then re-run.`));

  let companionResults = [];
  if (choices.companions.length) {
    const plan = planCompanions(choices.tools, { global: choices.global, ids: choices.companions });
    if (await confirmCompanions(plan, opts, log)) companionResults = runCompanions(plan, projectRoot, log);
  } else if (!interactive && !opts.noCompanions) {
    log(c.dim('\nCompanion skills (third-party) were not installed. To add them: --companions <ids> (see list-companions) or --all.'));
  }

  nextSteps(choices.tools, choices.skills, choices.global, log);
  for (const r of companionResults) log(`  ${r.ok ? c.green('✔') : c.red('✖')} ${r.name}${r.ok ? '' : c.dim(` failed — run manually: ${r.commands.join(' && ')}`)}`);
  if (interactive) require('@clack/prompts').outro(opts.dryRun ? 'Dry run complete — nothing was written.' : 'Done. Happy building!');
  else log('');
  if (companionResults.some((r) => !r.ok) || refused.length) process.exitCode = 1;
  return { choices, report, companionResults };
}

module.exports = { install, choicesFromFlags, writeAll, validate, agentList, skillList };
