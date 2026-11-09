# Mobile platform guide

System design essentials for iOS and Android apps. Stack details: [react-native-expo](../stacks/react-native-expo.md), [flutter](../stacks/flutter.md), [swiftui](../stacks/swiftui.md), [jetpack-compose](../stacks/jetpack-compose.md), [compose-multiplatform](../stacks/compose-multiplatform.md), [dotnet-maui](../stacks/dotnet-maui.md), [ionic-capacitor](../stacks/ionic-capacitor.md). Cross-cutting decisions: [../core/architecture.md](../core/architecture.md), [../core/performance.md](../core/performance.md).

## Native vs cross-platform decision

| Option | UI approach | Code sharing | Strengths | Weak spots | Pick when |
|---|---|---|---|---|---|
| Swift/SwiftUI + Kotlin/Compose | Native per platform | None (or logic via KMP) | Best feel, performance, day-one OS APIs, a11y | Two codebases/teams | Platform experience is the product; deep OS integration; budget for two teams |
| Flutter | Own renderer, custom widgets | UI + logic (~all) | Consistent branded UI, strong perf, one team | Not native widgets; plugin quality varies; Dart | Brand-driven UI, one team, mobile (+desktop) |
| React Native / Expo | Native views from React | UI + logic (high) | React/TS skills, web sharing, OTA JS updates, Expo tooling | JS/native boundary, library New-Arch support | Web/React team; CRUD/commerce/social apps |
| Kotlin Multiplatform (+ Compose MP) | Shared Compose UI or native UI per platform | Logic always; UI optional | Gradual adoption, native escape hatch, Kotlin | iOS tooling/ecosystem younger; Swift interop care | Android/Kotlin team adding iOS; existing native apps |
| .NET MAUI | Native controls via handlers | UI + logic | C#/.NET reuse, Windows target, enterprise suites | Smaller mobile ecosystem, polish effort | .NET shop, LOB/field apps, Windows + mobile |
| Ionic + Capacitor | Web UI in WebView | Web + mobile (~all) | Reuse web app/skills, PWA from same code | WebView perf ceiling, less native feel | Content/forms/internal apps, existing web app |

Decision prompts: Who is on the team today? Which OS features are in the first 12 months (widgets, watch, background audio, BLE, CarPlay)? Is pixel-consistent branding or platform-native feel the goal? Must code be shared with web? How strict are size/perf budgets?

## Navigation patterns

| Pattern | Use for | Rules |
|---|---|---|
| Bottom tabs (iOS tab bar / Material navigation bar) | 3–5 top-level destinations | Each tab keeps its own stack; re-tap scrolls to top/pops to root |
| Stack (push/pop) | Drill-down hierarchy | System back gesture/button must always work; preserve scroll position |
| Modal / sheet | Focused self-contained tasks (compose, filter, checkout step) | Clear dismiss + unsaved-change confirmation; sheets with detents for quick actions |
| Drawer / navigation rail | Many sections, tablets/foldables | Adapt: bottom bar on phones, rail/sidebar on large screens |
| Deep links | Custom schemes (`myapp://`) | Never trust parameters; route through the same router as in-app nav |
| Universal Links (iOS) / App Links (Android) | HTTPS links open the app if installed, web otherwise | Host `apple-app-site-association` and `assetlinks.json`; web fallback page must work |

Design every screen as addressable by URL from day one: it unlocks push-to-screen, sharing, marketing links, state restoration and E2E test shortcuts. Deferred deep links (after install) need a third-party or custom attribution service.

## Offline-first and sync

- Decide per feature: **online-only** (show clear error/retry), **offline-read** (cache last data), **offline-write** (local queue + sync), **local-first** (DB is source of truth, sync in background).
- Architecture: UI observes local DB (single source of truth) → repository fetches remote and writes DB → UI updates reactively.
- Write path: optimistic local write + outbox table of pending mutations with idempotency keys; retry with backoff on connectivity.
- Conflicts: last-write-wins for simple fields; per-field merge or server-side resolution for collaborative data; CRDTs only when true multi-writer collaboration is required.
- Sync triggers: app foreground, connectivity regained, push (silent/data message), periodic background task (best-effort).
- Show sync state in the UI (pending, failed with retry) and handle auth expiry during queued writes.
- Plan schema migrations for the local DB like server migrations — they ship inside app updates and old versions linger.

## Push notifications

- Transport: APNs (iOS) and FCM (Android; can also proxy to APNs). Store device tokens server-side per user+device, refresh on change, delete on logout.
- Permission: iOS requires an explicit prompt; recent Android versions also require a runtime notification permission. Ask **in context** after showing value (pre-permission screen), never on first launch.
- iOS provisional authorization delivers quietly to Notification Center without a prompt — good for gradual opt-in.
- Android notification channels per category so users can tune them; iOS interruption levels (passive, active, time-sensitive) used honestly.
- Silent/background pushes are throttled and not guaranteed — never rely on them for critical sync.
- Every notification deep-links to the relevant screen; track opens; respect quiet hours and frequency caps.

## Permissions UX

- Request at the moment of need, tied to a user action; explain value first (pre-prompt), then trigger the OS dialog.
- Handle every state: granted, denied, limited (photos, approximate location), "don't ask again" → link to Settings.
- Request minimum scope: approximate before precise location, photo picker instead of full library access, "while using" before "always".
- Declare purpose strings (iOS `Info.plist` usage descriptions) and Play data safety/permission declarations accurately — store review checks them.
- Degrade gracefully: the app must remain usable without optional permissions.

## Background tasks

| Need | iOS | Android |
|---|---|---|
| Periodic refresh | `BGAppRefreshTask` (system decides timing) | WorkManager periodic work |
| Long maintenance work | `BGProcessingTask` (often when charging/idle) | WorkManager with constraints |
| Uploads/downloads | Background `URLSession` | WorkManager / download manager |
| Ongoing user-visible work | Specific background modes (audio, location, VoIP), Live Activities | Foreground service with declared type + notification |

Assume background execution is opportunistic and can be killed; design idempotent, resumable jobs.

## Performance budgets (starting targets)

| Metric | Starting target | Notes |
|---|---|---|
| Cold start to first meaningful content | ≤ 2 s on a mid-tier device | Android vitals flags excessive cold starts; measure release builds |
| Frame time | ≤ 16.7 ms @60 Hz, ≤ 8.3 ms @120 Hz | Scroll and gestures jank-free; track slow/frozen frames |
| Download size | Keep as small as features allow; review every new SDK | Stores warn users before large cellular downloads; size affects install conversion |
| Memory | No growth across repeated navigation loops | Watch for leaks and image decode spikes on low-RAM devices |
| Crash-free sessions | ≥ 99.5% as an initial bar, raise over time | Also track ANRs (Android) and hangs (iOS) |

Tools: Xcode Instruments + MetricKit + Organizer; Android Studio profilers, Macrobenchmark, Baseline Profiles, Play Console Android vitals; Firebase Performance/Sentry for field data. Budgets are starting targets — calibrate to your users' devices.

## Store review and OTA policy caveats

- **Apple**: apps must be self-contained; downloading executable code that changes features is not allowed. Interpreted code (e.g. JavaScript) may be updated if it does not change the app's primary purpose, create a storefront for other code, or bypass review/security.
- **Google Play**: apps may not update themselves outside Play or download executable native code (dex, JAR, .so); code running in a VM/interpreter such as JavaScript in a WebView is exempt, within other policies.
- Practical OTA rules (EAS Update, Capacitor live updates, Dart code-push services): bug fixes and content/UI tweaks only; version-pin updates to the native runtime; staged rollout + instant rollback; never ship features that would fail review.
- Review risks: minimum functionality (thin web wrappers), in-app purchase rules for digital goods (regional rules vary — check current terms), account deletion requirement if you offer account creation, privacy nutrition labels / data safety forms, third-party SDK privacy manifests on iOS.
- Plan for review time in release schedules; keep an expedited-review/hotfix path documented.

## Mobile accessibility

- Screen readers: VoiceOver (iOS), TalkBack (Android) — every interactive element has a label, role/trait and state; decorative elements hidden.
- Text scaling: support Dynamic Type / Android font scale up to the largest sizes; layouts reflow (stack horizontally arranged content), no truncated critical text.
- Touch targets ≥ 44×44 pt (iOS HIG) / 48×48 dp (Material); adequate spacing between targets.
- Focus order follows visual order; move focus on screen change, modal open/close; announce async results.
- Respect Reduce Motion, Increase Contrast/Bold Text, color-independent status indicators; contrast meets WCAG 2.2 AA.
- Support external keyboards and switch control on tablets.
- Test on device with screen readers, plus Xcode Accessibility Inspector and Android Accessibility Scanner; add automated checks in UI tests.

## Platform conventions: HIG vs Material 3

| Concern | iOS (Human Interface Guidelines) | Android (Material 3) |
|---|---|---|
| Back navigation | Back button top-left + edge swipe | System back gesture/button (predictive back) |
| Primary nav | Tab bar (bottom), sidebar on iPad | Navigation bar (bottom), rail/drawer on large screens |
| Primary action | Toolbar/nav bar buttons | FAB or prominent filled button |
| Typography | San Francisco, Dynamic Type text styles | Roboto/brand font, Material type scale, `sp` units |
| Dialogs/sheets | Alerts, action sheets, sheets with detents | Dialogs, bottom sheets, snackbars |
| Feedback | Haptics, subtle highlights | Ripple/state layers, haptics |
| Color | System semantic colors, vibrancy/materials | Dynamic color from wallpaper, tonal palettes |
| Icons | SF Symbols | Material Symbols |
| Units | Points (pt) | Density-independent pixels (dp/sp) |

Brand-uniform UIs are valid, but keep platform behaviors (back, gestures, text selection, scroll physics, share sheets, pickers) native.

## Mobile security

- Secrets: user tokens in **Keychain** (iOS) / **Android Keystore**-backed encryption; never plain `UserDefaults`/SharedPreferences/AsyncStorage. (Jetpack Security's EncryptedSharedPreferences is deprecated — use Keystore-backed keys with DataStore or Tink.)
- **No secrets in the app binary**: anything shipped can be extracted. Use a backend to hold API keys; short-lived tokens; scoped public keys only.
- Auth: OAuth 2.0 + PKCE via system browser session (`ASWebAuthenticationSession`, Custom Tabs; AppAuth libraries); refresh tokens rotated; biometric unlock gates local key access.
- TLS everywhere (ATS on iOS, network security config on Android: no cleartext).
- **Certificate pinning trade-offs**: protects against compromised CAs/MITM on hostile networks, but a rotation mistake bricks connectivity for all installed versions. If used: pin public keys (SPKI), include backup pins, have a remote kill switch or expiry, coordinate with infra rotation.
- App integrity: App Attest / DeviceCheck (iOS), Play Integrity API (Android) checked server-side; jailbreak/root detection is advisory only.
- Obfuscation/minification (R8, Dart `--obfuscate`) raises effort but is not security; validate everything server-side.
- Reference: OWASP MASVS/MASTG for checklists.

## Release strategy

- **Phased/staged rollout**: App Store phased release (automatic over several days, pausable) and Play staged rollout percentages with halt; watch crash/ANR/business metrics before widening.
- **Feature flags / remote config**: ship dark, enable per cohort, kill switch for risky features; decouple release from deploy.
- **Force update**: backend exposes minimum supported version per platform; app checks at start → blocking "Update required" screen with store link (Android: In-App Updates immediate flow). Use soft prompts for recommended versions.
- **Backward compatibility**: old app versions live for months — version APIs, keep contracts additive, make the backend tolerant of unknown clients.
- Release train cadence (e.g. weekly/biweekly) with automated builds (Fastlane, EAS, Codemagic, Xcode Cloud, Gradle Play Publisher), beta channels (TestFlight, Play internal/closed testing), and release notes.
- Monitor post-release: crash reporting with symbol/mapping upload, store ratings, vitals dashboards.

## References

- https://developer.apple.com/design/human-interface-guidelines/
- https://m3.material.io/
- https://developer.apple.com/app-store/review/guidelines/
- https://play.google.com/about/developer-content-policy/
- https://developer.android.com/topic/architecture/data-layer/offline-first
- https://mas.owasp.org/
