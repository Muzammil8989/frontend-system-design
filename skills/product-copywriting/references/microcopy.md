# Microcopy

The small words in an interface: buttons, labels, hints, tooltips, status lines. People don't read them; they scan them while doing something else. Make each one obvious at a glance.

## Buttons

**Rule: verb + object.** The button says what happens when you press it.

| Weak | Better | Why |
|---|---|---|
| Submit | Send invoice | Names the result |
| OK | Delete project | Confirms the exact action |
| Yes / No | Keep editing / Discard changes | Readable without the question |
| Click here | Download the report | Works out of context (screen readers list links) |
| Get started | Create your first invoice | Says what "start" means |
| Learn more | See pricing | Tells them where they're going |

- Sentence case ("Send invoice"), unless the design system says otherwise.
- 1-4 words. If it needs more, the screen needs a clearer heading.
- The primary button and the page title should use the same verb ("Create invoice" → "Create").
- Keep the label stable while loading ("Sending…"), then confirm ("Sent").
- Pairs: put the safe option where the platform expects it; don't swap colors to trick people into the riskier choice.

## Forms

### Labels
- Always visible, above the field. Placeholders are not labels (they vanish and often fail contrast).
- Short nouns: "Email", "Company name". Not "Please enter your email address".
- Mark optional fields "(optional)" instead of starring required ones, when most fields are required.

### Hints
- Explain format or reason before they type: "We'll send the receipt here." "At least 8 characters."
- Put hints below the label, linked to the field (`aria-describedby`).

### Validation
- Validate on blur or submit, not on every keystroke.
- Say what's wrong and how to fix it, in the reader's terms:

| Weak | Better |
|---|---|
| Invalid email | Enter an email like name@example.com |
| Field required | Enter your company name |
| Password does not meet requirements | Add a number. Passwords need at least one. |
| Invalid date | Choose a date after today |
| Error | That card number is too short. Check the last 4 digits. |

- On submit, summarize errors at the top with links to each field, and move focus there.
- Keep what they typed. Never clear a form because of one error.

## Destructive actions

- Name the object and the consequence: "Delete 3 invoices? Clients won't be notified. You can't undo this."
- The confirm button repeats the verb: "Delete invoices".
- Prefer **undo** over confirmation for reversible actions ("Archived. [Undo]").
- For irreversible, high-impact actions, require typing the name or a clear checkbox.
- Use "delete" for gone forever, "remove" for taken out of a list but still existing, "archive" for hidden but recoverable. Be consistent.

## Loading and progress

| Wait | What to show | Example |
|---|---|---|
| < 1 s | Nothing, or a subtle spinner | — |
| 1-3 s | Spinner + verb | "Saving…" |
| 3-10 s | What's happening | "Checking your bank details…" |
| > 10 s | Progress + estimate + can they leave? | "Importing 2,400 contacts. About 1 minute. You can close this page." |

- Use the ellipsis character (…) and present participles: "Uploading…", "Sending…".
- Honest estimates. If unsure, say what you know: "This can take a few minutes for large files."
- Rotating "fun" loading messages are fine for playful brands, but the real status must still be clear.

## Tooltips

- For extra detail, never essential information (touch screens and many users never see them).
- One or two sentences, ≤ 150 characters.
- Don't repeat the label. "Due date: The date the client should pay by" adds nothing. "Due date: Reminders start the day after this" helps.
- Must work on keyboard focus, not just hover, and be dismissible.

## Inclusive and plain language

- Plain words: "use" not "utilize", "start" not "initiate", "help" not "facilitate", "buy" not "purchase" (unless the brand is formal).
- Address people directly ("you"); avoid "the user" in copy users read.
- Gender-neutral: "they", "everyone", "team"; avoid "guys", "manpower", "chairman".
- Avoid ableist idioms: "sanity check" → "quick check", "blind spot" → "gap", "crippled" → "slowed down".
- Avoid culture-bound idioms and sports metaphors ("home run", "touch base"); they confuse non-native readers and translate badly.
- Don't assume names (first/last), addresses or genders fit one format. Label fields "Full name" when you can.
- Ages, abilities, families: describe situations, not identities, unless relevant.

## i18n-friendly writing

- **Never concatenate fragments.** `"You have " + n + " invoices"` breaks in languages with different word order and plurals. Use full strings with variables and plural rules (ICU MessageFormat or the platform's plural resources):
  `{count, plural, one {You have # invoice} other {You have # invoices}}`
- **Leave room for expansion.** Translations often run 30-40% longer than English, and much more for very short strings. Don't design buttons that only fit English.
- One string per sentence; avoid splitting a sentence around a link or bold word. Use placeholders for embedded links: `"Read our {link}privacy policy{/link}."`
- Avoid idioms, puns, slang and wordplay in UI strings. Keep humor in places that can be rewritten per locale.
- Don't build strings from adjectives ("new" + item name); gender and case vary by language.
- Write dates, numbers, currency and units through locale formatting, not in copy ("May 3" vs "3 May").
- Add translator notes for ambiguous words: "Post (verb: publish a message)".
- Keep keys stable and descriptive: `invoice.empty.title`, not `text_17`.

## Accessibility wording

### Link text
- Meaningful out of context: "Read the pricing FAQ", not "Click here" or "Read more".
- If several links say "Read more", give each a unique accessible name ("Read more about invoices").
- Say when a link opens a new tab or downloads a file: "Download report (PDF, 2 MB)".

### Alt text
- Describe the purpose, not the pixels: for a chart, give the takeaway ("Revenue doubled from March to May").
- Decorative images: empty alt (`alt=""`), not "image" or the file name.
- Skip "image of" / "picture of". Screen readers already announce it as an image.
- Keep it to about one or two sentences; put long descriptions in the page or a linked description.
- Product photos: include what a buyer needs (color, material, what's shown).

### aria-label and accessible names
- Icon-only buttons need a name that matches the action: `aria-label="Delete invoice 1042"`, not `"trash"` or `"button"`.
- If there's visible text, the accessible name should start with it (helps voice control users say what they see).
- Don't add `aria-label` that repeats or contradicts visible text.
- Status updates ("Saved", "3 results") go in a live region so screen readers hear them.

### General
- Don't rely on color or position alone: "Fields in red are required" → "Required fields are marked (required)". "Click the button on the right" → "Select Continue".
- Expand abbreviations on first use.
- Error messages are announced; keep them short and specific.
