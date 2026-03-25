# Critical Rendering Path

> **Date:** 2026-03-25
> **Category:** Frontend System Design
> **Sub-Topic:** Performance / Rendering

> **Pre-requisite:** Read [How Browsers Work](./how-browsers-work.md) first.
> This note focuses on **optimizing** the pipeline — not explaining it from scratch.

---

## ELI5 — Simple Explanation

Imagine a new restaurant opening day:
- Without optimization: Chef waits for ALL ingredients before cooking anything → customers wait forever
- With optimization: Chef starts cooking with available ingredients, orders the rest in parallel → first dish out fast

> **CRP = The minimum steps browser MUST complete before showing ANYTHING on screen.**
> **Optimizing CRP = reducing what blocks those first steps.**

---

## Core Concept — Step by Step

### Section 1: What is the Critical Rendering Path?

The **Critical Rendering Path (CRP)** is specifically about:
- **Which resources block** the browser from rendering
- **How many bytes** must download before first render
- **How many round trips** to the server are required

```
GOAL: Get pixels on screen as fast as possible

PROBLEM: Some resources BLOCK the pipeline
         Until they finish downloading → nothing renders

SOLUTION: Identify + eliminate blocking resources
```

**Three CRP metrics:**

| Metric | What it measures | How to reduce |
|---|---|---|
| **Critical Resources** | Files that block rendering | Fewer files, inline critical CSS |
| **Critical Bytes** | Total size of blocking files | Minify, compress (gzip/brotli) |
| **Critical Round Trips** | Network requests needed | HTTP/2, preload, reduce files |

---

### Section 2: Render-Blocking Resources

#### CSS — Always Render-Blocking

```html
<!-- Browser STOPS rendering until this fully downloads -->
<link rel="stylesheet" href="styles.css">
```

Why? Browser needs CSSOM to build Render Tree → needs Render Tree to paint → nothing shows until CSS loads.

#### JavaScript — Parser-Blocking by Default

```html
<!-- Default: STOPS HTML parsing AND delays rendering -->
<script src="app.js"></script>
```

**The fix — `defer` vs `async`:**

```
DEFAULT <script>:
HTML:  ████████░░░░░░░░░░░████████  ← paused while JS downloads + runs
JS:            ████████████

DEFER:
HTML:  ████████████████████████    ← never paused
JS:            ████████████░░░░    ← runs AFTER HTML fully parsed, in order

ASYNC:
HTML:  ████████████░░████████████  ← paused only when JS actually runs
JS:            ████████████        ← runs immediately when downloaded, any order
```

**When to use which:**

| | `defer` | `async` |
|---|---|---|
| Needs DOM ready | ✅ Yes | ❌ No |
| Order matters | ✅ Preserves order | ❌ Random order |
| Use for | App scripts, frameworks | Analytics, ads, independent scripts |

---

### Section 3: Resource Hints

Tell the browser what it needs **before** it discovers it in HTML:

```html
<!-- preload: fetch THIS file RIGHT NOW (critical for current page) -->
<link rel="preload" href="hero.jpg" as="image">
<link rel="preload" href="main.js" as="script">
<link rel="preload" href="font.woff2" as="font" crossorigin>

<!-- preconnect: open TCP+TLS to domain early (no file yet) -->
<link rel="preconnect" href="https://fonts.googleapis.com">

<!-- dns-prefetch: just DNS lookup early (cheaper than preconnect) -->
<link rel="dns-prefetch" href="https://api.mysite.com">

<!-- prefetch: fetch for NEXT page navigation (low priority) -->
<link rel="prefetch" href="next-page-bundle.js">
```

**When to use each:**

| Hint | Use when | Priority |
|---|---|---|
| `preload` | Current page needs this file soon | 🔴 High — fetch immediately |
| `preconnect` | Will request from this domain soon | 🟡 Medium — open connection |
| `dns-prefetch` | May request from this domain | 🟢 Low — just DNS |
| `prefetch` | Next page will need this file | 🔵 Idle — download when quiet |

---

### Section 4: Inlining Critical CSS

**Critical CSS** = styles for content visible without scrolling (above the fold).

```html
<head>
  <!-- INLINE: renders immediately, zero network cost -->
  <style>
    /* Only above-the-fold styles — keep under 14KB (1 TCP round trip) */
    body  { margin: 0; font-family: sans-serif; }
    .hero { background: #1a1a2e; color: white; padding: 60px; }
    .nav  { display: flex; justify-content: space-between; }
  </style>

  <!-- DEFER rest of CSS: non-blocking trick -->
  <link rel="stylesheet"
        href="full-styles.css"
        media="print"
        onload="this.media='all'">
  <noscript>
    <link rel="stylesheet" href="full-styles.css">
  </noscript>
</head>
```

**Why 14KB limit?** → First TCP round trip carries ~14KB. Inline CSS within 14KB = renders without extra network wait.

---

### Section 5: Font Optimization

Fonts are a common CRP bottleneck:

```html
<!-- BAD: font blocks render → Flash of Invisible Text (FOIT) -->
<link href="https://fonts.googleapis.com/css?family=Inter" rel="stylesheet">

<!-- GOOD: 3 optimizations together -->

<!-- 1. preconnect: open connection to Google Fonts early -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- 2. load font CSS non-blocking -->
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter"
      media="print" onload="this.media='all'">

<!-- 3. font-display: swap in CSS → show fallback instantly, swap when loaded -->
<style>
  @font-face {
    font-family: 'Inter';
    src: url('inter.woff2') format('woff2');
    font-display: swap;  /* no invisible text */
  }
</style>
```

---

### Section 6: CRP Performance Metrics

| Metric | Measures | Good Target |
|---|---|---|
| **FCP** — First Contentful Paint | First text/image visible | < 1.8s |
| **LCP** — Largest Contentful Paint | Main content visible | < 2.5s |
| **TTI** — Time To Interactive | Page fully usable | < 3.8s |
| **TBT** — Total Blocking Time | JS blocking main thread | < 200ms |
| **CLS** — Cumulative Layout Shift | Visual stability | < 0.1 |

---

## Visual — Optimized vs Unoptimized

```
❌ UNOPTIMIZED:
────────────────────────────────────────────────────────
HTML:       ████
            → hits <link css> → STOP
CSS:              ████████████████
                                  → hits <script> → STOP
JS:                               ████████████
Render Tree:                                  ██
Layout:                                         ██
First Paint:                                      ✅ SLOW (1.8s+)


✅ OPTIMIZED:
────────────────────────────────────────────────────────
Critical CSS: (inlined in HTML, no extra request)
HTML:       ████
            → CSSOM ready immediately from inline CSS
JS defer:       ████████ (parallel download, runs after)
Render Tree:        ██
Layout:               ██
First Paint:            ✅ FAST (< 0.5s)
```

---

## Real-World Examples

**Example 1 — Correct script loading:**
```html
<head>
  <!-- Analytics: independent, load async -->
  <script async src="analytics.js"></script>

  <!-- Preload app bundle so it's ready when needed -->
  <link rel="preload" href="app.js" as="script">
</head>
<body>
  <div id="app"></div>

  <!-- App: needs DOM, runs after parse, in order -->
  <script defer src="vendors.js"></script>
  <script defer src="app.js"></script>
</body>
```

**Example 2 — Hero image optimization (LCP fix):**
```html
<!-- BAD: browser discovers hero image late during parse -->
<img src="hero.jpg" alt="Hero">

<!-- GOOD: preload tells browser immediately -->
<link rel="preload" as="image" href="hero.jpg">
<img src="hero.jpg" alt="Hero" fetchpriority="high">
```

**Example 3 — Eliminate render-blocking CSS:**
```html
<!-- BAD: all CSS blocks render -->
<link rel="stylesheet" href="styles.css">
<link rel="stylesheet" href="animations.css">
<link rel="stylesheet" href="print.css">

<!-- GOOD: only critical CSS blocks, rest deferred -->
<style>/* critical above-fold styles inlined */</style>
<link rel="stylesheet" href="styles.css" media="print" onload="this.media='all'">
<link rel="stylesheet" href="animations.css" media="print" onload="this.media='all'">
<link rel="stylesheet" href="print.css" media="print">
```

---

## Key Points Summary

| Concept | One-Line Explanation |
|---|---|
| **CRP** | Minimum steps before browser shows anything on screen |
| **Render-blocking CSS** | ALL CSS files block rendering until downloaded |
| **Parser-blocking JS** | Default `<script>` stops HTML parsing |
| **defer** | Script runs after HTML parsed, in order |
| **async** | Script runs immediately when downloaded, any order |
| **Critical CSS** | Above-the-fold styles inlined in `<head>` |
| **preload** | Force-fetch critical resource immediately |
| **preconnect** | Open connection to domain early |
| **FCP** | First Contentful Paint — first visible text/image |
| **LCP** | Largest Contentful Paint — main content visible |

---

## Test Your Understanding

**Q1 (Basic):**
A page has 3 `<link>` CSS files and 2 `<script>` tags (no `defer`/`async`).
How many render-blocking resources are there?

**Q2 (Application):**
Your LCP score is 4.2s — too slow. The LCP element is a hero image.
List 3 specific techniques with code to fix it.

**Q3 (Tricky):**
A developer adds `<link rel="preload" as="script" href="app.js">` but forgets the actual `<script src="app.js">` tag.
What happens? Does preload help here?

---

## Cheat Sheet

**Key Definitions:**
- **CRP:** Minimum steps before first pixel on screen
- **Render-blocking:** Resource that pauses the rendering pipeline
- **Critical CSS:** Above-fold styles that must load for first paint
- **FCP:** First visible text or image
- **LCP:** Largest visible content element painted

**Essential HTML:**
```html
<!-- Script loading -->
<script defer src="x.js">    <!-- after HTML parse, in order -->
<script async src="x.js">    <!-- immediately when ready, no order -->

<!-- Resource hints -->
<link rel="preload" href="x" as="font|script|style|image">
<link rel="preconnect" href="https://domain.com">
<link rel="dns-prefetch" href="https://domain.com">
<link rel="prefetch" href="next-page.js">

<!-- Non-blocking CSS -->
<link rel="stylesheet" href="x.css"
      media="print" onload="this.media='all'">

<!-- Font display -->
font-display: swap;
```

**CRP Optimization Checklist:**
```
✅ Inline critical (above-fold) CSS in <head>
✅ Defer all non-critical CSS with media="print" trick
✅ defer app scripts, async analytics/ads
✅ preconnect to Google Fonts, CDN domains
✅ preload hero image with fetchpriority="high"
✅ preload critical fonts
✅ font-display: swap for web fonts
✅ Minify + gzip/brotli all assets
✅ HTTP/2 to reduce round trips
✅ Keep inline critical CSS under 14KB
```

**Common Mistakes to Avoid:**

| Mistake | Why Wrong | Fix |
|---|---|---|
| `<script>` in `<head>` no defer | Blocks HTML parsing | Add `defer` or move to bottom of `<body>` |
| All CSS in one unspilt file | Entire file blocks render | Inline critical + defer rest |
| No `preconnect` for Google Fonts | Extra DNS+TCP delay | Add `<link rel="preconnect">` |
| `async` for interdependent scripts | Runs out of order, breaks app | Use `defer` for ordered execution |
| Hero image not preloaded | LCP is slow | `<link rel="preload" as="image">` |
| `preload` without using the resource | Wastes bandwidth | Only preload what current page uses |
| Third-party scripts not async | Blocks entire page for external server | Always `async` or `defer` third-party |

---

> **Previous Topic:** [How Browsers Work](./how-browsers-work.md)
> — Understand the full browser pipeline before optimizing it

*Saved on: 2026-03-25 | Repo: Frontend System Design Learning Notes*
