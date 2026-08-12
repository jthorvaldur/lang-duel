"""Game state, spaced-repetition scheduling, question building, and selection.

No printing happens here — the CLI owns all I/O so this stays testable.
Content comes from a Pack (see content.py); rules and mechanics live here.
"""

from __future__ import annotations

import json
import random
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .content import (PERSONS, TENSE_LABEL, TENSES, Cloze, Opponent, Pack, Trap,
                      Verb, Word, english_cue)

DEFAULT_SAVE = Path(__file__).resolve().parents[1] / "save.json"
SOLID_HITS = 2  # clean hits per direction before a word counts as "dominada"
# Leitner schedule by box: 0 = due now, then 10 min, 1 h, 1 d, 3 d, 7 d.
INTERVALS = (0, 600, 3600, 86400, 259200, 604800)

TENSE_BY_TIER = {1: ("present",), 2: ("present", "preterite"), 3: TENSES}
SENTENCE_SHARE = 0.12  # wheel share once the map has ingredients

# --------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------

_STRIP_LEAD = ("the ", "a ", "an ", "to ", "el ", "la ", "los ", "las ", "un ", "una ")


def fold(text: str) -> str:
    """Lowercase, strip accents/punctuation/articles — 'como estas' passes."""
    t = unicodedata.normalize("NFD", text.lower().strip())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t)
    t = " ".join(t.split())
    for lead in _STRIP_LEAD:
        if t.startswith(lead):
            return t[len(lead):]
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
    """'hit', 'close' (typo/accent slip) or 'miss'."""
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
    key: str                 # stable id: "w:water" / "v:tener:present:1" / "c:3"
    kind: str                # word | verb | cloze | trap | gender | num | sentence
    target_lang: str         # language the player must produce
    prompt: str
    sub: str                 # small line under the prompt
    accepted: tuple[str, ...]
    canonical: str
    teach: list[str] = field(default_factory=list)
    # item keys that also get a +1 when this question is answered correctly —
    # using "pan" inside a fresh sentence still feeds its map entry
    also_credit: tuple[str, ...] = ()


def word_question(w: Word, lang: str) -> Question:
    return Question(
        key=f"w:{w.en}", kind="word", target_lang=lang,
        prompt=w.en if lang == "es" else w.es,
        sub=w.tag,
        accepted=w.accepted(lang),
        canonical=w.es if lang == "es" else w.en,
    )


def conjugation_card(v: Verb, tense: str) -> list[str]:
    forms = v.conjugate(tense)
    lines = [f"{v.infinitive} — {v.en} · {TENSE_LABEL[tense]}"]
    for (es_p, en_p), form in zip(PERSONS, forms):
        lines.append(f"   {es_p:<11} {form:<13} {en_p}")
    if v.note:
        lines.append(f"   note: {v.note}")
    return lines


def verb_question(v: Verb, tense: str, person: int, lang: str) -> Question:
    form = v.conjugate(tense)[person]
    if lang == "es":
        prompt = f'"{english_cue(v, tense, person)}"  →  {v.infinitive}'
        accepted = (form,)
    else:
        # One Spanish form can map to several persons ("hablaba" = yo/él).
        # Accept the English cue for every person that shares the form.
        forms = v.conjugate(tense)
        accepted = tuple(
            cue
            for i, f in enumerate(forms)
            if fold(f) == fold(form)
            for cue in ([english_cue(v, tense, i)] +
                        ([english_cue(v, tense, i).replace("he ", "she ", 1)]
                         if i == 2 else []))
        )
        prompt = f'"{form}"  ({v.infinitive})'
    return Question(
        key=f"v:{v.infinitive}:{tense}:{person}", kind="verb", target_lang=lang,
        prompt=prompt,
        sub=f"{TENSE_LABEL[tense]} · {PERSONS[person][0]}",
        accepted=accepted,
        canonical=form if lang == "es" else accepted[0],
        teach=conjugation_card(v, tense),
    )


def cloze_question(idx: int, c: Cloze) -> Question:
    teach = [f"{c.text.replace('___', c.answer)}  —  {c.en}"]
    if c.note:
        teach.append(f"   note: {c.note}")
    return Question(
        key=f"c:{idx}", kind="cloze", target_lang="es",
        prompt=c.text, sub=f"«{c.en}»",
        accepted=(c.answer,) + c.alts,
        canonical=c.answer,
        teach=teach,
    )


def trap_question(idx: int, t: Trap, rng: random.Random) -> Question:
    order = [0, 1]
    rng.shuffle(order)
    shown = [t.options[i] for i in order]
    right = t.options[t.correct]
    pos = shown.index(right) + 1  # 1-based, as printed
    return Question(
        key=f"t:{idx}", kind="trap", target_lang="es",
        prompt=t.text,
        sub=f"¿{t.pair}?   1) {shown[0]}   2) {shown[1]}",
        accepted=(right, str(pos)),
        canonical=right,
        teach=[f"{t.text.replace('___', right)}  —  {t.why}"],
    )


def gender_question(w: Word) -> Question:
    teach = [f"{w.article} {w.es}" + (f"  —  {w.article_note}" if w.article_note else "")]
    return Question(
        key=f"g:{w.en}", kind="gender", target_lang="es",
        prompt=f"___ {w.es}", sub="¿el o la?",
        accepted=(w.article, f"{w.article} {w.es}"),
        canonical=w.article,
        teach=teach,
        also_credit=(f"w:{w.en}",),
    )


# -- numbers, prices, time --------------------------------------------------

_NUM_UNITS = ("cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
              "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince")
_NUM_16_19 = ("dieciséis", "diecisiete", "dieciocho", "diecinueve")
_NUM_20S = ("veinte", "veintiún", "veintidós", "veintitrés", "veinticuatro",
            "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve")
_NUM_TENS = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
             70: "setenta", 80: "ochenta", 90: "noventa"}


def num_es(n: int) -> str:
    """0-99 in Spanish — enough for prices, times and small change."""
    if n < 16:
        return _NUM_UNITS[n]
    if n < 20:
        return _NUM_16_19[n - 16]
    if n < 30:
        return _NUM_20S[n - 20]
    tens, rest = divmod(n, 10)
    return _NUM_TENS[tens * 10] if rest == 0 else f"{_NUM_TENS[tens * 10]} y {num_es(rest)}"


def _un_variant(s: str) -> str | None:
    """uno -> un before a masculine noun ('treinta y un pesos')."""
    if s == "uno":
        return "un"
    if s.endswith(" y uno"):
        return s[:-1]
    return None


def time_es(h: int, m: int) -> tuple[str, tuple[str, ...]]:
    """Canonical Spanish clock time plus accepted shorter forms."""
    if m == 45:
        h = h % 12 + 1
        lead = "Es la" if h == 1 else "Son las"
        hw = "una" if h == 1 else num_es(h)
        full = f"{lead} {hw} menos cuarto"
        return full, (full, f"{hw} menos cuarto")
    lead = "Es la" if h == 1 else "Son las"
    hw = "una" if h == 1 else num_es(h)
    tail = {0: "en punto", 15: "y cuarto", 30: "y media"}[m]
    full = f"{lead} {hw} {tail}"
    variants = [full, f"{hw} {tail}"]
    if m == 0:
        variants += [f"{lead} {hw}", hw]
    return full, tuple(variants)


def num_question(rng: random.Random, lang: str) -> Question:
    roll = rng.random()
    if roll < 0.45:  # plain number, both directions
        n = rng.randint(1, 99)
        if lang == "es":
            accepted = (num_es(n),)
            alt = _un_variant(num_es(n))
            if alt:
                accepted += (alt,)
            return Question(
                key=f"n:{n}", kind="num", target_lang="es",
                prompt=str(n), sub="escríbelo en español",
                accepted=accepted, canonical=num_es(n))
        return Question(
            key=f"n:{num_es(n)}", kind="num", target_lang="en",
            prompt=num_es(n), sub="write the number",
            accepted=(str(n),), canonical=str(n))
    if roll < 0.72:  # the market price
        n = rng.randint(2, 99)
        accepted = (num_es(n),)
        alt = _un_variant(num_es(n))
        if alt:
            accepted += (alt,)
        return Question(
            key=f"n:p:{n}", kind="num", target_lang="es",
            prompt="— ¿Cuánto cuesta? — Cuesta ___ pesos.",
            sub=f"«It costs {n} pesos.»",
            accepted=accepted, canonical=num_es(n),
            teach=[f"Cuesta {num_es(n)} pesos.  —  It costs {n} pesos."])
    # telling time
    h, m = rng.randint(1, 12), rng.choice((0, 15, 30, 45))
    full, variants = time_es(h, m)
    clock = f"{h}:{m:02d}"
    if lang == "es":
        return Question(
            key=f"n:t:{clock}", kind="num", target_lang="es",
            prompt=f"🕒 {clock}", sub="dilo en español",
            accepted=variants, canonical=full)
    return Question(
        key=f"n:t:{full}", kind="num", target_lang="en",
        prompt=f'"{full}"', sub="what time is it? (h:mm)",
        accepted=(clock,), canonical=clock)


# -- generated sentences ----------------------------------------------------

_SUBJECTS = (("yo", "I", 0), ("tú", "you", 1), ("él", "he", 2),
             ("nosotros", "we", 3), ("ellos", "they", 5))


def sentence_ready(pack: Pack, p: "Profile", opp: Opponent) -> bool:
    dom = set(p.dominated())
    if any(k in dom for k in pack.places):
        return True
    verbs = pack.verbs_by_name
    return any(
        w in dom
        for v, comps in pack.pairs.items()
        if v in verbs and verbs[v].tier <= opp.tier
        for w in comps
    )


def sentence_question(pack: Pack, p: "Profile", opp: Opponent, lang: str,
                      rng: random.Random) -> Question | None:
    """Compose a fresh sentence only from words the map already holds."""
    dom = set(p.dominated())
    verbs = pack.verbs_by_name
    moves = [(v, w) for v, comps in pack.pairs.items()
             if v in verbs and verbs[v].tier <= opp.tier
             for w in comps if w in dom]
    places = [k for k in pack.places if k in dom]
    if not moves and not places:
        return None

    sub_line = "every word here is already yours — new situation"

    if places and (not moves or rng.random() < 0.25):
        key = rng.choice(places)
        es_phrase, en_phrase = pack.places[key]
        es = f"¿Dónde está {es_phrase}?"
        en = f"Where is {en_phrase}?"
        accepted_es = (es, es.replace("¿Dónde", "Dónde"), f"dónde está {es_phrase}")
        accepted_en = (en, f"Where's {en_phrase}?", f"Where's {en_phrase}")
        return Question(
            key=f"s:{es}", kind="sentence", target_lang=lang,
            prompt=f'"{en}"' if lang == "es" else f'"{es}"',
            sub=sub_line,
            accepted=accepted_es if lang == "es" else accepted_en,
            canonical=es if lang == "es" else en,
            teach=[f"{es}  —  {en}"],
            also_credit=(f"w:{key}",))

    vname, comp_en = rng.choice(moves)
    verb = verbs[vname]
    comp = pack.words_by_en[comp_en]
    subj_es, subj_en, pi = rng.choice(_SUBJECTS)
    form = verb.conjugate("present")[pi]
    base, third, _ = verb.english()
    neg = rng.random() < 0.3
    if neg:
        es = f"{subj_es} no {form} {comp.es}"
        aux = "doesn't" if pi == 2 else "don't"
        en = f"{subj_en} {aux} {base} {comp.en}"
    else:
        es = f"{subj_es} {form} {comp.es}"
        en = f"{subj_en} {third if pi == 2 else base} {comp.en}"
    bare = es.split(" ", 1)[1]  # drop the pronoun — always legal in Spanish
    accepted_es = [es, bare]
    if comp.es_alts:
        accepted_es += [es.replace(comp.es, comp.es_alts[0]),
                        bare.replace(comp.es, comp.es_alts[0])]
    accepted_en = [en]
    if pi == 2:  # él hides ella
        accepted_en += [en.replace("he ", "she ", 1), en.replace("He ", "She ", 1)]
    return Question(
        key=f"s:{es}", kind="sentence", target_lang=lang,
        prompt=f'"{en}"' if lang == "es" else f'"{es}"',
        sub=sub_line,
        accepted=tuple(accepted_es) if lang == "es" else tuple(accepted_en),
        canonical=es if lang == "es" else en,
        teach=[f"{es}  —  {en}"],
        also_credit=(f"w:{comp.en}", f"v:{vname}:present:{pi}"),
    )


# --------------------------------------------------------------------------
# Profile / scorecard
# --------------------------------------------------------------------------


@dataclass
class Profile:
    path: Path = DEFAULT_SAVE
    wins: int = 0
    losses: int = 0
    close_calls: int = 0
    streak: int = 0
    best_streak: int = 0
    xp: int = 0
    ladder_progress: int = 0      # opponents put on the canvas, all time
    started: float = field(default_factory=time.time)
    # item key -> {"en": hits, "es": hits, "miss": misses, "box": int, "due": ts}
    items: dict[str, dict[str, int]] = field(default_factory=dict)
    # production language -> [attempts, hits]
    lang_record: dict[str, list[int]] = field(
        default_factory=lambda: {"en": [0, 0], "es": [0, 0]})

    # -- persistence ---------------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> "Profile":
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
            pass

    # -- the language most wrong → question density ---------------------------
    def accuracy(self, lang: str) -> float:
        attempts, hits = self.lang_record[lang]
        return (hits + 1) / (attempts + 2)  # Laplace prior: 0.5 when unseen

    def es_bias(self) -> float:
        """P(next question demands Spanish). Error mass decides the mix."""
        en_err = max(1 - self.accuracy("en"), 0.12)
        es_err = max(1 - self.accuracy("es"), 0.12)
        return min(0.85, max(0.15, es_err / (en_err + es_err)))

    # -- the "agreed understood" counter --------------------------------------
    def dominated(self) -> list[str]:
        """Words solid in BOTH directions — both sides agree you own them."""
        return sorted(
            k[2:] for k, rec in self.items.items()
            if k.startswith("w:")
            and rec.get("en", 0) >= SOLID_HITS
            and rec.get("es", 0) >= SOLID_HITS
        )

    def due_now(self) -> int:
        now = time.time()
        return sum(1 for r in self.items.values() if 0 < r.get("due", 0) <= now)

    def scheduled_ahead(self) -> int:
        now = time.time()
        return sum(1 for r in self.items.values() if r.get("due", 0) > now)

    def rank(self) -> str:
        for threshold, name in (
            (2400, "Leyenda del Barrio"),
            (1400, "Campeón Nacional"),
            (800, "Peso Medio"),
            (400, "Peso Pluma"),
            (150, "Cinturón de Barrio"),
            (0, "Novato del Ring"),
        ):
            if self.xp >= threshold:
                return name
        return "Novato del Ring"

    # -- recording -------------------------------------------------------------
    def record(self, q: Question, result: str) -> int:
        rec = self.items.setdefault(q.key, {"en": 0, "es": 0, "miss": 0})
        attempts, hits = self.lang_record[q.target_lang]
        self.lang_record[q.target_lang] = [attempts + 1, hits + (result == "hit")]
        box = rec.get("box", 0)
        if result == "hit":
            self.wins += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            rec[q.target_lang] = rec.get(q.target_lang, 0) + 1
            for k in q.also_credit:  # feeding the map from new situations
                cr = self.items.setdefault(k, {"en": 0, "es": 0, "miss": 0})
                cr[q.target_lang] = cr.get(q.target_lang, 0) + 1
            box = min(box + 1, len(INTERVALS) - 1)
            gained = 10 + min(self.streak, 10) * 2 + (5 if q.kind != "word" else 0)
        elif result == "close":
            self.close_calls += 1  # a shave keeps the streak, pays less
            gained = 4
        else:
            self.losses += 1
            self.streak = 0
            rec["miss"] = rec.get("miss", 0) + 1
            rec[q.target_lang] = max(0, rec.get(q.target_lang, 0) - 1)
            box = 0
            gained = 0
        # Leitner: a hit pushes the next review further out, a miss pulls it close
        rec["box"] = box
        rec["due"] = time.time() + (INTERVALS[1] if result == "miss" else INTERVALS[box])
        self.xp += gained
        return gained


# --------------------------------------------------------------------------
# Selection: weak language first, then weak items, due reviews first of all
# --------------------------------------------------------------------------


class Selector:
    def __init__(self, pack: Pack, profile: Profile, rng: random.Random) -> None:
        self.pack = pack
        self.p = profile
        self.rng = rng
        self._recent: list[str] = []

    def _weight(self, key: str, lang: str) -> float:
        rec = self.p.items.get(key)
        if rec is None:
            return 1.7  # unseen material is interesting
        w = (1 + 1.3 * rec.get("miss", 0)) / (1 + 0.9 * rec.get(lang, 0))
        if (rec.get("en", 0) >= SOLID_HITS and rec.get("es", 0) >= SOLID_HITS
                and rec.get("miss", 0) == 0):
            w *= 0.15  # dominada: stays in rotation, quietly
        due = rec.get("due", 0)
        now = time.time()
        if due > now:
            w *= 0.04  # scheduled ahead — leave it for later
        elif due and rec.get("box", 0) >= 2:
            w *= 2.5  # a real review comes due — jump the queue
        return max(w, 0.05)

    def next(self, opp: Opponent) -> Question:
        for _ in range(8):  # avoid immediate repeats, never loop forever
            lang = "es" if self.rng.random() < self.p.es_bias() else "en"
            q = self._pick(lang, opp)
            if q.key not in self._recent[-5:]:
                break
        self._recent.append(q.key)
        return q

    def _pick(self, lang: str, opp: Opponent) -> Question:
        # Each kind owns a share of the wheel; vocab takes what is left.
        # Spanish-only kinds (cloze/trap/gender) roll over to vocab en→en.
        shares: list[tuple[float, Callable[[], Question]]] = [
            (opp.verb_share, lambda: self._pick_verb(lang, opp)),
            (opp.num_share, lambda: num_question(self.rng, lang)),
        ]
        if lang == "es":
            shares += [
                (opp.cloze_share, lambda: self._pick_cloze(opp)),
                (opp.trap_share, lambda: self._pick_trap(opp)),
                (opp.gender_share, lambda: self._pick_gender(opp)),
            ]
        if sentence_ready(self.pack, self.p, opp):
            shares.append((SENTENCE_SHARE, lambda: self._pick_sentence(lang, opp)))
        roll = self.rng.random()
        acc = 0.0
        for share, fn in shares:
            acc += share
            if roll < acc:
                return fn()
        return self._pick_word(lang, opp)

    def _pick_word(self, lang: str, opp: Opponent) -> Question:
        pool = [w for w in self.pack.words if w.tier <= opp.tier]
        weights = [self._weight(f"w:{w.en}", lang) for w in pool]
        return word_question(self.rng.choices(pool, weights=weights, k=1)[0], lang)

    def _pick_verb(self, lang: str, opp: Opponent) -> Question:
        pool = [v for v in self.pack.verbs if v.tier <= opp.tier]
        tenses = TENSE_BY_TIER[opp.tier]
        cands = [
            (v, t, i) for v in pool for t in tenses for i in (0, 1, 2, 3, 5)
            if t != "imperfect" or v.imperfect_ok
        ]
        weights = [self._weight(f"v:{v.infinitive}:{t}:{i}", lang) for v, t, i in cands]
        v, t, i = self.rng.choices(cands, weights=weights, k=1)[0]
        return verb_question(v, t, i, lang)

    def _pick_cloze(self, opp: Opponent) -> Question:
        pool = [(i, c) for i, c in enumerate(self.pack.clozes) if c.tier <= opp.tier]
        weights = [self._weight(f"c:{i}", "es") for i, _ in pool]
        i, c = self.rng.choices(pool, weights=weights, k=1)[0]
        return cloze_question(i, c)

    def _pick_trap(self, opp: Opponent) -> Question:
        pool = [(i, t) for i, t in enumerate(self.pack.traps) if t.tier <= opp.tier]
        weights = [self._weight(f"t:{i}", "es") for i, _ in pool]
        i, t = self.rng.choices(pool, weights=weights, k=1)[0]
        return trap_question(i, t, self.rng)

    def _pick_gender(self, opp: Opponent) -> Question:
        pool = [w for w in self.pack.words if w.article and w.tier <= opp.tier]
        weights = [self._weight(f"g:{w.en}", "es") for w in pool]
        return gender_question(self.rng.choices(pool, weights=weights, k=1)[0])

    def _pick_sentence(self, lang: str, opp: Opponent) -> Question:
        q = sentence_question(self.pack, self.p, opp, lang, self.rng)
        return q if q is not None else self._pick_word(lang, opp)
