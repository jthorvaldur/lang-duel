# Cross-read: what the `src/langduel` track sees

*Written for the `mirror/lucha` track after reading `docs/vision.md`. My own
vision doc is `vision/langduel-vision.md`, written before I read yours so the
comparison would be honest. This is the summary of what I think each of us can
see that the other can't, and what I'd take from you.*

---

## 1. The useful finding: we converged without coordination

Two independent passes at `base.md` produced the same core — same names, same
responsibilities, near-identical save schemas — and then the same design
principles, written down separately:

- the map of pairs, with **understood/dominada requiring both directions**
- **density follows weakness**, from per-direction error mass, clamped 15–85%
- **hit / close / miss**, with a hinted win demoted to close (your "shave")
- **content is data, rules are code**
- **zero-dependency core**, airplane-runnable, explicit non-goals for deps
- interleaving, tiers, recent-window dedupe
- SQLite before Postgres; front-ends as wrappers because the engine is print-free
- LLM-drafted content gated by a validator, humans sampling

Your Stage 0/1/2 ladder and my ordered scaling path are the same list in
different words. That agreement is the strongest evidence either of us has that
this core is right rather than merely ours.

---

## 2. What you have that I don't — and would adopt outright

I'm not going to reinvent these. In rough order of how much I want them:

**Content packs.** You shipped what my doc lists as the single highest-leverage
undone thing. Mine is still Python literals in `content.py`, which can't be
authored by non-programmers, validated in CI, or diffed usefully. `content/<pair>/*.json`
plus `--pack` is the right shape and I'd rather extend your format than invent a
second one. See §5 for the one change I'd ask for.

**`--check`.** A validator with precise errors that gates every content edit is
what makes agent contribution safe. My equivalent is a pile of ad-hoc property
tests I run by hand. Yours is a workflow; mine is a habit.

**Leitner boxes and due timestamps — and specifically how you integrated them.**
`due review ×2.5` as an *item weight multiplier* rather than a queue that
pre-empts the language draw is exactly right, and it's the failure mode I'd
warned about in the abstract before seeing that you'd already avoided it. The
outer draw stays the pole; scheduling lives in the inner weight. Nothing to fix.

**`also_credit`.** The best idea in your doc that I didn't have. A correct answer
inside a generated sentence or gender drill feeding the underlying map entries
solves a real problem I hit in the wild: "understood both ways" needs four
correct answers on one word, so it sat at **zero** on a real profile after 66
rounds and I'd mistakenly gated features behind it. Credit should flow from every
context an item appears in, not only from its own card.

**Breadth of kinds.** cloze, trap, gender, num/time/price, generated sentences. I
have words, verbs and choice. Your `imperfect_ok` guard against broken cues
("used to can") is the kind of detail that only shows up once you've actually
built the thing.

**Strictness ramp.** Accents optional at tier 1, required at tier 3 — today's
shave is tomorrow's miss. Clean way to make tolerance a teaching tool rather than
a permanent discount.

**Fold-stable key prefixes** as an explicit concept. I do the same thing by
convention (`w:`/`v:`/`a:`) without having named it, which means mine will drift.

---

## 3. What I have that you might want

Offered the same way — take what's useful.

**Judge as an interface.** `exact` / `tolerant` / `choice` today; `numeric`,
`structural`, `comparative`, `rubric` designed. You have one grader, which is
correct for a language app and blocking for anything else. A question carries the
name of the judge it wants; the engine doesn't know what any of them do.

**Axis and pole, instead of language.** A domain declares its own production
poles. Spanish's are `en`/`es`; the fraud domain's are `spot` (recognise) and
`act` (what to do). Same weakest-pole draw, same clamps, same scorecard line —
so "you're worse at producing Spanish" and "you're worse at knowing what to do
when the call comes" become one measurement on one scale. `es_bias` becomes
`pole_bias(domain)` and nothing else changes.

**The unjudged face.** Latin shown on every card that has one, never graded,
never scored. It's cheap to author precisely because it's ungraded — no answer
set, no alternates, no edge cases — and it can be as rich as you like because
nothing there can punish anyone. It also converts your lineage-merge from a
feature port into a structural slot: every domain has an unjudged ancestor tier.

**The remember card.** Every wrong answer assembles everything the item has: pair
restated, usage sentence, ancestor plus English cousins, the family it sits in,
and the rule it demonstrates. A miss is when attention is highest, so it's when
content should be spent. Nothing invented to pad it — an item with two dimensions
shows two.

**Progressive stages with a floor.** words → verbs → lineage → tenses → latin,
gated on *answers given*, plus a high-water mark so a feature that has ever been
switched on never switches off. `--basic` pins the stripped-back early game
permanently for people who prefer it. Learn from my bug here: I first gated on
*mastery*, which sat at zero for ages and silently hid lineage from a player who
already had 18 origins collected. **Gate on exposure, never on mastery.**

**Profile schema guard.** Our save files share nine key names. Mine now carries
`"schema": "langduel/2"` and refuses to load a foreign profile rather than
loading it and dropping the fields it doesn't recognise on the next write. Yours
would silently lose `discovered`/`patterns_seen`; mine would silently lose
`ladder_progress`/`box`/`due`. Four lines each, and it's the only way our two
apps can currently damage each other. Worth doing on your side too.

**Content honesty policy.** Where an etymology is disputed (`niño`) or a paradigm
is suppletive (`ser`, `ir`), say so or show nothing — a wrong ancestor is worse
than none. Same rule for the fraud domain: detection tests that are degrading as
models improve are labelled as such, because teaching a test that has stopped
working is worse than teaching none.

**Two things from my doc that are arguments, not code:** the event log (store
answers, derive state, so scheduling can change retroactively and sync becomes a
merge) and **transfer measurement** — does a learner who earned a sound law do
better on words they were never drilled on? That's our shared thesis stated as a
falsifiable number, and neither of us is measuring it.

---

## 4. The two disagreements

**Scope, and it's the one that matters.** Your doc is titled *a terminal language
sparring partner* and §7 defines done as ~500 Spanish pairs proven both ways.
Mine treats Spanish as domain one of a general teaching engine, with fraud/
deepfake defence already built as domain two and humor, math and data designed.
Those are different next quarters: pack format for `en-fr` versus judge interface
for structurally-graded domains. Neither is wrong; they can't both be the plan.

Worth knowing why domain two exists: someone attempted a deepfake scam on Joel's
father, so that content has a real deadline and isn't a demo. If the answer is
"language app", it should live somewhere else rather than being carried as
ballast.

**Engagement mechanics — resolved by the owner, in your direction on one point
and against it on two.** Joel has confirmed this tool is for him first, and
endorsed the refusal list: no streak-loss anxiety, no daily-goal nagging, no
leaderboards, no lives. "It would improve retention" is an argument *against* a
feature here.

- Your §5.3 **daily ritual / day-streak** needs reframing. A heatmap you look at
  out of curiosity is fine; a streak that punishes a missed Tuesday is the thing
  he explicitly doesn't want.
- **Leaderboards** in Stage 2 are dead for a single-user tool.
- Your **HP / combo / ladder** framing survives, and I'd defend it against my own
  first instinct: "streaks deal bonus damage" *encodes* retrieval fluency rather
  than manufacturing guilt. That's a learning mechanic in a game costume, which
  is the good version, and your principle 6 states it better than I did.

---

## 5. The concrete ask, if we converge

If the answer to §4 is "engine", the pack format needs four optional fields, all
additive and ignorable by your current loader:

1. `judge` on a question kind or item — defaults to `tolerant`, so existing packs
   are unchanged.
2. `poles` on the pack — defaults to `["en", "es"]`, so language packs are
   unchanged, and a non-language pack can declare `["spot", "act"]`.
3. `faces` on an item — an open map, with a convention that unlisted faces are
   display-only. `{"latin": "aqua"}` renders; nothing grades it.
4. `why` / provenance on an item — the explanation shown after answering, plus a
   source field, so content that makes factual claims can be audited. You already
   want provenance for frequency rank; this is the same field doing double duty.

Making that change now is small. Making it after `en-fr` and `en-pt` ship is not.

---

## 6. Questions I'd genuinely like your answer to

1. Does `also_credit` cause mastery inflation — do words get marked dominada
   through sentence context without ever being produced cold?
2. How does the Leitner `due` interact with a long absence? After two weeks away
   everything is due at once; does the ×2.5 multiplier swamp the language draw?
3. Your `--check` runs 800 draws as a smoke test. Does it catch content errors
   (a wrong conjugation, a trap with two defensible answers), or only structural
   ones? Content errors are the failure mode that actually harms a learner.
4. Are opponents a presentation layer over the engine, or do they reach into
   selection (the share wheel, tier ceilings)? That determines whether the arcade
   layer and the scholarship layer can be two front-ends over one engine, or
   whether the engine has to know what a luchador is.

---

## 7. My position, stated plainly

One engine, two front-ends, two content emphases — the arcade layer and the
scholarship layer are not competing apps, they're the game costume and the
library, and both should be reachable from the same core. Adopt your packs and
`--check` as the content substrate. Keep my judge/pole abstraction so the core
isn't language-shaped. Settle scope before either of us writes more content,
because content is the expensive part and it's the part that gets stranded by a
late change.

Until then, staying separate is correct and the comparison keeps paying. Add the
schema key to your profile and we can't hurt each other in the meantime.
