#!/usr/bin/env python3
"""LUCHA LÉXICA — a mirror attempt at the base.md brief, next to src/langduel.

A terminal English⇄Spanish trainer dressed as a lucha libre ladder:
climb four opponents by landing answers. Every miss costs you HP.

The brief, point by point:
  * asks a question              → vocab, conjugation and fill-in-the-blank turns
  * alternates languages         → every item is asked en→es AND es→en
  * expands on verbs             → a full conjugation card after every verb turn
  * basic functional view        → cloze turns teach whole working sentences
  * density weighted to the      → next-question language mix follows the
    language most wrong            error mass of your weaker side (shown on the card)
  * scoring card                 → wins/losses, streaks, and "dominadas": words
                                   proven correct both ways, accumulated + repeated
  * spaced repetition            → Leitner boxes schedule every item into the
                                   future; due reviews jump the queue
  * classic traps                → ser/estar, por/para, saber/conocer and
                                   pretérito/imperfecto as forced choices
  * functional depth             → numbers, prices, telling time, gender, and
                                   fresh sentences generated from your dominadas
                                   (the map: old words in new situations)
  * make it fun                  → HP bars, combos, trash talk, seasons, ranks

No dependencies. Saves to save.json next to this script.
Run:  ./mirror/duelo.py   ·   flags: --rounds N --seed S --stats --reset
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

SAVE_PATH = Path(__file__).resolve().with_name("save.json")
PLAYER_HP = 10
SOLID_HITS = 2  # clean hits per direction before a word counts as "dominada"
# Leitner schedule by box: 0 = due now, then 10 min, 1 h, 1 d, 3 d, 7 d.
INTERVALS = (0, 600, 3600, 86400, 259200, 604800)

# --------------------------------------------------------------------------
# Content: vocabulary
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Word:
    en: str
    es: str
    tag: str
    es_alts: tuple[str, ...] = ()
    en_alts: tuple[str, ...] = ()
    tier: int = 1

    def accepted(self, lang: str) -> tuple[str, ...]:
        return (self.es,) + self.es_alts if lang == "es" else (self.en,) + self.en_alts


WORDS: tuple[Word, ...] = (
    # -- tier 1: survival ----------------------------------------------------
    Word("I", "yo", "pronoun"),
    Word("you", "tú", "pronoun", es_alts=("usted",)),
    Word("we", "nosotros", "pronoun", es_alts=("nosotras",)),
    Word("man", "hombre", "people", es_alts=("el hombre",)),
    Word("woman", "mujer", "people", es_alts=("la mujer",)),
    Word("friend", "amigo", "people", es_alts=("amiga",)),
    Word("water", "agua", "noun", es_alts=("el agua",)),
    Word("bread", "pan", "noun", es_alts=("el pan",)),
    Word("food", "comida", "noun", en_alts=("meal",), es_alts=("la comida",)),
    Word("house", "casa", "noun", en_alts=("home",), es_alts=("la casa", "hogar")),
    Word("money", "dinero", "noun", es_alts=("el dinero", "plata")),
    Word("day", "día", "noun", es_alts=("el día",)),
    Word("night", "noche", "noun", es_alts=("la noche",)),
    Word("here", "aquí", "glue", es_alts=("acá",)),
    Word("there", "allí", "glue", es_alts=("ahí", "allá")),
    Word("now", "ahora", "glue"),
    Word("today", "hoy", "glue"),
    Word("tomorrow", "mañana", "glue"),
    Word("with", "con", "glue"),
    Word("without", "sin", "glue"),
    Word("but", "pero", "glue"),
    Word("because", "porque", "glue"),
    Word("very", "muy", "glue"),
    Word("also", "también", "glue", en_alts=("too", "as well")),
    Word("always", "siempre", "glue"),
    # -- tier 2: everyday ----------------------------------------------------
    Word("child", "niño", "people", en_alts=("kid",), es_alts=("niña", "chico"), tier=2),
    Word("family", "familia", "people", es_alts=("la familia",), tier=2),
    Word("work", "trabajo", "noun", en_alts=("job",), es_alts=("el trabajo",), tier=2),
    Word("city", "ciudad", "noun", es_alts=("la ciudad",), tier=2),
    Word("street", "calle", "noun", es_alts=("la calle",), tier=2),
    Word("time", "tiempo", "noun", es_alts=("el tiempo", "vez"), tier=2),
    Word("book", "libro", "noun", es_alts=("el libro",), tier=2),
    Word("word", "palabra", "noun", es_alts=("la palabra",), tier=2),
    Word("good", "bueno", "adj", es_alts=("buena", "buen"), tier=2),
    Word("bad", "malo", "adj", es_alts=("mala", "mal"), tier=2),
    Word("big", "grande", "adj", en_alts=("large",), tier=2),
    Word("small", "pequeño", "adj", en_alts=("little",), es_alts=("pequeña",), tier=2),
    Word("new", "nuevo", "adj", es_alts=("nueva",), tier=2),
    Word("never", "nunca", "glue", es_alts=("jamás",), tier=2),
    Word("later", "después", "glue", en_alts=("afterwards",), es_alts=("luego",), tier=2),
    # -- tier 3: stretch -----------------------------------------------------
    Word("neighbor", "vecino", "people", es_alts=("vecina",), tier=3),
    Word("question", "pregunta", "noun", es_alts=("la pregunta",), tier=3),
    Word("mistake", "error", "noun", es_alts=("el error",), tier=3),
    Word("old", "viejo", "adj", es_alts=("vieja", "antiguo"), tier=3),
    Word("almost", "casi", "glue", tier=3),
    Word("still", "todavía", "glue", en_alts=("yet",), es_alts=("aún",), tier=3),
    Word("yesterday", "ayer", "glue", tier=3),
    Word("although", "aunque", "glue", en_alts=("even though",), tier=3),
)

# --------------------------------------------------------------------------
# Content: verbs & conjugation
# --------------------------------------------------------------------------

PERSONS: tuple[tuple[str, str], ...] = (
    ("yo", "I"),
    ("tú", "you"),
    ("él/ella", "he/she"),
    ("nosotros", "we"),
    ("vosotros", "you all"),
    ("ellos", "they"),
)

TENSES: tuple[str, ...] = ("present", "preterite", "imperfect")
TENSE_LABEL = {
    "present": "presente",
    "preterite": "pretérito (past, finished)",
    "imperfect": "imperfecto (used to)",
}
TENSE_BY_TIER = {1: ("present",), 2: ("present", "preterite"), 3: TENSES}

# Verbs whose English gloss survives "used to ___" — imperfect is only
# drawn from these (so we never print "used to can").
IMPERFECT_OK = {"hablar", "comer", "vivir", "beber", "trabajar", "necesitar",
                "aprender", "escribir", "ser", "ir", "entender"}

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


@dataclass(frozen=True)
class Verb:
    infinitive: str
    en: str                       # "to speak"
    gloss: str                    # "speak, talk" — first chunk is the cue base
    en_forms: tuple[str, str, str] = ()   # base / 3rd-person / past, if irregular
    irregular: dict[str, tuple[str, ...]] = field(default_factory=dict)
    note: str = ""
    tier: int = 1

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
            return self.en_forms
        base = self.gloss.split(",")[0].split("(")[0].strip()
        third = base + ("es" if base.endswith(("s", "sh", "ch", "x", "o")) else "s")
        past = base[:-1] + "d" if base.endswith("e") else base + "ed"
        return base, third, past


VERBS: tuple[Verb, ...] = (
    Verb("ser", "to be", "be (permanent: who/what you are)",
         en_forms=("be", "is", "was"),
         irregular={
             "present": ("soy", "eres", "es", "somos", "sois", "son"),
             "preterite": ("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
             "imperfect": ("era", "eras", "era", "éramos", "erais", "eran"),
         },
         note="ser = identity/origin/time. Preterite is identical to ir — context decides."),
    Verb("estar", "to be", "be (state/location: right now)",
         en_forms=("be", "is", "was"),
         irregular={
             "present": ("estoy", "estás", "está", "estamos", "estáis", "están"),
             "preterite": ("estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"),
         },
         note="estar = temporary states and places. 'Estoy cansado' vs 'Soy alto'."),
    Verb("tener", "to have", "have",
         en_forms=("have", "has", "had"),
         irregular={
             "present": ("tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"),
             "preterite": ("tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"),
         },
         note="e→ie in the boot. Idiom: tener hambre = to be hungry."),
    Verb("hablar", "to speak", "speak, talk"),
    Verb("comer", "to eat", "eat", en_forms=("eat", "eats", "ate")),
    Verb("vivir", "to live", "live"),
    Verb("ir", "to go", "go",
         en_forms=("go", "goes", "went"),
         irregular={
             "present": ("voy", "vas", "va", "vamos", "vais", "van"),
             "preterite": ("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
             "imperfect": ("iba", "ibas", "iba", "íbamos", "ibais", "iban"),
         },
         note="ir + a + infinitive = the easy future: 'voy a comer' = I'm going to eat.",
         tier=2),
    Verb("hacer", "to do / to make", "do, make",
         en_forms=("do", "does", "did"),
         irregular={
             "present": ("hago", "haces", "hace", "hacemos", "hacéis", "hacen"),
             "preterite": ("hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"),
         },
         note="hizo keeps the sound with a z.", tier=2),
    Verb("querer", "to want", "want",
         en_forms=("want", "wants", "wanted"),
         irregular={
             "present": ("quiero", "quieres", "quiere", "queremos", "queréis", "quieren"),
             "preterite": ("quise", "quisiste", "quiso", "quisimos", "quisisteis", "quisieron"),
         },
         note="e→ie in the boot. 'Quisiera' is the polite way to order.", tier=2),
    Verb("poder", "to be able / can", "can, be able to",
         en_forms=("can", "can", "could"),
         irregular={
             "present": ("puedo", "puedes", "puede", "podemos", "podéis", "pueden"),
             "preterite": ("pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"),
         },
         note="o→ue in the boot.", tier=2),
    Verb("beber", "to drink", "drink", en_forms=("drink", "drinks", "drank"), tier=2),
    Verb("trabajar", "to work", "work", tier=2),
    Verb("necesitar", "to need", "need", tier=2),
    Verb("aprender", "to learn", "learn", tier=2),
    Verb("escribir", "to write", "write", en_forms=("write", "writes", "wrote"), tier=3),
    Verb("entender", "to understand", "understand",
         en_forms=("understand", "understands", "understood"),
         irregular={"present": ("entiendo", "entiendes", "entiende",
                                "entendemos", "entendéis", "entienden")},
         note="e→ie in the boot. 'No entiendo' is a survival phrase.", tier=3),
)

VERBS_BY_NAME = {v.infinitive: v for v in VERBS}

_EN_SUBJECT = ("I", "you", "he", "we", "you all", "they")


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
# Content: clozes — whole working sentences, the "functional view"
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Cloze:
    text: str          # sentence with ___ where the answer goes
    answer: str
    alts: tuple[str, ...]
    en: str            # translation shown as the cue
    tier: int = 1
    note: str = ""


CLOZES: tuple[Cloze, ...] = (
    Cloze("Yo ___ español.", "hablo", (), "I speak Spanish."),
    Cloze("¿___ estás?", "Cómo", (), "How are you?"),
    Cloze("No ___.", "entiendo", ("no comprendo",), "I don't understand."),
    Cloze("___ las dos.", "Son", (), "It's two o'clock.",
          note="Time uses ser: 'Son las dos', 'Es la una'."),
    Cloze("Ella ___ cansada.", "está", (), "She is tired.",
          note="estar, because tired is a state, not an identity."),
    Cloze("¿Dónde ___ el baño?", "está", (), "Where is the bathroom?", tier=2),
    Cloze("¿Cuánto ___?", "cuesta", (), "How much does it cost?", tier=2),
    Cloze("Ellos ___ hambre.", "tienen", (), "They are hungry.", tier=2,
          note="Spanish 'has hunger': tener hambre, not *estar hambre*."),
    Cloze("¿Cómo te ___?", "llamas", (), "What is your name?", tier=2,
          note="Literally: how do you call yourself?"),
    Cloze("Nosotros ___ en Madrid.", "vivimos", (), "We live in Madrid.", tier=2),
    Cloze("¡___ mañana!", "Hasta", (), "See you tomorrow!", tier=3),
    Cloze("___ un café, por favor.", "Quisiera", ("Quiero", "Me gustaría"),
          "I'd like a coffee, please.", tier=3,
          note="'Quisiera' is the soft, polite order."),
    Cloze("Ayer ___ al mercado.", "fui", (), "Yesterday I went to the market.", tier=3),
    Cloze("Cuando era niño, ___ en la playa.", "jugaba", (),
          "When I was a kid, I used to play at the beach.", tier=3,
          note="Imperfect: a habit in the past."),
)

# --------------------------------------------------------------------------
# Content: classic traps — forced choices for the famous confusables
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Trap:
    pair: str          # "ser o estar"
    text: str          # sentence with ___ where the choice goes
    options: tuple[str, str]
    correct: int       # index into options
    why: str
    tier: int = 2


TRAPS: tuple[Trap, ...] = (
    # --- ser / estar --------------------------------------------------------
    Trap("ser o estar", "Ella ___ cansada.", ("es", "está"), 1,
         "estar for states — tired passes. ser is what you ARE."),
    Trap("ser o estar", "Él ___ médico.", ("es", "está"), 0,
         "ser for identity and occupation."),
    Trap("ser o estar", "___ las dos.", ("Son", "Están"), 0,
         "time is always ser: son las dos, es la una."),
    Trap("ser o estar", "Madrid ___ en España.", ("es", "está"), 1,
         "location is estar — even for places that never move."),
    Trap("ser o estar", "La fiesta ___ en mi casa.", ("es", "está"), 0,
         "events happen with ser: la fiesta ES en mi casa. "
         "Things ARE somewhere: el libro ESTÁ aquí."),
    Trap("ser o estar", "___ lloviendo.", ("Es", "Está"), 1,
         "estar + gerund = happening right now."),
    # --- por / para ---------------------------------------------------------
    Trap("por o para", "Gracias ___ tu ayuda.", ("por", "para"), 0,
         "por for reasons: thanks because-of your help.", tier=3),
    Trap("por o para", "Salimos ___ Madrid mañana.", ("por", "para"), 1,
         "para for destinations.", tier=3),
    Trap("por o para", "Un regalo ___ ti.", ("por", "para"), 1,
         "para for recipients.", tier=3),
    Trap("por o para", "Pagué diez euros ___ el libro.", ("por", "para"), 0,
         "por for exchanges — money for a book.", tier=3),
    Trap("por o para", "Estudio ___ médico.", ("por", "para"), 1,
         "para for goals: in order to become.", tier=3),
    Trap("por o para", "Hablo ___ teléfono.", ("por", "para"), 0,
         "por for the channel: by phone.", tier=3),
    # --- saber / conocer ----------------------------------------------------
    Trap("saber o conocer", "¿___ nadar?", ("Sabes", "Conoces"), 0,
         "saber + infinitive = know how to.", tier=3),
    Trap("saber o conocer", "¿___ Madrid?", ("Sabes", "Conoces"), 1,
         "conocer for places and people — to be familiar with.", tier=3),
    Trap("saber o conocer", "No ___ la respuesta.", ("sé", "conozco"), 0,
         "saber for facts.", tier=3),
    Trap("saber o conocer", "___ a tu hermano.", ("Sé", "Conozco"), 1,
         "conocer for people.", tier=3),
    # --- preterite / imperfect ----------------------------------------------
    Trap("pretérito o imperfecto", "Ayer ___ al cine.", ("fui", "iba"), 0,
         "one finished event → preterite.", tier=3),
    Trap("pretérito o imperfecto", "Cada verano ___ a la playa.", ("fui", "iba"), 1,
         "a habit in the past → imperfect.", tier=3),
    Trap("pretérito o imperfecto", "Mientras dormía, ___ el teléfono.",
         ("sonó", "sonaba"), 0,
         "the interrupting event → preterite; the scene around it → imperfect.", tier=3),
    Trap("pretérito o imperfecto", "Eran las ocho cuando ___.", ("llegué", "llegaba"), 0,
         "the clock time sets the scene (imperfect); what happened → preterite.", tier=3),
)

# --------------------------------------------------------------------------
# Content: gender — the article drills that folding articles away never tests
# --------------------------------------------------------------------------

# es noun -> (article, note). Only nouns that live in WORDS.
GENDERS: dict[str, tuple[str, str]] = {
    "casa": ("la", ""), "comida": ("la", ""), "noche": ("la", ""),
    "calle": ("la", ""), "ciudad": ("la", ""), "puerta": ("la", ""),
    "palabra": ("la", ""), "pregunta": ("la", ""), "familia": ("la", ""),
    "mujer": ("la", ""), "pan": ("el", ""), "dinero": ("el", ""),
    "trabajo": ("el", ""), "libro": ("el", ""), "tiempo": ("el", ""),
    "error": ("el", ""), "hombre": ("el", ""), "amigo": ("el", ""),
    "día": ("el", "ends in -a, still masculine — el día"),
    "agua": ("el", "feminine, but el for the sound — las aguas"),
}

# --------------------------------------------------------------------------
# Content: generated sentences — dominadas reappear in new situations
# --------------------------------------------------------------------------

_SUBJECTS = (("yo", "I", 0), ("tú", "you", 1), ("él", "he", 2),
             ("nosotros", "we", 3), ("ellos", "they", 5))

# verb infinitive -> complement en keys the verb can sensibly take
_SENTENCE_PAIRS = {
    "comer": ("bread", "food"),
    "beber": ("water",),
    "tener": ("money", "time"),
    "necesitar": ("money", "water", "time", "work"),
    "trabajar": ("today", "tomorrow", "now", "here"),
    "vivir": ("here", "there"),
}

# placeable nouns for "¿Dónde está...?" — en key -> (es phrase, en phrase)
_PLACES = {"house": ("la casa", "the house"), "book": ("el libro", "the book"),
           "door": ("la puerta", "the door"), "street": ("la calle", "the street")}

# --------------------------------------------------------------------------
# Content: numbers, prices, time — infinite drills from a RNG
# --------------------------------------------------------------------------

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

# --------------------------------------------------------------------------
# Content: the ladder
# --------------------------------------------------------------------------


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


OPPONENTS: tuple[Opponent, ...] = (
    Opponent("El Turista", "just got off the plane — survival words, present tense",
             hp=8, tier=1, verb_share=0.25, cloze_share=0.10, dmg=1,
             num_share=0.10),
    Opponent("La Maestra Severa", "everyday vocabulary, past tense, real sentences",
             hp=10, tier=2, verb_share=0.28, cloze_share=0.12, dmg=1,
             trap_share=0.08, num_share=0.08, gender_share=0.06),
    Opponent("El Pretérito Impasible", "the past is his home turf; habits too",
             hp=12, tier=3, verb_share=0.36, cloze_share=0.12, dmg=1,
             trap_share=0.10, num_share=0.06, gender_share=0.06),
    Opponent("El Verbo Supremo", "champion. every tense, every form, hits twice as hard",
             hp=16, tier=3, verb_share=0.40, cloze_share=0.15, dmg=2,
             trap_share=0.12, num_share=0.05, gender_share=0.06),
)

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
    # using "pan" inside a fresh sentence still feeds the w:bread... map entry
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
    article, note = GENDERS[w.es]
    teach = [f"{article} {w.es}" + (f"  —  {note}" if note else "")]
    return Question(
        key=f"g:{w.en}", kind="gender", target_lang="es",
        prompt=f"___ {w.es}", sub="¿el o la?",
        accepted=(article, f"{article} {w.es}"),
        canonical=article,
        teach=teach,
        also_credit=(f"w:{w.en}",),
    )


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
            prompt=f"— ¿Cuánto cuesta? — Cuesta ___ pesos.",
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


def sentence_ready(p: "Profile", opp: Opponent) -> bool:
    dom = set(p.dominated())
    if any(k in dom for k in _PLACES):
        return True
    return any(
        w in dom
        for v, comps in _SENTENCE_PAIRS.items()
        if VERBS_BY_NAME[v].tier <= opp.tier
        for w in comps
    )


def sentence_question(p: "Profile", opp: Opponent, lang: str,
                      rng: random.Random) -> Question | None:
    """Compose a fresh sentence only from words the map already holds."""
    dom = set(p.dominated())
    moves = [(v, w) for v, comps in _SENTENCE_PAIRS.items()
             if VERBS_BY_NAME[v].tier <= opp.tier
             for w in comps if w in dom]
    places = [k for k in _PLACES if k in dom]
    if not moves and not places:
        return None

    sub_line = "every word here is already yours — new situation"

    if places and (not moves or rng.random() < 0.25):
        key = rng.choice(places)
        es_phrase, en_phrase = _PLACES[key]
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
    verb = VERBS_BY_NAME[vname]
    comp = next(w for w in WORDS if w.en == comp_en)
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
    path: Path = SAVE_PATH
    wins: int = 0
    losses: int = 0
    close_calls: int = 0
    streak: int = 0
    best_streak: int = 0
    xp: int = 0
    ladder_progress: int = 0      # opponents put on the canvas, all time
    started: float = field(default_factory=time.time)
    # item key -> {"en": hits, "es": hits, "miss": misses}
    items: dict[str, dict[str, int]] = field(default_factory=dict)
    # production language -> [attempts, hits]
    lang_record: dict[str, list[int]] = field(
        default_factory=lambda: {"en": [0, 0], "es": [0, 0]})

    # -- persistence -------------------------------------------------------
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

    # -- the language most wrong → question density -------------------------
    def accuracy(self, lang: str) -> float:
        attempts, hits = self.lang_record[lang]
        return (hits + 1) / (attempts + 2)  # Laplace prior: 0.5 when unseen

    def es_bias(self) -> float:
        """P(next question demands Spanish). Error mass decides the mix."""
        en_err = max(1 - self.accuracy("en"), 0.12)
        es_err = max(1 - self.accuracy("es"), 0.12)
        return min(0.85, max(0.15, es_err / (en_err + es_err)))

    # -- the "agreed understood" counter ------------------------------------
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

    # -- recording -----------------------------------------------------------
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
# Selection: weak language first, then weak items
# --------------------------------------------------------------------------


class Selector:
    def __init__(self, profile: Profile, rng: random.Random) -> None:
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
        if sentence_ready(self.p, opp):
            shares.append((0.12, lambda: self._pick_sentence(lang, opp)))
        roll = self.rng.random()
        acc = 0.0
        for share, fn in shares:
            acc += share
            if roll < acc:
                return fn()
        return self._pick_word(lang, opp)

    def _pick_word(self, lang: str, opp: Opponent) -> Question:
        pool = [w for w in WORDS if w.tier <= opp.tier]
        weights = [self._weight(f"w:{w.en}", lang) for w in pool]
        return word_question(self.rng.choices(pool, weights=weights, k=1)[0], lang)

    def _pick_verb(self, lang: str, opp: Opponent) -> Question:
        pool = [v for v in VERBS if v.tier <= opp.tier]
        tenses = TENSE_BY_TIER[opp.tier]
        cands = [
            (v, t, i) for v in pool for t in tenses for i in (0, 1, 2, 3, 5)
            if t != "imperfect" or v.infinitive in IMPERFECT_OK
        ]
        weights = [self._weight(f"v:{v.infinitive}:{t}:{i}", lang) for v, t, i in cands]
        v, t, i = self.rng.choices(cands, weights=weights, k=1)[0]
        return verb_question(v, t, i, lang)

    def _pick_cloze(self, opp: Opponent) -> Question:
        pool = [(i, c) for i, c in enumerate(CLOZES) if c.tier <= opp.tier]
        weights = [self._weight(f"c:{i}", "es") for i, _ in pool]
        i, c = self.rng.choices(pool, weights=weights, k=1)[0]
        return cloze_question(i, c)

    def _pick_trap(self, opp: Opponent) -> Question:
        pool = [(i, t) for i, t in enumerate(TRAPS) if t.tier <= opp.tier]
        weights = [self._weight(f"t:{i}", "es") for i, _ in pool]
        i, t = self.rng.choices(pool, weights=weights, k=1)[0]
        return trap_question(i, t, self.rng)

    def _pick_gender(self, opp: Opponent) -> Question:
        pool = [w for w in WORDS if w.es in GENDERS and w.tier <= opp.tier]
        weights = [self._weight(f"g:{w.en}", "es") for w in pool]
        return gender_question(self.rng.choices(pool, weights=weights, k=1)[0])

    def _pick_sentence(self, lang: str, opp: Opponent) -> Question:
        q = sentence_question(self.p, opp, lang, self.rng)
        return q if q is not None else self._pick_word(lang, opp)


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


bold = lambda t: c("1", t)        # noqa: E731
dim = lambda t: c("2", t)         # noqa: E731
green = lambda t: c("32", t)      # noqa: E731
red = lambda t: c("31", t)        # noqa: E731
yellow = lambda t: c("33", t)     # noqa: E731
cyan = lambda t: c("36", t)       # noqa: E731
magenta = lambda t: c("35", t)    # noqa: E731

HITS = ("¡Golpe directo!", "¡Toma!", "¡En la mandíbula!", "¡Azotón!", "Clean hit!")
CLOSE = ("A shave! Right word, wrong dress.", "Accent gremlins — medio punto.",
         "So close the ref almost counted it.")
TAUNTS = ("{o} laughs it off.", "{o} didn't even blink.", "{o} cracks a smile.",
          "The crowd winces.", "{o}: «¿Eso fue todo?»")

FLAG = {"es": "ESPAÑOL 🇲🇽", "en": "ENGLISH 🇬🇧"}


def hr(ch: str = "─", width: int = 60) -> str:
    return dim(ch * width)


def hp_bar(hp: int, max_hp: int, color) -> str:
    width = 18
    filled = max(0, round(width * hp / max_hp))
    return color("♥" * filled) + dim("·" * (width - filled))


def banner() -> None:
    print()
    print(bold(red("   ██╗     ██╗   ██╗ ██████╗██╗  ██╗ █████╗ ")))
    print(bold(red("   ██║     ██║   ██║██╔════╝██║  ██║██╔══██╗")))
    print(bold(red("   ██║     ██║   ██║██║     ███████║███████║")))
    print(bold(red("   ███████╗ ╚██████╔╝╚██████╗██║  ██║██║  ██║")))
    print(bold(yellow("        L É X I C A — english ⇄ español, round for round")))
    print(dim("   :pista hint · :salta skip · :card scorecard · :salir quit\n"))


def fight_intro(opp: Opponent, season: int) -> None:
    print(hr("═"))
    print(bold(f"  ROUND: {opp.name}") + dim(f"  — {opp.epithet}"))
    if season > 1:
        print(yellow(f"  season {season}: the ladder resets, the rivals bulk up (+{(season - 1) * 2} HP)"))
    print(hr("═"))


def show_fight(player_hp: int, opp: Opponent, opp_hp: int, opp_max: int) -> None:
    print(f"  tú {hp_bar(player_hp, PLAYER_HP, green)} {player_hp}"
          f"   vs   {red(opp.name)} {hp_bar(opp_hp, opp_max, red)} {max(opp_hp, 0)}")


def scorecard(p: Profile) -> None:
    total = p.wins + p.losses
    pct = 100 * p.wins / total if total else 0.0
    width = 22
    filled = int(width * pct / 100)
    bar = green("█" * filled) + dim("░" * (width - filled))
    dom = p.dominated()

    print()
    print(hr("═"))
    print(bold("  LA TARJETA") + dim(f"  ·  {p.rank()}  ·  {p.xp} xp"))
    print(hr("═"))
    print(f"  wins {green(str(p.wins))} · losses {red(str(p.losses))} · "
          f"shaves {yellow(str(p.close_calls))}   {bar} {pct:.0f}%")
    print(f"  streak {bold(str(p.streak))} · best {bold(str(p.best_streak))}")
    for lang in ("en", "es"):
        att, hit = p.lang_record[lang]
        acc = f"{100 * hit / att:.0f}%" if att else "—"
        print(f"  producing {FLAG[lang]:<22} {hit}/{att} ({acc})")
    mix = int(100 * p.es_bias())
    print(yellow(f"  next-question mix → {mix}% Spanish / {100 - mix}% English")
          + dim("  (leans on your weaker side)"))
    print(f"  dominadas (both ways agreed): {bold(green(str(len(dom))))}"
          + (dim("   " + ", ".join(dom[:10]) + ("…" if len(dom) > 10 else "")) if dom else ""))
    print(f"  reviews due now: {bold(str(p.due_now()))}"
          + dim(f" · {p.scheduled_ahead()} scheduled ahead (Leitner)"))
    beaten = p.ladder_progress % len(OPPONENTS)
    print("  ladder: " + "  ".join(
        (green("✓ ") if i < beaten else bold("▶ ") if i == beaten else dim("· ")) + o.name
        for i, o in enumerate(OPPONENTS)))
    print(hr("═"))
    print()


def teach(q: Question) -> None:
    if not q.teach:
        return
    print(dim("  ┌─ repaso " + "─" * 48))
    for line in q.teach:
        print(dim("  │ ") + line)
    print(dim("  └" + "─" * 57))


def masked(canonical: str) -> str:
    return " ".join(w[0] + "·" * (len(w) - 1) if len(w) > 1 else w
                    for w in canonical.split())


# --------------------------------------------------------------------------
# The fight
# --------------------------------------------------------------------------


def play(path: Path, rounds: int, seed: int | None) -> int:
    rng = random.Random(seed)
    p = Profile.load(path)
    sel = Selector(p, rng)

    banner()
    if p.wins + p.losses:
        print(dim(f"  welcome back to the ring — {p.wins}W/{p.losses}L, "
                  f"{len(p.dominated())} dominadas, rank {p.rank()}"))

    start = (p.wins, p.losses, len(p.dominated()))
    idx = p.ladder_progress % len(OPPONENTS)
    season = p.ladder_progress // len(OPPONENTS) + 1
    opp = OPPONENTS[idx]
    opp_max = opp.hp + (season - 1) * 2
    opp_hp, player_hp = opp_max, PLAYER_HP
    fight_intro(opp, season)

    n = 0
    while rounds <= 0 or n < rounds:
        q = sel.next(opp)
        n += 1
        used_hint = False

        while True:
            print()
            show_fight(player_hp, opp, opp_hp, opp_max)
            print(hr())
            print(f"  {dim('#' + str(n))} answer in {cyan(FLAG[q.target_lang])}  "
                  f"{dim('· ' + q.sub)}")
            print(f"     {bold(q.prompt)}")
            try:
                answer = input("  ▸ ").strip()
            except EOFError:
                answer = ":salir"
            low = answer.lower()

            if low in (":salir", ":q", "quit", "exit"):
                p.save()
                farewell(p, start)
                return 0
            if low in (":card", ":stats"):
                scorecard(p)
                continue
            if low in (":pista", ":h", ":hint"):
                print(f"  {yellow('pista')}  {masked(q.canonical)}")
                used_hint = True
                continue
            if low in (":ayuda", ":help", "?"):
                print(dim("  :pista hint · :salta skip · :card · :salir quit"))
                continue
            if low in (":salta", ":s", ":skip"):
                print(f"  {dim('te saltas →')} {bold(q.canonical)}  "
                      + dim("(counts as a loss, but no damage)"))
                p.record(q, "miss")
                teach(q)
                break

            result = grade(answer, q.accepted)
            if used_hint and result == "hit":
                result = "close"  # a hinted win is a shave — keeps stats honest
            gained = p.record(q, result)

            if result == "hit":
                combo = p.streak % 3 == 0
                dmg = 1 + (1 if combo else 0)
                opp_hp -= dmg
                flair = yellow(f" ¡COMBO x{p.streak}! +1 damage") if combo else ""
                print(f"  {green('✔ ' + rng.choice(HITS))} "
                      f"{dim('-' + str(dmg) + ' HP, +' + str(gained) + ' xp')}{flair}")
            elif result == "close":
                print(f"  {yellow('~ ' + rng.choice(CLOSE))}  it's {bold(q.canonical)}  "
                      + dim(f"+{gained} xp, blocked"))
            else:
                player_hp -= opp.dmg
                alts = [a for a in q.accepted[1:3]]
                extra = dim("  also ok: " + ", ".join(alts)) if alts else ""
                print(f"  {red('✘ ' + rng.choice(TAUNTS).format(o=opp.name))}  "
                      f"answer: {bold(q.canonical)}{extra}  {dim('-' + str(opp.dmg) + ' HP')}")
            teach(q)
            break

        if opp_hp <= 0:
            p.ladder_progress += 1
            p.save()
            print()
            print(bold(green(f"  ★ ¡{opp.name} CAE! The crowd goes wild. ★")))
            idx = p.ladder_progress % len(OPPONENTS)
            season = p.ladder_progress // len(OPPONENTS) + 1
            if idx == 0:
                print(bold(magenta("  🏆 ¡CAMPEÓN! The ladder resets — "
                                   "new season, meaner rivals.")))
            opp = OPPONENTS[idx]
            opp_max = opp.hp + (season - 1) * 2
            opp_hp = opp_max
            player_hp = min(PLAYER_HP, player_hp + 3)
            fight_intro(opp, season)

        if player_hp <= 0:
            print()
            print(bold(red(f"  ¡TE NOQUEARON! {opp.name} keeps the belt... this time.")))
            print(dim("  you stagger back up at 8 HP — the card remembers everything."))
            player_hp, opp_hp = 8, opp_max

        if n % 6 == 0:
            scorecard(p)
            p.save()

    p.save()
    farewell(p, start)
    return 0


def farewell(p: Profile, start: tuple[int, int, int]) -> None:
    w, l, d = start
    scorecard(p)
    print(f"  this session: {green('+' + str(p.wins - w))} wins, "
          f"{red('+' + str(p.losses - l))} losses, "
          f"{bold('+' + str(len(p.dominated()) - d))} new dominadas")
    print(dim(f"  saved to {p.path}"))
    print(bold("  ¡Hasta la revancha! 👋\n"))


# --------------------------------------------------------------------------
# Entry
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="lucha-lexica",
        description="English ⇄ Spanish lucha libre: it leans on your weak side.")
    ap.add_argument("--rounds", type=int, default=0,
                    help="stop after N questions (0 = endless)")
    ap.add_argument("--seed", type=int, default=None,
                    help="deterministic question order")
    ap.add_argument("--profile", type=Path, default=SAVE_PATH, help="scorecard file")
    ap.add_argument("--stats", action="store_true", help="print the card and exit")
    ap.add_argument("--reset", action="store_true", help="delete the saved profile")
    a = ap.parse_args(argv)

    if a.reset:
        a.profile.unlink(missing_ok=True)
        print(f"  wiped {a.profile}")
        return 0
    if a.stats:
        scorecard(Profile.load(a.profile))
        return 0
    try:
        return play(a.profile, a.rounds, a.seed)
    except KeyboardInterrupt:
        print("\n" + dim("  ctrl-c — the card is saved. ¡Adiós!"))
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
