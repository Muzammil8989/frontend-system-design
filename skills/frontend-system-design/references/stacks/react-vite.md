# React + Vite (SPA)

> **Platform:** web · **Language:** TypeScript · **Rendering:** CSR (optional prerender of static routes) · **Best for:** authenticated apps, dashboards and internal tools where SEO does not matter

## When to choose

| Choose it when | Avoid it when |
|---|---|
| The app lives behind login (SaaS console, admin, CRM, back office) | Public pages need SEO, social previews or fast first paint on slow devices |
| You already have a separate API (REST/GraphQL/BFF) owned by another team | You want server-side data loading, mutations and auth in one codebase (use Next.js / React Router framework) |
| You want static hosting (S3 + CDN, Netlify, Cloudflare Pages) with zero server runtime | First-load LCP on low-end mobile is a business KPI (e-commerce, media) |
| Heavy client interactivity: editors, canvases, drag-and-drop, real-time dashboards | Content is mostly static (docs, blog, marketing) — use Astro or an SSG |
| The team wants a minimal, unopinionated toolchain and fast HMR | The team lacks discipline to own routing/data/folder conventions itself |
| Embedding inside another host (Electron, Tauri, micro-frontend shell) | You need streaming HTML or edge personalization |

## Project structure

```text
web/
├── index.html                    # single HTML entry; preload critical font here
├── vite.config.ts                # aliases (@/), plugins, manualChunks if needed
├── public/                       # copied as-is (favicons, robots.txt)
├── src/
│   ├── main.tsx                  # createRoot, providers, router mount
│   ├── app/
│   │   ├── providers.tsx         # QueryClientProvider, ThemeProvider, ErrorBoundary
│   │   ├── router.tsx            # route tree, lazy route modules
│   │   └── layouts/              # AppShell, AuthLayout
│   ├── features/
│   │   ├── billing/
│   │   │   ├── api/              # queries.ts (queryOptions), mutations.ts
│   │   │   ├── components/       # InvoiceTable.tsx, PlanCard.tsx
│   │   │   ├── routes/           # BillingPage.tsx (lazy-loaded)
│   │   │   ├── schemas.ts        # zod schemas shared by forms + API parsing
│   │   │   └── index.ts          # public API of the feature
│   │   └── projects/ ...
│   ├── shared/
│   │   ├── ui/                   # design-system primitives (Button, Dialog, Field)
│   │   ├── lib/                  # http client, formatters, cn()
│   │   ├── hooks/                # useMediaQuery, useDebounce
│   │   └── config/env.ts         # validated import.meta.env access
│   ├── styles/                   # tokens.css, globals.css
│   └── test/                     # setup.ts, MSW handlers, render helpers
├── e2e/                          # Playwright specs
└── .env.example
```

- Features import from `shared/` and from other features only through their `index.ts`; enforce with `eslint-plugin-boundaries` or `import/no-restricted-paths`.
- `shared/` never imports from `features/` or `app/`.
- Unit/component tests colocated as `*.test.tsx`; e2e lives in `/e2e`.
- One route = one lazy module (`routes/*Page.tsx`) so each route is its own chunk.
- Validate env once in `shared/config/env.ts`; nothing else reads `import.meta.env` directly.

## Routing & navigation

- **React Router** (declarative or data mode with `createBrowserRouter`, loaders, `lazy`) or **TanStack Router** (fully type-safe params/search, built-in search-param validation, route-level loaders integrating with TanStack Query).
- Code-split per route with `lazy()` / route `lazy`; show a skeleton in the layout, not a full-page spinner.
- Prefetch on hover/intent (TanStack Router `preload="intent"`, or call `queryClient.prefetchQuery` in `onMouseEnter`).
- Static hosting needs an SPA fallback: rewrite unknown paths to `/index.html` (but keep a real 404 route).
- Auth guards: redirect in loaders / `beforeLoad`, not inside rendered components (avoids flashing protected UI).

## State & data

| State kind | Recommended tool |
|---|---|
| Server state (remote data) | TanStack Query (`queryOptions` factories per feature); RTK Query if already on Redux; Apollo/urql for GraphQL |
| URL state (filters, tabs, pagination) | Router search params; TanStack Router validated search schemas or `nuqs` |
| Forms + validation | React Hook Form + Zod (`@hookform/resolvers`); TanStack Form as an alternative |
| Local UI state | `useState` / `useReducer`; lift only as far as needed |
| Global client state | Zustand (small slices) or Jotai (atomic); Redux Toolkit for large teams needing devtools/conventions; Context only for low-frequency values (theme, auth user) |

- Never copy server data into Zustand/Redux — keep it in the query cache and derive.
- Set a sensible default `staleTime` (e.g. 30-60s for dashboards) to avoid refetch storms; invalidate by key after mutations.
- Use optimistic updates via `onMutate` + rollback for toggles/likes; use `useSuspenseQuery` with route-level Suspense boundaries for predictable loading UI.
- Real-time: WebSocket/SSE events call `queryClient.setQueryData` or `invalidateQueries`; do not keep a parallel store.
- Mock the API with MSW in dev and tests so the frontend is not blocked on backend.

## Styling & design system

- Tokens as CSS custom properties (`--color-bg`, `--space-4`, `--radius-md`) in `styles/tokens.css`; map them into Tailwind's theme or CSS Modules.
- Component options: **shadcn/ui** (copy-in, Radix or Base UI + Tailwind), **Radix Primitives**, **React Aria Components** (strongest a11y/i18n), **Ark UI**, **Mantine**, **MUI**, **Chakra UI**. Pick one primitive layer; do not mix two headless libraries.
- Dark mode: `[data-theme="dark"]` or `.dark` class on `<html>` swapping token values; set it from an inline script in `index.html` before first paint to avoid a flash.
- Respect `prefers-reduced-motion`; keep motion in tokens (durations, easings).

## Performance

- CSR means LCP waits for JS: keep the entry chunk small, lazy-load routes, and render a meaningful shell from `index.html` (app frame skeleton) to help LCP ≤ 2.5s.
- Analyze bundles with `rollup-plugin-visualizer`; watch for icon libraries, date libraries and charting libs pulled into the entry chunk.
- `<link rel="preload">` the primary font (WOFF2, `font-display: swap`, size-adjusted fallback) and the LCP image; set `width`/`height` on images to keep CLS ≤ 0.1.
- INP ≤ 200ms: avoid re-rendering large trees on keystroke (split context, use selectors in Zustand, `useDeferredValue`/`useTransition` for expensive filtering, virtualize long lists with TanStack Virtual).
- React Compiler (Babel plugin) can remove most manual `useMemo`/`useCallback`; profile with React DevTools Profiler before hand-optimizing.
- Prerender public routes (landing, pricing) with a plugin or move them to a separate static site.

## Accessibility

- SPA route changes are silent: on navigation move focus to the page `<h1>` (or main) and update `document.title`; consider a visually hidden live region announcing the new page.
- Lint with `eslint-plugin-jsx-a11y`; test with `@axe-core/playwright` or `vitest-axe`.
- Prefer headless libraries (Radix, React Aria, Ark) for dialogs, menus, comboboxes, tabs — they handle focus trapping, roving tabindex and ARIA.
- Use `<button>`/`<a href>` not clickable `<div>`s; React Router `<Link>` renders real anchors.
- Form errors: associate with `aria-describedby`, set `aria-invalid`, move focus to the first error on submit (RHF `shouldFocusError`).

## Testing

- **Unit/component:** Vitest + React Testing Library + `@testing-library/user-event`; jsdom or happy-dom; Vitest browser mode for real-browser component tests.
- **API mocking:** MSW shared between tests, Storybook and local dev.
- **E2E:** Playwright (auth via stored `storageState`, run against `vite preview` build).
- **Visual/docs:** Storybook with interaction and a11y addons; optional Chromatic/Playwright screenshots.

## Build & deploy

- `vite build` produces static assets with hashed filenames; serve `index.html` with `Cache-Control: no-cache` and `/assets/*` as immutable.
- Hosts: any static host/CDN (Cloudflare Pages, Netlify, Vercel, S3 + CloudFront, Azure Static Web Apps, nginx container).
- Env vars: only variables prefixed `VITE_` are exposed via `import.meta.env` — and they are **public, baked into the bundle**. Never put secrets there; secrets belong to the API/BFF.
- For per-environment config without rebuilds, fetch a `/config.json` at boot or inject `window.__CONFIG__` at serve time.
- Add security headers (CSP, HSTS) at the CDN; SPAs commonly need `connect-src` for the API origin.

## Pitfalls

- **Fetching in `useEffect` everywhere** → race conditions, no caching, waterfalls. Use TanStack Query or router loaders.
- **Request waterfalls from nested components** → hoist fetches to route loaders or prefetch in parallel.
- **Giant entry bundle** from barrel files and eager imports → lazy routes, avoid `export *` barrels in hot paths.
- **Secrets in `VITE_*` vars** → anything in the bundle is public; proxy through a server.
- **Context as global store** causing app-wide re-renders → Zustand/Jotai with selectors, or split contexts.
- **No SPA fallback** → deep links 404 on refresh; configure rewrites.
- **Unvalidated API responses** → parse with Zod at the boundary for critical data.

## References

- https://vite.dev/guide/env-and-mode
- https://vite.dev/guide/build
- https://react.dev/reference/react/lazy
- https://react.dev/learn/react-compiler
- https://tanstack.com/query/latest/docs/framework/react/overview
- https://tanstack.com/router/latest/docs/framework/react/overview
