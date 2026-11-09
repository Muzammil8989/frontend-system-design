# Solid + SolidStart

> **Platform:** web · **Language:** TypeScript (JSX) · **Rendering:** CSR (Solid + Vite); SSR with streaming, SSG/prerender, server functions (SolidStart) · **Best for:** highly interactive, performance-critical UIs where fine-grained reactivity beats virtual-DOM re-rendering

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Real-time dashboards, trading/monitoring UIs, editors with frequent updates | You need a broad ecosystem of ready-made React components and integrations |
| Team knows JSX/React but wants signals and no re-render model | Team cannot absorb Solid's different mental model (components run once) |
| Bundle size and INP are top constraints (embedded widgets, low-end devices) | Large org needing a big hiring pool and long-term vendor support guarantees |
| You want a lean full-stack option (SolidStart server functions, SSR, streaming) | Content-heavy site with little interactivity (Astro is simpler) |
| Greenfield app where you control all dependencies | You need mature enterprise component suites (data grids, schedulers) out of the box |

## Project structure

```text
web/
├── app.config.ts                      # SolidStart config: server preset, prerender (file name varies by version)
├── src/
│   ├── app.tsx                        # <Router root={Layout}> + <FileRoutes/>, MetaProvider
│   ├── entry-client.tsx               # mount/hydrate
│   ├── entry-server.tsx               # document shell (<html>, assets, theme script)
│   ├── middleware.ts                  # auth/session, headers
│   ├── routes/
│   │   ├── index.tsx
│   │   ├── (app)/
│   │   │   ├── projects/
│   │   │   │   ├── index.tsx          # list; route `preload` warms query()
│   │   │   │   └── [id].tsx
│   │   │   └── settings.tsx
│   │   ├── api/webhooks/stripe.ts     # API route (GET/POST exports)
│   │   └── [...404].tsx
│   ├── features/
│   │   └── projects/
│   │       ├── components/            # ProjectTable.tsx, ProjectForm.tsx
│   │       ├── api.ts                 # query()/action() wrappers around "use server" functions
│   │       ├── server.ts              # "use server" DB access, auth checks
│   │       └── schema.ts              # zod/valibot
│   ├── components/ui/                 # Kobalte-based design-system primitives
│   ├── lib/                           # session.ts, env.ts, utils.ts
│   └── styles/                        # tokens.css, app.css
├── public/
├── tests/e2e/
└── .env.example
```

- Solid SPA variant: `vite-plugin-solid`, `src/index.tsx` with `render()`, routes defined via `@solidjs/router` config; same `features/` layout.
- Server functions (`"use server"`) live in dedicated `server.ts` files per feature; they must validate input and check auth.
- Components never destructure props; use `splitProps`/`mergeProps` (enforced by `eslint-plugin-solid`).
- Colocate unit tests (`*.test.tsx`); Playwright in `tests/e2e`.

## Routing & navigation

- `@solidjs/router`: nested routes, `<A>` links (active classes), `useNavigate`, `useParams`, `useSearchParams`, lazy route components.
- Data APIs: `query()` (cached, deduped fetchers, formerly `cache`), `createAsync()` to consume, route `preload` functions to start fetching on link hover/navigation in parallel with code loading.
- SolidStart file routes in `src/routes` (`[id].tsx`, `[...rest].tsx`, `(group)/`), rendered via `<FileRoutes />`.
- Redirects from server functions/queries with `redirect()`; `revalidate()` keys after actions.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | Router `query()` + `createAsync()` (SSR-aware, cached, revalidated by actions); TanStack Query for Solid for complex client caching/polling |
| Mutations | `action()` + `<form action={myAction} method="post">` or `useAction`; `useSubmission`/`useSubmissions` for pending and optimistic UI |
| URL state | `useSearchParams()` |
| Forms + validation | Modular Forms (Solid) or TanStack Form (Solid) with Zod/Valibot; re-validate in server functions |
| Local UI state | `createSignal`, `createMemo` |
| Global client state | `createStore` (nested reactive state, `produce`/`reconcile`) shared via context; module-level signals only in client-only apps |

- Components run once; reactivity lives in signals read inside JSX/effects. Reading a signal outside a tracking scope (e.g. in the component body to a const) freezes the value.
- Use `createMemo` for derived values; `createEffect` only for side effects.
- Use `reconcile` when replacing store data from the server to keep fine-grained updates.
- On the server, avoid module-level signals/stores (shared across requests).

## Styling & design system

- Tokens as CSS variables; Tailwind CSS, CSS Modules, or zero-runtime solutions (vanilla-extract, Panda CSS).
- Components: **Kobalte** (headless, accessible primitives), **Ark UI** (Solid), **Corvu** (headless), **solid-ui** (shadcn-style, built on Kobalte), **SUID** (Material port).
- Dark mode: inline script in `entry-server.tsx` sets `class`/`data-theme` before paint; tokens swap under `.dark`.
- Use `classList` for conditional classes; style props via CSS variables.

## Performance

- Fine-grained updates touch only changed DOM nodes — the main INP risk is expensive synchronous work in handlers, not rendering. Keep handlers small, batch with `batch()`, offload heavy work to Web Workers.
- SSR with streaming and `<Suspense>` boundaries per data region keeps TTFB/LCP low (LCP ≤ 2.5s); prerender static routes in `app.config.ts`.
- Use `<For>` (keyed by reference) / `<Index>` (keyed by index) instead of `array.map` for lists; virtualize long lists (TanStack Virtual for Solid).
- `lazy()` route components and heavy widgets; `clientOnly()` for browser-only libraries.
- No built-in image component: use `<img>` with width/height, `fetchpriority`, `loading="lazy"`, or a CDN image service (`unpic`); preload fonts in the document shell (CLS ≤ 0.1).

## Accessibility

- `eslint-plugin-solid` catches reactivity bugs; add `eslint-plugin-jsx-a11y` for markup rules.
- Route changes: manage focus manually (focus `<h1>`/main after navigation) and set titles with `@solidjs/meta` `<Title>`.
- Kobalte/Ark UI/Corvu implement WAI-ARIA patterns (dialog, menu, combobox, tabs) — prefer them over hand-rolled widgets.
- Forms via `action()` work without JS when using `<form action={…} method="post">`; still render field errors with `aria-invalid` and `aria-describedby`.

## Testing

- **Unit/component:** Vitest + `@solidjs/testing-library` (+ `@testing-library/user-event`), jsdom; configure `vite-plugin-solid` for tests.
- **Reactive logic:** test signals/stores inside `createRoot` to control disposal.
- **E2E:** Playwright against the production build.
- **API mocking:** MSW.

## Build & deploy

- Solid SPA: Vite + `vite-plugin-solid` → static hosting with SPA fallback.
- SolidStart: Vite-based build with Nitro server presets (Node, Vercel, Netlify, Cloudflare, AWS, static); select via `server.preset` in `app.config.ts`.
- Env vars: client code sees only `VITE_*` (public, inlined); server functions read `process.env`. Anything returned from a server function to the client is public.
- Server functions are HTTP endpoints — rate-limit and authorize them.

## Pitfalls

- **Destructuring props** (`({ title })`) → loses reactivity; use `props.title` or `splitProps`.
- **Reading signals at component top-level into constants** → value never updates; read inside JSX or `createMemo`.
- **Using `array.map` in JSX** → recreates nodes; use `<For>`/`<Index>`.
- **Early returns in components** for conditional UI → component runs once; use `<Show>`/`<Switch>`.
- **`createEffect` writing signals to derive state** → loops; use `createMemo`.
- **Unauthenticated `"use server"` functions** → exposed endpoints; check session and validate.
- **Assuming React ecosystem libraries work** → they need Solid equivalents or wrappers.

## References

- https://docs.solidjs.com/concepts/signals
- https://docs.solidjs.com/concepts/components/props
- https://docs.solidjs.com/solid-router
- https://docs.solidjs.com/solid-start
- https://docs.solidjs.com/solid-start/building-your-application/data-loading
- https://kobalte.dev/docs/core/overview/introduction
