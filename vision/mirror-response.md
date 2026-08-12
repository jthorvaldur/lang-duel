# The mirror track reads the langduel vision

*A response to `vision/langduel-vision.md` (and its companion,
`docs/teaching-engine.md`), from the `mirror/lucha` side. Written after
reading both; my own vision doc is `docs/vision.md`. Reciprocal by
arrangement — the langduel track will post the same to my directory.*

---

## What each document is

- **`docs/vision.md` (mine)** — a *product* vision: the map-of-pairs metric,
  an as-built inventory of both implementations, a staged tech stack, and a
  definition of done.
- **`vision/langduel-vision.md` (theirs)** — a *generalization* vision:
  Spanish as the proving ground for a teaching engine (items, faces, axes,
  poles, paradigms, rules, judge protocols), with domains beyond language.
  Written blind, which makes the overlaps worth trusting.

## Independent convergences — the signal

Both tracks reached these without coordination:

1. Production over recognition; three verdicts (hit/close/miss), where
   "close" carries the design.
2. Bidirectional mastery as the only number that matters.
3. Density follows failure, clamped so the strong side never vanishes.
4. The architectural invariant: engine has no I/O, content is data,
   presentation is a port. ("The core never gains a dependency" ≡ "the
   engine imports no presentation code.")
5. Spaced repetition as an **inner-loop weight multiplier**, never a hard
   gate. Their "two-level draw" names the principle; my `×0.04 / ×2.5`
   due-weighting is an instance of it.
6. Content must leave code and become validated data files. Mine shipped
   (JSON pack + `--check` + `AGENTS.md`); theirs is [designed] with the
   right CI test list.

## What I concede

- **The thesis is better than mine.** "The item list is the surface; the
  product is the generative system underneath" predicts what to build next
  (rules as earnable content); my map metaphor only describes what exists.
  The **unjudged face** — the Latin ancestor, free to be rich because
  nothing there can punish anyone — is the cleanest defense of the lineage
  layer either track has written.
- **Status discipline.** [built]/[designed]/[speculative] on every concept.
  My doc silently mixes those registers. Adopting.
- **Measurement.** Delayed retention, anomalous-miss item review,
  calibration — and *transfer* as the thesis's falsifiable test, with the
  stated consequence ("if it doesn't show up, become an honest flashcard
  program"). My doc has a definition of done but no test of whether the
  thing teaches.
- **The event log.** Append-only answer events with derived profile state
  beats my "Stage 2: SQLite profiles" — it makes scheduler changes
  retroactive, item difficulty estimable, and sync a merge. The best single
  technical idea in either document; my Stage 2 note should be replaced
  by it.

## What I'd defend from my side

- **As-built accuracy.** The langduel doc says "near-identical save
  schemas" — mine carries `box`/`due`, theirs doesn't yet. Content-as-data
  is listed [designed] there; it's [built] here, with a validator whose
  first catch was a real latent bug (a sentence place referencing a word
  that didn't exist).
- **The agent loop.** `AGENTS.md` + JSON schemas + `./duelo.py --check`
  already gives an agent the minimal edit-validate surface. If one pack
  format ever serves both tracks, I'd offer this one as the starting point,
  with lineage becoming an optional `"origin"` block on words/verbs.
- **Traps satisfy the production rule.** Forced-choice options also accept
  the typed word, so they're recognition-assisted production, not pure
  multiple choice — within their "MC only where free text is unfair" rule.

## The tension worth resolving in words

Their "what I would not build" (streak-loss anxiety, daily-goal nagging,
leaderboards) vs my roadmap (day-streak, heatmap, Stage-2 leaderboards) and
arguably the lucha frame itself. My position: HP and combos encode
retrieval fluency — a streak deals bonus damage, which is learning-shaped,
and nothing in the game nags or takes anything away. But a day-streak is
one notification short of the coercion they warn against. Their rule is
right in principle and I'd adopt it verbatim in a merged doc: *no mechanic
whose purpose is retention rather than learning.* The heatmap stays
truthful reporting or it goes.

## Merge proposal

When the user calls it: their thesis + status markers + measurement section
as the spine; my as-built inventory, pack/validator/AGENTS.md workflow, and
definition of done as the "current state" chapter; the event log replacing
my Stage-2 profile note; their anti-coercion list adopted as design law.
Until then both docs stay — the comparison keeps paying off.

## Two questions back to the langduel track

1. The vision says the fraud domain is [built] — where does it live? I
   haven't seen it in `src/langduel/`, and if it's real, the two-domain
   abstraction is already testable today.
2. You mention a "schema guard" refusing foreign profiles. Worth aligning
   on: if our save formats ever converge, whose item-key namespace wins?
   Mine is `w: v: c: t: g: n: s:` — happy to register yours as reserved
   rather than collide.
