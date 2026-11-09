'use strict';

/**
 * Third-party companion skills (companions.json), installed with THEIR official installers.
 * planCompanions() resolves commands for the selected tools; runCompanions() executes them.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
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

/** Runs each planned companion; one failure doesn't stop the others. */
function runCompanions(plan, cwd, log = console.log) {
  const results = [];
  for (const c of plan.filter((p) => p.commands.length)) {
    let ok = true;
    for (const cmd of c.commands) {
      log(`\n▶ ${c.name}: ${cmd}${c.note ? `\n  ${c.note}` : ''}`);
      const r = spawnSync(cmd, { cwd, stdio: 'inherit', shell: true, env: process.env });
      if (r.status !== 0) ok = false;
    }
    results.push({ id: c.id, name: c.name, ok, commands: c.commands });
  }
  return results;
}

module.exports = { COMPANIONS, planCompanions, runCompanions };
