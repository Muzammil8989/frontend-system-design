# Angular

> **Platform:** web · **Language:** TypeScript · **Rendering:** CSR, SSR + hydration (incremental), SSG/prerender per route · **Best for:** large enterprise apps with many teams that need strong conventions, DI and long-term maintainability

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Large teams/many squads need one opinionated way (CLI, DI, router, forms, HTTP, i18n built in) | Small team shipping a marketing site or MVP fast |
| Enterprise back-office, banking, insurance, ERP, admin-heavy forms | Content/SEO sites with little interactivity (Astro, Next.js, Nuxt are lighter) |
| Long-lived codebase where upgrade tooling (`ng update` migrations) matters | You need the broadest third-party component ecosystem (React wins) |
| Complex, dynamic forms with validation and cross-field rules | Embeddable widgets where bundle size must be tiny |
| Team comes from Java/C#/OOP backgrounds and likes DI + services | Team strongly prefers JSX/function-component idioms |

## Project structure

```text
web/
├── angular.json                       # builders, budgets, file replacements
├── src/
│   ├── main.ts                        # bootstrapApplication(App, appConfig)
│   ├── main.server.ts                 # SSR bootstrap
│   ├── server.ts                      # Node/Express SSR server
│   ├── index.html
│   ├── styles/                        # tokens.scss, theme.scss, global.scss
│   └── app/
│       ├── app.config.ts              # provideRouter, provideHttpClient(withInterceptors), hydration
│       ├── app.routes.ts              # top-level lazy routes (loadChildren/loadComponent)
│       ├── app.routes.server.ts       # per-route RenderMode: Server | Prerender | Client
│       ├── core/                      # singletons: auth.service.ts, http interceptors, guards, error handler
│       ├── shared/
│       │   ├── ui/                    # design-system: button, dialog, form-field (standalone)
│       │   ├── pipes/ directives/
│       │   └── util/
│       ├── layout/                    # shell.component.ts, sidebar, topbar
│       └── features/
│           ├── projects/
│           │   ├── projects.routes.ts # feature route config (lazy)
│           │   ├── data-access/       # projects.api.ts (HttpClient), projects.store.ts (SignalStore)
│           │   ├── ui/                # presentational: project-card.component.ts
│           │   ├── feature/           # smart/route components: project-list.page.ts
│           │   └── models.ts
│           └── billing/ ...
├── e2e/                               # Playwright
└── proxy.conf.json                    # dev API proxy
```

- Standalone components everywhere (no NgModules for new code); one feature = one lazy `*.routes.ts`.
- Layering inside a feature: `feature/` (routed, injects stores) → `ui/` (inputs/outputs only) → `data-access/`; `ui/` never injects services.
- `core/` is provided once at the root; features never import from each other's internals — use Nx module-boundary tags or ESLint `no-restricted-imports` in large repos.
- Specs colocated as `*.spec.ts`; e2e in `/e2e`.
- Use `inject()` over constructor injection for new code; keep components `ChangeDetectionStrategy.OnPush`.

## Routing & navigation

- `provideRouter(routes, withComponentInputBinding(), withViewTransitions(), withPreloading(...))`; route params bind directly to component `input()`s.
- Lazy load with `loadComponent` / `loadChildren`; preloading strategy (e.g. `PreloadAllModules` or a custom/quicklink strategy) for likely next routes.
- Functional guards/resolvers (`CanActivateFn`, `ResolveFn`) using `inject()`; redirect with `router.createUrlTree`.
- `routerLink` / `routerLinkActive` (with `ariaCurrentWhenActive`); `title` property on routes or a custom `TitleStrategy`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | `HttpClient` wrapped in services; `resource()`/`httpResource()` (newer signal-based APIs — check stability for your version); TanStack Query for Angular for caching/refetch semantics |
| URL state | Router query params bound via `withComponentInputBinding`; update with `router.navigate([], { queryParams, queryParamsHandling: 'merge' })` |
| Forms + validation | Typed Reactive Forms (`FormBuilder.nonNullable`) with custom/async validators; signal-based forms are emerging (experimental) |
| Local UI state | `signal()`, `computed()`, `linkedSignal()`; component `input()`/`output()`/`model()` |
| Global client state | NgRx SignalStore (feature stores with `withState`/`withComputed`/`withMethods`); classic NgRx Store/Effects for very large event-driven apps; plain injectable services with signals for small apps |

- Prefer signals for state, RxJS for event streams (debounce search, websockets); bridge with `toSignal`/`toObservable` from `@angular/core/rxjs-interop`.
- Interceptors (`withInterceptors([authInterceptor, errorInterceptor])`) for auth headers, retries and error toasts.
- With SSR, HTTP responses are cached in the transfer state and reused during hydration (avoid double fetch); exclude auth-specific requests as needed.
- Unsubscribe automatically with `takeUntilDestroyed()` or the `async` pipe / `toSignal`.

## Styling & design system

- Tokens as CSS custom properties; SCSS for authoring; Tailwind CSS is supported by the CLI.
- Components: **Angular Material** (Material 3 theming via design tokens/Sass mixins) + **Angular CDK** (overlay, a11y, drag-drop, virtual scroll), **Spartan** (shadcn-style: headless "brain" + styled "helm"), **PrimeNG**, **Taiga UI**, **NG-ZORRO**, **Angular Aria**/CDK primitives for headless patterns.
- Dark mode: swap token values under a `.dark`/`[data-theme]` class on `<html>`, or `color-scheme` with Material's light/dark token sets; persist preference and apply before bootstrap to avoid flash.
- Component styles are encapsulated (emulated) by default; theme through CSS variables rather than `::ng-deep`.

## Performance

- SSR + hydration for public routes; **incremental hydration** with `@defer (hydrate on viewport | interaction | idle)` keeps below-the-fold JS dormant; event replay captures early clicks.
- `@defer (on viewport) { ... } @placeholder { ... }` to lazy-load heavy components (charts, editors); always give placeholders fixed dimensions (CLS ≤ 0.1).
- `NgOptimizedImage` (`ngSrc`, `priority` on the LCP image, required width/height, `fill` mode) for LCP ≤ 2.5s; inline critical fonts via CLI font inlining.
- INP ≤ 200ms: `OnPush` + signals for fine-grained updates; `@for (...; track item.id)`; CDK virtual scroll for long lists; consider zoneless change detection to drop Zone.js overhead.
- Enforce `budgets` in `angular.json` (initial bundle, component styles) so CI fails on regressions; inspect with `source-map-explorer` / esbuild metafile.

## Accessibility

- `angular-eslint` template accessibility rules (`alt-text`, `click-events-have-key-events`, `interactive-supports-focus`, `label-has-associated-control`, etc.).
- CDK a11y: `FocusTrap`, `LiveAnnouncer`, `FocusMonitor`, `ListKeyManager` for custom widgets.
- Router does not move focus on navigation: in a `NavigationEnd` handler focus the main heading and announce the title (`LiveAnnouncer`).
- Angular Material components follow WAI-ARIA patterns; custom wrappers must forward `aria-*` and labels.
- Bind `[attr.aria-invalid]`/`aria-describedby` to form control errors; use `mat-error` or equivalent.

## Testing

- **Unit/component:** TestBed with the CLI test runner — Jasmine/Karma (legacy; Karma is deprecated), Jest, or Vitest via the newer CLI unit-test builder; check your CLI version's default. Angular Testing Library for user-centric component tests; component harnesses (`@angular/cdk/testing`) for Material components.
- **Stores/services:** test SignalStores and services directly with `TestBed.inject` and `HttpTestingController` (`provideHttpClientTesting`).
- **E2E:** Playwright or Cypress against `ng build` output / SSR server.
- **Visual:** Storybook for Angular.

## Build & deploy

- Angular CLI `application` builder (esbuild + Vite dev server); `ng build` emits `browser/` and, with SSR, `server/`.
- Hosts: static CDN for CSR (SPA fallback rewrite); Node server (Express in `server.ts`) on containers, Firebase App Hosting, Netlify, Vercel, Cloud Run; prerendered routes served as static HTML.
- Env config: `environment.ts` + `fileReplacements` or `define` — everything in the browser bundle is public. Secrets stay in the backend/SSR server (`process.env` in `server.ts` only).
- Runtime config per environment: load `/config.json` in an `APP_INITIALIZER`/`provideAppInitializer` before bootstrap completes.

## Pitfalls

- **Manual `subscribe()` without teardown** → memory leaks; use `async` pipe, `toSignal`, `takeUntilDestroyed`.
- **Default change detection + mutable objects** → sluggish UI; use `OnPush`, immutable updates, signals.
- **Calling methods in templates** (`{{ total() }}` on non-signal functions) → recomputed every cycle; use `computed()` or pure pipes.
- **Shared/feature modules that import everything** → huge initial bundle; standalone + lazy routes.
- **Browser APIs in SSR** (`window`, `localStorage`) → crashes; use `afterNextRender`, `isPlatformBrowser`, or DI tokens.
- **`::ng-deep` everywhere** → brittle theming; expose CSS variables.
- **Ignoring `ng update` migrations** → painful jumps; upgrade one major at a time.

## References

- https://angular.dev/guide/signals
- https://angular.dev/guide/templates/defer
- https://angular.dev/guide/ssr
- https://angular.dev/guide/incremental-hydration
- https://angular.dev/best-practices/a11y
- https://ngrx.io/guide/signals/signal-store
