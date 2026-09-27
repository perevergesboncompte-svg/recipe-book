# Recipe Book

A static site for a home recipe collection in four sections: baking, pasta,
croquetas, empanadas.

## How it works

The site is generated, not authored. Content lives as markdown in a Claude Code
skill at `~/.claude/skills/recipes/`, and `build.py` reads those files and writes
the pages to the repository root, which is what GitHub Pages serves. Editing the
generated HTML accomplishes nothing, because the next build overwrites it.
`assets/site.css` is the stylesheet source and gets copied to `site.css` on build.

    profile.md    oven, equipment, flours, defaults
    journal.md    dated log of what was made and how it went
    recipes/      one file per recipe, arranged as below

Rebuild after any change:

    python3 build.py

No dependencies beyond the Python standard library.

To build, commit and push in one step:

    ./publish.sh "what changed"

The build also copies the source markdown into `notes/`, so this repo carries the
collection's own history rather than only the rendered pages. `git log -p
notes/recipes/baking/sourdough.md` shows how a formula changed over time.

## Layout

A section holds ordered groups, and a group holds either recipes directly or part
folders. Order comes from a numeric prefix on the directory name, so reordering a
section is a rename and there is no index to keep in sync. The prefix is stripped
for display, and nesting stops at two levels.

    baking/01-chocolate-chip-cookies/*.md
    baking/05-tarts/01-doughs/*.md
    baking/05-tarts/03-dishes/*.md
    pasta/01-doughs/  02-fillings/  03-shapes/  04-dishes/
    croquetas/*.md
    empanadas/01-doughs/  02-fillings/  03-dishes/

Croquetas are whole recipes, so their files sit at the section root. Baking splits
into parts only inside tarts, because a tart is a dough plus a filling while a
cookie is not.

## Parts and dishes

A part is written once and reused, so one empanada dough serves every filling. A
dish names its parts by file stem:

    - Dough: criolla-dough
    - Filling: beef-picadillo

`Dough`, `Filling`, `Shape`, `Base` and `Coating` are recognised, each taking one
stem or a comma-separated list. The site renders them as links, adds a `Used in`
list to the part's own page, and prints `(not recorded yet)` when a stem matches
nothing, so an unwritten dough shows up as a gap instead of going unnoticed.
References resolve within a section only.

## Recipe format

Metadata comes first as `- Key: value` lines, before any heading. Everything
after the first `##` renders as written.

```markdown
# Sourdough Bread

- Section: baking
- Status: tested
- Yield: 2 loaves, 900 g each
- Source: mine

## Ingredients

- Bread flour: 1000 g (100%)
- Water: 750 g (75%)

## Method

1. Mix flour and water, rest 30 min.
```

`Status` is `stub`, `drafted`, `tested`, `house` or `retired`, and the site shows
it as a badge on every card so an unfinished formula is never mistaken for one
you can cook from. A `stub` carries ingredient names with no quantities.

Sections beyond `Ingredients`, `Method`, `Notes` and `Learnings` render in file
order, so a recipe can add `Dough`, `Filling` or `Cost` as needed.

## Pages

`index.html` lists the four sections with a count of how many recipes each holds
and how many are written up. Each section has its own page, and each recipe its
own. `journal.html` is the full log. `kitchen.html` holds the oven, equipment and
defaults, and marks which of them are still unrecorded.

## Privacy

Every page carries `noindex, nofollow` and `robots.txt` disallows all crawlers,
but GitHub Pages on a free account serves publicly, so anyone with the URL can
read the site. That is obscurity, not access control. Keep names, addresses and
anything else personal out of recipe text and journal entries.

`build.py` reads the local username and exits non-zero if it finds it in any file
it just wrote, so a stray absolute path cannot reach the published pages.
