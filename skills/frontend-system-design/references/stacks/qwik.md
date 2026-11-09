# Qwik + Qwik City

> **Platform:** web · **Language:** TypeScript (JSX) · **Rendering:** SSR with resumability (no hydration), SSG · **Best for:** large interactive pages where instant startup on slow devices matters more than ecosystem breadth (e-commerce storefronts, high-traffic landing + app hybrids)

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Time-to-interactive on low-end mobile is a top KPI and pages are large and interactive | You need a large, mature ecosystem of components and integrations |
| E-commerce/product pages with many widgets, most of which users never touch | Team needs abundant hiring pool, tutorials and long-term community support |
| You want SSR with JS loaded lazily per interaction, without hand-tuning islands | App is a long-session SPA behind login where startup cost is amortized (React/Vue/Solid are fine) |
| Team knows JSX and accepts the `$`/serialization rules | You rely on many browser-only libraries that expect eager initialization |
| You can absorb some framework churn (major version in progress, package namespace changes) | Strict long-term stability requirements with minimal upgrade work |

## Project structure

```text
web/
├── vite.config.ts                     # qwikCity(), qwikVite(), tsconfigPaths()
├── adapters/                          # deployment adapter configs (added via `qwik add`)
├── src/
│   ├── root.tsx                       # <QwikCityProvider>, <RouterHead>, <RouterOutlet>
│   ├── entry.ssr.tsx                  # SSR entry (renderToStream)
│   ├── entry.preview.tsx
│   ├── routes/
│   │   ├── layout.tsx                 # shell; onRequest middleware (auth, cache headers)
│   │   ├── index.tsx                  # home: head export for SEO
│   │   ├── plugin@auth.ts             # route plugin middleware
│   │   ├── products/
│   │   │   ├── index.tsx              # routeLoader$ list (query params)
│   │   │   └── [slug]/index.tsx       # routeLoader$ detail, routeAction$ add-to-cart
│   │   ├── (account)/orders/index.tsx
│   │   └── api/webhooks/index.ts      # onPost endpoint
│   ├── features/
│   │   └── cart/
│   │       ├── components/            # cart-drawer.tsx, cart-line.tsx (component$)
│   │       ├── cart.context.ts        # createContextId + store shape
│   │       ├── cart.server.ts         # server$ functions / DB access
│   │       └── schema.ts              # zod$ schemas
│   ├── components/ui/                 # design-system primitives (Qwik UI headless)
│   ├── lib/                           # env.ts, format.ts
│   └── styles/                        # tokens.css, global.css
├── public/
├── tests/e2e/
└── .env.example
```

- Route modules export `routeLoader$`/`routeAction$`; loaders used by components must be exported from a route file (`index.tsx`/`layout.tsx`) — re-export from feature files if defined there.
- Server-only code lives in `*.server.ts` and is only called from `routeLoader$`, `routeAction$`, `server$` or request handlers.
- Every closure crossing a `$` boundary must capture only serializable values — keep class instances, DOM nodes and library objects out of component state (use `noSerialize` when unavoidable).
- Unit tests colocated (`*.spec.tsx`); Playwright in `tests/e2e`.

## Routing & navigation

- Qwik City directory routing: `routes/<path>/index.tsx`, `layout.tsx` (nested), `[param]`, `[...rest]`, groups `(name)`, `plugin@*.ts` middleware.
- `<Link>` for SPA navigation with prefetching; `useNavigate()` programmatically; `useLocation()` for URL/params/pending state.
- Request handlers in route files: `onRequest`, `onGet`, `onPost` — set cache headers (`cacheControl`), redirect (`throw redirect(302, '/login')`), or return JSON.
- `head` export / `DocumentHead` for titles and meta; `routeLoader$` data can feed `head`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | `routeLoader$` (runs on server before render, typed, serialized into the page); `server$` for RPC-style calls from the client |
| Mutations | `routeAction$` + `<Form action={…}>` (progressive enhancement); `zod$` for validation; `globalAction$` for actions used across routes |
| URL state | `useLocation().url.searchParams` + `useNavigate()` to update |
| Forms + validation | `routeAction$` + `zod$`; Modular Forms (Qwik) for complex client-side forms |
| Local UI state | `useSignal`, `useStore`, `useComputed$` |
| Global client state | `useContextProvider` + `useContext` with a store (`createContextId`) |

- `useTask$` runs on server and/or client when tracked state changes; `useVisibleTask$` runs eagerly on the client when visible — use it sparingly, it defeats resumability.
- Use `useResource$` + `<Resource>` for async values that depend on reactive state.
- Keep serialized state small: everything in stores/signals is embedded in the HTML.

## Styling & design system

- `useStylesScoped$` / `useStyles$` for component CSS; tokens as CSS custom properties; Tailwind CSS via `qwik add tailwind`; CSS Modules supported.
- Components: **Qwik UI** (headless primitives plus styled kit), Modular Forms; React components can be embedded via `qwikify$` (`@builder.io/qwik-react`) but each one reintroduces hydration cost — use only for islands that have no Qwik alternative.
- Dark mode: inline script in the document head sets `class`/`data-theme` before paint; tokens swap under `.dark`.

## Performance

- Resumability: the server serializes state and listeners into HTML; JS for a handler downloads only when needed. Startup JS stays near-constant regardless of page size — good for INP ≤ 200ms on first interaction and TBT.
- Prefetching: Qwik preloads likely-needed symbols (via modulepreload/service worker depending on version); confirm in production that the first click does not wait on the network.
- LCP ≤ 2.5s: SSR + CDN caching via `cacheControl` in `onGet`; use the image optimization (`?jsx` imports / `@unpic/qwik`) with width/height and `fetchpriority="high"` on the hero.
- CLS ≤ 0.1: explicit image dimensions, reserved space for lazy content, self-hosted fonts with metric-matched fallbacks.
- Traps: `useVisibleTask$` and `qwikify$` React islands bring back eager JS; large serialized stores bloat HTML.

## Accessibility

- Server-rendered HTML with real `<form>`/`<a>` works before any JS loads — preserve that by using `<Form>` and `<Link>`.
- Route changes in SPA mode: move focus to the main heading and update the document title (`head` export); verify announcements with a screen reader.
- Qwik UI headless components follow WAI-ARIA patterns; check each component's documented keyboard support.
- Lint with `eslint-plugin-qwik` plus jsx-a11y rules; run axe in Playwright.

## Testing

- **Unit/component:** Vitest with Qwik's testing utilities (`createDOM`) for components; test pure logic and `*.server.ts` directly.
- **E2E:** Playwright against `npm run build` + preview/adapter server; include first-interaction tests (click before any JS is loaded).
- **API mocking:** MSW for client `fetch`; stub DB in server tests.

## Build & deploy

- Vite build producing client symbols and an SSR bundle; add a deployment target with `npm run qwik add` (Node/Express, Cloudflare Pages, Vercel Edge, Netlify Edge, Deno, Bun, Azure, static SSG).
- Env vars: client code sees only `import.meta.env.PUBLIC_*` (public, inlined); server code reads `requestEvent.env.get('NAME')` in loaders/actions/handlers.
- Static generation via the static adapter for marketing pages; mix with SSR routes via the server adapter.
- The next major version is moving to new package names (`@qwik.dev/*`) — pin versions and check the migration guide before upgrading.

## Pitfalls

- **Capturing non-serializable values in `$` closures** → build/runtime errors; capture IDs/plain data, use `noSerialize` for library instances.
- **`useVisibleTask$` for data loading** → eager JS and waterfalls; use `routeLoader$`.
- **Defining `routeLoader$` outside route files without re-exporting** → loader never runs.
- **Huge stores serialized into HTML** → slower TTFB/LCP; keep state minimal.
- **Wrapping many React components with `qwikify$`** → hydration costs return.
- **Assuming instant first interaction** without verifying prefetch → test on throttled network.
- **Unauthenticated `server$` functions** → callable endpoints; check auth inside.

## References

- https://qwik.dev/docs/concepts/resumable/
- https://qwik.dev/docs/components/state/
- https://qwik.dev/docs/route-loader/
- https://qwik.dev/docs/action/
- https://qwik.dev/docs/deployments/
- https://qwik.dev/docs/guides/best-practices/
