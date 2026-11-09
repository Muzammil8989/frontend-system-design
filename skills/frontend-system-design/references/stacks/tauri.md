# Tauri

> **Platform:** desktop (Windows, macOS, Linux; iOS and Android supported in Tauri 2) · **Language:** Rust (core) + TypeScript/any web framework (UI) · **Rendering:** OS system WebView (WebView2 on Windows, WKWebView on macOS/iOS, WebKitGTK on Linux, Android WebView) · **Best for:** small, secure, resource-efficient desktop apps with a web UI and a native Rust backend

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Small installers and low memory matter (no bundled browser engine) | You need pixel-identical rendering across OSes — WebView engines differ |
| Security-sensitive apps: explicit capability/permission model, Rust core | Team cannot take on Rust for non-trivial native logic |
| Utilities, tray apps, dev tools, local-first editors, companion apps | You rely on Chromium-only web APIs (some features are missing in WebKit/WebKitGTK) |
| Web team + someone comfortable with Rust for system work | Linux is a primary target and you need top WebView performance (WebKitGTK lags) |
| Want one project to also produce mobile builds (evaluate maturity for your needs) | You need a large, mature desktop plugin ecosystem today (Electron's is larger) |

## Project structure

```text
src/                              # web frontend (React/Vue/Svelte/Solid + Vite)
  app/router.tsx
  features/
    notes/
      NotesPage.tsx
      notes.api.ts                # typed wrappers around invoke('list_notes', ...)
  shared/ui/
  lib/tauri.ts                    # single place that imports @tauri-apps/api
src-tauri/
  Cargo.toml
  tauri.conf.json                 # app id, windows, bundle targets, CSP, updater config
  capabilities/
    main.json                     # which windows get which permissions (least privilege)
  src/
    main.rs                       # desktop entry (calls lib::run)
    lib.rs                        # Builder: plugins, manage(state), invoke_handler
    commands/
      notes.rs                    # #[tauri::command] fns; validate inputs, return Result<T, Error>
    db.rs                         # SQLite (sqlx/rusqlite) or tauri-plugin-sql
    error.rs                      # serializable error type
  icons/
  gen/                            # generated mobile projects (android/, apple/) when targeting mobile
```

- Keep the frontend platform-agnostic: all `invoke`/plugin calls behind `lib/tauri.ts` so it can run and be tested in a browser with mocks.
- Commands are the API boundary: typed inputs/outputs (serde), validated in Rust, never "run arbitrary shell/fs" commands.
- Capabilities per window: the main window gets what it needs; secondary windows/remote content get nothing by default.
- Generate TS bindings from Rust types (e.g. tauri-specta or ts-rs) to keep the IPC contract in sync.

## Routing & navigation

- In-window: the frontend SPA router (any history mode works with Tauri's asset protocol; hash is safest for multi-window URLs).
- Multi-window: define windows in `tauri.conf.json` or create with `WebviewWindowBuilder`; each window has its own label → capabilities target labels.
- Deep links: `tauri-plugin-deep-link` (custom schemes; universal/app links on mobile) + `tauri-plugin-single-instance` to route links to the running instance.
- External links: open via the opener plugin; do not navigate the app WebView to remote sites.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | TanStack Query in frontend; HTTP from frontend `fetch` (CSP/`connect-src` allow-list) or `tauri-plugin-http`/Rust `reqwest` for privileged requests |
| Local persistence / offline DB | SQLite in Rust (`sqlx`/`rusqlite`) exposed via commands, or `tauri-plugin-sql` |
| Settings | `tauri-plugin-store` (persistent key-value) |
| Secrets | OS keychain via a keyring crate in Rust or Stronghold plugin; never in frontend storage |
| Forms + validation | Frontend: React Hook Form + Zod (or equivalent); re-validate in Rust commands |
| UI state | Framework component state |
| App-wide state | Frontend store (Zustand/Pinia/Svelte stores); backend state via `app.manage(T)` + `State<'_, Mutex<T>>`; push changes with events |
| DI | Rust managed state; frontend modules |

## Styling & design system

- Standard web styling (CSS variables tokens, Tailwind, Radix/shadcn, etc.) — but test in **all three engines**: Chromium (WebView2), WebKit (macOS), WebKitGTK (Linux).
- Desktop conventions: native menus (`Menu` API), OS shortcuts (`CmdOrCtrl`), tray (`TrayIconBuilder`), context menus.
- Custom title bars: `decorations: false` + `data-tauri-drag-region`; reproduce OS window controls carefully (macOS overlay title bar style is an alternative).
- Dark mode: `prefers-color-scheme` + window `theme` API; follow system by default.
- Typography: system font stacks per OS; honor OS scaling (DPI) and in-app zoom.

## Performance

- Small footprint by design: system WebView + compact Rust binary → installers typically far smaller than Electron; still measure your own.
- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz in the WebView; same web rules (virtualized lists, workers, no layout thrash).
- IPC: arguments are serialized — avoid chatty calls and large JSON payloads; use **Channels** for streaming, raw/binary responses or custom protocols for big data.
- Async commands (`async fn`) run off the main thread; never block the main/event-loop thread with long work (use `tauri::async_runtime::spawn`/`spawn_blocking`).
- Startup: lazy plugin init, small frontend bundle, show window after first render (`visible: false` then `show()`).
- Release profile: `opt-level`, `lto`, `codegen-units = 1`, `strip = true`, `panic = "abort"` to shrink binaries.
- Linux WebKitGTK may be slower for heavy CSS/animations — profile there if Linux matters.

## Accessibility

- WebView engines expose web accessibility trees to OS APIs (UIA on Windows, NSAccessibility on macOS, AT-SPI on Linux): semantic HTML + correct ARIA.
- Keyboard navigation for all actions; menu accelerators; visible focus, including custom title bars and tray menus.
- Support forced colors/high contrast, reduced motion, OS text scaling.
- Test with Narrator/NVDA (Windows), VoiceOver (macOS), Orca (Linux) — behavior differs per engine; axe-core for automated checks.

## Testing

| Level | Tooling |
|---|---|
| Rust unit/integration | `cargo test`; Tauri's `test` module (mock runtime/app) for command tests |
| Frontend unit/component | Vitest + Testing Library; `@tauri-apps/api/mocks` (`mockIPC`, `mockWindows`) |
| E2E | WebDriver via `tauri-driver` (Windows/Linux; macOS lacks a WKWebView driver) with WebdriverIO/Selenium; or Playwright against the web build with mocked IPC |
| Packaging | Install signed bundles on clean VMs per OS |

## Build & deploy

- `tauri build` → bundles: MSI (WiX) and NSIS (Windows), `.app`/dmg (macOS), AppImage/deb/rpm (Linux); mobile via `tauri android|ios build`.
- CI: **tauri-action** (GitHub Actions) builds per-OS matrix, creates releases and updater artifacts; cache Rust (`Swatinem/rust-cache`).
- Signing: macOS Developer ID + notarization (configure Apple credentials in CI); Windows Authenticode (cloud/HSM signing); Linux packages per distro rules.
- Auto-update: `tauri-plugin-updater` — updates are **signed with your updater key** (public key in config) independently of OS code signing; host a static JSON manifest or dynamic endpoint; stage rollouts server-side.
- WebView2 runtime on Windows: choose install mode (download bootstrapper, embedded, offline/fixed version) based on offline/enterprise needs.
- Sidecars: ship external binaries via `externalBin` (signed too) when needed.

## Pitfalls

- Over-broad capabilities (e.g. `fs` with `$HOME/**`, shell execute) — defeats Tauri's security model; scope per window and path.
- Loading remote URLs into a window that has IPC permissions.
- Assuming Chromium behavior: CSS/JS features, codecs, WebRTC and devtools differ on WebKit/WebKitGTK.
- Losing the updater private key → cannot ship updates to existing installs; back it up securely.
- Blocking the main thread in sync commands → frozen UI.
- Underestimating Rust compile times in CI without caching.
- Missing WebView2 on locked-down Windows machines when using the download bootstrapper.

## References

- https://v2.tauri.app/
- https://v2.tauri.app/concept/architecture/
- https://v2.tauri.app/security/capabilities/
- https://v2.tauri.app/develop/calling-rust/
- https://v2.tauri.app/plugin/updater/
- https://v2.tauri.app/distribute/
