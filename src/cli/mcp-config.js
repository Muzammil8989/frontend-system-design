'use strict';

/**
 * `install --mcp`: registers `npx frontend-system-design mcp` in each selected tool's MCP config.
 * Every file is merged in place and only our own server key is added or replaced.
 */

const { PKG } = require('./util');

const NAME = 'frontend-system-design';

/** The server command, pinned to this installer's version like the companions are. */
function serverCommand({ projectDirArg } = {}) {
  const args = ['-y', `${PKG.name}@${PKG.version}`, 'mcp', ...(projectDirArg ? ['--dir', projectDirArg] : [])];
  return { command: 'npx', args };
}

const setServer = (key, entry) => (cfg) => {
  if (cfg[key] !== undefined && (typeof cfg[key] !== 'object' || Array.isArray(cfg[key]))) throw new Error(`"${key}" is not an object; left untouched`);
  cfg[key] = { ...(cfg[key] || {}), [NAME]: entry };
  return cfg;
};

/** A JSON-merge output, plus the snippet to paste if the file can't be merged (e.g. JSONC with comments). */
const configOutput = (file, key, entry) => ({ path: file, json: setServer(key, entry), manual: `"${key}": { "${NAME}": ${JSON.stringify(entry)} }` });

/**
 * Per-tool config outputs (project scope). Tools without a project-level MCP file get a printed snippet instead.
 * @returns {{ outputs: Array<{tool: string, out: object}>, notes: string[] }}
 */
function mcpOutputs({ tools, global }) {
  const outputs = [];
  const notes = [];
  for (const tool of tools) {
    if (tool === 'claude') {
      if (global) {
        notes.push(`Claude Code (global): claude mcp add --scope user ${NAME} -- npx -y ${PKG.name}@${PKG.version} mcp`);
        continue;
      }
      // Native Windows needs the cmd /c wrapper to start npx (Claude Code docs).
      const base = serverCommand({ projectDirArg: '${CLAUDE_PROJECT_DIR:-.}' });
      const entry = process.platform === 'win32' ? { command: 'cmd', args: ['/c', base.command, ...base.args] } : base;
      outputs.push({ tool, out: configOutput('.mcp.json', 'mcpServers', entry) });
    } else if (tool === 'cursor') {
      outputs.push({ tool, out: configOutput('.cursor/mcp.json', 'mcpServers', serverCommand()) });
    } else if (tool === 'copilot') {
      outputs.push({ tool, out: configOutput('.vscode/mcp.json', 'servers', { type: 'stdio', ...serverCommand({ projectDirArg: '${workspaceFolder}' }) }) });
    } else if (tool === 'gemini') {
      outputs.push({ tool, out: configOutput('.gemini/settings.json', 'mcpServers', serverCommand()) });
    } else if (tool === 'windsurf') {
      notes.push(`Windsurf: add to ~/.codeium/windsurf/mcp_config.json → "mcpServers": { "${NAME}": ${JSON.stringify(serverCommand())} }`);
    } else if (tool === 'agents') {
      notes.push(`Codex / other MCP clients: run \`npx -y ${PKG.name}@${PKG.version} mcp\` as a stdio server (see the README's MCP section).`);
    }
  }
  return { outputs, notes };
}

module.exports = { mcpOutputs, serverCommand, NAME };
