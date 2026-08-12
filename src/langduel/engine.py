"""Game state, adaptive question selection, and answer grading.

No printing happens here — the CLI owns all I/O so this stays testable.
"""

from __future__ import annotations

import json
import random
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import content, lineage
from .content import VERBS, WORDS, Verb, Word

DEFAULT_PROFILE = Path.home() / ".langduel.json"

# How many clean hits in ONE direction before that direction counts as solid.
SOLID_HITS = 2
# A word is "understood" (scorecard counter) once both directions are solid.
DIRECTIONS = ("en", "es")


# --------------------------------------------------------------------------
# Answer normalisation & grading
# --------------------------------------------------------------------------

_STRIP_LEAD = ("the ", "a ", "an ", "to ", "el ", "la ", "los ", "las ", "un ", "una ")


def fold(text: str) -> str:
    """Lowercase, strip accents/punctuation/articles — so typing 'como estas' passes."""
    t = unicodedata.normalize("NFD", text.lower().strip())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t)
    t = " ".join(t.split())
    for lead in _STRIP_LEAD:
        if t.startswith(lead):
            t = t[len(lead):]
            break
    return t


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def grade(answer: str, accepted: tuple[str, ...]) -> str:
    """Return 'hit', 'close' (typo / accent slip), or 'miss'."""
    given = fold(answer)
    if not given:
        return "miss"
    folded = [fold(a) for a in accepted]
    if given in folded:
        return "hit"
    tolerance = 1 if len(given) <= 6 else 2
    if any(edit_distance(given, f) <= tolerance for f in folded):
        return "close"
    return "miss"


# --------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------


@dataclass
class Question:
    key: str  # stable item id, e.g. "w:water" or "v:tener:present:1"
    kind: str  # "word" | "verb"
    target_lang: str  # the language the player must PRODUCE
    prompt: str  # what we show
    hint: str  # tag / tense label shown under the prompt
    accepted: tuple[str, ...]
    canonical: str  # the answer we print when they miss
    expansion: list[str] = field(default_factory=list)  # teaching card, verbs only
    origin_key: str = ""  # index into lineage.ORIGINS, "" when we have nothing

    @property
    def origin(self) -> "lineage.Origin | None":
        return lineage.ORIGINS.get(self.origin_key) if self.origin_key else None


def word_question(w: Word, target_lang: str) -> Question:
    src = "en" if target_lang == "es" else "es"
    return Question(
        key=f"w:{w.en}",
        kind="word",
        target_lang=target_lang,
        prompt=w.prompt_text(src),
        hint=w.tag,
        accepted=w.accepted(target_lang),
        canonical=w.es if target_lang == "es" else w.en,
        origin_key=w.es if w.es in lineage.ORIGINS else "",
    )


def verb_question(v: Verb, tense: str, person: int, target_lang: str) -> Question:
    forms = v.conjugate(tense)
    form = forms[person]
    cue = content.english_cue(v, tense, person)
    if target_lang == "es":
        prompt = f'"{cue}"   →  {v.infinitive}'
        # Spanish drops the subject pronoun; accept it either way.
        subj = content.PERSONS[person][0].split("/")
        accepted: tuple[str, ...] = (form,) + tuple(f"{s} {form}" for s in subj)
        canonical = form
    else:
        prompt = f'"{form}"   ({v.infinitive})'
        clauses = content.english_forms(v, tense, person)
        subject = content.PERSONS[person][1]
        bare = tuple(cl.split(" ", 1)[1] for cl in clauses)  # "had", "used to have"
        # Also accept "he/she had" for the third person, and the bare verb phrase.
        alt_subj = tuple(f"{subject} {b}" for b in bare) if "/" in subject else ()
        accepted = clauses + bare + alt_subj
        canonical = cue
    return Question(
        key=f"v:{v.infinitive}:{tense}:{person}",
        kind="verb",
        target_lang=target_lang,
        hint=f"{content.TENSE_LABEL[tense]} · {content.PERSONS[person][0]}",
        prompt=prompt,
        accepted=accepted,
        canonical=canonical,
        expansion=content.teaching_card(v, tense),
        origin_key=v.infinitive if v.infinitive in lineage.ORIGINS else "",
    )


# --------------------------------------------------------------------------
# Profile / scorecard
# --------------------------------------------------------------------------


@dataclass
class Profile:
    path: Path = DEFAULT_PROFILE
    wins: int = 0
    losses: int = 0
    close_calls: int = 0
    streak: int = 0
    best_streak: int = 0
    xp: int = 0
    rounds: int = 0
    started: float = field(default_factory=time.time)
    # item key -> {"en": hits, "es": hits, "miss": total misses}
    items: dict[str, dict[str, int]] = field(default_factory=dict)
    # production language -> [attempts, hits]
    lang_record: dict[str, list[int]] = field(
        default_factory=lambda: {"en": [0, 0], "es": [0, 0]}
    )
    unlocked_level: int = 1
    # Lineage entries and sound-law patterns the player has been shown.
    discovered: list[str] = field(default_factory=list)
    patterns_seen: list[str] = field(default_factory=list)

    # -- persistence ------------------------------------------------------
    @classmethod
    def load(cls, path: Path = DEFAULT_PROFILE) -> "Profile":
        if not path.exists():
            return cls(path=path)
        try:
            raw = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return cls(path=path)
        raw.pop("path", None)
        known = {f for f in cls.__dataclass_fields__ if f != "path"}
        return cls(path=path, **{k: v for k, v in raw.items() if k in known})

    def save(self) -> None:
        data = {k: v for k, v in self.__dict__.items() if k != "path"}
        try:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except OSError:
            pass  # a read-only home should never cost you a game

    # -- derived stats ----------------------------------------------------
    def accuracy(self, lang: str) -> float:
        attempts, hits = self.lang_record[lang]
        # Unseen languages start at a neutral 0.5 so neither is starved early.
        return hits / attempts if attempts >= 3 else 0.5

    def weakest_lang(self) -> str:
        return min(DIRECTIONS, key=self.accuracy)

    def es_bias(self) -> float:
        """P(next question demands Spanish). Density follows the weaker side."""
        en_acc, es_acc = self.accuracy("en"), self.accuracy("es")
        # Error mass per side, floored so the strong side never disappears.
        en_err, es_err = max(1 - en_acc, 0.12), max(1 - es_acc, 0.12)
        return min(0.85, max(0.15, es_err / (en_err + es_err)))

    def understood(self) -> int:
        """Words solid in BOTH directions — the 'agreed understood' counter."""
        return sum(
            1
            for k, rec in self.items.items()
            if k.startswith("w:")
            and rec.get("en", 0) >= SOLID_HITS
            and rec.get("es", 0) >= SOLID_HITS
        )

    def verbs_drilled(self) -> int:
        return len({k.split(":")[1] for k in self.items if k.startswith("v:")})

    def rank(self) -> str:
        for threshold, name in (
            (12000, "Nativo Honorario"),
            (6000, "Conversador"),
            (2500, "Se Defiende"),
            (900, "Turista Valiente"),
            (250, "Menú y Sonrisas"),
            (0, "Recién Llegado"),
        ):
            if self.xp >= threshold:
                return name
        return "Recién Llegado"

    # -- recording --------------------------------------------------------
    def record(self, q: Question, result: str) -> int:
        """Update the scorecard. Returns XP earned for this answer."""
        self.rounds += 1
        rec = self.items.setdefault(q.key, {"en": 0, "es": 0, "miss": 0})
        attempts, hits = self.lang_record[q.target_lang]
        self.lang_record[q.target_lang] = [attempts + 1, hits + (result == "hit")]

        if result == "hit":
            self.wins += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            rec[q.target_lang] = rec.get(q.target_lang, 0) + 1
            gained = 10 + min(self.streak, 10) * 2 + (5 if q.kind == "verb" else 0)
        elif result == "close":
            self.close_calls += 1
            self.streak = max(self.streak, 0)  # a near miss doesn't break the chain
            gained = 4
        else:
            self.losses += 1
            self.streak = 0
            rec["miss"] = rec.get("miss", 0) + 1
            rec[q.target_lang] = max(0, rec.get(q.target_lang, 0) - 1)
            gained = 0

        self.xp += gained
        self.unlocked_level = 1 + min(2, self.understood() // 12)
        return gained


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------


class Selector:
    """Picks the next question: weak language first, then weak items."""

    def __init__(self, profile: Profile, rng: random.Random | None = None,
                 verb_share: float = 0.4) -> None:
        self.p = profile
        self.rng = rng or random.Random()
        self.verb_share = verb_share
        self._recent: list[str] = []

    def _weight(self, key: str, lang: str, base: float) -> float:
        rec = self.p.items.get(key)
        if rec is None:
            return base * 1.6  # unseen material is interesting
        solid = rec.get(lang, 0)
        misses = rec.get("miss", 0)
        w = base * (1 + 1.4 * misses) / (1 + solid)
        if solid >= SOLID_HITS and misses == 0:
            w *= 0.25  # mastered: keep it in rotation, quietly
        return max(w, 0.05)

    def next(self) -> Question:
        lang = "es" if self.rng.random() < self.p.es_bias() else "en"
        for _ in range(8):  # avoid immediate repeats without looping forever
            q = self._pick(lang)
            if q.key not in self._recent[-5:]:
                break
        self._recent.append(q.key)
        return q

    def _pick(self, lang: str) -> Question:
        if self.rng.random() < self.verb_share:
            return self._pick_verb(lang)
        return self._pick_word(lang)

    def _pick_word(self, lang: str) -> Question:
        pool = [w for w in WORDS if w.level <= self.p.unlocked_level]
        weights = [self._weight(f"w:{w.en}", lang, 1.0) for w in pool]
        w = self.rng.choices(pool, weights=weights, k=1)[0]
        return word_question(w, lang)

    def _pick_verb(self, lang: str) -> Question:
        pool = [v for v in VERBS if v.level <= self.p.unlocked_level]
        tenses = ("present",) if self.p.unlocked_level == 1 else content.TENSES
        cands: list[tuple[Verb, str, int]] = [
            (v, t, i) for v in pool for t in tenses for i in range(6)
            if not (i == 4 and self.rng.random() < 0.7)  # vosotros: rare on purpose
        ]
        weights = [
            self._weight(f"v:{v.infinitive}:{t}:{i}", lang, 1.0) for v, t, i in cands
        ]
        v, t, i = self.rng.choices(cands, weights=weights, k=1)[0]
        return verb_question(v, t, i, lang)
