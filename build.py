#!/usr/bin/env python3
"""Render the recipes skill's markdown into a static site.

Source of truth is the skill's own files, so the site never diverges from the
collection the assistant maintains:

    ~/.claude/skills/recipes/profile.md
    ~/.claude/skills/recipes/journal.md
    ~/.claude/skills/recipes/recipes/<section>/...

A section holds ordered groups, and a group holds either recipes directly or
part folders (doughs, fillings, shapes, dishes). Order comes from a numeric
prefix on the directory name, so reordering is a rename and there is no separate
index to keep in sync. Layout the walker accepts:

    <section>/*.md                        flat, no groups
    <section>/<NN-group>/*.md             one group of plain recipes
    <section>/<NN-group>/<NN-part>/*.md   a group split into parts

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

PART_TYPES = {"doughs": "Dough", "fillings": "Filling", "shapes": "Shape",
              "dishes": "Dish", "bases": "Base", "coatings": "Coating"}

STATUS_ORDER = ["house", "tested", "drafted", "stub", "retired"]

META_ORDER = ["yield", "makes", "serves", "unit weight", "active time",
              "rest", "total time", "oven", "price", "tags", "source"]
LINK_KEYS = ["dough", "filling", "shape", "base", "coating"]
SCORE_KEYS = ["appearance", "texture", "flavor", "technique", "overall"]
BODY_ORDER = ["ingredients", "method", "notes", "preserving", "learnings"]
HIDE_META = {"section", "status", "image", "thumb", "category", "group"}

CSSVER = ""


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "item"


def esc(s):
    return html.escape(s or "")


def inline(s):
    out = esc(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


UNITS = r"(?:g|kg|ml|l|oz|lb|tbsp|tsp|cups?)"
QTY = re.compile(
    r"(?<![\d./])(?:"
    r"(?P<lo>\d+(?:\.\d+)?)\s*(?:-|to)\s*(?P<hi>\d+(?:\.\d+)?)\s*(?P<u1>" + UNITS + r")\b"
    r"|(?P<fn>\d+)/(?P<fd>\d+)\s*(?P<u2>" + UNITS + r")\b"
    r"|(?P<n>\d+(?:\.\d+)?)\s*(?P<u3>" + UNITS + r")\b"
    r")", re.I)
COUNT = re.compile(r"(?<![\d./%])(?P<c>\d+(?:\.\d+)?)(?![\d.])(?!\s*%)"
                   r"(?!\s*" + UNITS + r"\b)")


def qspan(value, suffix):
    return f'<span class="q" data-q="{value:g}">{value:g}</span>{suffix}'


def shape_art(stem):
    """Ordered shaping drawings for a shape, matched on a digit-anchored name so
    `agnolotti` never picks up `agnolotti-dal-plin`."""
    d = SKILL / "images" / "shapes"
    if not d.is_dir():
        return []
    pat = re.compile(rf"^{re.escape(stem)}-(\d+)\.(jpg|jpeg|png)$", re.I)
    hits = []
    for f in d.iterdir():
        m = pat.match(f.name)
        if m:
            hits.append((int(m.group(1)), f.name))
    return [n for _, n in sorted(hits)]


def mark_qty(text):
    """Wrap scalable quantities so the page can multiply them client-side.

    Only numbers carrying a known unit, or bare counts, get touched. A percent
    and a flour grade like `00` must never move, so everything before the first
    colon is left alone and `%` is excluded outright.
    """
    body = inline(text)
    head = ""
    if ": " in body:
        head, _, body = body.partition(": ")
        head += ": "

    def unit_sub(m):
        u = m.group("u1") or m.group("u2") or m.group("u3")
        if m.group("lo"):
            return (qspan(float(m.group("lo")), "") + "-"
                    + qspan(float(m.group("hi")), f" {u}"))
        if m.group("fn"):
            return qspan(int(m.group("fn")) / int(m.group("fd")), f" {u}")
        return qspan(float(m.group("n")), f" {u}")

    out, n = QTY.subn(unit_sub, body)
    if not n:
        out = COUNT.sub(lambda m: qspan(float(m.group("c")), ""), body)
    return head + out


SCALER = """<div class="scaler" data-scaler>
<span class="slab">Batch</span>
<button type="button" data-f="0.5">&frac12;&times;</button>
<button type="button" data-f="1" class="on">1&times;</button>
<button type="button" data-f="2">2&times;</button>
<button type="button" data-f="3">3&times;</button>
<label>or <input type="number" min="0.1" max="100" step="0.1" value="1"></label>
</div>
<script>
(function(){
  function init(){
    var box=document.querySelector('[data-scaler]'); if(!box) return;
    var qs=[].slice.call(document.querySelectorAll('.q'));
    qs.forEach(function(e){ e.dataset.base=e.dataset.q; });
    function fmt(v){ var d=v>=100?0:(v>=10?1:2);
      return parseFloat(v.toFixed(d)).toString(); }
    function apply(f){
      if(!(f>0)) return;
      qs.forEach(function(e){ e.textContent=fmt(parseFloat(e.dataset.base)*f); });
      var bs=box.querySelectorAll('button');
      for(var i=0;i<bs.length;i++){
        bs[i].classList.toggle('on', parseFloat(bs[i].dataset.f)===f); }
    }
    var bs=box.querySelectorAll('button');
    for(var i=0;i<bs.length;i++){
      bs[i].addEventListener('click', function(){
        var f=parseFloat(this.dataset.f);
        box.querySelector('input').value=f; apply(f); }); }
    box.querySelector('input').addEventListener('input', function(){
      apply(parseFloat(this.value)); });
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else { init(); }
})();
</script>"""


def mark_lead(text):
    """Scale only the leading number of a yield, so `2 loaves, 900 g each` is safe."""
    s = inline(text)
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)", s)
    if m:
        return (qspan(float(m.group(1)), "") + "-"
                + qspan(float(m.group(2)), "") + s[m.end():])
    m = re.match(r"^(\d+(?:\.\d+)?)", s)
    if m:
        return qspan(float(m.group(1)), "") + s[m.end():]
    return s


def strip_order(name):
    return re.sub(r"^\d+[-_]", "", name)


def order_key(path):
    m = re.match(r"^(\d+)[-_]", path.name)
    return (int(m.group(1)), "") if m else (10 ** 6, path.name.lower())


def nice(name):
    s = strip_order(name).replace("-", " ").replace("_", " ").strip()
    return s[:1].upper() + s[1:] if s else s


def subdirs(p):
    return [d for d in p.iterdir() if d.is_dir() and not d.name.startswith(".")]


def parse_recipe(path, section, group, part):
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
    bits = [section] + [strip_order(x) for x in (group, part) if x] + [path.stem]
    return {
        "name": name,
        "slug": path.stem,
        "section": section,
        "group": nice(group) if group else None,
        "part": PART_TYPES.get(strip_order(part)) if part else None,
        "status": (meta.get("status") or "").lower() or "stub",
        "meta": meta,
        "order": order,
        "blocks": blocks,
        "url": "recipes/" + "-".join(bits) + ".html",
        "stem": path.stem,
        "used_in": [],
    }


def score(r):
    try:
        return float(r["meta"].get("overall", ""))
    except ValueError:
        return -1.0


def sort_recipes(items):
    """Status first, then the best-rated inside a status, then by name."""
    return sorted(items, key=lambda r: (
        STATUS_ORDER.index(r["status"]) if r["status"] in STATUS_ORDER else 99,
        -score(r), r["name"].lower()))


def walk_section(key):
    """Groups in prefix order, each carrying one or more labelled buckets."""
    root = SKILL / "recipes" / key
    groups = []
    if not root.is_dir():
        return groups

    loose = sort_recipes([parse_recipe(f, key, None, None)
                          for f in sorted(root.glob("*.md"))])
    if loose:
        groups.append({"label": None, "buckets": [{"label": None, "items": loose}]})

    for d in sorted(subdirs(root), key=order_key):
        parts = sorted(subdirs(d), key=order_key)
        if parts:
            stranded = sorted(f.name for f in d.glob("*.md"))
            if stranded:
                sys.exit(f"{key}/{d.name} has part folders, so its loose files "
                         f"would never render: {', '.join(stranded)}")
            buckets = [{"label": nice(p.name),
                        "items": sort_recipes([parse_recipe(f, key, d.name, p.name)
                                               for f in sorted(p.glob("*.md"))])}
                       for p in parts]
        else:
            buckets = [{"label": None,
                        "items": sort_recipes([parse_recipe(f, key, d.name, None)
                                               for f in sorted(d.glob("*.md"))])}]
        groups.append({"label": nice(d.name), "buckets": buckets})
    return groups


def flatten(groups):
    return [r for g in groups for b in g["buckets"] for r in b["items"]]


def link_parts(recipes):
    """Resolve `- Dough: <slug>` style keys to the part entry they name."""
    by_section = {}
    for r in recipes:
        by_section.setdefault(r["section"], {})[r["slug"]] = r
    for r in recipes:
        r["links"] = []
        for k in LINK_KEYS:
            raw = r["meta"].get(k)
            if not raw:
                continue
            for ref in [x.strip() for x in raw.split(",") if x.strip()]:
                target = by_section.get(r["section"], {}).get(ref)
                r["links"].append((k.title(), ref, target))
                if target is not None:
                    target["used_in"].append(r)


def render_md(lines, mark=None):
    """The markdown subset recipes are written in: lists, tables, paragraphs.

    `mark` rewrites list-item text, which is how ingredient quantities pick up
    the spans the scale control multiplies.
    """
    out, buf, kind = [], [], None
    item = mark or inline

    def flush():
        nonlocal buf, kind
        if not buf:
            kind = None
            return
        if kind == "ul":
            out.append("<ul>" + "".join(f"<li>{item(x)}</li>" for x in buf) + "</ul>")
        elif kind == "ol":
            out.append("<ol>" + "".join(f"<li>{item(x)}</li>" for x in buf) + "</ol>")
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


def page(title, body, here="", depth=""):
    def link(key, label):
        c = ' class="here"' if key == here else ""
        return f'<a href="{depth}{key}.html"{c}>{esc(label)}</a>'
    nav = " ".join(link(k, label) for k, label in SECTIONS)
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


def card(r, depth=""):
    bits = [r["meta"][k] for k in ("yield", "makes", "serves", "total time")
            if r["meta"].get(k)]
    sub = f'<p class="peek">{esc(" · ".join(bits))}</p>' if bits else ""
    ing = next((b for b in r["blocks"] if b["heading"].lower() == "ingredients"), None)
    n = len([l for l in (ing["lines"] if ing else []) if l.strip().startswith("-")])
    bits2 = []
    if r["meta"].get("overall"):
        bits2.append(f'<strong>{esc(r["meta"]["overall"])}/5</strong> overall')
    if n:
        bits2.append(f'{n} ingredient{"s" if n != 1 else ""}')
    tail = f'<p class="count">{" · ".join(bits2)}</p>' if bits2 else ""
    thumb = ""
    src = r["meta"].get("thumb") or r["meta"].get("image")
    if src:
        cls = "thumb line" if r["meta"].get("thumb") else "thumb"
        thumb = (f'<span class="{cls}"><img src="{depth}{esc(src)}"'
                 f' alt="" loading="lazy"></span>')
    cls = "card has-thumb" if thumb else "card"
    return (f'<a class="{cls}" href="{depth}{r["url"]}">{thumb}'
            f'<h3>{esc(r["name"])}</h3>{sub}{tail}</a>')


def build_section(key, label, groups):
    items = flatten(groups)
    if not items:
        body = (f'<section class="lede"><h1>{esc(label)}</h1>'
                "<p>No recipes recorded yet.</p></section>")
        return page(f"{label} | Vergés Recipes", body, here=key)

    parts = []
    for g in groups:
        if g["label"]:
            gdone, gtotal = counts(flatten([g]))
            parts.append(f'<h2 class="group">{esc(g["label"])}'
                         f'<span class="gcount">{gtotal} recipe'
                         f'{"s" if gtotal != 1 else ""}, {gdone} with a method</span></h2>')
        for b in g["buckets"]:
            if b["label"]:
                parts.append(f'<h3 class="bucket">{esc(b["label"])}</h3>')
            if b["items"]:
                parts.append('<div class="cards">'
                             + "".join(card(r) for r in b["items"]) + "</div>")
            else:
                parts.append('<p class="empty">Nothing here yet.</p>')

    done, total = counts(items)
    ngroups = len([g for g in groups if g["label"]])
    lede = f"{total} recipe{'s' if total != 1 else ''}, {done} with a method"
    if ngroups:
        lede += f", in {ngroups} group{'s' if ngroups != 1 else ''}"
    body = (f'<section class="lede"><h1>{esc(label)}</h1><p>{esc(lede + ".")}</p></section>'
            + "".join(parts))
    return page(f"{label} | Vergés Recipes", body, here=key)


def build_index(sections):
    cards = []
    for key, label in SECTIONS:
        groups = sections[key]
        items = flatten(groups)
        done, total = counts(items)
        if total:
            names = [g["label"] for g in groups if g["label"]]
            if not names:
                names = [r["name"] for r in items[:6]]
            peek = ", ".join(names[:7])
            if len(names) > 7:
                peek += f", and {len(names) - 7} more"
            inner = (f'<p class="count">{total} recipe{"s" if total != 1 else ""}, '
                     f'{done} with a method</p><p class="peek">{esc(peek)}</p>')
        else:
            inner = '<p class="count">Nothing recorded yet</p>'
        cards.append(f'<a class="card" href="{key}.html"><h2>{esc(label)}</h2>'
                     f"{inner}</a>")

    allitems = [r for key, _ in SECTIONS for r in flatten(sections[key])]
    done, total = counts(allitems)
    lede = (f"{total} recipe{'s' if total != 1 else ''} across four sections, "
            f"{done} with a method written up.")
    return page("Vergés Recipes", f"""
<section class="lede"><h1>Recipes</h1><p>{esc(lede)}</p></section>
<section class="cards">{''.join(cards)}</section>
""", here="index")


def build_recipe(r):
    label = dict(SECTIONS)[r["section"]]
    crumb = [f'<a href="../{r["section"]}.html">{esc(label)}</a>']
    if r["group"]:
        crumb.append(esc(r["group"]))
    if r["part"]:
        crumb.append(esc(r["part"]))

    rows = []
    seen = set()
    for k, ref, target in r.get("links") or []:
        if target is not None:
            rows.append(f"<dt>{esc(k)}</dt>"
                        f'<dd><a href="../{target["url"]}">{esc(target["name"])}</a></dd>')
        else:
            rows.append(f"<dt>{esc(k)}</dt>"
                        f'<dd class="empty">{esc(ref)} (not recorded yet)</dd>')
        seen.add(k.lower())
    for k in META_ORDER + [k for k in r["order"] if k not in META_ORDER]:
        if (k in seen or k in HIDE_META or k in LINK_KEYS or k in SCORE_KEYS
                or not r["meta"].get(k)):
            continue
        seen.add(k)
        val = (mark_lead(r["meta"][k]) if k in ("yield", "makes", "serves")
               else inline(r["meta"][k]))
        rows.append(f"<dt>{esc(k.title())}</dt><dd>{val}</dd>")
    facts = f"<dl>{''.join(rows)}</dl>" if rows else ""

    img = ""
    if r["meta"].get("image"):
        img = (f'<p class="shot"><img src="../{esc(r["meta"]["image"])}" '
               f'alt="{esc(r["name"])}" loading="lazy"></p>')

    blocks = sorted(r["blocks"], key=lambda b: (
        BODY_ORDER.index(b["heading"].lower())
        if b["heading"].lower() in BODY_ORDER else 50))
    body_parts = []
    art = shape_art(r["stem"])
    if art:
        figs = "".join(
            f'<figure><img src="../images/shapes/{esc(n)}" alt="{esc(r["name"])}'
            f' step {i}" loading="lazy"><figcaption>{i}</figcaption></figure>'
            for i, n in enumerate(art, 1))
        if r["meta"].get("image"):
            figs += (f'<figure class="shot-fig"><img src="../{esc(r["meta"]["image"])}"'
                     f' alt="{esc(r["name"])}" loading="lazy">'
                     f"<figcaption>made</figcaption></figure>")
            img = ""
        body_parts.append('<section class="block"><h2>Shaping</h2>'
                          f'<div class="art">{figs}</div></section>')
    if any(r["meta"].get(k) for k in SCORE_KEYS):
        cells = []
        for k in SCORE_KEYS:
            v = r["meta"].get(k)
            if not v:
                continue
            num = re.fullmatch(r"[\d.]+", v)
            cls = "sc big" if k == "overall" else "sc"
            val = f"{esc(v)}<span class='den'>/5</span>" if num else esc(v)
            cells.append(f'<div class="{cls}"><span class="scv">{val}</span>'
                         f'<span class="scl">{esc(k.title())}</span></div>')
        body_parts.append('<section class="block"><h2>Scorecard</h2>'
                          f'<div class="score">{"".join(cells)}</div></section>')
    for b in blocks:
        ing = b["heading"].lower() == "ingredients"
        inner = (render_md(b["lines"], mark_qty if ing else None)
                 or '<p class="empty">Not recorded yet.</p>')
        if ing and 'class="q"' in inner:
            inner = SCALER + inner
        body_parts.append(f'<section class="block"><h2>{esc(b["heading"])}</h2>'
                          f"{inner}</section>")

    if r["used_in"]:
        links = "".join(f'<li><a href="../{u["url"]}">{esc(u["name"])}</a></li>'
                        for u in sort_recipes(r["used_in"]))
        body_parts.append('<section class="block"><h2>Used in</h2>'
                          f"<ul>{links}</ul></section>")

    note = ""
    if r["status"] == "stub":
        note = ('<p class="warn">No method recorded yet. The ingredients and weights '
                'are here, the steps are not, so this is a formula rather than '
                'something to cook from.</p>')

    body = (f'<p class="crumb">{" / ".join(crumb)}</p>'
            f'<section class="lede"><h1>{esc(r["name"])}</h1>'
            f'{note}{img}{facts}</section>{"".join(body_parts)}')
    return page(f"{r['name']} | Vergés Recipes", body, here=r["section"], depth="../")


def export_notes():
    """Carry the source markdown into the repo so it holds its own history."""
    if NOTES.exists():
        shutil.rmtree(NOTES)
    NOTES.mkdir(parents=True, exist_ok=True)
    src = SKILL / "recipes"
    if src.is_dir():
        shutil.copytree(src, NOTES / "recipes",
                        ignore=shutil.ignore_patterns(".*"))


def export_images():
    """Photos live with the recipes they belong to, so they ship from the skill."""
    dst = ROOT / "images"
    if dst.exists():
        shutil.rmtree(dst)
    src = SKILL / "images"
    if src.is_dir():
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".*"))


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

    sections = {key: walk_section(key) for key, _ in SECTIONS}
    allitems = [r for key, _ in SECTIONS for r in flatten(sections[key])]

    urls = {}
    for r in allitems:
        if r["url"] in urls:
            sys.exit(f"two recipes render to {r['url']}: "
                     f"{urls[r['url']]} and {r['section']}/{r['slug']}")
        urls[r["url"]] = f"{r['section']}/{r['slug']}"

    link_parts(allitems)

    pages = {"index.html": build_index(sections)}
    for key, label in SECTIONS:
        pages[f"{key}.html"] = build_section(key, label, sections[key])
    for r in allitems:
        pages[r["url"]] = build_recipe(r)

    privacy_check(pages)

    if (ROOT / "recipes").is_dir():
        shutil.rmtree(ROOT / "recipes")
    for rel, text in pages.items():
        write(rel, text)
    export_notes()
    export_images()

    print(f"{len(pages)} pages, {len(allitems)} recipes")
    for key, _ in SECTIONS:
        gs = sections[key]
        desc = ", ".join(
            f"{g['label'] or 'ungrouped'} "
            f"[{'/'.join(str(len(b['items'])) for b in g['buckets'])}]"
            for g in gs) or "empty"
        print(f"  {key}: {desc}")


if __name__ == "__main__":
    main()
