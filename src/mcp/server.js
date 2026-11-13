'use strict';

/**
 * `npx frontend-system-design mcp`: a zero-dependency MCP server on stdio.
 * Newline-delimited JSON-RPC 2.0; stdout carries protocol messages only, logs go to stderr.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { PKG } = require('../cli/util');
const { callTool, toolList } = require('./tools');

const SUPPORTED = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05'];
const log = (msg) => process.stderr.write(`[frontend-system-design mcp] ${msg}\n`);

/** The folder tools may read: --dir, then $FSD_MCP_ROOT, then the working directory. */
function resolveRoot(opts = {}) {
  for (const candidate of [opts.dir, process.env.FSD_MCP_ROOT]) {
    if (!candidate) continue;
    const abs = path.resolve(candidate);
    if (fs.existsSync(abs) && fs.statSync(abs).isDirectory()) return fs.realpathSync(abs);
    log(`ignoring root "${candidate}" (not a folder)`);
  }
  return fs.realpathSync(process.cwd());
}

/** Handles one parsed message; returns a response object, or null for notifications. */
async function handle(msg, ctx) {
  const isRequest = msg && msg.id !== undefined && msg.id !== null;
  const reply = (result) => ({ jsonrpc: '2.0', id: msg.id, result });
  const error = (code, message) => ({ jsonrpc: '2.0', id: isRequest ? msg.id : null, error: { code, message } });

  if (!msg || msg.jsonrpc !== '2.0' || typeof msg.method !== 'string') return isRequest ? error(-32600, 'Invalid Request') : null;
  if (!isRequest) return null; // notifications (initialized, cancelled, …) need no answer

  switch (msg.method) {
    case 'initialize': {
      const asked = msg.params && msg.params.protocolVersion;
      return reply({
        protocolVersion: SUPPORTED.includes(asked) ? asked : SUPPORTED[0],
        capabilities: { tools: {} },
        serverInfo: { name: PKG.name, version: PKG.version },
        instructions:
          'Frontend system design tools. Start with recommend for a new product, detect_stack/audit_scan for existing code, ' +
          'list_notes + read_note to ground a decision in the learning notes, copy_check for UI copy and commit_check for commit messages.',
      });
    }
    case 'ping':
      return reply({});
    case 'tools/list':
      return reply({ tools: toolList() });
    case 'tools/call': {
      const { name, arguments: args = {} } = msg.params || {};
      if (typeof name !== 'string' || typeof args !== 'object' || args === null) return error(-32602, 'Invalid params: expected { name, arguments }');
      const result = await callTool(name, args, ctx);
      return result ? reply(result) : error(-32602, `Unknown tool: ${name}`);
    }
    default:
      return error(-32601, `Method not found: ${msg.method}`);
  }
}

function start(opts = {}) {
  const ctx = { root: resolveRoot(opts) };
  log(`v${PKG.version} ready on stdio; tools may read ${ctx.root}`);
  const send = (obj) => process.stdout.write(`${JSON.stringify(obj)}\n`);
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  let pending = Promise.resolve();
  rl.on('line', (line) => {
    if (!line.trim()) return;
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } });
      return;
    }
    // Answer in order; a slow tool call doesn't reorder later replies.
    pending = pending
      .then(() => handle(msg, ctx))
      .then((res) => res && send(res))
      .catch((e) => {
        log(`error: ${e.stack || e.message}`);
        if (msg && msg.id !== undefined) send({ jsonrpc: '2.0', id: msg.id, error: { code: -32603, message: 'Internal error' } });
      });
  });
  return new Promise((resolve) => rl.on('close', () => pending.then(resolve)));
}

module.exports = { start, handle, resolveRoot, SUPPORTED };
