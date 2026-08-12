"""Terminal chrome: colour, width-aware alignment, and the app frame.

The app draws a fixed layout every round rather than scrolling: a header with
the running record pinned to the right, a question panel, a feedback area, and
a command footer. Everything here is pure presentation.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import unicodedata

# --------------------------------------------------------------------------
# Colour
# --------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
FANCY = sys.stdout.isatty() and os.environ.get("LANGDUEL_ASCII") is None


def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def bold(t: str) -> str: return c("1", t)
def dim(t: str) -> str: return c("2", t)
def green(t: str) -> str: return c("32", t)
def red(t: str) -> str: return c("31", t)
def yellow(t: str) -> str: return c("33", t)
def blue(t: str) -> str: return c("36", t)
def magenta(t: str) -> str: return c("35", t)
def violet(t: str) -> str: return c("38;5;141", t)
def orange(t: str) -> str: return c("38;5;214", t)


# --------------------------------------------------------------------------
# Width-aware helpers
# --------------------------------------------------------------------------

_ANSI = re.compile(r"\033\[[0-9;]*m")


def strip(text: str) -> str:
    return _ANSI.sub("", text)


def vlen(text: str) -> int:
    """Visible width: ignores colour codes, counts wide glyphs as two columns."""
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        for ch in strip(text)
        if unicodedata.category(ch) != "Mn"
    )


def pad(text: str, width: int) -> str:
    return text + " " * max(0, width - vlen(text))


def clip(text: str, width: int) -> str:
    """Truncate to a visible width, keeping colour codes intact."""
    if vlen(text) <= width:
        return text
    out, used = [], 0
    for part in _ANSI.split(text):
        for ch in part:
            w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
            if used + w > width - 1:
                return "".join(out) + "…\033[0m"
            out.append(ch)
            used += w
    return "".join(out)


def width() -> int:
    return max(52, min(shutil.get_terminal_size((78, 24)).columns, 96))


# --------------------------------------------------------------------------
# Screen control
# --------------------------------------------------------------------------


def enter_app() -> None:
    """Switch to the alternate screen buffer so the shell is left untouched."""
    if FANCY:
        sys.stdout.write("\033[?1049h\033[?25h")
        sys.stdout.flush()


def leave_app() -> None:
    if FANCY:
        sys.stdout.write("\033[?1049l")
        sys.stdout.flush()


def clear() -> None:
    sys.stdout.write("\033[2J\033[H" if FANCY else "\n")
    sys.stdout.flush()


# --------------------------------------------------------------------------
# Boxes
# --------------------------------------------------------------------------

def rule(w: int, ch: str = "─") -> str:
    return dim(ch * w)


def bar(w: int, ch: str = "═") -> str:
    return dim(ch * w)


def split_row(left: str, right: str, w: int) -> str:
    """Left-aligned and right-aligned content on one line — the header pattern."""
    gap = w - vlen(left) - vlen(right)
    if gap < 1:
        left = clip(left, max(1, w - vlen(right) - 1))
        gap = max(1, w - vlen(left) - vlen(right))
    return left + " " * gap + right


def panel(title: str, lines: list[str], w: int, colour=dim) -> list[str]:
    """A titled box. Lines are clipped, never wrapped mid-word by accident."""
    inner = w - 4
    head = colour("┌─ ") + bold(title) + " " + colour("─" * max(0, inner - vlen(title) - 1) + "┐")
    out = [head]
    for ln in lines:
        out.append(colour("│ ") + pad(clip(ln, inner), inner) + colour(" │"))
    out.append(colour("└" + "─" * (w - 2) + "┘"))
    return out


def progress(frac: float, w: int, fill=None) -> str:
    fill = fill or green
    n = max(0, min(w, round(w * frac)))
    return fill("█" * n) + dim("░" * (w - n))


def wrap(text: str, w: int, indent: str = "") -> list[str]:
    """Plain greedy wrap. Input must be uncoloured."""
    words, line, out = text.split(), "", []
    for word in words:
        cand = f"{line} {word}".strip()
        if len(cand) + len(indent) > w and line:
            out.append(indent + line)
            line = word
        else:
            line = cand
    if line:
        out.append(indent + line)
    return out
