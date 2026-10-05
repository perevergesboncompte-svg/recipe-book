"""What gates each pasta dish: the ingredient that must be in season, or nothing.

Read off the extracted ingredient lists. A dish is season-neutral when every
ingredient is pantry, dairy, cured meat, or produce that holds all year in
Southern California (onion, carrot, celery, garlic, potato, lemon, herbs).

REUSE maps a dish to the non-pasta recipes a batch made for it can be spent on.
"""

DRIVERS = {
    "fettuccine-alfredo": [],
    "penne-alla-vodka": [],
    "trofie-al-pesto-genovese": ["basil"],
    "tajarin-al-tartufo": ["white truffle"],
    "pizzoccheri-alla-valtellinese": ["savoy cabbage"],
    "tortelli-di-zucca": ["delicata squash", "butternut squash", "sage"],
    "canederli": [],
    "passatelli-in-brodo": [],
    "bigoli-in-salsa": [],
    "cjalsons": ["granny smith apple"],
    "tagliatelle-alla-bolognese": [],
    "balanzoni-burro-e-salvia": ["sage"],
    "agnolotti-dal-plin-brisket": [],
    "corzetti-alle-erbe": [],
    "timballo-alla-teramana": ["spinach"],
    "strangozzi-alla-norcina": ["black winter truffle"],
    "bucatini-all-amatriciana": [],
    "maccheroncini-di-campofilone-al-sugo": [],
    "culurgiones-alla-nuorese": [],
    "busiate-al-pesto-trapanese": ["cherry tomatoes", "basil"],
    "orecchiette-con-cime-di-rapa": ["broccoli rabe"],
    "spaghetti-alla-puttanesca": [],
    "rigatoni-diavola": [],
    "potato-and-creme-fraiche-ravioli": [],
    "parmigiano-fonduta-tortellini-in-brodo": [],
    "ravioli-with-taleggio-fonduta-peas-and-speck": ["english peas"],
    "eggplant-mezzelune-with-ricotta-salata": ["japanese eggplant", "basil"],
    "pappardelle-with-porcini-and-veal-bolognese": ["fennel bulb"],
    "prosciutto-and-goat-cheese-cappelletti": ["spinach"],
    "caramelle-with-caramelized-onion-and-balsamic": [],
    "tagliatelle-with-ossobuco-and-soffritto": [],
    "sheeps-milk-ricotta-occhi-with-bottarga": [],
    "corzetti-with-sungold-tomatoes-and-pecorino": ["cherry tomatoes", "basil"],
    "spaghetti-with-colatura-and-bread-crumbs": [],
    "corzetti-with-chanterelles-and-aged-goat-cheese": ["chanterelle"],
    "stricchetti-with-smashed-peas-and-prosciutto": ["sugar snap peas"],
    "tagliatelle-with-matsutake-lemon-and-mint": ["matsutake"],
    "grilled-summer-beans-with-garlic-vinaigrette": ["romano beans"],
    "porcini-with-rosemary-and-garlic": ["porcini"],
    "roasted-eggplant-with-olives-and-sun-dried-tomato": ["japanese eggplant"],
    "roasted-kabocha-squash-with-hot-honey": ["kabocha squash"],
    "aubergine-ravioli": ["japanese eggplant"],
    "butternut-squash-and-marjoram-ravioli": ["butternut squash"],
    "butternut-squash-ravioli": ["butternut squash"],
    "crab-ravioli-corrigan": ["dungeness crab"],
    "crab-ravioli-with-crab-sauce": ["dungeness crab"],
    "crab-with-turnip": ["dungeness crab"],
    "duck-ravioli-with-langoustines": [],
    "goat-s-cheese-ravioli": [],
    "langoustine-ravioli": [],
    "oxtail-ravioli": ["celeriac"],
    "pink-prawn-ravioli": ["spot prawn"],
    "polenta-ravioli": ["artichoke", "white truffle"],
    "prawn-and-smoked-salmon-ravioli": [],
    "pulled-pork-raviolo": [],
    "smoked-potato-ravioli": ["black summer truffle"],
    "truffle-ravioli": ["white truffle"],
    "turkey-and-squash-ravioli": ["butternut squash"],
    "watercress-and-egg-yolk-ravioli": ["watercress", "jerusalem artichoke"],
}

REUSE = {
    "tortelli-di-zucca": ["empanadas/calabaza-cabra"],
    "butternut-squash-ravioli": ["empanadas/calabaza-cabra"],
    "pappardelle-with-porcini-and-veal-bolognese": ["croquetas/boletus"],
    "porcini-with-rosemary-and-garlic": ["croquetas/boletus"],
    "passatelli-in-brodo": ["croquetas/pollo-arguinano"],
    "parmigiano-fonduta-tortellini-in-brodo": ["croquetas/marisa-sanchez-echaurren",
                                               "empanadas/pollo"],
    "caramelle-with-caramelized-onion-and-balsamic": ["empanadas/queso-azul-nueces"],
    "timballo-alla-teramana": ["empanadas/espinacas"],
    "prosciutto-and-goat-cheese-cappelletti": ["empanadas/espinacas"],
    "oxtail-ravioli": ["croquetas/rabo-de-toro", "empanadas/rabo-de-toro"],
    "pulled-pork-raviolo": ["empanadas/zorza-raxo"],
    "bigoli-in-salsa": ["croquetas/puerro"],
    "goat-s-cheese-ravioli": ["empanadas/calabaza-cabra"],
}

if __name__ == "__main__":
    gated = {k: v for k, v in DRIVERS.items() if v}
    print(f"{len(DRIVERS)} dishes, {len(gated)} season-gated, "
          f"{len(DRIVERS) - len(gated)} year-round")
    print(f"{sum(len(v) for v in REUSE.values())} reuse links "
          f"across {len(REUSE)} dishes")
    seen = sorted({i for v in DRIVERS.values() for i in v})
    print(f"\n{len(seen)} distinct gating ingredients:")
    print("  " + ", ".join(seen))
