# Desktop platform guide

System design essentials for Windows, macOS and Linux apps. Stack details: [electron](../stacks/electron.md), [tauri](../stacks/tauri.md), [swiftui](../stacks/swiftui.md), [compose-multiplatform](../stacks/compose-multiplatform.md), [dotnet-maui](../stacks/dotnet-maui.md), [flutter](../stacks/flutter.md). Cross-cutting decisions: [../core/architecture.md](../core/architecture.md), [../core/performance.md](../core/performance.md).

## Choosing a desktop approach

| Option | Rendering | Footprint | Strengths | Weak spots | Pick when |
|---|---|---|---|---|---|
| Electron | Bundled Chromium + Node.js | Large (ships a browser engine) | Consistent rendering, huge ecosystem, mature updater/packaging, web team reuse | RAM/disk use, security hardening required, frequent upgrades | Feature-rich cross-OS apps by web teams (editors, chat, IDE-like tools) |
| Tauri | System WebView + Rust core | Small | Small installers, capability-based security, Rust performance | WebView differences per OS (WebKitGTK on Linux), Rust skills | Utilities, tray apps, security-sensitive or size-sensitive apps |
| Native (SwiftUI/AppKit, WinUI/WPF, GTK/Qt) | OS toolkit | Small–medium | Best integration, accessibility, performance, OS look | One codebase per OS (Qt is cross-platform C++/QML) | Single-OS products, pro tools, deep OS integration |
| Compose Multiplatform (desktop JVM) | Skia via JVM | Medium (bundled JRE) | Kotlin sharing with Android, declarative UI | JVM startup/size, smaller desktop ecosystem | Kotlin teams, internal/dev tools, Android code reuse |
| Flutter desktop | Own renderer | Medium | Shared UI with mobile, consistent branding | Desktop idioms (menus, a11y, text) need extra work | Mobile-first products adding a desktop companion |
| .NET MAUI / WinUI / Avalonia | Native (MAUI/WinUI) or own renderer (Avalonia) | Medium | C#/.NET reuse, enterprise | MAUI has no Linux target; Mac via Catalyst | .NET shops; Windows-centric enterprise apps |
| PWA (installed web app) | Browser engine | Minimal | Zero install friction, instant updates, one codebase | Limited OS integration (filesystem, tray, background), browser-dependent | Mostly-online tools where a browser app suffices |

Decision prompts: Which OSes, in what priority? Need for filesystem, background processes, tray, global shortcuts, native SDKs? Install size/RAM constraints (VDI, low-end corporate laptops)? Offline requirement? Existing web or mobile codebase to share? Distribution channel (direct download, Mac App Store, Microsoft Store, enterprise MDM)?

## Windowing

- Define the window model early: single-window (tabs/panels inside) vs multi-window (documents, detachable panels). Multi-window needs a main-process/shared-state owner and cross-window messaging.
- Persist and restore size, position, maximized state and display — validate against current monitors (a saved position may be off-screen).
- Single-instance lock: forward second-launch arguments (files, deep links) to the running instance.
- DPI and multi-monitor: per-monitor DPI awareness, crisp icons at all scale factors, test mixed-DPI setups.
- Custom title bars: keep OS conventions (macOS traffic lights left, Windows controls right, Snap Layouts on hover of maximize where supported), provide drag regions, keep double-click-to-maximize.
- Minimum window size; responsive layouts down to it (desktop windows get narrow too).
- Tray/menu bar apps: clear "quit" vs "close to tray" behavior; do not silently keep running without an indicator.
- macOS: closing the last window usually keeps the app running (Dock); Windows/Linux usually quit — follow each.

## Menus and keyboard shortcuts

- macOS menu bar structure: **App** (About, Settings `Cmd+,`, Quit `Cmd+Q`), File, Edit (Undo/Redo/Cut/Copy/Paste/Select All — required for text fields to work), View, Window, Help.
- Windows/Linux: in-window menu bar or command bar; `Alt` access keys; Settings typically under File or a gear.
- Use `Cmd` on macOS and `Ctrl` on Windows/Linux (`CmdOrCtrl` in Electron/Tauri); respect platform-specific shortcuts (`Ctrl+Y` vs `Cmd+Shift+Z` for redo).
- Every menu command shows its accelerator; every frequent action has one; avoid clashing with OS/global shortcuts.
- Context menus on right-click (and `Shift+F10`/Menu key on Windows).
- Command palette (`CmdOrCtrl+K`/`CmdOrCtrl+Shift+P`) for power users in feature-rich apps.
- Global shortcuts (work when app unfocused) only on explicit user opt-in.

## File system and OS integration

| Integration | Notes |
|---|---|
| Open/save dialogs | Native dialogs; remember last directory; respect sandbox rules |
| macOS sandbox (App Store) | Access only user-selected files; persist access with security-scoped bookmarks |
| File associations | Register document types/extensions in the installer/bundle; handle "open with" at launch and while running |
| Protocol handlers / deep links | Custom URL schemes (`myapp://`); validate all parameters |
| Drag and drop | Files in and out of the app; show drop targets |
| Recent documents | OS recent lists (Dock/Jump Lists) |
| Notifications | Native notifications; deep-link back to content |
| Startup at login | Opt-in setting, never default-on silently |
| Clipboard | Read on user action only; support rich formats where relevant |
| File watching | Debounce; handle external edits and conflicts |

Store app data in OS-correct locations (`%APPDATA%`/`%LOCALAPPDATA%`, `~/Library/Application Support`, XDG dirs on Linux), never next to the executable.

## Auto-update

| Stack | Mechanism |
|---|---|
| Electron | `autoUpdater` (Squirrel.Mac/Squirrel.Windows) + update.electronjs.org or own server; electron-updater (electron-builder) with GitHub/S3/generic feeds |
| Tauri | `tauri-plugin-updater` with signed update artifacts and a JSON manifest/endpoint |
| Native macOS | Sparkle (outside the App Store); Mac App Store handles updates itself |
| Native Windows | MSIX + App Installer, Microsoft Store, WinGet, or a custom updater |
| Linux | Distro package repos, Flatpak/Snap stores, AppImage update tooling |

Rules: verify update signatures; download in background and apply on restart (with user prompt for long sessions); staged rollouts by percentage; ability to pull a bad release; delta updates where supported; enterprise customers may need updates disabled and managed via MDM/SCCM — make it configurable.

## Code signing and notarization

- **macOS**: Developer ID Application certificate, hardened runtime, minimal entitlements, **notarization** via `notarytool`, then staple the ticket. Unsigned/unnotarized apps are blocked by Gatekeeper by default. Mac App Store builds use different certificates and require the sandbox.
- **Windows**: Authenticode signing of executables and installers; private keys must live in hardware (HSM/token) or a cloud signing service (e.g. Azure Trusted Signing). SmartScreen warnings fade as reputation builds — do not count on any certificate type to skip that entirely. MSIX packages must be signed.
- **Linux**: sign repositories/packages (GPG) for apt/rpm; Flatpak/Snap stores handle their own signing.
- Sign in CI with secrets in a secure store; sign every binary including helpers/sidecars; timestamp signatures so they outlive certificate expiry.

## Security model

| Concern | Electron | Tauri | Native |
|---|---|---|---|
| Untrusted UI code | Renderer sandboxed; `contextIsolation`, no `nodeIntegration` | WebView has no system access except granted commands | N/A (but still validate input) |
| Privilege boundary | Preload `contextBridge` exposing narrow typed APIs; validate IPC sender and args | Commands + **capabilities/permissions** per window, scoped paths | Process/sandbox entitlements |
| Content policy | Strict CSP, block navigation/new windows | CSP in config; no remote content in privileged windows | — |
| Packaging integrity | Fuses, ASAR integrity | Signed updater artifacts | OS code signing |
| Secrets | `safeStorage`/OS keychain | Keychain via Rust/Stronghold | Keychain / DPAPI / Secret Service |

Baseline for all: least privilege, no secrets in the binary, validate all IPC/deep-link/file inputs, keep runtimes (Chromium, WebView2, OS deps) patched, signed updates only.

## Offline and data

- Desktop users expect apps to open and work without network: local DB (SQLite) as source of truth for documents/projects, sync in background.
- Use OS-correct data directories; plan migrations for local schema; back up before migrating.
- Large files: stream, do not load into memory; work off the UI thread/process.
- Crash safety: atomic writes (write temp + rename), autosave and recovery on next launch.
- Sync conflicts: same strategies as mobile (outbox, idempotency, merge rules) — see [mobile.md](mobile.md#offline-first-and-sync).

## Accessibility on desktop

- Use OS accessibility APIs through your toolkit: UI Automation (Windows), NSAccessibility (macOS), AT-SPI (Linux). WebView-based apps inherit these from semantic HTML + ARIA.
- **Full keyboard operability** is mandatory: tab order, arrow-key navigation in lists/trees/grids, visible focus, no keyboard traps, menu accelerators.
- Support high contrast/contrast themes (Windows), Increase Contrast and Reduce Motion (macOS), OS text scaling and in-app zoom without layout breakage.
- Screen readers to test: Narrator, NVDA, JAWS (Windows); VoiceOver (macOS); Orca (Linux).
- Tools: Accessibility Insights for Windows, Xcode Accessibility Inspector, axe-core for WebView UIs.
- Target WCAG 2.2 AA as applicable to software, plus platform guidelines.

## References

- https://www.electronjs.org/docs/latest/tutorial/security
- https://v2.tauri.app/security/
- https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- https://learn.microsoft.com/windows/apps/design/
- https://developer.apple.com/design/human-interface-guidelines/designing-for-macos
- https://learn.microsoft.com/windows/apps/design/accessibility/accessibility-overview
