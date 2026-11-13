#!/usr/bin/env node
'use strict';

/**
 * fsd-guard: a Claude Code PreToolUse hook that enforces the git-workflow skill's safety rules.
 * Installed by `npx frontend-system-design install --hooks`; remove its entry from .claude/settings.json
 * (hooks → PreToolUse) and delete this file to uninstall.
 *
 *   deny  git push --force / -f / +refspec, --no-verify, committing secret files (.env, keys, certificates)
 *   ask   any other git push, reset --hard, clean -f, branch -D, filter-repo/filter-branch, stash drop/clear,
 *         checkout/restore of the whole tree, tag -d
 *
 * Never blocks on its own failure: on any error it exits 0 with a note on stderr (fail open).
 * Zero dependencies; Node 18+.
 */

const { execFileSync } = require('child_process');
const path = require('path');

const RANK = { allow: 0, ask: 1, deny: 2 };

/* ---------- shell-ish parsing (good enough for guard decisions, not a full shell) ---------- */

/** Splits a command line into segments on unquoted && || ; | & and newlines; returns token arrays. */
function segments(command) {
  const out = [];
  let tokens = [];
  let cur = '';
  let quote = null;
  let has = false;
  const pushToken = () => {
    if (has) tokens.push(cur);
    cur = '';
    has = false;
  };
  const pushSegment = () => {
    pushToken();
    if (tokens.length) out.push(tokens);
    tokens = [];
  };
  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (quote) {
      if (ch === quote) quote = null;
      else if (ch === '\\' && quote === '"' && i + 1 < command.length) cur += command[++i];
      else cur += ch;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      has = true;
    } else if (ch === '\\' && i + 1 < command.length) {
      cur += command[++i];
      has = true;
    } else if (/\s/.test(ch)) {
      if (ch === '\n') pushSegment();
      else pushToken();
    } else if (ch === ';' || ch === '|' || ch === '&') {
      pushSegment();
      if (command[i + 1] === ch) i++;
    } else if (ch === '(' || ch === ')') {
      pushSegment();
    } else {
      cur += ch;
      has = true;
    }
  }
  pushSegment();
  return out;
}

const GLOBAL_WITH_VALUE = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--config-env']);

/** Finds `git <subcommand> args` in a token list; returns { dir, sub, args } or null. */
function parseGit(tokens) {
  let i = 0;
  // Skip env assignments and harmless wrappers: FOO=1 env command sudo time nice
  while (i < tokens.length && (/^[A-Za-z_][A-Za-z0-9_]*=/.test(tokens[i]) || ['env', 'command', 'sudo', 'time', 'nice', 'exec'].includes(tokens[i]))) i++;
  const exe = tokens[i];
  if (!exe || !/^git(\.exe)?$/i.test(path.basename(exe))) return null;
  i++;
  let dir = null;
  while (i < tokens.length && tokens[i].startsWith('-')) {
    const t = tokens[i];
    if (GLOBAL_WITH_VALUE.has(t)) {
      if (t === '-C') dir = dir ? path.join(dir, tokens[i + 1] || '') : tokens[i + 1] || null;
      i += 2;
    } else i++;
  }
  if (i >= tokens.length) return null;
  return { dir, sub: tokens[i], args: tokens.slice(i + 1) };
}

/** True if `flag` (e.g. 'f') is set as --long or inside a short-flag cluster like -fd. */
function hasFlag(args, short, long) {
  return args.some((a) => (long && (a === long || a.startsWith(`${long}=`))) || (short && /^-[A-Za-z]+$/.test(a) && a.slice(1).includes(short)));
}

// `git commit` options whose next token is a value (a message like "-n" must not read as a flag).
const COMMIT_VALUE_OPT = /^(-[A-Za-z]*[mFCct]|--message|--file|--author|--date|--template|--reuse-message|--reedit-message|--fixup|--squash|--trailer|--cleanup)$/;

/** The flag tokens of a commit command, skipping option values and everything after `--`. */
function commitFlags(args) {
  const flags = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--') break;
    if (!a.startsWith('-')) continue;
    flags.push(a);
    if (COMMIT_VALUE_OPT.test(a)) i++;
  }
  return flags;
}

/* ---------- secrets ---------- */

const SECRET_FILE_RES = [
  /(^|\/)\.env$/,
  /(^|\/)\.env\.(?!example$|sample$|template$|dist$|defaults$)[^/]+$/,
  /(^|\/)[^/]+\.env$/,
  /\.(pem|key|p12|pfx|jks|keystore|ppk)$/i,
  /(^|\/)id_(rsa|dsa|ecdsa|ed25519)$/,
  /(^|\/)(credentials|client_secret[^/]*|service[-_]?account[^/]*)\.json$/i,
  /(^|\/)\.(netrc|pgpass)$/,
];
const isSecretFile = (f) => SECRET_FILE_RES.some((re) => re.test(f.replace(/\\/g, '/')));

/* ---------- decision ---------- */

function decideSegment(git, ctx) {
  const { sub, args } = git;
  const verdicts = [];
  const deny = (reason) => verdicts.push({ decision: 'deny', reason });
  const ask = (reason) => verdicts.push({ decision: 'ask', reason });

  if ((sub === 'commit' || sub === 'push' || sub === 'merge' || sub === 'rebase') && args.includes('--no-verify')) {
    deny(`\`git ${sub} --no-verify\` skips the repo's hooks. Fix what the hook reports instead; the user can bypass it themselves if they really mean to.`);
  }
  if (sub === 'commit' && hasFlag(commitFlags(args), 'n', null)) {
    deny('`git commit -n` skips the repo\'s hooks (it is --no-verify). Fix what the hook reports instead.');
  }

  if (sub === 'push') {
    const forced = hasFlag(args, 'f', '--force') || args.some((a) => /^\+[^\s]/.test(a));
    const lease = args.some((a) => a.startsWith('--force-with-lease') || a.startsWith('--force-if-includes'));
    if (forced && !lease) deny('Plain force-push can overwrite other people\'s commits. Use `git push --force-with-lease` on your own branch, and only after the user asks.');
    else if (lease) ask('Force-push (with lease) rewrites the remote branch. Confirm the user asked for it.');
    else if (hasFlag(args, 'd', '--delete') || args.some((a) => /^:[^/]/.test(a))) ask('This deletes a remote branch or tag. Confirm with the user.');
    else ask('Pushing publishes commits to the remote. Confirm the user wants to push now.');
  }

  if (sub === 'commit') {
    const all = hasFlag(commitFlags(args), 'a', '--all');
    const files = ctx.changedFiles(git.dir, all);
    const secrets = files.filter(isSecretFile);
    if (secrets.length) {
      deny(`Refusing to commit likely secrets: ${secrets.slice(0, 5).join(', ')}${secrets.length > 5 ? ', …' : ''}. Unstage them (\`git restore --staged <file>\`), add them to .gitignore, and commit an example file instead.`);
    }
  }

  if (sub === 'reset' && args.includes('--hard')) ask('`git reset --hard` discards uncommitted work. Make a backup branch or stash first, and confirm with the user.');
  if (sub === 'clean' && hasFlag(args, 'f', '--force')) ask('`git clean -f` deletes untracked files permanently. Preview with `git clean -nd` and confirm with the user.');
  if (sub === 'branch' && (hasFlag(args, 'D', null) || (hasFlag(args, 'd', '--delete') && hasFlag(args, 'f', '--force')))) ask('`git branch -D` deletes a branch even if it is not merged. Confirm with the user.');
  if (sub === 'filter-repo' || sub === 'filter-branch') ask(`\`git ${sub}\` rewrites history for everyone who shares it. Confirm with the user and plan the force-push and re-clone.`);
  if (sub === 'stash' && (args[0] === 'drop' || args[0] === 'clear')) ask(`\`git stash ${args[0]}\` deletes stashed work. Confirm with the user.`);
  if ((sub === 'checkout' || sub === 'restore') && !args.includes('--staged')) {
    const dd = args.indexOf('--');
    const paths = dd >= 0 ? args.slice(dd + 1) : sub === 'restore' ? args.filter((a) => !a.startsWith('-')) : [];
    if (paths.some((p) => p === '.' || p === ':/' || p === '*') || (sub === 'checkout' && hasFlag(args, 'f', '--force'))) {
      ask(`\`git ${sub}\` here discards uncommitted changes across the tree. Stash first and confirm with the user.`);
    }
  }
  if (sub === 'tag' && hasFlag(args, 'd', '--delete')) ask('Deleting a tag can break anyone who already uses it. Confirm with the user.');
  return verdicts;
}

/**
 * Pure decision for a command line.
 * @param {string} command
 * @param {{ changedFiles?: (dir: string|null, all: boolean) => string[] }} ctx
 * @returns {{ decision: 'allow'|'ask'|'deny', reason?: string }}
 */
function decide(command, ctx = {}) {
  const context = { changedFiles: ctx.changedFiles || (() => []) };
  let best = { decision: 'allow' };
  const reasons = { ask: [], deny: [] };
  for (const tokens of segments(String(command || ''))) {
    const git = parseGit(tokens);
    if (!git) continue;
    for (const v of decideSegment(git, context)) {
      reasons[v.decision].push(v.reason);
      if (RANK[v.decision] > RANK[best.decision]) best = { decision: v.decision };
    }
  }
  if (best.decision === 'allow') return best;
  return { decision: best.decision, reason: `fsd-guard: ${[...new Set(reasons[best.decision])].join(' ')}` };
}

/** Real lookup of staged (and, for commit -a, modified tracked) files. */
function gitChangedFiles(cwd) {
  return (dir, all) => {
    const where = dir ? path.resolve(cwd, dir) : cwd;
    const run = (args) =>
      execFileSync('git', ['-C', where, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000 })
        .split('\0')
        .filter(Boolean);
    const files = run(['diff', '--cached', '--name-only', '-z']);
    if (all) files.push(...run(['diff', '--name-only', '-z']));
    return [...new Set(files)];
  };
}

function main() {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (d) => (raw += d));
  process.stdin.on('end', () => {
    try {
      const input = JSON.parse(raw || '{}');
      if (input.tool_name !== 'Bash' || !input.tool_input || typeof input.tool_input.command !== 'string') return;
      const cwd = input.cwd || process.cwd();
      const result = decide(input.tool_input.command, { changedFiles: gitChangedFiles(cwd) });
      if (result.decision === 'allow') return;
      process.stdout.write(
        JSON.stringify({ hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: result.decision, permissionDecisionReason: result.reason } })
      );
    } catch (e) {
      process.stderr.write(`fsd-guard: skipped (${e.message})\n`);
    }
  });
}

if (require.main === module) main();

module.exports = { decide, segments, parseGit, isSecretFile };
