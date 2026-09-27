#!/usr/bin/env python3
"""Render the recipes skill's markdown into a static site.

Source of truth is the skill's own files, so the site never diverges from the
collection the assistant maintains:

    ~/.claude/skills/recipes/profile.md
    ~/.claude/skills/recipes/journal.md
    ~/.claude/skills/recipes/recipes/<section>/<slug>.md

Pages are written to the repository root, which is what GitHub Pages serves.

    python3 build.py

The published pages carry noindex and the repo disallows crawlers, but Pages on a
free account serves publicly, so the build refuses to write any file containing
the local username.
"""

import html
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL = Path(os.path.expanduser("~/.claude/skills/recipes"))
ROOT = Path(__file__).parent
NOTES = ROOT / "notes"

SECTIONS = [
    ("baking", "Baking"),
    ("pasta", "Pasta"),
    ("croquetas", "Croquetas"),
    ("empanadas", "Empanadas"),
]

STATUS_ORDER = ["house", "tested", "drafted", "stub", "retired"]
STATUS_CLASS = {
    "house": "s-house", "tested": "s-tested", "drafted": "s-draft",
    "stub": "s-stub", "retired": "s-retired",
}
STATUS_HELP = {
    "house": "the settled formula, cook from this one",
    "tested": "made at least once and it worked",
    "drafted": "written down but not yet made",
    "stub": "incomplete, no method recorded",
    "retired": "superseded, kept for reference",
}

META_ORDER = ["category", "yield", "makes", "serves", "unit weight", "active time",
              "rest", "total time", "oven", "price", "tags", "source"]
BODY_ORDER = ["ingredients", "method", "notes", "learnings"]

CSSVER = ""


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "item"


def esc(s):
    return html.escape(s or "")


def inline(s):
    """Escape, then honour the one inline mark recipes actually use."""
    out = esc(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def parse_recipe(path, section):
    """Metadata is the `- Key: value` run before the first heading."""
    name = path.stem.replace("-", " ").title()
    meta, order, blocks = {}, [], []
    cur = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            name = line[2:].strip()
            continue
        if line.startswith("## "):
            cur = {"heading": line[3:].strip(), "lines": []}
            blocks.append(cur)
            continue
        if cur is not None:
            cur["lines"].append(line)
            continue
        m = re.match(r"^- ([A-Za-z][A-Za-z ]*?):\s*(.*)$", line)
        if m:
            key = m.group(1).strip().lower()
            meta[key] = m.group(2).strip()
            order.append(key)
    status = (meta.get("status") or "").lower() or "stub"
    return {
        "name": name,
        "slug": path.stem,
        "section": section,
        "status": status,
        "meta": meta,
        "order": order,
        "blocks": blocks,
        "url": f"recipes/{section}-{path.stem}.html",
    }


def parse_recipes():
    out = {}
    for key, _ in SECTIONS:
        d = SKILL / "recipes" / key
        out[key] = [parse_recipe(f, key) for f in sorted(d.glob("*.md"))] if d.is_dir() else []
        out[key].sort(key=lambda r: (STATUS_ORDER.index(r["status"])
                                     if r["status"] in STATUS_ORDER else 99,
                                     r["name"].lower()))
    return out


def parse_journal():
    p = SKILL / "journal.md"
    if not p.exists():
        return []
    days, cur = [], None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = {"date": line[3:].strip(), "lines": []}
            days.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    return days


def parse_profile():
    p = SKILL / "profile.md"
    if not p.exists():
        return []
    groups, cur = [], None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = {"heading": line[3:].strip(), "rows": [], "notes": []}
            groups.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^- ([A-Za-z][A-Za-z ]*?):\s*(.*)$", line)
        if m:
            cur["rows"].append((m.group(1).strip(), m.group(2).strip()))
        else:
            cur["notes"].append(line)
    return groups


def render_md(lines):
    """The markdown subset recipes are written in: lists, tables, paragraphs."""
    out, buf, kind = [], [], None

    def flush():
        nonlocal buf, kind
        if not buf:
            kind = None
            return
        if kind == "ul":
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
        elif kind == "ol":
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ol>")
        elif kind == "table":
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in buf]
            rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
            if rows:
                th = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
                tr = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r)
                             + "</tr>" for r in rows[1:])
                out.append(f'<div class="scroll" tabindex="0"><table><thead><tr>{th}'
                           f"</tr></thead><tbody>{tr}</tbody></table></div>")
        else:
            out.append(f"<p>{inline(' '.join(buf))}</p>")
        buf, kind = [], None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.lstrip().startswith("|"):
            if kind != "table":
                flush()
            kind = "table"
            buf.append(line)
            continue
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            if kind != "ul":
                flush()
            kind = "ul"
            buf.append(m.group(1))
            continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if m:
            if kind != "ol":
                flush()
            kind = "ol"
            buf.append(m.group(1))
            continue
        if kind in ("ul", "ol", "table"):
            flush()
        kind = "p"
        buf.append(line.strip())
    flush()
    return "".join(out)


def badge(status):
    cls = STATUS_CLASS.get(status, "s-stub")
    title = STATUS_HELP.get(status, "")
    t = f' title="{esc(title)}"' if title else ""
    return f'<span class="badge {cls}"{t}>{esc(status)}</span>'


def page(title, body, here="", depth=""):
    def link(key, label):
        c = ' class="here"' if key == here else ""
        return f'<a href="{depth}{key}.html"{c}>{esc(label)}</a>'
    nav = " ".join([link(k, label) for k, label in SECTIONS]
                   + [link("journal", "Journal"), link("kitchen", "Kitchen")])
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{esc(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{depth}site.css?v={CSSVER}">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="bar"><a class="brand" href="{depth}index.html">Verg&eacute;s <span>Recipes</span></a><nav>{nav}</nav></div></header>
<main id="main">{body}</main>
<footer><div class="bar">Built {date.today().isoformat()} from the recipes skill.</div></footer>
</body></html>
"""


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def counts(items):
    """A recipe counts as usable once it has a method, not once it is a favourite."""
    done = sum(1 for r in items if r["status"] in ("house", "tested", "drafted"))
    return done, len(items)


def build_index(recipes):
    cards = []
    for key, label in SECTIONS:
        items = recipes[key]
        done, total = counts(items)
        if total:
            state = f"{total} recipe{'s' if total != 1 else ''}, {done} with a method"
            names = ", ".join(r["name"] for r in items[:6])
            if total > 6:
                names += f", and {total - 6} more"
            inner = f'<p class="count">{esc(state)}</p><p class="peek">{esc(names)}</p>'
        else:
            inner = '<p class="count">Nothing recorded yet</p>'
        cards.append(f'<a class="card" href="{key}.html"><h2>{esc(label)}</h2>{inner}</a>')

    total = sum(len(recipes[k]) for k, _ in SECTIONS)
    done = sum(counts(recipes[k])[0] for k, _ in SECTIONS)
    lede = (f"{total} recipe{'s' if total != 1 else ''} across four sections, "
            f"{done} with a method written up.")
    return page("Vergés Recipes", f"""
<section class="lede"><h1>Recipes</h1><p>{esc(lede)}</p></section>
<section class="cards">{''.join(cards)}</section>
""", here="index")


def build_section(key, label, items):
    if not items:
        body = (f"<section class=\"lede\"><h1>{esc(label)}</h1>"
                "<p>No recipes recorded yet.</p></section>")
        return page(f"{label} | Vergés Recipes", body, here=key)

    rows = []
    for r in items:
        bits = []
        for k in ("category", "yield", "makes", "serves", "total time"):
            if r["meta"].get(k):
                bits.append(r["meta"][k])
        sub = f'<p class="peek">{esc(" · ".join(bits))}</p>' if bits else ""
        ing = next((b for b in r["blocks"] if b["heading"].lower() == "ingredients"), None)
        n = len([l for l in (ing["lines"] if ing else []) if l.strip().startswith("-")])
        tail = f'<p class="count">{n} ingredient{"s" if n != 1 else ""}</p>' if n else ""
        rows.append(f'<a class="card" href="{r["url"]}">'
                    f'<h2>{esc(r["name"])} {badge(r["status"])}</h2>{sub}{tail}</a>')

    done, total = counts(items)
    lede = f"{total} recipe{'s' if total != 1 else ''}, {done} with a method."
    body = (f'<section class="lede"><h1>{esc(label)}</h1><p>{esc(lede)}</p></section>'
            f'<section class="cards">{"".join(rows)}</section>')
    return page(f"{label} | Vergés Recipes", body, here=key)


def build_recipe(r):
    label = dict(SECTIONS)[r["section"]]
    rows = []
    seen = set()
    for k in META_ORDER + [k for k in r["order"] if k not in META_ORDER]:
        if k in seen or k in ("section", "status", "image") or not r["meta"].get(k):
            continue
        seen.add(k)
        rows.append(f"<dt>{esc(k.title())}</dt><dd>{inline(r['meta'][k])}</dd>")
    facts = f"<dl>{''.join(rows)}</dl>" if rows else ""

    img = ""
    if r["meta"].get("image"):
        img = (f'<p class="shot"><img src="../{esc(r["meta"]["image"])}" '
               f'alt="{esc(r["name"])}" loading="lazy"></p>')

    blocks = sorted(r["blocks"], key=lambda b: (
        BODY_ORDER.index(b["heading"].lower())
        if b["heading"].lower() in BODY_ORDER else 50))
    parts = []
    for b in blocks:
        inner = render_md(b["lines"])
        if not inner:
            inner = '<p class="empty">Not recorded yet.</p>'
        parts.append(f'<section class="block"><h2>{esc(b["heading"])}</h2>{inner}</section>')

    note = ""
    if r["status"] == "stub":
        note = ('<p class="warn">No method recorded yet. The ingredients and weights '
                'are here, the steps are not, so this is a formula rather than '
                'something to cook from.</p>')

    body = (f'<p class="crumb"><a href="../{r["section"]}.html">{esc(label)}</a></p>'
            f'<section class="lede"><h1>{esc(r["name"])} {badge(r["status"])}</h1>'
            f'{note}{img}{facts}</section>{"".join(parts)}')
    return page(f"{r['name']} | Vergés Recipes", body, here=r["section"], depth="../")


def build_journal(days):
    if not days:
        body = ('<section class="lede"><h1>Journal</h1>'
                '<p>Nothing logged yet.</p></section>')
    else:
        items = "".join(f'<section class="block"><h2>{esc(d["date"])}</h2>'
                        f'{render_md(d["lines"])}</section>' for d in days)
        body = (f'<section class="lede"><h1>Journal</h1>'
                f'<p>{len(days)} day{"s" if len(days) != 1 else ""} logged, newest first.</p>'
                f'</section>{items}')
    return page("Journal | Vergés Recipes", body, here="journal")


def build_kitchen(groups):
    parts = []
    for g in groups:
        rows = "".join(
            f"<dt>{esc(k)}</dt><dd" + (' class="empty"' if v.lower() == "unknown" else "")
            + f">{inline(v)}</dd>" for k, v in g["rows"])
        notes = render_md(g.get("notes") or [])
        if rows or notes:
            parts.append(f'<section class="block"><h2>{esc(g["heading"])}</h2>'
                         f"{notes}{f'<dl>{rows}</dl>' if rows else ''}</section>")
    unknown = sum(1 for g in groups for _, v in g["rows"] if v.lower() == "unknown")
    lede = ("<p>Oven, equipment and defaults the recipes assume. "
            f"{unknown} value{'s' if unknown != 1 else ''} still unrecorded.</p>"
            if unknown else "<p>Oven, equipment and defaults the recipes assume.</p>")
    body = f'<section class="lede"><h1>Kitchen</h1>{lede}</section>{"".join(parts)}'
    return page("Kitchen | Vergés Recipes", body, here="kitchen")


def export_notes():
    """Carry the source markdown into the repo so it holds its own history."""
    if NOTES.exists():
        shutil.rmtree(NOTES)
    for name in ("profile.md", "journal.md"):
        src = SKILL / name
        if src.exists():
            NOTES.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, NOTES / name)
    for key, _ in SECTIONS:
        d = SKILL / "recipes" / key
        if not d.is_dir():
            continue
        dst = NOTES / "recipes" / key
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(d.glob("*.md")):
            shutil.copy2(f, dst / f.name)


def privacy_check(pages):
    """Pages are world readable to anyone with the URL. Keep the box out of them.

    Runs before anything is written, so a page that would leak never lands on
    disk and cannot be picked up by a later build that happens to pass.
    """
    user = os.environ.get("USER") or Path.home().name
    bad = sorted(rel for rel, text in pages.items() if user and user in text)
    if bad:
        sys.exit(f"username {user!r} would reach published files: {', '.join(bad)}")


def main():
    global CSSVER
    if not SKILL.is_dir():
        sys.exit(f"missing {SKILL}. The recipes skill has to exist first.")

    css_src = ROOT / "assets" / "site.css"
    if css_src.exists():
        shutil.copy2(css_src, ROOT / "site.css")
        CSSVER = str(int(css_src.stat().st_mtime))

    recipes = parse_recipes()
    pages = {"index.html": build_index(recipes)}
    for key, label in SECTIONS:
        pages[f"{key}.html"] = build_section(key, label, recipes[key])
        for r in recipes[key]:
            pages[r["url"]] = build_recipe(r)
    pages["journal.html"] = build_journal(parse_journal())
    pages["kitchen.html"] = build_kitchen(parse_profile())

    privacy_check(pages)

    if (ROOT / "recipes").is_dir():
        shutil.rmtree(ROOT / "recipes")
    for rel, text in pages.items():
        write(rel, text)
    export_notes()

    total = sum(len(recipes[k]) for k, _ in SECTIONS)
    print(f"{len(pages)} pages, {total} recipes "
          + ", ".join(f"{k} {len(recipes[k])}" for k, _ in SECTIONS))


if __name__ == "__main__":
    main()
