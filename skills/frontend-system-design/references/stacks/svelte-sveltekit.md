# Svelte + SvelteKit

> **Platform:** web · **Language:** TypeScript · **Rendering:** SSR (default), SSG/prerender, CSR/SPA per route · **Best for:** fast, low-JS full-stack web apps and sites where a small team values simplicity and performance

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Performance and small bundles matter (mobile-heavy audiences, emerging markets) | You depend on React-only libraries (specific editors, design systems, RN sharing) |
| Small-to-mid team wants minimal boilerplate and readable components | Hiring at scale for a framework with a smaller talent pool is a risk |
| Full-stack app with forms that should work without JS (form actions + progressive enhancement) | Org mandates Angular/React for consistency across many teams |
| Mixed site: prerendered marketing + SSR app + SPA sections in one project | You need a huge catalog of enterprise-grade component suites |
| Interactive data viz, dashboards, embedded widgets | Team is mid-migration between Svelte syntaxes and cannot afford mixed codebases |

## Project structure

```text
web/
├── svelte.config.js                   # adapter, aliases, prerender options
├── vite.config.ts                     # sveltekit() plugin, vitest config
├── src/
│   ├── app.html                       # %sveltekit.head%, theme script
│   ├── app.d.ts                       # App.Locals, App.PageData, App.Error types
│   ├── hooks.server.ts                # auth session -> event.locals, security headers
│   ├── params/                        # param matchers (e.g. id.ts)
│   ├── lib/
│   │   ├── components/ui/             # design-system primitives (shadcn-svelte / Bits UI)
│   │   ├── features/
│   │   │   └── projects/
│   │   │       ├── ProjectCard.svelte
│   │   │       ├── ProjectForm.svelte
│   │   │       ├── projects.svelte.ts # shared rune-based state (class with $state)
│   │   │       └── schema.ts          # zod/valibot schema shared by form + action
│   │   ├── server/                    # server-only: db.ts, auth.ts, projects.repo.ts
│   │   └── utils/
│   ├── routes/
│   │   ├── +layout.svelte             # root shell
│   │   ├── (marketing)/
│   │   │   ├── +page.svelte
│   │   │   └── +page.ts               # export const prerender = true
│   │   ├── (app)/
│   │   │   ├── +layout.server.ts      # require user, return session
│   │   │   └── projects/
│   │   │       ├── +page.server.ts    # load + form actions (create/delete)
│   │   │       ├── +page.svelte
│   │   │       └── [id=id]/+page.server.ts
│   │   ├── api/webhooks/+server.ts    # endpoint for external callers
│   │   └── +error.svelte
│   └── styles/                        # tokens.css, app.css
├── static/
├── tests/e2e/                         # Playwright
└── .env.example
```

- `$lib/server/*` is enforced server-only: importing it from client code fails the build — put DB, secrets and auth there.
- Route files stay thin: `+page.server.ts` calls repositories in `$lib/server`; UI comes from `$lib/features` and `$lib/components`.
- Shared reactive state lives in `.svelte.ts` modules (runes work there); use context for per-request/per-user state.
- Component tests colocated (`*.svelte.test.ts` / `*.test.ts`); Playwright in `tests/e2e`.

## Routing & navigation

- File-based routing: `+page.svelte`, `+layout.svelte`, `+page.ts` (universal load), `+page.server.ts` (server load + actions), `+server.ts` (endpoints), `+error.svelte`; groups `(name)`, params `[id]`, optional `[[lang]]`, rest `[...path]`, matchers `[id=id]`.
- Client-side navigation with plain `<a href>`; preload with `data-sveltekit-preload-data="hover"` (default in the template) and `preload-code` for code only.
- `goto()`, `invalidate()`/`invalidateAll()` for programmatic navigation and refetching; `redirect()`/`error()` helpers from `@sveltejs/kit` in load/actions.
- Page options per route: `export const prerender | ssr | csr | trailingSlash`.
- Shallow routing (`pushState`/`replaceState` from `$app/navigation`) for history-backed modals.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | `load` functions (`+page.server.ts` for DB/secrets, `+page.ts` for public APIs); stream non-critical data by returning promises and using `{#await}`; TanStack Query for Svelte for polling/infinite/real-time |
| Mutations | Form actions + `use:enhance` (progressive enhancement); `+server.ts` endpoints for JSON clients; remote functions are an emerging (experimental) option |
| URL state | `page.url.searchParams` (from `$app/state`), update via `goto('?q=…', { replaceState: true, keepFocus: true })` |
| Forms + validation | Superforms + Zod/Valibot (server-validated, client-enhanced); Formsnap for accessible field markup with Bits UI |
| Local UI state | `$state`, `$derived`, `$props`, `$bindable` runes |
| Global client state | Rune-based classes/objects in `.svelte.ts` modules provided via `setContext`; stores remain supported for streams |

- Never keep user data in module-level state on the server — modules are shared across requests. Use `event.locals`, load data, or context.
- Use `$derived` for computed values; reserve `$effect` for syncing with external systems (DOM APIs, analytics), not for deriving state.
- `load` functions in parallel layouts run concurrently; avoid `await parent()` unless you need the parent's data.
- Use `depends('app:projects')` + `invalidate('app:projects')` for targeted refetch after mutations.

## Styling & design system

- Scoped `<style>` per component by default; tokens as CSS custom properties; Tailwind CSS via the Vite plugin is common.
- Components: **shadcn-svelte** (copy-in, built on Bits UI), **Bits UI** (headless), **Melt UI** (headless builders), **Skeleton**, **Flowbite Svelte**, **Ark UI** (Svelte).
- Dark mode: `mode-watcher` or an inline script in `app.html` setting `class`/`data-theme` before paint; tokens swap under `.dark`.
- Pass styling hooks to children via CSS variables (`--card-padding`) rather than `:global` overrides.

## Performance

- SSR + prerender public pages for LCP ≤ 2.5s; the compiler produces small per-route chunks and hydration cost is low.
- Stream slow data from `load` (return unawaited promises) so the shell paints immediately.
- Images: `@sveltejs/enhanced-img` (build-time AVIF/WebP, dimensions) or a CDN image service; `fetchpriority="high"` on the LCP image; explicit dimensions for CLS ≤ 0.1.
- Fonts: self-host WOFF2, preload via `<svelte:head>` or the `preload` option of `resolve()` in the `handle` hook (`hooks.server.ts`).
- INP ≤ 200ms: fine-grained reactivity avoids re-render storms; keep `$effect` chains short; virtualize long lists; lazy-import heavy libs inside `onMount`/dynamic `import()`.
- Use `csr = false` on purely static pages to ship zero JS.

## Accessibility

- The Svelte compiler emits a11y warnings (missing `alt`, click handlers on non-interactive elements, invalid ARIA) — treat them as errors in CI (`svelte-check`, `eslint-plugin-svelte`).
- SvelteKit announces route changes and resets focus to `<body>` after navigation; set a unique `<title>` per page via `<svelte:head>` so the announcement is meaningful.
- Use `keepFocus` when updating URL state from inputs so typing is not interrupted.
- Bits UI / Melt UI implement WAI-ARIA patterns for dialogs, menus, comboboxes, tabs.
- Superforms + Formsnap wire `aria-invalid`, `aria-describedby` and labels automatically.

## Testing

- **Unit/component:** Vitest + `@testing-library/svelte` (jsdom) or `vitest-browser-svelte` (Vitest browser mode, real browser).
- **Server logic:** call `load`/actions with mocked `RequestEvent`, or test `$lib/server` repositories directly.
- **Type/a11y checks:** `svelte-check` in CI.
- **E2E:** Playwright (template includes it) against `vite preview` / the built adapter output.

## Build & deploy

- Vite build; output determined by the adapter: `adapter-auto`, `adapter-node`, `adapter-static` (SSG/SPA with `fallback`), `adapter-vercel`, `adapter-netlify`, `adapter-cloudflare`.
- Env vars: `$env/static/private` / `$env/dynamic/private` are server-only (importing into client code is a build error); only `PUBLIC_*` vars are available via `$env/static/public` / `$env/dynamic/public`.
- Set security headers and CSP in `hooks.server.ts` or `kit.csp` config (supports nonces/hashes).
- Configure `kit.prerender.entries` / crawling for static routes; handle `version` polling for long-lived tabs after deploys.

## Pitfalls

- **Module-level server state** → data leaks between users; use `locals`/context.
- **`$effect` to derive state** → loops and extra renders; use `$derived`.
- **Destructuring reactive objects outside runes semantics** → lost reactivity; read properties where used or use `$derived`.
- **Mixing legacy (`export let`, `$:`) and runes syntax inconsistently** → migrate per component with `npx sv migrate`.
- **Fetching in `onMount`** instead of `load` → waterfalls and no SSR; use `load`.
- **Using `fetch` without SvelteKit's provided `fetch` in load** → loses cookies/relative URLs and response inlining.
- **Forgetting `use:enhance`** → full page reloads on submit (works, but slower UX).

## References

- https://svelte.dev/docs/svelte/what-are-runes
- https://svelte.dev/docs/kit/load
- https://svelte.dev/docs/kit/form-actions
- https://svelte.dev/docs/kit/state-management
- https://svelte.dev/docs/kit/adapters
- https://svelte.dev/docs/kit/accessibility
