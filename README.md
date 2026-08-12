# ¡Duelo de Idiomas! — English ⇄ Spanish

A full-screen terminal trainer that alternates between the two languages,
expands every verb into its paradigm, traces where the words came from, and
**aims most of its questions at whichever language you're worse at producing**.

No dependencies. Python 3.10+.

```bash
./play
```

## The screen

The record lives in the top right and updates every round.

```
══════════════════════════════════════════════════════════════════════
¡DUELO!  english ⇄ español                  W 24  L 7  ~ 3  ·  612 xp
Turista Valiente  ·  9 words understood   mix 71% es  ███████░░░ 77%
══════════════════════════════════════════════════════════════════════

  #32  ▶ answer in ESPAÑOL                            present · tú

      "you have"   →  tener

  ✔ ¡Eso!  +18 xp   ^^ streak 6

┌─ conjugation ──────────────────────────────────────────────────────┐
│ tener — to have  ·  present                                        │
│    yo           tengo          I                                   │
│    tú           tienes         you                                 │
│    ...                                                             │
│    note: e→ie in the boot (tienes, tiene, tienen)                  │
└────────────────────────────────────────────────────────────────────┘
┌─ lineage · tener  ★ new ───────────────────────────────────────────┐
│ Latin tenere, to hold                                              │
│ english cousins: tenant, tenacious, contain, retain, tenure        │
│                                                                    │
│ A tenant holds. So does anyone who tiene.                          │
└────────────────────────────────────────────────────────────────────┘
```

Commands: `:h` hint · `:e` origin · `:l` library · `:p` patterns ·
`:stats` · `:skip` · `:q` quit.

## Does it remember?

Yes. The profile is written to `~/.langduel.json` **after every single round**,
plus on quit and on ctrl-c — closing the terminal mid-question cannot cost you
anything. It holds your record, per-language accuracy, per-item history, and
your lineage collection. `./play --stats` and `./play --library` print it
without starting a game. `./play --reset` wipes it.

The app runs on the terminal's alternate screen, so quitting leaves your
scrollback exactly as it was — except for the final scorecard, which is printed
back to the real screen on the way out.

## The four mechanics

**Alternation.** Every question names a production language. Vocabulary runs
both ways (`agua → water` and `water → agua`); verbs do too — you either build
the Spanish form from an English cue, or read a Spanish form back into English.

**Density follows failure.** Accuracy is tracked separately per *production*
language. The next question's language is drawn from the error mass on each
side, floored at 15/85 so the strong side never vanishes. Miss ten Spanish
prompts and roughly 85% of what follows will demand Spanish. Within a language,
individual items are weighted by misses and quieted once solid, so your specific
weak words keep resurfacing.

**Scorecard.** Wins / losses / close calls, streak and best, XP and rank —
plus the counter that actually matters: **words understood both ways**,
incremented only once a word has been produced correctly twice in *each*
direction. Misses decay that credit. Every 12 understood words unlocks a
content tier (harder vocabulary, then the past tenses).

**Lineage.** The value-add layer, in two halves:

- *Origins* — 70 words and verbs carry their ancestry: the Latin, Arabic or
  Greek source, the English words descended from that same source, and a hook.
  `hablar` is Latin *fabulari*, to tell fables. `trabajo` traces to the
  *tripalium*, a torture device — so does *travail*, and probably *travel*.
  Each is handed over the first time you meet the word, worth +15 xp, and
  collects in the library (`:l`).
- *Sound laws* — the eight rules that generate cognates wholesale: Latin `f-`
  → silent Spanish `h-`, `-ct-` → `-ch-`, English `-ty` → `-dad`, `-tion` →
  `-ción`, the Arabic `al-` layer, and the stress rule that produces the
  stem-change "boot" you keep meeting in the conjugation drills. Each surfaces
  right after a word that demonstrates it, and collects under `:p`.

Where an etymology is genuinely disputed the entry says so — `niño` is most
likely nursery babble, not Latin, and the app tells you that rather than
inventing a root.

Near-misses (one or two characters — a dropped accent, a typo) score as
`close`: partial XP, no streak break, no loss on the card. Winning with a hint
also scores `close`, so the stats stay honest.

**Every wrong answer buys the whole item.** A miss is when attention is highest,
so that is when the app spends content. It assembles a card from every dimension
the item has — the pair restated, an example sentence, the ancestor and its
English cousins, the family the word belongs to, and the sound law it
demonstrates if you have met it:

```
┌─ remember it ──────────────────────────────────────────────────────┐
│ ahora   =   now                                                    │
│                                                                    │
│   Ahora no puedo hablar.                                           │
│   I can't talk right now.                                          │
│                                                                    │
│ Latin hac hora, at this hour                                       │
│ english cousins: hour, horoscope                                   │
│                                                                    │
│ glue: pero, porque, también, siempre, nunca, después               │
└────────────────────────────────────────────────────────────────────┘
```

Nothing is invented to pad it out — an item with two dimensions shows two. The
card appears regardless of which stage you are at, because an error is the one
moment worth interrupting for.

## Modes

The app opens small and grows. A new player gets word pairs and nothing else;
verbs, lineage, the past tenses and the Latin face each arrive as they are
earned, so the first screen is never a wall of panels.

| Stage | Unlocks at | Adds |
|---|---|---|
| words | start | word pairs, both directions |
| verbs | 6 | the present tense |
| lineage | 14 | origins and sound laws |
| tenses | 24 | preterite, imperfect, harder vocabulary |
| latin | 40 | the ancestor face on every card that has one |

`--basic` pins the app to that first stripped-back stage permanently, and
`--stage N` pins it anywhere in between. Progress still accrues underneath, so
this is a way to *play* the simple game, not a way to be stuck in it.

### The third face: Latin, unjudged

At the last stage each card shows the ancestor both sides descend from —
`aqua → agua & water`, `fabulari → hablar & to speak`, `al-mujadda → almohada &
pillow`. It is displayed, never graded, never scored. That is the point: the
unjudged face can be as rich as it likes because nothing there can punish you,
and it turns the pair into a derivation rather than a coincidence. Where the
etymology is disputed or the paradigm is suppletive — `niño`, `ser`, `ir` — the
card shows nothing rather than guessing.

## Second domain: spotting fakes, and handling the call

```bash
./play --domain aiid      # just this
./play --domain mixed     # woven into the Spanish
```

Voice cloning now needs seconds of audio, and the people most often targeted get
the least practice. This domain drills two poles, tracked separately: **spot it**
(recognising synthetic media and machine-written text) and **act on it** (what to
actually do when the call comes). The split matters — being good at spotting and
bad at acting is the more dangerous gap, and the scorecard names it.

The content leans on protocol over detection, because protocol keeps working
when detection fails: hang up and call back on a number you already have, agree
a family passphrase that was never written down, treat urgency plus secrecy as
the signature. Detection tests that are degrading as models improve are labelled
as such — teaching a test that has stopped working is worse than teaching none.

## Options

```bash
./play --rounds 20          # fixed-length session (default: endless)
./play --verbs 0.6          # 60% conjugation drills (default 0.4)
./play --stats              # print the scorecard and exit
./play --library            # print collected origins and sound laws, exit
./play --seed 42            # reproducible question order
./play --reset              # wipe the saved profile
./play --profile ./me.json  # keep a separate scorecard
./play --basic              # the stripped-back early game, at any level
./play --stage 3            # pin to a particular stage
./play --domain mixed       # Spanish and the deepfake domain together
```

Set `NO_COLOR=1` to drop colour, `LANGDUEL_ASCII=1` to disable the alternate
screen (useful when piping output).

## Layout

| File | Contents |
|---|---|
| `src/langduel/content.py` | Words, verbs, and the conjugator. Pure data + functions. |
| `src/langduel/lineage.py` | Etymologies and sound laws. Pure data. |
| `src/langduel/engine.py` | Profile, scoring, stages, adaptive selection. No I/O. |
| `src/langduel/judges.py` | What counts as right: exact, tolerant, choice. |
| `src/langduel/aiid.py` | Deepfake/AI-identification domain. Pure data. |
| `src/langduel/ui.py` | Colour, width-aware alignment, panels, screen control. |
| `src/langduel/cli.py` | The app: screens, round loop, input. |

Adding vocabulary means appending a `Word(...)` to `WORDS`; adding a verb means
appending a `Verb(...)`, and regular verbs need nothing but an infinitive and a
gloss — the conjugator handles present, preterite and imperfect from the
endings table, with irregulars overriding it. Etymologies attach by Spanish
headword, so a new `Origin` entry lights up automatically for any word already
in the bank. The engine imports no UI code, and the language pair is confined to
`content.py` and `lineage.py`.
