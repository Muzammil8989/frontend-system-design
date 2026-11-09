'use strict';

/** CLI entry: argument parsing and command dispatch. */

const fs = require('fs');
const path = require('path');
const { c, CliError, fail, NPX, PKG, PKG_ROOT, read, REPO_URL } = require('./util');
const { ADAPTERS } = require('./adapters');
const { SKILLS } = require('./skills');
const { COMPANIONS } = require('./companions');

const VALUE_FLAGS = ['agent', 'dir', 'title', 'companions', 'skills', 'phase'];

// One notes/ folder per README roadmap phase, in order (phase 1 → index 0).
const NOTE_PHASES = [
  '01-web-fundamentals',
  '02-rendering-and-architecture',
  '03-state-and-data',
  '04-performance-engineering',
  '05-design-systems-and-components',
  '06-accessibility-and-i18n',
  '07-security',
  '08-testing',
  '09-monitoring-and-observability',
  '10-advanced-topics',
  '11-system-design-cases',
];
const BOOLEAN_FLAGS = ['all', 'yes', 'global', 'force', 'dryRun', 'noCompanions', 'listCompanions', 'ci', 'quiet', 'noReadme', 'json', 'help'];

function parseArgs(argv, { warn = (msg) => console.error(c.yellow(msg)) } = {}) {
  const opts = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-y') opts.yes = true;
    else if (!a.startsWith('--')) opts._.push(a);
    else {
      const [rawKey, inline] = a.slice(2).split(/=(.*)/s);
      const key = rawKey.replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
      if (VALUE_FLAGS.includes(key)) {
        const value = inline !== undefined ? inline : argv[++i];
        if (value === undefined || value === '' || (inline === undefined && value.startsWith('--'))) fail(`--${rawKey} needs a value`);
        opts[key] = value;
      } else {
        if (!BOOLEAN_FLAGS.includes(key)) warn(`warning: unknown option --${rawKey} (ignored)`);
        opts[key] = true;
      }
    }
  }
  return opts;
}

function help() {
  console.log(`
${c.bold('frontend-system-design')} ${c.dim(`v${PKG.version}`)}: staff-level frontend architect + product copywriter for AI coding tools

${c.bold('Usage')}
  ${NPX} install               ${c.dim('# interactive wizard')}
  ${NPX} <command> [options]

${c.bold('Commands')}
  install                Install skills, specialist agents and commands (asks questions in a terminal)
    --agent <list>         ${Object.keys(ADAPTERS).join(', ')}, all
    --skills <list>        ${SKILLS.map((s) => s.id).join(', ')} (default: both)
    --global               Claude Code: install to ~/.claude (all projects)
    --dir <path>           Target project (default: current directory)
    --companions <ids>     Run these third-party companion installers (pinned versions; see list-companions)
    --no-companions        Skip third-party companion skills
    --all                  Every tool + every default companion skill
    --yes, -y              No questions: use flags/defaults (companions only with --companions or --all)
    --force                Overwrite files you changed locally
    --dry-run              Preview; write and run nothing
  list                   Show what each tool integration installs
  list-companions        Show companion skills and their licenses
  new <slug> --phase <n> (contributors) Scaffold notes/<phase-folder>/<slug>.md from the template
  lint [files...]        (contributors) Validate notes and README progress
  help, --version

${c.bold('Examples')}
  ${NPX} install
  ${NPX} install --agent claude --global --yes
  ${NPX} install --agent cursor,windsurf --skills product-copywriting --no-companions

Docs: ${REPO_URL}#readme
`);
}

function listCompanions() {
  console.log(c.bold('\nCompanion skills (installed by default; --no-companions to skip, --companions <ids> to choose)\n'));
  for (const x of COMPANIONS) {
    console.log(`${c.cyan(x.id.padEnd(22))} ${c.bold(x.name)}`);
    console.log(`${' '.repeat(23)}${x.purpose}`);
    console.log(`${' '.repeat(23)}${c.dim(`${x.license} · ${x.repo} · tools: ${Object.keys(x.agents).join(', ')}`)}\n`);
  }
}

function list() {
  const skills = SKILLS.map((s) => s.id);
  console.log(c.bold('\nWhat each integration installs\n'));
  for (const [id, a] of Object.entries(ADAPTERS)) {
    console.log(`${c.cyan(id.padEnd(9))} ${a.label}${a.global ? c.dim('  (supports --global)') : ''}`);
    const seen = new Set();
    for (const o of a.outputs({ skills, global: false })) {
      const m = o.path.match(/^(.*?skills\/[^/]+)\//);
      if (m) {
        if (!seen.has(m[1])) console.log(`          ${c.dim(`${m[1]}/  (SKILL.md + references, scripts, data)`)}`);
        seen.add(m[1]);
      } else console.log(`          ${c.dim(o.path)}${o.block !== undefined ? c.dim('  (managed block)') : ''}`);
    }
  }
  console.log('');
  listCompanions();
}

function newNote(opts) {
  const slug = opts._[0];
  if (!slug) fail('usage: npm run new-note -- <slug> --phase <1-11> [--title "Title"]');
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) fail(`slug "${slug}" must be lower-case and hyphenated, e.g. dom-and-virtual-dom`);
  const phases = NOTE_PHASES.map((f, i) => `  ${i + 1}  ${f}`).join('\n');
  if (!opts.phase) fail(`--phase is required (the README roadmap phase the note belongs to):\n${phases}`);
  const phase = /^\d+$/.test(opts.phase) ? NOTE_PHASES[Number(opts.phase) - 1] : NOTE_PHASES.find((f) => f === opts.phase);
  if (!phase) fail(`unknown --phase "${opts.phase}"; use a number or folder name:\n${phases}`);
  const rel = `notes/${phase}/${slug}.md`;
  const root = path.resolve(opts.dir || process.cwd());
  const target = path.join(root, rel);
  if (fs.existsSync(target)) fail(`${rel} already exists`);
  const local = path.join(root, 'notes', '_TEMPLATE.md');
  const template = read(fs.existsSync(local) ? local : path.join(PKG_ROOT, 'notes', '_TEMPLATE.md'));
  const title = opts.title || slug.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, template.replace(/<Topic Title>/g, title).replace(/YYYY-MM-DD/g, new Date().toISOString().slice(0, 10)));
  console.log(c.green(`✔ Created ${rel}`));
  console.log(`\nNext:\n  1. Fill every section (see CONTRIBUTING.md)\n  2. Mark the topic ✅ in README.md (link ./${rel}) and update progress\n  3. ${c.cyan(`npm run lint:notes -- ${rel}`)} and ${c.cyan('npm run sync:knowledge')}\n`);
}

async function main(argv = process.argv.slice(2)) {
  const [command = 'help', ...rest] = argv;
  const opts = parseArgs(rest);
  if (opts.help) return help();
  switch (command) {
    case 'install':
    case 'i':
      if (opts.listCompanions) return listCompanions();
      return require('./install').install(opts);
    case 'list':
    case 'ls':
      return list();
    case 'list-companions':
      return listCompanions();
    case 'new':
      return newNote(opts);
    case 'lint': {
      const { run } = require('../../scripts/lint-notes.js');
      process.exitCode = run({ root: path.resolve(opts.dir || process.cwd()), files: opts._, readme: !opts.noReadme, json: !!opts.json });
      return undefined;
    }
    case '-v':
    case '--version':
    case 'version':
      return console.log(PKG.version);
    case 'help':
    case '-h':
    case '--help':
      return help();
    default:
      console.error(c.red(`Unknown command "${command}".`));
      help();
      process.exitCode = 1;
      return undefined;
  }
}

function run() {
  main().catch((err) => {
    console.error(c.red(`✖ ${err instanceof CliError ? err.message : err.stack || err.message}`));
    process.exitCode = 1;
  });
}

module.exports = { main, run, parseArgs };
