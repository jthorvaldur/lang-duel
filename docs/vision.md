# Vision — a terminal language sparring partner

*Status: living document. Two working implementations exist; this describes
where they came from, everything they currently contain, and where the
project should go. Last updated against `mirror/lucha` v2.0 and
`src/langduel` (with lineage).*

---

## 1. The north star

Take a learner from zero to a **basic functional view of a language** —
greet people, order coffee, ask where the bathroom is, handle numbers,
prices and time, and not fall into the classic traps — using nothing but a
terminal, a few minutes at a time.

The original brief (`base.md`) asked for: a question-asking CLI that
alternates languages, expands on verbs and conjugations, weights question
density toward the language most often gotten wrong, keeps a scoring card
of wins/losses plus accumulated agreed-understood words, and is fun.

Everything since flows from one idea that proved out:

> **Knowledge is a map of pairs.** `lang1_i ↔ lang2_i` is either known —
> proven correct in *both* directions — or it isn't. The game's job is to
> grow that map, and then to make old pairs resurface in *new situations*
> (fresh sentences, clozes, traps), the same way people optimally study
> for tests: retrieval practice, spaced repetition, interleaving.

## 2. Design principles

1. **The map is the metric.** Words proven both ways ("dominadas" /
   "understood") are the progress number that matters; XP and ladders are
   seasoning.
2. **Spaced repetition, not just weighting.** Every item carries a Leitner
   box and a due timestamp. Hits push reviews further out (10 min → 1 h →
   1 d → 3 d → 7 d); misses pull them back. Due reviews jump the queue.
3. **Density follows weakness.** The next question's language mix is the
   error mass of each direction, clamped 15–85 %, and shown openly on the
   scorecard.
4. **Honest grading.** Accent/case/article-insensitive folding; one typo =
   a "shave" (half win, keeps the streak, doesn't advance mastery); a
   hinted win is automatically a shave. Stats stay meaningful.
5. **Content is data, rules are code.** All teaching material lives in
   JSON packs; the engine is pack-agnostic. Agents and humans edit content
   without reading game code, and `./duelo.py --check` gates every edit.
6. **Fun is mechanics, not decoration.** HP, combos, knockouts, seasons
   all encode learning behavior (streaks deal bonus damage → retrieval
   fluency is literally power).
7. **Zero-dependency core, airplane-runnable.** Python 3.12 stdlib only.
   Everything testable headless with piped stdin and a seeded RNG.
8. **Agents are first-class contributors.** Minimal schemas, a validator
   with precise errors, and a scoped `AGENTS.md` per implementation.

## 3. The two implementations

| | `src/langduel` | `mirror/lucha` |
|---|---|---|
| Frame | calm drill duel | lucha libre arcade ladder |
| Layout | Python package, content in code | package + JSON content packs |
| Signature feature | **lineage** — etymology layer (Latin roots, English cognates, the Arabic layer, sound-change patterns) with a discovery mechanic (`:e`/`:l`/`:p`) | **breadth of kinds** — traps, gender, numbers/time, generated sentences; Leitner scheduling |
| Entry | `./play` | `./mirror/duelo.py` |

They are deliberate design-space exploration, not competitors. The obvious
endgame is one engine with both feature sets (see §6).

## 4. Concepts — the complete list

### Learning model
- **Map / dominada / understood** — a word correct ≥ 2× in *each*
  direction (`SOLID_HITS`); the "both sides agree you own it" counter.
- **Leitner box / due** — per-item scheduling state (`box` 0–5, `due`
  timestamp); intervals `(0, 10m, 1h, 1d, 3d, 7d)`.
- **Reviews due now / scheduled ahead** — scorecard visibility into the
  schedule.
- **es_bias / density weighting** — P(next question demands Spanish) from
  per-direction error mass, Laplace prior 0.5, clamped [0.15, 0.85].
- **Item weighting** — unseen ×1.7; misses boost (1 + 1.3·miss); hits damp
  (1 + 0.9·hits); dominada ×0.15; scheduled-ahead ×0.04; due review ×2.5.
- **also_credit** — a correct answer inside a generated sentence or gender
  drill also feeds the underlying word/verb map entries.
- **Interleaving** — kinds and tenses mixed every turn; recent-window
  dedupe avoids immediate repeats.
- **Tiers 1–3** — curriculum gating (survival → everyday → stretch);
  opponents cap the tier ceiling.

### Question kinds
- **word** — vocab both directions, with alternative-answer lists.
- **verb** — conjugation drill both directions; imperfect accepts every
  person sharing a form ("hablaba" → I/he/she used to speak); full
  six-person teaching card after each; `imperfect_ok` guards broken cues
  ("used to can").
- **cloze** — whole working sentences with a blank (`¿Dónde ___ el baño?`),
  translation as cue, usage note after.
- **trap** — forced choice for the classic confusables: ser/estar (incl.
  the event rule: *la fiesta ES en mi casa*), por/para, saber/conocer,
  pretérito/imperfecto. Options shuffled, answerable by word or number.
- **gender** — `el o la` drills; articles enrolled per-word in the pack
  (with notes for `el día`, `el agua`).
- **num** — numbers 0–99 both directions, market prices (`Cuesta ___
  pesos`), telling time (`y cuarto / y media / menos cuarto / en punto`,
  reverse clock-reading).
- **sentence** — generated fresh from dominated ingredients only: SVO,
  negatives with do-support, pronoun-dropping accepted, place questions
  (`¿Dónde está la casa?`). The map in new situations, literally.

### Grading
- **fold** — lowercase, strip accents/punctuation/leading articles.
- **hit / close / miss** — exact fold match / edit distance ≤ 1–2 / else.
- **hint → shave** — a hinted hit is recorded as a close.

### Game frame (lucha)
- **Opponents / ladder / seasons** — four gates (El Turista → La Maestra
  Severa → El Pretérito Impasible → El Verbo Supremo); clearing the ladder
  starts a new season with +2 HP rivals.
- **HP / combo** — hits deal 1 damage, every 3rd streak answer +1; misses
  cost the opponent's `dmg`; knockout → opponent heals, you rise at 8 HP.
- **Share wheel** — each kind owns a fraction per opponent (vocab takes
  the remainder; sentences auto-take 0.12 once the map has ingredients).
- **Ranks / XP / streaks** — Novato del Ring → Leyenda del Barrio.

### Etymology layer (langduel, to be merged)
- **lineage / origin cards** — Latin root, English cognates, a one-line
  story ("a fact is a thing done"); XP bonus for first discovery.
- **patterns** — sound laws as collectibles: Latin f- → h- (facere →
  hacer), diphthong/boot verbs, the Arabic layer (ojalá ← inshallah).
- **library / `:l`** — browsable collection of unearthed lineages.

### Engineering
- **content pack** — `content/<pair>/*.json`: words, verbs, clozes, traps,
  sentences, opponents. `es-en` today; a new pair is a new directory.
- **validate / `--check`** — schema + reference + smoke checks (800
  draws), exit 1 with one line per problem; the content-edit loop.
- **profile / save.json** — wins/losses/shaves, streaks, XP, ladder,
  per-item `{en, es, miss, box, due}`, per-language `[attempts, hits]`.
- **fold-stable keys** — `w:` `v:` `c:` `t:` `g:` `n:` `s:` prefixes keep
  item identity stable across refactors.

## 5. Current directions (active work)

1. **Audio/dictation** — deferred on purpose (in-flight, untestable):
   macOS `say -v Monica` for hear-it-type-it rounds. Design is settled;
   implementation waits for a testable moment.
2. **Lineage merge** — port etymology into the pack schema as optional
   `"origin"` blocks on words/verbs, keep the discovery mechanic.
3. **Daily ritual** — daily-duel mode, day-streak, heatmap on the card.
4. **Strictness ramp** — accents optional at tier 1, required at tier 3;
   today's shave becomes tomorrow's miss.
5. **Curriculum expansion** — themed packs (restaurant, airport, family),
   A1→A2 coverage, more traps (pedir/preguntar, llevar/tomar, por la
   mañana/de la mañana).
6. **Second language pair** — prove the pack format (`en-fr` or `en-pt`).

## 6. Tech stack — how it should scale

The rule: **the core never gains a dependency; scale adds wrappers, not
rewrites.**

**Stage 0 — now (correct):** Python 3.12 stdlib only. JSON packs, JSON
profile, hand-rolled validator, scripted-stdin tests, `./play` and
`./duelo.py` launchers. This is what makes it airplane-runnable and
trivially agent-editable. Do not "upgrade" this layer.

**Stage 1 — when content or contributors grow:**
- `pack.schema.json` (JSON Schema) enforced in CI — not at runtime; the
  hand-rolled `--check` stays the in-repo loop.
- Test harnesses → `pytest` (dev-only dep): golden-file CLI sessions,
  property tests for `fold`/`grade`/conjugation/`num_es`, pack fuzzing.
- Content provenance fields: frequency rank, source, so curriculum choices
  are auditable and new packs can be seeded from frequency lists.
- Packaging: `pyproject.toml`, console entry point, `pipx install`.
  Packs discovered from `content/*/`; `--pack` already exists.

**Stage 2 — when it becomes a platform:**
- The engine is already print-free and pack-driven, so front-ends are
  wrappers: **Textual** TUI (richer terminal UI, same process) or
  **FastAPI** + tiny web client (engine as a library).
- Profile store JSON → **SQLite** (single-file, concurrent-safe, migration
  path is one import script); Postgres only if truly multi-user hosted.
- Pack registry with versions; user profiles sync; daily-duel leaderboards.
- LLM-assisted content generation pipeline *behind* `--check`: agents
  draft, the validator gates, humans sample.

**Explicit non-goals for the core:** ORMs, web frameworks, async,
cloud services, native audio deps. If a feature needs one, it lives at
Stage 2 and the terminal game must still run without it.

## 7. What "done" looks like

A learner with a few weeks of daily sessions holds a map of ~500 pairs
proven both ways, all core conjugations, the four trap families, and
numbers/time/prices cold — and the scorecard can *prove* it (due reviews
near zero, dominadas high, mix settled at 50/50). That's basic functional
fluency, from a terminal, for the price of a text file.
