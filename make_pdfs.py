#!/usr/bin/env python3
"""Render every recipe in the skill to an A4 PDF card in the compact sheet style."""

import re
import sys
from pathlib import Path

from fpdf import FPDF
from fpdf.image_parsing import preload_image

SKILL = Path.home() / ".claude/skills/recipes"
SHAPES = SKILL / "images" / "shapes"
FONTDIR = Path("/usr/share/fonts/dejavu")
SITE = "perevergesboncompte-svg.github.io/recipe-book"
SKIP = {"section", "status", "image", "thumb", "category", "group",
        "appearance", "texture",
        "flavor", "technique", "overall", "formed", "used in", "unit price",
        "store", "filling note", "pasta colour", "difficulty", "source"}
GRID = ["yield", "makes", "serves", "active time", "rest", "total time", "oven",
        "unit weight", "energy cost", "price"]
ORDER = ["ingredients", "method", "notes", "preserving", "learnings"]
INK, MUTED, RULE = (17, 17, 17), (102, 102, 102), (51, 51, 51)


def parse(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)
    meta, blocks, head, buf = {}, [], None, []
    for line in lines:
        if line.startswith("## "):
            if head is not None:
                blocks.append((head, buf))
            head, buf = line[3:].strip(), []
            continue
        if head is None:
            m = re.match(r"- ([A-Za-z][A-Za-z /'-]*):\s*(.+)$", line)
            if m:
                meta[m.group(1).strip().lower()] = m.group(2).strip()
            continue
        buf.append(line)
    if head is not None:
        blocks.append((head, buf))
    return title, meta, blocks


def items(buf):
    """One entry per bullet or paragraph, with wrapped source lines rejoined."""
    out, joinable = [], False
    for line in buf:
        s = line.strip()
        if not s:
            joinable = False
            continue
        m = re.match(r"^(?:[-*]|\d+\.)\s+(.*)$", s)
        if m:
            out.append(m.group(1).strip())
        elif joinable:
            out[-1] = f"{out[-1]} {s}"
        else:
            out.append(s)
        joinable = True
    return out


def split_qty(line):
    if ": " in line:
        name, qty = line.rsplit(": ", 1)
        if len(qty) <= 44:
            return name.strip(), qty.strip()
    m = re.match(r"^([\d/.,]+\s*(?:g|kg|ml|l|oz|lb|tbsp|tsp|cups?)\b\.?)\s+(.*)$", line, re.I)
    return (m.group(2).strip(), m.group(1).strip()) if m else (line, "")


def shape_art(stem):
    if not SHAPES.is_dir():
        return []
    pat = re.compile(rf"^{re.escape(stem)}-(\d+)\.(jpg|jpeg|png)$", re.I)
    hits = []
    for f in SHAPES.iterdir():
        m = pat.match(f.name)
        if m:
            hits.append((int(m.group(1)), f))
    return [f for _, f in sorted(hits)]


class Card(FPDF):
    def __init__(self, crumb=""):
        super().__init__("P", "mm", "A4")
        self.crumb = crumb
        self.set_margins(14, 14, 14)
        self.set_auto_page_break(True, 16)
        for style, name in (("", "DejaVuSans.ttf"), ("B", "DejaVuSans-Bold.ttf"),
                            ("I", "DejaVuSans-Oblique.ttf")):
            self.add_font("dv", style, str(FONTDIR / name))

    @property
    def avail(self):
        return self.w - self.l_margin - self.r_margin

    def header(self):
        self.set_y(9)
        self.set_font("dv", "", 6.5)
        self.set_text_color(*MUTED)
        half = self.avail / 2
        self.cell(half, 3.4, "VERGÉS RECIPES")
        self.cell(half, 3.4, self.crumb.upper(), align="R",
                  new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(221, 221, 221)
        self.set_line_width(0.2)
        y = self.get_y() + 0.9
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.set_y(y + 3.5)

    def footer(self):
        self.set_y(-11)
        self.set_font("dv", "", 6.5)
        self.set_text_color(*MUTED)
        half = self.avail / 2
        self.cell(half, 3.4, SITE)
        self.cell(half, 3.4, str(self.page_no()), align="R")

    def art(self, files, cols=4, gap=3):
        w = (self.avail - gap * (cols - 1)) / cols
        for i in range(0, len(files), cols):
            row = files[i:i + cols]
            heights = []
            for f in row:
                info = preload_image(self.image_cache, str(f))[2]
                heights.append(w * info["h"] / info["w"])
            band = max(heights)
            if self.get_y() + band + 4 > self.h - self.b_margin:
                self.add_page()
            top = self.get_y()
            for n, (f, ih) in enumerate(zip(row, heights)):
                x = self.l_margin + n * (w + gap)
                self.image(str(f), x=x, y=top + (band - ih) / 2, w=w)
                self.set_xy(x, top + band + 0.4)
                self.set_font("dv", "", 6)
                self.set_text_color(*MUTED)
                self.cell(w, 3, str(i + n + 1), align="C")
            self.set_y(top + band + 4.5)

    def rule_heading(self, text):
        if self.get_y() > self.h - 42:
            self.add_page()
        self.ln(2.5)
        self.set_font("dv", "B", 10)
        self.set_text_color(*INK)
        self.cell(0, 5.5, text.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*RULE)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(1.8)

    def masthead(self, title, source):
        self.set_font("dv", "B", 15)
        self.set_text_color(*INK)
        self.multi_cell(0, 7, title.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
        if source:
            self.set_font("dv", "", 8)
            self.set_text_color(*MUTED)
            self.multi_cell(0, 4.2, source, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def facts(self, pairs):
        for i in range(0, len(pairs), 4):
            row = pairs[i:i + 4]
            w = self.avail / len(row)
            top = self.get_y()
            if top > self.h - 38:
                self.add_page()
                top = self.get_y()
            h = 10.5
            self.set_fill_color(245, 245, 245)
            self.set_draw_color(221, 221, 221)
            self.set_line_width(0.2)
            for n, (label, value) in enumerate(row):
                x = self.l_margin + n * w
                self.rect(x, top, w, h, style="DF")
                self.set_xy(x + 1, top + 1.2)
                self.set_font("dv", "", 6.2)
                self.set_text_color(*MUTED)
                self.cell(w - 2, 2.8, label.upper(), align="C")
                self.set_xy(x + 1, top + 4.4)
                self.set_font("dv", "B", 8)
                self.set_text_color(*INK)
                self.multi_cell(w - 2, 3.1, value, align="C", max_line_height=3.1)
            self.set_y(top + h + 1.5)

    def ingredients(self, rows):
        qw = self.avail * 0.3
        self.set_draw_color(187, 187, 187)
        self.set_line_width(0.2)
        for line in rows:
            name, qty = split_qty(line)
            if self.get_y() > self.h - 24:
                self.add_page()
            y = self.get_y()
            self.set_font("dv", "B", 8.5)
            self.set_text_color(*INK)
            self.set_xy(self.l_margin, y)
            self.multi_cell(qw - 2.5, 4.2, qty, align="R", max_line_height=4.2)
            qh = self.get_y() - y
            self.set_font("dv", "", 8.5)
            self.set_xy(self.l_margin + qw, y)
            self.multi_cell(self.avail - qw, 4.2, name, max_line_height=4.2)
            nh = self.get_y() - y
            h = max(qh, nh, 4.2)
            self.line(self.l_margin + qw - 1.2, y, self.l_margin + qw - 1.2, y + h)
            self.set_y(y + h)

    def steps(self, rows, numbered):
        self.set_font("dv", "", 8.5)
        self.set_text_color(*INK)
        for n, line in enumerate(rows, 1):
            if self.get_y() > self.h - 22:
                self.add_page()
            bullet = f"{n}." if numbered else "•"
            y = self.get_y()
            self.set_xy(self.l_margin, y)
            self.cell(6, 4.4, bullet)
            self.set_xy(self.l_margin + 6, y)
            self.multi_cell(self.avail - 6, 4.4, line, max_line_height=4.4)
            self.ln(0.6)

    def tinted(self, rows):
        self.set_fill_color(255, 253, 231)
        self.set_draw_color(255, 193, 7)
        inner = self.avail - 6
        self.set_font("dv", "", 8)
        total = 2.6
        for line in rows:
            total += 4 * max(1, len(self.multi_cell(inner, 4, line, dry_run=True,
                                                    output="LINES")))
        if self.get_y() + total > self.h - self.b_margin:
            self.add_page()
        top = self.get_y()
        self.rect(self.l_margin, top, self.avail, total, style="F")
        self.set_line_width(0.8)
        self.line(self.l_margin, top, self.l_margin, top + total)
        self.set_xy(self.l_margin + 3, top + 1.3)
        self.set_text_color(*INK)
        for line in rows:
            self.set_x(self.l_margin + 3)
            self.multi_cell(inner, 4, line, max_line_height=4)
        self.set_y(top + total + 1.5)

    def signoff(self):
        if self.get_y() > self.h - 26:
            self.add_page()
        self.ln(3)
        self.set_draw_color(*RULE)
        self.set_line_width(0.5)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(2.5)
        self.set_font("dv", "", 7)
        self.set_text_color(*MUTED)
        third = self.avail / 3
        for label in ("DATE  ____ / ____ / ____", "RATING  ____ / 5", "OVEN ADJ  __________"):
            self.cell(third, 4, label)
        self.ln(6)
        self.set_text_color(*MUTED)
        self.cell(0, 4, "NOTES  " + "_" * 92, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.cell(0, 4, "_" * 104, new_x="LMARGIN", new_y="NEXT")


def render(path, out, crumb=""):
    title, meta, blocks = parse(path)
    art = shape_art(path.stem)
    pdf = Card(crumb)
    pdf.add_page()
    pdf.masthead(title, meta.get("source", ""))
    shot = SKILL / meta["image"] if meta.get("image") else None
    if shot and shot.exists():
        side = 58
        pdf.image(str(shot), x=(pdf.w - side) / 2, w=side)
        pdf.ln(2)
    pdf.facts([(k, meta[k]) for k in GRID if meta.get(k)])
    extra = [(k, v) for k, v in meta.items() if k not in SKIP and k not in GRID]
    if extra:
        pdf.rule_heading("Details")
        pdf.steps([f"{k.title()}: {v}" for k, v in extra], False)
    seen = set()
    for want in ORDER:
        for head, buf in blocks:
            if head.lower() != want:
                continue
            seen.add(head)
            rows = items(buf)
            if not rows:
                continue
            pdf.rule_heading(head)
            if want == "ingredients":
                pdf.ingredients(rows)
            elif want == "method":
                pdf.steps(rows, True)
                if art:
                    pdf.rule_heading("Shaping")
                    pdf.art(art)
                    art = []
            elif want in ("notes", "preserving"):
                pdf.tinted(rows)
            else:
                pdf.steps(rows, False)
    for head, buf in blocks:
        if head in seen:
            continue
        rows = items(buf)
        if rows:
            pdf.rule_heading(head)
            pdf.steps(rows, False)
    if art:
        pdf.rule_heading("Shaping")
        pdf.art(art)
    pdf.signoff()
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out))


def main():
    root = SKILL / "recipes"
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pdf")
    made = failed = 0
    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root)
        if rel.parts[0] == "ingredients":
            continue
        parts = [re.sub(r"^\d+[-_]", "", p) for p in rel.parts[:-1]]
        slug = "-".join(parts + [md.stem])
        crumb = " / ".join(p.replace("-", " ") for p in parts)
        try:
            render(md, outdir / f"{slug}.pdf", crumb)
            made += 1
        except Exception as exc:
            failed += 1
            print(f"FAILED {rel}: {exc}", file=sys.stderr)
    print(f"{made} PDFs written to {outdir}" + (f", {failed} failed" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
