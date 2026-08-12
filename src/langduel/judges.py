"""Judges — the thing that decides whether an answer is right enough.

Extracted from `engine.grade` so that domains can bring their own notion of
correctness without the engine caring. A judge takes the raw answer and the
question, and returns a verdict plus an optional note explaining itself.

Three verdicts, unchanged from the original game: hit, close, miss.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Protocol

HIT, CLOSE, MISS = "hit", "close", "miss"


@dataclass(frozen=True)
class Verdict:
    result: str
    note: str = ""  # shown to the player when it explains something useful


class Judge(Protocol):
    def __call__(self, answer: str, accepted: tuple[str, ...],
                 options: tuple[str, ...] = ()) -> Verdict: ...


# --------------------------------------------------------------------------
# Normalisation
# --------------------------------------------------------------------------

_STRIP_LEAD = ("the ", "a ", "an ", "to ", "el ", "la ", "los ", "las ", "un ", "una ")


def fold(text: str) -> str:
    """Lowercase, drop accents, punctuation and leading articles."""
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


# --------------------------------------------------------------------------
# Judges
# --------------------------------------------------------------------------


def exact(answer: str, accepted: tuple[str, ...], options: tuple[str, ...] = ()) -> Verdict:
    """No forgiveness beyond case and spacing. For terminology that must be exact."""
    return Verdict(HIT if fold(answer) in {fold(a) for a in accepted} else MISS)


def tolerant(answer: str, accepted: tuple[str, ...], options: tuple[str, ...] = ()) -> Verdict:
    """The original grader: accents and one or two typos are forgiven as 'close'."""
    given = fold(answer)
    if not given:
        return Verdict(MISS)
    folded = [fold(a) for a in accepted]
    if given in folded:
        return Verdict(HIT)
    tolerance = 1 if len(given) <= 6 else 2
    if any(edit_distance(given, f) <= tolerance for f in folded):
        return Verdict(CLOSE, "spelling only")
    return Verdict(MISS)


def choice(answer: str, accepted: tuple[str, ...], options: tuple[str, ...] = ()) -> Verdict:
    """Pick-one questions. Accepts the option letter (a/b/c) or its text.

    Used where free text would be unfair to grade — safety scenarios, where what
    matters is choosing the right action, not phrasing it the author's way.
    """
    given = fold(answer)
    if not given:
        return Verdict(MISS)
    letters = {chr(ord("a") + i): opt for i, opt in enumerate(options)}
    picked = letters.get(given)
    if picked is None:
        for opt in options:
            if given == fold(opt) or (len(given) > 4 and given in fold(opt)):
                picked = opt
                break
    if picked is None:
        return Verdict(MISS, "answer with a letter, or the option's wording")
    return Verdict(HIT if fold(picked) in {fold(a) for a in accepted} else MISS)


BY_NAME: dict[str, Judge] = {"exact": exact, "tolerant": tolerant, "choice": choice}
