# How Browsers Work

> **Date:** 2026-03-25
> **Category:** Frontend System Design
> **Sub-Topic:** Rendering / Networking / Performance

---

## ELI5 — Simple Explanation

Imagine you order food at a restaurant:
- You give your **order** (URL) to the waiter (browser)
- Waiter goes to the **kitchen** (server) and fetches food (HTML/CSS/JS)
- Kitchen prepares and **plates** it (renders the page)
- You **see** the final dish on your table (screen)

> **Browser = Messenger + Chef + Painter** — it fetches, processes, and paints everything you see.

---

## Core Concept — Step by Step

### Section 1: URL to Server — Networking Phase

```
You type: https://google.com
         ↓
Step 1 → DNS Lookup
         "google.com" → finds IP address → 142.250.80.46
         ↓
Step 2 → TCP Connection
         Browser connects to server (3-way handshake)
         SYN → SYN-ACK → ACK
         ↓
Step 3 → TLS Handshake (HTTPS only)
         Secure encrypted tunnel established
         ↓
Step 4 → HTTP Request sent
         GET / HTTP/1.1
         Host: google.com
         ↓
Step 5 → Server sends back HTML response
```

**Key Term — DNS (Domain Name System):**
> Like a phone book. Converts `google.com` → IP address so browser knows WHERE to send the request.

**Key Term — TCP Handshake:**
> Like knocking on a door and waiting for "come in" before entering. Ensures connection is ready before sending data.

---

### Section 2: HTML Received — Parsing Phase

Once browser gets the HTML file, it starts **parsing** (reading + understanding):

```
HTML Text (raw string)
      ↓
Tokenizer
      ↓
DOM Tree (Document Object Model)
```

**What is the DOM?**
> DOM = HTML converted into a **tree of objects** that JavaScript can read and modify.

```
HTML:                        DOM Tree:
<html>                       Document
  <body>                     └── html
    <h1>Hello</h1>                └── body
    <p>World</p>                       ├── h1 → "Hello"
  </body>                             └── p  → "World"
</html>
```

**Important:** When parser hits `<script>` tag → it **STOPS** parsing HTML until JS downloads + runs.
This is why we put `<script>` at bottom of `<body>` or use `defer`/`async`.

---

### Section 3: CSS — CSSOM Construction

Parallel to DOM, browser also builds **CSSOM** (CSS Object Model):

```
CSS Text
    ↓
CSSOM Tree
    ↓
Every element gets computed styles
```

```
CSS:                    CSSOM:
body { font: 16px }     body → font-size: 16px
h1   { color: red  }    └── h1 → color: red
```

---

### Section 4: Render Tree — Combining DOM + CSSOM

```
DOM Tree  +  CSSOM Tree
        ↓
   Render Tree
(only VISIBLE elements)
```

> `display: none` elements are **excluded** from Render Tree.
> `visibility: hidden` elements are **included** (take space but invisible).

---

### Section 5: Layout (Reflow)

Browser calculates **exact position and size** of every element:

```
Render Tree
     ↓
Layout Engine
     ↓
Box Model calculated for each element:
- Width, Height
- Position (x, y)
- Margin, Padding, Border
```

**Key Term — Reflow:**
> Recalculating layout. Very expensive! Triggered by: changing width/height, adding/removing elements, font size change.

---

### Section 6: Paint

Browser fills in actual **pixels** — colors, borders, shadows, text:

```
Layout
  ↓
Paint
  ↓
Pixels drawn on layers
```

**Key Term — Repaint:**
> Redrawing pixels without layout change. Less expensive than Reflow. Triggered by: color change, background change, visibility change.

---

### Section 7: Compositing — Final Step

Multiple **layers** are combined into the final screen image:

```
Layer 1 (background)
Layer 2 (content)
Layer 3 (fixed navbar)
Layer 4 (modal/overlay)
        ↓
GPU combines all layers
        ↓
Final screen image  ✅
```

> `transform` and `opacity` changes happen on **GPU layer** — that's why they're 60fps smooth (no reflow/repaint).

---

## Visual — Full Browser Pipeline

```
URL Typed
    │
    ▼
┌─────────────────┐
│   DNS Lookup    │  google.com → IP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TCP + TLS      │  Secure connection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │  GET /index.html
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTML Response  │  Raw HTML arrives
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────┐
│  DOM  │  │ CSSOM  │  Parsed in parallel
└───┬───┘  └───┬────┘
    └─────┬─────┘
          ▼
   ┌─────────────┐
   │ Render Tree │  Visible elements only
   └──────┬──────┘
          ▼
   ┌─────────────┐
   │   Layout    │  Positions + sizes
   └──────┬──────┘
          ▼
   ┌─────────────┐
   │    Paint    │  Colors + pixels
   └──────┬──────┘
          ▼
   ┌─────────────┐
   │  Composite  │  GPU merges layers
   └──────┬──────┘
          ▼
      SCREEN ✅
```

---

## Real-World Examples

**Example 1 — Why `<script>` at bottom matters:**
```html
<!-- BAD: blocks HTML parsing -->
<head>
  <script src="big-file.js"></script>
</head>

<!-- GOOD: parse HTML first, run JS after -->
<body>
  ...content...
  <script src="big-file.js" defer></script>
</body>
```

**Example 2 — Why `transform` is faster than `top/left`:**
```css
/* SLOW: triggers Layout + Paint + Composite */
.box { top: 100px; }

/* FAST: only Composite (GPU) — no Layout, no Paint */
.box { transform: translateY(100px); }
```

**Example 3 — Critical Rendering Path optimization:**
```html
<!-- Inline critical CSS → no extra request → faster first paint -->
<style>
  body { margin: 0; font-family: sans-serif; }
  .hero { background: #000; color: #fff; }
</style>
```

---

## Key Points Summary

| Concept | One-Line Explanation |
|---|---|
| **DNS Lookup** | Converts domain name to IP address |
| **DOM** | HTML converted to a JavaScript-readable tree |
| **CSSOM** | CSS converted to a tree of computed styles |
| **Render Tree** | DOM + CSSOM merged, only visible elements |
| **Layout / Reflow** | Calculates position and size of every element |
| **Paint / Repaint** | Fills pixels with colors, borders, shadows |
| **Compositing** | GPU merges all layers into final screen image |
| **Critical Rendering Path** | Full journey from HTML to pixels |
| **Reflow** | Most expensive — avoid by batching DOM changes |
| **transform / opacity** | GPU-only — no reflow, no repaint, always smooth |

---

## Test Your Understanding

**Q1 (Basic):**
What is the difference between the **DOM** and the **Render Tree**? Why are they not the same?

**Q2 (Application):**
A developer changes the `width` of a `div` using JavaScript. Which steps re-run — Layout, Paint, Composite, or all three? Why?

**Q3 (Tricky):**
Why does `opacity: 0` and `display: none` both make an element invisible — but behave differently in the Render Tree and performance cost?

---

## Cheat Sheet

**Key Definitions:**
- **DNS:** Domain → IP address conversion
- **DOM:** Tree structure of HTML elements
- **CSSOM:** Tree structure of CSS styles
- **Render Tree:** DOM + CSSOM, visible elements only
- **Layout/Reflow:** Calculate exact size + position
- **Paint/Repaint:** Draw pixels (colors, borders)
- **Composite:** GPU merges layers → final screen
- **Critical Rendering Path:** URL → screen pipeline

**Browser Pipeline Order:**
```
DNS → TCP → TLS → HTTP Request → HTML
→ DOM + CSSOM → Render Tree
→ Layout → Paint → Composite → Screen
```

**Performance Rules:**
```
Reflow    = most expensive  (layout recalc)
Repaint   = medium cost     (pixel redraw)
Composite = cheapest        (GPU only)

✅ Use transform/opacity for animations
✅ Avoid reading offsetWidth inside loops
✅ Batch DOM changes
✅ Put <script> at bottom or use defer/async
✅ Inline critical CSS for faster first paint
```

**Common Mistakes to Avoid:**

| Mistake | Why Wrong | Fix |
|---|---|---|
| `<script>` in `<head>` without `defer` | Blocks HTML parsing | Use `defer` or move to bottom of `<body>` |
| Animating `top/left` | Triggers reflow every frame | Use `transform: translate()` instead |
| Reading `offsetWidth` inside a loop | Forces reflow on every iteration | Read once outside the loop |
| Too many inline styles via JS | Causes multiple reflows | Batch via CSS class toggle |
| Large unoptimized images | Delays rendering | Use WebP, lazy load, proper sizing |
| `display:none` vs `visibility:hidden` confusion | Different Render Tree behavior | `display:none` = removed from tree; `visibility:hidden` = stays in tree |

---

*Saved on: 2026-03-25 | Repo: Frontend System Design Learning Notes*
