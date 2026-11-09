#!/usr/bin/env node
'use strict';

/**
 * Validates everything the installer distributes:
 *   - every skill in skills/ (frontmatter, size, referenced files exist, data present)
 *   - stack reference files follow the shared template headings
 *   - agents/ and commands/ frontmatter, and that the installer catalog (src/cli/skills.js) matches them
 *   - plugin manifests and companion registry
 * Zero dependencies. Exit code 1 on any error.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const errors = [];
const warnings = [];
let checked = 0;

const rel = (p) => path.relative(ROOT, p).split(path.sep).join('/');
const err = (file, msg) => errors.push(`${rel(file)}: ${msg}`);
const warn = (file, msg) => warnings.push(`${rel(file)}: ${msg}`);
const read = (f) => fs.readFileSync(f, 'utf8').replace(/\r\n/g, '\n');

function frontmatter(file) {
  const text = read(file);
  const m = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) {
    err(file, 'missing YAML frontmatter');
    return { meta: {}, body: text };
  }
  const meta = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([\w-]+):\s*(.*)$/);
    if (kv) meta[kv[1]] = kv[2].trim();
  }
  return { meta, body: text.slice(m[0].length) };
}

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.name === '__pycache__' || e.name.startsWith('.')) return [];
    const abs = path.join(dir, e.name);
    return e.isDirectory() ? walk(abs) : [abs];
  });
}

function json(file) {
  checked++;
  try {
    return JSON.parse(read(file));
  } catch (e) {
    err(file, `invalid JSON: ${e.message}`);
    return null;
  }
}

/* 1. Skills */
const STACK_HEADINGS = ['## When to choose', '## Project structure', '## Routing & navigation', '## State & data', '## Styling & design system',
  '## Performance', '## Accessibility', '## Testing', '## Build & deploy', '## Pitfalls', '## References'];

const skillsDir = path.join(ROOT, 'skills');
const skillIds = fs.readdirSync(skillsDir).filter((d) => fs.existsSync(path.join(skillsDir, d, 'SKILL.md')));
for (const id of skillIds) {
  const dir = path.join(skillsDir, id);
  const skillFile = path.join(dir, 'SKILL.md');
  checked++;
  const { meta, body } = frontmatter(skillFile);
  if (meta.name !== id) err(skillFile, `frontmatter name must be "${id}" (matches folder)`);
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(meta.name || '')) err(skillFile, 'name must be lowercase letters, digits and hyphens');
  if (!meta.description || meta.description.length < 80) err(skillFile, 'description must be a specific trigger description (≥ 80 chars)');
  if (meta.description && meta.description.length > 1024) err(skillFile, `description is ${meta.description.length} chars (max 1024)`);
  const lines = body.split('\n').length;
  if (lines > 500) warn(skillFile, `SKILL.md body is ${lines} lines; keep it under ~500 and move detail to references/`);

  // Every `references/…`, `scripts/…`, `data/…` path mentioned anywhere in the skill must exist
  const files = walk(dir).filter((f) => f.endsWith('.md'));
  for (const file of files) {
    const text = read(file);
    for (const m of text.matchAll(/(?:^|[\s`(|"])((?:references|scripts|data)\/[\w./-]+\.(?:md|py|csv|json))/g)) {
      checked++;
      const target = m[1];
      if (!fs.existsSync(path.join(dir, target))) err(file, `mentions "${target}" which does not exist in skills/${id}/`);
    }
    // Relative markdown links inside references must resolve
    for (const m of text.matchAll(/\]\((\.{1,2}\/[^)#\s]+)/g)) {
      checked++;
      if (!fs.existsSync(path.resolve(path.dirname(file), m[1]))) err(file, `broken relative link ${m[1]}`);
    }
  }

  // Stack files follow the shared template
  const stacksDir = path.join(dir, 'references', 'stacks');
  if (fs.existsSync(stacksDir)) {
    for (const f of fs.readdirSync(stacksDir).filter((x) => x.endsWith('.md'))) {
      const file = path.join(stacksDir, f);
      checked++;
      const text = read(file);
      const pos = STACK_HEADINGS.map((h) => text.indexOf(`\n${h}\n`));
      const missing = STACK_HEADINGS.filter((_, i) => pos[i] < 0);
      if (missing.length) err(file, `missing headings: ${missing.join(', ')}`);
      else if (pos.some((p, i) => i && p < pos[i - 1])) err(file, 'template headings out of order');
      if (!text.includes('```text')) err(file, 'project structure needs a ```text folder tree');
      if (!/\*\*Platform:\*\*/.test(text)) err(file, 'missing "> **Platform:** …" summary line');
    }
  }

  // Data CSVs present and non-trivial
  const dataDir = path.join(dir, 'data');
  if (fs.existsSync(dataDir)) {
    for (const f of fs.readdirSync(dataDir).filter((x) => x.endsWith('.csv'))) {
      checked++;
      if (read(path.join(dataDir, f)).trim().split('\n').length < 3) err(path.join(dataDir, f), 'dataset is empty');
    }
  }
}

/* 2. Agents and commands, and the installer catalog */
const agentNames = new Set();
for (const kind of ['agents', 'commands']) {
  for (const f of fs.readdirSync(path.join(ROOT, kind)).filter((x) => x.endsWith('.md'))) {
    const file = path.join(ROOT, kind, f);
    checked++;
    const { meta, body } = frontmatter(file);
    if (!meta.description) err(file, 'missing description');
    if (kind === 'agents') {
      if (meta.name !== f.replace(/\.md$/, '')) err(file, `name "${meta.name}" must match the file name`);
      if (!meta.tools) warn(file, 'no tools list — agent inherits every tool');
      if (/reviewer|auditor/.test(meta.name) && /\b(Write|Edit)\b/.test(meta.tools || '')) err(file, 'reviewer agents must be read-only (no Write/Edit)');
      agentNames.add(meta.name);
    } else if (!body.includes('$ARGUMENTS')) warn(file, 'command never uses $ARGUMENTS');
    if (body.trim().length < 200) err(file, 'body is too short to be useful');
  }
}
for (const f of fs.readdirSync(path.join(ROOT, 'commands'))) {
  const text = read(path.join(ROOT, 'commands', f));
  for (const m of text.matchAll(/^\s*- `([a-z]+(?:-[a-z]+)+)`:/gm)) {
    if (!agentNames.has(m[1])) err(path.join(ROOT, 'commands', f), `references unknown agent "${m[1]}"`);
  }
}
const { SKILLS } = require('../src/cli/skills');
const catalogFile = path.join(ROOT, 'src', 'cli', 'skills.js');
for (const s of SKILLS) {
  checked++;
  if (!skillIds.includes(s.id)) err(catalogFile, `catalog lists skill "${s.id}" but skills/${s.id}/SKILL.md is missing`);
  for (const a of s.agents) if (!agentNames.has(a)) err(catalogFile, `${s.id}: agent "${a}" has no agents/${a}.md`);
  for (const cmd of s.commands) if (!fs.existsSync(path.join(ROOT, 'commands', `${cmd}.md`))) err(catalogFile, `${s.id}: command "${cmd}" has no commands/${cmd}.md`);
}
for (const id of skillIds) if (!SKILLS.some((s) => s.id === id)) err(catalogFile, `skills/${id} exists but is not in the installer catalog`);
const catalogued = new Set(SKILLS.flatMap((s) => s.agents));
for (const a of agentNames) if (!catalogued.has(a)) err(catalogFile, `agents/${a}.md is not installed by any skill`);

/* 3. Manifests & registry */
const pkg = json(path.join(ROOT, 'package.json'));
const lock = json(path.join(ROOT, 'package-lock.json'));
if (lock && pkg && (lock.version !== pkg.version || (lock.packages && lock.packages[''] && lock.packages[''].version !== pkg.version))) {
  err(path.join(ROOT, 'package-lock.json'), `version ${lock.version} ≠ package.json ${pkg.version} — run: npm install --package-lock-only`);
}

const reg = json(path.join(ROOT, 'companions.json'));
const { ADAPTERS } = require('../src/cli/adapters');
if (reg) {
  const where = path.join(ROOT, 'companions.json');
  const ids = new Set();
  for (const c of reg.companions) {
    for (const k of ['id', 'name', 'repo', 'license', 'purpose', 'command', 'agents', 'runner']) if (!c[k]) err(where, `${c.id || '?'}: missing "${k}"`);
    if (ids.has(c.id)) err(where, `duplicate id ${c.id}`);
    ids.add(c.id);
    if (!/^https:\/\/github\.com\//.test(c.repo || '')) err(where, `${c.id}: repo must be a GitHub https URL`);
    if (!['once', 'per-agent'].includes(c.runner)) err(where, `${c.id}: runner must be once|per-agent`);
    if (/[;&|`$<>]/.test((c.command || '').replace(/\{\w+\}/g, ''))) err(where, `${c.id}: command contains shell metacharacters`);
    // Companion installers run third-party code on users' machines: pin an exact version so a hijacked release isn't picked up.
    const npx = (c.command || '').match(/^npx\s+(?:--?\S+\s+)*(\S+)/);
    if (!npx) err(where, `${c.id}: command must start with "npx <package>@<version>"`);
    else if (!/^(?:@[\w.-]+\/)?[\w.-]+@\d+\.\d+\.\d+$/.test(npx[1])) err(where, `${c.id}: pin "${npx[1]}" to an exact version, e.g. ${npx[1].replace(/@[^/]*$/, '')}@1.2.3`);
    for (const a of Object.keys(c.agents || {})) if (!ADAPTERS[a]) err(where, `${c.id}: unknown tool key ${a}`);
  }
}

for (const w of warnings) console.log(`warning  ${w}`);
for (const e of errors) console.log(`error    ${e}`);
const summary = `${skillIds.length} skills, ${checked} checks — ${errors.length} error(s), ${warnings.length} warning(s)`;
console.log(errors.length ? `\n✖ ${summary}` : `\n✔ ${summary}`);
process.exitCode = errors.length ? 1 : 0;
