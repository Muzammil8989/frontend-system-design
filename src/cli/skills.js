'use strict';

/**
 * Skill catalog: which skills ship, and which agents/commands belong to each.
 * Adding a skill = add a folder under skills/ and an entry here.
 */

const fs = require('fs');
const path = require('path');
const { PKG_ROOT, read, splitFrontmatter, walk } = require('./util');

const SKILLS = [
  {
    id: 'frontend-system-design',
    label: 'Frontend System Design',
    hint: 'architecture + UI for web, mobile & desktop, every stack; audits; learning notes',
    agents: ['frontend-architect', 'ui-designer', 'mobile-engineer', 'performance-engineer', 'accessibility-specialist', 'security-reviewer', 'ui-ux-reviewer'],
    commands: ['design', 'docs', 'audit', 'learn'],
  },
  {
    id: 'product-copywriting',
    label: 'Product Copywriting',
    hint: 'human-sounding website & app copy: landing pages, onboarding, microcopy',
    agents: ['copywriter'],
    commands: ['copy'],
  },
  {
    id: 'git-workflow',
    label: 'Git Workflow',
    hint: 'clean commits, PRs, safe undo & releases: Conventional Commits, semver, changelog',
    agents: [],
    commands: ['commit', 'pr', 'undo', 'release'],
  },
];

const skillDir = (id) => path.join(PKG_ROOT, 'skills', id);
const byId = (id) => SKILLS.find((s) => s.id === id);

/** Points a skill body at its installed location (used where an agent can't resolve relative paths). */
function localize(text, dir) {
  return text
    .replace(/<skill-dir>/g, dir)
    .replace(/(?<![\w/.-])(references|scripts|data)\//g, (m, folder) => `${dir}/${folder}/`);
}

/** All files of a skill, mapped under targetDir; SKILL.md gets `<skill-dir>` resolved. */
function skillFiles(id, targetDir, displayDir = targetDir) {
  const src = skillDir(id);
  return walk(src).map((rel) => {
    let content = read(path.join(src, rel));
    if (rel === 'SKILL.md') content = content.replace(/<skill-dir>/g, displayDir);
    return { path: `${targetDir}/${rel}`, content };
  });
}

const skillMd = (id) => splitFrontmatter(read(path.join(skillDir(id), 'SKILL.md')));
const agentFile = (name) => read(path.join(PKG_ROOT, 'agents', `${name}.md`));
const commandFile = (name) => splitFrontmatter(read(path.join(PKG_ROOT, 'commands', `${name}.md`)));
const exists = (id) => fs.existsSync(path.join(skillDir(id), 'SKILL.md'));

module.exports = { SKILLS, byId, skillDir, localize, skillFiles, skillMd, agentFile, commandFile, exists };
