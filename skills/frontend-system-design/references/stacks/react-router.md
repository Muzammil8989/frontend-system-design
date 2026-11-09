# React Router (framework mode, Remix lineage)

> **Platform:** web · **Language:** TypeScript · **Rendering:** SSR (default), SPA mode, static prerender per route · **Best for:** web-standards full-stack React apps with forms, mutations and progressive enhancement

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Data-heavy CRUD apps where loaders/actions map cleanly to routes (admin, SaaS, booking) | Mostly static content sites (Astro or an SSG is lighter) |
| You want progressive enhancement: forms that work before JS loads | You rely heavily on React Server Components patterns and their ecosystem (Next.js is more mature there) |
| You value Web Fetch API primitives (`Request`, `Response`, `FormData`, headers, cookies) over framework magic | You need image optimization, ISR and similar features built in rather than assembled |
| Existing Remix or React Router app that should evolve incrementally | Team wants a pure client SPA with an external API and no server (library mode + Vite is enough) |
| Deploying to many runtimes (Node, Cloudflare Workers, Vercel, Netlify, Deno/Bun) | You need a large plugin ecosystem of framework-specific integrations |

## Project structure

```text
web/
├── react-router.config.ts        # ssr: true|false, prerender: [...], appDirectory
├── vite.config.ts                # reactRouter() plugin, tsconfigPaths()
├── app/
│   ├── root.tsx                  # <html>, Links/Meta/Scripts, root ErrorBoundary
│   ├── routes.ts                 # route config: route(), index(), layout(), prefix()
│   ├── entry.server.tsx          # optional: streaming, headers, CSP nonce
│   ├── routes/
│   │   ├── _marketing.home.tsx   # loader + meta + component
│   │   ├── app.layout.tsx        # authenticated layout; loader requires user
│   │   ├── app.projects.tsx      # list: loader (query params), action (create)
│   │   ├── app.projects.$id.tsx  # detail: loader, action (update/delete via intent)
│   │   └── api.webhooks.stripe.ts# resource route (no default export)
│   ├── features/
│   │   └── projects/
│   │       ├── components/       # ProjectTable.tsx, ProjectForm.tsx
│   │       ├── projects.server.ts# data access; .server excluded from client bundle
│   │       └── schemas.ts        # zod schemas for actions
│   ├── components/ui/            # design-system primitives
│   ├── lib/
│   │   ├── session.server.ts     # cookie session storage, requireUser()
│   │   ├── env.server.ts         # validated server env
│   │   └── utils.ts
│   └── styles/app.css
├── e2e/
└── .react-router/types/          # generated route types (gitignored)
```

- Route modules stay thin: `loader`/`action` call into `features/*/*.server.ts`; components import UI from `features/` and `components/ui`.
- Anything touching DB, secrets or sessions lives in `*.server.ts` files (or `.server/` folders) so the bundler refuses to ship them to the client.
- Use generated types: `import type { Route } from "./+types/app.projects"` for typed `loaderData`, `actionData`, `params`.
- Tests colocated (`*.test.tsx`); Playwright in `/e2e`.

## Routing & navigation

- Routes declared in `app/routes.ts` (config-based) or file-based via `@react-router/fs-routes`; nested layouts render through `<Outlet />`.
- Each route module can export `loader`, `action`, `clientLoader`, `clientAction`, `meta`, `links`, `headers`, `ErrorBoundary`, `HydrateFallback`, `shouldRevalidate`.
- `<Link prefetch="intent">` preloads code and data on hover/focus; `"viewport"` for visible links.
- Pending UI: `useNavigation()` for global progress, `useFetcher()` for in-place mutations without navigation, `useNavigation().formData` for optimistic UI.
- Redirects/auth: `throw redirect("/login")` from loaders; 404s via `throw data(null, { status: 404 })` handled by `ErrorBoundary`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | Route `loader`s (parallel per nested route, auto-revalidated after actions); `clientLoader` for client caches; TanStack Query only for polling/infinite scroll/real-time |
| Mutations | `<Form method="post">` / `useFetcher().submit` → route `action`; use a hidden `intent` field for multiple actions per route |
| URL state | `useSearchParams`; loaders read `new URL(request.url).searchParams` so filters are server-rendered and shareable |
| Forms + validation | Conform + Zod (progressive enhancement, server-first) or React Hook Form + Zod (client-heavy forms); always re-validate in the action |
| Local UI state | `useState` |
| Global client state | Rarely needed; Zustand or context for UI-only concerns (sidebar, command palette) |

- Loaders of all matched nested routes run in parallel — design routes so each loads only its own data.
- After an action, all active loaders revalidate; tune with `shouldRevalidate` for expensive ones.
- Return only serializable data the UI needs (DTOs), not raw DB rows.
- Optimistic UI from `fetcher.formData` before the action resolves; no separate client store required.

## Styling & design system

- Tailwind CSS with tokens as CSS variables, CSS Modules, or vanilla-extract; route `links` export can attach route-specific stylesheets.
- Components: **shadcn/ui** (has React Router setup docs), **Radix Primitives**, **React Aria Components**, **Mantine**, **Ark UI**.
- Dark mode: store preference in a cookie, read it in the root loader and set `class`/`data-theme` on `<html>` server-side — no flash, no hydration mismatch (e.g. `remix-themes`).

## Performance

- SSR + streaming: return promises from loaders and render with `<Suspense>` + `<Await>` to stream slow data without blocking TTFB.
- Route-based code splitting is automatic; `prefetch="intent"` makes subsequent navigations near-instant.
- LCP ≤ 2.5s: SSR the hero, preload LCP image and fonts via the `links` export, set cache headers with the `headers` export (`Cache-Control`, `s-maxage`, `stale-while-revalidate` on a CDN).
- `prerender` in config for static routes (marketing, docs) — served as HTML files.
- INP ≤ 200ms: fetchers avoid full navigations; keep client components small; defer third-party scripts.
- CLS ≤ 0.1: dimensioned images and skeletons that match final layout.
- No built-in image optimizer — use a CDN image service (Cloudinary, imgix, Cloudflare Images) or `unpic`.

## Accessibility

- Forms are real `<form>` elements → keyboard and assistive tech work before hydration.
- On client navigation, manage focus (focus `<h1>`/main) and announce route changes; React Router restores scroll with `<ScrollRestoration />`.
- After a failed action, render field errors with `aria-invalid`/`aria-describedby` and focus the first invalid field (Conform helps).
- Lint with `eslint-plugin-jsx-a11y`; run axe in Playwright.
- Headless primitives (Radix, React Aria) for menus, dialogs, comboboxes.

## Testing

- **Unit:** Vitest for `.server.ts` logic and Zod schemas; call `loader`/`action` directly with a constructed `Request`.
- **Component:** Vitest + React Testing Library with `createRoutesStub` to render routes with stubbed loaders/actions.
- **E2E:** Playwright against the production build (`react-router build` + `react-router-serve` or your server); test with JS disabled for critical forms.

## Build & deploy

- Vite-based build via the `@react-router/dev` plugin; outputs `build/client` (static assets) and `build/server`.
- Hosts: Node (`@react-router/node`, `@react-router/serve`, Express adapter), Cloudflare Workers, Vercel, Netlify, Fly.io, containers; `ssr: false` for static SPA hosting.
- Env vars: loaders/actions read `process.env` (or platform bindings) on the server; client code sees only `VITE_*` variables, which are public. Pass needed public config through the root loader.
- Sessions: cookie-based session storage with signed secrets, `httpOnly`, `secure`, `sameSite`.

## Pitfalls

- **Fetching in `useEffect`** instead of loaders → waterfalls and spinners; move to loaders.
- **Importing server code into route components** → bundling errors or leaked secrets; isolate in `.server.ts`.
- **Returning entire DB records** from loaders → serialized into HTML; select fields explicitly.
- **Expensive revalidation after every action** → implement `shouldRevalidate` or split routes.
- **Missing `ErrorBoundary`** on routes → one failing loader blanks the page; add per-route boundaries.
- **Only client-side validation** → actions must re-validate; never trust `FormData`.
- **Ignoring HTTP caching** → use `headers` export and a CDN for public routes.

## References

- https://reactrouter.com/start/modes
- https://reactrouter.com/start/framework/routing
- https://reactrouter.com/start/framework/data-loading
- https://reactrouter.com/start/framework/actions
- https://reactrouter.com/start/framework/pending-ui
- https://reactrouter.com/how-to/pre-rendering
