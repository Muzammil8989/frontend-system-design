'use strict';

/** Installer tests (node:test, Node ≥ 18). Run: npm run test:node */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const { parseArgs } = require('../../src/cli/index');
const { install, choicesFromFlags, agentList } = require('../../src/cli/install');
const { CliError } = require('../../src/cli/util');
const { ADAPTERS } = require('../../src/cli/adapters');
const { SKILLS } = require('../../src/cli/skills');
const { planCompanions } = require('../../src/cli/companions');
const { detectTools, detectStack } = require('../../src/cli/detect');

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'fsd-test-'));
const quietInstall = (dir, extra = {}) => install({ dir, noCompanions: true, quiet: true, ci: true, ...extra });
const listFiles = (dir) =>
  fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? listFiles(path.join(dir, e.name)) : [path.join(dir, e.name)]));

test('parseArgs handles flags, values and short -y', () => {
  const o = parseArgs(['--agent', 'claude,cursor', '--no-companions', '--dir=/tmp/x', '-y', 'extra']);
  assert.equal(o.agent, 'claude,cursor');
  assert.equal(o.noCompanions, true);
  assert.equal(o.dir, '/tmp/x');
  assert.equal(o.yes, true);
  assert.deepEqual(o._, ['extra']);
});

test('install --all writes every integration and both skills', async () => {
  const dir = tmp();
  await quietInstall(dir, { all: true });
  const must = [
    '.claude/skills/frontend-system-design/SKILL.md',
    '.claude/skills/frontend-system-design/references/stacks/flutter.md',
    '.claude/skills/frontend-system-design/references/knowledge/INDEX.md',
    '.claude/skills/product-copywriting/scripts/copy_check.py',
    '.claude/agents/mobile-engineer.md',
    '.claude/agents/copywriter.md',
    '.claude/commands/fsd/design.md',
    '.claude/commands/fsd/learn.md',
    '.claude/commands/fsd/copy.md',
    '.agents/skills/frontend-system-design/scripts/detect_stack.py',
    '.agents/skills/product-copywriting/SKILL.md',
    '.cursor/rules/frontend-system-design.mdc',
    '.cursor/rules/product-copywriting.mdc',
    '.github/prompts/fsd-design.prompt.md',
    '.github/prompts/fsd-copy.prompt.md',
    '.windsurf/rules/frontend-system-design.md',
    'GEMINI.md',
    'AGENTS.md',
  ];
  for (const f of must) assert.ok(fs.existsSync(path.join(dir, f)), `missing ${f}`);
  assert.equal(listFiles(dir).filter((f) => f.includes('__pycache__')).length, 0);
});

test('re-running is idempotent and managed blocks are not duplicated', async () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'AGENTS.md'), '# My project rules\n\nKeep this line.\n');
  await quietInstall(dir, { all: true });
  const second = await quietInstall(dir, { all: true });
  const changed = second.report.flatMap((r) => r.rows).filter((r) => r.action !== 'unchanged');
  assert.deepEqual(changed, []);
  const agents = fs.readFileSync(path.join(dir, 'AGENTS.md'), 'utf8');
  assert.equal(agents.match(/fsd:start/g).length, 1);
  assert.match(agents, /Keep this line\./);
});

test('local edits are kept unless --force', async () => {
  const dir = tmp();
  await quietInstall(dir, { agent: 'claude' });
  const file = path.join(dir, '.claude/agents/ui-designer.md');
  fs.appendFileSync(file, '\nmy custom note\n');
  const kept = await quietInstall(dir, { agent: 'claude' });
  assert.ok(kept.report[0].rows.some((r) => r.action === 'skipped'));
  assert.match(fs.readFileSync(file, 'utf8'), /my custom note/);
  await quietInstall(dir, { agent: 'claude', force: true });
  assert.doesNotMatch(fs.readFileSync(file, 'utf8'), /my custom note/);
});

test('--dry-run writes nothing', async () => {
  const dir = tmp();
  await quietInstall(dir, { all: true, dryRun: true });
  assert.deepEqual(fs.readdirSync(dir), []);
});

test('--skills limits what is installed', async () => {
  const dir = tmp();
  await quietInstall(dir, { agent: 'claude', skills: 'product-copywriting' });
  assert.ok(fs.existsSync(path.join(dir, '.claude/skills/product-copywriting/SKILL.md')));
  assert.ok(!fs.existsSync(path.join(dir, '.claude/skills/frontend-system-design')));
  assert.ok(!fs.existsSync(path.join(dir, '.claude/agents/ui-designer.md')));
  assert.ok(fs.existsSync(path.join(dir, '.claude/agents/copywriter.md')));
});

test('unknown tools or skills fail with a clear message', async () => {
  await assert.rejects(quietInstall(tmp(), { agent: 'notepad' }), /unknown tool/);
  await assert.rejects(quietInstall(tmp(), { agent: 'claude', skills: 'nope' }), /unknown skill/);
});

test('non-Claude tools get paths that resolve inside .agents/skills', async () => {
  const dir = tmp();
  await quietInstall(dir, { agent: 'cursor,copilot' });
  const rule = fs.readFileSync(path.join(dir, '.cursor/rules/frontend-system-design.mdc'), 'utf8');
  assert.match(rule, /^---\ndescription: ".+"\nglobs: \nalwaysApply: false\n---/);
  assert.doesNotMatch(rule, /<skill-dir>/);
  for (const m of rule.matchAll(/`(\.agents\/skills\/[^`\s<>{}]+\.(?:md|py|json))`/g)) {
    assert.ok(fs.existsSync(path.join(dir, m[1])), `cursor rule points to missing ${m[1]}`);
  }
  const prompt = fs.readFileSync(path.join(dir, '.github/prompts/fsd-design.prompt.md'), 'utf8');
  assert.match(prompt, /\$\{input:product:/);
  assert.doesNotMatch(prompt, /\$ARGUMENTS/);
});

test('every adapter and catalog entry is consistent', () => {
  for (const [id, a] of Object.entries(ADAPTERS)) {
    const outs = a.outputs({ skills: SKILLS.map((s) => s.id), global: false });
    assert.ok(outs.length > 0, id);
    for (const o of outs) assert.ok(!o.path.startsWith('/') && !o.path.includes('..'), `${id}: unsafe path ${o.path}`);
  }
});

test('companion plan maps tools to each installer', () => {
  const plan = planCompanions(['claude', 'windsurf'], {});
  const uipro = plan.find((c) => c.id === 'ui-ux-pro-max');
  assert.deepEqual(uipro.commands, ['npx --yes ui-ux-pro-max-cli@2.15.0 init --ai claude', 'npx --yes ui-ux-pro-max-cli@2.15.0 init --ai windsurf']);
  const imp = plan.find((c) => c.id === 'impeccable');
  assert.deepEqual(imp.commands, ['npx --yes impeccable@4.8.1 install --providers=claude --scope=project']);
  const global = planCompanions(['claude'], { global: true, ids: ['ui-ux-pro-max'] });
  assert.equal(global[0].commands[0], 'npx --yes ui-ux-pro-max-cli@2.15.0 init --ai claude --global');
  const none = planCompanions(['gemini'], { ids: ['impeccable'] });
  assert.match(none[0].skip, /not available/);
});

test('companion installers are pinned to exact versions', () => {
  for (const c of planCompanions(Object.keys(ADAPTERS), { ids: require('../../src/cli/companions').COMPANIONS.map((x) => x.id) })) {
    for (const cmd of c.commands) assert.match(cmd, /^npx --yes (?:@[\w.-]+\/)?[\w.-]+@\d+\.\d+\.\d+ /, cmd);
  }
});

test('--global only applies to companions for tools that install globally', () => {
  const [imp] = planCompanions(['claude', 'cursor'], { global: true, ids: ['impeccable'] });
  assert.deepEqual(imp.commands, [
    'npx --yes impeccable@4.8.1 install --providers=claude --scope=global',
    'npx --yes impeccable@4.8.1 install --providers=cursor --scope=project',
  ]);
  const [uipro] = planCompanions(['cursor'], { global: true, ids: ['ui-ux-pro-max'] });
  assert.deepEqual(uipro.commands, ['npx --yes ui-ux-pro-max-cli@2.15.0 init --ai cursor']);
});

test('--yes alone never runs third-party companions', () => {
  assert.deepEqual(choicesFromFlags({ yes: true, agent: 'claude' }, {}).companions, []);
  assert.deepEqual(choicesFromFlags({ yes: true, companions: 'impeccable' }, {}).companions, ['impeccable']);
  assert.ok(choicesFromFlags({ all: true, yes: true }, {}).companions.length > 0);
  assert.deepEqual(choicesFromFlags({ all: true, noCompanions: true }, {}).companions, []);
});

test('--agent all expands everywhere, and the wizard rejects bad flags cleanly', async () => {
  assert.deepEqual(agentList('all'), Object.keys(ADAPTERS));
  assert.deepEqual(agentList('claude, all'), Object.keys(ADAPTERS));
  assert.deepEqual(choicesFromFlags({ agent: 'all' }, {}).tools, Object.keys(ADAPTERS));
  // Simulate a terminal so install() takes the wizard path; it must fail with a CliError, not a TypeError.
  const tty = [process.stdin.isTTY, process.stdout.isTTY];
  const write = process.stdout.write;
  process.stdin.isTTY = true;
  process.stdout.isTTY = true;
  process.stdout.write = () => true;
  try {
    await assert.rejects(install({ agent: 'notepad', noCompanions: true, dir: tmp() }), (e) => e instanceof CliError && /unknown tool/.test(e.message));
    await assert.rejects(install({ agent: 'all', skills: 'nope', noCompanions: true, dir: tmp() }), (e) => e instanceof CliError && /unknown skill/.test(e.message));
  } finally {
    [process.stdin.isTTY, process.stdout.isTTY] = tty;
    process.stdout.write = write;
  }
});

test('writes never follow a symlink out of the target directory', async (t) => {
  const dir = tmp();
  const outside = path.join(tmp(), 'victim.md');
  fs.writeFileSync(outside, 'original\n');
  try {
    fs.symlinkSync(outside, path.join(dir, 'AGENTS.md'));
    fs.symlinkSync(path.join(tmp(), 'missing.md'), path.join(dir, 'GEMINI.md'));
  } catch (e) {
    return t.skip(`cannot create symlinks here (${e.code})`);
  }
  try {
    const { report } = await quietInstall(dir, { agent: 'agents,gemini', skills: 'product-copywriting' });
    const rows = report.flatMap((r) => r.rows);
    assert.equal(rows.find((r) => r.path === 'AGENTS.md').action, 'refused');
    assert.match(rows.find((r) => r.path === 'GEMINI.md').reason, /dangling/);
    assert.equal(fs.readFileSync(outside, 'utf8'), 'original\n');
    assert.equal(process.exitCode, 1);
  } finally {
    process.exitCode = 0;
  }

  // A link that stays inside the project (AGENTS.md → CLAUDE.md is common) is still written through.
  const repo = tmp();
  fs.writeFileSync(path.join(repo, 'CLAUDE.md'), '# Project\n');
  fs.symlinkSync(path.join(repo, 'CLAUDE.md'), path.join(repo, 'AGENTS.md'));
  await quietInstall(repo, { agent: 'agents', skills: 'product-copywriting' });
  assert.match(fs.readFileSync(path.join(repo, 'CLAUDE.md'), 'utf8'), /fsd:start/);
});

test('--global puts Claude files in the home folder and other tools in the project', async () => {
  const home = tmp();
  const dir = tmp();
  const saved = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE };
  process.env.HOME = home;
  process.env.USERPROFILE = home;
  try {
    await quietInstall(dir, { agent: 'claude,cursor', global: true, skills: 'product-copywriting' });
    assert.ok(fs.existsSync(path.join(home, '.claude/skills/product-copywriting/SKILL.md')));
    assert.ok(!fs.existsSync(path.join(dir, '.claude')));
    assert.ok(fs.existsSync(path.join(dir, '.cursor/rules/product-copywriting.mdc')));
  } finally {
    for (const [k, v] of Object.entries(saved)) if (v === undefined) delete process.env[k];
    else process.env[k] = v;
  }
});

test('parseArgs rejects missing values and warns on unknown flags', () => {
  assert.throws(() => parseArgs(['--dir=']), /--dir needs a value/);
  assert.throws(() => parseArgs(['--agent', '--yes']), /--agent needs a value/);
  const warnings = [];
  const o = parseArgs(['--agents', 'claude', '--dry-run'], { warn: (m) => warnings.push(m) });
  assert.equal(o.dryRun, true);
  assert.match(warnings.join('\n'), /unknown option --agents/);
});

test('tool and stack detection', () => {
  const home = tmp();
  const cwd = tmp();
  fs.mkdirSync(path.join(cwd, '.cursor'));
  fs.mkdirSync(path.join(home, '.claude'));
  const tools = detectTools(cwd, home);
  assert.ok(tools.cursor);
  assert.ok(tools.claude);
  fs.writeFileSync(path.join(cwd, 'pubspec.yaml'), 'name: app\nflutter:\n');
  assert.equal(detectStack(cwd), 'Flutter');
  fs.writeFileSync(path.join(cwd, 'package.json'), JSON.stringify({ dependencies: { next: '1', react: '1' } }));
  assert.equal(detectStack(cwd), 'Next.js + Flutter');
});

test('knowledge folder is in sync with notes/', () => {
  const r = spawnSync(process.execPath, [path.join(ROOT, 'scripts', 'sync-knowledge.js'), '--check'], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stdout + r.stderr);
});

test('notes live in phase folders and flatten cleanly into knowledge/', () => {
  const { build, roadmap } = require('../../scripts/sync-knowledge');
  for (const t of roadmap().filter((r) => r.written)) {
    assert.match(t.dir, /^\d{2}-[a-z0-9-]+$/, `${t.slug} must live in a notes/<NN-phase>/ folder`);
    assert.ok(fs.existsSync(path.join(ROOT, 'notes', t.dir, `${t.slug}.md`)), `notes/${t.dir}/${t.slug}.md missing`);
  }
  for (const [name, content] of build()) {
    if (name.endsWith('.md')) assert.doesNotMatch(content, /\]\(\.\.\/[a-z0-9-]+\/[a-z0-9-]+\.md/, `${name} keeps a phase-folder link`);
  }
});

test('knowledge INDEX.md stays within its token budget', () => {
  const { build } = require('../../scripts/sync-knowledge');
  const index = build().get('INDEX.md');
  // Read on every design and lesson: keep it near 6k tokens (~4 chars per token).
  assert.ok(index.length < 28000, `INDEX.md is ${index.length} chars; keep it under 28000`);
});

test('every knowledge note maps its sections to the right line ranges', () => {
  const { build } = require('../../scripts/sync-knowledge');
  for (const [name, content] of build()) {
    if (!name.endsWith('.md') || name === 'INDEX.md') continue;
    const lines = content.split('\n');
    const map = lines[1].match(/^<!-- sections \(line ranges in this file\): (.+) -->$/);
    assert.ok(map, `${name}: line 2 must be the section map`);
    const ranges = map[1].split(' · ').map((s) => s.match(/^(.+) (\d+)-(\d+)$/));
    for (const required of ['ELI5', 'Key Points Summary', 'Cheat Sheet']) {
      assert.ok(ranges.some((r) => r[1] === required), `${name}: "${required}" missing from the section map`);
    }
    for (const [, section, start, end] of ranges) {
      assert.ok(lines[start - 1].startsWith(`## ${section}`), `${name}: "${section}" should start at line ${start}`);
      assert.ok(Number(end) >= Number(start) && Number(end) <= lines.length, `${name}: bad range for "${section}"`);
    }
  }
});

test('install ships all notes with the skill for Claude Code and shared .agents', async () => {
  const dir = tmp();
  await quietInstall(dir, { agent: 'claude,agents', skills: 'frontend-system-design' });
  const notes = require('../../scripts/sync-knowledge').listNotes().length;
  for (const root of ['.claude/skills', '.agents/skills']) {
    const k = path.join(dir, root, 'frontend-system-design/references/knowledge');
    assert.ok(fs.existsSync(path.join(k, 'INDEX.md')), `${root}: INDEX.md missing`);
    assert.equal(fs.readdirSync(k).filter((f) => f.endsWith('.md') && f !== 'INDEX.md').length, notes, `${root}: not every note was installed`);
  }
});

test('CLI new scaffolds a note into its phase folder', () => {
  const cli = path.join(ROOT, 'bin', 'cli.js');
  const dir = tmp();
  const ok = spawnSync(process.execPath, [cli, 'new', 'test-topic', '--phase', '3', '--dir', dir], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stdout + ok.stderr);
  assert.ok(fs.existsSync(path.join(dir, 'notes', '03-state-and-data', 'test-topic.md')));
  const missing = spawnSync(process.execPath, [cli, 'new', 'other-topic', '--dir', dir], { encoding: 'utf8' });
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /--phase is required/);
});

test('legacy skill id storytelling-copywriter installs product-copywriting', () => {
  const dir = tmp();
  const r = spawnSync(process.execPath, [path.join(ROOT, 'bin', 'cli.js'), 'install', '--agent', 'claude', '--skills', 'storytelling-copywriter', '--yes', '--no-companions', '--dir', dir], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stderr, /renamed to "product-copywriting"/);
  assert.ok(fs.existsSync(path.join(dir, '.claude/skills/product-copywriting/SKILL.md')));
  assert.ok(!fs.existsSync(path.join(dir, '.claude/skills/storytelling-copywriter')));
});

test('CLI help and version run', () => {
  const cli = path.join(ROOT, 'bin', 'cli.js');
  const v = spawnSync(process.execPath, [cli, '--version'], { encoding: 'utf8' });
  assert.equal(v.stdout.trim(), require('../../package.json').version);
  const h = spawnSync(process.execPath, [cli, 'help'], { encoding: 'utf8' });
  assert.match(h.stdout, /install/);
  const bad = spawnSync(process.execPath, [cli, 'install', '--agent', 'nope', '--yes', '--dir', tmp()], { encoding: 'utf8' });
  assert.notEqual(bad.status, 0);
  assert.match(bad.stderr, /unknown tool/);
});
