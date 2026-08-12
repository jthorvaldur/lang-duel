# Lucha Léxica — agent guide

A terminal English⇄Spanish trainer (lucha libre frame). The design rule:
**all teaching material is JSON data; all rules are code.** Content work
never touches code, and code changes should not smuggle in content.

```
mirror/
  duelo.py                  launcher — the only entry point (./duelo.py)
  lucha/
    content/es-en/          the pack: words/verbs/clozes/traps/sentences/opponents JSON
    content.py              loaders + validate() — nothing else
    engine.py               grading, Leitner scheduling, question builders, selection
    cli.py                  printing, the fight loop, argparse
  save.json                 a player's scorecard (never edit by hand)
```

## The loop

1. Edit JSON in `lucha/content/es-en/`.
2. Run `./duelo.py --check` — it loads the pack, runs `validate()`, and
   smoke-draws 800 questions. Red output = fix the JSON, not the code.
3. Play a few rounds (`./duelo.py --seed 1`) to eyeball the result.

`--check` rejects unknown fields, so schema drift fails fast.

## Schemas (one example each; optional keys may be omitted)

`words.json` — list of:
```json
{"en": "water", "es": "agua", "tag": "noun", "es_alts": ["el agua"],
 "en_alts": [], "tier": 1, "article": "el", "article_note": "feminine, but el for the sound"}
```
- `tag`: pronoun | people | noun | adj | glue | phrase. `tier`: 1-3 (unlock order).
- `article` ("el"/"la") enrolls the word in gender drills. Omit it to opt out.

`verbs.json` — list of:
```json
{"infinitive": "tener", "en": "to have", "gloss": "have",
 "en_forms": ["have", "has", "had"],
 "irregular": {"present": ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"]},
 "note": "e→ie in the boot", "tier": 1, "imperfect_ok": true}
```
- Regular forms are computed from the infinitive; only supply `irregular` tables
  (always all 6 persons: yo tú él nosotros vosotros ellos) and `en_forms`
  (base / 3rd-person / past) when the defaults are wrong.
- `gloss` first chunk becomes the English cue ("speak, talk" → "I speak").
- `imperfect_ok: false` when "used to ___" is broken English (see poder).

`clozes.json` — `{"text": "¿Dónde ___ el baño?", "answer": "está", "alts": [], "en": "Where is the bathroom?", "tier": 2, "note": ""}`
- `text` must contain `___`; `en` is the cue shown to the player.

`traps.json` — `{"pair": "ser o estar", "text": "Ella ___ cansada.", "options": ["es", "está"], "correct": 1, "why": "estar for states", "tier": 2}`
- Exactly 2 options; `correct` indexes into them; `why` is the teach card.

`sentences.json` — ingredients for generated sentences (built only from words
the player has dominated):
```json
{"pairs": {"comer": ["bread", "food"]},
 "places": {"house": ["la casa", "the house"]}}
```
- `pairs`: verb infinitive → word `en` keys that work as its complement.
- `places`: word `en` key → (es phrase, en phrase) for "¿Dónde está …?".
- Every key referenced must exist in words.json/verbs.json (checked).

`opponents.json` — `{"name": "El Turista", "epithet": "…", "hp": 8, "tier": 1, "verb_share": 0.25, "cloze_share": 0.10, "dmg": 1, "trap_share": 0.0, "num_share": 0.10, "gender_share": 0.0}`
- Shares are fractions of the question wheel; their sum must stay ≤ 0.95
  (vocab takes the remainder; sentences auto-take 0.12 once possible).

## Invariants the engine relies on

- Question kinds are fixed: word, verb, cloze, trap, gender, num, sentence.
  A new kind means engine + cli work, not just JSON.
- Grading strips accents, case, punctuation and leading articles — write
  canonical answers in natural form; add `*_alts` for real variants only.
- Save-file item records carry `en`/`es`/`miss`/`box`/`due`; new question
  keys must be unique per content item (`w:`, `v:`, `c:`, `t:`, `g:`, `n:`, `s:` prefixes).
- Tiers are 1-3 everywhere; opponents gate content by tier.

## When you change code

- Keep `engine.py` print-free; keep `content.py` pack-agnostic (no es-en literals).
- If a schema or these rules change, update this file in the same edit.
- `./duelo.py --check` must stay green.
