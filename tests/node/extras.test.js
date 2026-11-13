'use strict';

/** Tests for the opt-in extras: guardrail hooks (--hooks) and the MCP server (mcp, --mcp). Run: npm run test:node */

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..', '..');
const CLI = path.join(ROOT, 'bin', 'cli.js');
const { decide, isSecretFile } = require('../../hooks/fsd-guard');
const { writeOutput } = require('../../src/cli/writer');
const { mergeGuard, commitMsgHook } = require('../../src/cli/hooks');
const { mcpOutputs, NAME } = require('../../src/cli/mcp-config');
const { install } = require('../../src/cli/install');
const { findPython } = require('../../src/cli/python');

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'fsd-extras-'));
const hasGit = spawnSync('git', ['--version']).status === 0;
const git = (cwd, ...args) => spawnSync('git', args, { cwd, encoding: 'utf8' });

/* ---------- guard ---------- */

test('guard: denies force-push, --no-verify and committing secrets; asks before risky commands', () => {
  const staged = (files) => ({ changedFiles: () => files });
  const cases = [
    ['git status', 'allow'],
    ['ls && git log --oneline', 'allow'],
    ['echo "git push --force"', 'allow'],
    ['git push', 'ask'],
    ['git -C packages/web push origin main', 'ask'],
    ['git push --force-with-lease', 'ask'],
    ['git push origin --delete old-branch', 'ask'],
    ['git push --force', 'deny'],
    ['git push -f origin main', 'deny'],
    ['git push origin +main', 'deny'],
    ['FOO=1 git push -f', 'deny'],
    ['npm test && git push --force', 'deny'],
    ['git commit --no-verify -m "x"', 'deny'],
    ['git commit -nm "x"', 'deny'],
    ['git commit -m "-n is part of the message"', 'allow'],
    ['git reset --hard HEAD~1', 'ask'],
    ['git reset --soft HEAD~1', 'allow'],
    ['git clean -fd', 'ask'],
    ['git clean -nd', 'allow'],
    ['git branch -D feature', 'ask'],
    ['git branch -d feature', 'allow'],
    ['git stash drop', 'ask'],
    ['git checkout -- .', 'ask'],
    ['git restore .', 'ask'],
    ['git restore --staged .', 'allow'],
    ['git checkout main', 'allow'],
    ['git tag -d v1.0.0', 'ask'],
    ['git filter-repo --path secrets.txt --invert-paths', 'ask'],
  ];
  for (const [cmd, expected] of cases) assert.equal(decide(cmd).decision, expected, cmd);
  assert.equal(decide('git commit -m "feat: x"', staged(['.env'])).decision, 'deny');
  assert.equal(decide('git commit -am "feat: x"', staged(['config/prod.env'])).decision, 'deny');
  assert.equal(decide('git commit -m "feat: x"', staged(['.env.example', 'src/app.ts'])).decision, 'allow');
  assert.match(decide('git push --force').reason, /^fsd-guard: .*force-with-lease/);
});

test('guard: secret file patterns', () => {
  for (const f of ['.env', 'apps/web/.env.local', 'prod.env', 'certs/server.pem', 'id_rsa', 'keys/id_ed25519', 'credentials.json', 'a/client_secret_123.json', 'store.jks']) {
    assert.ok(isSecretFile(f), f);
  }
  for (const f of ['.env.example', '.env.sample', 'id_rsa.pub', 'src/env.ts', 'docs/keys.md', 'package.json']) assert.ok(!isSecretFile(f), f);
});

test('guard: speaks the PreToolUse protocol and fails open on bad input', () => {
  const guard = path.join(ROOT, 'hooks', 'fsd-guard.js');
  const run = (input) => spawnSync(process.execPath, [guard], { input, encoding: 'utf8' });
  const denied = run(JSON.stringify({ tool_name: 'Bash', tool_input: { command: 'git push --force' }, cwd: ROOT }));
  assert.equal(denied.status, 0);
  const out = JSON.parse(denied.stdout).hookSpecificOutput;
  assert.equal(out.hookEventName, 'PreToolUse');
  assert.equal(out.permissionDecision, 'deny');
  const allowed = run(JSON.stringify({ tool_name: 'Bash', tool_input: { command: 'npm test' }, cwd: ROOT }));
  assert.equal(allowed.status, 0);
  assert.equal(allowed.stdout, '');
  assert.equal(run(JSON.stringify({ tool_name: 'Edit', tool_input: { file_path: 'x' } })).stdout, '');
  const broken = run('not json');
  assert.equal(broken.status, 0);
  assert.equal(broken.stdout, '');
  assert.match(broken.stderr, /fsd-guard: skipped/);
});

/* ---------- settings.json merge ---------- */

test('settings.json merge keeps other hooks, is idempotent, and refuses invalid JSON', () => {
  const dir = tmp();
  const file = path.join(dir, '.claude', 'settings.json');
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const theirs = { matcher: 'Edit', hooks: [{ type: 'command', command: 'prettier --write' }] };
  fs.writeFileSync(file, JSON.stringify({ model: 'x', hooks: { PreToolUse: [theirs], Stop: [] } }));
  const out = { path: '.claude/settings.json', json: mergeGuard('node "guard/fsd-guard.js"') };
  assert.equal(writeOutput(dir, out).action, 'updated');
  const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.equal(cfg.model, 'x');
  assert.deepEqual(cfg.hooks.PreToolUse[0], theirs);
  assert.equal(cfg.hooks.PreToolUse.length, 2);
  assert.deepEqual(cfg.hooks.Stop, []);
  assert.equal(writeOutput(dir, out).action, 'unchanged');
  // A changed command replaces our entry instead of adding a second one.
  writeOutput(dir, { path: out.path, json: mergeGuard('node "other/fsd-guard.js"') });
  assert.equal(JSON.parse(fs.readFileSync(file, 'utf8')).hooks.PreToolUse.length, 2);

  fs.writeFileSync(file, '{ // comment\n}');
  const r = writeOutput(dir, out);
  assert.equal(r.action, 'refused');
  assert.equal(fs.readFileSync(file, 'utf8'), '{ // comment\n}');
  fs.writeFileSync(file, '{"hooks": []}');
  assert.equal(writeOutput(dir, out).action, 'refused');
});

/* ---------- git commit-msg hook ---------- */

test('commit-msg hook: installed in a fresh repo, never over someone else\'s hook or core.hooksPath', { skip: !hasGit && 'git not installed' }, async () => {
  const dir = tmp();
  git(dir, 'init', '-q');
  const choices = { tools: ['claude'], skills: ['git-workflow'], global: false };
  const h = commitMsgHook(choices, dir);
  assert.ok(h.out, h.skip);
  assert.equal(h.out.path, '.git/hooks/commit-msg');
  assert.match(h.out.content, /fsd-guard: managed/);
  assert.match(h.out.content, /\.claude\/skills\/git-workflow\/scripts\/commit_check\.py/);
  assert.match(commitMsgHook({ ...choices, skills: ['product-copywriting'] }, dir).skip, /git-workflow/);
  assert.match(commitMsgHook(choices, tmp()).skip, /not a git repository/);

  fs.writeFileSync(path.join(dir, '.git', 'hooks', 'commit-msg'), '#!/bin/sh\nnpx commitlint --edit "$1"\n');
  assert.match(commitMsgHook(choices, dir).skip, /already exists/);
  fs.rmSync(path.join(dir, '.git', 'hooks', 'commit-msg'));
  git(dir, 'config', 'core.hooksPath', '.husky');
  assert.match(commitMsgHook(choices, dir).skip, /core\.hooksPath/);
});

test('install --hooks writes the guard, merges settings and adds the commit-msg hook', { skip: !hasGit && 'git not installed' }, async () => {
  const dir = tmp();
  git(dir, 'init', '-q');
  await install({ dir, agent: 'claude', skills: 'git-workflow', noCompanions: true, hooks: true, quiet: true, ci: true });
  assert.ok(fs.existsSync(path.join(dir, '.claude', 'hooks', 'fsd-guard.js')));
  const cfg = JSON.parse(fs.readFileSync(path.join(dir, '.claude', 'settings.json'), 'utf8'));
  assert.match(cfg.hooks.PreToolUse[0].hooks[0].command, /\$\{CLAUDE_PROJECT_DIR\}\/\.claude\/hooks\/fsd-guard\.js/);
  assert.ok(fs.existsSync(path.join(dir, '.git', 'hooks', 'commit-msg')));
  const again = await install({ dir, agent: 'claude', skills: 'git-workflow', noCompanions: true, hooks: true, quiet: true, ci: true });
  assert.deepEqual(again.report.flatMap((r) => r.rows).filter((r) => r.action !== 'unchanged'), []);
  // Without --hooks nothing is written.
  const plain = tmp();
  await install({ dir: plain, agent: 'claude', skills: 'git-workflow', noCompanions: true, quiet: true, ci: true });
  assert.ok(!fs.existsSync(path.join(plain, '.claude', 'settings.json')));
});

/* ---------- companion environment ---------- */

test('companion installers do not inherit npm_config_package / npm_config_call from an outer npx -p', () => {
  const { companionEnv } = require('../../src/cli/companions');
  const env = companionEnv({ PATH: '/bin', npm_config_package: 'x.tgz', NPM_CONFIG_CALL: 'node x', npm_config_yes: 'true', npm_config_registry: 'https://r' });
  assert.equal(env.npm_config_package, undefined);
  assert.equal(env.NPM_CONFIG_CALL, undefined);
  assert.equal(env.PATH, '/bin');
  assert.equal(env.npm_config_yes, 'true');
  assert.equal(env.npm_config_registry, 'https://r'); // a private registry setting still reaches the installers
});

/* ---------- --mcp config ---------- */

test('--mcp registers the server under each tool\'s key and merges idempotently', async () => {
  const { outputs, notes } = mcpOutputs({ tools: ['claude', 'cursor', 'copilot', 'gemini', 'windsurf', 'agents'], global: false });
  const byPath = Object.fromEntries(outputs.map((o) => [o.out.path, o.out]));
  assert.deepEqual(Object.keys(byPath).sort(), ['.cursor/mcp.json', '.gemini/settings.json', '.mcp.json', '.vscode/mcp.json']);
  assert.equal(notes.length, 2);

  const dir = tmp();
  fs.mkdirSync(path.join(dir, '.gemini'));
  fs.writeFileSync(path.join(dir, '.gemini', 'settings.json'), JSON.stringify({ theme: 'dark', mcpServers: { other: { command: 'x' } } }));
  for (const o of outputs) assert.notEqual(writeOutput(dir, o.out).action, 'refused', o.out.path);
  const read = (p) => JSON.parse(fs.readFileSync(path.join(dir, p), 'utf8'));
  assert.ok(read('.mcp.json').mcpServers[NAME]);
  assert.ok(read('.cursor/mcp.json').mcpServers[NAME]);
  assert.equal(read('.vscode/mcp.json').servers[NAME].type, 'stdio');
  const gemini = read('.gemini/settings.json');
  assert.equal(gemini.theme, 'dark');
  assert.deepEqual(Object.keys(gemini.mcpServers).sort(), [NAME, 'other']);
  for (const o of outputs) assert.equal(writeOutput(dir, o.out).action, 'unchanged', o.out.path);
  assert.match(byPath['.mcp.json'].manual, /"mcpServers"/);
  assert.ok(mcpOutputs({ tools: ['claude'], global: true }).notes[0].includes('claude mcp add --scope user'));
});

/* ---------- MCP server ---------- */

/** Starts the server, sends messages, collects replies until every request id is answered. */
function mcpSession(messages, { dir } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [CLI, 'mcp', ...(dir ? ['--dir', dir] : [])], { cwd: dir || ROOT });
    const want = new Set(messages.filter((m) => m.id !== undefined).map((m) => m.id));
    const replies = {};
    let buf = '';
    let raw = '';
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`timeout; got ${Object.keys(replies)}`));
    }, 60000);
    child.stdout.setEncoding('utf8').on('data', (d) => {
      raw += d;
      buf += d;
      let i;
      while ((i = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, i);
        buf = buf.slice(i + 1);
        const msg = JSON.parse(line); // every stdout line must be JSON
        replies[msg.id] = msg;
        want.delete(msg.id);
      }
      if (!want.size) {
        clearTimeout(timer);
        child.stdin.end();
        resolve({ replies, raw });
      }
    });
    for (const m of messages) child.stdin.write(`${JSON.stringify(m)}\n`);
  });
}

const call = (id, name, args) => ({ jsonrpc: '2.0', id, method: 'tools/call', params: { name, arguments: args } });

test('mcp: protocol, tool list, notes, root sandbox and errors', async () => {
  const dir = tmp();
  const { replies, raw } = await mcpSession(
    [
      { jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 't', version: '1' } } },
      { jsonrpc: '2.0', method: 'notifications/initialized' },
      { jsonrpc: '2.0', id: 2, method: 'tools/list' },
      call(3, 'list_notes', { query: 'token storage' }),
      call(4, 'read_note', { slug: 'critical-rendering-path', sections: ['Cheat Sheet'] }),
      call(5, 'detect_stack', { path: '..' }),
      call(6, 'read_note', { slug: 'nope' }),
      { jsonrpc: '2.0', id: 7, method: 'no/such' },
      { jsonrpc: '2.0', id: 8, method: 'ping' },
      { jsonrpc: '2.0', id: 9, method: 'initialize', params: { protocolVersion: '1999-01-01' } },
    ],
    { dir }
  );
  assert.ok(raw.split('\n').filter(Boolean).every((l) => JSON.parse(l).jsonrpc === '2.0'));
  assert.equal(replies[1].result.protocolVersion, '2025-06-18');
  assert.deepEqual(replies[1].result.capabilities, { tools: {} });
  assert.equal(replies[9].result.protocolVersion, '2025-11-25');
  const names = replies[2].result.tools.map((t) => t.name);
  for (const n of ['recommend', 'search', 'budget', 'detect_stack', 'audit_scan', 'tokens_check', 'copy_check', 'commit_check', 'list_notes', 'read_note']) assert.ok(names.includes(n), n);
  for (const t of replies[2].result.tools) assert.equal(t.inputSchema.type, 'object', t.name);
  assert.match(replies[3].result.content[0].text, /browser-storage-mechanisms/);
  assert.equal(replies[4].result.isError, false);
  assert.match(replies[4].result.content[0].text, /^# Critical Rendering Path/);
  assert.match(replies[4].result.content[0].text, /^#+ .*Cheat Sheet/m);
  assert.doesNotMatch(replies[4].result.content[0].text, /^#+ .*Key Points Summary/m); // only the requested section
  assert.equal(replies[5].result.isError, true);
  assert.match(replies[5].result.content[0].text, /outside the allowed folder/);
  assert.equal(replies[6].result.isError, true);
  assert.equal(replies[7].error.code, -32601);
  assert.deepEqual(replies[8].result, {});
});

test('mcp: Python tools run from the package', { skip: !findPython().exe && 'Python 3.9+ not installed' }, async () => {
  const { replies } = await mcpSession([
    { jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-11-25' } },
    call(2, 'search', { domain: 'palettes', query: 'fintech trustworthy', limit: 1 }),
    call(3, 'commit_check', { message: 'Added stuff.' }),
    call(4, 'commit_check', { message: 'feat(cli): add an mcp command' }),
    call(5, 'copy_check', { text: 'Send the invoice when the work is done. We chase the late ones for you.' }),
    call(6, 'recommend', { description: '-x booking app for hair salons' }),
  ]);
  const json = (id) => JSON.parse(replies[id].result.content[0].text);
  assert.equal(replies[2].result.isError, false);
  assert.ok(Array.isArray(json(2)));
  assert.equal(json(3).pass, false); // a failing score is a result, not a tool error
  assert.equal(replies[3].result.isError, false);
  assert.equal(json(4).pass, true);
  assert.equal(typeof json(5).score, 'number');
  assert.equal(json(6).input, '-x booking app for hair salons'); // leading "-" is not parsed as a flag
  assert.ok(!replies[2].result.content[0].text.includes('\n  '), 'JSON is compacted');
});
