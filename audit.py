"""Audit every recipe in the skill for the defects that have actually bitten."""
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

SKILL = Path(os.path.expanduser("~/.claude/skills/recipes"))
ROOT = SKILL / "recipes"
IMAGES = SKILL / "images"
LINKS = ["dough", "filling", "sauce", "shape", "base", "coating"]
STATUS = {"house", "tested", "drafted", "stub", "retired"}
SCORES = ["appearance", "texture", "flavor", "technique", "overall"]
NO_QTY = ("quantity not given", "quantity not recorded", "quantity not recorded yet",
          "to taste", "q.b.", "as needed")

recipes = []
for md in sorted(ROOT.rglob("*.md")):
    text = md.read_text(encoding="utf-8")
    head = text.split("## ", 1)[0]
    meta, order = {}, []
    for k, v in re.findall(r"^- ([A-Za-z][A-Za-z /'-]*):\s*(.*)$", head, re.M):
        key = k.strip().lower()
        meta[key] = v.strip()
        order.append(key)
    blocks = {h.strip().lower(): [x for x in b.splitlines() if x.strip()]
              for h, b in re.findall(r"^## (.+?)$\n(.*?)(?=^## |\Z)", text, re.S | re.M)}
    title = re.match(r"# (.+)", text)
    recipes.append({"p": md, "rel": md.relative_to(ROOT), "text": text, "meta": meta,
                    "order": order, "blocks": blocks,
                    "title": title.group(1).strip() if title else None,
                    "stem": md.stem})

cook = [r for r in recipes if r["rel"].parts[0] != "ingredients"]
stems = {r["stem"] for r in recipes}
problems = defaultdict(list)


def flag(kind, r, detail=""):
    problems[kind].append(f"{r['rel']}{'  ' + detail if detail else ''}")


for r in recipes:
    m, rel = r["meta"], r["rel"]
    if not r["title"]:
        flag("no H1", r)
    if m.get("section") != rel.parts[0]:
        flag("Section mismatch", r, f"{m.get('section')!r} vs dir {rel.parts[0]!r}")
    st = (m.get("status") or "").lower()
    if st not in STATUS:
        flag("bad Status", r, repr(m.get("status")))
    if len(r["order"]) != len(set(r["order"])):
        dup = [k for k, n in Counter(r["order"]).items() if n > 1]
        flag("duplicate metadata key", r, str(dup))
    if "--" in r["text"]:
        flag("double hyphen", r)
    for key in LINKS:
        for ref in [x.strip() for x in (m.get(key) or "").split(",") if x.strip()]:
            if ref not in stems:
                flag("part link resolves to nothing", r, f"{key}: {ref}")
    img = m.get("image")
    if img and not (SKILL / img).exists():
        flag("missing image file", r, img)
    graded = [k for k in SCORES if m.get(k)]
    if graded and st in ("drafted", "stub"):
        flag("graded but still drafted", r, f"{graded} status={st}")
    if st == "tested" and not m.get("overall") and rel.parts[0] != "ingredients":
        flag("tested but no Overall", r)

for r in cook:
    if not r["blocks"].get("method"):
        flag("no Method", r)
    shape = "03-shapes" in str(r["rel"])
    composed = any(r["meta"].get(k) for k in LINKS)
    if not r["blocks"].get("ingredients") and not shape and not composed:
        flag("no Ingredients", r, f"status={r['meta'].get('status')}")
    for line in r["blocks"].get("ingredients", []):
        s = line.strip()
        if s.startswith("- ") and ":" not in s:
            flag("ingredient with no colon", r, s[:60])

phr = Counter()
for r in recipes:
    for line in r["blocks"].get("ingredients", []):
        low = line.lower()
        for p in NO_QTY:
            if low.rstrip().endswith(": " + p) or low.rstrip().endswith(p):
                phr[p] += 1
                break

titles = defaultdict(list)
for r in recipes:
    if r["title"]:
        titles[r["title"].lower()].append(str(r["rel"]))
dupe_titles = {t: v for t, v in titles.items() if len(v) > 1}

used = {m.get("image") for m in (r["meta"] for r in recipes) if m.get("image")}
on_disk = {f"images/{p.name}" for p in IMAGES.glob("*.jpg")}
orphan_images = sorted(on_disk - used)

src = {}
for r in recipes:
    if r["meta"].get("source"):
        src[r["meta"]["source"]] = src.get(r["meta"]["source"], 0) + 1

print(f"{len(recipes)} files, {len(cook)} recipes, {len(recipes) - len(cook)} ingredients\n")
total = 0
for kind in sorted(problems):
    rows = problems[kind]
    total += len(rows)
    print(f"{kind}  ({len(rows)})")
    for row in rows[:8]:
        print(f"    {row}")
    if len(rows) > 8:
        print(f"    ... {len(rows) - 8} more")
print(f"\n{total} flagged items\n")

print("missing-quantity wording in use:")
for p, n in phr.most_common():
    print(f"  {n:4d}  {p}")
print(f"\nduplicate titles: {len(dupe_titles)}")
for t, v in dupe_titles.items():
    print(f"  {t!r}: {v}")
print(f"\norphan images ({len(orphan_images)}): {orphan_images}")
print(f"\nSource strings in use ({len(src)}):")
for s, n in sorted(src.items(), key=lambda kv: -kv[1])[:14]:
    print(f"  {n:4d}  {s}")
