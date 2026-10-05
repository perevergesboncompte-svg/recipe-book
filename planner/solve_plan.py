"""Order the pasta dishes into weeks.

Three passes. Availability is a hard gate and character a soft one, so each dish
gets a feasible week set from their intersection. The most constrained dishes
claim a week first, because a chanterelle dish has four candidate months and
fettuccine alfredo has twelve. Then each month's dishes are permuted to put
shared batches and repeated shapes side by side.
"""
import itertools
import json
from collections import defaultdict
from datetime import date, timedelta

from character import CHARACTER, CONTORNI_CHARACTER
from drivers import DRIVERS, REUSE

ALL = set(range(1, 13))
WINDOWS = {
    "white truffle": {10, 11, 12},
    "black winter truffle": {11, 12, 1, 2, 3},
    "black summer truffle": {5, 6, 7, 8, 9},
    "chanterelle": {12, 1, 2, 3},
    "porcini": {10, 11, 12, 1},
    "matsutake": {9, 10, 11, 12, 1, 2},
    "delicata squash": {9, 10, 11, 12},
    "jerusalem artichoke": {9, 10, 11, 12, 1, 2, 3, 4, 5},
    "romano beans": {6, 7, 8, 9, 10},
    "dungeness crab": {12, 1, 2, 3, 4},
    "spot prawn": set(range(2, 11)),
    "english peas": {11, 12, 1, 2, 3, 4, 5, 6},
    "granny smith apple": ALL - {7},
}
FIELD = {"cherry tomatoes": {4, 5, 6, 7, 8, 9, 10, 11}}
YEAR_ROUND = {
    "basil", "sage", "savoy cabbage", "broccoli rabe", "butternut squash",
    "kabocha squash", "japanese eggplant", "fennel bulb", "spinach",
    "watercress", "celeriac", "artichoke", "sugar snap peas",
}
CONTORNI = set(CONTORNI_CHARACTER)
inp = {r["stem"]: r for r in json.load(open("season_inputs.json"))}


def gate(stem):
    months, gates = set(ALL), []
    for ing in DRIVERS[stem]:
        if ing in YEAR_ROUND:
            continue
        months &= FIELD.get(ing) or WINDOWS[ing]
        gates.append(ing)
    return months, gates


dishes = [s for s in DRIVERS if s not in CONTORNI]
shared = defaultdict(list)
for s in dishes:
    for k in ("filling", "sauce"):
        for ref in [x.strip() for x in (inp[s]["parts"].get(k) or "").split(",") if x.strip()]:
            shared[ref].append(s)
chains_full = {k: v for k, v in shared.items() if len(v) > 1}
chains = set(chains_full)

START = date(2026, 10, 5)
weeks = [START + timedelta(weeks=i) for i in range(len(dishes))]
info = {s: gate(s) for s in dishes}

feasible = {}
for s in dishes:
    avail = info[s][0]
    want = avail & CHARACTER[s]
    ok = [i for i, d in enumerate(weeks) if d.month in (want or avail)]
    feasible[s] = ok or [i for i, d in enumerate(weeks) if d.month in avail]

def month_gap(month, wanted):
    return min(min((month - w) % 12, (w - month) % 12) for w in wanted)


slot, taken = {}, {}
for s in sorted(dishes, key=lambda x: (len(feasible[x]), x)):
    free = [i for i in feasible[s] if i not in taken]
    if free:
        pick = min(free, key=lambda i: (sum(1 for o in dishes
                                            if o not in slot and i in feasible[o]), i))
    else:
        wanted = info[s][0] & CHARACTER[s] or info[s][0]
        pick = min((i for i in range(len(weeks)) if i not in taken),
                   key=lambda i: (month_gap(weeks[i].month, wanted), i))
    slot[s] = pick
    taken[pick] = s


KEEPS_WEEKS = 4

for ref, members in sorted(chains_full.items()):
    if len(members) != 2:
        continue
    a, b = sorted(members, key=lambda s: slot[s])
    if slot[b] - slot[a] <= KEEPS_WEEKS:
        continue
    for target in range(slot[a] + 1, slot[a] + KEEPS_WEEKS + 1):
        if target >= len(weeks):
            break
        other = taken[target]
        if target in feasible[b] and slot[b] in feasible[other]:
            taken[target], taken[slot[b]] = b, other
            slot[other], slot[b] = slot[b], target
            break


def bond(a, b):
    pa, pb = inp[a]["parts"], inp[b]["parts"]
    if any(v in chains for v in set(pa.values()) & set(pb.values())):
        return 3
    if pa.get("shape") and pa.get("shape") == pb.get("shape"):
        return 2
    if inp[a]["bucket"] == inp[b]["bucket"]:
        return 1
    return 0


by_month = defaultdict(list)
for i, d in enumerate(weeks):
    by_month[(d.year, d.month)].append(i)

for key, idxs in by_month.items():
    members = [taken[i] for i in idxs if i in taken]
    if len(members) < 2 or len(members) > 7:
        continue
    before = taken.get(min(idxs) - 1)

    def score(order):
        total = 0
        if before:
            total += bond(before, order[0])
        for x, y in zip(order, order[1:]):
            total += bond(x, y)
        return total

    best = max(itertools.permutations(members), key=score)
    for i, s in zip(idxs, best):
        taken[i] = s
        slot[s] = i

rows, made, used_side = [], set(), set()
for i, day in enumerate(weeks):
    s = taken[i]
    reuse = []
    for k in ("filling", "sauce"):
        for ref in [x.strip() for x in (inp[s]["parts"].get(k) or "").split(",") if x.strip()]:
            if ref in chains:
                first = min(slot[m] for m in chains_full[ref])
                near = i - first <= KEEPS_WEEKS
                reuse.append(("reuse " if ref in made and near else "make ") + ref)
                made.add(ref)
    also = list(REUSE.get(s, []))
    for c in sorted(CONTORNI):
        if c in used_side:
            continue
        cm, _ = gate(c)
        if day.month in cm and day.month in CONTORNI_CHARACTER[c]:
            also.append(c)
            used_side.add(c)
            break
    rows.append({"week": i + 1, "day": day.isoformat(), "stem": s,
                 "reuse": "; ".join(reuse), "also": also,
                 "season": ", ".join(info[s][1]) or "year-round"})

off = [r for r in rows if date.fromisoformat(r["day"]).month not in info[r["stem"]][0]]
bad = [r for r in rows if date.fromisoformat(r["day"]).month not in CHARACTER[r["stem"]]]
runs = sum(1 for a, b in zip(rows, rows[1:]) if bond(a["stem"], b["stem"]) >= 2)
print(f"{len(rows)} weeks, {len(off)} outside availability, "
      f"{len(bad)} outside character, {runs} adjacent shape or batch pairs")
for r in off:
    print("  AVAIL", r["week"], r["day"], r["stem"], sorted(info[r["stem"]][0]))
for r in bad:
    print("  CHAR ", r["week"], r["day"], r["stem"], sorted(CHARACTER[r["stem"]]))
json.dump(rows, open("plan_rows.json", "w"), indent=1)
