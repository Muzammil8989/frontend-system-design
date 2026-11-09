# Reading the notes

The learning notes in [`notes/`](../notes) are plain Markdown with Mermaid diagrams and collapsible quiz answers. The easiest place to read them is GitHub, which renders everything with no setup. To read them offline in VS Code, follow the steps below.

## 1. Clone the project

```bash
git clone https://github.com/Muzammil8989/frontend-system-design.git
cd frontend-system-design
code .          # opens the folder in VS Code
```

> No Git? Download the ZIP from the green **Code** button on GitHub and extract it.

## 2. Open a note as a formatted page

1. In the sidebar, open the [`notes/`](../notes) folder, then a phase folder (`01-web-fundamentals/` … `11-system-design-cases/`), and click any `.md` file.
2. Press **`Ctrl + Shift + V`** (Mac: **`Cmd + Shift + V`**) to open the Markdown preview.
3. Press **`Ctrl + K`**, then **`V`**, to open the preview side by side with the source.

Suggested reading order: follow Phase 1 in the [README roadmap](../README.md#phase-1--web-fundamentals). Each note links to the previous and next topic.

## 3. Diagrams not showing?

GitHub renders [Mermaid](https://mermaid.js.org/) diagrams automatically. VS Code's built-in preview doesn't, so you may see raw ` ```mermaid ` code instead.

**Option 1: install the VS Code extension (recommended)**

1. Open Extensions with **`Ctrl + Shift + X`**.
2. Search for **Markdown Preview Mermaid Support** (publisher *Matt Bierner*, id `bierner.markdown-mermaid`) and click **Install**.
3. Reopen the preview with **`Ctrl + Shift + V`**.

```bash
code --install-extension bierner.markdown-mermaid
```

VS Code also suggests this extension when you open the project (see [`.vscode/extensions.json`](../.vscode/extensions.json)).

**Option 2: read on GitHub.** Diagrams work out of the box.

**Option 3: paste into [mermaid.live](https://mermaid.live).** Copy the diagram code, without the fence lines, to view it or export it as an image.

**Option 4: use another extension.** [Markdown Preview Enhanced](https://marketplace.visualstudio.com/items?itemName=shd101wyy.markdown-preview-enhanced) also renders Mermaid. Open the Command Palette with `Ctrl + Shift + P` and run **Markdown Preview Enhanced: Open Preview to the Side**.

## Troubleshooting

| Problem | Fix |
|---|---|
| Diagram shows as plain code | Install Markdown Preview Mermaid Support (Option 1) |
| Installed, but still not showing | Reload VS Code: `Ctrl + Shift + P` → **Developer: Reload Window** |
| Answers hidden under "Answer" | Click the ▶ arrow. Answers are collapsible on purpose |
| Extensions blocked (office PC, no internet) | Read on GitHub (Option 2) or use mermaid.live (Option 3) |

## Learn with your AI agent

Install the skill (see the [README](../README.md#quick-start)), then ask your agent:

```text
/fsd:learn critical rendering path
```

It teaches from the matching note: ELI5, then the core concept, a real-world example, why it matters when building, and a quiz with one question at a time.
