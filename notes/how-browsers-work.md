# How Browsers Work

> **Date:** 2026-03-25
> **Category:** Frontend System Design
> **Sub-Topic:** Browser Internals / Rendering

---

## ELI5 — Simple Explanation

Imagine you order food at a restaurant:
- You give your **order** (URL) to the waiter (browser)
- Waiter goes to the **kitchen** (server) and fetches food (HTML/CSS/JS)
- Kitchen **prepares and plates** it (parses + builds render tree)
- You **see the final dish** on your table (pixels on screen)

> **Browser = Messenger + Chef + Painter**
> It fetches, processes, and paints everything you see.

---

## Core Concept — Step by Step

### Section 1: Networking — URL to HTML

```
You type: https://google.com
         ↓
Step 1 → DNS Lookup
         "google.com" → IP address (142.250.80.46)
         (like a phone book — domain to IP)
         ↓
Step 2 → TCP 3-Way Handshake
         Client: SYN  →  Server: SYN-ACK  →  Client: ACK
         (knocking on a door and waiting for "come in")
         ↓
Step 3 → TLS Handshake  (HTTPS only)
         Encrypted secure tunnel established
         ↓
Step 4 → HTTP GET Request sent
         GET / HTTP/1.1
         Host: google.com
         ↓
Step 5 → Server responds with HTML file
```

| Term | Simple Meaning |
|---|---|
| **DNS** | Phone book — converts domain to IP |
| **TCP Handshake** | Confirm connection before sending data |
| **TLS** | Locks the conversation so no one can spy |
| **HTTP GET** | Browser asks server: "please send me this page" |

---

### Section 2: HTML Parsing → DOM Tree

Once HTML arrives, browser starts **parsing** (reading line by line):

```
Raw HTML string
      ↓
  Tokenizer
  (breaks HTML into tokens: <html>, <body>, "Hello", </body>…)
      ↓
   DOM Tree
  (tree of JavaScript objects)
```

**What is the DOM?**
> DOM = HTML converted into a **tree of objects** that JavaScript can read and modify.

```
HTML:                     DOM Tree:
<html>                    Document
  <body>                  └── html
    <h1>Hello</h1>             └── body
    <p>World</p>                    ├── h1 → "Hello"
  </body>                          └── p  → "World"
</html>
```

**Important rule:** When parser hits `<script>` tag → it **STOPS** building the DOM until the script downloads and runs. (This is a separate topic — see Critical Rendering Path note.)

---

### Section 3: CSS Parsing → CSSOM Tree

While DOM is being built, browser also parses CSS into **CSSOM** (CSS Object Model):

```
Raw CSS string
      ↓
  CSSOM Tree
  (every element gets computed styles)
```

```
CSS:                      CSSOM:
body { font-size: 16px }  body → font-size: 16px
h1   { color: red }            └── h1 → color: red (inherits 16px)
p    { margin: 8px }           └── p  → margin: 8px (inherits 16px)
```

**Key rule:** CSS styles **cascade** — child elements inherit from parents.

---

### Section 4: Render Tree = DOM + CSSOM

Browser combines DOM and CSSOM into a **Render Tree**:

```
  DOM Tree    +    CSSOM Tree
       ↓
   Render Tree
   (only VISIBLE elements with their styles)
```

**Important difference — DOM vs Render Tree:**

| | DOM Tree | Render Tree |
|---|---|---|
| `display: none` | ✅ included | ❌ excluded (not rendered) |
| `visibility: hidden` | ✅ included | ✅ included (takes space, invisible) |
| `<head>`, `<script>`, `<meta>` | ✅ included | ❌ excluded (not visual) |

> **Rule:** DOM = everything in HTML. Render Tree = only what the user can see.

---

### Section 5: Layout (Reflow)

Browser calculates **exact position and size** of every element in the Render Tree:

```
Render Tree
     ↓
  Layout Engine
     ↓
  Box Model for each element:
  ┌─────────────────────┐
  │       margin        │
  │  ┌───────────────┐  │
  │  │    border     │  │
  │  │  ┌─────────┐  │  │
  │  │  │ padding │  │  │
  │  │  │ CONTENT │  │  │
  │  │  └─────────┘  │  │
  │  └───────────────┘  │
  └─────────────────────┘
  x, y position on screen calculated
```

**Reflow** = recalculating layout. Triggered by:
- Changing `width`, `height`, `font-size`
- Adding or removing elements from DOM
- Resizing the browser window

> **Reflow is the most expensive browser operation.** Avoid triggering it unnecessarily.

---

### Section 6: Paint (Repaint)

Browser fills in actual **pixels** for each element:

```
Layout
  ↓
Paint
  ↓
Pixels drawn: colors, borders, shadows, text, images
```

**Repaint** = redrawing pixels without layout change. Triggered by:
- Color change
- Background change
- `visibility: hidden/visible` toggle

> **Repaint is less expensive than Reflow** — no position recalculation needed.

---

### Section 7: Compositing — Final Screen

Browser has multiple **layers**. GPU combines them into the final image:

```
Layer 1: background
Layer 2: main content
Layer 3: fixed navbar
Layer 4: modal/popup
      ↓
  GPU composites all layers
      ↓
  Final screen ✅
```

**Why `transform` and `opacity` are special:**
> They only affect the **Composite** step — GPU handles them directly.
> No Layout recalc, no Paint — that's why they're smooth at 60fps.

```css
/* Triggers Layout + Paint + Composite (slow) */
.box { left: 100px; }

/* Triggers Composite ONLY (fast, GPU) */
.box { transform: translateX(100px); }
```

---

## Full Visual Pipeline

```
[ URL TYPED ]
      │
      ▼
┌─────────────┐
│  DNS Lookup │  google.com → 142.250.80.46
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ TCP + TLS   │  Secure connection established
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ HTTP Request│  GET /index.html
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ HTML arrives│  Raw bytes → characters → tokens
└──────┬──────┘
       │
  ┌────┴────┐
  ▼         ▼
┌─────┐  ┌───────┐
│ DOM │  │ CSSOM │   Built in parallel
└──┬──┘  └───┬───┘
   └────┬────┘
        ▼
  ┌───────────┐
  │Render Tree│   Only visible elements
  └─────┬─────┘
        ▼
  ┌───────────┐
  │  Layout   │   Exact position + size
  └─────┬─────┘
        ▼
  ┌───────────┐
  │   Paint   │   Colors + pixels
  └─────┬─────┘
        ▼
  ┌───────────┐
  │ Composite │   GPU merges layers
  └─────┬─────┘
        ▼
  [ SCREEN ✅ ]
```

---

## Real-World Examples

**Example 1 — DOM vs Render Tree:**
```html
<div style="display: none">Hidden</div>  <!-- in DOM, NOT in Render Tree -->
<div style="visibility: hidden">Ghost</div> <!-- in DOM AND Render Tree (takes space) -->
<div>Visible</div>  <!-- in both -->
```

**Example 2 — Reflow trigger:**
```javascript
// BAD: reads layout property inside loop → forces reflow every iteration
for (let i = 0; i < 100; i++) {
  el.style.width = el.offsetWidth + 10 + 'px';  // reflow × 100!
}

// GOOD: read once outside loop
const width = el.offsetWidth;
for (let i = 0; i < 100; i++) {
  el.style.width = width + 10 + 'px';  // reflow × 1
}
```

**Example 3 — Composite-only animation:**
```css
/* GPU-only, no reflow, no repaint → buttery smooth */
@keyframes slide {
  from { transform: translateX(0); }
  to   { transform: translateX(200px); }
}
```

---

## Key Points Summary

| Concept | One-Line Explanation |
|---|---|
| **DNS** | Domain name → IP address |
| **TCP Handshake** | 3-step connection confirmation |
| **DOM** | HTML parsed into a JavaScript-readable tree |
| **CSSOM** | CSS parsed into a styles tree |
| **Render Tree** | DOM + CSSOM — only visible elements |
| **Layout / Reflow** | Calculate exact size and position of every element |
| **Paint / Repaint** | Fill in pixels — colors, borders, text |
| **Composite** | GPU merges all layers → final screen |
| **display:none** | Removed from Render Tree entirely |
| **visibility:hidden** | In Render Tree but invisible (still takes space) |
| **transform/opacity** | Composite-only — fastest, GPU-handled |

---

## Test Your Understanding

**Q1 (Basic):**
What is the difference between the DOM and the Render Tree?
Give one example of an element that exists in DOM but NOT in Render Tree.

**Q2 (Application):**
A developer changes `width` of a `div` via JavaScript.
Which steps re-run: Layout, Paint, Composite — or all three? Why?

**Q3 (Tricky):**
`opacity: 0` and `display: none` both make elements invisible.
How do they differ in the Render Tree and in performance cost?

---

## Cheat Sheet

**Key Definitions:**
- **DNS:** Domain → IP address lookup
- **TCP Handshake:** 3-step connection setup (SYN → SYN-ACK → ACK)
- **DOM:** HTML → JavaScript tree of objects
- **CSSOM:** CSS → tree of computed styles
- **Render Tree:** DOM + CSSOM, visible elements only
- **Layout/Reflow:** Calculate position + size (most expensive)
- **Paint/Repaint:** Draw pixels — colors, borders (medium cost)
- **Composite:** GPU merges layers → screen (cheapest)

**Pipeline Order:**
```
DNS → TCP → TLS → HTTP → HTML
→ DOM + CSSOM (parallel)
→ Render Tree
→ Layout → Paint → Composite
→ Screen
```

**Cost Comparison:**
```
Reflow    = 💀 most expensive  → avoid in loops
Repaint   = ⚠️  medium cost    → minimize
Composite = ✅ cheapest        → prefer (transform, opacity)
```

**Common Mistakes to Avoid:**

| Mistake | Why Wrong | Fix |
|---|---|---|
| Reading `offsetWidth` in a loop | Forces reflow every iteration | Read once before the loop |
| Animating `top` / `left` | Triggers reflow + repaint every frame | Use `transform: translate()` |
| Confusing `display:none` vs `visibility:hidden` | Different Render Tree + cost behavior | `display:none` = out of tree; `visibility:hidden` = in tree |
| Changing many styles one by one | Multiple reflows | Batch via CSS class toggle |
| Large unoptimized images | Slow download, blocks paint | Use WebP, correct sizing |

---

> **Next Topic:** [Critical Rendering Path](./critical-rendering-path.md)
> — How to optimize the pipeline for faster page loads

*Saved on: 2026-03-25 | Repo: Frontend System Design Learning Notes*
