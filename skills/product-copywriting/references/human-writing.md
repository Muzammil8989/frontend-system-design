# Human writing

Copy sounds machine-made when it is vague, symmetrical and pleased with itself. It sounds human when it is specific, a little uneven and focused on the reader. Use these rules to edit, then run `scripts/copy_check.py`.

## The rules

### 1. Concrete nouns and real numbers
Swap abstractions for things you could photograph or count.
- Weak: "Improve your productivity with powerful features."
- Better: "Close your laptop at 5. The reports already went out."
Only use numbers the user gave you. Otherwise write `[placeholder: time saved per week]`.

### 2. Active voice, named actors
Say who does what. Passive voice hides the actor and adds words.
- Weak: "Your data is encrypted and backups are performed daily."
- Better: "We encrypt your data and back it up every night."
Passive is fine when the actor doesn't matter ("Your order was delivered").

### 3. Contractions
People say "you'll", "don't", "it's". Copy without contractions sounds like a contract. Exception: a firm warning ("Do not unplug the device") or a very formal brand.

### 4. Rhythm: vary sentence length
Machine copy marches: every sentence 14-18 words, same shape. Mix it up. Write a long sentence that carries the reader through a full thought, with a turn in the middle. Then stop. Short lines land the point.

### 5. Reading level
Marketing: grade 6-9. UI: lower. This isn't dumbing down; experts read plain copy faster too. Short words, short sentences, one idea each.

### 6. Cut filler and hedges
"Very", "really", "basically", "in order to", "it's worth noting". Cut them and the sentence usually gets stronger. Hedges ("may potentially", "to some extent") make the reader doubt you. Commit, or say exactly when it applies.

### 7. Show, don't tell
Don't say "easy". Show that it's easy: "Three steps. About two minutes."
Don't say "we care about privacy". Show it: "We don't sell your data. We don't show ads. Delete your account and everything goes within 30 days."

### 8. Write to one person
Picture one reader and talk to them. Use "you". Avoid "users", "customers", "individuals" in copy they will read. Avoid writing to everyone at once ("Whether you're a startup or an enterprise...").

### 9. Avoid symmetrical triads and over-parallel structure
"Fast, simple, and secure." "Plan. Track. Grow." One triad is fine. Three on a page reads as a template. Use two items, or one strong one with a detail. Also watch paragraphs where every sentence starts the same way or has the same length.

### 10. Go easy on em-dashes
One per page is plenty. Most can be a period, comma or parentheses. Stacked dashes are one of the most recognizable machine tells.

### 11. Skip "not X, but Y" and "it's not just X, it's Y"
"It's not just a calendar, it's a way of life." This contrast trick is overused and usually inflates a small claim. Say what it is.

### 12. No emoji spam
Emoji as bullets, emoji after every heading, rockets and sparkles: all read as generated. Keep emoji for channels where people use them (some push notifications, social) and use one at most, only when it adds meaning.

### 13. No fake urgency or hype
"Act now", "limited time", countdown timers that reset, "only 2 left" when it isn't true. They cost trust and, in many regions, break consumer law. State real deadlines plainly.

### 14. Earn every adjective
If an adjective could describe any competitor ("powerful", "intuitive", "robust"), cut it or replace it with the detail that proves it.

### 15. Read it out loud
If you'd never say it to a friend across a table, rewrite it. If you run out of breath, split the sentence.

## AI tells → human rewrite

The checker's full list lives in `data/ai-tells.csv`. These are the most common.

| AI tell | Why it fails | Human rewrite |
|---|---|---|
| delve / delve into | Nobody says it out loud | "look at", "cover", or just start |
| in today's fast-paced world | Empty throat-clearing | Start with the reader's problem |
| in the digital age | Says nothing | Cut it |
| unlock | Vague promise | Name the thing they can now do |
| unleash | Hype | Say what changes, with a number if you have one |
| elevate | Vague | "faster", "fewer steps", "looks sharper" |
| seamless / seamlessly | Claimed by everyone | Name the step that disappears |
| robust | Generic | Say what it survives: "works offline", "10,000 rows" |
| cutting-edge / state-of-the-art | Label, not proof | Name the technique or show the result |
| game-changer | Self-praise | Show the before and after |
| revolutionize | Overclaim | Say the one thing that changes |
| empower | Corporate | "help", "let", or the actual action |
| leverage | Jargon | "use" |
| harness the power of | Filler metaphor | Start with the verb that matters |
| supercharge / turbocharge | Hype | Give the real speed-up |
| tapestry | Purple prose | Say what is mixed together |
| a testament to | Purple prose | State the evidence |
| embark on | Inflated | "start" |
| journey | Vague | "first week", "setup", or name the steps |
| realm | Inflated | "area", "field" |
| landscape | Abstract | Name the market or situation |
| navigate the complexities of | Abstract | Say what's hard and how you help |
| it's important to note | Hedge | Cut it; state the fact |
| it's worth noting | Hedge | Cut it; state the fact |
| furthermore / moreover | Essay voice | "also", "and", or a new sentence |
| additionally | Essay voice | "also" |
| in conclusion / in summary | Essay voice | End on the point itself |
| whether you're X or Y | Writes to nobody | Pick one reader |
| look no further | Cliché | Say why this fits their case |
| take X to the next level | Vague | Say what "next level" means, in numbers |
| effortless / effortlessly | Unprovable | "two taps", "about a minute" |
| ever-evolving | Filler | Say what changed and when |
| a myriad of / a plethora of | Inflated | "many", or the number |
| boasts | Brochure voice | "has", "includes" |
| dive into / deep dive | Cliché | "look at", "detailed guide" |
| stands as | Inflated | "is" |
| plays a crucial role | Filler | Say what it does |
| pivotal | Inflated | Show why it matters |
| foster / bolster | Corporate | "build", "grow", "support" |
| meticulously crafted | Unprovable | Name the detail you got right |
| tailored to your needs | Cliché | Say what adapts and how |
| one-stop shop | Cliché | List the 2-3 tools they no longer need |
| like never before | Hype | Say what is new |
| we've got you covered | Cliché | Say what's covered |
| say goodbye to | Cliché | Name the problem and its replacement |
| at your fingertips | Cliché | "on your phone", "one tap away" |
| peace of mind | Abstract | Name the worry that goes away |
| hassle-free | Abstract | Name the hassle that's gone |
| imagine a world where | Template opener | Describe the reader's real day |
| it's not just X, it's Y | Contrast trick | Say what it is |
| actionable insights | Jargon | "what to fix next" |
| best-in-class / world-class | Unsupported | Back it with a source, or describe the result |
| ready to get started? | Generic CTA lead-in | A CTA that says what happens: "Send your first invoice" |

## Self-edit checklist

Run through this before you hand copy over.

- [ ] Could a competitor paste this headline on their site unchanged? If yes, rewrite it.
- [ ] Is the reader the subject of most sentences? Count "you" vs "we".
- [ ] Every claim has proof the user provided, or a `[placeholder: …]`.
- [ ] No invented names, numbers, quotes, logos or awards.
- [ ] Each sentence holds one idea. Nothing over 30 words; most under 20.
- [ ] Sentence lengths vary. At least one short line per section.
- [ ] No more than one triad and one em-dash on the page.
- [ ] No words from the AI-tells table (or a reason to keep each one).
- [ ] Buttons say what happens next (verb + object).
- [ ] Reading grade within target (`copy_check.py` reports it).
- [ ] Read aloud once. Fix every place you stumbled.
- [ ] `copy_check.py` score ≥ 80 and no high-severity flags.
