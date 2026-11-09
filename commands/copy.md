---
description: Write or rewrite human-sounding, story-driven copy for a website page or app screen
argument-hint: "<page or screen, e.g. 'landing page', 'about page', 'onboarding', 'empty states', 'app store listing'>"
---

Write the copy for: **$ARGUMENTS**

Use the `product-copywriting` skill.

1. **Gather context:**
   - read the existing page or screen if there is one;
   - read the README and the product description;
   - read the design doc at `docs/frontend-system-design.md` if it exists;
   - read any brand or voice notes.

   Write a 5-line brief covering the audience, the problem, the transformation, the proof available, and the voice. Ask at most 3 questions, and only if the story depends on the answers.
2. **Write.** Delegate to the **copywriter** subagent with the brief. If subagents are unavailable, follow the skill yourself.
3. **Check.** The final copy must pass `scripts/copy_check.py` with a score of at least 80 and no high-severity flags. Show the score.
4. **Present:**
   - labelled copy blocks;
   - 2–3 headline alternatives;
   - a list of every `[placeholder: …]` that needs real proof from the user.

   Offer to apply the copy to the actual files. Don't edit them before the user says yes.
