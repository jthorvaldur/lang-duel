"""Content bank for the English/Spanish pair.

Everything here is data + pure functions. No I/O, no state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Word:
    """One lexical item. `es_alts` are also accepted when answering in Spanish."""

    en: str
    es: str
    tag: str
    en_alts: tuple[str, ...] = ()
    es_alts: tuple[str, ...] = ()
    level: int = 1  # 1 = survival, 2 = everyday, 3 = stretch

    def accepted(self, lang: str) -> tuple[str, ...]:
        if lang == "es":
            return (self.es,) + self.es_alts
        return (self.en,) + self.en_alts

    def prompt_text(self, lang: str) -> str:
        return self.es if lang == "es" else self.en


WORDS: tuple[Word, ...] = (
    # --- people & pronouns -------------------------------------------------
    Word("I", "yo", "pronoun"),
    Word("you", "tú", "pronoun", es_alts=("usted", "vos")),
    Word("he", "él", "pronoun"),
    Word("she", "ella", "pronoun"),
    Word("we", "nosotros", "pronoun", es_alts=("nosotras",)),
    Word("they", "ellos", "pronoun", es_alts=("ellas",)),
    Word("man", "hombre", "people", es_alts=("el hombre",)),
    Word("woman", "mujer", "people", es_alts=("la mujer",)),
    Word("friend", "amigo", "people", es_alts=("amiga", "el amigo")),
    Word("child", "niño", "people", en_alts=("kid", "boy"), es_alts=("niña", "chico")),
    Word("family", "familia", "people", es_alts=("la familia",)),
    Word("neighbor", "vecino", "people", es_alts=("vecina",), level=2),
    # --- everyday nouns ----------------------------------------------------
    Word("water", "agua", "noun", es_alts=("el agua",)),
    Word("bread", "pan", "noun", es_alts=("el pan",)),
    Word("food", "comida", "noun", en_alts=("meal",), es_alts=("la comida",)),
    Word("house", "casa", "noun", en_alts=("home",), es_alts=("la casa", "hogar")),
    Word("city", "ciudad", "noun", es_alts=("la ciudad",)),
    Word("street", "calle", "noun", es_alts=("la calle",)),
    Word("work", "trabajo", "noun", en_alts=("job",), es_alts=("el trabajo",)),
    Word("day", "día", "noun", es_alts=("el día",)),
    Word("night", "noche", "noun", es_alts=("la noche",)),
    Word("time", "tiempo", "noun", es_alts=("el tiempo", "vez")),
    Word("money", "dinero", "noun", es_alts=("el dinero", "plata")),
    Word("book", "libro", "noun", es_alts=("el libro",)),
    Word("door", "puerta", "noun", es_alts=("la puerta",), level=2),
    Word("word", "palabra", "noun", es_alts=("la palabra",), level=2),
    Word("question", "pregunta", "noun", es_alts=("la pregunta",), level=2),
    Word("mistake", "error", "noun", es_alts=("el error", "equivocación"), level=3),
    # --- adjectives --------------------------------------------------------
    Word("good", "bueno", "adj", es_alts=("buena", "buen")),
    Word("bad", "malo", "adj", es_alts=("mala", "mal")),
    Word("big", "grande", "adj", en_alts=("large",)),
    Word("small", "pequeño", "adj", en_alts=("little",), es_alts=("pequeña", "chico")),
    Word("new", "nuevo", "adj", es_alts=("nueva",)),
    Word("old", "viejo", "adj", es_alts=("vieja", "antiguo")),
    Word("hot", "caliente", "adj", level=2),
    Word("cold", "frío", "adj", es_alts=("fría",), level=2),
    Word("easy", "fácil", "adj", level=2),
    Word("hard", "difícil", "adj", en_alts=("difficult",), level=2),
    Word("tired", "cansado", "adj", es_alts=("cansada",), level=2),
    Word("happy", "feliz", "adj", es_alts=("contento", "contenta"), level=2),
    # --- glue words: the real unlock --------------------------------------
    Word("but", "pero", "glue"),
    Word("because", "porque", "glue"),
    Word("also", "también", "glue", en_alts=("too", "as well")),
    Word("always", "siempre", "glue"),
    Word("never", "nunca", "glue", es_alts=("jamás",)),
    Word("now", "ahora", "glue"),
    Word("later", "después", "glue", en_alts=("afterwards", "after"), es_alts=("luego", "más tarde")),
    Word("today", "hoy", "glue"),
    Word("tomorrow", "mañana", "glue"),
    Word("yesterday", "ayer", "glue"),
    Word("here", "aquí", "glue", es_alts=("acá",)),
    Word("there", "allí", "glue", es_alts=("allá", "ahí")),
    Word("with", "con", "glue"),
    Word("without", "sin", "glue"),
    Word("very", "muy", "glue"),
    Word("almost", "casi", "glue", level=2),
    Word("still", "todavía", "glue", en_alts=("yet",), es_alts=("aún",), level=2),
    Word("although", "aunque", "glue", en_alts=("even though",), level=3),
    # --- the Arabic layer (see lineage.py) ---------------------------------
    Word("sugar", "azúcar", "arabic", es_alts=("el azúcar",), level=2),
    Word("oil", "aceite", "arabic", es_alts=("el aceite",), level=2),
    Word("pillow", "almohada", "arabic", es_alts=("la almohada",), level=2),
    Word("rug", "alfombra", "arabic", en_alts=("carpet",), level=3),
    Word("hopefully", "ojalá", "arabic", en_alts=("let's hope", "I hope so"), level=3),
    # --- phrases: functional survival kit ---------------------------------
    Word("How are you?", "¿Cómo estás?", "phrase", es_alts=("¿Cómo está?", "¿Qué tal?")),
    Word("What is your name?", "¿Cómo te llamas?", "phrase", es_alts=("¿Cuál es tu nombre?",)),
    Word("I don't understand", "No entiendo", "phrase", es_alts=("No comprendo",)),
    Word("Can you repeat that?", "¿Puedes repetir?", "phrase", es_alts=("¿Puede repetir?",)),
    Word("How much does it cost?", "¿Cuánto cuesta?", "phrase", es_alts=("¿Cuánto vale?",)),
    Word("Where is the bathroom?", "¿Dónde está el baño?", "phrase", es_alts=("¿Dónde queda el baño?",)),
    Word("I would like a coffee", "Quisiera un café", "phrase", es_alts=("Me gustaría un café", "Quiero un café")),
    Word("See you tomorrow", "Hasta mañana", "phrase", es_alts=("nos vemos mañana",)),
    Word("I'm learning Spanish", "Estoy aprendiendo español", "phrase", level=2),
    Word("It doesn't matter", "No importa", "phrase", es_alts=("da igual",), level=2),
)

# --------------------------------------------------------------------------
# Verbs & conjugation
# --------------------------------------------------------------------------

PERSONS: tuple[tuple[str, str], ...] = (
    ("yo", "I"),
    ("tú", "you"),
    ("él/ella", "he/she"),
    ("nosotros", "we"),
    ("vosotros", "you all"),
    ("ellos/ellas", "they"),
)

TENSES: tuple[str, ...] = ("present", "preterite", "imperfect")

TENSE_LABEL = {
    "present": "present",
    "preterite": "past (preterite)",
    "imperfect": "past (imperfect / used to)",
}

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


@dataclass(frozen=True)
class Verb:
    infinitive: str
    en: str  # bare English infinitive, e.g. "to speak"
    gloss: str  # short meaning used in prompts, e.g. "speak"
    # English base / third-person-singular / simple past. Defaults are the
    # regular "+s / +ed" pattern; irregular English verbs state all three.
    en_forms: tuple[str, str, str] = ()
    irregular: dict[str, tuple[str, ...]] = field(default_factory=dict)
    stem_change: str = ""  # note shown in the teaching card
    level: int = 1

    def english(self) -> tuple[str, str, str]:
        if self.en_forms:
            return self.en_forms
        base = self.gloss.split(",")[0].split("(")[0].strip()
        third = base + ("es" if base.endswith(("s", "sh", "ch", "x", "o")) else "s")
        past = base[:-1] + "d" if base.endswith("e") else base + "ed"
        return base, third, past

    @property
    def ending(self) -> str:
        return self.infinitive[-2:]

    @property
    def stem(self) -> str:
        return self.infinitive[:-2]

    def conjugate(self, tense: str) -> tuple[str, ...]:
        """Full six-person row for a tense. Irregular table wins outright."""
        if tense in self.irregular:
            return self.irregular[tense]
        return tuple(self.stem + e for e in _ENDINGS[tense][self.ending])


VERBS: tuple[Verb, ...] = (
    Verb(
        "ser", "to be", "be (permanent: identity, origin)",
        en_forms=("be", "is", "was"),
        irregular={
            "present": ("soy", "eres", "es", "somos", "sois", "son"),
            "preterite": ("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
            "imperfect": ("era", "eras", "era", "éramos", "erais", "eran"),
        },
        stem_change="ser = what something IS; estar = how/where it is right now",
    ),
    Verb(
        "estar", "to be", "be (state/location: right now)",
        en_forms=("be", "is", "was"),
        irregular={
            "present": ("estoy", "estás", "está", "estamos", "estáis", "están"),
            "preterite": ("estuve", "estuviste", "estuvo", "estuvimos",
                          "estuvisteis", "estuvieron"),
        },
    ),
    Verb(
        "tener", "to have", "have",
        en_forms=("have", "has", "had"),
        irregular={
            "present": ("tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"),
            "preterite": ("tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"),
        },
        stem_change="e→ie in the boot (tienes, tiene, tienen)",
    ),
    Verb(
        "ir", "to go", "go",
        en_forms=("go", "goes", "went"),
        irregular={
            "present": ("voy", "vas", "va", "vamos", "vais", "van"),
            "preterite": ("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"),
            "imperfect": ("iba", "ibas", "iba", "íbamos", "ibais", "iban"),
        },
        stem_change="preterite is identical to ser — context decides",
    ),
    Verb(
        "hacer", "to do / to make", "do, make",
        en_forms=("do", "does", "did"),
        irregular={
            "present": ("hago", "haces", "hace", "hacemos", "hacéis", "hacen"),
            "preterite": ("hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"),
        },
        stem_change="hizo keeps the sound with a z",
    ),
    Verb(
        "querer", "to want", "want",
        en_forms=("want", "wants", "wanted"),
        irregular={
            "present": ("quiero", "quieres", "quiere", "queremos", "queréis", "quieren"),
            "preterite": ("quise", "quisiste", "quiso", "quisimos", "quisisteis",
                          "quisieron"),
        },
        stem_change="e→ie in the boot",
    ),
    Verb(
        "poder", "to be able / can", "can, be able to",
        en_forms=("can", "can", "could"),
        irregular={
            "present": ("puedo", "puedes", "puede", "podemos", "podéis", "pueden"),
            "preterite": ("pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"),
        },
        stem_change="o→ue in the boot",
    ),
    Verb(
        "decir", "to say / to tell", "say, tell",
        en_forms=("say", "says", "said"),
        irregular={
            "present": ("digo", "dices", "dice", "decimos", "decís", "dicen"),
            "preterite": ("dije", "dijiste", "dijo", "dijimos", "dijisteis", "dijeron"),
        },
        level=2,
    ),
    Verb(
        "saber", "to know (facts)", "know (a fact, how to)",
        en_forms=("know", "knows", "knew"),
        irregular={
            "present": ("sé", "sabes", "sabe", "sabemos", "sabéis", "saben"),
            "preterite": ("supe", "supiste", "supo", "supimos", "supisteis", "supieron"),
        },
        stem_change="contrast with conocer = know a person or place",
        level=2,
    ),
    Verb(
        "ver", "to see", "see",
        en_forms=("see", "sees", "saw"),
        irregular={
            "present": ("veo", "ves", "ve", "vemos", "veis", "ven"),
            "preterite": ("vi", "viste", "vio", "vimos", "visteis", "vieron"),
            "imperfect": ("veía", "veías", "veía", "veíamos", "veíais", "veían"),
        },
        level=2,
    ),
    Verb("hablar", "to speak", "speak, talk", en_forms=("speak", "speaks", "spoke")),
    Verb("comer", "to eat", "eat", en_forms=("eat", "eats", "ate")),
    Verb("vivir", "to live", "live"),
    Verb("trabajar", "to work", "work", level=2),
    Verb("aprender", "to learn", "learn", level=2),
    Verb("escribir", "to write", "write",
         en_forms=("write", "writes", "wrote"), level=2),
    Verb("necesitar", "to need", "need", level=2),
    Verb(
        "entender", "to understand", "understand",
        en_forms=("understand", "understands", "understood"),
        irregular={"present": ("entiendo", "entiendes", "entiende",
                               "entendemos", "entendéis", "entienden")},
        stem_change="e→ie in the boot",
        level=3,
    ),
)

VERBS_BY_NAME = {v.infinitive: v for v in VERBS}

# English person-forms used to build the prompt sentence, per tense.
_EN_SUBJECT = ("I", "you", "he", "we", "you all", "they")
_EN_THIRD_S = 2


def english_forms(verb: Verb, tense: str, person: int) -> tuple[str, ...]:
    """Accepted English renderings for one cell, best first.

    Each is a full clause ("he had"); the grader also accepts the bare verb
    phrase, so "had" alone counts too.
    """
    subject = _EN_SUBJECT[person]
    base, third, past = verb.english()

    if tense == "present":
        if base == "be":
            vp = ["am" if person == 0 else "is" if person == _EN_THIRD_S else "are"]
        elif base == "can":
            vp = ["can"]
        else:
            head = third if person == _EN_THIRD_S else base
            vp = [head, f"{'is' if person == _EN_THIRD_S else 'am' if person == 0 else 'are'} "
                        f"{_gerund(base)}"]
    elif tense == "preterite":
        vp = [past]
    else:  # imperfect: habitual / ongoing past
        vp = [f"used to {base}", f"{'was' if person in (0, _EN_THIRD_S) else 'were'} "
                                 f"{_gerund(base)}", past]
    return tuple(f"{subject} {v}" for v in vp)


def _gerund(base: str) -> str:
    if base.endswith("e") and not base.endswith("ee"):
        return base[:-1] + "ing"
    return base + "ing"


def english_cue(verb: Verb, tense: str, person: int) -> str:
    """The single English clause shown as a prompt."""
    return english_forms(verb, tense, person)[0]


def teaching_card(verb: Verb, tense: str) -> list[str]:
    """The expansion shown after a verb is answered: full paradigm + note."""
    forms = verb.conjugate(tense)
    lines = [f"{verb.infinitive} — {verb.en}  ·  {TENSE_LABEL[tense]}"]
    for (es_p, en_p), form in zip(PERSONS, forms):
        lines.append(f"   {es_p:<12} {form:<14} {en_p}")
    if verb.stem_change:
        lines.append(f"   note: {verb.stem_change}")
    return lines


# --------------------------------------------------------------------------
# Usage examples — the context dimension, shown when an answer goes wrong
# --------------------------------------------------------------------------
#
# Keyed by Spanish headword. Deliberately short and ordinary: a word met in a
# sentence is remembered better than a word met alone, and a sentence you can
# picture beats a clever one. Phrases are omitted — they are already sentences.

USES: dict[str, tuple[str, str]] = {
    "yo": ("Yo hablo español.", "I speak Spanish."),
    "tú": ("¿Tú vienes también?", "Are you coming too?"),
    "él": ("Él es mi hermano.", "He is my brother."),
    "ella": ("Ella trabaja aquí.", "She works here."),
    "nosotros": ("Nosotros vivimos en Madrid.", "We live in Madrid."),
    "ellos": ("Ellos no entienden.", "They don't understand."),
    "hombre": ("Ese hombre es mi vecino.", "That man is my neighbour."),
    "mujer": ("La mujer del sombrero.", "The woman with the hat."),
    "amigo": ("Es un amigo del trabajo.", "He's a friend from work."),
    "niño": ("El niño tiene hambre.", "The child is hungry."),
    "familia": ("Toda la familia come junta.", "The whole family eats together."),
    "vecino": ("Mi vecino tiene un perro.", "My neighbour has a dog."),
    "agua": ("Quiero un vaso de agua.", "I want a glass of water."),
    "pan": ("Compro pan cada mañana.", "I buy bread every morning."),
    "comida": ("La comida está lista.", "The food is ready."),
    "casa": ("Estoy en casa.", "I'm at home."),
    "ciudad": ("Vivo en una ciudad grande.", "I live in a big city."),
    "calle": ("Cruzamos la calle.", "We cross the street."),
    "trabajo": ("Voy al trabajo a las ocho.", "I go to work at eight."),
    "día": ("Hace un día bonito.", "It's a lovely day."),
    "noche": ("Trabajo por la noche.", "I work at night."),
    "tiempo": ("No tengo tiempo.", "I don't have time."),
    "dinero": ("No llevo dinero encima.", "I'm not carrying any money."),
    "libro": ("Estoy leyendo un libro.", "I'm reading a book."),
    "puerta": ("Cierra la puerta, por favor.", "Close the door, please."),
    "palabra": ("No entiendo esa palabra.", "I don't understand that word."),
    "pregunta": ("Tengo una pregunta.", "I have a question."),
    "error": ("Fue un error mío.", "It was my mistake."),
    "bueno": ("Es un buen libro.", "It's a good book."),
    "malo": ("Tuve un día malo.", "I had a bad day."),
    "grande": ("Viven en una casa grande.", "They live in a big house."),
    "pequeño": ("Es un problema pequeño.", "It's a small problem."),
    "nuevo": ("Tengo un coche nuevo.", "I have a new car."),
    "viejo": ("Ese edificio es muy viejo.", "That building is very old."),
    "caliente": ("El café está caliente.", "The coffee is hot."),
    "frío": ("Hace frío hoy.", "It's cold today."),
    "fácil": ("El examen fue fácil.", "The exam was easy."),
    "difícil": ("Es difícil de explicar.", "It's hard to explain."),
    "cansado": ("Estoy cansado.", "I'm tired."),
    "feliz": ("Estoy feliz de verte.", "I'm happy to see you."),
    "pero": ("Quiero ir, pero no puedo.", "I want to go, but I can't."),
    "porque": ("No fui porque llovía.", "I didn't go because it was raining."),
    "también": ("Yo también quiero.", "I want some too."),
    "siempre": ("Siempre llega tarde.", "He always arrives late."),
    "nunca": ("Nunca he estado allí.", "I have never been there."),
    "ahora": ("Ahora no puedo hablar.", "I can't talk right now."),
    "después": ("Hablamos después.", "We'll talk later."),
    "hoy": ("Hoy es lunes.", "Today is Monday."),
    "mañana": ("Nos vemos mañana.", "See you tomorrow."),
    "ayer": ("Ayer comí en casa.", "Yesterday I ate at home."),
    "aquí": ("Ven aquí.", "Come here."),
    "allí": ("El libro está allí.", "The book is over there."),
    "con": ("Voy con mis amigos.", "I'm going with my friends."),
    "sin": ("Café sin azúcar.", "Coffee without sugar."),
    "muy": ("Está muy lejos.", "It's very far away."),
    "casi": ("Casi me caigo.", "I almost fell."),
    "todavía": ("Todavía no está listo.", "It isn't ready yet."),
    "aunque": ("Iré aunque llueva.", "I'll go even if it rains."),
    "azúcar": ("Un café con azúcar.", "A coffee with sugar."),
    "aceite": ("Aceite de oliva.", "Olive oil."),
    "almohada": ("Necesito otra almohada.", "I need another pillow."),
    "alfombra": ("La alfombra es roja.", "The rug is red."),
    "ojalá": ("Ojalá tengas razón.", "I hope you're right."),
}

# Verbs get their paradigm instead, but a sentence still helps the meaning land.
VERB_USES: dict[str, tuple[str, str]] = {
    "ser": ("Soy de Islandia.", "I'm from Iceland."),
    "estar": ("Estoy en la oficina.", "I'm at the office."),
    "tener": ("Tengo dos hermanas.", "I have two sisters."),
    "ir": ("Vamos a la playa.", "We're going to the beach."),
    "hacer": ("¿Qué haces?", "What are you doing?"),
    "querer": ("Quiero aprender español.", "I want to learn Spanish."),
    "poder": ("No puedo ahora.", "I can't right now."),
    "decir": ("¿Qué dijiste?", "What did you say?"),
    "saber": ("No sé.", "I don't know."),
    "ver": ("No veo nada.", "I can't see anything."),
    "hablar": ("Hablo un poco de español.", "I speak a little Spanish."),
    "comer": ("Comemos a las dos.", "We eat at two."),
    "vivir": ("Vivo aquí desde 2019.", "I've lived here since 2019."),
    "trabajar": ("Trabajo desde casa.", "I work from home."),
    "aprender": ("Aprendo rápido.", "I learn fast."),
    "escribir": ("Le escribo a mi madre.", "I write to my mother."),
    "necesitar": ("Necesito ayuda.", "I need help."),
    "entender": ("No entiendo.", "I don't understand."),
}


def usage(key: str) -> tuple[str, str] | None:
    """The example sentence for a headword, if we have one."""
    return USES.get(key) or VERB_USES.get(key)
