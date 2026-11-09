'use strict';

/**
 * Third-party companion skills (companions.json), installed with THEIR official installers.
 * planCompanions() resolves commands for the selected tools; runCompanions() executes them in parallel.
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { PKG_ROOT, versionGte } = require('./util');
const { ADAPTERS } = require('./adapters');

const COMPANIONS = JSON.parse(fs.readFileSync(path.join(PKG_ROOT, 'companions.json'), 'utf8')).companions;

function planCompanions(tools, { global = false, ids = null } = {}) {
  const unique = (xs) => [...new Set(xs)];
  return COMPANIONS.filter((c) => (ids ? ids.includes(c.id) : c.default)).map((c) => {
    const supported = tools.filter((t) => c.agents[t]);
    if (!supported.length) return { ...c, commands: [], skip: `not available for ${tools.join(', ')}` };
    if (c.requires_node && !versionGte(process.versions.node, c.requires_node)) {
      return { ...c, commands: [], skip: `needs Node ≥ ${c.requires_node} (you have ${process.versions.node})` };
    }
    // Mirror where our own files go: --global only applies to tools whose adapter supports it.
    const isGlobal = (t) => global && !!(ADAPTERS[t] && ADAPTERS[t].global);
    const groups = [true, false]
      .map((g) => ({ global: g, agents: unique(supported.filter((t) => isGlobal(t) === g).map((t) => c.agents[t])) }))
      .filter((g) => g.agents.length);
    const fill = (tpl, g, agent = '') =>
      tpl
        .replace('{global}', g.global ? c.global_flag || '' : '')
        .replace('{skills_global}', g.global ? c.skills_global_flag || '' : '')
        .replace('{providers}', g.agents.join(','))
        .replace('{skills_agents}', g.agents.join(' '))
        .replace('{scope}', g.global ? 'global' : 'project')
        .replace('{agent}', agent);
    const commands = groups.flatMap((g) => (c.runner === 'per-agent' ? g.agents.map((a) => fill(c.command, g, a)) : [fill(c.command, g)]));
    return { ...c, commands };
  });
}

/** `npx --yes skills@1.7.6 add …` → `skills`; any other command is its own lane. */
const npxPackage = (cmd) => (cmd.match(/^npx --yes ((?:@[\w.-]+\/)?[\w.-]+)@/) || [, cmd])[1];

/**
 * Groups commands into lanes that may run at the same time. Commands for the same npx package
 * share a lane and run in order: concurrent first-time installs of one package race on npx's cache folder.
 */
function lanes(plan) {
  const byPkg = new Map();
  for (const c of plan.filter((p) => p.commands.length)) {
    for (const cmd of c.commands) byPkg.set(npxPackage(cmd), [...(byPkg.get(npxPackage(cmd)) || []), { companion: c, cmd }]);
  }
  return [...byPkg.values()];
}

/** Runs one command with buffered output (so parallel runs don't interleave) and no stdin (so a prompt fails fast instead of hanging). */
function exec(cmd, cwd) {
  return new Promise((resolve) => {
    let stdout = '';
    let stderr = '';
    const child = spawn(cmd, { cwd, shell: true, env: process.env, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout.on('data', (d) => (stdout += d));
    child.stderr.on('data', (d) => (stderr += d));
    child.on('error', (e) => resolve({ code: 1, stdout, stderr: `${stderr}${e.message}\n` }));
    child.on('close', (code) => resolve({ code, stdout, stderr }));
  });
}

/**
 * `skills add … --json` exits 0 even when a requested skill doesn't exist (e.g. after an upstream rename),
 * so read its per-skill report. Returns null when stdout isn't that report.
 */
function skillsReport(stdout) {
  let rows;
  try {
    rows = JSON.parse(stdout.slice(stdout.indexOf('[')));
  } catch {
    return null;
  }
  if (!Array.isArray(rows) || !rows.every((r) => r && typeof r.name === 'string' && typeof r.status === 'string')) return null;
  const bad = rows.filter((r) => r.status !== 'installed');
  const installed = [...new Set(rows.filter((r) => r.status === 'installed').map((r) => r.name))];
  const lines = [];
  if (installed.length) lines.push(`installed: ${installed.join(', ')}`);
  for (const r of bad) lines.push(`not installed: ${r.name} (${r.reason || r.status})`);
  return { ok: !bad.length && installed.length > 0, text: lines.join('\n') || 'no skills reported' };
}

/** Runs the planned companions in parallel lanes; output is printed per command as it finishes. One failure doesn't stop the others. */
async function runCompanions(plan, cwd, log = console.log) {
  const runnable = plan.filter((p) => p.commands.length);
  const total = runnable.reduce((n, c) => n + c.commands.length, 0);
  const failed = new Set();
  if (total) log(`\n▶ Running ${total} companion installer(s) in parallel. This can take a minute…`);
  await Promise.all(
    lanes(runnable).map(async (jobs) => {
      for (const { companion: c, cmd } of jobs) {
        const started = Date.now();
        const r = await exec(cmd, cwd);
        const report = / --json\b/.test(cmd) ? skillsReport(r.stdout) : null;
        const ok = r.code === 0 && (!/ --json\b/.test(cmd) || (report && report.ok));
        if (!ok) failed.add(c.id);
        const secs = ((Date.now() - started) / 1000).toFixed(0);
        log(`\n${ok ? '✔' : '✖'} ${c.name} (${secs}s): ${cmd}`);
        // On success show the short report; on failure show everything the installer printed.
        const out = (report && ok ? report.text : [report && report.text, r.stdout, r.stderr].filter(Boolean).join('\n')).trimEnd();
        if (out) log(out.replace(/^/gm, '  │ '));
      }
    })
  );
  return runnable.map((c) => ({ id: c.id, name: c.name, ok: !failed.has(c.id), note: c.note, commands: c.commands }));
}

module.exports = { COMPANIONS, planCompanions, runCompanions, lanes, skillsReport };
