# -*- coding: utf-8 -*-
"""Soulbound v0.38.12 — Named Dungeon Entry / Return.

At a dungeon threshold the player uses the dungeon name instead of a compass
boundary direction. `wyjście` / `exit` returns to the same safe threshold.
Interior exploration still uses normal directions.
"""

V03812_DUNGEON_COMMANDS_VERSION = "0.38.12"


def _v03812_norm(value):
    return normalize_lookup_text(str(value or "")).strip()


def _v03812_spec(label, anchor, target, aliases, guide):
    return {
        "label": str(label),
        "anchor": str(anchor),
        "target": str(target),
        "aliases": tuple(_v03812_norm(x) for x in aliases),
        "guide": str(guide),
    }


DUNGEON_ENTRY_SPECS_V03812 = [
    _v03812_spec(
        "Krypta", "crypt_entrance", "crypt_hall",
        ("krypta", "krypty", "crypt", "crypts"), "krypta",
    ),
    _v03812_spec(
        "Mityczna Krypta", "mythic_crypt_gate", mythic_crypt_floor_id(1),
        ("mityczna krypta", "mityczne krypty", "mythic crypt"), "mityczna krypta",
    ),
    _v03812_spec(
        "Wieża Astralna", "astral_gate", astral_floor_id(ASTRAL_MIN_FLOOR),
        ("wieza", "wieża", "wieza astralna", "wieża astralna", "astral tower"), "wieza astralna",
    ),
    _v03812_spec(
        "Mityczna Wieża Astralna", "mythic_astral_gate", mythic_astral_floor_id(1),
        ("mityczna wieza", "mityczna wieża", "mityczna wieza astralna", "mityczna wieża astralna", "mythic astral tower"),
        "mityczna wieza astralna",
    ),
    _v03812_spec(
        "Twierdza Gigantów", "giant_fortress_gate", giant_fortress_floor_id(1),
        ("twierdza", "twierdza gigantow", "twierdza gigantów", "giant fortress"), "twierdza gigantow",
    ),
    _v03812_spec(
        "Kopalnia Głębinowa", "crystal_chamber", mine_floor_id(MINE_MIN_FLOOR),
        ("kopalnia", "kopalnia glebinowa", "kopalnia głębinowa", "deep mine"), "kopalnia glebinowa",
    ),
    _v03812_spec(
        "Kryształowe Groty", "crystal_chamber", profession_dungeon_room_id("crystal_mine", 1),
        ("krysztalowe groty", "kryształowe groty", "crystal grottos"), "krysztalowe groty",
    ),
    _v03812_spec(
        "Zatopiona Grota", "sea_pier", profession_dungeon_room_id("sunken_grotto", 1),
        ("zatopiona grota", "sunken grotto"), "zatopiona grota",
    ),
    _v03812_spec(
        "Pradawny Las", "deep_grove", profession_dungeon_room_id("ancient_forest", 1),
        ("pradawny las", "ancient forest"), "pradawny las",
    ),
    _v03812_spec(
        "Ogród Alchemika", "herbalist_hut", profession_dungeon_room_id("alchemy_garden", 1),
        ("ogrod alchemika", "ogród alchemika", "alchemy garden"), "ogrod alchemika",
    ),
    _v03812_spec(
        "Jaskinia Trolli", "troll_cave_entrance", "troll_cave_1",
        ("jaskinia trolli", "trolle", "troll cave"), "jaskinia trolli",
    ),
    _v03812_spec(
        "Nieskończony Kompleks Magitek", "magitek_gate", "magitek_yard",
        ("magitek", "kompleks magitek", "magitek dungeon", "nieskonczony magitek", "nieskończony magitek"), "magitek",
    ),
]

# Every authored megadungeon gate follows the same boundary rule.
for _mega_key, _mega_spec in V020_MEGADUNGEONS.items():
    DUNGEON_ENTRY_SPECS_V03812.append(
        _v03812_spec(
            _mega_spec["name"], v0200_mega_gate_id(_mega_key), v0200_mega_room_id(_mega_key, 1),
            (_mega_spec["name"], f"megaloch {_mega_spec['name']}", f"megadungeon {_mega_key}"),
            _mega_spec["name"],
        )
    )


def _v03812_specs_for_anchor(room_id):
    rid = str(room_id or "")
    return [spec for spec in DUNGEON_ENTRY_SPECS_V03812 if spec["anchor"] == rid]


def _v03812_direction_to(room_id, target):
    room = ROOMS.get(str(room_id or ""), {})
    for direction, candidate in (room.get("exits", {}) or {}).items():
        if str(candidate) == str(target):
            return str(direction)
    return None


async def _try_dungeon_entry_command_v03812(self, raw):
    """Consume a dungeon-name command only when standing at its threshold."""
    if not self.character:
        return False
    query = _v03812_norm(raw)
    if not query:
        return False
    room_id = str(self.character.room_id)
    local_specs = _v03812_specs_for_anchor(room_id)
    if not local_specs:
        return False

    # Generic `loch` works when the threshold has exactly one destination.
    generic = query in {
        "loch", "lochy", "dungeon", "dungeons", "wejscie do lochu", "wejście do lochu"
    }
    candidates = local_specs if generic else [
        spec for spec in local_specs if query in spec["aliases"]
    ]
    if not candidates:
        return False
    if len(candidates) > 1:
        await self.send(
            "Przy tym wejściu są dwa różne miejsca: "
            + ", ".join(spec["label"] for spec in candidates)
            + ". Wpisz nazwę wybranego miejsca."
        )
        return True

    spec = candidates[0]
    target = str(spec["target"])
    if target not in ROOMS:
        self.server.world.ensure_runtime_room(target)
    direction = _v03812_direction_to(room_id, target)
    if direction is None:
        await self.send(
            f"Wejście do {spec['label']} jest chwilowo niedostępne z tej lokacji. "
            f"Użyj prowadz {spec['guide']} i spróbuj ponownie."
        )
        return True

    self._dungeon_entry_label_v03812 = spec["label"]
    try:
        await self.move(direction)
    finally:
        self._dungeon_entry_label_v03812 = ""
    return True


Session.try_dungeon_entry_command_v03812 = _try_dungeon_entry_command_v03812


# `wyjście` must return to the same threshold used by the named-entry command.
_dungeon_exit_destination_before_v03812 = Session.dungeon_exit_destination


def _dungeon_exit_destination_v03812(self, room_id=None):
    rid = str(room_id or (self.character.room_id if self.character else ""))

    # The ordinary Crypt has a two-room vestibule. Treat both interior rooms
    # and all generated floors as one dungeon and return to Przedsionek Krypty.
    if rid in ("crypt_hall", "crypt_depths") or crypt_floor_number(rid) is not None:
        return "crypt_entrance", "Krypta"

    # v0.20 megadungeons did not previously participate in dungeonexit.
    identity = v0200_mega_identity(rid)
    if identity:
        key, _index = identity
        return v0200_mega_gate_id(key), V020_MEGADUNGEONS[key]["name"]

    result = _dungeon_exit_destination_before_v03812(self, rid)
    return result


Session.dungeon_exit_destination = _dungeon_exit_destination_v03812


# Guide must stop at the threshold, never inside a profession dungeon/mine.
GUIDE_DESTINATION_ALIASES.update({
    "kopalnia": "crystal_chamber",
    "mine": "crystal_chamber",
    "kopalnia glebinowa": "crystal_chamber",
    "kopalnia głębinowa": "crystal_chamber",
    "deep mine": "crystal_chamber",
    "kopalnia krysztalow": "crystal_chamber",
    "kopalnia kryształów": "crystal_chamber",
    "krysztalowe groty": "crystal_chamber",
    "kryształowe groty": "crystal_chamber",
    "crystal grottos": "crystal_chamber",
    "zatopiona grota": "sea_pier",
    "sunken grotto": "sea_pier",
    "pradawny las": "deep_grove",
    "ancient forest": "deep_grove",
    "ogrod alchemika": "herbalist_hut",
    "ogród alchemika": "herbalist_hut",
    "alchemy garden": "herbalist_hut",
    "magitek": "magitek_gate",
    "kompleks magitek": "magitek_gate",
    "magitek dungeon": "magitek_gate",
})

HELP_TOPICS["wejscia_lochow_v03812"] = [
    "v0.38.12: prowadzenie do lochu kończy się przy jego progu. Nie trzeba wpisywać kierunku granicznego.",
    "Przy Przedsionku Krypty wpisz krypta albo krypty. Przy Astralnej Bramie wpisz wieza albo wieza astralna.",
    "Tak samo działają: mityczna krypta, mityczna wieza astralna, twierdza gigantow, kopalnia, krysztalowe groty, zatopiona grota, pradawny las, ogrod alchemika, jaskinia trolli i magitek.",
    "Przy pojedynczym wejściu możesz też wpisać loch / dungeon. Jeśli z jednego miejsca prowadzą dwa lochy, gra poprosi o konkretną nazwę.",
    "Wewnątrz lochu normalne kierunki nadal służą do eksploracji pięter i pomieszczeń.",
    "wyjście / wyjscie / exit / cofnij natychmiast wraca do bezpiecznego progu danego rozpoznanego lochu.",
]
HELP_TOPIC_ALIASES.update({
    "wejscia lochow": "wejscia_lochow_v03812",
    "wejścia lochów": "wejscia_lochow_v03812",
    "wejscie do lochu": "wejscia_lochow_v03812",
    "wejście do lochu": "wejscia_lochow_v03812",
    "dungeon entry": "wejscia_lochow_v03812",
})
HELP_TOPICS.setdefault("nawigacja", []).append(
    "v0.38.12: po doprowadzeniu do progu lochu wpisujesz jego nazwę, np. krypty, wieza astralna lub jaskinia trolli; nie wpisujesz kierunku wejściowego. `wyjście` wraca do tego progu."
)
HELP_TOPICS.setdefault("dungeon_exit", []).append(
    "v0.38.12: wyjście wraca dokładnie do bezpiecznego progu, z którego wchodzi się komendą nazwy lochu; zwykła Krypta wraca do Przedsionka Krypty."
)
HELP_TOPICS.setdefault("krypta", []).append(
    "v0.38.12: po `prowadz krypta` w Przedsionku wpisz `krypty` albo `krypta`, aby wejść bez podawania kierunku. `wyjście` wraca do Przedsionka."
)
HELP_TOPICS.setdefault("wieza", []).append(
    "v0.38.12: przy Astralnej Bramie wpisz `wieza` lub `wieza astralna`, aby wejść bez podawania kierunku. `wyjście` wraca do bramy."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.12: nazwane wejścia do Krypt, Wież i lochów zastępują ręczny kierunek na granicy; `wyjście` wraca do progu wejściowego."
)


def dungeon_named_entry_audit_v03812():
    errors = []
    checked = 0
    for spec in DUNGEON_ENTRY_SPECS_V03812:
        anchor = spec["anchor"]
        target = spec["target"]
        if anchor not in ROOMS:
            errors.append(f"missing anchor {anchor} for {spec['label']}")
            continue
        # Lazy destinations are allowed, but the edge itself must exist.
        direction = _v03812_direction_to(anchor, target)
        if direction is None:
            errors.append(f"no threshold edge {anchor}->{target} for {spec['label']}")
            continue
        if not spec["aliases"]:
            errors.append(f"no aliases for {spec['label']}")
            continue
        checked += 1

    # Exact regression requested by the user.
    probe = type("_V03812Probe", (), {})()
    probe.character = type("_V03812Char", (), {"room_id": crypt_floor_id(1)})()
    crypt_exit = Session.dungeon_exit_destination(probe)
    if not crypt_exit or crypt_exit[0] != "crypt_entrance":
        errors.append(f"crypt exit={crypt_exit!r}, expected crypt_entrance")

    # Guide aliases for profession dungeons must point outside.
    guide_expected = {
        "kopalnia": "crystal_chamber",
        "krysztalowe groty": "crystal_chamber",
        "zatopiona grota": "sea_pier",
        "pradawny las": "deep_grove",
        "ogrod alchemika": "herbalist_hut",
    }
    for alias, expected in guide_expected.items():
        actual = GUIDE_DESTINATION_ALIASES.get(alias)
        if actual != expected:
            errors.append(f"guide {alias}={actual!r}, expected {expected!r}")

    return {
        "version": V03812_DUNGEON_COMMANDS_VERSION,
        "entries_checked": checked,
        "entry_specs": len(DUNGEON_ENTRY_SPECS_V03812),
        "error_count": len(errors),
        "errors": errors,
    }


DUNGEON_NAMED_ENTRY_AUDIT_V03812 = dungeon_named_entry_audit_v03812()
if DUNGEON_NAMED_ENTRY_AUDIT_V03812["error_count"]:
    raise RuntimeError(
        "Dungeon Named Entry Audit v0.38.12 failed: "
        + "; ".join(DUNGEON_NAMED_ENTRY_AUDIT_V03812["errors"][:100])
    )


LATEST_CHANGES_TITLE = "Soulbound v0.38.12 - Named Dungeon Entry & Return"
LATEST_CHANGES = [
    "Przy progu Krypty, Wieży lub lochu wpisujesz nazwę miejsca zamiast kierunku granicznego.",
    "Przykłady: krypty, wieza astralna, mityczna krypta, twierdza gigantow, jaskinia trolli, magitek.",
    "wyjście / wyjscie / exit wraca do bezpiecznego progu wejściowego; zwykła Krypta wraca do Przedsionka Krypty.",
    "Prowadzenie do Kopalni Głębinowej i lochów profesyjnych zatrzymuje się teraz przed wejściem.",
    "Wejście nazwą nie czyta sztucznego kierunku granicznego; wewnątrz zwykłe kierunki pozostają do eksploracji.",
    "Zmiana obejmuje także Nieskończony Kompleks Magitek i pięć megalochów v0.20.",
    "Brak zmian balansu i brak wipe SQLite.",
]
