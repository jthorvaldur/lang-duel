# From a Spanish drill to a teaching engine

Two independent implementations of `base.md` (`src/langduel/`, `mirror/duelo.py`)
converged on the same core without coordination. That convergence is the
evidence this document builds on: whatever both attempts reached for is probably
the actual abstraction, not an artifact of one design.

This is a design document, not a plan of record. Nothing here is built yet.

---

## 1. What the two implementations actually discovered

Stripped of Spanish, both apps are the same five ideas:

| Primitive | In the language app | Generalised |
|---|---|---|
| **Pair** | `agua` ⇄ `water` | Two representations of one underlying thing |
| **Direction** | which language you must *produce* | which face you must generate from the other |
| **Paradigm** | the six-person conjugation table | the closed system an item belongs to |
| **Rule** | `f-` → silent `h-`, `-ty` → `-dad` | a transformation that generates items wholesale |
| **Judge** | fold accents, edit distance, hit/close/miss | a gradeable notion of "right enough" |

And three mechanics on top of them:

- **Production over recognition.** You type the answer. Multiple choice measures
  familiarity; generation measures competence.
- **Bidirectional mastery.** An item counts as understood only when both
  directions are solid. Recognising `agua` is not knowing it.
- **Density follows failure.** Accuracy is tracked per *production axis*, and the
  weaker axis gets the questions.

The insight worth keeping: **paradigm + rule is the pedagogical core, not the
item list.** Drilling `hablar → hablo` teaches one cell. Showing the paradigm
teaches six. Showing the sound law that maps Latin `f-` to Spanish `h-` lets the
learner *derive* words they have never seen. Items are the surface; the app's
real product is the generative system underneath.

That generalises to every domain, which is the whole thesis here.

---

## 2. The elevated model

Five objects. Everything else is presentation.

**Item** — a pair of faces plus the domain it lives in. A face is any
representation: a word, a number, an expression, a chart, a setup line, a
dataset shape.

**Axis** — the dimension a question is produced along. In the language app there
is one axis with two poles (produce English / produce Spanish). In general there
are many: produce-symbolic / produce-numeric, produce-punchline /
produce-structure-name, produce-query / produce-result. Accuracy is tracked per
pole, and *the weak pole gets the density*. This is the language-weighting
mechanic, generalised — and it is the piece that makes a mixed-domain app work,
because "you are worse at producing Spanish" and "you are worse at producing
proofs" become the same measurement.

**Paradigm** — the closed table an item sits in. Conjugation table, times table,
unit circle, the seven basic joke structures, the standard chart types. Answer
one cell, get shown the whole table. Cheap to author, disproportionate payoff.

**Rule** — a transformation that generates or explains items. Sound laws;
distributive law; "setup establishes schema A, punchline forces schema B";
normalisation rules. Rules are the app's high-value content and should be
*earned* — surfaced when the learner meets an item that demonstrates one, and
collected. This is `lineage.py` generalised out of etymology.

**Judge** — decides hit / close / miss and, crucially, *says why*. The current
`grade()` (case-fold, strip accents, edit distance) is one implementation of an
interface that needs several:

| Judge | Verdict from | Domain examples |
|---|---|---|
| `Exact` | string equality after normalisation | vocabulary, terminology |
| `Tolerant` | normalisation + edit distance | current default; typos and accents |
| `Numeric` | value within tolerance, units checked | math, prices, estimation |
| `Structural` | parse the answer, check properties | humor mechanics, SQL shape, proof steps |
| `Comparative` | pairwise A/B, not absolute score | anything subjective — see §3 |
| `Rubric` | named criteria, each pass/fail | writing, explanation quality |

The judge is where domain difficulty concentrates. Get the interface right and
adding a domain is mostly content.

---

## 3. First hard domain: what is funny?

Humor is the right stress test precisely because it looks ungradeable. Working
through it forces the judge abstraction to be honest.

### 3.1 The theory, in operational terms

Four accounts, three of which are directly usable:

- **Incongruity–resolution** (Kant, Schopenhauer; formalised by Suls, 1972). A
  setup builds an expectation; the punchline violates it; a second reading
  retroactively makes the violation fit. Two stages: *incongruity*, then
  *resolution*. If nothing resolves, it's nonsense; if nothing is violated, it's
  a statement.
- **Semantic script theory** (Raskin, 1985; extended by Attardo & Raskin's
  General Theory of Verbal Humor, 1991). A joke is a text compatible with **two
  opposed scripts**. GTVH decomposes a joke into six knowledge resources —
  script opposition, logical mechanism, situation, target, narrative strategy,
  language. That decomposition is close to a ready-made drill schema: each
  resource is a dimension you can hold fixed and vary.
- **Benign violation** (McGraw & Warren, 2010). Something is simultaneously
  *wrong* and *okay*. Explains the dials the other theories leave implicit:
  violation magnitude and psychological distance. Too benign is boring, too
  violating is offensive, and the window moves with audience, time, and who is
  speaking.
- **Superiority** (Hobbes) and **relief** (Freud/Spencer) explain audience and
  social effects — who laughs, and why punch direction matters — more than they
  explain construction.

Synthesis the app can teach: **a joke is a controlled collision between two
readings, resolved late, at a violation level the audience will tolerate.** Each
clause in that sentence is a separately drillable skill.

### 3.2 The craft layer — where the actual drills live

Comedy writing is unusually explicit about mechanics, which is what makes it
teachable in this format:

| Mechanic | Drillable as | Auto-gradeable? |
|---|---|---|
| Two-schema pivot | given a setup, produce a second reading | partly — check the pivot word is genuinely ambiguous |
| Reveal position | rewrite so the surprise lands on the final word | **yes** — position of the pivot token |
| Compression | say it in fewer words without losing the turn | **yes** — token/syllable count, pivot preserved |
| Specificity | replace generic nouns with concrete ones | **yes** — lexical concreteness lookup |
| Rule of three | complete a pattern, break it on the third | **yes** — structural |
| Heightening | escalate while staying internally consistent | partly |
| Callback | reuse an earlier item in a new frame | **yes** — reference check |
| Misdirection | write a setup that supports two readings equally | partly |
| Punch direction | identify target and status | rubric |

Note how much of that column is "yes". **You can grade craft without grading
funniness** — which is exactly how comedy is taught by humans. "Your reveal is
in the middle of the sentence" is objective, actionable, and true regardless of
taste.

Some craft folklore should be marked as such: the claim that hard consonants
(the "k rule", from *The Sunshine Boys*) are inherently funnier is tradition with
weak empirical support. The app should teach it as a convention comedians
believe and use, not as a fact — the same honesty rule `lineage.py` already
applies to disputed etymologies.

### 3.3 The pairs

Humor maps onto the Item primitive more cleanly than expected:

- setup ⇄ punchline (both directions — reverse-engineering a setup from a
  punchline is the harder and more instructive one)
- flat sentence ⇄ compressed version with the reveal moved last
- joke ⇄ name of its mechanism (recognition; the cheap direction)
- premise ⇄ three escalating heightenings
- topic ⇄ its benign-violation coordinates (what's wrong / what makes it okay)
- observation ⇄ the second script that collides with it

Paradigms: the closed sets — joke structures, the standard misdirection types,
the escalation ladder. Rules: the transformations — *invert the status*,
*take the metaphor literally*, *apply the logic consistently past the point of
absurdity*, *replace the abstract with the specific*.

### 3.4 Grading, honestly — three tiers

1. **Mechanical.** Did you execute the mechanism asked for? Reveal in final
   position, pivot word genuinely two-sensed, word count reduced, pattern broken
   on the third beat. Objective, instant, no model needed. **Most learning
   happens here** and it should be the default.
2. **Comparative.** Pairwise "which is funnier" between the learner's version
   and a reference — never an absolute 1–10. People (and models) are far more
   reliable at comparison than at absolute rating, and pairwise results feed an
   Elo cleanly.
3. **Audience.** Real reactions. Ground truth, expensive, optional, last.

The app must never claim to score funniness absolutely. It scores whether you
executed the mechanism, and it says which one you missed. That constraint is a
feature: it keeps the engine honest and it matches how the skill is actually
coached.

---

## 4. Mixing domains

The payoff of one engine is cross-domain items — which are not a gimmick, they
are where fluency actually lives.

- **Math** — `7 × 8` ⇄ `56` (pair); the times table (paradigm); the distributive
  law (rule: `7 × 8 = 7 × 10 − 7 × 2`, the same "derive rather than memorise"
  move as a sound law); `Numeric` judge. Higher up: expression ⇄ equivalent form,
  theorem ⇄ proof sketch, graded `Structural`.
- **Data** — chart ⇄ the claim it supports; distribution ⇄ the summary statistic
  that misrepresents it; query ⇄ result shape. Rules: *what a log axis hides*,
  *when a mean lies*. Many are `Structural`.
- **Language × math** — say the number, the price, the time. Already on the
  other implementation's todo list; it is a cross-domain item that nobody had to
  design as one.
- **Language × humor** — puns are sound laws weaponised. A learner who has
  earned the `f-`/`h-` law has the equipment for a class of bilingual jokes; the
  false-friend inventory (`embarazada`) is a joke generator.
- **Data × humor** — the misleading chart is a visual incongruity: it sets up one
  reading and the axis delivers another. Same structure, different medium.

The axis mechanic makes the mix coherent rather than chaotic: every domain
reports accuracy per production pole into one profile, so "you are weak at
producing Spanish" and "you are weak at producing proofs" and "you are weak at
landing the reveal" compete for the same attention budget on the same scale.

---

## 5. What this costs in the current code

The existing engine is closer to this than expected. Roughly, in order:

1. **`grade()` → `Judge` protocol.** Current logic becomes `TolerantJudge`.
   `Question` gains a judge reference. Nothing else changes yet. *Small.*
2. **`lang_record` → `axis_record`.** Language becomes one axis among several;
   `es_bias()` becomes a general weakest-pole draw. The Selector's shape —
   outer axis draw, inner item weight — survives unchanged. *Small, but it is a
   save-schema change, so version the profile first.*
3. **`content.py` → `domains/<name>/`.** Each domain supplies items, paradigms,
   rules. `lineage.py` becomes the etymology domain's rule set, and `Rule`
   becomes a first-class object with the discovery/XP mechanic already built.
   *Medium, mostly mechanical.*
4. **Presentation split.** The two implementations already prototype the two
   halves: the arcade layer (opponents, HP, ladder) and the scholarship layer
   (library, lineage, sound laws). Those are two front-ends over one engine, not
   two apps — and keeping the boundary explicit is what lets a domain like humor
   arrive without the game layer needing to know what a punchline is. *Medium.*
5. **Humor domain.** Content-heavy, judge-heavy. Do it last, and only after the
   `Structural` judge exists — it is the proof that the abstraction holds.

Steps 1–2 are worth doing whether or not the rest happens: they cost little and
they are the ones that get expensive to retrofit once there is a second domain
and saved profiles in the wild.

---

## 6. The honest risks

- **Humor may not survive the drill format.** Mechanics are teachable; timing,
  persona and taste may not be. The app's defensible claim is "you will construct
  jokes more competently", not "you will be funny."
- **Cultural specificity.** Benign-violation windows differ by audience far more
  than conjugation does. Content needs an audience parameter or it will be
  quietly wrong for most users.
- **Generalising too early.** One domain plus a good abstraction is a library;
  four domains plus a mediocre one is a mess. The abstraction should be extracted
  from the *second* domain (math — cheap, objective, and it exercises the
  `Numeric` judge), not from the hardest one.
