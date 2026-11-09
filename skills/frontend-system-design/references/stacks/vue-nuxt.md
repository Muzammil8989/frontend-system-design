# Vue (SPA) + Nuxt

> **Platform:** web · **Language:** TypeScript · **Rendering:** CSR (Vue + Vite); SSR, SSG, ISR/SWR, hybrid per-route (Nuxt) · **Best for:** teams wanting an approachable, batteries-included framework — SaaS, dashboards (Vue SPA) and SEO/content/e-commerce sites (Nuxt)

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Team prefers templates + SFCs and a gentle learning curve (common with backend-heavy teams, Laravel shops) | Hiring pool or existing codebase is overwhelmingly React |
| Internal tools/dashboards behind login → Vue + Vite SPA | You need a library that only exists for React (some charting/editor ecosystems) |
| SEO pages, e-commerce, content sites → Nuxt with per-route rendering rules | Tiny static sites with almost no interactivity (Astro ships less JS) |
| You want official, cohesive tooling (Vue Router, Pinia, DevTools, Nuxt modules) | You need React Native-level code sharing with mobile |
| Full-stack in one repo with Nuxt server routes (Nitro) deployable to Node, edge or static | Very large app where the team cannot agree on Nuxt auto-import conventions (can be disabled, but costs clarity) |

## Project structure

```text
web/                                   # Nuxt app (current default uses app/ as srcDir)
├── nuxt.config.ts                     # modules, routeRules, runtimeConfig
├── app/
│   ├── app.vue                        # <NuxtLayout><NuxtPage/></NuxtLayout>
│   ├── app.config.ts                  # public, reactive UI config (theme colors)
│   ├── layouts/                       # default.vue, dashboard.vue, auth.vue
│   ├── pages/
│   │   ├── index.vue
│   │   ├── pricing.vue
│   │   └── projects/
│   │       ├── index.vue              # list (URL query = filters)
│   │       └── [id].vue               # detail
│   ├── middleware/auth.ts             # route middleware (client + server)
│   ├── features/
│   │   └── projects/
│   │       ├── components/            # ProjectCard.vue, ProjectForm.vue
│   │       ├── composables/           # useProjects.ts (useFetch wrappers)
│   │       ├── stores/                # projectsUi.ts (Pinia, UI-only)
│   │       └── schemas.ts             # zod/valibot schemas
│   ├── components/ui/                 # design-system primitives
│   ├── composables/                   # shared: useDebounce, useToast
│   └── assets/css/                    # tokens.css, main.css
├── server/
│   ├── api/projects/index.get.ts      # Nitro handlers (BFF)
│   ├── api/projects/index.post.ts
│   └── utils/db.ts                    # server-only helpers
├── shared/                            # types/utils used by app and server
├── public/
├── tests/                             # unit/, nuxt/ (runtime env), e2e/
└── .env.example
```

- Vue SPA variant: same `features/` layout under `src/` with `main.ts`, `router/index.ts`, `stores/`.
- Register feature folders explicitly (`components.dirs`, `imports.dirs`) or import explicitly — keep auto-imports predictable.
- `server/` code never imports from `app/`; shared types go in `shared/`.
- Feature components import other features only via their composables/public exports; enforce with ESLint (`@nuxt/eslint` + boundaries rules).
- Unit tests colocated (`*.spec.ts`) or in `tests/unit`; Nuxt-runtime tests in `tests/nuxt`; Playwright in `tests/e2e`.

## Routing & navigation

- **Vue SPA:** Vue Router with lazy routes (`component: () => import(...)`), navigation guards (`beforeEach`) for auth, typed routes via `unplugin-vue-router` (file-based).
- **Nuxt:** file-based routing in `pages/`; `<NuxtLink>` prefetches visible links; `navigateTo()` for programmatic and server redirects; route middleware in `middleware/`.
- `definePageMeta({ layout, middleware })` per page; `useHead`/`useSeoMeta` for titles and meta tags.
- Hybrid rendering via `routeRules`: `{ '/': { prerender: true }, '/blog/**': { swr: 3600 }, '/app/**': { ssr: false } }`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state (Nuxt) | `useFetch` / `useAsyncData` (SSR-safe, dedupes and transfers payload to client); `$fetch` inside event handlers and server routes |
| Server state (Vue SPA) | TanStack Query for Vue (`@tanstack/vue-query`) or Pinia Colada |
| URL state | `route.query` + `router.replace`; VueUse `useRouteQuery` for two-way binding |
| Forms + validation | VeeValidate + Zod/Valibot (`toTypedSchema`), FormKit for schema-driven forms, Nuxt UI `UForm` with schema validation |
| Local UI state | `ref` / `reactive` / `computed` in `<script setup>`; `defineModel` for v-model components |
| Global client state | Pinia (setup stores); Nuxt `useState` for small SSR-safe shared values |

- Never use `$fetch` directly in `<script setup>` for initial data in Nuxt — it runs twice (server + client). Use `useFetch`/`useAsyncData` with a stable key.
- Use `pick`/`transform` options to reduce payload serialized into the HTML.
- Avoid module-level `ref()` state in Nuxt: it is shared across requests on the server (cross-user leak). Use `useState` or Pinia.
- Keep server data in the fetch cache; Pinia stores hold UI/client state and derived selections.

## Styling & design system

- Tokens as CSS variables; Tailwind CSS or UnoCSS mapping to them; `<style scoped>` or CSS Modules for component-local styles.
- Components: **Nuxt UI** (Tailwind + Reka UI), **Reka UI** (headless, formerly Radix Vue), **shadcn-vue**, **PrimeVue** (styled or unstyled mode), **Vuetify** (Material), **Quasar**, **Element Plus**, **Naive UI**.
- Dark mode: `@nuxtjs/color-mode` (SSR-safe, no flash) or VueUse `useDark` in SPA; swap token values under `.dark`/`[data-theme]`.

## Performance

- Nuxt: prerender/SWR-cache public routes via `routeRules` to hit LCP ≤ 2.5s; SSR the hero and avoid client-only rendering above the fold.
- Lazy components: prefix with `Lazy` (`<LazyChartPanel />`) and use delayed/lazy hydration strategies (`hydrate-on-visible`, `hydrate-on-idle`) for below-the-fold widgets; `<ClientOnly>` for browser-only libraries.
- `@nuxt/image` (`<NuxtImg>`, `<NuxtPicture>`) with explicit sizes and `preload` for the LCP image; `@nuxt/fonts` self-hosts fonts with fallback metrics (CLS ≤ 0.1).
- INP ≤ 200ms: use `shallowRef` for large immutable datasets, `v-memo`/`v-once` for heavy lists, virtualize with `vue-virtual-scroller` or TanStack Virtual; debounce input handlers.
- Analyze with `nuxi analyze` / `rollup-plugin-visualizer`; watch heavy UI kits imported globally instead of via auto-import/tree-shaking resolvers.
- `@nuxt/scripts` to load third-party scripts with deferred triggers.

## Accessibility

- Lint with `eslint-plugin-vuejs-accessibility`; run axe checks in Playwright (`@axe-core/playwright`).
- Route changes: Nuxt provides `<NuxtRouteAnnouncer>` — include it in `app.vue`; in a Vue SPA, focus the `<h1>` in `router.afterEach` and update `document.title`.
- Prefer Reka UI / Nuxt UI / PrimeVue components that implement WAI-ARIA patterns for dialogs, menus, comboboxes.
- `v-html` content bypasses semantics checks — sanitize and review headings/landmarks.
- Bind `aria-invalid` and `aria-describedby` to VeeValidate field errors; focus first error on submit.

## Testing

- **Unit/component:** Vitest + Vue Test Utils or `@testing-library/vue`.
- **Nuxt runtime:** `@nuxt/test-utils` (`mountSuspended`, `mockNuxtImport`, `registerEndpoint`) with the Nuxt Vitest environment.
- **E2E:** Playwright (or `@nuxt/test-utils/playwright`) against the built app.
- **API mocking:** MSW for SPA; `registerEndpoint` for Nuxt.
- **Visual/docs:** Storybook (Vue 3 + Vite) or Histoire.

## Build & deploy

- Vue SPA: `vite build` → static hosting with SPA fallback.
- Nuxt: `nuxi build` produces a Nitro server for Node, Vercel, Netlify, Cloudflare, Deno, AWS Lambda and more via presets; `nuxi generate` for fully static output.
- Env vars (Nuxt): declare in `runtimeConfig`; keys under `runtimeConfig.public` reach the browser, all others are server-only; override at runtime with `NUXT_*` / `NUXT_PUBLIC_*` env vars.
- Env vars (Vue SPA): only `VITE_*` are exposed and are public.
- `app.config.ts` is bundled and public — never put secrets there.

## Pitfalls

- **Destructuring reactive objects/props** loses reactivity → use `toRefs`, `storeToRefs` (Pinia), or reactive props destructure only where supported.
- **`$fetch` for initial page data in Nuxt** → double fetching and hydration mismatch; use `useFetch`/`useAsyncData`.
- **Module-level state on the server** → leaks between users; use `useState`/Pinia.
- **Hydration mismatches** from `Date`, `Math.random`, `window` checks → `<ClientOnly>` or `onMounted`.
- **Deep watchers on huge objects** → INP regressions; watch specific sources, use `shallowRef`.
- **Over-reliance on auto-imports** → unclear dependencies; keep feature boundaries explicit.
- **Secrets in `runtimeConfig.public` or `VITE_*`** → public; move to private runtime config.

## References

- https://vuejs.org/guide/best-practices/performance.html
- https://vuejs.org/guide/scaling-up/state-management.html
- https://nuxt.com/docs/getting-started/data-fetching
- https://nuxt.com/docs/guide/concepts/rendering
- https://nuxt.com/docs/guide/going-further/runtime-config
- https://pinia.vuejs.org/core-concepts/
