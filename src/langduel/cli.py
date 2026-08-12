"""¡Duelo! — a terminal Spanish/English trainer that fights back.

Run:  ./play      (or  python3 -m langduel)
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from . import lineage, ui
from .engine import DEFAULT_PROFILE, Profile, Question, Selector, grade
from .ui import (bar, blue, bold, clip, dim, green, magenta, orange, pad,
                 panel, progress, red, rule, split_row, violet, wrap, yellow)

FLAG = {"es": "ESPAÑOL", "en": "ENGLISH"}
TINT = {"es": orange, "en": blue}

CHEERS = ("¡Eso!", "¡Dale!", "Clean.", "¡Perfecto!", "Nailed it.", "¡Qué crack!", "Sí señor.")
CONSOLE = ("Casi.", "Not this time.", "The verb wins this round.", "Anótalo.",
           "Next one's yours.")
CLOSE = ("So close — spelling only.", "Right word, wrong dress.", "Accent gremlins.")

# A sound-law card surfaces this often, when an unseen one is available.
PATTERN_EVERY = 9
DISCOVERY_XP = 15


class App:
    """Owns the screen. One instance per session."""

    def __init__(self, profile: Profile, selector: Selector, rng: random.Random) -> None:
        self.p = profile
        self.sel = selector
        self.rng = rng
        self.n = 0
        self.body: list[str] = []      # feedback area, rebuilt each round
        self.toast = ""                # one-line status under the header

    # -- chrome ----------------------------------------------------------
    def header(self, w: int) -> list[str]:
        p = self.p
        title = bold(magenta("¡DUELO!")) + dim("  english ⇄ español")
        streak = f"  {orange('^' + str(p.streak))}" if p.streak >= 3 else ""
        record = (f"{dim('W')} {green(str(p.wins))}  {dim('L')} {red(str(p.losses))}  "
                  f"{dim('~')} {yellow(str(p.close_calls))}{streak}  "
                  f"{dim('·')}  {bold(str(p.xp))} {dim('xp')}")
        total = p.wins + p.losses
        pct = 100 * p.wins / total if total else 0.0
        sub_left = (f"{violet(p.rank())}  {dim('·')}  "
                    f"{bold(green(str(p.understood())))} {dim('words understood')}")
        sub_right = (f"{dim('mix')} {int(100 * p.es_bias())}{dim('% es')}  "
                     f"{progress(pct / 100, 10)} {dim(f'{pct:.0f}%')}")
        return [
            bar(w),
            split_row(title, record, w),
            split_row(sub_left, sub_right, w),
            bar(w),
        ]

    def footer(self, w: int) -> list[str]:
        return [rule(w),
                dim("  :h hint   :e origin   :l library   :p patterns   "
                    ":stats   :q quit")]

    def draw(self, q: Question | None, prompt_line: bool = True) -> None:
        w = ui.width()
        ui.clear()
        out = self.header(w)
        if self.toast:
            out.append("  " + self.toast)
        out.append("")

        if q is not None:
            tint = TINT[q.target_lang]
            tag = f"{dim('#' + str(self.n))}  {tint('▶ answer in ' + FLAG[q.target_lang])}"
            out.append(split_row("  " + tag, dim(q.hint) + "  ", w))
            out.append("")
            out.append("      " + bold(clip(q.prompt, w - 8)))
            out.append("")

        out.extend(self.body)
        sys.stdout.write("\n".join(out) + "\n")
        if prompt_line:
            sys.stdout.write("\n" + rule(w) + "\n")
            sys.stdout.write("  " + TINT[q.target_lang]("▸ ") if q else "  ▸ ")
        sys.stdout.flush()

    def ask(self, q: Question) -> str:
        self.draw(q)
        try:
            return input().strip()
        except EOFError:
            return ":q"

    def pause(self, q: Question | None = None, label: str = "enter to continue") -> None:
        w = ui.width()
        self.draw(q, prompt_line=False)
        sys.stdout.write("\n" + rule(w) + "\n  " + dim(label + " ") + "▸ ")
        sys.stdout.flush()
        try:
            input()
        except EOFError:
            pass

    # -- screens ---------------------------------------------------------
    def screen(self, lines: list[str], label: str = "enter to return") -> None:
        w = ui.width()
        ui.clear()
        sys.stdout.write("\n".join(self.header(w) + [""] + lines) + "\n")
        sys.stdout.write("\n" + rule(w) + "\n  " + dim(label + " ") + "▸ ")
        sys.stdout.flush()
        try:
            input()
        except EOFError:
            pass

    def stats_lines(self, w: int) -> list[str]:
        p = self.p
        total = p.wins + p.losses
        pct = 100 * p.wins / total if total else 0.0
        rows = [
            f"wins {green(str(p.wins))}   losses {red(str(p.losses))}   "
            f"close calls {yellow(str(p.close_calls))}",
            f"streak {bold(str(p.streak))}   best {bold(str(p.best_streak))}   "
            f"xp {bold(str(p.xp))}   rank {violet(p.rank())}",
            f"accuracy {progress(pct / 100, 20)} {pct:.0f}%   over {p.rounds} answers",
            "",
            f"words understood both ways   {bold(green(str(p.understood())))}"
            + dim("   (correct twice in each direction)"),
            f"verbs drilled                {bold(str(p.verbs_drilled()))}",
            f"lineages unearthed           {bold(violet(str(len(p.discovered))))}"
            + dim(f" / {len(lineage.ORIGINS)}"),
            f"sound laws learned           {bold(violet(str(len(p.patterns_seen))))}"
            + dim(f" / {len(lineage.PATTERNS)}"),
            f"content tier                 {bold(str(p.unlocked_level))}/3"
            + dim("   (12 understood words per tier)"),
            "",
        ]
        for lang in ("en", "es"):
            att, hit = p.lang_record[lang]
            acc = 100 * p.accuracy(lang)
            flag = TINT[lang](pad(FLAG[lang], 8))
            weak = yellow("  ← most wrong, so most asked") if lang == p.weakest_lang() and att else ""
            rows.append(f"producing {flag} {hit}/{att}  {progress(acc / 100, 14)} "
                        f"{acc:.0f}%{weak}")
        rows += ["", dim(f"next question: {int(100 * p.es_bias())}% chance Spanish, "
                         f"{100 - int(100 * p.es_bias())}% English")]
        return panel("SCORECARD", rows, w)

    def library_lines(self, w: int) -> list[str]:
        p = self.p
        if not p.discovered:
            return panel("LIBRARY", [
                "Nothing unearthed yet.",
                "",
                "Every word and verb with a known ancestry hands you its story",
                "the first time you meet it. They collect here.",
            ], w, colour=violet)
        rows: list[str] = []
        for key in p.discovered:
            o = lineage.ORIGINS.get(key)
            if not o:
                continue
            rows.append(f"{bold(violet(key))}  {dim('<')}  {o.root}")
            if o.cousins and o.cousins != "none":
                rows.extend(wrap(f"english: {o.cousins}", w - 8, "    "))
            rows.append("")
        rows.append(dim(f"{len(p.discovered)} of {len(lineage.ORIGINS)} lineages"))
        return panel("LIBRARY — what you've unearthed", rows, w, colour=violet)

    def patterns_lines(self, w: int) -> list[str]:
        rows: list[str] = []
        for pat in lineage.PATTERNS:
            seen = pat.pid in self.p.patterns_seen
            mark = green("✓") if seen else dim("·")
            rows.append(f"{mark} {bold(violet(pat.title)) if seen else dim(pat.title)}")
            if seen:
                ex = ", ".join(f"{a} = {b.split(',')[0]}" for a, b in pat.examples[:3])
                rows.extend(wrap(ex, w - 8, "    "))
            rows.append("")
        rows.append(dim(f"{len(self.p.patterns_seen)} of {len(lineage.PATTERNS)} learned — "
                        "each one unlocks a whole family of cognates"))
        return panel("SOUND LAWS", rows, w, colour=violet)

    # -- cards -----------------------------------------------------------
    def expansion_card(self, q: Question) -> None:
        if q.expansion:
            self.body.extend(panel("conjugation", q.expansion, ui.width()))

    def origin_card(self, q: Question, force: bool = False) -> int:
        """Show ancestry. Returns bonus XP for a first-time discovery."""
        o = q.origin
        if o is None:
            if force:
                self.toast = dim("no recorded ancestry for that one")
            return 0
        first = q.origin_key not in self.p.discovered
        if not first and not force:
            return 0
        w = ui.width()
        rows = wrap(o.root, w - 8)
        if o.cousins and o.cousins != "none":
            rows += wrap(f"english cousins: {o.cousins}", w - 8)
        if o.hook:
            rows += [""] + [dim(x) for x in wrap(o.hook, w - 8)]
        title = f"lineage · {q.origin_key}" + ("  ★ new" if first else "")
        self.body.extend(panel(title, rows, w, colour=violet))
        if first:
            self.p.discovered.append(q.origin_key)
            return DISCOVERY_XP
        return 0

    def pattern_card(self, pid: str = "") -> bool:
        pool = [p for p in lineage.PATTERNS if p.pid not in self.p.patterns_seen]
        pat = lineage.PATTERNS_BY_ID.get(pid) if pid else (pool[0] if pool else None)
        if pat is None:
            return False
        w = ui.width()
        rows = wrap(pat.rule, w - 8) + [""]
        for es, en in pat.examples:
            rows.append(f"   {bold(pad(es, 18))} {dim('=')} {en}")
        rows += [""] + [green(x) for x in wrap(pat.payoff, w - 8)]
        self.body.extend(panel(f"sound law · {pat.title}", rows, w, colour=violet))
        if pat.pid not in self.p.patterns_seen:
            self.p.patterns_seen.append(pat.pid)
        return True

    # -- round -----------------------------------------------------------
    def round(self) -> bool:
        """Play one question. Returns False when the player quits."""
        q = self.sel.next()
        self.n += 1
        self.body = []
        used_hint = False

        while True:
            answer = self.ask(q)
            low = answer.lower()
            self.toast = ""

            if low in (":q", ":quit", "quit", "exit"):
                return False
            if low in (":stats", ":score", ":s"):
                self.screen(self.stats_lines(ui.width()))
                continue
            if low in (":l", ":lib", ":library"):
                self.screen(self.library_lines(ui.width()))
                continue
            if low in (":p", ":patterns"):
                self.screen(self.patterns_lines(ui.width()))
                continue
            if low in (":e", ":etym", ":origin"):
                self.p.xp += self.origin_card(q, force=True)
                continue
            if low in (":h", ":hint"):
                masked = " ".join(
                    word[0] + "·" * (len(word) - 1) if len(word) > 1 else word
                    for word in q.canonical.split()
                )
                self.toast = f"{yellow('hint')}  {bold(masked)}  {dim(f'({len(q.canonical)} chars)')}"
                used_hint = True
                continue
            if low in (":skip", ":next"):
                self.body.append(f"  {dim('skipped →')} {bold(q.canonical)}")
                self.p.record(q, "miss")
                break
            if low in (":help", "?"):
                self.screen(self.help_lines(ui.width()))
                continue

            result = grade(answer, q.accepted)
            if used_hint and result == "hit":
                result = "close"  # a hinted win is a half win — keeps the stats honest
            gained = self.p.record(q, result)

            if result == "hit":
                tail = ("   " + orange("^" * min(self.p.streak // 3, 6))
                        + dim(f" streak {self.p.streak}")) if self.p.streak >= 3 else ""
                self.body.append(f"  {green('✔ ' + self.rng.choice(CHEERS))}  "
                                 f"{dim('+' + str(gained) + ' xp')}{tail}")
            elif result == "close":
                self.body.append(f"  {yellow('~ ' + self.rng.choice(CLOSE))}  it's "
                                 f"{bold(q.canonical)}  {dim('+' + str(gained) + ' xp')}")
            else:
                alts = [a for a in q.accepted[1:] if q.canonical not in a][:2]
                extra = dim("    also ok: " + ", ".join(alts)) if alts else ""
                self.body.append(f"  {red('✘ ' + self.rng.choice(CONSOLE))}  answer: "
                                 f"{bold(q.canonical)}{extra}")
            break

        self.body.append("")
        self.expansion_card(q)
        bonus = self.origin_card(q)
        if bonus:
            self.p.xp += bonus
            self.body.append(f"  {violet('★ lineage unearthed')} {dim('+' + str(bonus) + ' xp')}")

        # A sound law lands best right after a word that demonstrates it;
        # otherwise drip-feed the next unseen one on a schedule.
        o = q.origin
        if o is not None and o.pattern and o.pattern not in self.p.patterns_seen:
            self.pattern_card(o.pattern)
        elif self.n % PATTERN_EVERY == 0:
            self.pattern_card()

        self.p.save()  # every single round — quitting can never cost you progress
        self.pause(q)
        return True

    def help_lines(self, w: int) -> list[str]:
        return panel("HOW THIS WORKS", [
            bold("The mix follows your weakness."),
            "Accuracy is tracked separately for each language you have to",
            "produce. Whichever side you miss more, the more it gets asked —",
            "up to 85%. Within a language, your specific weak items resurface.",
            "",
            bold("Words count as understood only both ways."),
            "Two correct answers producing English AND two producing Spanish.",
            "Misses take the credit back. That counter is the real score.",
            "",
            bold("Every verb expands."),
            "Answer one and you get the whole six-person paradigm for that",
            "tense, plus the stem-change note.",
            "",
            bold("Lineage."),
            "Words with known ancestry hand it over the first time you meet",
            "them (+15 xp). Sound laws — the rules that convert English to",
            "Spanish wholesale — surface as you play. Both collect in :l and :p.",
            "",
            bold("Near misses are forgiven."),
            "A dropped accent or one-character typo scores as close: partial",
            "xp, streak survives, no loss recorded. Winning after a hint also",
            "scores close.",
            "",
            dim("commands   :h hint  :e origin  :l library  :p patterns  "
                ":stats  :skip  :q quit"),
            dim(f"progress saved to {self.p.path} after every round"),
        ], w)


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def play(profile_path: Path, rounds: int, seed: int | None, verb_share: float) -> int:
    rng = random.Random(seed)
    p = Profile.load(profile_path)
    app = App(p, Selector(p, rng=rng, verb_share=verb_share), rng)
    start = p.wins, p.losses, p.understood(), len(p.discovered)

    ui.enter_app()
    try:
        if p.rounds:
            app.toast = dim(f"welcome back — {p.wins}W/{p.losses}L, {p.understood()} words "
                            f"understood, {len(p.discovered)} lineages")
        else:
            app.body = app.help_lines(ui.width())
            app.pause(None, "enter to start")
            app.body = []
        while rounds <= 0 or app.n < rounds:
            if not app.round():
                break
        p.save()
        farewell(app, start)
    finally:
        ui.leave_app()
    return 0


def farewell(app: App, start: tuple[int, int, int, int]) -> None:
    p = app.p
    w0, l0, u0, d0 = start
    ui.clear()
    w = ui.width()
    lines = app.stats_lines(w) + [""]
    lines.append("  this session:  "
                 f"{green('+' + str(p.wins - w0))} wins   "
                 f"{red('+' + str(p.losses - l0))} losses   "
                 f"{bold('+' + str(p.understood() - u0))} words understood   "
                 f"{violet('+' + str(len(p.discovered) - d0))} lineages")
    lines.append(dim(f"  saved to {p.path}"))
    lines.append("")
    lines.append("  " + bold("¡Hasta la próxima!"))
    text = "\n".join(app.header(w) + [""] + lines) + "\n"
    ui.leave_app()          # drop back to the real screen so this survives
    sys.stdout.write(text + "\n")


def cmd_stats(path: Path) -> int:
    p = Profile.load(path)
    app = App(p, Selector(p), random.Random())
    w = ui.width()
    print("\n".join(app.header(w) + [""] + app.stats_lines(w)))
    return 0


def cmd_library(path: Path) -> int:
    p = Profile.load(path)
    app = App(p, Selector(p), random.Random())
    w = ui.width()
    print("\n".join(app.header(w) + [""] + app.library_lines(w)
                    + [""] + app.patterns_lines(w)))
    return 0


def cmd_reset(path: Path) -> int:
    if path.exists():
        path.unlink()
        print(f"  wiped {path}")
    else:
        print("  nothing to reset")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="langduel",
        description="English ⇄ Spanish drill that leans on your weak side.",
    )
    ap.add_argument("--rounds", type=int, default=0, help="stop after N questions (0 = endless)")
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE, help="scorecard file")
    ap.add_argument("--seed", type=int, default=None, help="deterministic question order")
    ap.add_argument("--verbs", type=float, default=0.4, metavar="P",
                    help="share of questions that are conjugations (0-1, default 0.4)")
    ap.add_argument("--stats", action="store_true", help="print the scorecard and exit")
    ap.add_argument("--library", action="store_true",
                    help="print collected etymologies and sound laws, then exit")
    ap.add_argument("--reset", action="store_true", help="delete the saved profile")
    a = ap.parse_args(argv)

    if a.reset:
        return cmd_reset(a.profile)
    if a.stats:
        return cmd_stats(a.profile)
    if a.library:
        return cmd_library(a.profile)
    try:
        return play(a.profile, a.rounds, a.seed, min(max(a.verbs, 0.0), 1.0))
    except KeyboardInterrupt:
        ui.leave_app()
        print("\n" + dim("  ctrl-c — progress saved. ¡Adiós!"))
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
