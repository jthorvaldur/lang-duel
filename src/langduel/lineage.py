"""Etymology and language lineage — the "why is it that word?" layer.

Two kinds of content live here:

* `ORIGINS` — per-item ancestry, keyed by the Spanish headword (or verb
  infinitive). Each entry names the ancestor, the English words that descend
  from the *same* ancestor, and a hook that makes the pair memorable.
* `PATTERNS` — the sound laws and suffix mappings. These are the real payload:
  learn one and you can generate hundreds of cognates yourself instead of
  memorising them one at a time.

Only well-established etymologies are stated as fact. Where scholarship is
genuinely unsettled, the entry says so — a language app that bluffs about
origins is worse than one that stays quiet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Origin:
    root: str          # the ancestor form and its meaning
    cousins: str       # English words from the same ancestor
    hook: str = ""     # the line that makes it stick
    pattern: str = ""  # id of the PATTERNS entry this word demonstrates


ORIGINS: dict[str, Origin] = {
    # --- nouns ------------------------------------------------------------
    "agua": Origin("Latin aqua, water", "aquatic, aquarium, aqueduct",
                   "Same water, drained of its q."),
    "pan": Origin("Latin panis, bread", "pantry, company, companion",
                  "A companion is literally someone you share bread with: com + panis."),
    "casa": Origin("Latin casa, hut, cottage", "casino, casita",
                   "Latin's word for a shack won out over domus, the grand house."),
    "ciudad": Origin("Latin civitas, body of citizens", "city, civic, citizen, civil",
                     "Rome's word named the people, not the buildings.", pattern="ty-dad"),
    "calle": Origin("Latin callis, a worn path", "callus",
                    "The same root as the hard skin a path wears into your foot."),
    "trabajo": Origin("Late Latin tripalium, a three-staked instrument of torture",
                      "travail, and probably travel",
                      "Work and travel descend from the same torture device. Monday confirmed."),
    "día": Origin("Latin dies, day", "diary, diurnal, journal (via French jour)",
                  "English 'day' is NOT related — a rare false friend of the eye."),
    "noche": Origin("Latin nox / noctem, night", "nocturnal, equinox",
                    "English 'night' IS a cousin — both from PIE *nokwt-.", pattern="ct-ch"),
    "tiempo": Origin("Latin tempus, time", "temporal, tempo, tempest, tense",
                     "Spanish uses it for weather too — time and weather, one word."),
    "dinero": Origin("Latin denarius, a Roman silver coin", "denarius, dinar",
                     "The 'd' in old British £sd stood for this same coin."),
    "libro": Origin("Latin liber, the inner bark of a tree", "library, libretto",
                    "Before paper, you wrote on bark. The bark became the book."),
    "puerta": Origin("Latin porta, gate", "port, portal, porch, portico",
                     "A port is a gate in a coastline."),
    "palabra": Origin("Latin parabola, a comparison, from Greek parabolē",
                      "parable, parabola, parole",
                      "parabola → palabra: the l and r swapped places. Word from parable."),
    "error": Origin("Latin errare, to wander", "err, erratic, errand, knight-errant",
                    "A mistake is a wandering-off, not a crime."),
    "hombre": Origin("Latin homo / hominem, human being", "human, homicide, homage",
                     "Latin vir was the male; homo was anyone. Spanish merged them."),
    "mujer": Origin("Latin mulier, woman", "muliebrity (rare)",
                    "One of the few everyday words with no common English cousin."),
    "amigo": Origin("Latin amicus, from amare, to love", "amiable, amicable, amateur",
                    "An amateur does it for love. So does a friend."),
    "familia": Origin("Latin familia, the household — servants included, from famulus, servant",
                      "family, familiar",
                      "Rome's 'family' meant everyone under the roof, staff and all."),
    "vecino": Origin("Latin vicinus, from vicus, village", "vicinity, vicinage",
                     "A neighbour is simply someone of your village."),
    "comida": Origin("Latin comedere, to eat up (com + edere)", "edible, comestible, obese",
                     "Spanish kept the intensive com-: not eat, but eat *up*."),
    "niño": Origin("Disputed — most likely an expressive nursery word (nin-nin baby talk)",
                   "none established",
                   "Not everything descends from Latin. Some words are just how adults "
                   "talk to babies."),
    "pregunta": Origin("Latin percontari, to inquire — literally to sound a depth with a pole",
                       "none in common English use",
                       "To ask was to take a sounding, the way a boatman tests the river."),
    "puerta_": Origin("", ""),  # placeholder guard, never shown
    # --- adjectives -------------------------------------------------------
    "bueno": Origin("Latin bonus, good", "bonus, bounty, bonanza, boon",
                    "A bonus is just 'a good'."),
    "malo": Origin("Latin malus, bad", "malice, malign, dismal, malaria",
                   "Malaria = mala aria, 'bad air' — what they blamed before mosquitoes."),
    "grande": Origin("Latin grandis, full-grown, large", "grand, grandiose, aggrandize"),
    "nuevo": Origin("Latin novus, new", "novel, novice, innovate, renovate",
                    "English 'new' is a cousin too — PIE *newos ran down both branches.",
                    pattern="diphthong"),
    "viejo": Origin("Latin vetulus, little-old, from vetus", "veteran, inveterate",
                    "A veteran is an old hand, literally."),
    "caliente": Origin("Latin calere, to be hot", "calorie, cauldron, scald, nonchalant",
                       "Nonchalant = non + chaloir, 'not warming to it'."),
    "frío": Origin("Latin frigidus, cold", "frigid, refrigerate, refrigerator"),
    "fácil": Origin("Latin facilis, doable, from facere, to do", "facile, facility, faculty",
                    "Easy means do-able. Same root as hacer."),
    "difícil": Origin("Latin difficilis, dis- + facilis, not-doable", "difficult, difficulty"),
    "feliz": Origin("Latin felix, fruitful, lucky", "felicity, felicitate, Felix",
                    "Happiness as good harvest, not good mood."),
    "cansado": Origin("From cansar, generally traced to Latin campsare, to round a cape "
                      "(a nautical borrowing from Greek kampsai, to bend)",
                      "none in common English use",
                      "Tiredness as the exhaustion of rounding the headland."),
    # --- glue words -------------------------------------------------------
    "porque": Origin("por + que, from Latin pro quid", "the 'pro' of pro-rata",
                     "¿Por qué? is two words and a question; porque is one word and an answer."),
    "siempre": Origin("Latin semper, always", "sempiternal, semper fidelis"),
    "ahora": Origin("Latin hac hora, at this hour", "hour, horoscope",
                    "'Now' is Spanish for 'at this hour', worn down."),
    "después": Origin("Latin de ex post, from after that", "post-, posterior, postpone"),
    "hoy": Origin("Latin hodie = hoc die, on this day", "French aujourd'hui keeps the whole phrase",
                  "hoc die → hoy. Two words compressed into three letters."),
    "mañana": Origin("Latin mane, in the morning", "matinée (via French matin)",
                     "Morning and tomorrow are the same word — the joke writes itself."),
    "ayer": Origin("Latin ad heri, to yesterday", "yester- in yesterday, yesteryear",
                   "Latin heri and English 'yester' are PIE cousins."),
    "con": Origin("Latin cum, with", "connect, conspire, companion, concert",
                  "Every English con-/com- word is this preposition, glued on."),
    "sin": Origin("Latin sine, without", "sinecure",
                  "A sinecure is a job sine cura — without care."),
    "muy": Origin("Latin multum, much", "multi-, multitude, multiply",
                  "muy is multum with the middle worn away."),
    "casi": Origin("Latin quasi, as if", "quasi-, quasi-official"),
    "también": Origin("tan + bien, 'so well'", "none — it's a Spanish compound",
                      "Built in Spanish, not inherited. Two words that fused."),
    "todavía": Origin("toda vía, 'all the way'", "via, viaduct, obvious, trivial",
                      "'Still' as 'the whole road so far'."),
    "nunca": Origin("Latin nunquam, never", "none in common use"),
    # --- the Arabic layer -------------------------------------------------
    "ojalá": Origin("Arabic law šāʾ Allāh, if God wills", "none — but compare 'inshallah'",
                    "Eight centuries of al-Andalus, preserved in a shrug.", pattern="arabic"),
    "azúcar": Origin("Arabic as-sukkar, itself from Sanskrit śarkarā", "sugar, saccharine",
                     "Sugar reached English through French, and Spain through Arabic — "
                     "same Sanskrit source, two roads.", pattern="arabic"),
    "almohada": Origin("Arabic al-mujadda, the cushion", "none",
                       "The al- is the Arabic 'the', fused on and never removed.",
                       pattern="arabic"),
    "aceite": Origin("Arabic az-zayt, olive oil", "none — English took Latin oleum instead",
                     "Spain has two oil words: aceite (Arabic) and óleo (Latin).",
                     pattern="arabic"),
    "alfombra": Origin("Arabic al-ḥanbal, a carpet", "none", pattern="arabic"),
    # --- verbs ------------------------------------------------------------
    "ser": Origin("A merger of Latin esse, to be, and sedere, to sit",
                  "essence, essential; and sedentary, session from the other half",
                  "The preterite fui comes from a third root, PIE *bʰuH- — the same "
                  "ancestor as English 'be'."),
    "estar": Origin("Latin stare, to stand", "state, status, stable, stance, statue",
                    "ser is what you ARE; estar is where you STAND. The etymology is the rule."),
    "tener": Origin("Latin tenere, to hold", "tenant, tenacious, contain, retain, tenure",
                    "A tenant holds. So does anyone who tiene.", pattern="diphthong"),
    "ir": Origin("Three Latin verbs fused: ire (ir, iré), vadere (voy, vas, va), "
                 "and the fui forms from PIE *bʰuH-",
                 "exit and transit from ire; evade and invade from vadere",
                 "'Go' is irregular in Spanish for the same reason it is in English: "
                 "the paradigm was assembled from spare parts."),
    "hacer": Origin("Latin facere, to do or make", "fact, factory, perfect, affect, satisfy",
                    "A fact is a thing done.", pattern="f-h"),
    "querer": Origin("Latin quaerere, to seek", "query, quest, question, inquire, require",
                     "Spanish moved it from seeking to wanting — you seek what you want.",
                     pattern="diphthong"),
    "poder": Origin("Vulgar Latin potere, replacing classical posse", "potent, power, possible",
                    "puedo and 'power' are the same word wearing different clothes.",
                    pattern="diphthong"),
    "decir": Origin("Latin dicere, to say", "dictate, diction, verdict, predict, dictionary",
                    "A verdict is a true-saying: vere + dictum."),
    "saber": Origin("Latin sapere, to taste, hence to have taste, hence to be wise",
                    "sapient, insipid, sage; and 'savvy', borrowed from Spanish sabe",
                    "Homo sapiens is the tasting ape before it is the knowing one."),
    "ver": Origin("Latin videre, to see", "video, vision, evident, survey, provide",
                  "Video literally means 'I see' — the yo form of the Latin verb."),
    "hablar": Origin("Latin fabulari, to chat, to tell tales", "fable, fabulous, confab",
                     "To speak is to tell fables. Latin f- became a silent Spanish h-.",
                     pattern="f-h"),
    "comer": Origin("Latin comedere, to eat up", "edible, comestible"),
    "vivir": Origin("Latin vivere, to live", "vivid, revive, survive, vital, victual"),
    "trabajar": Origin("Late Latin tripaliare, to torture with the tripalium",
                       "travail, and probably travel"),
    "aprender": Origin("Latin apprehendere, to grasp", "apprehend, apprentice, prehensile",
                       "To learn is to grab hold. An apprentice is a grabber."),
    "escribir": Origin("Latin scribere, to scratch, to write", "scribe, script, describe, "
                       "manuscript"),
    "necesitar": Origin("Latin necesse, unavoidable", "necessary, necessity"),
    "entender": Origin("Latin intendere, to stretch toward", "intend, intense, tend, tension",
                       "To understand is to lean toward the thing.", pattern="diphthong"),
    "estar_": Origin("", ""),
}

ORIGINS.pop("puerta_", None)
ORIGINS.pop("estar_", None)


# --------------------------------------------------------------------------
# Patterns: the rules that generate cognates wholesale
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Pattern:
    pid: str
    title: str
    rule: str
    examples: tuple[tuple[str, str], ...]  # (spanish, english cousin)
    payoff: str


PATTERNS: tuple[Pattern, ...] = (
    Pattern(
        "f-h", "Latin f- became a silent Spanish h-",
        "Where Latin had f-, Castilian softened it to h- and then stopped pronouncing it. "
        "English borrowed the same words later, straight from Latin, and kept the f.",
        (("hacer", "fact, factory"), ("hablar", "fable"), ("hijo", "filial"),
         ("hierro", "ferrous"), ("harina", "farina"), ("hoja", "foliage")),
        "See an h- in Spanish? Try it with an f- and you may already know the word.",
    ),
    Pattern(
        "ct-ch", "Latin -ct- became Spanish -ch-",
        "The Latin cluster -ct- palatalised into -ch- in Spanish. English took the "
        "learned Latin form, so the pairs sit side by side.",
        (("noche", "nocturnal"), ("ocho", "octave"), ("leche", "lactose"),
         ("hecho", "fact"), ("pecho", "pectoral"), ("derecho", "direct")),
        "-ch- in Spanish often means -ct- in an English cousin.",
    ),
    Pattern(
        "pl-ll", "Latin pl-, cl-, fl- became ll-",
        "Initial consonant + l collapsed into the Spanish ll.",
        (("llamar", "claim, clamour"), ("llave", "clavicle, clef"),
         ("lleno", "plenty, plenary"), ("llover", "pluvial"), ("llama (flame)", "flame")),
        "An unfamiliar ll- word? Test pl-, cl- and fl- against your English.",
    ),
    Pattern(
        "ty-dad", "English -ty is Spanish -dad",
        "Both descend from the Latin abstract-noun ending -tatem.",
        (("ciudad", "city"), ("universidad", "university"), ("libertad", "liberty"),
         ("realidad", "reality"), ("dificultad", "difficulty")),
        "This one is nearly mechanical: convert -ty to -dad and you are usually right.",
    ),
    Pattern(
        "tion-cion", "English -tion is Spanish -ción",
        "Same Latin ending -tionem, two spellings. Every noun of this shape is feminine.",
        (("nación", "nation"), ("acción", "action"), ("información", "information"),
         ("conversación", "conversation")),
        "Thousands of words, free. La nación, la acción — always la.",
    ),
    Pattern(
        "ous-oso", "English -ous is Spanish -oso",
        "From Latin -osus, 'full of'.",
        (("famoso", "famous"), ("curioso", "curious"), ("nervioso", "nervous"),
         ("delicioso", "delicious")),
        "Adjective ending in -ous? Swap in -oso and check the vowel.",
    ),
    Pattern(
        "diphthong", "The stem-change boot is a sound law, not a whim",
        "Latin's short stressed e and o broke into ie and ue. Stress falls on the stem "
        "in yo/tú/él/ellos and on the ending in nosotros/vosotros — so the change appears "
        "in exactly those four, drawing the famous boot shape.",
        (("poder → puedo", "potent (unstressed stem keeps the o: podemos)"),
         ("tener → tienes", "tenant"), ("querer → quiero", "query"),
         ("entender → entiendo", "intend")),
        "You are not memorising exceptions. You are watching where the stress landed.",
    ),
    Pattern(
        "arabic", "The Arabic layer, and its fused article",
        "Roughly 4% of Spanish comes from Arabic after eight centuries of al-Andalus. "
        "Words borrowed with the article al- kept it fused, which is why so many begin al-.",
        (("almohada", "the pillow — al + mujadda"), ("azúcar", "sugar — as-sukkar"),
         ("aceite", "oil — az-zayt"), ("álgebra", "algebra — al-jabr"),
         ("ojalá", "if God wills — law šāʾ Allāh")),
        "This is the layer English mostly lacks — where Spanish stops looking like Latin.",
    ),
)

PATTERNS_BY_ID = {p.pid: p for p in PATTERNS}


def origin_for(key: str) -> Origin | None:
    return ORIGINS.get(key)


def coverage() -> tuple[int, int]:
    """(items with an origin entry, total patterns) — used by the library screen."""
    return len(ORIGINS), len(PATTERNS)
