# Adding or upgrading a stack

Every stack the skill recommends has a reference file. Agents read that file to get the **project folder structure** and the stack-specific practices.

## 1. Write `skills/frontend-system-design/references/stacks/<ref>.md`

Use a lowercase, hyphenated `<ref>` (e.g. `remix`, `nativescript`). The validator enforces this structure, with these exact H2 headings in this order:

```text
# <Stack name>

> **Platform:** web|mobile|desktop|cross · **Language:** … · **Rendering:** … · **Best for:** …

## When to choose          (Choose it when | Avoid it when table)
## Project structure        (```text folder tree for a medium, feature-based app + 3–5 rules)
## Routing & navigation
## State & data             (state kind → tool table)
## Styling & design system
## Performance
## Accessibility
## Testing
## Build & deploy
## Pitfalls
## References               (4–6 official doc links)
```

Rules:
- Describe capabilities, not version numbers you haven't verified. Label any numbers as starting targets.
- Link only official documentation.
- Aim for about 90–160 lines: dense tables and checklists, no filler.

## 2. Register it in the data

- **`data/stacks.csv`:** add a row with `id,name,category,platform,ref,keywords,best_for,trade_offs,url`. Set `ref` to your file name without `.md`.
- **`data/product-types.csv`:** add the stack id to `stacks`, `mobile_stacks` or `desktop_stacks` for the product types where it should be recommended.
- **`scripts/detect_stack.py`:** add a detection rule if the stack has a recognisable marker (a dependency, config file or manifest).
- **`src/cli/detect.js`:** optionally add the same marker for the wizard's one-line stack label.

## 3. Test

```bash
npm run validate      # headings, links, catalog
npm run test:py       # every stacks.csv ref must have a file that follows the template
python skills/frontend-system-design/scripts/recommend.py "<product>" --stack <id>
```

In `tests/python/test_platforms.py`, add a `DetectStackTest` case with a minimal fixture project if you added a detection rule.

## 4. Mention it

Add the stack to the supported-stacks table in `README.md` and the stack list in `SKILL.md`, and add a CHANGELOG entry.
