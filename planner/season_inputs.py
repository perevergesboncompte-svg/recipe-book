"""Every pasta dish and contorno with its shape, parts and ingredient names."""
import json
import re
from pathlib import Path

ROOT = Path.home() / ".claude/skills/recipes/recipes"
LINKS = ["dough", "filling", "sauce", "shape", "base", "coating"]
TARGETS = ["pasta/04-dishes", "pasta/05-contorni"]

out = []
for t in TARGETS:
    for md in sorted((ROOT / t).rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        head = text.split("## ", 1)[0]
        meta = {k.strip().lower(): v.strip() for k, v in
                re.findall(r"^- ([A-Za-z][A-Za-z /'-]*):\s*(.*)$", head, re.M)}
        m = re.search(r"^## Ingredients\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
        ings = []
        if m:
            for line in m.group(1).splitlines():
                line = line.strip()
                if line.startswith("- "):
                    ings.append(line[2:].rsplit(":", 1)[0].strip())
        out.append({
            "stem": md.stem,
            "title": re.match(r"# (.+)", text).group(1) if text.startswith("# ") else md.stem,
            "group": md.relative_to(ROOT / "pasta").parts[0],
            "bucket": md.parent.name,
            "region": meta.get("region", ""),
            "parts": {k: meta[k] for k in LINKS if meta.get(k)},
            "ingredients": ings,
        })

Path("season_inputs.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"{len(out)} dishes and contorni")
for r in out:
    print(f"\n{r['stem']}  [{r['bucket']}{' ' + r['region'] if r['region'] else ''}]")
    print("   parts:", r["parts"])
    print("   ing:", "; ".join(r["ingredients"]))
