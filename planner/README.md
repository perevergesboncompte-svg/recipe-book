# Planner

Regenerates `~/.claude/skills/recipes/plan.md`, the week-by-week cooking calendar the
site renders as the Plan page. The calendar is a decision, not a derivation, so it is
generated once and then committed. Edit `plan.md` by hand to move a week.

Run from this directory:

    python3 season_inputs.py     # reads every pasta dish, writes season_inputs.json
    python3 solve_plan.py        # assigns dishes to weeks, writes plan_rows.json
    python3 write_plan.py        # writes plan.md into the skill

## What decides the order

`drivers.py` records the ingredient that gates each dish, read off its ingredient list.
`solve_plan.py` turns that into a month window, using verified Orange County
availability. Most produce is year-round here through the Salinas and Imperial Valley
relay, through storage, or on imports, so only about fifteen dishes are genuinely gated.

`character.py` is the soft constraint: when a dish wants to be eaten, regardless of
whether its produce is sold. Savoy cabbage is in the shops in August, but pizzoccheri
belongs in the cold half of the year.

Availability is a hard gate and character a soft one. The most constrained dishes claim a
week first, then each month's dishes are permuted to put shared batches and repeated
shapes side by side.

`KEEPS_WEEKS` in `solve_plan.py` bounds a batch chain at four weeks, which is how long a
sauce survives frozen. A chain wider than that is relabelled so both weeks say `make`,
because claiming a reuse across three months would be false.

## Changing it

Moving a dish between seasons means editing `CHARACTER`. Changing what gates a dish means
editing `DRIVERS`. A new month window goes in `WINDOWS`, and `YEAR_ROUND` is the list of
ingredients whose seasonality does not constrain a cook here. Re-run the three scripts.
