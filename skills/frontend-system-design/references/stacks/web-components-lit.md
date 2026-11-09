# Web Components + Lit

> **Platform:** web · **Language:** TypeScript · **Rendering:** CSR (custom elements); SSR via Declarative Shadow DOM is experimental (`@lit-labs/ssr`) · **Best for:** framework-agnostic design systems, embeddable widgets and micro-frontends shared across teams/stacks

## When to choose

| Choose it when | Avoid it when |
|---|---|
| A design system must work in React, Angular, Vue, Svelte and plain HTML/CMS pages | A single-framework product team just needs an app (use that framework's components) |
| Embeddable widgets for third-party sites (chat bubble, checkout, booking, video player) need style isolation | SEO/LCP-critical content must render server-side reliably today |
| Micro-frontends need a stable, standards-based contract between independently deployed apps | Heavy app-level concerns (routing, data loading, SSR) — Lit is a component library, not an app framework |
| Long-lived components that should outlive framework churn | Forms need deep integration with a framework's form library and team cannot handle `ElementInternals` |
| Server-rendered MPAs (Rails, Django, Laravel) need rich, reusable client widgets | Accessibility relationships must cross many shadow roots (ARIA ID references do not cross shadow boundaries) |

## Project structure

```text
design-system/
├── package.json                       # "exports" per component, "customElements": "custom-elements.json"
├── custom-elements-manifest.config.mjs
├── vite.config.ts                     # library mode, multiple entries
├── src/
│   ├── index.ts                       # registers all elements (side-effect entry)
│   ├── tokens/
│   │   ├── tokens.json                # source of truth (Style Dictionary / DTCG format)
│   │   └── tokens.css                 # generated CSS custom properties
│   ├── styles/                        # shared css`` fragments: focus-ring.ts, reset.ts
│   ├── controllers/                   # reactive controllers: FormControlController, MediaQueryController
│   ├── utils/                         # define.ts (safe customElements.define), events.ts
│   └── components/
│       ├── button/
│       │   ├── ds-button.ts           # LitElement class, static styles, @property
│       │   ├── ds-button.styles.ts
│       │   ├── ds-button.test.ts
│       │   └── ds-button.stories.ts
│       ├── dialog/ ...
│       └── combobox/ ...
├── react/                             # generated wrappers via @lit/react createComponent
├── docs/                              # Storybook / docs site
└── test/                              # shared fixtures, a11y helpers
```

- One folder per element: component, styles, test, story; tag names share a prefix (`ds-`) to avoid collisions.
- Components depend on tokens/styles/controllers, never on an app; no global CSS assumptions.
- Publish ESM with per-component entry points so consumers can import only what they use; do not bundle Lit itself into each component.
- Generate a Custom Elements Manifest (`@custom-elements-manifest/analyzer`) — it powers docs, IDE autocompletion and framework wrappers.
- Tests colocated (`*.test.ts`) and run in a real browser.

## Routing & navigation

- Lit has no official app router. For apps: `@lit-labs/router` (labs, URLPattern-based), Vaadin Router, or a small router on the Navigation API / URLPattern.
- Most Lit usage is components inside a host app — the host (Next.js, Rails, Angular) owns routing.
- Links inside components must be real `<a href>` (or slotted anchors) so host routers and middle-click work.
- Micro-frontends: a shell maps routes to custom elements and lazy-imports each remote's entry.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | `@lit/task` (`Task` controller for async data with pending/error states); host app's data layer passes data in via properties |
| URL state | Host app owns it; in Lit apps read `URLSearchParams` and update with `history.replaceState` in a reactive controller |
| Forms + validation | Form-associated custom elements (`static formAssociated = true` + `ElementInternals`: `setFormValue`, `setValidity`) so components participate in native `<form>` and constraint validation |
| Local UI state | `@state()` reactive internal properties; `@property()` for public API (reflect only what CSS needs) |
| Global client state | `@lit/context` (provider/consumer across the tree); `@lit-labs/signals` (labs) or a framework-agnostic store (Nano Stores, Zustand vanilla) via a reactive controller |

- Public API = properties in, DOM events out (`new CustomEvent('ds-change', { bubbles: true, composed: true, detail })`). Document both in the manifest.
- Pass rich data as properties, not attributes (attributes are strings).
- Avoid fetching inside design-system components; keep them presentational.

## Styling & design system

- Shadow DOM encapsulates styles: theme through **CSS custom properties** (inherit through shadow boundaries) and expose **`::part()`** for targeted overrides; use slots for content.
- Tokens: maintain in DTCG/Style Dictionary JSON, generate `tokens.css` for consumers and import shared `css` fragments into `static styles` (constructable stylesheets, shared across instances).
- Libraries: **Web Awesome** (successor to **Shoelace**), **Spectrum Web Components** (Adobe), **FAST** (Microsoft), **Ionic** (mobile-style), **Vaadin** components; Material Web is in maintenance mode — avoid for new work.
- Dark mode: swap token values under `:root[data-theme="dark"]` / `prefers-color-scheme` in the host; components only read variables.

## Performance

- Lit is small and updates only changed template parts; main costs are many element definitions and large style sheets — share styles and lazy-define rarely used elements (dynamic `import()` when first needed).
- CLS ≤ 0.1: undefined custom elements render as unknown inline elements until defined — reserve space with `:not(:defined)` styles (`display:block; min-height`) to avoid layout shift and FOUC.
- LCP ≤ 2.5s: do not render hero content only inside client-defined shadow roots; use light DOM/slots for critical text, or Declarative Shadow DOM SSR (`@lit-labs/ssr`) where it fits.
- INP ≤ 200ms: batch property updates (Lit batches per microtask), avoid synchronous layout reads in `updated()`, virtualize long lists with `@lit-labs/virtualizer`.
- Embeds: load the widget script `async`/`defer`, avoid global polyfills, and do not pull a framework runtime into a widget.

## Accessibility

- Shadow DOM breaks ID-based ARIA across roots (`aria-labelledby`, `aria-controls`, `<label for>`): keep related elements in the same root, use `ElementInternals` ARIA reflection (`internals.role`, `internals.ariaLabel`), or slot light-DOM labels.
- Use `delegatesFocus: true` in `shadowRootOptions` for composite controls; implement roving tabindex and keyboard patterns per WAI-ARIA APG.
- Form controls must be form-associated to work with native labels, validation and form reset.
- Lint with `eslint-plugin-lit`, `eslint-plugin-lit-a11y`, `eslint-plugin-wc`; run axe (it inspects shadow DOM) in component and e2e tests.
- Events must be `composed: true` to escape the shadow root, or host apps (and their focus/announcement logic) never see them.

## Testing

- **Component:** `@web/test-runner` + `@open-wc/testing` (fixtures, `chai-a11y-axe`) in real browsers, or Vitest browser mode with Playwright provider.
- **Visual/docs:** Storybook for web components (stories double as test cases), Playwright screenshot tests.
- **E2E:** Playwright (locators pierce open shadow roots by default).
- **Cross-framework:** smoke-test the built package inside React, Angular and Vue sample apps in CI.

## Build & deploy

- Build with Vite library mode or Rollup; ship ESM + `.d.ts` + `custom-elements.json`; mark `lit` as a peer/external dependency.
- Distribute via npm (and a CDN build such as jsDelivr/unpkg for script-tag consumers).
- React wrappers via `@lit/react` (`createComponent`) for property/event mapping; recent React versions handle custom element properties and events natively — test both.
- No env vars in components; configuration comes from attributes/properties set by the host. Widgets reading API keys must use publishable keys only.
- Version with semver + changesets; never remove a tag or attribute without a deprecation cycle.

## Pitfalls

- **Double `customElements.define`** (two copies of the library on a page) → throws; guard defines, ship one copy, consider scoped registries.
- **Passing objects as attributes** → `[object Object]`; use property binding (`.items=${items}` in Lit, `prop` binding in frameworks).
- **Non-composed events** → host never receives them; set `bubbles` and `composed` deliberately.
- **ARIA references across shadow roots** → broken labels; keep them in one root or use `ElementInternals`.
- **FOUC/CLS before definition** → `:not(:defined)` styles.
- **Styling via deep selectors** → impossible through shadow DOM; expose CSS variables and parts.
- **Treating Lit as an app framework** → you rebuild routing/data/SSR; use a meta-framework for the app and Lit for components.

## References

- https://lit.dev/docs/components/overview/
- https://lit.dev/docs/components/styles/
- https://lit.dev/docs/data/context/
- https://lit.dev/docs/ssr/overview/
- https://developer.mozilla.org/en-US/docs/Web/API/Web_components
- https://web.dev/articles/more-capable-form-controls
