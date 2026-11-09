# Electron

> **Platform:** desktop (Windows, macOS, Linux) · **Language:** TypeScript/JavaScript (Node.js main process + web renderer) · **Rendering:** bundled Chromium per app · **Best for:** feature-rich desktop apps built by web teams that need consistent rendering and full Node.js/OS access

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Web team, React/Vue/Svelte skills; want to share UI with a web app | Install size and RAM footprint are key constraints (bundles Chromium + Node) |
| You need identical rendering on every OS (one Chromium version you control) | A small utility/tray app where Tauri or native is lighter |
| Rich ecosystem: Node modules, native addons, mature tooling (VS Code, Slack-class apps) | You need deep native look-and-feel on each OS (use native toolkits) |
| Complex multi-window apps, editors, IDE-like tools, collaboration clients | Security team cannot accept the Node-in-desktop attack surface review burden |
| Mature auto-update and packaging options are required now | Mobile is also a target (Electron is desktop only) |

## Project structure

```text
src/
  main/                         # Node.js main process (one per app)
    index.ts                    # app lifecycle, single-instance lock, protocol handler
    windows/mainWindow.ts       # BrowserWindow factory with secure webPreferences
    ipc/                        # ipcMain.handle handlers, one file per domain
      files.ipc.ts              # validates sender + args (zod) before acting
    services/                   # db (better-sqlite3), updater, menu, tray, keychain
    menu.ts                     # application + context menus, accelerators
  preload/
    index.ts                    # contextBridge.exposeInMainWorld('api', {...}) — narrow, typed
  renderer/                     # SPA (React/Vue/Svelte) — no Node access
    src/
      app/router.tsx
      features/projects/ ...
      shared/ui/ ...
  shared/
    ipc-contract.ts             # channel names + request/response types shared by all layers
resources/                      # icons, entitlements.mac.plist
forge.config.ts | electron-builder.yml
electron.vite.config.ts         # or Forge Vite plugin config
```

- Three security zones: **main** (privileged), **preload** (bridge), **renderer** (untrusted web content). Treat renderer input as hostile.
- One typed IPC contract in `shared/`; preload exposes functions (`api.openFile()`), never raw `ipcRenderer`.
- Heavy CPU/IO work in a `utilityProcess` or worker, not the main process (a blocked main process freezes all windows).
- Serve the renderer from a custom protocol (`protocol.handle('app', ...)`) rather than `file://` for a proper origin and CSP.

## Routing & navigation

- In-window navigation is the SPA router (React Router, TanStack Router, Vue Router); use hash or memory history if served from `file://`.
- Multi-window: each `BrowserWindow` loads a route/entry (`app://index.html#/settings`); coordinate via main process or `MessageChannelMain`.
- Block unexpected navigation: `will-navigate` handler and `setWindowOpenHandler` (deny by default; open external links via `shell.openExternal` after allow-listing).
- Deep links: `app.setAsDefaultProtocolClient('myapp')`; handle `open-url` (macOS) and `second-instance` argv (Windows/Linux) with `requestSingleInstanceLock`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | TanStack Query in renderer (fetch from renderer, or via IPC when requests need main-process credentials) |
| Local persistence / offline DB | SQLite via **better-sqlite3** in main/utility process (expose queries over IPC); IndexedDB for renderer-only caches |
| Settings | `electron-store` (JSON) in main process |
| Secrets | OS keychain: `safeStorage` encryption API (or a keychain native module); never plaintext files |
| Forms + validation | React Hook Form + Zod (or framework equivalent); re-validate in main for privileged actions |
| UI state | Component state |
| App-wide state | Zustand/Redux Toolkit/Pinia in renderer; cross-window state owned by main and broadcast over IPC |
| DI | Plain modules/factories in main; renderer per framework |

## Styling & design system

- Web design systems apply (tokens as CSS custom properties, Tailwind, Radix/shadcn, MUI, Fluent UI React).
- Desktop conventions: native menus, OS-correct shortcuts (`CmdOrCtrl`), context menus, window controls placement (left on macOS, right on Windows).
- Custom title bars: `titleBarStyle: 'hidden'` + `titleBarOverlay`; mark drag regions with `-webkit-app-region: drag`.
- Dark mode: `nativeTheme.themeSource` + `prefers-color-scheme`; follow system by default.
- Fonts: system font stack per OS; respect OS zoom/scaling; support `Ctrl/Cmd +/-` zoom (`webContents.setZoomFactor`).
- Platform polish: macOS vibrancy and traffic lights, Windows Mica/acrylic background materials where supported.

## Performance

- Startup: bundle main and preload (Vite/esbuild), lazy-`require` heavy modules, show window on `ready-to-show`, avoid sync file IO at boot; V8 snapshots for advanced cases.
- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz in the renderer; same web rules: virtualize long lists, avoid layout thrash, use workers.
- Never use synchronous IPC (`sendSync`) or blocking work in main; batch IPC calls, transfer large data via `MessagePort` or files.
- Memory: each window = renderer process; reuse/hide windows instead of creating many; watch leaks with Chrome DevTools memory panel.
- App size: Chromium + Node baseline; trim with ASAR, prune devDependencies, exclude source maps from packages, avoid duplicate native modules.
- Background throttling: set `backgroundThrottling: false` only for windows that truly need it.

## Accessibility

- Chromium exposes the DOM accessibility tree to platform APIs (UI Automation/MSAA on Windows, NSAccessibility on macOS, AT-SPI on Linux): use semantic HTML and ARIA correctly.
- Keyboard-first: every action reachable by keyboard; menus with accelerators; visible focus; logical tab order across custom title bars.
- Support high contrast/forced colors (`forced-colors` media query, `nativeTheme.shouldUseHighContrastColors`), reduced motion, OS text scaling.
- Test with NVDA/JAWS/Narrator (Windows), VoiceOver (macOS), Orca (Linux); axe-core in renderer tests; Accessibility Insights for Windows.

## Testing

| Level | Tooling |
|---|---|
| Unit | Vitest/Jest for main services and renderer logic (mock `electron` module) |
| Component | Testing Library in jsdom/browser mode |
| IPC contract | Test handlers with fake `IpcMainInvokeEvent` (sender validation, arg validation) |
| E2E | Playwright's Electron support (`_electron.launch`) or WebdriverIO Electron service |
| Packaging | Smoke-test signed installers on clean VMs per OS |

## Build & deploy

- Tooling: **Electron Forge** (official; makers for Squirrel.Windows, MSI/WiX, dmg, zip, deb, rpm, flatpak) or **electron-builder** (NSIS, dmg, AppImage, snap); electron-vite for dev build.
- macOS: Developer ID signing, hardened runtime + entitlements, **notarization** (`notarytool`) and stapling; Mac App Store needs sandboxed build.
- Windows: Authenticode signing (keys in HSM/cloud signing service, e.g. Azure Trusted Signing); SmartScreen reputation builds over time.
- Auto-update: built-in `autoUpdater` (Squirrel) with update.electronjs.org for public GitHub releases, or **electron-updater** (electron-builder) with S3/GitHub/generic feeds; staged rollouts via feed percentage.
- Security hardening at package time: Electron **Fuses** (disable `RunAsNode`, enable ASAR integrity, `OnlyLoadAppFromAsar`).
- Native modules: rebuild for Electron's ABI (`@electron/rebuild`, handled by Forge/builder); CI matrix per OS/arch.
- Keep Electron current: Chromium security fixes arrive via Electron releases — schedule regular upgrades.

## Pitfalls

- Disabling `contextIsolation`, enabling `nodeIntegration`, or turning off `sandbox`/`webSecurity` "to make it work".
- Exposing generic `ipcRenderer.send/invoke` or `fs` through the preload — equivalent to giving web content full OS access.
- Loading remote content in a privileged window; missing CSP; unvalidated `shell.openExternal(url)`.
- Blocking the main process with sync IO or CPU work → whole app hangs.
- Not signing/notarizing → Gatekeeper/SmartScreen warnings and broken auto-update on macOS.
- Falling many Electron majors behind (unpatched Chromium).
- Memory bloat from many hidden windows and leaked listeners.

### Security checklist

- [ ] `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` (defaults — never override)
- [ ] Strict CSP; no `unsafe-eval`; load only local app content in privileged windows
- [ ] Validate `event.senderFrame` origin and all IPC arguments in every `ipcMain.handle`
- [ ] Deny `window.open`/navigation by default; allow-list external URLs
- [ ] No secrets in the app bundle; use `safeStorage`/keychain for user tokens
- [ ] Fuses and ASAR integrity enabled; code signed and notarized

## References

- https://www.electronjs.org/docs/latest/
- https://www.electronjs.org/docs/latest/tutorial/security
- https://www.electronjs.org/docs/latest/tutorial/process-model
- https://www.electronjs.org/docs/latest/tutorial/ipc
- https://www.electronforge.io/
- https://www.electron.build/
