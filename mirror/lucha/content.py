"""Content packs for Lucha Léxica.

A pack is a directory of JSON files under `content/` (default: `es-en`).
All teaching material lives in those files — edit them to change what the
game teaches; the code here only loads and checks them. After editing a
pack, run `./duelo.py --check`, which calls `validate()`.

Schemas are documented in mirror/AGENTS.md and enforced by validate().
Everything here is data + pure functions. No I/O beyond reading the pack.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CONTENT_ROOT = Path(__file__).resolve().parent / "content"
DEFAULT_PACK = "es-en"

TAGS = ("pronoun", "people", "noun", "adj", "glue", "phrase")
TENSES: tuple[str, ...] = ("present", "preterite", "imperfect")
TENSE_LABEL = {
    "present": "presente",
    "preterite": "pretérito (past, finished)",
    "imperfect": "imperfecto (used to)",
}

PERSONS: tuple[tuple[str, str], ...] = (
    ("yo", "I"),
    ("tú", "you"),
    ("él/ella", "he/she"),
    ("nosotros", "we"),
    ("vosotros", "you all"),
    ("ellos", "they"),
)
_EN_SUBJECT = ("I", "you", "he", "we", "you all", "they")

# Regular endings, indexed by person 0..5.
_ENDINGS: dict[str, dict[str, tuple[str, ...]]] = {
    "present": {
        "ar": ("o", "as", "a", "amos", "áis", "an"),
        "er": ("o", "es", "e", "emos", "éis", "en"),
        "ir": ("o", "es", "e", "imos", "ís", "en"),
    },
    "preterite": {
        "ar": ("é", "aste", "ó", "amos", "asteis", "aron"),
        "er": ("í", "iste", "ió", "imos", "isteis", "ieron"),
        "ir": ("í", "iste", "ió", "imos", "isteis", "ieron"),
    },
    "imperfect": {
        "ar": ("aba", "abas", "aba", "ábamos", "abais", "aban"),
        "er": ("ía", "ías", "ía", "íamos", "íais", "ían"),
        "ir": ("ía", "ías", "ía", "íamos", "íais", "ían"),
    },
}


# --------------------------------------------------------------------------
# Records — one dataclass per JSON file
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Word:
    en: str
    es: str
    tag: str
    es_alts: tuple[str, ...] = ()
    en_alts: tuple[str, ...] = ()
    tier: int = 1
    article: str = ""        # "el"/"la" — enables the gender drill
    article_note: str = ""   # shown after gender answers (e.g. el día)

    def accepted(self, lang: str) -> tuple[str, ...]:
        return (self.es,) + self.es_alts if lang == "es" else (self.en,) + self.en_alts


@dataclass(frozen=True)
class Verb:
    infinitive: str
    en: str                       # "to speak"
    gloss: str                    # "speak, talk" — first chunk is the cue base
    en_forms: tuple[str, str, str] = ()   # base / 3rd-person / past, if irregular
    irregular: dict[str, tuple[str, ...]] = field(default_factory=dict)
    note: str = ""
    tier: int = 1
    imperfect_ok: bool = True     # False when "used to ___" breaks (poder: *used to can*)

    @property
    def ending(self) -> str:
        return self.infinitive[-2:]

    @property
    def stem(self) -> str:
        return self.infinitive[:-2]

    def conjugate(self, tense: str) -> tuple[str, ...]:
        if tense in self.irregular:
            return self.irregular[tense]
        return tuple(self.stem + e for e in _ENDINGS[tense][self.ending])

    def english(self) -> tuple[str, str, str]:
        if self.en_forms:
            return tuple(self.en_forms)  # type: ignore[return-value]
        base = self.gloss.split(",")[0].split("(")[0].strip()
        third = base + ("es" if base.endswith(("s", "sh", "ch", "x", "o")) else "s")
        past = base[:-1] + "d" if base.endswith("e") else base + "ed"
        return base, third, past


@dataclass(frozen=True)
class Cloze:
    text: str          # sentence with ___ where the answer goes
    answer: str
    alts: tuple[str, ...] = ()
    en: str = ""       # translation shown as the cue
    tier: int = 1
    note: str = ""


@dataclass(frozen=True)
class Trap:
    pair: str          # "ser o estar"
    text: str          # sentence with ___ where the choice goes
    options: tuple[str, str]
    correct: int       # index into options
    why: str
    tier: int = 2


@dataclass(frozen=True)
class Opponent:
    name: str
    epithet: str
    hp: int
    tier: int            # content ceiling while fighting this opponent
    verb_share: float    # fraction of turns that are conjugations
    cloze_share: float
    dmg: int             # HP you lose per miss
    trap_share: float = 0.0
    num_share: float = 0.0
    gender_share: float = 0.0
    # vocab takes whatever share is left; sentences take 0.12 when ingredients exist


@dataclass
class Pack:
    name: str
    words: tuple[Word, ...]
    verbs: tuple[Verb, ...]
    clozes: tuple[Cloze, ...]
    traps: tuple[Trap, ...]
    opponents: tuple[Opponent, ...]
    pairs: dict[str, tuple[str, ...]]    # verb infinitive -> complement en keys
    places: dict[str, tuple[str, str]]   # word en key -> (es phrase, en phrase)

    @property
    def verbs_by_name(self) -> dict[str, Verb]:
        return {v.infinitive: v for v in self.verbs}

    @property
    def words_by_en(self) -> dict[str, Word]:
        return {w.en: w for w in self.words}


def english_cue(verb: Verb, tense: str, person: int) -> str:
    base, third, past = verb.english()
    subj = _EN_SUBJECT[person]
    if tense == "present":
        if base == "be":
            form = {0: "am", 2: "is"}.get(person, "are")
        else:
            form = third if person == 2 else base
        return f"{subj} {form}"
    if tense == "preterite":
        return f"{subj} {past}"
    return f"{subj} used to {base}"


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def _records(raw: list[dict], cls):
    known = set(cls.__dataclass_fields__)
    out = []
    for entry in raw:
        unknown = set(entry) - known
        if unknown:
            raise ValueError(f"{cls.__name__}: unknown field(s) {sorted(unknown)} "
                             f"in {entry!r:.80}")
        kwargs = {k: (tuple(v) if isinstance(v, list) else v) for k, v in entry.items()}
        if cls is Verb and "irregular" in kwargs:
            kwargs["irregular"] = {t: tuple(f) for t, f in kwargs["irregular"].items()}
        if cls is Verb and "en_forms" in kwargs:
            kwargs["en_forms"] = tuple(kwargs["en_forms"])
        out.append(cls(**kwargs))
    return tuple(out)


def load_pack(name: str = DEFAULT_PACK) -> Pack:
    d = CONTENT_ROOT / name
    if not d.is_dir():
        raise FileNotFoundError(f"no content pack at {d}")
    get = lambda fn: json.loads((d / fn).read_text())  # noqa: E731
    sentences = get("sentences.json")
    return Pack(
        name=name,
        words=_records(get("words.json"), Word),
        verbs=_records(get("verbs.json"), Verb),
        clozes=_records(get("clozes.json"), Cloze),
        traps=_records(get("traps.json"), Trap),
        opponents=_records(get("opponents.json"), Opponent),
        pairs={k: tuple(v) for k, v in sentences["pairs"].items()},
        places={k: tuple(v) for k, v in sentences["places"].items()},
    )


# --------------------------------------------------------------------------
# Validation — the --check loop for content edits
# --------------------------------------------------------------------------


def validate(pack: Pack) -> list[str]:
    """Static checks on a pack. Returns a list of human-readable errors."""
    err: list[str] = []
    words_by_en = pack.words_by_en
    verbs_by_name = pack.verbs_by_name

    for w in pack.words:
        if not w.en or not w.es:
            err.append(f"word with empty side: {w!r}")
        if w.tag not in TAGS:
            err.append(f"word {w.en!r}: unknown tag {w.tag!r} (one of {TAGS})")
        if w.article and w.article not in ("el", "la"):
            err.append(f"word {w.en!r}: article must be el/la, got {w.article!r}")
        if w.article_note and not w.article:
            err.append(f"word {w.en!r}: article_note without article")
        if w.tier not in (1, 2, 3):
            err.append(f"word {w.en!r}: tier {w.tier} not in 1..3")

    for v in pack.verbs:
        if v.ending not in ("ar", "er", "ir"):
            err.append(f"verb {v.infinitive!r}: must end ar/er/ir")
        if v.en_forms and len(v.en_forms) != 3:
            err.append(f"verb {v.infinitive!r}: en_forms needs exactly 3 forms")
        for tense, forms in v.irregular.items():
            if tense not in TENSES:
                err.append(f"verb {v.infinitive!r}: unknown tense {tense!r}")
            if len(forms) != 6:
                err.append(f"verb {v.infinitive!r}/{tense}: needs 6 forms, got {len(forms)}")
        for tense in TENSES:
            try:
                v.conjugate(tense)
                english_cue(v, tense, 0)
            except Exception as e:  # noqa: BLE001 — report, don't crash
                err.append(f"verb {v.infinitive!r}/{tense}: {e}")

    for i, c in enumerate(pack.clozes):
        if "___" not in c.text:
            err.append(f"cloze {i} ({c.text!r}): missing ___ blank")
        if not c.answer or not c.en:
            err.append(f"cloze {i} ({c.text!r}): needs answer and en")

    for i, t in enumerate(pack.traps):
        if len(t.options) != 2:
            err.append(f"trap {i} ({t.text!r}): needs exactly 2 options")
        if t.correct not in (0, 1):
            err.append(f"trap {i} ({t.text!r}): correct must be 0 or 1")
        if "___" not in t.text or not t.why:
            err.append(f"trap {i} ({t.text!r}): needs ___ blank and why")

    for v, comps in pack.pairs.items():
        if v not in verbs_by_name:
            err.append(f"sentences.pairs: {v!r} is not a verb in verbs.json")
        for comp in comps:
            if comp not in words_by_en:
                err.append(f"sentences.pairs: {v}/{comp!r} is not a word in words.json")
    for key, phrases in pack.places.items():
        if key not in words_by_en:
            err.append(f"sentences.places: {key!r} is not a word in words.json")
        if len(phrases) != 2:
            err.append(f"sentences.places: {key!r} needs (es phrase, en phrase)")

    for o in pack.opponents:
        total = (o.verb_share + o.cloze_share + o.trap_share
                 + o.num_share + o.gender_share)
        if total > 0.95:
            err.append(f"opponent {o.name!r}: shares sum to {total:.2f} > 0.95, "
                       "vocab needs the remainder")
        if o.tier not in (1, 2, 3) or o.hp <= 0 or o.dmg <= 0:
            err.append(f"opponent {o.name!r}: bad tier/hp/dmg")
    return err
