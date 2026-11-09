# App and product copy

In-product copy has one job: help the person finish what they came to do. Story still matters (where am I, what's next, what do I get), but it's told in a sentence, not a page. Plainer than marketing, calmer under stress.

## Onboarding screens

**Shape:** a short Before → After → Bridge. Show the payoff, then get them to the first useful action fast.

| Element | Length | Rules |
|---|---|---|
| Title | 2-6 words | The outcome, not the feature |
| Body | 1-2 sentences, ≤ 120 characters | What they'll be able to do; one idea per screen |
| Primary button | 1-3 words | Moves forward: "Continue", "Add your first client" |
| Skip | 1-2 words | Always available, never guilt-tripping |

Rules:
- 3 screens or fewer before something useful happens. Better still, teach in context the first time each feature appears.
- Ask for information only when you use it, and say why: "Your time zone, so reminders arrive in working hours."
- Progress is honest: "Step 2 of 3".
- The last screen hands off to a real first action, not "Get started".

**Good**
> **Get paid without chasing**
> Send an invoice and we'll remind late payers for you.
> [Create your first invoice] · Skip

**Weak**
> **Welcome to InvoiceHub!**
> The all-in-one platform that empowers you to seamlessly manage your finances!
> [Next]

## Empty states

**Shape:** what this space is for → why it's empty → one action that fills it.

| Type | What to say | Example |
|---|---|---|
| First use | The value of this screen + first action | "Your invoices will show up here. Create one in about a minute." [Create invoice] |
| No results | What was searched, how to widen it | "No invoices match 'Acme'. Check the spelling or clear filters." [Clear filters] |
| All done | Celebrate briefly, suggest what's next | "All paid up. Nothing overdue." |
| No access | Why, and who can help | "Only admins can see billing. Ask [placeholder: admin name] for access." |
| Error-caused | Treat it as an error (below) | "We couldn't load your invoices." [Try again] |

Avoid: "Nothing here!", "No data", a sad illustration with no action.

## Error messages

**Shape:** what happened → why (if useful) → how to fix it. Lead with the fix when it's obvious.

Rules:
- Plain words; no codes in the main message (put them in a "Details" line for support).
- Never blame: "That password doesn't match" beats "You entered an invalid password".
- Be specific: "The file is 32 MB. The limit is 25 MB." not "Upload failed".
- Keep what the user typed. Put the message next to the field it's about.
- If it's our fault, say so and say what we're doing.
- No humor, no "Oops!", no exclamation marks.

| Situation | Weak | Better |
|---|---|---|
| Validation | "Invalid input." | "Enter a date in the future, like 12/05/2026." |
| Network | "Error 503." | "You're offline. We'll send it when you're back online." |
| Server | "Something went wrong!" | "We couldn't save your changes. Try again in a minute. [Try again]" |
| Payment | "Transaction failed." | "Your card was declined. Try another card or contact your bank." |
| Permission | "Access denied." | "You need edit access to change this. [Request access]" |
| Limit | "Quota exceeded." | "You've used all 20 invoices this month. Upgrade or wait until June 1." |
| Not found | "404." | "That invoice was deleted or moved. [Back to invoices]" |

## Permission pre-prompts (iOS / Android)

Show your own explanation **before** the system dialog, at the moment the feature needs it. The system dialog's purpose text (iOS usage-description strings, Android rationale) must also be clear; store reviewers read them.

**Shape:** what you'll do with it → the benefit to them → [Allow] / [Not now]

| Permission | Pre-prompt | Purpose string |
|---|---|---|
| Notifications | "Get a heads-up when a client pays? We'll only notify you about payments and overdue invoices." | "Notifications tell you when a client pays." |
| Camera | "Snap a receipt and we'll fill in the amount and date." | "The camera is used to scan receipts." |
| Location | "Show cafés near you? We use your location only while the app is open." | "Your location is used to show nearby places while you use the app." |
| Contacts | "Find teammates already on [App]? We don't store or message your contacts." | "Contacts are used to find people you know on [App]." |

Rules: ask in context, never on first launch for everything at once; say what you won't do; "Not now" must work and the app must still be usable; explain how to turn it on later if they decline.

## Push notifications

**Shape:** the news first → why it matters → (optional) action. Each push should be worth an interruption.

Approximate guidance (visible length varies by OS, device, language and settings; test on real devices):

| Part | Aim for | Notes |
|---|---|---|
| Title | ≤ 30-40 characters | Often bold; may be truncated around 40-50 |
| Body | ≤ 90-110 characters | Lock screens typically show 2-4 lines |
| Action buttons | 1-2 words | "Pay now", "Reply" |

**Good**
> **Acme paid $1,200**
> Invoice #1042 is settled. That's everything from March.

**Weak**
> **🚀🔥 Don't miss out!!**
> Exciting things are happening in your account! Tap to find out more!

Rules: no clickbait, no guilt ("You're losing your streak!" sparingly, if ever), respect quiet hours, personalize with real data, let people choose categories.

## In-app confirmations

### Success (toasts, snackbars)
Short past tense. Offer undo when you can.
> "Invoice sent to Acme." [Undo]
> "Saved."

### Destructive confirmations (dialogs)
**Shape:** Title as a question naming the object · consequence · buttons that repeat the verb.
> **Delete "Q3 report"?**
> This removes it for everyone on your team. You can't undo this.
> [Cancel] [Delete report]

Rules: name the specific thing; state who is affected and whether it's reversible; the destructive button says the action ("Delete report"), never "OK" or "Yes"; for high-impact actions, ask them to type the name. If the action is reversible, skip the dialog and offer undo instead.

## Paywalls and upgrades

Honest and clear. The reader should know what they get, what it costs and how to leave.

**Shape:** the outcome they unlock (in plain words) → 3-5 specific inclusions → price with period and total → trial terms → CTA → easy dismiss.

**Good**
> **Send unlimited invoices**
> - No monthly limit
> - Custom reminders and branding
> - Bank transfer payments
> $12/month, billed monthly. 14-day free trial; we'll remind you 3 days before it ends. Cancel any time in Settings.
> [Start free trial] · Not now

Never:
- Hide the close button or make it tiny or delayed.
- Use confirmshaming ("No thanks, I like losing money").
- Show only a weekly price for an annual plan without the total.
- Pre-select the most expensive plan without saying so.
- Use countdowns or "only today" offers that aren't real.

## App store listing

Character limits differ by store and change over time. **Check the current Apple App Store Connect and Google Play Console documentation before finalizing.** As a starting point (verify):

| Field | Apple App Store | Google Play |
|---|---|---|
| App name / title | ~30 | ~30 |
| Subtitle / short description | Subtitle ~30 | Short description ~80 |
| Promotional text | ~170 (editable without a release) | — |
| Description | ~4,000 | ~4,000 |
| Keywords | ~100 (comma-separated, hidden) | No keyword field; uses listing text |
| What's new / release notes | ~4,000 | ~500 |

**Structure for the description:**
1. **First 1-3 lines** (shown before "more"): who it's for and the main outcome. No awards you can't prove.
2. **How it helps:** 3-6 short benefit paragraphs or bullets, each starting with the result.
3. **Proof:** real ratings, press or numbers only, if provided.
4. **Details:** pricing model, subscription terms, privacy note, support contact.

**Good title + subtitle**
> Title: Ledgerly: Simple Invoices
> Subtitle: Send invoices, get paid faster

**Weak**
> Title: Ledgerly - #1 Best Invoice App
> Subtitle: The ultimate all-in-one finance solution

Avoid superlatives and rankings you can't prove; store review guidelines often prohibit them. Don't stuff keywords into the title.

## Release notes

Written for users, not the team. Lead with what they can now do.

**Shape per item:** what changed → why it matters to them → how to try it (optional).

**Good**
> **What's new**
> - Search invoices by amount. Type "450" and find it.
> - Reminders now skip weekends, so they don't land on Saturday morning.
> - Fixed: PDFs no longer cut off long addresses. Thanks to everyone who reported it.

**Weak**
> - Bug fixes and performance improvements.
> - Various enhancements to elevate your experience.

"Bug fixes and performance improvements" is fine for a release with nothing user-visible. If something is visible, name it. Credit users who reported issues (without naming them unless they agreed).
