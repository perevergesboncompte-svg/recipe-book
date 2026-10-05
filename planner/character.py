"""When a dish wants to be eaten, independent of whether its produce is sold.

Availability is a hard gate; this is the soft one. Savoy cabbage is sold in
August in Orange County, but pizzoccheri is a cabbage, potato and fontina dish
from the Alps and belongs in the cold half of the year.
"""

COLD = {10, 11, 12, 1, 2, 3}
WARM = {5, 6, 7, 8, 9}
SPRING = {3, 4, 5, 6}
ANY = set(range(1, 13))

CHARACTER = {
    "pizzoccheri-alla-valtellinese": COLD,
    "canederli": COLD,
    "passatelli-in-brodo": COLD,
    "parmigiano-fonduta-tortellini-in-brodo": COLD,
    "tagliatelle-alla-bolognese": COLD,
    "tagliatelle-with-ossobuco-and-soffritto": COLD,
    "maccheroncini-di-campofilone-al-sugo": COLD,
    "agnolotti-dal-plin-brisket": COLD,
    "timballo-alla-teramana": COLD,
    "cjalsons": COLD,
    "balanzoni-burro-e-salvia": COLD,
    "tortelli-di-zucca": COLD,
    "oxtail-ravioli": COLD,
    "pulled-pork-raviolo": COLD,
    "duck-ravioli-with-langoustines": COLD,
    "turkey-and-squash-ravioli": COLD,
    "butternut-squash-ravioli": COLD,
    "butternut-squash-and-marjoram-ravioli": COLD,
    "pappardelle-with-porcini-and-veal-bolognese": COLD,
    "strangozzi-alla-norcina": COLD,
    "tajarin-al-tartufo": COLD,
    "truffle-ravioli": COLD,
    "polenta-ravioli": COLD,
    "corzetti-with-chanterelles-and-aged-goat-cheese": COLD,
    "tagliatelle-with-matsutake-lemon-and-mint": COLD,
    "crab-ravioli-corrigan": COLD,
    "crab-ravioli-with-crab-sauce": COLD,
    "crab-with-turnip": COLD,
    "caramelle-with-caramelized-onion-and-balsamic": COLD,
    "rigatoni-diavola": COLD,
    "bucatini-all-amatriciana": COLD,

    "busiate-al-pesto-trapanese": WARM,
    "corzetti-with-sungold-tomatoes-and-pecorino": WARM,
    "eggplant-mezzelune-with-ricotta-salata": WARM,
    "trofie-al-pesto-genovese": WARM,
    "aubergine-ravioli": WARM,
    "spaghetti-with-colatura-and-bread-crumbs": WARM,
    "sheeps-milk-ricotta-occhi-with-bottarga": WARM,
    "spaghetti-alla-puttanesca": WARM,
    "smoked-potato-ravioli": WARM,
    "pink-prawn-ravioli": WARM,
    "langoustine-ravioli": WARM,

    "stricchetti-with-smashed-peas-and-prosciutto": SPRING,
    "ravioli-with-taleggio-fonduta-peas-and-speck": SPRING,
    "orecchiette-con-cime-di-rapa": SPRING,
    "watercress-and-egg-yolk-ravioli": SPRING,

    "fettuccine-alfredo": ANY,
    "penne-alla-vodka": ANY,
    "corzetti-alle-erbe": ANY,
    "culurgiones-alla-nuorese": ANY,
    "potato-and-creme-fraiche-ravioli": ANY,
    "goat-s-cheese-ravioli": ANY,
    "prawn-and-smoked-salmon-ravioli": ANY,
    "bigoli-in-salsa": ANY,
    "prosciutto-and-goat-cheese-cappelletti": ANY,
}

CONTORNI_CHARACTER = {
    "grilled-summer-beans-with-garlic-vinaigrette": WARM,
    "porcini-with-rosemary-and-garlic": COLD,
    "roasted-eggplant-with-olives-and-sun-dried-tomato": WARM,
    "roasted-kabocha-squash-with-hot-honey": COLD,
}
