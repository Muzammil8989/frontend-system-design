# Voice and tone

**Voice** is who you are. It stays the same everywhere. **Tone** is how that voice adjusts to the moment: a friend sounds different at a party and at a hospital, but they're still the same person.

## Defining the voice

1. Read the existing copy (site, app strings, support macros). Note 3 lines that sound right and 3 that don't.
2. Pick one primary archetype below, and at most one secondary.
3. Write a voice chart: **We are X, not Y** (three rows), plus one sample line per row.
4. Agree on 5-10 words the brand uses and 5-10 it never uses.

```text
We are confident, not cocky.      "Payroll in 10 minutes." (not "The world's best payroll")
We are plain, not plain-boring.   "Your money's on its way." (not "Transaction initiated")
We are warm, not gushing.         "Nice work. That's the last one." (not "Amazing!! 🎉🎉")
```

Machine-readable versions live in `data/voice-archetypes.csv` (id, name, keywords, description, do, dont, sample).

## Archetypes

### Friendly expert
Knows the subject cold and explains it like a good colleague.
- **Do:** explain the why in one line; use everyday examples; admit trade-offs.
- **Don't:** lecture, show off jargon, stack qualifiers.
- **Sample:** "Most teams lose an hour a week to status meetings. Here's how to get it back."
- **Fits:** SaaS, education, productivity tools.

### Calm professional
Steady and precise. Someone you'd trust with your money or data.
- **Do:** lead with facts; say what happens next and when; keep errors short and even.
- **Don't:** joke about money or data; hype; use exclamation marks.
- **Sample:** "Your transfer is on its way. It usually arrives within 1 business day."
- **Fits:** finance, legal, health, B2B, security.

### Playful
Light and quick. Humor is the garnish, never the meal.
- **Do:** use wit in low-stakes moments (empty states, 404, success); keep instructions plain.
- **Don't:** joke in errors, billing or anything that cost the user something; spam emoji; make puns that slow reading.
- **Sample:** "No plans yet. Your calendar is suspiciously free."
- **Fits:** consumer apps, games, food, social.

### Bold challenger
Names the old way and says why it's broken. Confident, with receipts.
- **Do:** name the status quo; take a clear position; back claims with specifics.
- **Don't:** insult competitors by name; make claims you can't prove; shout every line.
- **Sample:** "Spreadsheets weren't built for payroll. We were."
- **Fits:** startups entering a crowded market.

### Warm caregiver
Kind and patient. Puts the reader's feelings first without being syrupy.
- **Do:** acknowledge feelings; offer one small next step; offer a human.
- **Don't:** promise outcomes you can't control; guilt; use clinical jargon.
- **Sample:** "Missed a few days? That's okay. Pick up where you left off."
- **Fits:** health, wellness, parenting, nonprofits, support.

### Precise technical
Exact and terse. Respects the reader's expertise and time.
- **Do:** exact names, numbers, versions and limits; show the command.
- **Don't:** marketing adjectives; "easy" or "simple"; hiding limits.
- **Sample:** "Deploys take about 40 seconds. Rollback is one command: `deploy rollback`."
- **Fits:** developer tools, APIs, infrastructure, data.

### Plainspoken maker
Sounds like the founder talking. Practical, specific, a bit personal.
- **Do:** first person when true; real places, tools, materials; short true stories.
- **Don't:** pretend to be bigger than you are; invent history; corporate words.
- **Sample:** "We started this in a garage in Leeds because our own bikes kept getting stolen." *(only if true)*
- **Fits:** small businesses, indie products, craft, local services.

### Refined minimal
Few words, chosen carefully. Confidence through restraint.
- **Do:** short lines; name materials and details; let one fact carry the line.
- **Don't:** stack superlatives; over-explain; discount language; exclamation marks.
- **Sample:** "Merino from one farm. Knitted to last ten winters."
- **Fits:** premium, fashion, hospitality, design.

## Tone by context

Same voice, different volume. The more the moment costs the user (money, data, time, stress), the plainer and calmer the copy.

| Context | User's state | Tone | Humor? | Example |
|---|---|---|---|---|
| Marketing / hero | Curious, skeptical | Confident, specific | Light, if on-brand | "Get paid in days, not months." |
| Onboarding | Hopeful, impatient | Encouraging, brief | Light | "Two steps left. Then you're sending invoices." |
| Success | Pleased | Warm, short; don't overdo it | Yes, small | "Sent. Nice work." |
| Empty state | Unsure what to do | Helpful, inviting | Light | "No invoices yet. Create one in about a minute." |
| Error (user can fix) | Annoyed | Calm, direct, blame-free | No | "That card was declined. Try another or check with your bank." |
| Error (our fault) | Frustrated | Own it, plain, give a timeline | No | "We couldn't save your changes. We're on it; try again in a minute." |
| Destructive confirmation | Cautious | Serious, exact | No | "Delete 'Q3 report'? This removes it for everyone and can't be undone." |
| Billing / payments | Wary | Precise, transparent | No | "You'll be charged $12 on May 3. Cancel any time before then." |
| Security / privacy | Worried | Calm, factual, reassuring with specifics | No | "Someone signed in from a new device in Lisbon. Not you? Secure your account." |
| Waiting / loading | Impatient | Honest about time | Maybe | "Importing 2,400 contacts. About 1 minute." |
| Cancellation / offboarding | Decided | Respectful, no guilt | No | "Your plan ends on June 1. Your files stay available until then." |
| Release notes | Interested | Friendly, concrete | Light | "Search now finds invoices by amount. Try '450'." |

## Tone dials

When a brief says "more friendly" or "more serious", adjust these instead of adding adjectives:

| Dial | Warmer / lighter | Cooler / more serious |
|---|---|---|
| Person | "you", "we", first names | Fewer pronouns, more nouns |
| Sentence length | Short, varied, fragments allowed | Complete sentences, even length |
| Contractions | Always | Fewer (keep "don't" for readability) |
| Humor | Small, situational | None |
| Punctuation | Occasional dash or question | Periods |
| Specificity | Same. Never trade specifics for tone. | Same |
