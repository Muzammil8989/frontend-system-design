# Server-rendered MPA (htmx, Hotwire, Livewire, LiveView, templates)

> **Platform:** web · **Language:** Python / Ruby / PHP / Elixir + HTML (minimal JS) · **Rendering:** SSR multi-page, HTML-over-the-wire partial updates · **Best for:** CRUD-heavy business apps, admin/back office, content + forms products built by backend-strong teams

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Team is backend-strong (Django, Rails, Laravel, Phoenix) and wants one codebase, one language | UI needs rich client-only interactivity: canvas editors, offline-first, complex drag-and-drop |
| Most screens are lists, forms, detail pages, wizards, dashboards with server data | App must work offline or on flaky networks with local-first sync |
| Fast first paint, SEO and low client JS matter with minimal build tooling | You need a native mobile app sharing UI logic with the web (consider Hotwire Native only if web views suffice) |
| You want server-side authorization and validation as the single source of truth | Per-interaction latency must be near zero far from the server (every action is a round trip) |
| Real-time updates via server push are enough (Turbo Streams, LiveView, Livewire polling/Reverb) | A separate frontend team already owns a React/Vue design system and SPA |

| Stack | Server-driven update model | Sprinkles of JS |
|---|---|---|
| **htmx** (any backend) | Attributes (`hx-get`, `hx-post`, `hx-target`, `hx-swap`, `hx-trigger`) swap HTML fragments | Alpine.js, hyperscript, vanilla |
| **Hotwire** (Rails-first, any backend) | Turbo Drive (navigation), Turbo Frames (scoped regions), Turbo Streams (append/replace/remove over HTTP or WebSocket) | Stimulus controllers |
| **Laravel Livewire** | PHP component classes re-render on actions; DOM diffed client-side | Alpine.js (bundled) |
| **Phoenix LiveView** | Stateful process per connection over WebSocket; sends minimal diffs | JS hooks, `Phoenix.LiveView.JS` commands |

## Project structure

```text
app/                                   # Django + htmx example; Rails/Laravel/Phoenix map 1:1 (see bullets)
├── config/                            # settings/base.py, settings/prod.py, urls.py
├── apps/
│   ├── projects/
│   │   ├── models.py
│   │   ├── forms.py                   # server-side validation (single source of truth)
│   │   ├── views.py                   # full page vs partial: check request.htmx
│   │   ├── urls.py
│   │   ├── services.py                # business logic, no HTTP
│   │   ├── templates/projects/
│   │   │   ├── list.html              # full page extends base.html
│   │   │   ├── detail.html
│   │   │   └── partials/
│   │   │       ├── _table.html        # swapped by hx-get on filter/paginate
│   │   │       ├── _row.html          # swapped after inline edit
│   │   │       └── _form.html         # re-rendered with errors (422)
│   │   └── tests/                     # test_views.py, test_forms.py
│   └── billing/ ...
├── templates/
│   ├── base.html                      # <html lang>, skip link, landmarks, CSRF header for htmx
│   └── components/                    # _button.html, _modal.html, _field.html (template partials/includes)
├── static/
│   ├── css/                           # tokens.css, app.css (Tailwind build output)
│   └── js/                            # htmx, alpine, small modules
├── e2e/                               # Playwright specs
└── .env.example
```

- **Rails:** `app/views/<resource>/` with `_partial.html.erb`, `*.turbo_stream.erb`; `app/components/` (ViewComponent or Phlex); `app/javascript/controllers/` (Stimulus); importmap or jsbundling.
- **Laravel:** `app/Livewire/` component classes + `resources/views/livewire/`; Blade components in `resources/views/components/`.
- **Phoenix:** `lib/my_app_web/live/` (LiveViews), `components/core_components.ex` (function components), `assets/js/hooks/`.
- Every partial has one owner view; partials are named `_*.html` and are renderable alone (they are API responses).
- Business logic in services/contexts, never in templates; tests live with each app/feature.

## Routing & navigation

- Server routes are the source of truth (Django `urls.py`, Rails `routes.rb`, Laravel `routes/web.php`, Phoenix router `live` routes).
- SPA-like navigation without a client router: `hx-boost="true"` on `<body>`, Turbo Drive (default in Rails), Livewire `wire:navigate`, LiveView `<.link navigate>` / `patch`.
- Update the URL for filterable views: `hx-push-url="true"` / `hx-replace-url`, Turbo Frame `data-turbo-action="advance"`, LiveView `push_patch`, Livewire `#[Url]` properties.
- Every partial-updating URL should also render a full page on direct load (check `HX-Request` header / `turbo_frame_request?`).

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | The database + server-rendered templates; cache fragments (Rails Russian-doll caching, Django template fragment cache, Laravel cache) |
| URL state | Query params read by the view; pushed via `hx-push-url`, Turbo, `push_patch`, Livewire `#[Url]` |
| Forms + validation | Server forms: Django Forms/`django-crispy-forms`, Rails form builders + model validations, Laravel Form Requests / Livewire `#[Validate]`, Phoenix `Ecto.Changeset` with `phx-change` live validation |
| Local UI state | Alpine.js (`x-data`) or Stimulus values/targets; LiveView `JS` commands for client-only toggles |
| Global client state | Avoid; persist in the server session or DB. Small cross-widget needs: Alpine stores |
| Real-time | Turbo Streams over Action Cable, LiveView PubSub, Livewire + Laravel Reverb/Echo, htmx SSE/WebSocket extensions |

- Return the smallest fragment that changes; use out-of-band swaps (`hx-swap-oob`, multiple Turbo Streams) to update counters/flash messages elsewhere.
- Validation errors re-render the form partial with errors; Turbo requires a 4xx/5xx status (e.g. 422) for rendered errors and a 303 redirect on success.
- LiveView: use streams (`stream/3`) for large collections to avoid holding them in socket memory.

## Styling & design system

- Tokens as CSS custom properties in `tokens.css`; Tailwind CSS (standalone CLI or framework integrations: `tailwindcss-rails`, `django-tailwind`, Laravel Vite) or plain CSS with cascade layers.
- Components as server-side partials/components: ViewComponent/Phlex (Rails), Blade components + Flux (Livewire), Phoenix function components (`core_components.ex`), Django template partials/`django-cotton`.
- CSS-only kits that fit MPAs: DaisyUI (Tailwind plugin), Bootstrap; for complex widgets use web components (Web Awesome) or accessible Alpine/Stimulus implementations.
- Dark mode: inline script in `base.html` head sets `data-theme` before paint; persist choice in a cookie so the server renders the right theme.

## Performance

- No hydration: HTML is usable immediately — LCP ≤ 2.5s depends on server TTFB. Fix N+1 queries (`select_related`/`prefetch_related`, `includes`, eager loading), cache fragments, put static assets on a CDN.
- INP ≤ 200ms: each interaction is a network round trip — show immediate feedback (`hx-indicator`, `aria-busy`, Turbo progress bar, `wire:loading`, `phx-click-loading`), debounce input (`hx-trigger="keyup changed delay:300ms"`, `wire:model.live.debounce`), and keep endpoints fast.
- CLS ≤ 0.1: swapped fragments should match the size of the placeholder; avoid inserting content above the viewport; dimensioned images.
- Use `hx-swap` with `settle`/`transition` options or Turbo morphing to avoid flicker; Turbo prefetch on hover makes navigations feel instant.
- Compress HTML (gzip/brotli) — HTML responses are the payload.

## Accessibility

- Server HTML makes semantic markup natural: real links, forms, buttons; progressive enhancement means features degrade gracefully without JS.
- Partial swaps are silent to screen readers: wrap updated regions in `aria-live="polite"` or announce via a live region; move focus to new content (e.g. error summary, opened modal) after swaps.
- Boosted/Turbo navigation: verify page title updates and focus is reset to the top or main heading; test with NVDA/VoiceOver.
- Disable submit buttons during requests (`hx-disabled-elt`, Turbo `data-turbo-submits-with`) while keeping them perceivable.
- Lint templates with `djlint`/`erb_lint`/Blade linters; run axe via Playwright on key pages.

## Testing

- **Views/partials:** Django test client / `pytest-django`, Rails request + component tests (Minitest/RSpec), Pest/PHPUnit with `Livewire::test()`, `Phoenix.LiveViewTest` (`live/2`, `render_click`, `render_submit`).
- **System/E2E:** Rails system tests (Capybara), Laravel Dusk, Playwright (any stack, including pytest-playwright).
- **JS sprinkles:** Vitest for Stimulus/Alpine modules where logic is non-trivial.

## Build & deploy

- Minimal or no bundler: htmx/Alpine from a vendored file or importmap; Vite for Laravel; esbuild/Tailwind CLI for Phoenix; jsbundling/importmap for Rails.
- Hosts: any app server platform — containers on Fly.io, Render, Railway, Heroku, Kamal (Rails), Laravel Cloud/Forge, Gigalixir/Fly (Phoenix), Kubernetes; static assets via CDN with hashed filenames.
- Secrets stay server-side by construction; anything rendered into HTML (including `data-*`, inline JSON, Alpine `x-data`) is public — never render tokens or internal IDs you would not show.
- CSRF: include the token in htmx requests (`hx-headers` on `<body>` or a meta tag + config); Turbo/Livewire/LiveView handle it via framework helpers. Set CSP; htmx/Alpine need care with inline handlers (`unsafe-eval` for some Alpine builds — use the CSP build).

## Pitfalls

- **Returning full pages to partial requests** → nested layouts inside targets; branch on `HX-Request`/Turbo-Frame headers.
- **Turbo form errors returned with 200** → nothing renders; return 422 for errors, 303 for redirects.
- **Silent DOM swaps** → screen readers miss changes; use live regions and focus management.
- **Chatty endpoints** (one request per keystroke) → debounce and cache; batch updates with OOB swaps.
- **Back/forward restoring stale or broken state** → configure history caching (`hx-history`, Turbo cache control, `data-turbo-permanent`).
- **LiveView holding large assigns per user** → memory pressure; use streams and `temporary_assigns`.
- **JS widgets not re-initializing after swaps** → use Stimulus controllers / Alpine (auto-init) / `htmx.onLoad` / LiveView hooks instead of `DOMContentLoaded`.
- **Rebuilding an SPA in sprinkles** → if a screen needs heavy client state, mount a single island (web component or small framework app) there.

## References

- https://htmx.org/docs/
- https://turbo.hotwired.dev/handbook/introduction
- https://stimulus.hotwired.dev/handbook/introduction
- https://livewire.laravel.com/docs/quickstart
- https://hexdocs.pm/phoenix_live_view/welcome.html
- https://docs.djangoproject.com/en/stable/topics/templates/
