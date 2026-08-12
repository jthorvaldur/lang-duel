"""¡Lucha Léxica! — terminal presentation and the fight loop.

Run:  ./duelo.py  (or `python3 -m lucha` from the mirror directory)
All teaching content lives in lucha/content/<pack>/*.json — see AGENTS.md.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

from . import content
from .content import Opponent, Pack
from .engine import DEFAULT_SAVE, Profile, Question, Selector, grade

PLAYER_HP = 10

# --------------------------------------------------------------------------
# Colour
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


# --------------------------------------------------------------------------
# Presentation
# --------------------------------------------------------------------------


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


def scorecard(p: Profile, pack: Pack) -> None:
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
    beaten = p.ladder_progress % len(pack.opponents)
    print("  ladder: " + "  ".join(
        (green("✓ ") if i < beaten else bold("▶ ") if i == beaten else dim("· ")) + o.name
        for i, o in enumerate(pack.opponents)))
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


def play(pack: Pack, path: Path, rounds: int, seed: int | None) -> int:
    rng = random.Random(seed)
    p = Profile.load(path)
    sel = Selector(pack, p, rng)
    opponents = pack.opponents

    banner()
    if p.wins + p.losses:
        print(dim(f"  welcome back to the ring — {p.wins}W/{p.losses}L, "
                  f"{len(p.dominated())} dominadas, rank {p.rank()}"))

    start = (p.wins, p.losses, len(p.dominated()))
    idx = p.ladder_progress % len(opponents)
    season = p.ladder_progress // len(opponents) + 1
    opp = opponents[idx]
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
                farewell(p, pack, start)
                return 0
            if low in (":card", ":stats"):
                scorecard(p, pack)
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
            idx = p.ladder_progress % len(opponents)
            season = p.ladder_progress // len(opponents) + 1
            if idx == 0:
                print(bold(magenta("  🏆 ¡CAMPEÓN! The ladder resets — "
                                   "new season, meaner rivals.")))
            opp = opponents[idx]
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
            scorecard(p, pack)
            p.save()

    p.save()
    farewell(p, pack, start)
    return 0


def farewell(p: Profile, pack: Pack, start: tuple[int, int, int]) -> None:
    w, l, d = start
    scorecard(p, pack)
    print(f"  this session: {green('+' + str(p.wins - w))} wins, "
          f"{red('+' + str(p.losses - l))} losses, "
          f"{bold('+' + str(len(p.dominated()) - d))} new dominadas")
    print(dim(f"  saved to {p.path}"))
    print(bold("  ¡Hasta la revancha! 👋\n"))


# --------------------------------------------------------------------------
# --check: the content-edit feedback loop
# --------------------------------------------------------------------------


def cmd_check(pack_name: str) -> int:
    try:
        pack = content.load_pack(pack_name)
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(red(f"  pack {pack_name!r} failed to load: {e}"))
        return 1
    errors = content.validate(pack)

    # smoke: every opponent must be able to serve well-formed questions
    rng = random.Random(0)
    n_questions = 0
    for opp in pack.opponents:
        sel = Selector(pack, Profile(), rng)
        for _ in range(200):
            q = sel.next(opp)
            n_questions += 1
            if not q.accepted or not q.canonical:
                errors.append(f"smoke: bad question from {opp.name}: {q.key!r}")

    print(f"  pack {pack.name!r}: {len(pack.words)} words · {len(pack.verbs)} verbs · "
          f"{len(pack.clozes)} clozes · {len(pack.traps)} traps · "
          f"{len(pack.opponents)} opponents")
    print(f"  gender drills: {sum(1 for w in pack.words if w.article)} · "
          f"sentence verbs: {len(pack.pairs)} · places: {len(pack.places)} · "
          f"smoke: {n_questions} questions")
    if errors:
        print(red(f"  ✘ {len(errors)} problem(s):"))
        for e in errors:
            print(red(f"    - {e}"))
        return 1
    print(green("  ✔ pack is sound"))
    return 0


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
    ap.add_argument("--profile", type=Path, default=DEFAULT_SAVE, help="scorecard file")
    ap.add_argument("--pack", default=content.DEFAULT_PACK, help="content pack name")
    ap.add_argument("--stats", action="store_true", help="print the card and exit")
    ap.add_argument("--reset", action="store_true", help="delete the saved profile")
    ap.add_argument("--check", action="store_true",
                    help="validate the content pack and exit")
    a = ap.parse_args(argv)

    if a.reset:
        a.profile.unlink(missing_ok=True)
        print(f"  wiped {a.profile}")
        return 0
    try:
        pack = content.load_pack(a.pack)
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"  cannot load pack {a.pack!r}: {e}")
        return 1
    if a.check:
        return cmd_check(a.pack)
    if a.stats:
        scorecard(Profile.load(a.profile), pack)
        return 0
    try:
        return play(pack, a.profile, a.rounds, a.seed)
    except KeyboardInterrupt:
        print("\n" + dim("  ctrl-c — the card is saved. ¡Adiós!"))
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
