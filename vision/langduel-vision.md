# Vision — from a Spanish drill to a general teaching engine

Written from the `src/langduel` track, without reading the parallel document in
`docs/`, so the two can be compared honestly.

Status of everything below is marked: **[built]** exists and is tested,
**[designed]** is specified but unwritten, **[speculative]** is a bet I would
want evidence for before spending real effort.

---

## 1. The thesis

Most learning software is a quiz with a progress bar. It tests recall of items
and calls the resulting number "progress". That model is cheap to build, easy to
game, and teaches the shallowest thing available — recognition of the exact
material drilled.

The bet here is different, and it came out of the Spanish work rather than being
imposed on it:

> **The item list is the surface. The product is the generative system
> underneath it — the paradigm the item sits in, and the rule that would let you
> derive it without ever having seen it.**

Drilling `hablar → hablo` teaches one cell. Showing the six-person paradigm
teaches six. Teaching that Latin `f-` became a silent Spanish `h-` lets a learner
derive `hacer` from *fact*, `hijo` from *filial*, `hierro` from *ferrous*, and a
few hundred more they will never be drilled on. The third of those is worth more
than the first two combined, and it is the one almost no app bothers with.

Every domain has that shape. Math has the distributive law where Spanish has a
sound law. Comedy has "setup establishes one reading, punchline forces a second."
Fraud has "urgency plus secrecy plus an irreversible payment method." In each
case the rule is small, transferable, and generates the items — and in each case
the app's job is to get the learner to the rule, using items as the vehicle.

**The app teaches the system, and uses the items as evidence you have it.**

---

## 2. Complete concept list

The vocabulary the whole design runs on. Anything not in this list is a detail,
not a concept.

### 2.1 Core objects

| Concept | Definition | Status |
|---|---|---|
| **Item** | One thing to be learned, held as a set of faces. Not "a question" — a question is generated *from* an item. | [built] |
| **Face** | One representation of an item: the Spanish word, the English word, the Latin ancestor, a conjugated form, a sentence, a chart, a punchline. Items are N-faced, not two-faced. | [built] |
| **Judged face** | A face the learner must produce and that is graded. | [built] |
| **Unjudged face** | A face that is shown but never graded — the Latin ancestor. Cheap to author (no answer set, no alternates, no edge cases), and free to be as rich and digressive as it likes, because nothing there can punish anyone. Every domain has one: Latin under Romance vocabulary, the derivation under a formula, the raw data under a statistic, the true story under a joke. | [built] |
| **Axis** | The dimension a question is produced along. | [built] |
| **Pole** | One end of an axis — the thing you must produce. Spanish's poles are `en`/`es`; the fraud domain's are `spot`/`act`. Accuracy is tracked per pole. | [built] |
| **Paradigm** | The closed table an item belongs to: the conjugation table, the times table, the standard chart types, the seven joke structures. Answer one cell, get shown the table. Cheap to author, disproportionate payoff. | [built] |
| **Rule** | A transformation that generates or explains items wholesale: sound laws, the distributive law, "take the metaphor literally", "irreversible payment method means fraud". The highest-value content in the system. | [built] |
| **Domain** | A bundle of items, paradigms, rules, poles and judges. Spanish and fraud-defence exist; humor, math and data are designed. | [built] |
| **Judge** | Decides hit / close / miss for an answer, and says why. The interface where domain difficulty concentrates. | [built] |
| **Verdict** | A judge's output: result plus an optional note shown to the learner. | [built] |
| **Question** | A generated challenge: an item, a target pole, a prompt, an accepted set, a judge, and the cards to show afterwards. | [built] |
| **Profile** | Everything known about one learner: record, per-pole accuracy, per-item history, collections, stage. Schema-versioned, local, portable. | [built] |

### 2.2 Grading concepts

| Concept | Definition | Status |
|---|---|---|
| **Production over recognition** | You type the answer. Multiple choice measures familiarity; generation measures competence. Multiple choice is used only where free text would be *unfair* (safety scenarios). | [built] |
| **Hit / close / miss** | Three verdicts, not two. The middle one carries the design. | [built] |
| **Close** | Right knowledge, wrong execution — a dropped accent, a one-character typo, a win after a hint. Partial credit, streak survives, no loss recorded. Prevents the app from punishing the thing it is not testing. | [built] |
| **Tolerant judge** | Normalisation (case, accents, punctuation, leading articles) plus bounded edit distance. The default. | [built] |
| **Exact judge** | For terminology that must be exact. | [built] |
| **Choice judge** | Pick-one, accepting a letter or the option's wording. | [built] |
| **Numeric judge** | Value within tolerance, units checked. | [designed] |
| **Structural judge** | Parse the answer and check properties: is the reveal in final position, is the pivot word genuinely two-sensed, does the query have the right shape, does the proof step follow. The judge that makes subjective domains gradeable. | [designed] |
| **Comparative judge** | Pairwise "which is better", never an absolute score. Humans and models are both far more reliable comparing than rating. Feeds an Elo. | [designed] |
| **Rubric judge** | Named criteria, each pass/fail, each explained. | [designed] |
| **Grade the mechanism, not the magic** | The principle that makes humor and writing tractable: score whether the learner executed the technique asked for, never whether the result is good. "Your reveal is in the middle of the sentence" is objective, actionable, and true regardless of taste. | [designed] |

### 2.3 Selection and progression

| Concept | Definition | Status |
|---|---|---|
| **Density follows failure** | The signature mechanic. Accuracy is tracked per production pole and the weaker pole gets the questions, floored at 15/85 so the strong side never vanishes. | [built] |
| **Two-level draw** | Outer draw picks the pole, inner draw picks the item. Everything added later — spaced repetition, new domains, difficulty targeting — belongs in the inner weight. Promote anything to the outer draw and the density mechanic quietly dies. | [built] |
| **Item weight** | Inner-loop weighting by miss count, decayed by solid hits, boosted for unseen material. | [built] |
| **Understood both ways** | An item counts as learned only when produced correctly twice in *each* direction. Recognising `agua` is not knowing it. Misses decay the credit. The number that actually means something. | [built] |
| **Stage** | Progressive disclosure of the app itself: words → verbs → lineage → tenses → Latin. A new player sees word pairs and nothing else. | [built] |
| **Stage floor** | A feature that has ever been switched on never switches off. Lets thresholds be retuned without taking things away from someone mid-game. | [built] |
| **Cap / basic mode** | Pin the app to an earlier stage deliberately. Progress still accrues underneath — a way to *play* the simple game, not to be stuck in it. Some people like the bare version, and the bare version is genuinely good. | [built] |
| **Content tier** | Difficulty band of the material itself (survival / everyday / stretch), distinct from stage, which is about which *features* are on. | [built] |
| **Spaced repetition** | Due-scheduling per item (Leitner boxes or FSRS). Must enter as an inner-loop multiplier, never as a hard gate — see two-level draw. | [designed] |
| **Interleaving** | Mixing item types and domains rather than blocking them. Well-supported in the learning literature and mostly free here, since selection is already probabilistic. | [designed] |

### 2.4 Teaching moments

| Concept | Definition | Status |
|---|---|---|
| **Expansion** | After a verb, the whole paradigm for that tense plus the stem-change note. One answer, six cells. | [built] |
| **Remember card** | Every wrong answer buys the whole item: the pair restated, an example sentence, the ancestor and its English cousins, the family the word sits in, the rule it demonstrates. A miss is when attention is highest, so it is when content gets spent. Nothing invented to pad it. | [built] |
| **Usage example** | One short, ordinary, picturable sentence per item. Context is the cheapest memory hook there is. | [built] |
| **Discovery** | The first meeting with an item's ancestry, paid in XP and collected permanently. | [built] |
| **Recall line** | Once collected, the origin recalls itself in a single dim line whenever the word returns — visible without repeating the full card. | [built] |
| **Sound law / pattern card** | A rule, surfaced right after an item that demonstrates it. The moment where the app stops teaching words and starts teaching Spanish. | [built] |
| **Library** | Everything collected — origins and rules — browsable. The scholarship layer's trophy case. | [built] |
| **Honest uncertainty** | Where the etymology is disputed (`niño`) or the paradigm is suppletive (`ser`, `ir`), the app says so or shows nothing. A wrong ancestor is worse than no ancestor, and an app that bluffs about the interesting part cannot be trusted about the boring part. | [built] |
| **Degrading test** | Content whose usefulness is decaying — deepfake detection tells — labelled as such. Teaching a test that has stopped working is worse than teaching none. | [built] |

### 2.5 Scoring and framing

| Concept | Definition | Status |
|---|---|---|
| **Record** | Wins, losses, close calls, pinned top-right and updated every round. | [built] |
| **Streak / XP / rank** | Momentum and progress framing. Deliberately secondary to "understood both ways". | [built] |
| **Scorecard** | The full picture, including the per-pole accuracy that explains *why* the questions are arriving as they are. Showing the learner the adaptive mechanism is part of the honesty. | [built] |
| **Opponent / ladder** | The arcade framing prototyped on the other track: HP, opponents, progression. A presentation layer, not an engine concern. | [built, other track] |

### 2.6 Cross-domain

| Concept | Definition | Status |
|---|---|---|
| **Cross-domain item** | An item whose faces come from different domains: say the price (language × math), the bilingual pun (language × humor), the misleading chart (data × humor). Where fluency actually lives. | [designed] |
| **Shared attention budget** | Because every domain reports per-pole accuracy into one profile on one scale, "weak at producing Spanish", "weak at producing proofs" and "weak at landing the reveal" compete on equal terms. This is what makes a multi-domain app coherent rather than four apps in a trench coat. | [designed] |
| **Lineage hub** | Latin as the shared ancestor node. Add Portuguese, Italian, French and the hub already explains all of them at once; PIE sits above it for the Germanic side (`noche`/`night`). Lineage depth scales sub-linearly with language count. | [designed] |

---

## 3. The domains

**Spanish ⇄ English, with Latin unjudged** [built]. The proving ground. 80 words,
18 verbs across three tenses, 70 etymologies, 8 sound laws.

**Fraud and synthetic media defence** [built]. Built because someone tried a
deepfake on a family member. Two poles — `spot` (recognise) and `act` (what to
do) — tracked separately, because being good at spotting and bad at acting is the
more dangerous gap. Content leans on protocol over detection, since protocol
survives a perfect fake: hang up and call back on a number you already have,
agree a passphrase that was never written down, treat urgency plus secrecy as the
signature. This domain matters disproportionately: it is the proof the engine is
not a language toy, and it is the one with a real deadline attached.

**More languages** [designed]. The Latin hub means each added Romance language
costs items but not lineage. Portuguese and Italian are nearly free riders.

**Humor** [designed]. The hard case, and the reason the judge abstraction exists.
A joke is a controlled collision between two readings, resolved late, at a
violation level the audience tolerates — incongruity-resolution, script
opposition, and benign violation each supplying one clause. The craft mechanics
are unusually explicit and therefore drillable: reveal position, compression,
pivot ambiguity, rule of three, callback, heightening. Most of those are
structurally checkable, which means the app can teach comedy without ever
claiming to score funniness.

**Math** [designed]. Should be the *second* domain built, not the fourth. It is
cheap, objective, exercises the numeric judge, and its rules (distributive law,
place value, identities) are exactly the "derive rather than memorise" shape the
thesis needs a second data point for.

**Data literacy** [speculative]. Chart ⇄ the claim it supports; distribution ⇄
the statistic that misrepresents it. Rules: what a log axis hides, when a mean
lies. Overlaps the fraud domain more than it looks like it should.

---

## 4. Tech stack, and how it scales

### 4.1 Where it is now

Pure Python 3.12, **zero runtime dependencies**, one JSON file per learner, a
terminal front end drawn with ANSI escapes. Roughly 2,000 lines. `uv` for the
dev toolchain, `ruff`, `pytest`.

This is not a placeholder to be replaced. Zero dependencies means it runs on
anything, starts instantly, and cannot rot from under itself — and the constraint
has been load-bearing for design quality, because it forced the engine to stay
data-plus-functions rather than accreting a framework.

### 4.2 The invariant to protect

**The engine imports no presentation code, and domains import no engine
policy.** Content is data. Judges are functions. The UI is a port. Everything
proposed below either preserves that or should be rejected.

### 4.3 Scaling path, in the order I would actually do it

**1. Content moves from Python literals to data files.** [designed]
The bottleneck is content, not code, and Python literals cannot be authored by
non-programmers, validated in CI, translated, or diffed usefully. Move items,
origins and rules to TOML or JSON with a schema, validated at load and linted in
CI. This is the single highest-leverage change and it unblocks everything else.

**2. Answers become an append-only event log.** [designed]
Today the profile stores derived state. Storing the *events* — item, pole,
verdict, timestamp, latency — instead means every metric can be re-derived,
scheduling algorithms can be changed retroactively, item difficulty can be
estimated, and multi-device sync becomes a merge of append-only logs rather than
a conflict. SQLite the moment the log outgrows a JSON file, which is soon.

**3. Spaced repetition on top of the log.** [designed]
FSRS or Leitner as an inner-loop weight multiplier. The event log makes this
retro-fittable to existing history rather than starting everyone from zero.

**4. Audio.** [designed]
The largest missing modality for language, and unavoidable for fraud training —
"does this voice sound synthetic" cannot be taught in text. TTS for listening
drills, STT for speaking drills. This is the first hard dependency I would
accept, and it should live behind an interface with a null implementation so the
zero-dependency core still runs.

**5. Model-backed judges, carefully.** [designed]
Structural and comparative judges need a model for the interesting cases. Order
of preference: deterministic parse first (free, explainable, testable), local
model second (Ollama — private, free, good enough for pairwise comparison), API
last for genuinely hard judgements. Every model call is cached by content hash.
A learner must always be able to run the app with models disabled and lose only
the subjective domains. Never let a model grade something a parser can grade.

**6. A second front end.** [speculative]
Because the engine has no I/O, a web or mobile client is a presentation port, not
a rewrite — the same reason the arcade layer and the scholarship layer can be two
faces of one engine. I would resist this until content and audio are solved,
since a prettier client teaches nobody anything.

**7. Server, only if multi-device demands it.** [speculative]
Local-first stays the default. If sync is needed: a thin service holding the
event log, Postgres, Railway (already in the toolchain). The profile is a
behavioural record of what someone is bad at — treat it as sensitive by default,
no telemetry without explicit consent, and no engagement analytics at all.

### 4.4 Testing, which is unusually important here

Content bugs are the real risk — a wrong conjugation or a fabricated etymology
does direct harm to a learner's model of the world. The property tests already in
use should become the CI gate:

- every item grades its own canonical answer as a hit, in every direction
  (currently 648 verb cells plus every word, both ways)
- every choice drill's answer is among its options
- every usage example contains the word it illustrates
- every rendered card stays inside the frame at any terminal width
- every lineage key references a real item; every rule reference resolves
- schema guards: foreign profiles are refused, old profiles migrate

Plus, once models are involved: golden-file tests for judges, and a
human-reviewed sample of any generated content before it ships. **No content
enters the app unreviewed, including content I generate.**

### 4.5 Measurement — does it actually teach?

The uncomfortable question most learning apps avoid by reporting engagement
instead. What I would actually track:

- **delayed retention**: re-test items at intervals after they were marked
  understood, and report the decay honestly
- **transfer**: does a learner who earned a sound law perform better on words
  they were never drilled on? That is the thesis, stated as a testable claim, and
  it is the single most important number in the system
- **item quality**: items with anomalous miss rates are usually bad items, not
  hard ones — surface them for review
- **calibration**: does "understood" predict getting it right in a month?

If transfer does not show up, the thesis is wrong and the app should become an
honest flashcard program.

---

## 5. Current directions

**Immediate.** Content to data files; event log; math as the second domain to
prove the abstraction on something cheap and objective before attempting humor.

**The two tracks.** `src/langduel` and `mirror/duelo.py` independently converged
on the same core — same names, same responsibilities, near-identical save
schemas — then diverged into a scholarship layer (lineage, library, sound laws)
and an arcade layer (opponents, HP, ladder). That is not two apps; it is one
engine with two front ends and two content emphases. They should converge on the
core and stay separate in presentation, and the trigger for merging is a grading
bug that has to be fixed twice. Until then the comparison has value, and the only
way they can damage each other is by reading each other's save files — which the
schema guard now prevents.

**What I would not build.** Streak-loss anxiety, daily-goal nagging, leaderboards,
lives, or any mechanic whose purpose is retention rather than learning. The
scorecard exists to tell the truth about your competence, and the moment it
starts flattering or coercing, it stops being able to do that. Similarly: no
claiming to teach what the app cannot grade, and no domain where being confidently
wrong is dangerous unless the content has been reviewed by someone who actually
knows it.

---

## 6. Open questions

1. **Does the rule layer transfer?** The entire thesis. Untested.
2. **How much content can be generated versus authored?** Etymologies must be
   verified; usage sentences probably can be generated and spot-checked. The
   ratio decides whether this scales to twenty domains or three.
3. **Does humor survive drilling?** Mechanics are teachable; timing, persona and
   taste may not be. The defensible claim is "you will construct jokes more
   competently", not "you will be funny."
4. **Whose audience?** Benign-violation windows and fraud pretexts are far more
   culturally specific than conjugation. Content needs an audience parameter or
   it will be quietly wrong for most users.
5. **Is the two-level draw right when domains multiply?** With eight domains, an
   outer draw over poles may need a domain-level draw above it — and that is
   exactly the kind of change that can kill the density mechanic by accident.
