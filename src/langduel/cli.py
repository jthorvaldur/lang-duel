"""¡Duelo! — a terminal Spanish/English trainer that fights back.

Run:  ./play      (or  python3 -m langduel)
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from . import aiid, content, lineage, ui
from .engine import (DEFAULT_PROFILE, STAGES, ForeignProfile, Profile,
                     Question, Selector, latin_face)
from .ui import (bar, blue, bold, clip, dim, green, magenta, orange, pad,
                 panel, progress, red, rule, split_row, violet, wrap, yellow)

FLAG = {"es": "ESPAÑOL", "en": "ENGLISH",
        "spot": "SPOT IT", "act": "ACT ON IT"}
TINT = {"es": orange, "en": blue, "spot": violet, "act": violet}

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
        subtitle = {"aiid": "spot it ⇄ act on it"}.get(
            getattr(self.sel, "domains", ("es",))[-1], "english ⇄ español")
        title = bold(magenta("¡DUELO!")) + dim("  " + subtitle)
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
            for line in (wrap(q.prompt, w - 10) if len(q.prompt) > w - 10 else [q.prompt]):
                out.append("      " + bold(line))
            out.append("")
            for i, opt in enumerate(q.options):
                letter = tint(bold(chr(ord("a") + i) + ")"))
                first, *rest = wrap(opt, w - 14) or [""]
                out.append(f"      {letter}  {first}")
                out.extend("         " + r for r in rest)
            if q.options:
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
        for pole in ("en", "es"):
            att, hit = p.axis_record.get(pole, [0, 0])
            acc = 100 * p.accuracy(pole)
            flag = TINT[pole](pad(FLAG[pole], 9))
            weak = yellow("  ← most asked") if pole == p.weakest("es") and att else ""
            rows.append(f"producing {flag} {hit}/{att}  {progress(acc / 100, 14)} "
                        f"{acc:.0f}%{weak}")
        rows += ["", dim(f"next question: {int(100 * p.es_bias())}% chance Spanish, "
                         f"{100 - int(100 * p.es_bias())}% English")]

        if any(p.axis_record.get(x, [0, 0])[0] for x in aiid.POLES):
            rows.append("")
            for pole in aiid.POLES:
                att, hit = p.axis_record.get(pole, [0, 0])
                acc = 100 * p.accuracy(pole)
                weak = yellow("  ← the gap") if pole == p.weakest("aiid") and att else ""
                rows.append(f"deepfake  {violet(pad(FLAG[pole], 9))} {hit}/{att}  "
                            f"{progress(acc / 100, 14)} {acc:.0f}%{weak}")

        rows += ["", f"stage {bold(str(p.stage() + 1))}/{len(STAGES)} "
                     f"{violet(p.stage_name())}" + dim(f" — {STAGES[p.stage()][2]}")]
        if p.cap is not None:
            rows.append(dim("      pinned here — drop --basic/--stage for the rest"))
        else:
            nxt = p.next_unlock()
            if nxt:
                blurb, togo = nxt
                rows.append(dim(f"      next unlock in {max(togo, 0)}: {blurb}"))
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

    def face_card(self, q: Question) -> None:
        """The unjudged ancestor face. Shown, never graded, never scored."""
        faces = latin_face(q)
        if not faces:
            return
        lang, head = next(iter(faces.items()))
        # Always show the headwords, never the inflected prompt — the ancestor
        # relates the dictionary forms, not "I speak" to fabulari.
        es = q.origin_key
        verb = content.VERBS_BY_NAME.get(q.origin_key)
        if verb is not None:
            en = verb.en
        else:
            word = next((w for w in content.WORDS if w.es == q.origin_key), None)
            en = word.en if word else (q.prompt if q.target_lang == "es" else q.canonical)
        chain = f"{bold(head)}  {dim('→')}  {orange(es)}   {dim('&')}   {blue(en)}"
        self.body.append(f"  {dim(lang + ':')} {chain}   {dim('(not graded)')}")

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
        stage_before = self.p.stage()

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

            verdict = q.decide(answer)
            result, note = verdict.result, verdict.note
            if result == "miss" and note:      # e.g. "answer with a letter"
                self.toast = yellow(note)
                continue
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
        if q.why:                       # safety drills explain themselves either way
            self.body.extend(panel("why", wrap(q.why, ui.width() - 8), ui.width(),
                                   colour=violet))
        if self.p.has("latin"):
            self.face_card(q)
        if not self.p.has("lineage"):   # early game stays deliberately bare
            if self.p.stage() > stage_before:
                name, _, blurb = STAGES[self.p.stage()]
                self.body.append("")
                self.body.append(
                    f"  {bold(magenta('★ UNLOCKED: ' + name.upper()))}  {dim(blurb)}")
            self.p.save()
            self.pause(q)
            return True
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

        if self.p.stage() > stage_before:
            name, _, blurb = STAGES[self.p.stage()]
            self.body.append("")
            self.body.append(f"  {bold(magenta('★ UNLOCKED: ' + name.upper()))}  {dim(blurb)}")

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


def play(profile_path: Path, rounds: int, seed: int | None, verb_share: float,
         domains: tuple[str, ...] = ("es",), cap: int | None = None) -> int:
    rng = random.Random(seed)
    p = Profile.load(profile_path)
    p.cap = cap
    app = App(p, Selector(p, rng=rng, verb_share=verb_share, domains=domains), rng)
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
    def signed(n: int) -> str:
        return f"+{n}" if n >= 0 else str(n)

    lines.append("  this session:  "
                 f"{green(signed(p.wins - w0))} wins   "
                 f"{red(signed(p.losses - l0))} losses   "
                 f"{bold(signed(p.understood() - u0))} words understood   "
                 f"{violet(signed(len(p.discovered) - d0))} lineages")
    lines.append(dim(f"  saved to {p.path}"))
    lines.append("")
    lines.append("  " + bold("¡Hasta la próxima!"))
    text = "\n".join(app.header(w) + [""] + lines) + "\n"
    ui.leave_app()          # drop back to the real screen so this survives
    sys.stdout.write(text + "\n")


def cmd_stats(path: Path) -> int:
    p = Profile.load(path)   # raises ForeignProfile, handled in main
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
    ap.add_argument("--basic", action="store_true",
                    help="the stripped-back early game: word pairs only, no panels, "
                         "no lineage — plays the same at any level of progress")
    ap.add_argument("--stage", type=int, default=None, metavar="N",
                    help=f"pin to stage 1-{len(STAGES)} instead of the earned one")
    ap.add_argument("--domain", default="es", choices=("es", "aiid", "mixed"),
                    help="es = Spanish (default), aiid = spotting fakes and "
                         "handling the call, mixed = both")
    ap.add_argument("--stats", action="store_true", help="print the scorecard and exit")
    ap.add_argument("--library", action="store_true",
                    help="print collected etymologies and sound laws, then exit")
    ap.add_argument("--reset", action="store_true", help="delete the saved profile")
    a = ap.parse_args(argv)

    try:
        if a.reset:
            return cmd_reset(a.profile)
        if a.stats:
            return cmd_stats(a.profile)
        if a.library:
            return cmd_library(a.profile)
    except ForeignProfile as e:
        print(f"\n  {red('refusing to load that profile')}\n  {e}\n")
        return 2
    domains = {"es": ("es",), "aiid": ("aiid",), "mixed": ("es", "aiid")}[a.domain]
    cap = 0 if a.basic else (max(0, min(a.stage - 1, len(STAGES) - 1))
                             if a.stage else None)
    try:
        return play(a.profile, a.rounds, a.seed, min(max(a.verbs, 0.0), 1.0), domains, cap)
    except ForeignProfile as e:
        print(f"\n  {red('refusing to load that profile')}\n  {e}\n")
        return 2
    except KeyboardInterrupt:
        ui.leave_app()
        print("\n" + dim("  ctrl-c — progress saved. ¡Adiós!"))
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
