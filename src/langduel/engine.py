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

from . import aiid, content, judges, lineage
from .content import VERBS, WORDS, Verb, Word
from .judges import Verdict, edit_distance, fold  # re-exported for callers

DEFAULT_PROFILE = Path.home() / ".langduel.json"

# Bump when the saved shape changes. A profile written by a different app —
# mirror/duelo.py shares nine key names with this one — must never be loaded
# and silently rewritten with its unknown fields dropped.
SCHEMA = "langduel/2"

# How many clean hits in ONE direction before that direction counts as solid.
SOLID_HITS = 2
# A word is "understood" (scorecard counter) once both directions are solid.
DIRECTIONS = ("en", "es")

# Domains supply items and name their own production poles. Language happens to
# have two poles that are languages; the aiid domain's poles are spot / act.
DOMAINS = {"es": ("en", "es"), "aiid": aiid.POLES}
ALL_POLES = tuple(pole for poles in DOMAINS.values() for pole in poles)


class ForeignProfile(Exception):
    """Raised when a save file was written by something that is not this app."""


# Progressive disclosure. A new player gets word pairs and nothing else; the
# rest of the app arrives as they play, so the first screen stays small.
#
# Thresholds are ANSWERS GIVEN, not mastery. Gating features on mastery was a
# mistake: "words understood" needs four correct answers on one word (twice in
# each direction) and so sits at zero for a long time, which pushed the good
# parts of the app absurdly far away. You unlock the app by playing it.
STAGES: tuple[tuple[str, int, str], ...] = (
    ("words",   0,  "word pairs, both directions"),
    ("verbs",   5,  "+ verbs in the present tense"),
    ("lineage", 12, "+ where the words come from, and the sound laws"),
    ("tenses",  40, "+ the past tenses, and the harder vocabulary"),
    ("latin",   70, "+ the Latin ancestor shown on every card it applies to"),
)


# --------------------------------------------------------------------------
# Grading — see judges.py for the implementations
# --------------------------------------------------------------------------

def grade(answer: str, accepted: tuple[str, ...]) -> str:
    """The original grader, kept as a shorthand for the tolerant judge."""
    return judges.tolerant(answer, accepted).result


# --------------------------------------------------------------------------
# Questions
# --------------------------------------------------------------------------


@dataclass
class Question:
    key: str  # stable item id, e.g. "w:water" or "v:tener:present:1"
    kind: str  # "word" | "verb"
    target_lang: str  # the production pole: "en"/"es", or "spot"/"act"
    prompt: str  # what we show
    hint: str  # tag / tense label shown under the prompt
    accepted: tuple[str, ...]
    canonical: str  # the answer we print when they miss
    expansion: list[str] = field(default_factory=list)  # teaching card, verbs only
    origin_key: str = ""  # index into lineage.ORIGINS, "" when we have nothing
    domain: str = "es"
    judge: str = "tolerant"
    options: tuple[str, ...] = ()   # choice questions only
    faces: dict[str, str] = field(default_factory=dict)  # display-only, never graded
    why: str = ""                   # explanation shown after answering

    def decide(self, answer: str) -> Verdict:
        return judges.BY_NAME[self.judge](answer, self.accepted, self.options)

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


def aiid_question(idx: int, d: aiid.Drill) -> Question:
    """A pick-one safety drill. Graded by choice, explained either way."""
    return Question(
        key=f"a:{d.pole}:{idx}",
        kind="aiid",
        target_lang=d.pole,
        prompt=d.prompt,
        hint=aiid.POLE_LABEL[d.pole] + (f" · {d.tag}" if d.tag else ""),
        accepted=(d.answer,),
        canonical=d.answer,
        domain="aiid",
        judge="choice",
        options=d.options,
        why=d.why,
    )


def latin_face(q: Question) -> dict[str, str]:
    """The unjudged third face: the ancestor both sides descend from."""
    o = q.origin
    if o is None:
        return {}
    lang, head = o.ancestor()
    return {lang.lower(): head} if head else {}


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
    # production pole -> [attempts, hits]. Language is one axis among several.
    axis_record: dict[str, list[int]] = field(
        default_factory=lambda: {pole: [0, 0] for pole in ALL_POLES}
    )
    schema: str = SCHEMA
    unlocked_level: int = 1
    # Lineage entries and sound-law patterns the player has been shown.
    discovered: list[str] = field(default_factory=list)
    patterns_seen: list[str] = field(default_factory=list)
    # High-water mark. A feature that has ever been switched on never switches
    # back off — thresholds can be retuned without taking things away from
    # someone mid-game.
    stage_floor: int = 0
    # Runtime only, never saved: pins the app to an earlier stage so the
    # stripped-back early game stays playable at any level of progress.
    cap: int | None = None

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

        found = raw.get("schema")
        if found is None and "ladder_progress" in raw:
            # mirror/duelo.py's shape: nine key names in common, different meaning.
            raise ForeignProfile(
                f"{path} was written by another app (duelo). Refusing to load it — "
                "saving would drop its fields. Use --profile to pick a different file."
            )
        if found not in (None, SCHEMA):
            raise ForeignProfile(f"{path} has schema {found!r}, this app writes {SCHEMA!r}.")

        # v1 → v2: the language record became a general axis record.
        if "lang_record" in raw and "axis_record" not in raw:
            raw["axis_record"] = raw.pop("lang_record")
        raw["schema"] = SCHEMA
        if raw.get("stage_floor") is None and (raw.get("discovered")
                                               or raw.get("patterns_seen")):
            # Played before stages existed — do not take the lineage away.
            raw["stage_floor"] = 2

        known = {f for f in cls.__dataclass_fields__ if f not in ("path", "cap")}
        p = cls(path=path, **{k: v for k, v in raw.items() if k in known})
        for pole in ALL_POLES:                       # new poles start empty
            p.axis_record.setdefault(pole, [0, 0])
        return p

    def save(self) -> None:
        data = {k: v for k, v in self.__dict__.items() if k not in ("path", "cap")}
        try:
            self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except OSError:
            pass  # a read-only home should never cost you a game

    # -- derived stats ----------------------------------------------------
    def accuracy(self, pole: str) -> float:
        attempts, hits = self.axis_record.get(pole, [0, 0])
        # Unseen poles start at a neutral 0.5 so neither is starved early.
        return hits / attempts if attempts >= 3 else 0.5

    def weakest(self, domain: str = "es") -> str:
        return min(DOMAINS[domain], key=self.accuracy)

    def weakest_lang(self) -> str:
        return self.weakest("es")

    def pole_bias(self, domain: str = "es") -> float:
        """P(next question uses the SECOND pole). Density follows the weaker side."""
        a, b = DOMAINS[domain]
        # Error mass per side, floored so the strong side never disappears.
        err_a, err_b = max(1 - self.accuracy(a), 0.12), max(1 - self.accuracy(b), 0.12)
        return min(0.85, max(0.15, err_b / (err_a + err_b)))

    def es_bias(self) -> float:
        return self.pole_bias("es")

    # -- progressive disclosure -------------------------------------------
    def stage(self) -> int:
        """How much of the app is switched on."""
        reached = max(i for i, (_, need, _) in enumerate(STAGES) if self.rounds >= need)
        reached = max(reached, self.stage_floor)
        return reached if self.cap is None else min(reached, self.cap)

    def stage_name(self) -> str:
        return STAGES[self.stage()][0]

    def has(self, feature: str) -> bool:
        return self.stage() >= [s[0] for s in STAGES].index(feature)

    def next_unlock(self) -> tuple[str, int] | None:
        for name, need, blurb in STAGES[self.stage() + 1:]:
            return blurb, need - self.rounds
        return None

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
        attempts, hits = self.axis_record.setdefault(q.target_lang, [0, 0])
        self.axis_record[q.target_lang] = [attempts + 1, hits + (result == "hit")]

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
        if self.cap is None:
            self.stage_floor = max(self.stage_floor, self.stage())
        return gained


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------


class Selector:
    """Picks the next question: weak domain pole first, then weak items.

    The two-level draw is the point. The outer draw is the production pole, so
    the app keeps asking for whatever you are worse at *producing*; the inner
    draw is the item, weighted by your history with it. Anything added later —
    spaced repetition, new domains — belongs in the inner weight, not as a
    replacement for the outer draw, or the density mechanic quietly dies.
    """

    def __init__(self, profile: Profile, rng: random.Random | None = None,
                 verb_share: float = 0.4, domains: tuple[str, ...] = ("es",),
                 aiid_share: float = 0.25) -> None:
        self.p = profile
        self.rng = rng or random.Random()
        self.verb_share = verb_share
        self.domains = domains
        self.aiid_share = aiid_share
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
        domain = "es"
        if "aiid" in self.domains and (
                self.domains == ("aiid",) or self.rng.random() < self.aiid_share):
            domain = "aiid"
        poles = DOMAINS[domain]
        pole = poles[1] if self.rng.random() < self.p.pole_bias(domain) else poles[0]

        for _ in range(8):  # avoid immediate repeats without looping forever
            q = self._pick(domain, pole)
            if q.key not in self._recent[-6:]:
                break
        self._recent.append(q.key)
        return q

    def _pick(self, domain: str, pole: str) -> Question:
        if domain == "aiid":
            return self._pick_aiid(pole)
        # Verbs stay locked until the player has earned them.
        if self.p.has("verbs") and self.rng.random() < self.verb_share:
            return self._pick_verb(pole)
        return self._pick_word(pole)

    def _pick_aiid(self, pole: str) -> Question:
        pool = [(i, d) for i, d in enumerate(aiid.DRILLS)
                if d.pole == pole and d.level <= self.p.unlocked_level + 1]
        weights = [self._weight(f"a:{d.pole}:{i}", pole, 1.0) for i, d in pool]
        i, d = self.rng.choices(pool, weights=weights, k=1)[0]
        return aiid_question(i, d)

    def _pick_word(self, lang: str) -> Question:
        pool = [w for w in WORDS if w.level <= self.p.unlocked_level]
        weights = [self._weight(f"w:{w.en}", lang, 1.0) for w in pool]
        w = self.rng.choices(pool, weights=weights, k=1)[0]
        return word_question(w, lang)

    def _pick_verb(self, lang: str) -> Question:
        pool = [v for v in VERBS if v.level <= self.p.unlocked_level]
        tenses = content.TENSES if self.p.has("tenses") else ("present",)
        cands: list[tuple[Verb, str, int]] = [
            (v, t, i) for v in pool for t in tenses for i in range(6)
            if not (i == 4 and self.rng.random() < 0.7)  # vosotros: rare on purpose
        ]
        weights = [
            self._weight(f"v:{v.infinitive}:{t}:{i}", lang, 1.0) for v, t, i in cands
        ]
        v, t, i = self.rng.choices(cands, weights=weights, k=1)[0]
        return verb_question(v, t, i, lang)
