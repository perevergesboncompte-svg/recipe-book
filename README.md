# Recipe Book

A static site for a home recipe collection in four sections: baking, pasta,
croquetas, empanadas.

## How it works

The site is generated, not authored. Content lives as markdown in a Claude Code
skill at `~/.claude/skills/recipes/`, and `build.py` reads those files and writes
the pages to the repository root, which is what GitHub Pages serves. Editing the
generated HTML accomplishes nothing, because the next build overwrites it.
`assets/site.css` is the stylesheet source and gets copied to `site.css` on build.

    profile.md                      oven, equipment, flours, defaults
    journal.md                      dated log of what was made and how it went
    recipes/<section>/<slug>.md     one file per recipe

Rebuild after any change:

    python3 build.py

No dependencies beyond the Python standard library.

To build, commit and push in one step:

    ./publish.sh "what changed"

The build also copies the source markdown into `notes/`, so this repo carries the
collection's own history rather than only the rendered pages. `git log -p
notes/recipes/baking/sourdough.md` shows how a formula changed over time.

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
