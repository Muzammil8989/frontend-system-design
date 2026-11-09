'use strict';

/**
 * Detects which AI coding tools the user has, so the wizard can preselect them,
 * and gives a quick one-line guess of the project's stack for the intro banner.
 * (The skill's scripts/detect_stack.py does the thorough stack detection.)
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

function onPath(cmd) {
  const exts = process.platform === 'win32' ? (process.env.PATHEXT || '.EXE;.CMD;.BAT').split(';') : [''];
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    if (!dir) continue;
    for (const ext of exts) {
      try {
        if (fs.statSync(path.join(dir, cmd + ext.toLowerCase())).isFile()) return true;
      } catch {
        /* not here */
      }
      try {
        if (ext && fs.statSync(path.join(dir, cmd + ext)).isFile()) return true;
      } catch {
        /* not here */
      }
    }
  }
  return false;
}

const has = (p) => fs.existsSync(p);

/** @returns {Record<string, string|false>} tool id → reason it was detected (or false) */
function detectTools(cwd = process.cwd(), home = os.homedir()) {
  const why = (checks) => {
    for (const [ok, reason] of checks) if (ok) return reason;
    return false;
  };
  return {
    claude: why([[onPath('claude'), '`claude` on PATH'], [has(path.join(cwd, '.claude')), '.claude/ in project'], [has(path.join(home, '.claude')), '~/.claude']]),
    cursor: why([[onPath('cursor'), '`cursor` on PATH'], [has(path.join(cwd, '.cursor')), '.cursor/ in project'], [has(path.join(home, '.cursor')), '~/.cursor']]),
    copilot: why([[onPath('code'), '`code` (VS Code) on PATH'], [has(path.join(cwd, '.github', 'copilot-instructions.md')), 'copilot-instructions.md'], [has(path.join(cwd, '.vscode')), '.vscode/ in project']]),
    windsurf: why([[onPath('windsurf'), '`windsurf` on PATH'], [has(path.join(cwd, '.windsurf')), '.windsurf/ in project'], [has(path.join(home, '.codeium', 'windsurf')), '~/.codeium/windsurf']]),
    gemini: why([[onPath('gemini'), '`gemini` on PATH'], [has(path.join(home, '.gemini')), '~/.gemini'], [has(path.join(cwd, 'GEMINI.md')), 'GEMINI.md']]),
    agents: why([[onPath('codex'), '`codex` on PATH'], [has(path.join(home, '.codex')), '~/.codex'], [has(path.join(cwd, 'AGENTS.md')), 'AGENTS.md']]),
  };
}

const NPM_STACKS = [
  ['expo', 'Expo (React Native)'], ['react-native', 'React Native'], ['@capacitor/core', 'Capacitor'], ['@tauri-apps/api', 'Tauri'],
  ['electron', 'Electron'], ['next', 'Next.js'], ['nuxt', 'Nuxt'], ['@sveltejs/kit', 'SvelteKit'], ['astro', 'Astro'],
  ['@angular/core', 'Angular'], ['@builder.io/qwik', 'Qwik'], ['solid-js', 'Solid'], ['@react-router/dev', 'React Router'],
  ['lit', 'Lit'], ['vue', 'Vue'], ['svelte', 'Svelte'], ['react', 'React'],
];

/** @returns {string|null} a short human label for the project's stack */
function detectStack(cwd = process.cwd()) {
  const found = [];
  try {
    const pkg = JSON.parse(fs.readFileSync(path.join(cwd, 'package.json'), 'utf8'));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    const hit = NPM_STACKS.find(([dep]) => dep in deps);
    if (hit) found.push(hit[1]);
  } catch {
    /* no package.json */
  }
  const read = (f) => {
    try {
      return fs.readFileSync(path.join(cwd, f), 'utf8');
    } catch {
      return '';
    }
  };
  if (/^\s*flutter\s*:/m.test(read('pubspec.yaml'))) found.push('Flutter');
  if (/androidx\.compose|compose\s*=\s*true/.test(read('app/build.gradle.kts') + read('app/build.gradle'))) found.push('Jetpack Compose');
  if (has(path.join(cwd, 'Package.swift')) || fs.readdirSync(cwd).some((f) => f.endsWith('.xcodeproj'))) found.push('Swift / SwiftUI');
  if (fs.readdirSync(cwd).some((f) => f.endsWith('.csproj') && /UseMaui/.test(read(f)))) found.push('.NET MAUI');
  return found.length ? [...new Set(found)].join(' + ') : null;
}

module.exports = { detectTools, detectStack, onPath };
