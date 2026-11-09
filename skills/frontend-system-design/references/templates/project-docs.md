# Project docs template

The **project docs** are the living reference for a website or app: how it is built (architecture, system design) and how it looks (design tokens, color, typography, components). Write them into the user's project when they **create** a product (`/fsd:design`, or "build me a site") and refresh them with `/fsd:docs` when the code changes.

The design doc (`docs/frontend-system-design.md`) records *why* each decision was made. The project docs describe *what is true now*, so link to the design doc for the reasoning instead of repeating it.

## Rules

1. **Code wins.** When code exists, read the values from it: theme or Tailwind config, CSS custom properties, `tokens.json`, the font loading code, `package.json` versions and the folder tree. Never document a value the code doesn't have.
2. **Mark what isn't built yet.** Every table row and section shows its status: **In code** (cite `path:line`), **Proposed** (from the design doc, not built yet) or **TBD** (undecided: say what decides it).
3. **One source of truth for tokens.** `docs/design-system/tokens.json` (W3C Design Tokens format, see `references/templates/tokens.example.json`) holds the values when the project has no token file of its own. If the project already has one (Style Dictionary, Tailwind theme, a `theme.ts`), document that file and skip `tokens.json`.
4. **Compute, don't guess.** Run `scripts/tokens_check.py <tokens.json>` and paste its contrast and type-scale tables into `color.md` and `typography.md`. Without a JSON token file, compute contrast for each text/background pair the same way and say how you got it.
5. **Diagrams in Mermaid**, so they render on GitHub and in VS Code. One diagram per idea.
6. **Ask before overwriting.** If a file exists, update the sections you own and keep the user's other text. Show a summary of what changed.
7. **Scale to the product.** A landing page can merge `architecture.md` and `system-design.md` into one short file. Drop a file only when it truly doesn't apply, and say why in `docs/README.md`.

## Layout

```text
docs/
├── README.md                    # index: product in 3 lines, stack + versions, doc map with status, last updated
├── frontend-system-design.md    # the design doc from /fsd:design: the why behind every decision
├── architecture.md              # system context, rendering per route, stack, folder structure, boundaries, build & deploy
├── system-design.md             # data model, API contract, state split, caching, real-time, offline, errors, observability
├── design-system/
│   ├── README.md                # direction, principles, token pipeline (tokens → CSS vars / Tailwind / native theme)
│   ├── tokens.json              # source of truth when the project has no token file of its own
│   ├── tokens.md                # every non-color, non-type token: spacing, radius, elevation, motion, breakpoints, z-index
│   ├── color.md                 # palette, semantic roles, light/dark, contrast table
│   ├── typography.md            # families, loading, type scale, roles, responsive, i18n, rules
│   └── components.md            # inventory, API conventions, states matrix, a11y contract
└── quality.md                   # performance budgets, accessibility, security, testing, browser/device support
```

## File skeletons

Fill every section from the design doc and the code. Replace each `<…>` placeholder, and delete any instruction text in parentheses.

### `docs/README.md`

```markdown
# <Product> docs

<What the product is, who it's for and the job it does, in 3 lines.>

**Platform:** web | mobile | desktop · **Stack:** <framework x.y, styling, component library, data layer> · **Last updated:** YYYY-MM-DD

| Doc | What's in it | Status |
|---|---|---|
| [Architecture](architecture.md) | Rendering, stack, folder structure, deploy | In code / Proposed |
| [System design](system-design.md) | Data, API, state, caching, real-time, errors | … |
| [Design system](design-system/README.md) | Direction, tokens, color, typography, components | … |
| [Quality](quality.md) | Budgets, accessibility, security, testing | … |
| [Design decisions](frontend-system-design.md) | Why we chose what we chose | Approved / Draft |

## Keeping these docs current
Run `/fsd:docs` after changing tokens, routes, the data layer or dependencies.
```

### `docs/architecture.md`

```markdown
# Architecture

## System context
(Mermaid flowchart: users/devices → CDN/edge → app (web/mobile/desktop) → BFF/API → services, auth provider, analytics, plus the real-time channel)

## Rendering and app model
| Route / screen | Strategy (SSG, ISR, SSR, streaming, CSR, native screen) | Data it needs | Cache / revalidate | Status |
|---|---|---|---|---|

## Stack
| Layer | Choice | Version | Why (link a section of frontend-system-design.md) |
|---|---|---|---|
| Framework | | | |
| Styling | | | |
| Component library | | | |
| Server state / data | | | |
| Client state | | | |
| Forms & validation | | | |
| Testing | | | |
| Hosting / CI | | | |

## Folder structure
(the real tree from the project, ```text block with a one-line comment per folder)

## Module boundaries
- What may import what (e.g. `features/*` never import each other; shared code lives in `shared/`)
- How a new feature is added (the folders and files it gets)

## Build, environments and deploy
| Environment | URL | Deploys from | Notes |
|---|---|---|---|
- Env vars the frontend reads (names only, never values), feature flags, release and rollback steps
```

### `docs/system-design.md`

```markdown
# System design

## Requirements recap
Core journeys and the non-functional targets (link the design doc's requirements).

## Data model
| Entity | Key fields | Source (API / local DB / URL) | Cache key | Normalized? |
|---|---|---|---|---|
(Mermaid erDiagram or classDiagram when there are 4+ entities)

## API contract
| Operation | Method + path / query | Request | Response | Errors | Used by |
|---|---|---|---|---|---|
- Auth: how requests are authenticated; token storage (httpOnly cookie, secure storage on mobile)
- Pagination style, versioning, rate limits

## State
| Kind | Lives in | Tool | Examples |
|---|---|---|---|
| Server state | cache | | |
| URL state | route / search params | | filters, page, tab |
| Form state | form library | | |
| Local UI state | component | | open/closed |
| Global client state | store (keep tiny) | | theme, session |

## Caching and freshness
HTTP cache headers per asset type, CDN rules, client cache lifetimes, invalidation after mutations, optimistic updates.

## Real-time and offline
Channel (SSE / WebSocket / polling) and reconnect policy; offline storage, sync queue and conflict rule. Write "Not needed: <reason>" when it doesn't apply.

## Key flows
(Mermaid sequenceDiagram for the 1–3 most important journeys, e.g. sign-in, checkout, publish)

## Errors and resilience
| Failure | What the user sees | Retry policy | Logged as |
|---|---|---|---|

## Observability
RUM (Core Web Vitals or app startup), error tracking, analytics events, alerts and who gets them.
```

### `docs/design-system/README.md`

```markdown
# Design system

**Intent:** <one sentence> · **Feel:** <3 adjectives> · **Signature element:** <one memorable detail>
**Benchmarks:** <1–2 systems we learn from>

## Principles
3–5 rules that settle design arguments, e.g. "Data first: chrome stays quiet".

## How tokens reach the code
(Mermaid: tokens.json or the theme file → build step → CSS custom properties / Tailwind theme / native theme → components)
- Naming: `<category>-<role>-<variant>`, e.g. `color-text-muted`, `space-4`
- Components use **role** tokens (`color-primary`), never palette tokens (`blue-600`) or raw values
- Adding or changing a token: edit <file>, run `python3 <skill-dir>/scripts/tokens_check.py <file>`, update these docs

## Theming
Light and dark (and brand themes, if any): how a theme is selected, stored and applied without a flash on load.

| Doc | Covers |
|---|---|
| [Tokens](tokens.md) | Spacing, radius, elevation, motion, breakpoints, z-index |
| [Color](color.md) | Palette, roles, light/dark, contrast |
| [Typography](typography.md) | Fonts, scale, roles, loading |
| [Components](components.md) | Inventory, APIs, states |
```

### `docs/design-system/tokens.md`

```markdown
# Tokens

Source: `<path to tokens.json or theme file>` · Format: <DTCG / Tailwind / Style Dictionary / …>

## Spacing
| Token | Value | Use for |
|---|---|---|
(4px base. Say which steps are for gaps inside components and which are for layout.)

## Radius
| Token | Value | Use for |
|---|---|---|

## Elevation
| Token | Shadow | Dark-mode treatment | Use for |
|---|---|---|---|

## Motion
| Token | Value | Use for |
|---|---|---|
Reduced motion: what changes under `prefers-reduced-motion` (or the OS setting in apps).

## Layout
| Breakpoint | Min width | Layout change |
|---|---|---|
Grid (columns, gutters, max content width) and where container queries are used.

## Layers (z-index)
| Token | Value | Used by |
|---|---|---|

## Sizes
Icon sizes, minimum touch target (≥ 24×24 px; 44×44 px for primary touch actions), control heights.
```

### `docs/design-system/color.md`

```markdown
# Color

## Palette
| Token | Hex | Swatch note |
|---|---|---|
(The raw scale. Components never use these directly.)

## Semantic roles
| Role | Light | Dark | Use for | Never use for |
|---|---|---|---|---|
| bg | | | Page background | |
| surface / surface-raised | | | Cards, menus, dialogs | |
| text / text-muted | | | Body text / secondary text | Disabled-only meaning |
| border | | | Control edges, dividers | |
| primary / on-primary | | | Main action | Links in body text |
| danger, success, warning (+ on-*) | | | Status | The only signal (pair with an icon or text) |
| focus-ring | | | Keyboard focus | |

## Contrast
(Paste the contrast table from `tokens_check.py`. Text needs 4.5:1, or 3:1 at ≥ 24 px / ≥ 18.66 px bold; focus rings and control boundaries need 3:1.)

## Dark mode
How dark values were chosen (not inverted: lighter surfaces instead of shadows, less saturation), and how images and logos adapt.

## Data visualization
Categorical, sequential and diverging palettes if the product has charts. Write "Not needed" if it doesn't.
```

### `docs/design-system/typography.md`

```markdown
# Typography

## Families
| Role | Family | Fallback stack | Weights shipped | License / source |
|---|---|---|---|---|
| UI / body | | | | |
| Display / headings | | | | |
| Code / numbers | | | | |

## Loading
How fonts load: self-hosted or provider, `font-display` value, which 1–2 files are preloaded, subsetting, variable fonts, and the fallback metrics override that prevents layout shift (`size-adjust`, `ascent-override`). Native apps: bundled fonts and Dynamic Type / font scaling.

## Type scale
(Paste the type-scale table from `tokens_check.py`: token, size, line height, weight, tracking, step ratio.)
Base size and ratio: <16 px, ×1.25>. Fluid sizing, if used: the `clamp()` formula and the viewport range it covers.

## Roles
| Use | Token | Notes |
|---|---|---|
| Page title | | One per page |
| Section heading | | |
| Body | | Measure 60–75 characters |
| Secondary / caption | | Never below 12 px |
| Buttons and labels | | |
| Tables and metrics | | `font-variant-numeric: tabular-nums` |
| Code | | |

## Rules
- Headings follow the document outline (one h1, no skipped levels), not the visual size you want
- At most ~3 sizes per screen
- Text resizes to 200% without loss of content; apps respect the OS text-size setting
- Sentence case for UI text

## Internationalization
Scripts and languages supported, fallback fonts for them, line-height for tall scripts, RTL behavior, room for text expansion (~30–40% for German and Finnish).
```

### `docs/design-system/components.md`

```markdown
# Components

Library: <headless primitives + own styles / shadcn/ui / MUI / …> · Location: `<path>`

## Inventory
| Component | Status | Variants | Built on | Notes |
|---|---|---|---|---|

## API conventions
Prop naming (`variant`, `size`, `disabled`), composition (slots or children, compound components), controlled vs uncontrolled, forwarding refs, and styling hooks (`className`, data attributes).

## States matrix
| Component | Default | Hover | Focus | Active | Disabled | Loading | Error | Empty |
|---|---|---|---|---|---|---|---|---|

## Accessibility contract
| Component | Role / element | Keyboard | Screen-reader name | Pattern (WAI-ARIA APG) |
|---|---|---|---|---|

## Screen patterns
App shell and navigation, and the empty, loading, error, offline and permission states for each key screen.
```

### `docs/quality.md`

```markdown
# Quality

## Performance budgets
(Paste the table from `scripts/budget.py`.) The LCP element per key route, JS budget per route, image and font strategy. Where budgets are enforced (CI step, Lighthouse CI).

## Accessibility
Target: WCAG 2.2 AA. Landmarks and headings, keyboard map, focus management (dialogs, route changes), tested with <axe, screen readers, devices>.

## Security
Auth and session model, CSP, XSS sinks avoided, CSRF, third-party scripts, how secrets stay out of the client bundle.

## Testing
| Layer | Tool | What it covers | Runs in |
|---|---|---|---|
| Unit | | | |
| Component | | | |
| E2E | | Critical journeys: … | |
| Visual regression | | | |
| Accessibility | | | |

## Support
| Browsers / OS | Versions | Devices tested |
|---|---|---|
```
