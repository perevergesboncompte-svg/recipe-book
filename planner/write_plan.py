import json
from datetime import date
from pathlib import Path

OUT = Path.home() / ".claude/skills/recipes/plan.md"
rows = json.load(open("plan_rows.json"))

INTRO = """One pasta a week, ordered by what is actually buyable in Orange County rather than
by the Italian calendar the book assumes. Where a batch stretches, the week after spends
it, and where nothing chains, dishes sharing a shape sit together so the second attempt
builds on the first.

Availability is a hard constraint and the character of the dish a soft one. Savoy cabbage
is sold here in August, but pizzoccheri is cabbage, potato and fontina from the Alps, so it
sits in March. Two dishes break their own rule: timballo and the turkey ravioli land in
September because there are 31 cold-weather dishes and only 29 cold weeks in the run.

Four things worth knowing before you shop.

Wild mushrooms are triggered by rain, not by the date. Chanterelles want about six weeks of
regular rain and porcini come up a week to ten days after an inch of it, so a nominal window
can collapse into a short scramble or miss a dry year entirely. Almost none of this fruits
in Orange County: there are ten chanterelle records in sixteen years, no Boletus edulis
against 247 logged boletes, and no matsutake against 152 logged Tricholoma. Everything
arrives trucked or flown from Northern California and the Pacific Northwest, and the main
Los Angeles distributor carries neither fresh porcini nor matsutake, so those two weeks mean
mail order.

Dungeness crab has not matched its own statute for years. The season reads November 15 to
June 30, but whale-entanglement delays pushed the last one to January 5 and the 2026-27
season is still closed with no opener declared. The three crab weeks sit in December on
paper and will probably move to January.

Southern California truffle supply stops short of the Italian legal season. Alba white
truffle is importable to the end of January but US importers stop in December, so October
to December is the real window. Black winter truffle peaks in January and February.

Most of what looks seasonal here is not. Artichoke, fennel, broccoli rabe, savoy cabbage,
basil, cherry tomatoes, butternut and kabocha squash, Japanese eggplant, watercress,
spinach, celeriac and lemon all hold year-round, through the Salinas and Imperial Valley
relay, through storage, or on imports. Cherry tomatoes are the exception worth respecting:
sold every month on Canadian greenhouse supply, but the two dishes built on sweet raw
tomatoes are placed in the California field season instead."""


def main():
    seen_side = set()
    lines = ["# Plan", "", INTRO, "",
             "| Week | Starting | Pasta | In season | Also cook, from the same batch |",
             "|---|---|---|---|---|"]
    for r in rows:
        day = date.fromisoformat(r["day"])
        also = []
        if r["reuse"]:
            also.append(r["reuse"].replace("-", " "))
        for ref in r["also"]:
            stem = ref.split("/")[-1]
            if stem not in seen_side or ref.startswith("pasta"):
                also.append(stem)
            seen_side.add(stem)
        lines.append(f"| {r['week']} | {day.strftime('%-d %b %Y')} | {r['stem']} "
                     f"| {r['season']} | {', '.join(dict.fromkeys(also))} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT} written, {len(rows)} weeks")


if __name__ == "__main__":
    main()
