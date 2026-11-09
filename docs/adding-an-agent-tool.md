# Supporting another AI coding tool

The installer has one adapter per tool, in `src/cli/adapters/index.js`. An adapter returns the list of files to write. The writer handles idempotency, managed blocks and `--force`/`--dry-run`.

## 1. Find out what the tool reads

Check the tool's **official docs** for:
- **Native skills support** (`SKILL.md` folders), and from which paths. Many tools read `.agents/skills/`.
- **Project rules/instructions**: file location, frontmatter (trigger or glob fields), size limits.
- **Prompt or command files**, if it has any.

## 2. Add the adapter

```js
newtool: {
  label: 'New Tool',
  global: false,                       // true only if you implement a user-level install
  outputs({ skills }) {
    return [
      ...shared(skills),               // copies skills into .agents/skills/<id>/
      ...skills.map((id) => ({         // a pointer the tool always loads
        path: `.newtool/rules/${id}.md`,
        content: withFrontmatter({ description: quote(skillMd(id).meta.description) },
          `Read \`${sharedPath(id)}\` and follow its workflow.\n`),
      })),
      // or a managed block in a shared file:
      // { path: 'NEWTOOL.md', heading: '# NEWTOOL.md', block: pointerBlock(skills) },
    ];
  },
},
```

Prefer **pointers** to copying full skill bodies into rule files. Rules are often loaded into every session, and some tools cap their size.

## 3. Detection and companions

- **`src/cli/detect.js`:** add a check (CLI on PATH, a home folder or a project folder) so the wizard preselects the tool.
- **`companions.json`:** add the tool's id to each companion's `agents` map, but only where that companion's official installer documents support for it.

## 4. Tests and docs

- In `tests/node/installer.test.js`, assert the new files exist after `install --all`.
- In `.github/workflows/ci.yml`, add a `test -f` line in the installer job.
- Update the README tool table, `THIRD_PARTY.md` (if companions changed), and `CHANGELOG.md`.
- Add the output paths to `.gitignore`, so contributors who run the installer inside this repo don't commit them.
