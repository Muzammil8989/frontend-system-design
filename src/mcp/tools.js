'use strict';

/**
 * MCP tools: the skills' Python engine (run from the package, no install needed) and the learning notes.
 * Every path argument is confined to the server's root folder.
 */

const fs = require('fs');
const path = require('path');
const { PKG_ROOT, read } = require('../cli/util');
const { runPython } = require('../cli/python');

const FSD = path.join(PKG_ROOT, 'skills', 'frontend-system-design');
const SCRIPTS = {
  recommend: path.join(FSD, 'scripts', 'recommend.py'),
  search: path.join(FSD, 'scripts', 'search.py'),
  budget: path.join(FSD, 'scripts', 'budget.py'),
  detect_stack: path.join(FSD, 'scripts', 'detect_stack.py'),
  audit_scan: path.join(FSD, 'scripts', 'audit_scan.py'),
  tokens_check: path.join(FSD, 'scripts', 'tokens_check.py'),
  copy_check: path.join(PKG_ROOT, 'skills', 'product-copywriting', 'scripts', 'copy_check.py'),
  commit_check: path.join(PKG_ROOT, 'skills', 'git-workflow', 'scripts', 'commit_check.py'),
};
const KNOWLEDGE = path.join(FSD, 'references', 'knowledge');
const MAX_OUTPUT = 20000;
const DEFAULT_SECTIONS = ['Key Points Summary', 'Cheat Sheet'];

class ToolError extends Error {}

const cap = (text) =>
  text.length > MAX_OUTPUT ? `${text.slice(0, MAX_OUTPUT)}\n\n[truncated at ${MAX_OUTPUT} characters; narrow the query or path]` : text;

/** Scripts pretty-print their JSON for humans; the model gets it without the indentation (far fewer tokens). */
function compact(text) {
  if (!/^[[{]/.test(text)) return text;
  try {
    return JSON.stringify(JSON.parse(text));
  } catch {
    return text;
  }
}

/** Resolves a user path inside root (symlinks included); throws ToolError outside it. */
function inRoot(root, p = '.', { mustExist = true } = {}) {
  const abs = path.resolve(root, String(p));
  let real = abs;
  if (fs.existsSync(abs)) real = fs.realpathSync(abs);
  else if (mustExist) throw new ToolError(`not found: ${p}`);
  const rel = path.relative(root, real);
  if (rel.startsWith('..') || path.isAbsolute(rel)) throw new ToolError(`${p} is outside the allowed folder (${root}); start the server with --dir to change it`);
  return real;
}

/** Runs a script; exit 0/1 are results (1 = "issues found"/"no match"), anything else is a tool error. */
async function py(name, args, { cwd, input } = {}) {
  const r = await runPython(SCRIPTS[name], args, { cwd, input });
  if (r.timedOut) throw new ToolError(`${name} timed out`);
  if (r.code === 0 || r.code === 1) return cap(compact((r.stdout || r.stderr).trim()) || '(no output)');
  throw new ToolError((r.stderr || r.stdout).trim() || `${name} exited with code ${r.code}`);
}

/* ---------- notes ---------- */

let indexCache;
const topics = () => (indexCache ||= JSON.parse(read(path.join(KNOWLEDGE, 'index.json'))).topics.filter((t) => t.written));

/** Line 2 of every knowledge note: "<!-- sections (line ranges in this file): Name 1-9 · Other 10-20 -->". */
function sectionMap(lines) {
  const m = (lines[1] || '').match(/sections \(line ranges in this file\):\s*(.*?)\s*-->/);
  if (!m) return [];
  return m[1].split(' · ').map((part) => {
    const r = part.match(/^(.*) (\d+)-(\d+)$/);
    return r ? { name: r[1], start: +r[2], end: +r[3] } : null;
  }).filter(Boolean);
}

function listNotes({ phase, query } = {}) {
  const words = String(query || '').toLowerCase().split(/\s+/).filter(Boolean);
  const hits = topics().filter((t) => {
    if (phase && t.phase !== Number(phase)) return false;
    const hay = `${t.slug} ${t.title} ${t.category} ${t.informs}`.toLowerCase();
    return words.every((w) => hay.includes(w));
  });
  if (!hits.length) return 'No notes match. Try fewer words, or list a phase (1-11).';
  const shown = hits.slice(0, 40);
  return [
    `${hits.length} note(s)${hits.length > shown.length ? `, first ${shown.length} shown` : ''}. Read one with read_note { slug }.`,
    ...shown.map((t) => `- ${t.slug} · ${t.title} (phase ${t.phase}, ${t.level}): ${t.informs}`),
  ].join('\n');
}

function readNote({ slug, sections } = {}) {
  const topic = topics().find((t) => t.slug === slug);
  if (!topic) throw new ToolError(`unknown note "${slug}"; find slugs with list_notes`);
  const lines = read(path.join(KNOWLEDGE, topic.file)).split('\n');
  const map = sectionMap(lines);
  const wanted = sections && sections.length ? sections : DEFAULT_SECTIONS;
  const header = `# ${topic.title}\nSections: ${map.map((s) => s.name).join(' · ')}\nSource: ${topic.url} (CC BY 4.0)\n`;
  if (wanted.some((s) => String(s).toLowerCase() === 'all')) return cap(`${header}\n${lines.slice(2).join('\n')}`);
  const picked = wanted.map((w) => map.find((s) => s.name.toLowerCase() === String(w).toLowerCase())).filter(Boolean);
  if (!picked.length) throw new ToolError(`no section named ${wanted.join(', ')}; available: ${map.map((s) => s.name).join(', ')}`);
  return cap(`${header}\n${picked.map((s) => lines.slice(s.start - 1, s.end).join('\n')).join('\n\n')}`);
}

/* ---------- definitions ---------- */

const str = (description, extra = {}) => ({ type: 'string', description, ...extra });

const TOOLS = [
  {
    name: 'recommend',
    description: 'Turn a product idea into a frontend recommendation: product type, platform, stack, UI styles, contrast-checked palettes, fonts, UX patterns, performance budget, files to read and the learning notes behind each choice.',
    inputSchema: {
      type: 'object',
      properties: {
        description: str('The product or problem, e.g. "offline-first field-service app for 2,000 technicians"'),
        platform: str('Force a platform', { enum: ['web', 'mobile', 'desktop', 'cross'] }),
        stack: str('Prefer a stack, e.g. "Next.js" or "Flutter"'),
        project_dir: str('Existing project folder to detect its stack (relative to the server root)'),
      },
      required: ['description'],
    },
    run: (a, { root }) => {
      const args = ['--json'];
      if (a.platform) args.push('--platform', a.platform);
      if (a.stack) args.push('--stack', String(a.stack));
      if (a.project_dir) args.push('--project', inRoot(root, a.project_dir));
      return py('recommend', [...args, '--', String(a.description)], { cwd: root });
    },
  },
  {
    name: 'search',
    description: 'BM25 search over the curated datasets: product types, stacks, UI styles, WCAG-AA palettes, font pairings and UX patterns.',
    inputSchema: {
      type: 'object',
      properties: {
        domain: str('Dataset to search', { enum: ['products', 'stacks', 'styles', 'palettes', 'fonts', 'patterns'] }),
        query: str('What to look for, e.g. "fintech trustworthy"'),
        limit: { type: 'integer', minimum: 1, maximum: 20, description: 'Results to return (default 5)' },
      },
      required: ['domain', 'query'],
    },
    run: (a, { root }) => py('search', ['--json', '-d', a.domain, '-n', String(a.limit || 5), '--', String(a.query)], { cwd: root }),
  },
  {
    name: 'budget',
    description: 'Performance budgets: Core Web Vitals and size budgets for the web, startup/frame/size targets for mobile and desktop. Give a product type or a description.',
    inputSchema: {
      type: 'object',
      properties: {
        product_type: str('A product type id, e.g. "mobile-consumer" (see search domain=products)'),
        description: str('Or describe the product and let it pick the type'),
        platform: str('Target platform (default web)', { enum: ['web', 'mobile', 'desktop'] }),
      },
    },
    run: (a, { root }) => {
      if (!a.product_type && !a.description) throw new ToolError('give product_type or description');
      const args = ['--format', 'json', ...(a.product_type ? ['--type', String(a.product_type)] : ['--from', String(a.description)])];
      if (a.platform) args.push('--platform', a.platform);
      return py('budget', args, { cwd: root });
    },
  },
  {
    name: 'detect_stack',
    description: 'Detect the stack of an existing project (monorepos too): web frameworks, React Native, Flutter, Swift, Kotlin, MAUI, Tauri, Electron.',
    inputSchema: { type: 'object', properties: { path: str('Project folder, relative to the server root (default ".")') } },
    run: (a, { root }) => py('detect_stack', ['--json', inRoot(root, a.path || '.')], { cwd: root }),
  },
  {
    name: 'audit_scan',
    description: 'Static accessibility, security and performance scan of a project folder, with file:line findings.',
    inputSchema: {
      type: 'object',
      properties: {
        path: str('Folder to scan, relative to the server root (default ".")'),
        max: { type: 'integer', minimum: 1, maximum: 500, description: 'Most findings to return (default 50)' },
      },
    },
    run: (a, { root }) => py('audit_scan', ['--format', 'json', '--max', String(a.max || 50), inRoot(root, a.path || '.')], { cwd: root }),
  },
  {
    name: 'tokens_check',
    description: 'Validate a design-tokens JSON file: references, types and WCAG color contrast.',
    inputSchema: { type: 'object', properties: { file: str('tokens.json path, relative to the server root') }, required: ['file'] },
    run: (a, { root }) => py('tokens_check', ['--format', 'json', inRoot(root, a.file)], { cwd: root }),
  },
  {
    name: 'copy_check',
    description: 'Score website or app copy 0-100 for human, specific writing: flags AI-sounding phrases, filler, passive voice, rhythm and reading level, with line-level fixes.',
    inputSchema: {
      type: 'object',
      properties: { text: str('The copy to check (markdown or plain text)'), mode: str('marketing (default) or ui (stricter reading level)', { enum: ['marketing', 'ui'] }) },
      required: ['text'],
    },
    run: (a, { root }) => py('copy_check', ['--json', '--mode', a.mode || 'marketing', '-'], { cwd: root, input: String(a.text) }),
  },
  {
    name: 'commit_check',
    description: 'Lint a commit message (Conventional Commits, imperative mood, length, breaking-change footers) or every commit in a git range, and suggest the next semantic version.',
    inputSchema: {
      type: 'object',
      properties: {
        message: str('A commit message to check'),
        range: str('Or a git range in the server root repo, e.g. "origin/main..HEAD" or "v1.2.0..HEAD"'),
        suggest_bump: { type: 'boolean', description: 'With range: suggest major/minor/patch from the commits' },
      },
    },
    run: (a, { root }) => {
      if (a.range) return py('commit_check', ['--json', '--range', String(a.range), '--repo', root, ...(a.suggest_bump ? ['--suggest-bump'] : [])], { cwd: root });
      if (a.message) return py('commit_check', ['--json', '--', String(a.message)], { cwd: root });
      throw new ToolError('give message or range');
    },
  },
  {
    name: 'list_notes',
    description: 'Find learning notes (120 frontend system design topics in 11 phases) by keyword or phase. Returns slugs for read_note.',
    inputSchema: {
      type: 'object',
      properties: { query: str('Keywords, e.g. "rendering ssr" or "auth token storage"'), phase: { type: 'integer', minimum: 1, maximum: 11, description: 'Only this roadmap phase' } },
    },
    run: (a) => listNotes(a),
  },
  {
    name: 'read_note',
    description: 'Read a learning note by slug. Returns only the requested sections (default: Key Points Summary and Cheat Sheet) to save tokens; pass ["all"] for the whole note.',
    inputSchema: {
      type: 'object',
      properties: { slug: str('Note slug from list_notes, e.g. "critical-rendering-path"'), sections: { type: 'array', items: { type: 'string' }, description: 'Section names, e.g. ["ELI5", "Cheat Sheet"]' } },
      required: ['slug'],
    },
    run: (a) => readNote(a),
  },
];

/** Runs a tool; returns an MCP CallToolResult. */
async function callTool(name, args, ctx) {
  const tool = TOOLS.find((t) => t.name === name);
  if (!tool) return null;
  try {
    const missing = (tool.inputSchema.required || []).filter((k) => args[k] === undefined || args[k] === '');
    if (missing.length) throw new ToolError(`missing ${missing.join(', ')}`);
    const text = await tool.run(args, ctx);
    return { content: [{ type: 'text', text }], isError: false };
  } catch (e) {
    const message = e instanceof ToolError || /Python 3\.9\+ not found/.test(e.message) ? e.message : `internal error: ${e.message}`;
    return { content: [{ type: 'text', text: message }], isError: true };
  }
}

const toolList = () => TOOLS.map(({ name, description, inputSchema }) => ({ name, description, inputSchema }));

module.exports = { callTool, toolList, inRoot, sectionMap, listNotes, readNote, ToolError };
