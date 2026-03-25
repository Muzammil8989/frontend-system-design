# Critical Rendering Path

> **Date:** 2026-03-25
> **Category:** Frontend System Design
> **Sub-Topic:** Rendering / Performance

---

## ELI5 — Simple Explanation

Imagine building a house before anyone can live in it:
- First you need the **blueprint** (HTML → DOM)
- Then the **interior design plan** (CSS → CSSOM)
- Then **combine both plans** (Render Tree)
- Then **measure every room** (Layout)
- Then **paint the walls** (Paint)
- Then **open the doors** for people (Screen visible)

> **CRP = The minimum set of steps a browser MUST complete before showing anything on screen.**
> Optimizing CRP = making users see your page faster.

---

## Core Concept — Step by Step

### Section 1: What is the Critical Rendering Path?

The **Critical Rendering Path (CRP)** is the sequence of steps the browser takes to convert HTML + CSS + JS into pixels on screen.

```
HTML  ──→  DOM
CSS   ──→  CSSOM
            ↓
       Render Tree
            ↓
          Layout
            ↓
          Paint
            ↓
        Composite
            ↓
         SCREEN ✅
```

**Why it matters:**
- Every extra step = more time before user sees content
- Blocking resources (CSS, JS) pause this pipeline
- Faster CRP = better **FCP** (First Contentful Paint) & **LCP** (Largest Contentful Paint)

---

### Section 2: Render-Blocking Resources

**Render-blocking** = resource that pauses the CRP pipeline until it fully downloads + processes.

#### CSS is always render-blocking

```html
<!-- This BLOCKS rendering until styles.css fully downloads -->
<link rel="stylesheet" href="styles.css">
```

Browser will NOT render anything until ALL CSS is downloaded.
Why? Because it needs CSSOM to build the Render Tree.

#### JavaScript is parser-blocking (by default)

```html
<!-- BAD: stops HTML parsing AND rendering -->
<script src="app.js"></script>

<!-- GOOD: downloads in parallel, runs after HTML parsed -->
<script src="app.js" defer></script>

<!-- GOOD: downloads in parallel, runs immediately when ready -->
<script src="app.js" async></script>
```

#### `defer` vs `async` — Key Difference

```
Normal <script>:
HTML: ██████░░░░░░░░░░░░██████  (pause while JS downloads + runs)
JS:         ████████████

defer:
HTML: ██████████████████████    (never paused)
JS:         ████████████░░░░    (runs AFTER HTML fully parsed)

async:
HTML: ██████████░░░██████████   (paused only when JS runs)
JS:         ████████████        (runs immediately when downloaded)
```

> **Rule:** Use `defer` for scripts that need the DOM. Use `async` for independent scripts (analytics, ads).

---

### Section 3: Critical Resources, Bytes & Round Trips

Three metrics define CRP cost:

| Metric | What it means | How to reduce |
|---|---|---|
| **Critical Resources** | Number of files that block rendering | Fewer CSS/JS files, inline critical CSS |
| **Critical Bytes** | Total size of blocking files | Minify, compress (gzip/brotli), tree-shake |
| **Critical Round Trips** | Number of network requests needed | HTTP/2 multiplexing, preload, reduce files |

---

### Section 4: Preload, Prefetch, Preconnect

Tell the browser what it will need **before** it discovers it:

```html
<!-- preload: fetch THIS resource ASAP (critical for current page) -->
<link rel="preload" href="hero-font.woff2" as="font" crossorigin>
<link rel="preload" href="critical.css" as="style">

<!-- prefetch: fetch for NEXT page navigation (low priority) -->
<link rel="prefetch" href="next-page.js">

<!-- preconnect: open TCP+TLS to a domain early (no file yet) -->
<link rel="preconnect" href="https://fonts.googleapis.com">

<!-- dns-prefetch: just DNS lookup early (cheaper than preconnect) -->
<link rel="dns-prefetch" href="https://api.mysite.com">
```

---

### Section 5: Inlining Critical CSS

**Critical CSS** = styles needed for above-the-fold content (what user sees first without scrolling).

```html
<!-- Strategy: inline critical CSS → defer the rest -->
<head>
  <!-- INLINE: renders immediately, no network request -->
  <style>
    body { margin: 0; font-family: sans-serif; }
    .hero { background: #1a1a2e; color: white; padding: 60px; }
    .nav  { display: flex; justify-content: space-between; }
  </style>

  <!-- DEFER: non-critical CSS loads after render -->
  <link rel="stylesheet" href="full-styles.css" media="print"
        onload="this.media='all'">
</head>
```

> **Result:** Page renders with hero section visible immediately. Rest of styles load in background.

---

### Section 6: Measuring CRP — Key Metrics

| Metric | What it measures | Good target |
|---|---|---|
| **FCP** (First Contentful Paint) | When first text/image appears | < 1.8s |
| **LCP** (Largest Contentful Paint) | When main content appears | < 2.5s |
| **TTI** (Time To Interactive) | When page is fully interactive | < 3.8s |
| **TBT** (Total Blocking Time) | JS blocking main thread | < 200ms |
| **CLS** (Cumulative Layout Shift) | Visual stability score | < 0.1 |

---

## Visual — CRP Optimization Comparison

```
UNOPTIMIZED CRP:
─────────────────────────────────────────────────────
HTML download  ████
               → parse → hit CSS link → STOP
CSS download           ████████████████
                                       → CSSOM built
JS download            ██████
                             → JS runs → DOM modified
Render Tree                                          ██
Layout                                                 ██
Paint                                                    ██
Screen visible                                             ✅ LATE

OPTIMIZED CRP:
─────────────────────────────────────────────────────
Inline CSS     (already in HTML, no extra request)
HTML download  ████
               → parse → DOM + CSSOM built together
JS defer       ████████ (parallel, runs after parse)
Render Tree        ██
Layout               ██
Paint                  ██
Screen visible           ✅ EARLY
```

---

## Real-World Examples

**Example 1 — Google's approach (inline critical CSS):**
```html
<head>
  <style>
    /* Only above-the-fold styles — ~14KB max (1 TCP round trip) */
    .search-bar { ... }
    .logo { ... }
  </style>
  <link rel="stylesheet" href="rest.css" media="print" onload="this.media='all'">
</head>
```

**Example 2 — Font optimization:**
```html
<!-- BAD: font blocks render, causes Flash of Invisible Text (FOIT) -->
<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet">

<!-- GOOD: preconnect early + font-display swap -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
  @font-face {
    font-family: 'Inter';
    font-display: swap; /* show fallback font instantly, swap when loaded */
  }
</style>
```

**Example 3 — Script loading strategy:**
```html
<head>
  <!-- analytics: doesn't need DOM, load async -->
  <script async src="analytics.js"></script>

  <!-- preload important script so it's ready when needed -->
  <link rel="preload" href="main-app.js" as="script">
</head>
<body>
  <!-- app script: needs DOM, run after parse -->
  <script defer src="main-app.js"></script>
</body>
```

---

## Key Points Summary

| Concept | One-Line Explanation |
|---|---|
| **Critical Rendering Path** | Steps browser must complete before showing pixels |
| **Render-blocking CSS** | ALL CSS blocks rendering until fully downloaded |
| **Parser-blocking JS** | Default `<script>` pauses HTML parsing |
| **defer** | Script runs after HTML parsed, in order |
| **async** | Script runs immediately when downloaded, any order |
| **Critical CSS** | Above-the-fold styles inlined in `<head>` |
| **preload** | Force-fetch critical resource early |
| **prefetch** | Fetch resource for next navigation |
| **preconnect** | Open TCP+TLS connection to domain early |
| **FCP / LCP** | Key metrics measuring CRP speed |

---

## Test Your Understanding

**Q1 (Basic):**
A page has 3 CSS files and 2 JS files (no `defer`/`async`). How many render-blocking resources does it have, and which steps of the CRP are delayed?

**Q2 (Application):**
You have a Google Font causing a 500ms delay in your FCP. List 3 specific techniques you would apply (with code) to fix this without removing the font.

**Q3 (Tricky):**
A developer uses `<link rel="preload" as="script" href="app.js">` but forgets the `<script src="app.js">` tag. What happens? Does preload help or hurt here?

---

## Cheat Sheet

**Key Definitions:**
- **CRP:** Steps from HTML/CSS/JS → visible pixels
- **Render-blocking:** Resource that pauses CRP pipeline
- **Parser-blocking:** Resource that pauses HTML parsing
- **Critical CSS:** Above-the-fold styles needed for first paint
- **FCP:** First Contentful Paint — first text/image visible
- **LCP:** Largest Contentful Paint — main content visible

**Key HTML Tags:**
```html
<!-- Script loading -->
<script src="x.js">          <!-- blocks parser + render -->
<script src="x.js" defer>    <!-- non-blocking, runs after parse, in order -->
<script src="x.js" async>    <!-- non-blocking, runs ASAP, no order -->

<!-- Resource hints -->
<link rel="preload" href="x" as="font|script|style|image">
<link rel="prefetch" href="x">
<link rel="preconnect" href="https://domain.com">
<link rel="dns-prefetch" href="https://domain.com">

<!-- Non-blocking CSS trick -->
<link rel="stylesheet" href="x.css" media="print" onload="this.media='all'">
```

**CRP Optimization Checklist:**
- Inline critical (above-fold) CSS in `<head>`
- Defer all non-critical CSS
- Use `defer` on app scripts, `async` on analytics
- `preconnect` to third-party domains (fonts, APIs)
- `preload` critical fonts, hero images
- Minify + compress HTML/CSS/JS (gzip/brotli)
- Use HTTP/2 to reduce round trips
- Use `font-display: swap` for web fonts

**Common Mistakes to Avoid:**

| Mistake | Why Wrong | Fix |
|---|---|---|
| All CSS in one big file | Entire file blocks render | Split: inline critical + defer rest |
| `<script>` in `<head>` without `defer` | Blocks HTML parsing | Add `defer` or move before `</body>` |
| No `preconnect` for Google Fonts | DNS + TCP delay on first request | Add `<link rel="preconnect">` |
| Using `async` for scripts that depend on each other | Runs out of order, breaks app | Use `defer` for ordered execution |
| Loading hero image without `preload` | LCP is slow | `<link rel="preload" as="image" href="hero.jpg">` |
| `preload` without actually using the resource | Wastes bandwidth | Only preload what current page uses |
| Render-blocking third-party scripts | Delays entire page | Use `async` or load after page interactive |

---

*Saved on: 2026-03-25 | Repo: Frontend System Design Learning Notes*
