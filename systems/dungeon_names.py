# -*- coding: utf-8 -*-
"""Shared procedural display names for dungeon mobs.

v1.13.36 contract:
- dungeon mob display names never expose floor/level numbers;
- infinite floors still get deterministic, unique readable names;
- room names and progression commands keep numeric floor information.
"""

DUNGEON_MOB_NAME_THEMES_V11336 = {
    "crypt": (
        "Kościana Warta", "Grobowy Mrok", "Krwawy Korytarz",
        "Popielna Krypta", "Widmowy Chód", "Nekrotyczny Krąg",
        "Otchłanny Znak", "Pustkowa Straż", "Przeklęty Grobowiec",
        "Wieczna Katakumba",
    ),
    "mythic_crypt": (
        "Mityczna Kość", "Duszożerny Mrok", "Czarny Płomień",
        "Żelazny Grobowiec", "Bezdenny Krąg", "Astralny Grób",
        "Pustkowa Pieczęć", "Widmowy Tron", "Kres Katakumb",
        "Wieczna Otchłań",
    ),
    "astral": (
        "Gwiezdna Brama", "Pył Konstelacji", "Mgła Nebuli",
        "Ślad Komety", "Gwiezdny Ogień", "Orbitalny Krąg",
        "Pęknięcie Sfer", "Seraficzna Pustka", "Burza Gwiazd",
        "Firmament",
    ),
    "mythic_astral": (
        "Mityczny Rezonans", "Pęknięta Konstelacja", "Czarna Nebula",
        "Upadła Kometa", "Wieczny Gwiazdozbiór", "Otchłań Sfer",
        "Astralny Bastion", "Pustkowy Firmament", "Burza Wieczności",
        "Tron Suwerena",
    ),
    "giant": (
        "Kamienny Garnizon", "Sala Miotaczy", "Runiczny Bastion",
        "Górski Mur", "Cyklopia Warta", "Burzowa Cytadela",
        "Żelazny Dziedziniec", "Królewski Szaniec", "Tytaniczny Krąg",
        "Tron Gigantów",
    ),
    "sunken_grotto": (
        "Mętna Toń", "Zatopiony Prąd", "Głębinowa Szczelina",
        "Słona Otchłań", "Wrakowy Szlak", "Ciemna Rafa",
        "Studnia Prądu", "Syreni Przesmyk", "Głębinowy Wir",
        "Dno Bez Światła",
    ),
    "ancient_forest": (
        "Stary Korzeń", "Cierniowy Ostęp", "Dziki Gaj",
        "Omszała Knieja", "Pradawna Kora", "Leśny Krąg",
        "Zielony Mrok", "Duchowy Matecznik", "Splątany Ostęp",
        "Serce Lasu",
    ),
    "alchemy_garden": (
        "Cierniowy Sektor", "Toksyczna Grządka", "Zarodnikowy Krąg",
        "Mutacyjna Aleja", "Ogród Oparów", "Kwasowy Kwartał",
        "Esencjonalny Węzeł", "Trujący Labirynt", "Alchemiczny Rozrost",
        "Serce Mutacji",
    ),
    "deep_dungeon": (
        "Mroczna Szczelina", "Zapomniany Trakt", "Pęknięta Otchłań",
        "Widmowy Korytarz", "Czarna Komnata", "Głęboki Labirynt",
        "Martwy Przesmyk", "Przeklęty Krąg", "Pustkowy Szlak",
        "Bezdenna Droga",
    ),
    "deep_dungeon_apanda": (
        "Straż Progu", "Kamień Próby", "Cień Otchłani",
        "Pieczęć Głębi", "Warta Bezdenna", "Próg Ciszy",
        "Krąg Strażnika", "Mroczna Pieczęć", "Brama Głębi",
        "Wieczna Warta",
    ),
    "magitek": (
        "Patrol Alfa", "Węzeł Beta", "Sektor Gamma",
        "Rdzeń Delta", "Kanał Epsilon", "Macierz Zeta",
        "Obwód Eta", "Pętla Theta", "Moduł Iota", "Sieć Kappa",
    ),
    "magitek_elite": (
        "Przeciążony Rdzeń", "Pancerz Omega", "Węzeł Wojenny",
        "Reaktor Szturmowy", "Macierz Oblężnicza", "Protokół Zagłady",
        "Pętla Bojowa", "Rdzeń Niszczyciela", "Sektor Czerwony",
        "Kanał Krytyczny",
    ),
    "magitek_boss": (
        "Protokół Alfa", "Protokół Beta", "Protokół Gamma",
        "Protokół Delta", "Protokół Epsilon", "Protokół Zeta",
        "Protokół Eta", "Protokół Theta", "Protokół Iota",
        "Protokół Omega",
    ),
}

# Bijective syllable alphabet. Encoding the ordinal this way gives every
# procedural floor a stable unique word without ever putting digits on screen.
_DUNGEON_NAME_SYLLABLES_V11336 = (
    "mor", "vel", "kar", "dra", "zel", "tor", "nar", "vyr",
    "sal", "kor", "mir", "ran", "thal", "zor", "fen", "gar",
    "lor", "var", "ser", "bel", "rin", "dar", "vor", "kyn",
)


def dungeon_depth_word_v11336(floor, variant=0):
    floor = max(1, int(floor))
    variant = max(0, int(variant))
    base = len(_DUNGEON_NAME_SYLLABLES_V11336)

    # Reserve a fixed variant lane per floor, then offset by one base so even
    # shallow floors have a natural two-syllable codename.
    value = (floor - 1) * 32 + variant + 1 + base
    parts = []
    while value > 0:
        value -= 1
        parts.append(_DUNGEON_NAME_SYLLABLES_V11336[value % base])
        value //= base
    return "".join(reversed(parts)).capitalize()


def dungeon_mob_display_name_v11336(kind, base_name, floor, variant=0):
    floor = max(1, int(floor))
    variant = max(0, int(variant))
    themes = DUNGEON_MOB_NAME_THEMES_V11336.get(str(kind), ())
    codename = dungeon_depth_word_v11336(floor, variant=variant)
    if not themes:
        return f"{str(base_name).strip()} {codename}".strip()
    theme = themes[(floor - 1 + variant) % len(themes)]
    return f"{str(base_name).strip()} {codename}".strip()


def dungeon_mob_name_audit_v11336():
    errors = []
    kinds = tuple(DUNGEON_MOB_NAME_THEMES_V11336)
    for kind in kinds:
        seen = set()
        for floor in range(1, 2001):
            name = dungeon_mob_display_name_v11336(
                kind, "Przeciwnik Testowy", floor
            )
            if any(ch.isdigit() for ch in name):
                errors.append(
                    f"{kind}: digit leaked into display name at floor {floor}: {name}"
                )
                break
            if name in seen:
                errors.append(
                    f"{kind}: duplicate display name at floor {floor}: {name}"
                )
                break
            seen.add(name)

    # Multiple mobs sharing one floor also need separate identities.
    for kind in kinds:
        names = {
            dungeon_mob_display_name_v11336(
                kind, "Przeciwnik Testowy", 777, variant=variant
            )
            for variant in range(8)
        }
        if len(names) != 8:
            errors.append(f"{kind}: same-floor variants are not unique")

    return {
        "version": "1.13.36",
        "checked_kinds": len(kinds),
        "sampled_floors_per_kind": 2000,
        "error_count": len(errors),
        "errors": errors,
    }


DUNGEON_MOB_NAME_AUDIT_V11336 = dungeon_mob_name_audit_v11336()
