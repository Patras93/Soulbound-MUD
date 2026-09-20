COLLECTION_CATEGORY_ALIASES = {
    "fish": "fish", "ryby": "fish", "ryba": "fish",
    "minerals": "minerals", "mineral": "minerals", "mineraly": "minerals", "minerały": "minerals", "rudy": "minerals",
    "herbs": "herbs", "herb": "herbs", "ziola": "herbs", "zioła": "herbs",
    "gems": "gems", "gem": "gems", "klejnoty": "gems", "klejnot": "gems",
    "materials": "materials", "material": "materials", "materialy": "materials", "materiały": "materials",
    "unique": "unique", "unikalne": "unique", "wyjatkowe": "unique", "wyjątkowe": "unique",
    "equipment": "equipment", "eq": "equipment", "ekwipunek": "equipment", "sprzet": "equipment", "sprzęt": "equipment",
    "named": "named", "namedloot": "named", "loot": "named",
    "set": "sets", "sets": "sets", "sety": "sets",
    "boss": "bosses", "bosses": "bosses", "bossowie": "bosses",
    "rare": "rare", "raremobs": "rare", "raremoby": "rare",
    "chest": "chests", "chests": "chests", "skrzynie": "chests",
}

ACHIEVEMENT_TRACKS = {
    "goblin_kills": {
        "name": "Pogromca Goblinów",
        "tiers": ((10, "Bronze"), (50, "Silver"), (100, "Gold"), (250, "Platinum")),
    },
    "chests_opened": {
        "name": "Otwieracz Skrzyń",
        "tiers": ((10, "Bronze"), (25, "Silver"), (50, "Gold"), (100, "Platinum")),
    },
    "rare_kills": {
        "name": "Łowca Rare",
        "tiers": ((3, "Bronze"), (10, "Silver"), (25, "Gold"), (50, "Platinum")),
    },
    "boss_kills": {
        "name": "Pogromca Bossów",
        "tiers": ((5, "Bronze"), (15, "Silver"), (30, "Gold"), (60, "Platinum")),
    },
    "exploration_rooms": {
        "name": "Kartograf Świata",
        "tiers": ((100, "Bronze"), (500, "Silver"), (1000, "Gold"), (1272, "Platinum")),
    },
    "profession_masters": {
        "name": "Mistrz Profesji",
        "tiers": ((1, "Bronze"), (3, "Silver"), (5, "Gold"), (8, "Platinum")),
    },
    "profession_transcendents": {
        "name": "Transcendentny Mistrz Profesji",
        "tiers": ((1, "Bronze"), (3, "Silver"), (5, "Gold"), (8, "Platinum")),
    },
    "bestiary_unique": {
        "name": "Kronikarz Bestiariusza",
        "tiers": ((50, "Bronze"), (250, "Silver"), (500, "Gold"), (953, "Platinum")),
    },
    "rare_fish_caught": {
        "name": "Łowca Rzadkich Ryb",
        "tiers": ((1, "Bronze"), (10, "Silver"), (50, "Gold"), (200, "Platinum")),
    },
    "gems_found": {
        "name": "Poszukiwacz Klejnotów",
        "tiers": ((1, "Bronze"), (25, "Silver"), (100, "Gold"), (500, "Platinum")),
    },
    "multiclass_classes": {
        "name": "Droga Wielu Klas",
        "tiers": ((2, "Silver"), (3, "Platinum")),
    },
    "soul_level": {
        "name": "Mistrz Broni Duszy",
        "tiers": ((50, "Bronze"), (100, "Silver"), (150, "Gold"), (200, "Platinum"), (400, "Mythic")),
    },
    "bounties_completed": {
        "name": "Łowca Kontraktów",
        "tiers": ((5, "Bronze"), (25, "Silver"), (100, "Gold"), (250, "Platinum")),
    },
}

ACHIEVEMENT_TITLE_REWARDS = {
    ("rare_kills", "Gold"): "Łowca Rare",
    ("boss_kills", "Gold"): "Pogromca Bossów",
    ("chests_opened", "Gold"): "Mistrz Skrzyń",
    ("goblin_kills", "Gold"): "Goblinobójca",
    ("exploration_rooms", "Gold"): "Kartograf Świata",
    ("exploration_rooms", "Platinum"): "Odkrywca Całego Świata",
    ("profession_masters", "Gold"): "Mistrz Profesji",
    ("profession_masters", "Platinum"): "Arcymistrz Ośmiu Profesji",
    ("profession_transcendents", "Platinum"): "Transcendentny Mistrz Ośmiu Profesji",
    ("bestiary_unique", "Gold"): "Kronikarz Bestiariusza",
    ("bestiary_unique", "Platinum"): "Mistrz Bestiariusza",
    ("rare_fish_caught", "Gold"): "Łowca Rzadkich Ryb",
    ("gems_found", "Gold"): "Poszukiwacz Klejnotów",
    ("multiclass_classes", "Platinum"): "Mistrz Wielu Dróg",
    ("soul_level", "Gold"): "Władca Broni Duszy",
    ("soul_level", "Platinum"): "Dusza Doskonała",
    ("soul_level", "Mythic"): "Dusza Absolutu",
    ("bounties_completed", "Gold"): "Łowca Kontraktów",
}

# v0.9.3 - losowana Tablica Zleceń. Nagrody są umiarkowane i nie zmieniają
# istniejących mnożników walki ani ekonomii. Jedna postać może mieć jeden
# aktywny kontrakt, a jego licznik jest trwały w SQLite.
BOUNTY_OFFER_COUNT = 3
BOUNTY_KINDS = ("kill", "mine", "fish", "wood", "herb", "explore", "event", "secret", "mini")
BOUNTY_RESOURCE_LABELS = {
    "mine": "Wydobycie rud",
    "fish": "Połów ryb",
    "wood": "Pozyskanie drewna",
    "herb": "Zbiór ziół",
    "explore": "Eksploracja rubieży",
    "event": "Wydarzenia świata",
    "secret": "Odkrywanie sekretów",
    "mini": "Mini-lochy",
}
BOUNTY_RESOURCE_NEEDS = {
    "mine": (6, 8, 10, 12),
    "fish": (5, 6, 8, 10),
    "wood": (6, 8, 10, 12),
    "herb": (6, 8, 10, 12),
    "explore": (8, 12, 16, 20),
    "event": (1, 2, 3, 4),
    "secret": (1, 2, 3),
    "mini": (1, 2, 3),
}

def bounty_reward_values(kind, needed):
    needed = max(1, int(needed))
    base = {"kill": 180, "mine": 140, "fish": 120, "wood": 130, "herb": 130, "explore": 160, "event": 260, "secret": 320, "mini": 420}.get(kind, 120)
    per = {"kill": 28, "mine": 22, "fish": 20, "wood": 20, "herb": 20, "explore": 18, "event": 90, "secret": 120, "mini": 150}.get(kind, 20)
    soul_xp = base + needed * per
    gold = max(1, min(5, 1 + needed // 6))
    return soul_xp, gold


def _collection_slug(value):
    text = str(value or "").strip().lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "region"


def _zone_title(zone):
    special = {
        "Nekropolia": "Pogromca Nekropolii",
        "Lodowe Jaskinie": "Mistrz Wiecznego Lodu",
        "Ruiny Kultystów": "Łamacz Kultu Pustki",
        "Stary Cmentarz": "Strażnik Starego Cmentarza",
        "Legowisko Bestii": "Pogromca Legowiska Bestii",
        "Kanały Pod Miastem": "Odkrywca Podmiejskich Kanałów",
        "Jaskinie Goblinów": "Kartograf Jaskiń Goblinów",
        "Obozowiska Bandytów": "Pogromca Obozowisk Bandytów",
        "Las Szeptów": "Strażnik Lasu Szeptów",
        "Ruiny Strażnicy": "Pogromca Ruin Strażnicy",
    }
    return special.get(zone, f"Odkrywca: {zone}")



# ============================================================
# v0.9.23 - ENDGAME REGIONS 300-400 + STEEL RECYCLING
# ============================================================
# Cztery zwykłe regiony świata dają alternatywę dla nieskończonych Krypt/Wież.
# Każdy region ma własną ZALECANĄ Biegłość aktywnej klasy, kilka gatunków mobów
# i bossa świata. Nie są instancjami i nie generują nieskończonych pięter.
# v0.9.24: zalecenie nigdy nie blokuje wejścia — ryzyko podejmuje gracz.
V0923_ENDGAME_REGIONS = (
    ("Popielne Pustkowia", 300),
    ("Rozbite Niebo", 330),
    ("Wybrzeże Pustki", 360),
    ("Korona Świata", 390),
)

# Zlecenie Haldora: Stalowe Płyty są materiałem rzemieślniczym.
# v0.30.34: najpierw fizycznie trafiają na ciało moba; po zabraniu z ciała
# są przenoszone do Szkatułki i dopiero wtedy zaliczają postęp questa.
ITEMS["salvaged_steel_plate"] = {
    "name": "Stalowa Płyta z Pancerza",
    "type": "craft_material",
    "price": None,
    "craftbox_category": "blacksmithing",
    "desc": (
        "Ciężka płyta odzyskana ze starego pancerza nieumarłych. "
        "Cztery płyty można oddać w godzinnym zleceniu Haldora albo "
        "samodzielnie przetopić w 1 Sztabkę Stali."
    ),
}
ITEMS["steel_ingot"] = {
    "name": "Sztabka Stali",
    "type": "craft_material",
    "price": None,
    "craftbox_category": "blacksmithing",
    "desc": "Sztabka stali odzyskana przez przetopienie czterech Stalowych Płyt z Pancerza.",
}
CRAFT_MATERIAL_STORAGE_IDS = frozenset(
    set(CRAFT_MATERIAL_STORAGE_IDS) | {"salvaged_steel_plate", "steel_ingot"}
)

# v0.31.12: odłamki żelaza z salvage można ponownie przetopić w pełny materiał.
CRAFT_RECIPES["recycled_iron_ingot"] = {
    "name": "Przetop Odłamków Żelaza",
    "stations": ("forge",),
    "ingredients": {"salvage_iron_scrap": 2},
    "output": "iron_ingot",
    "quantity": 1,
    "min_profession_level": 1,
    "profession_xp": 12,
    "tool_xp": 10,
    "category": "smithing",
    "desc": "Przetop 2 Odłamki Żelaza ze Szkatułki Rzemieślniczej w 1 Żelazną sztabkę.",
}

# v0.31.13: standardowy `przetop <metal>` potrafi automatycznie sięgnąć
# do Szkatułki -> Salvage, gdy zabraknie zwykłej rudy w Sakwie Górnika.
# Salvage jest mniej wydajny od świeżej rudy: 2 fragmenty = 1 sztabka.
SALVAGE_SMELT_FALLBACK_V03113 = {
    "iron_ingot": "recycled_iron_ingot",
    "steel_ingot": "recycled_steel_scrap_ingot_v03113",
    "cobalt_ingot": "recycled_cobalt_ingot_v03113",
    "runestone_ingot": "recycled_runic_ingot_v03113",
    "dragonsteel_ingot": "recycled_dragonsteel_ingot_v03113",
    "astral_ingot": "recycled_astral_ingot_v03113",
    "void_ingot": "recycled_void_ingot_v03113",
    "eternium_ingot": "recycled_eternium_ingot_v03113",
}

_SALVAGE_SMELT_DEFS_V03113 = (
    ("recycled_steel_scrap_ingot_v03113", "Przetop Odłamków Stali", "salvage_steel_scrap", "steel_ingot", 1),
    ("recycled_cobalt_ingot_v03113", "Przetop Fragmentów Kobaltu", "salvage_cobalt_fragment", "cobalt_ingot", 100),
    ("recycled_runic_ingot_v03113", "Przetop Fragmentów Runicznych", "salvage_runic_fragment", "runestone_ingot", 120),
    ("recycled_dragonsteel_ingot_v03113", "Przetop Fragmentów Smoczej Stali", "salvage_dragonsteel_fragment", "dragonsteel_ingot", 140),
    ("recycled_astral_ingot_v03113", "Przetop Fragmentów Astralnych", "salvage_astral_fragment", "astral_ingot", 160),
    ("recycled_void_ingot_v03113", "Przetop Fragmentów Pustki", "salvage_void_fragment", "void_ingot", 180),
    ("recycled_eternium_ingot_v03113", "Przetop Fragmentów Eternium", "salvage_eternium_fragment", "eternium_ingot", 200),
)
for _rid, _name, _fragment, _output, _level in _SALVAGE_SMELT_DEFS_V03113:
    CRAFT_RECIPES[_rid] = {
        "name": _name,
        "stations": ("forge",),
        "ingredients": {_fragment: 2},
        "output": _output,
        "quantity": 1,
        "min_profession_level": _level,
        "min_tool_level": _level,
        "profession_xp": 12 + max(0, _level // 10),
        "tool_xp": 10 + max(0, _level // 12),
        "category": "smithing",
        "desc": "Przetop 2 materiały odzyskane z Salvage w 1 właściwą sztabkę.",
    }

# v0.31.12: gracz może wykorzystać płyty poza questem Haldora.
CRAFT_RECIPES["recycled_steel_ingot"] = {
    "name": "Przetop Stalowych Płyt",
    "stations": ("forge",),
    "ingredients": {"salvaged_steel_plate": 4},
    "output": "steel_ingot",
    "quantity": 1,
    "min_profession_level": 1,
    "profession_xp": 18,
    "tool_xp": 14,
    "category": "smithing",
    "desc": "Przetop 4 Stalowe Płyty z Pancerza ze Szkatułki Rzemieślniczej w 1 Sztabkę Stali.",
}

QUESTS["haldor_steel_recycling"] = {
    "name": "Zlecenie Haldora: Stal do Przetopu",
    "giver": "Mistrz Rzemiosła Haldor",
    "kind": "collect",
    "target": "salvaged_steel_plate",
    "needed": 4,
    "progress_label": "Stalowe Płyty",
    "description": (
        "Zdobądź po przyjęciu zlecenia 4 Stalowe Płyty z opancerzonych "
        "nieumarłych na Starym Cmentarzu. Płyty znajdują się na ciałach; "
        "przeszukaj ciało albo weź płytę z ciała. Po zabraniu trafiają do "
        "Szkatułki Rzemieślniczej i zaliczają postęp. Przy oddaniu wszystkie "
        "4 płyty są zużywane."
    ),
    "specialist_tool_type": "crafting",
    "min_tool_level": 1,
    "reward_profession": "Kowalstwo",
    "reward_profession_xp": 1300,
    "reward_tool_type": "crafting",
    "reward_tool_xp": 1000,
    "reward_silver": 260,
    "reward_gold": 1,
    "reward_mithril": 0,
    "reward_items": {},
    "repeatable": True,
    "repeat_cooldown": 60 * 60,
}

# Osobny cmentarny szkielet daje czytelne źródło Płyt. Stare moby cmentarza
# również mogą je upuścić, żeby quest nie zależał od jednego respawnu.
MOB_TEMPLATES["cemetery_steel_skeleton"] = {
    "name": "Szkielet w Stalowym Kirysie",
    "max_hp": 390,
    "damage": 29,
    "damage_type": "physical",
    "silver": 72,
    "gold": 0,
    "mithril": 0,
    "stat_reward": 90,
    "class_xp_reward": 1150,
    "soul_reward": 690,
    "drops": {"soul_shard": 0.20},
    "corpse_material_chances": {"salvaged_steel_plate": 0.72},
    "quest_target": "cemetery_steel_skeleton",
}
for _mid, _chance in (
    ("cemetery_restless_dead", 0.28),
    ("cemetery_bone_collector", 0.42),
):
    if _mid in MOB_TEMPLATES:
        # v0.30.34: płyta ma być widoczna na ciele, nie przyznawana automatycznie.
        MOB_TEMPLATES[_mid].setdefault("drops", {}).pop("salvaged_steel_plate", None)
        MOB_TEMPLATES[_mid].setdefault("corpse_material_chances", {})["salvaged_steel_plate"] = _chance
MOB_SPAWNS.extend([
    ("graveyard", "cemetery_steel_skeleton"),
    ("graveyard", "cemetery_steel_skeleton"),
    ("cemetery_bone_field", "cemetery_steel_skeleton"),
    ("cemetery_fallen_chapel", "cemetery_steel_skeleton"),
])

# Endgame world route: z Obozu Szczytowego w górę zaczyna się świat 300-400.
ROOMS["summit_camp"]["exits"]["up"] = "ashen_frontier"

_v0923_rooms = {
    # 300-329
    "ashen_frontier": ("Popielne Pustkowia", "Popielna Granica", 300, {"down":"summit_camp","north":"ashen_waste","east":"cinder_ravine"}),
    "ashen_waste": ("Popielne Pustkowia", "Morze Popiołu", 300, {"south":"ashen_frontier","north":"ember_ruins","east":"ash_bonefield"}),
    "cinder_ravine": ("Popielne Pustkowia", "Wąwóz Żaru", 300, {"west":"ashen_frontier","north":"ember_ruins"}),
    "ash_bonefield": ("Popielne Pustkowia", "Pole Zwęglonych Kości", 300, {"west":"ashen_waste","north":"ashen_citadel"}),
    "ember_ruins": ("Popielne Pustkowia", "Ruiny Ostatniego Paleniska", 300, {"south":"ashen_waste","east":"ashen_citadel"}),
    "ashen_citadel": ("Popielne Pustkowia", "Cytadela Popiołu", 300, {"west":"ember_ruins","south":"ash_bonefield","up":"skybreak_gate"}),
    # 330-359
    "skybreak_gate": ("Rozbite Niebo", "Brama Rozbitego Nieba", 330, {"down":"ashen_citadel","north":"storm_bridge"}),
    "storm_bridge": ("Rozbite Niebo", "Most Burz", 330, {"south":"skybreak_gate","north":"shattered_aerie","east":"thunder_shelf"}),
    "thunder_shelf": ("Rozbite Niebo", "Półka Gromu", 330, {"west":"storm_bridge","north":"cloud_scar"}),
    "cloud_scar": ("Rozbite Niebo", "Blizna Chmur", 330, {"south":"thunder_shelf","west":"shattered_aerie"}),
    "shattered_aerie": ("Rozbite Niebo", "Rozbite Gniazdo", 330, {"south":"storm_bridge","east":"cloud_scar","north":"tempest_sanctum"}),
    "tempest_sanctum": ("Rozbite Niebo", "Sanktuarium Nawałnicy", 330, {"south":"shattered_aerie","up":"void_coast_gate"}),
    # 360-389
    "void_coast_gate": ("Wybrzeże Pustki", "Czarna Przełęcz", 360, {"down":"tempest_sanctum","north":"void_shore"}),
    "void_shore": ("Wybrzeże Pustki", "Brzeg Bez Gwiazd", 360, {"south":"void_coast_gate","north":"drowned_observatory","east":"black_tide_flats"}),
    "black_tide_flats": ("Wybrzeże Pustki", "Równina Czarnego Przypływu", 360, {"west":"void_shore","north":"starless_chapel"}),
    "drowned_observatory": ("Wybrzeże Pustki", "Zatopione Obserwatorium", 360, {"south":"void_shore","east":"starless_chapel"}),
    "starless_chapel": ("Wybrzeże Pustki", "Kaplica Bez Gwiazd", 360, {"west":"drowned_observatory","south":"black_tide_flats","north":"void_throne"}),
    "void_throne": ("Wybrzeże Pustki", "Tron Przypływu Pustki", 360, {"south":"starless_chapel","up":"world_crown_gate"}),
    # 390-400
    "world_crown_gate": ("Korona Świata", "Brama Korony Świata", 390, {"down":"void_throne","north":"eternal_causeway"}),
    "eternal_causeway": ("Korona Świata", "Wieczna Grobla", 390, {"south":"world_crown_gate","north":"crown_stair","east":"absolute_gallery"}),
    "absolute_gallery": ("Korona Świata", "Galeria Absolutu", 390, {"west":"eternal_causeway","north":"crown_stair"}),
    "crown_stair": ("Korona Świata", "Schody Korony", 390, {"south":"eternal_causeway","east":"timeless_balcony","north":"world_crown_summit"}),
    "timeless_balcony": ("Korona Świata", "Ponadczasowy Balkon", 390, {"west":"crown_stair","north":"world_crown_summit"}),
    "world_crown_summit": ("Korona Świata", "Szczyt Korony Świata", 390, {"south":"crown_stair","west":"timeless_balcony"}),
}
for _rid, (_zone, _name, _req, _exits) in _v0923_rooms.items():
    ROOMS[_rid] = {
        "zone": _zone,
        "name": _name,
        "desc": (
            f"Region endgame; zalecana Biegłość {_req}+. "
            "To zwykła strefa świata, nie nieskończona instancja."
        ),
        "exits": dict(_exits),
        "recommended_mastery": int(_req),
    }

EXP_AREAS = EXP_AREAS + (
    {
        "id":"ashen_wastes","name":"Popielne Pustkowia",
        "aliases":("popielne pustkowia","popielna granica","ash wastes"),
        "soul_min":300,"soul_max":329,"mastery_min":300,"mastery_max":329,
        "difficulty":"endgame 300-329","guide":"popielne pustkowia",
        "enemies":"Popielny Revenant, Upiór Żaru, Zwęglony Kolos, Wieszcz Popiołu i Suweren Popielnej Cytadeli",
        "description":"Pierwszy otwarty region endgame po Górach, przeznaczony dla Levelu postaci 300+.",
        "note":"To zwykły region świata, nie instancja. Zalecany Level postaci: 300; wejście nie jest blokowane.",
    },
    {
        "id":"shattered_sky","name":"Rozbite Niebo",
        "aliases":("rozbite niebo","brama rozbitego nieba","shattered sky"),
        "soul_min":330,"soul_max":359,"mastery_min":330,"mastery_max":359,
        "difficulty":"endgame 330-359","guide":"rozbite niebo",
        "enemies":"Serafin Nawałnicy, Łamacz Nieba, Gromowy Harcownik, Tytan Chmur i Królowa Rozbitej Nawałnicy",
        "description":"Wysokogórski region burzowy rozwijający otwarty endgame poza Wieżą.",
        "note":"Zalecany Level postaci: 330; wejście nie jest blokowane.",
    },
    {
        "id":"void_coast","name":"Wybrzeże Pustki",
        "aliases":("wybrzeze pustki","wybrzeże pustki","void coast"),
        "soul_min":360,"soul_max":389,"mastery_min":360,"mastery_max":389,
        "difficulty":"endgame 360-389","guide":"wybrzeze pustki",
        "enemies":"Żeglarz Pustki, Wyrocznia Czarnego Przypływu, Rycerz Bez Gwiazd, Manta Otchłani i Monarcha Przypływu Pustki",
        "description":"Czarny brzeg i zatopione obserwatorium dla późnego endgame.",
        "note":"Zalecany Level postaci: 360; wejście nie jest blokowane.",
    },
    {
        "id":"world_crown","name":"Korona Świata",
        "aliases":("korona swiata","korona świata","world crown"),
        "soul_min":390,"soul_max":400,"mastery_min":390,"mastery_max":400,
        "difficulty":"endgame 390-400","guide":"korona swiata",
        "enemies":"Strażnik Korony, Ponadczasowy Magister, Strażnik Absolutu, Echo Korony Świata i Awatar Korony Świata",
        "description":"Końcowy otwarty region progresji 390-400 z bossem na Szczycie Korony Świata.",
        "note":"Zalecany Level postaci: 390; wejście nie jest blokowane, a finał jest projektowany pod 400.",
    },
)
EXP_ZONE_AREA_ID.update({
    "Popielne Pustkowia":"ashen_wastes",
    "Rozbite Niebo":"shattered_sky",
    "Wybrzeże Pustki":"void_coast",
    "Korona Świata":"world_crown",
})
EXP_AREA_BASE_CATEGORY.update({
    "ashen_wastes":"Endgame", "shattered_sky":"Endgame",
    "void_coast":"Endgame", "world_crown":"Endgame",
})

# Moby są skalowane do odpowiednich odcinków 300-400. Każdy region ma
# kilka archetypów, a finałowy pokój ma własnego world bossa.
_v0923_mob_specs = {
    "ash_revenant": ("Popielny Revenant", 9200, 176, "physical", 28500, 4850, 300),
    "cinder_wraith": ("Upiór Żaru", 8600, 190, "magic", 29200, 5000, 300),
    "charred_colossus": ("Zwęglony Kolos", 11200, 168, "physical", 30500, 5200, 300),
    "ash_seer": ("Wieszcz Popiołu", 8900, 198, "magic", 31000, 5300, 300),
    "storm_seraph": ("Serafin Nawałnicy", 10300, 210, "magic", 34000, 5700, 330),
    "skybreaker": ("Łamacz Nieba", 12100, 205, "physical", 35000, 5900, 330),
    "thunder_harrier": ("Gromowy Harcownik", 9800, 225, "magic", 35500, 6050, 330),
    "cloud_titan": ("Tytan Chmur", 13300, 198, "physical", 36200, 6200, 330),
    "void_mariner": ("Żeglarz Pustki", 11900, 238, "physical", 39500, 6650, 360),
    "black_tide_oracle": ("Wyrocznia Czarnego Przypływu", 11100, 252, "magic", 40500, 6850, 360),
    "starless_knight": ("Rycerz Bez Gwiazd", 13900, 232, "physical", 41500, 7000, 360),
    "abyssal_manta": ("Manta Otchłani", 11600, 260, "magic", 42000, 7150, 360),
    "crown_sentinel": ("Strażnik Korony", 13600, 270, "physical", 45500, 7650, 390),
    "timeless_magister": ("Ponadczasowy Magister", 12800, 292, "magic", 46800, 7900, 390),
    "absolute_guardian": ("Strażnik Absolutu", 15100, 274, "physical", 47800, 8100, 390),
    "worldcrown_echo": ("Echo Korony Świata", 13200, 300, "magic", 48500, 8250, 390),
}
for _mid, (_name, _hp, _dmg, _dtype, _cxp, _sxp, _mastery) in _v0923_mob_specs.items():
    _tmpl = {
        "name": _name, "max_hp": _hp, "damage": _dmg, "damage_type": _dtype,
        "silver": 420 + (_mastery - 300) * 5, "gold": 3 + (_mastery - 300)//30,
        "mithril": 0, "stat_reward": 900 + (_mastery - 300) * 7,
        "class_xp_reward": _cxp, "soul_reward": _sxp,
        "drops": {"soul_shard": 0.35 + (_mastery - 300) / 600.0},
        "quest_target": None, "endgame_region_mastery": _mastery,
    }
    MOB_TEMPLATES[_mid] = _tmpl
    try:
        _configure_dynamic_corpse_material(_tmpl)
    except Exception:
        pass

_v0923_boss_specs = {
    "ashen_sovereign": ("Suweren Popielnej Cytadeli", 260000, 300, "magic", 72000, 11500, 320, "ashen_citadel"),
    "tempest_queen": ("Królowa Rozbitej Nawałnicy", 330000, 345, "magic", 83000, 13000, 350, "tempest_sanctum"),
    "void_tide_monarch": ("Monarcha Przypływu Pustki", 420000, 390, "magic", 96000, 15000, 380, "void_throne"),
    "world_crown_avatar": ("Awatar Korony Świata", 560000, 440, "physical", 120000, 17500, 400, "world_crown_summit"),
}
for _mid, (_name, _hp, _dmg, _dtype, _cxp, _sxp, _mastery, _room) in _v0923_boss_specs.items():
    _tmpl = {
        "name": _name, "max_hp": _hp, "damage": _dmg, "damage_type": _dtype,
        "silver": 3500 + (_mastery - 300) * 20, "gold": 20 + (_mastery - 300)//10,
        "mithril": 1 if _mastery >= 380 else 0,
        "stat_reward": 2600 + (_mastery - 300) * 12,
        "class_xp_reward": _cxp, "soul_reward": _sxp,
        "drops": {"soul_shard": 1.0, "soul_elixir": 0.45},
        "quest_target": None, "world_boss": True,
        "endgame_region_mastery": _mastery,
        "boss_mechanic": "endgame_region_boss",
        "boss_mechanic_text": "Boss endgame ma podwyższone obrażenia i wytrzymałość odpowiednie do regionu.",
    }
    MOB_TEMPLATES[_mid] = _tmpl
    try:
        _configure_dynamic_corpse_material(_tmpl)
    except Exception:
        pass
    MOB_SPAWNS.append((_room, _mid))

_v0923_region_spawns = {
    "ashen_frontier": ("ash_revenant","cinder_wraith","ash_revenant"),
    "ashen_waste": ("ash_revenant","charred_colossus","cinder_wraith"),
    "cinder_ravine": ("charred_colossus","ash_seer","cinder_wraith"),
    "ash_bonefield": ("ash_revenant","charred_colossus","ash_seer"),
    "ember_ruins": ("cinder_wraith","ash_seer","charred_colossus"),
    "skybreak_gate": ("storm_seraph","skybreaker","thunder_harrier"),
    "storm_bridge": ("thunder_harrier","storm_seraph","skybreaker"),
    "thunder_shelf": ("cloud_titan","thunder_harrier","storm_seraph"),
    "cloud_scar": ("skybreaker","cloud_titan","thunder_harrier"),
    "shattered_aerie": ("storm_seraph","cloud_titan","skybreaker"),
    "void_coast_gate": ("void_mariner","black_tide_oracle","starless_knight"),
    "void_shore": ("void_mariner","abyssal_manta","black_tide_oracle"),
    "black_tide_flats": ("abyssal_manta","starless_knight","void_mariner"),
    "drowned_observatory": ("black_tide_oracle","abyssal_manta","starless_knight"),
    "starless_chapel": ("starless_knight","black_tide_oracle","void_mariner"),
    "world_crown_gate": ("crown_sentinel","timeless_magister","absolute_guardian"),
    "eternal_causeway": ("crown_sentinel","worldcrown_echo","timeless_magister"),
    "absolute_gallery": ("absolute_guardian","timeless_magister","worldcrown_echo"),
    "crown_stair": ("crown_sentinel","absolute_guardian","worldcrown_echo"),
    "timeless_balcony": ("timeless_magister","worldcrown_echo","crown_sentinel"),
}
for _room, _mobs in _v0923_region_spawns.items():
    for _mob in _mobs:
        MOB_SPAWNS.append((_room, _mob))

GUIDE_DESTINATION_ALIASES.update({
    "popielne pustkowia": "ashen_frontier", "popielna granica": "ashen_frontier",
    "rozbite niebo": "skybreak_gate", "brama rozbitego nieba": "skybreak_gate",
    "wybrzeze pustki": "void_coast_gate", "wybrzeże pustki": "void_coast_gate",
    "korona swiata": "world_crown_gate", "korona świata": "world_crown_gate",
})

# Polecenia rankingów. Jedna komenda udostępnia pięć trwałych rankingów.
COMMAND_ALIASES.update({
    "rankingi": "leaderboards", "ranking": "leaderboards",
    "leaderboard": "leaderboards", "leaderboards": "leaderboards",
    "tablica rekordow": "leaderboards", "tablica rekordów": "leaderboards",
})
HELP_TOPICS["leaderboards"] = [
    "rankingi / leaderboard - skrócone Top 5 wszystkich kategorii.",
    "rankingi krypta - najwyższe odwiedzone piętro Krypty.",
    "rankingi wieza - najwyższe odwiedzone piętro Wieży Astralnej.",
    "rankingi boss - najszybsze zarejestrowane pokonania bossów.",
    "rankingi legendy - liczba odkrytych legendarnych elementów EQ.",
    "rankingi sety - liczba w pełni skompletowanych zestawów EQ.",
]
HELP_TOPIC_ALIASES.update({
    "rankingi": "leaderboards", "ranking": "leaderboards",
    "leaderboard": "leaderboards", "leaderboards": "leaderboards",
})



# ============================================================
# v0.9.30 - LARGE EXPLORATION REGIONS
# ============================================================
def build_v0930_large_exploration_regions():
    """Rozbudowuje małe expowiska do dużych, zapętlonych regionów.

    Bez nowego eventu eksploracyjnego: zmiana dotyczy wyłącznie świata.
    Nowe sektory tworzą siatki z pętlami i bocznymi drogami zamiast prostych
    krzyży. Istniejące wejścia, bossowie i połączenia między regionami zostają.
    """
    reverse = {"north":"south","south":"north","east":"west","west":"east","up":"down","down":"up"}
    targets = {
        "Obozowiska Bandytów": 24,
        "Jaskinie Goblinów": 24,
        "Ruiny Strażnicy": 24,
        "Stary Cmentarz": 24,
        "Ruiny Kultystów": 24,
        "Legowisko Bestii": 24,
        "Nekropolia": 24,
        "Kanały Pod Miastem": 24,
        "Lodowe Jaskinie": 24,
        "Las Szeptów": 24,
        "Pustynia": 28,
        "Bagna": 28,
        "Góry": 28,
        "Popielne Pustkowia": 30,
        "Rozbite Niebo": 30,
        "Wybrzeże Pustki": 30,
        "Korona Świata": 30,
    }
    anchors = {
        "Obozowiska Bandytów":"bandit_outer_ring",
        "Jaskinie Goblinów":"goblin_scrap_tunnels",
        "Ruiny Strażnicy":"ruin_courtyard",
        "Stary Cmentarz":"cemetery_ossuary_path",
        "Ruiny Kultystów":"cult_ruins_courtyard",
        "Legowisko Bestii":"beast_lair_tracks",
        "Nekropolia":"necropolis_procession",
        "Kanały Pod Miastem":"sewer_runoff",
        "Lodowe Jaskinie":"ice_cave_blue_tunnel",
        "Las Szeptów":"forest_old_oaks",
        "Pustynia":"desert_dunes",
        "Bagna":"reed_mire",
        "Góry":"mountain_lower_slopes",
        "Popielne Pustkowia":"ashen_waste",
        "Rozbite Niebo":"storm_bridge",
        "Wybrzeże Pustki":"void_shore",
        "Korona Świata":"eternal_causeway",
    }
    words = {
        "Obozowiska Bandytów": (("Ścieżka","Namioty","Barykada","Plac","Zaułek"),("Czerwonych Chust","Zrabowanych Wozów","Nocnej Straży","Starych Palisad","Przemytników","Wilczych Zębów"),"Palisady, wozy i boczne przejścia rozbijają obóz na wiele połączonych sektorów."),
        "Jaskinie Goblinów": (("Tunel","Grota","Szyb","Nora","Galeria"),("Zielonego Dymu","Kościanych Totemów","Złomiarzy","Krzywych Kilofów","Grzybowych Lamp","Piszczałek"),"Kręte tunele przecinają się i wracają do wcześniejszych grot, tworząc rozległą sieć."),
        "Ruiny Strażnicy": (("Korytarz","Dziedziniec","Wieża","Komnata","Galeria"),("Pękniętych Tarcz","Starej Warty","Runicznych Murów","Zawalonych Łuków","Zapomnianego Garnizonu","Kamiennych Schodów"),"Pozostałości murów, krużganków i podziemi łączą się wieloma drogami."),
        "Stary Cmentarz": (("Aleja","Kwatera","Mauzoleum","Krypta","Ogród"),("Zapomnianych Imion","Krzywych Krzyży","Czarnych Róż","Otwartych Grobów","Płaczących Figur","Zgaszonych Lamp"),"Nagrobki, mauzolea i boczne alejki tworzą rozległy cmentarz z licznymi pętlami."),
        "Ruiny Kultystów": (("Krużganek","Komnata","Dziedziniec","Galeria","Przejście"),("Czarnej Pieczęci","Zgaszonych Świec","Pękniętych Run","Szeptów Otchłani","Spalonego Pergaminu","Pustych Masek"),"Ruiny świątyni ciągną się przez dziedzińce, biblioteki i boczne przejścia rytualne."),
        "Legowisko Bestii": (("Grota","Korytarz","Gniazdo","Szczelina","Łowisko"),("Starych Kości","Poszarpanych Skór","Żelaznych Korzeni","Ciepłego Oddechu","Śladów Pazurów","Głębokiego Ryku"),"Naturalne jaskinie rozchodzą się na kilka poziomów i łączą z powrotem bocznymi szczelinami."),
        "Nekropolia": (("Aleja","Katakumby","Mauzoleum","Plac","Grobowiec"),("Kamiennych Królów","Bezimiennych","Czarnych Chorągwi","Milczących Straży","Kościanych Bram","Wiecznego Czuwania"),"Monumentalna nekropolia ma wiele ulic grobowych, placów i zejść do katakumb."),
        "Kanały Pod Miastem": (("Kanał","Tunel","Komora","Przepust","Cysterna"),("Czarnej Wody","Starych Krat","Zgniłych Desek","Przemytników","Zielonego Szlamu","Głębokiego Odpływu"),"Kanały tworzą prawdziwy labirynt przepustów, cystern i bocznych odpływów."),
        "Lodowe Jaskinie": (("Tunel","Grota","Szczelina","Komora","Galeria"),("Błękitnego Lodu","Szronowych Kolumn","Zamarzniętych Ech","Kryształowego Pyłu","Pękniętego Lodowca","Wiecznej Zimy"),"Lodowe korytarze rozgałęziają się między szczelinami i zamarzniętymi komorami."),
        "Las Szeptów": (("Ścieżka","Polana","Zagajnik","Parów","Krąg"),("Starych Dębów","Cichego Mchu","Wilczych Tropów","Srebrnych Brzóz","Księżycowych Paproci","Powalonych Pni"),"Leśne trakty przecinają się, zawracają i prowadzą przez liczne polany oraz parowy."),
        "Pustynia": (("Wydmy","Kanion","Równina","Ruiny","Szlak"),("Siedmiu Wiatrów","Białych Kości","Czerwonego Piasku","Zaginionych Karawan","Szklanego Pyłu","Palącego Słońca"),"Wydmy i kaniony tworzą szeroki teren z wieloma szlakami między ruinami i oazami."),
        "Bagna": (("Mokradło","Groble","Rozlewisko","Torfowisko","Zarośla"),("Czarnej Wody","Gnijących Korzeni","Trujących Oparów","Zatopionych Drzew","Bagiennych Świateł","Wężowych Gniazd"),"Groble, wyspy i rozlewiska układają się w duży, zapętlony teren bagienny."),
        "Góry": (("Grań","Przełęcz","Półka","Wąwóz","Szlak"),("Białych Szczytów","Wiecznego Wiatru","Kamiennych Kozic","Starych Kopalń","Burzowych Chmur","Zamarzniętych Turni"),"Górskie trakty rozchodzą się po graniach, półkach i bocznych przełęczach."),
        "Popielne Pustkowia": (("Szlak","Pole","Wąwóz","Ruiny","Krawędź"),("Czarnego Popiołu","Dogasłych Palenisk","Zwęglonych Kości","Czerwonego Żaru","Martwych Pieców","Popielnej Burzy"),"Pustkowia rozciągają się daleko między polami popiołu, ruinami i pęknięciami ziemi."),
        "Rozbite Niebo": (("Most","Półka","Taras","Grań","Platforma"),("Piorunów","Rozdartych Chmur","Nawałnicy","Gromowych Wież","Podniebnych Ruin","Białego Wiatru"),"Podniebne mosty i półki tworzą wielodrogowy region wysoko nad chmurami."),
        "Wybrzeże Pustki": (("Brzeg","Molo","Ruiny","Zatoka","Taras"),("Czarnego Przypływu","Bezgwiezdnej Wody","Zatopionych Dzwonów","Pustych Latarni","Martwych Żagli","Otchłani"),"Czarny brzeg ciągnie się przez zatoki, mola i zatopione ruiny połączone wieloma ścieżkami."),
        "Korona Świata": (("Grobla","Galeria","Taras","Schody","Dziedziniec"),("Absolutu","Wiecznego Światła","Ponadczasowych Bram","Milczących Gwiazd","Białego Kamienia","Ostatniej Korony"),"Monumentalny szczyt tworzy rozległy kompleks tarasów, galerii i wielkich schodów."),
    }
    detail = (
        "Boczna droga wraca do dalszej części regionu, więc nie jest to ślepy krzyż.",
        "Kilka przejść pozwala obejść główny trakt i odkrywać teren różnymi trasami.",
        "Ścieżki łączą ten sektor z sąsiednimi częściami regionu w dużą pętlę.",
        "To jeden z wielu równoległych traktów; mapa ma liczne alternatywne połączenia.",
    )

    # Zbierz zwykłe moby obecnych regionów zanim dołożymy nowe spawny.
    room_zone = {rid: room.get("zone") for rid, room in ROOMS.items()}
    zone_pools = {}
    for rid, mid in list(MOB_SPAWNS):
        zone = room_zone.get(rid)
        if zone not in targets:
            continue
        tmpl = MOB_TEMPLATES.get(mid, {})
        if tmpl.get("world_boss") or tmpl.get("boss") or tmpl.get("boss_mechanic"):
            continue
        zone_pools.setdefault(zone, [])
        if mid not in zone_pools[zone]:
            zone_pools[zone].append(mid)

    # Cmentarz dostaje gęstszy zestaw nieumarłych, aby 0/25 nie wymagało stania na respawnie.
    cemetery_pool = [
        mid for mid in (
            "cemetery_restless_dead", "cemetery_bone_collector",
            "cemetery_bell_wraith", "cemetery_steel_skeleton",
            "cemetery_grave_hound", "cemetery_crypt_reaper",
            "cemetery_mourning_knight",
        ) if mid in MOB_TEMPLATES
    ]
    if cemetery_pool:
        zone_pools["Stary Cmentarz"] = cemetery_pool

    for zone, target in targets.items():
        existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
        need = max(0, int(target) - len(existing))
        if need <= 0:
            continue
        anchor = anchors[zone]
        prefixes, suffixes, zone_desc = words[zone]
        safe = _collection_slug(zone)
        new_ids = [f"v0930_{safe}_{i+1:02d}" for i in range(need)]
        # v0.33.6: nazwa każdego pokoju ma być globalnie jednoznaczna dla NVDA.
        # Wybieramy pełne kombinacje prefix x suffix i omijamy nazwy istniejące
        # już wcześniej w świecie; żadnych dopisków 2/3/4.
        used_room_names = {
            str(existing_room.get("name", "")).casefold().strip()
            for existing_room in ROOMS.values()
            if str(existing_room.get("name", "")).strip()
        }
        name_combinations = [
            (pfx, sfx)
            for sfx in suffixes
            for pfx in prefixes
        ]
        combo_cursor = 0
        for i, rid in enumerate(new_ids):
            chosen_pair = None
            while combo_cursor < len(name_combinations):
                candidate = name_combinations[combo_cursor]
                combo_cursor += 1
                candidate_name = f"{candidate[0]} {candidate[1]}"
                if candidate_name.casefold().strip() not in used_room_names:
                    chosen_pair = candidate
                    used_room_names.add(candidate_name.casefold().strip())
                    break
            if chosen_pair is None:
                # Teoretyczny bezpiecznik: pula ma 30 kombinacji, a każdy region
                # potrzebuje mniej nowych sektorów niż ten limit.
                chosen_pair = (prefixes[i % len(prefixes)], suffixes[(i // len(prefixes)) % len(suffixes)])
            prefix, suffix = chosen_pair
            room_data = {
                "zone": zone,
                "name": f"{prefix} {suffix}",
                "desc": f"{zone_desc} {detail[i % len(detail)]}",
                "exits": {},
            }
            endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
            if endgame_recommended is not None:
                room_data["recommended_mastery"] = int(endgame_recommended)
            ROOMS[rid] = room_data

        # Dołącz nową część bez nadpisywania istniejących wyjść.
        anchor_exits = ROOMS[anchor].setdefault("exits", {})
        attach = next((d for d in ("south","east","west","north","down","up") if d not in anchor_exits), None)
        if attach is None:
            attach = "down"
        anchor_exits[attach] = new_ids[0]
        ROOMS[new_ids[0]]["exits"][reverse[attach]] = anchor

        # Łącznik + nieregularna siatka 5 kolumn. Pełne poziome rzędy i kilka
        # pionowych łączników dają pętle i alternatywne trasy, ale nie prosty krzyż.
        if len(new_ids) > 1:
            back_from_connector = reverse[attach]
            forward = "south" if back_from_connector != "south" else "east"
            ROOMS[new_ids[0]]["exits"][forward] = new_ids[1]
            ROOMS[new_ids[1]]["exits"][reverse[forward]] = new_ids[0]

            grid = new_ids[1:]
            width = 5
            for idx, rid in enumerate(grid):
                row, col = divmod(idx, width)
                # poziome przejścia
                if col + 1 < width and idx + 1 < len(grid):
                    other = grid[idx + 1]
                    ROOMS[rid]["exits"]["east"] = other
                    ROOMS[other]["exits"]["west"] = rid
                # pionowe przejścia: kolumny skrajne zawsze, środkowe naprzemiennie
                down_idx = idx + width
                if down_idx < len(grid) and (col in (0, width-1) or (row + col) % 2 == 0):
                    other = grid[down_idx]
                    ROOMS[rid]["exits"]["south"] = other
                    ROOMS[other]["exits"]["north"] = rid

        # Zaludnij nowe sektory istniejącymi zwykłymi mobami regionu.
        pool = zone_pools.get(zone, [])
        if pool:
            for i, rid in enumerate(new_ids):
                MOB_SPAWNS.append((rid, pool[i % len(pool)]))
                if i % 4 == 0 and len(pool) > 1:
                    MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))

    # Achievement ma oznaczać faktyczne odkrycie całego aktualnego świata.
    tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
    if tiers:
        fixed = [(req, rank) for req, rank in tiers if rank != "Platinum"]
        fixed.append((len(ROOMS), "Platinum"))
        ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(fixed)

build_v0930_large_exploration_regions()


# ============================================================
# v0.10.0 - MASSIVE WORLD & DUNGEONS
# ============================================================
V0100_MAJOR_FLOOR_ROOMS = 15
V0100_PROF_FLOOR_ROOMS = 10
V0100_RESOURCE_ROOM_SETS = (
    "MINING_ROOMS", "FISHING_ROOMS", "SEA_FISHING_ROOMS",
    "OCEAN_FISHING_ROOMS", "MARINE_FISHING_ROOMS",
    "WOODCUTTING_ROOMS", "HERBALISM_ROOMS", "MEADOW_HERBALISM_ROOMS",
)

V0100_INSTANCE_LABELS = {
    "crypt": (
        "Galeria Sarkofagów", "Korytarz Kości", "Zawalona Katakumba",
        "Komnata Pieczęci", "Aleja Grobowców", "Sala Zgaszonych Świec",
        "Krypta Bezimiennych", "Kamienny Labirynt", "Przejście Strażników",
        "Komnata Popiołu", "Korytarz Otchłani", "Sala Starych Run",
        "Galeria Umarłych", "Schody Głębi",
    ),
    "mythic_crypt": (
        "Mityczna Galeria Kości", "Korytarz Pękniętej Duszy", "Komnata Otchłani",
        "Sala Czarnego Płomienia", "Katakumba Pustki", "Galeria Krwawych Run",
        "Krypta Bez Końca", "Korytarz Widm", "Komnata Zatraconych",
        "Przejście Nekromantów", "Sala Echa", "Grobowiec Pustki",
        "Labirynt Dusz", "Brama Głębszej Otchłani",
    ),
    "astral": (
        "Gwiezdna Galeria", "Taras Konstelacji", "Korytarz Mgławic",
        "Sala Gwiezdnego Pyłu", "Most Astralny", "Komnata Orbit",
        "Galeria Firmamentu", "Taras Srebrnych Gwiazd", "Sala Światła",
        "Korytarz Meteorytów", "Komnata Sfer", "Most Niebios",
        "Galeria Konstelacji", "Schody Wyższego Kręgu",
    ),
    "mythic_astral": (
        "Mityczna Galeria Gwiazd", "Taras Pustych Konstelacji", "Korytarz Zaćmienia",
        "Sala Rozdartego Nieba", "Most Wieczności", "Komnata Ciemnych Orbit",
        "Galeria Pustki", "Taras Gwiezdnej Burzy", "Sala Załamanego Światła",
        "Korytarz Serafinów", "Komnata Sfer", "Most Firmamentu",
        "Labirynt Gwiazd", "Brama Wyższej Sfery",
    ),
    "giant": (
        "Galeria Kolosów", "Kamienna Hala", "Korytarz Cyklopów",
        "Sala Głazów", "Dziedziniec Tytanów", "Most Gigantów",
        "Zbrojownia Olbrzymów", "Komnata Runicznego Kamienia", "Hala Wojowników",
        "Korytarz Burzy", "Sala Żelaznych Bram", "Taras Twierdzy",
        "Galeria Królewska", "Schody Wyższego Bastionu",
    ),
    "profession": (
        "Boczna Komora", "Rozgałęziony Korytarz", "Głęboki Sektor",
        "Komora Zasobów", "Stare Przejście", "Ukryta Odnoga",
        "Szeroka Galeria", "Mistrzowski Sektor", "Przejście Głębiej",
    ),
    "mine": (
        "Galeria Skał", "Komora Żył", "Tunel Głębinowy",
        "Sala Kryształów", "Zawalony Chodnik", "Szyb Boczny",
        "Komora Rudy", "Stary Przekop", "Schody Głębi",
    ),
}


def v0100_instance_spec(room_id):
    """Zwraca opis kanonicznego pokoju piętra, bez jego nowych odnóg."""
    rid = str(room_id or "")
    floor = crypt_floor_number(rid)
    if floor is not None and rid == crypt_floor_id(floor):
        return {
            "kind": "crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "crypt_boss",
        }
    floor = mythic_crypt_floor_number(rid)
    if floor is not None and rid == mythic_crypt_floor_id(floor):
        return {
            "kind": "mythic_crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_crypt_boss",
        }
    floor = astral_floor_number(rid)
    if floor is not None and rid == astral_floor_id(floor):
        return {
            "kind": "astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "astral_boss",
        }
    floor = mythic_astral_floor_number(rid)
    if floor is not None and rid == mythic_astral_floor_id(floor):
        return {
            "kind": "mythic_astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_astral_boss",
        }
    floor = giant_fortress_floor_number(rid)
    if floor is not None and rid == giant_fortress_floor_id(floor):
        return {
            "kind": "giant", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "giant_fortress_boss",
        }
    floor = mine_floor_number(rid)
    if floor is not None and rid == mine_floor_id(floor):
        return {
            "kind": "mine", "floor": floor, "next_dir": "down",
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    dungeon, floor = profession_dungeon_floor(rid)
    if dungeon is not None and rid == profession_dungeon_room_id(dungeon, floor):
        next_dirs = {
            "crystal_mine": "down", "sunken_grotto": "down",
            "ancient_forest": "south", "alchemy_garden": "east",
        }
        return {
            "kind": "profession", "profession_dungeon": dungeon,
            "floor": floor, "next_dir": next_dirs[dungeon],
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    return None


def v0100_subroom_id(canonical_room, index):
    return f"{canonical_room}_r{int(index):02d}"


def v0100_copy_resource_membership(canonical_room, subrooms):
    for set_name in V0100_RESOURCE_ROOM_SETS:
        room_set = globals().get(set_name)
        if isinstance(room_set, set) and canonical_room in room_set:
            room_set.update(subrooms)


def v0100_connect_pair(a, direction, b, reverse_direction):
    ROOMS[a].setdefault("exits", {})[direction] = b
    ROOMS[b].setdefault("exits", {})[reverse_direction] = a


def v0100_expand_instance_floor(canonical_room, spawn_pairs=None, runtime=False):
    """Zmienia jedno liniowe piętro w dużą, zapętloną mapę.

    Kanoniczny pokój pozostaje lądowaniem/checkpointem. Wyjście na kolejne
    piętro zostaje przeniesione do ostatniej komnaty. Na piętrze bossa boss
    również trafia do tej komnaty, dzięki czemu naprawdę pilnuje dalszej drogi.
    """
    canonical_room = str(canonical_room or "")
    spec = v0100_instance_spec(canonical_room)
    if not spec or canonical_room not in ROOMS:
        return list(spawn_pairs or ())
    first_sub = v0100_subroom_id(canonical_room, 1)
    if first_sub in ROOMS:
        return list(spawn_pairs or ())

    base = ROOMS[canonical_room]
    exits = base.setdefault("exits", {})
    next_dir = spec["next_dir"]
    vertical_reverse = {"down":"up", "up":"down", "south":"north", "north":"south", "east":"west", "west":"east"}
    previous_dir = vertical_reverse[next_dir]
    # Jeżeli poprzednie piętro jest już rozbudowane, powrót prowadzi do jego
    # prawdziwej komnaty schodów, a nie teleportuje na początek piętra.
    previous_target = exits.get(previous_dir)
    previous_spec = v0100_instance_spec(previous_target) if previous_target else None
    if previous_spec:
        previous_final = v0100_subroom_id(previous_target, int(previous_spec["rooms"]) - 1)
        if previous_final in ROOMS:
            exits[previous_dir] = previous_final
    next_target = exits.pop(next_dir, None)
    total_rooms = max(3, int(spec["rooms"]))
    subrooms = [v0100_subroom_id(canonical_room, i) for i in range(1, total_rooms)]
    maze_rooms = subrooms[:-1]
    final_room = subrooms[-1]
    labels = V0100_INSTANCE_LABELS[spec["kind"]]
    floor = int(spec["floor"])
    zone = base.get("zone", "Loch")
    generated_profile_v025 = v0250_instance_floor_profile(spec["kind"], floor)

    for index, rid in enumerate(subrooms, 1):
        label_seed = int(hashlib.sha256(f"{spec['kind']}:{floor}".encode("utf-8")).hexdigest()[:8], 16)
        label = labels[(label_seed + index - 1) % len(labels)]
        if rid == final_room:
            if spec.get("boss_flag") and is_crypt_boss_floor(floor) and spec["kind"] in {"crypt", "mythic_crypt"}:
                label = "Komnata Strażnika Progu"
            elif spec.get("boss_flag") and spec["kind"] in {"astral", "mythic_astral"} and floor % 10 == 0:
                label = "Komnata Strażnika Kręgu"
            elif spec.get("boss_flag") and spec["kind"] == "giant" and floor % 10 == 0:
                label = "Sala Strażnika Bastionu"
        ROOMS[rid] = {
            "zone": zone,
            "name": f"{label} — {floor}",
            "desc": (
                f"Rozległa część poziomu {floor}. Korytarze rozchodzą się w kilka stron, "
                "łączą w pętle i prowadzą przez boczne komnaty. To pełne piętro lochu, "
                "a nie pojedynczy liniowy pokój. "
                f"Generator piętra: {generated_profile_v025['layout']}; "
                f"motyw: {generated_profile_v025['motif']}."
            ),
            "exits": {},
            "v0100_instance_kind": spec["kind"],
            "v0250_generator_profile": generated_profile_v025,
            "v0100_floor": floor,
            "v0100_floor_room": index + 1,
            "procedural_dynamic": True,
        }
        if "recommended_mastery" in base:
            ROOMS[rid]["recommended_mastery"] = base["recommended_mastery"]
        dungeon = spec.get("profession_dungeon")
        if dungeon:
            ROOMS[rid]["profession_dungeon"] = dungeon
            ROOMS[rid]["profession_dungeon_floor"] = floor

    # v0.11.0: układ jest proceduralny, ale deterministyczny dla rodzaju i numeru
    # piętra. Restart serwera nie zmienia mapy w trakcie progresji gracza.
    seed_text = f"{V0250_WORLD_SEED}:soulbound-v0110:{spec['kind']}:{floor}:{spec.get('profession_dungeon','')}"
    floor_seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    floor_rng = random.Random(floor_seed)

    # Wejście na piętro prowadzi do labiryntu bokiem, a nie od razu dalej.
    free_attach = [d for d in ("east", "south", "west", "north") if d not in exits]
    attach_dir = floor_rng.choice(free_attach) if free_attach else "east"
    reverse = {"east": "west", "west": "east", "north": "south", "south": "north"}
    v0100_connect_pair(canonical_room, attach_dir, maze_rooms[0], reverse[attach_dir])

    # Różne piętra dostają siatkę o szerokości 3 albo 4. Każdy rząd pozostaje
    # spójny, a między kolejnymi rzędami zawsze istnieje co najmniej jedno
    # przejście; dodatkowe przejścia tworzą losowane, lecz stałe pętle.
    width = 3 + floor_rng.randrange(2)
    for idx, rid in enumerate(maze_rooms):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(maze_rooms):
            other = maze_rooms[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")

    rows = (len(maze_rooms) + width - 1) // width
    for row in range(rows - 1):
        current = list(range(row * width, min((row + 1) * width, len(maze_rooms))))
        below = list(range((row + 1) * width, min((row + 2) * width, len(maze_rooms))))
        possible = [c for c in range(min(len(current), len(below)))]
        if not possible:
            continue
        chosen = {floor_rng.choice(possible)}
        # Każde piętro ma co najmniej jedną prawdziwą pętlę, a część rzędów
        # dostaje dodatkowe alternatywne przejście.
        if len(possible) > 1 and (row == 0 or floor_rng.random() < 0.70):
            extras = [c for c in possible if c not in chosen]
            if extras:
                chosen.add(floor_rng.choice(extras))
        for c in sorted(chosen):
            a = maze_rooms[current[c]]
            b = maze_rooms[below[c]]
            if "south" not in ROOMS[a]["exits"] and "north" not in ROOMS[b]["exits"]:
                v0100_connect_pair(a, "south", b, "north")

    # Ostatnia komnata jest za labiryntem i zawiera drogę na kolejne piętro.
    tail = maze_rooms[-1]
    if "east" in ROOMS[tail]["exits"]:
        # Dla krótszej siatki użyj pierwszej wolnej pary.
        for d, rev in (("south", "north"), ("north", "south"), ("west", "east")):
            if d not in ROOMS[tail]["exits"] and rev not in ROOMS[final_room]["exits"]:
                v0100_connect_pair(tail, d, final_room, rev)
                break
    else:
        v0100_connect_pair(tail, "east", final_room, "west")
    if next_target:
        ROOMS[final_room]["exits"][next_dir] = next_target
        # Gdy następne piętro istnieje już statycznie, jego droga powrotna
        # wskazuje na tę samą klatkę schodową. Dynamiczne piętro naprawi ten
        # link w chwili utworzenia.
        next_spec = v0100_instance_spec(next_target)
        if next_spec and next_target in ROOMS:
            ROOMS[next_target].setdefault("exits", {})[vertical_reverse[next_dir]] = final_room

    v0100_copy_resource_membership(canonical_room, subrooms)

    pairs = list(spawn_pairs or ())
    if not pairs and not runtime:
        pairs = [(r, t) for r, t in MOB_SPAWNS if r == canonical_room]
    boss_flag = spec.get("boss_flag")
    boss_ids = []
    regular_ids = []
    for r, tid in pairs:
        if r != canonical_room:
            continue
        template = MOB_TEMPLATES.get(tid, {})
        if boss_flag and template.get(boss_flag):
            boss_ids.append(tid)
        else:
            regular_ids.append(tid)

    # Przy statycznych piętrach przenieś bossów z lądowania do sali wyjściowej.
    if not runtime and boss_ids:
        moved = set(boss_ids)
        MOB_SPAWNS[:] = [
            (r, t) for r, t in MOB_SPAWNS
            if not (r == canonical_room and t in moved)
        ]
        for tid in boss_ids:
            MOB_SPAWNS.append((final_room, tid))
    elif runtime and boss_ids:
        pairs = [
            (final_room if (r == canonical_room and t in set(boss_ids)) else r, t)
            for r, t in pairs
        ]

    # Każda boczna komnata dostaje przeciwnika; część komnat ma dwa różne typy.
    extra_pairs = []
    if regular_ids:
        for index, rid in enumerate(subrooms):
            if rid == final_room and boss_ids:
                continue
            extra_pairs.append((rid, regular_ids[index % len(regular_ids)]))
            if index % 3 == 1 and len(regular_ids) > 1:
                extra_pairs.append((rid, regular_ids[(index + 1) % len(regular_ids)]))
    if runtime:
        pairs.extend(extra_pairs)
        return pairs
    MOB_SPAWNS.extend(extra_pairs)
    return pairs


def build_v0100_massive_instance_floors():
    canonical = []
    canonical.extend(crypt_floor_id(f) for f in range(1, CRYPT_PREGENERATED_MAX_FLOOR + 1))
    canonical.extend(mythic_crypt_floor_id(f) for f in range(1, MYTHIC_MAX_FLOOR + 1))
    canonical.extend(astral_floor_id(f) for f in range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1))
    canonical.extend(mythic_astral_floor_id(f) for f in range(1, MYTHIC_MAX_FLOOR + 1))
    canonical.extend(giant_fortress_floor_id(f) for f in range(1, GIANT_FORTRESS_MAX_FLOOR + 1))
    for dungeon in PROF_DUNGEON_PREFIXES:
        canonical.extend(profession_dungeon_room_id(dungeon, f) for f in range(1, PROF_DUNGEON_MAX_FLOOR + 1))
    for rid in canonical:
        if rid in ROOMS:
            v0100_expand_instance_floor(rid, runtime=False)


V0100_SURFACE_TARGETS = {
    "Wybrzeże": 30,
    "Łąki": 30,
    "Podziemia": 30,
    "Łąki Zielarskie": 30,
    "Jaskinia Trolli": 36,
    "Obozowiska Bandytów": 30,
    "Jaskinie Goblinów": 30,
    "Ruiny Strażnicy": 30,
    "Stary Cmentarz": 30,
    "Ruiny Kultystów": 30,
    "Legowisko Bestii": 30,
    "Nekropolia": 30,
    "Kanały Pod Miastem": 30,
    "Lodowe Jaskinie": 30,
    "Las Szeptów": 30,
    "Dzicz": 36,
    "Pustynia": 36,
    "Bagna": 36,
    "Góry": 36,
    "Popielne Pustkowia": 40,
    "Rozbite Niebo": 40,
    "Wybrzeże Pustki": 40,
    "Korona Świata": 40,
}

V0100_SURFACE_WORDS = {
    "Wybrzeże": ("Brzeg", "Klif", "Zatoka", "Molo", "Wydma"),
    "Łąki": ("Łąka", "Polana", "Pastwisko", "Wzgórze", "Zagajnik"),
    "Podziemia": ("Korytarz", "Komnata", "Galeria", "Katakumba", "Przejście"),
    "Łąki Zielarskie": ("Łąka", "Polana", "Ogród", "Zagajnik", "Dolina"),
    "Jaskinia Trolli": ("Grota", "Tunel", "Sala", "Rozpadlina", "Korytarz"),
    "Dzicz": ("Trakt", "Parów", "Polana", "Urwisko", "Ostęp"),
    "Pustynia": ("Wydmy", "Kanion", "Równina", "Ruiny", "Szlak"),
    "Bagna": ("Mokradło", "Groble", "Rozlewisko", "Torfowisko", "Zarośla"),
    "Góry": ("Grań", "Przełęcz", "Półka", "Wąwóz", "Szlak"),
}


def v0100_zone_regular_pool(zone):
    result = []
    for rid, tid in MOB_SPAWNS:
        if ROOMS.get(rid, {}).get("zone") != zone:
            continue
        template = MOB_TEMPLATES.get(tid, {})
        if (
            template.get("world_boss") or template.get("boss")
            or template.get("boss_mechanic") or template.get("crypt_boss")
            or template.get("astral_boss") or template.get("mythic_crypt_boss")
            or template.get("mythic_astral_boss") or template.get("giant_fortress_boss")
        ):
            continue
        if tid not in result:
            result.append(tid)
    return result


def v0100_find_surface_anchor(zone):
    candidates = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
    # Najpierw wybierz pomieszczenie z wolnym kierunkiem poziomym i bez bossa.
    boss_rooms = {
        rid for rid, tid in MOB_SPAWNS
        if ROOMS.get(rid, {}).get("zone") == zone
        and (
            MOB_TEMPLATES.get(tid, {}).get("world_boss")
            or MOB_TEMPLATES.get(tid, {}).get("boss_mechanic")
        )
    }
    candidates.sort(key=lambda rid: (rid in boss_rooms, len(ROOMS[rid].get("exits", {})), rid))
    for rid in candidates:
        exits = ROOMS[rid].get("exits", {})
        if any(d not in exits for d in ("east", "south", "west", "north")):
            return rid
    return candidates[0] if candidates else None


def v0100_expand_surface_zone(zone, target):
    existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
    need = max(0, int(target) - len(existing))
    if not need:
        return
    anchor = v0100_find_surface_anchor(zone)
    if not anchor:
        return
    pool = v0100_zone_regular_pool(zone)
    safe = _collection_slug(zone)
    new_ids = [f"v0100_{safe}_{i+1:03d}" for i in range(need)]
    words = V0100_SURFACE_WORDS.get(zone, ("Szlak", "Sektor", "Przejście", "Odnoga", "Rejon"))
    for i, rid in enumerate(new_ids):
        word = words[i % len(words)]
        ROOMS[rid] = {
            "zone": zone,
            "name": f"{word} {zone} {i+1}",
            "desc": (
                f"Rozległa część regionu {zone}. Teren rozchodzi się na boczne drogi, "
                "pętle i alternatywne przejścia, dzięki czemu obszar nie jest małym expowiskiem."
            ),
            "exits": {},
            "procedural_surface_v0100": True,
        }
        endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
        if endgame_recommended is not None:
            ROOMS[rid]["recommended_mastery"] = int(endgame_recommended)

    reverse = {"east":"west", "west":"east", "north":"south", "south":"north"}
    anchor_exits = ROOMS[anchor].setdefault("exits", {})
    attach = next((d for d in ("east", "south", "west", "north") if d not in anchor_exits), None)
    if attach is None:
        return
    v0100_connect_pair(anchor, attach, new_ids[0], reverse[attach])

    width = 5
    for idx, rid in enumerate(new_ids):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(new_ids):
            other = new_ids[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")
        down_idx = idx + width
        if down_idx < len(new_ids) and (col in (0, width - 1) or (row + col) % 2 == 0):
            other = new_ids[down_idx]
            if "south" not in ROOMS[rid]["exits"] and "north" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "south", other, "north")

    # Skopiuj charakter profesyjny regionu, jeśli stara część już go miała.
    for set_name in V0100_RESOURCE_ROOM_SETS:
        room_set = globals().get(set_name)
        if isinstance(room_set, set) and any(r in room_set for r in existing):
            room_set.update(new_ids)

    if pool:
        for i, rid in enumerate(new_ids):
            MOB_SPAWNS.append((rid, pool[i % len(pool)]))
            if i % 3 == 0 and len(pool) > 1:
                MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))


def build_v0100_massive_surface_world():
    for zone, target in V0100_SURFACE_TARGETS.items():
        v0100_expand_surface_zone(zone, target)


# v0.11.0: piętrowe instancje nie są już rozwijane przy starcie serwera.
# Ich pełne mapy powstają dopiero przy pierwszym wejściu gracza.
build_v0100_massive_surface_world()

# ============================================================
# v0.11.0 - FULL LAZY DYNAMIC DUNGEONS
# ============================================================
# Od tej wersji wszystkie piętrowe instancje są tworzone dopiero przy wejściu.
# Zachowujemy istniejące template'y mobów/EQ dla kompatybilności zapisów i
# questów, ale usuwamy tysiące gotowych pokojów oraz ich statyczne spawny.
# Dzięki temu piętro 1 działa dokładnie tak samo proceduralnie jak piętro 401+.

def v0110_dynamic_instance_kind(room_id):
    rid = str(room_id or "")
    if crypt_floor_number(rid) is not None:
        return "crypt"
    if mythic_crypt_floor_number(rid) is not None:
        return "mythic_crypt"
    if astral_floor_number(rid) is not None:
        return "astral"
    if mythic_astral_floor_number(rid) is not None:
        return "mythic_astral"
    if giant_fortress_floor_number(rid) is not None:
        return "giant"
    if mine_floor_number(rid) is not None:
        return "mine"
    dungeon, floor = profession_dungeon_floor(rid)
    if dungeon is not None and floor is not None:
        return "profession"
    return None


def v0110_is_dynamic_instance_room(room_id):
    return v0110_dynamic_instance_kind(room_id) is not None


def v0110_remove_pregenerated_instance_rooms():
    removed = {rid for rid in tuple(ROOMS) if v0110_is_dynamic_instance_room(rid)}
    if not removed:
        return 0

    # Usuń wyłącznie pokoje piętrowych instancji. Bramy, wejścia i huby świata
    # pozostają i nadal wskazują na identyfikator pierwszego dynamicznego piętra.
    for rid in removed:
        ROOMS.pop(rid, None)

    MOB_SPAWNS[:] = [(rid, tid) for rid, tid in MOB_SPAWNS if rid not in removed]

    # Zestawy zasobowe mają zawierać tylko realnie istniejące pokoje.
    # create_infinite_* doda je ponownie, kiedy piętro faktycznie powstanie.
    for set_name in V0100_RESOURCE_ROOM_SETS + ("MINING_DEPTH_ROOMS",):
        room_set = globals().get(set_name)
        if isinstance(room_set, set):
            room_set.difference_update(removed)

    return len(removed)


V0110_REMOVED_PREGENERATED_INSTANCE_ROOMS = v0110_remove_pregenerated_instance_rooms()

# Kotwice wejściowe są stałe, ale ich cele nie muszą istnieć aż do pierwszego kroku.
V0110_DYNAMIC_DUNGEON_ENTRANCES = {
    "crypt_hall": crypt_floor_id(1),
    "mythic_crypt_gate": mythic_crypt_floor_id(1),
    "astral_gate": astral_floor_id(ASTRAL_MIN_FLOOR),
    "mythic_astral_gate": mythic_astral_floor_id(1),
    "giant_fortress_gate": giant_fortress_floor_id(1),
    "crystal_chamber": mine_floor_id(1),
    "profession_crystal_mine": profession_dungeon_room_id("crystal_mine", 1),
    "sea_pier": profession_dungeon_room_id("sunken_grotto", 1),
    "deep_grove": profession_dungeon_room_id("ancient_forest", 1),
    "herbalist_hut": profession_dungeon_room_id("alchemy_garden", 1),
}

# ============================================================
# v0.10.2 - CITY LIFE + OUTSKIRTS + ROAMING MOBS + TOOL BALANCE
# ============================================================

def build_v0102_city_and_outskirts():
    """Rozbudowuje Miasto Dusz i tworzy żywe przedmieścia.

    Miasto pozostaje strefą bezpieczną bez wrogich spawnów. Przedmieścia
    są niskopoziomowym obszarem przejściowym między bramami i Łąkami.
    """
    city_rooms = {
        "artisan_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Rzemieślników",
            "desc":"Kamienna ulica pachnie drewnem, skórą i rozgrzanym metalem. Z obu stron stoją małe warsztaty miejskich fachowców.",
            "exits":{},
        },
        "tailor_workshop": {
            "zone":"Miasto Dusz", "name":"Pracownia Krawiecka",
            "desc":"Stoły są przykryte tkaninami, nićmi i wykrojami płaszczy dla mieszkańców oraz straży.",
            "exits":{},
        },
        "carpenter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Ciesielski",
            "desc":"Belki, deski i gotowe framugi wypełniają pracownię. Cieśla naprawia wozy i miejskie budynki.",
            "exits":{},
        },
        "leatherworker_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Kaletnika",
            "desc":"Na półkach leżą pasy, torby i uprzęże. W powietrzu czuć garbowaną skórę i wosk.",
            "exits":{},
        },
        "mason_yard": {
            "zone":"Miasto Dusz", "name":"Dziedziniec Kamieniarzy",
            "desc":"Kamienne bloki, dłuta i fragmenty nowych murów tworzą głośny plac pracy budowniczych.",
            "exits":{},
        },
        "potter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Garncarski",
            "desc":"Koło garncarskie obraca się obok pieca. Na półkach schną misy, dzbany i naczynia dla karczmy.",
            "exits":{},
        },
        "lantern_alley": {
            "zone":"Miasto Dusz", "name":"Zaułek Latarni",
            "desc":"Wąski zaułek oświetlają rzędy błękitnych lamp. Mieszkańcy skracają tędy drogę do południowej dzielnicy.",
            "exits":{},
        },
        "city_bakery": {
            "zone":"Miasto Dusz", "name":"Piekarnia Pod Złotym Bochenkiem",
            "desc":"Ciepły zapach chleba wypełnia niewielką piekarnię zaopatrującą karczmę i strażników przy bramach.",
            "exits":{},
        },
        "healer_house": {
            "zone":"Miasto Dusz", "name":"Dom Uzdrowicielki",
            "desc":"Cicha izba z łóżkami, bandażami i suszonymi ziołami służy rannym podróżnym oraz mieszkańcom.",
            "exits":{},
        },
        "residential_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Domów",
            "desc":"Szereg niewielkich kamiennych domów otacza spokojną ulicę z ławkami i studzienkami deszczowymi.",
            "exits":{},
        },
        "well_square": {
            "zone":"Miasto Dusz", "name":"Plac Starej Studni",
            "desc":"Mały plac skupia mieszkańców południowej dzielnicy. Pośrodku stoi głęboka, nadal używana studnia.",
            "exits":{},
        },
        "courier_office": {
            "zone":"Miasto Dusz", "name":"Poczta i Biuro Kurierów",
            "desc":"Posłańcy sortują listy, paczki i meldunki przeznaczone dla portu, straży oraz odległych posterunków.",
            "exits":{},
        },
        "dockside_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Portowa",
            "desc":"Szeroka droga biegnie wzdłuż magazynów i nabrzeża. Słychać liny, dzwonki statków i nawoływania tragarzy.",
            "exits":{},
        },
        "harbor_warehouse": {
            "zone":"Miasto Dusz", "name":"Magazyn Portowy",
            "desc":"Skrzynie, beczki i zaplombowane pakunki czekają na odbiór przez kupców oraz rybaków.",
            "exits":{},
        },
        "ropewalk": {
            "zone":"Miasto Dusz", "name":"Powroźnia",
            "desc":"Długi warsztat służy do skręcania lin dla statków, wozów i miejskich dźwigów.",
            "exits":{},
        },
        "shipwright_yard": {
            "zone":"Miasto Dusz", "name":"Stocznia Miejska",
            "desc":"Na drewnianych podporach stoi naprawiany kuter. Szkutnicy wymieniają deski i uszczelniają kadłub.",
            "exits":{},
        },
        "scholar_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Uczonych",
            "desc":"Spokojna uliczka łączy Plac Treningowy z domami skrybów, nauczycieli i kartografów.",
            "exits":{},
        },
        "cartographer_house": {
            "zone":"Miasto Dusz", "name":"Pracownia Kartografa",
            "desc":"Ściany pokrywają mapy traktów, ruin, bagien i gór. Na dużym stole powstają nowe szkice szlaków.",
            "exits":{},
        },
        "city_watch_office": {
            "zone":"Miasto Dusz", "name":"Biuro Patroli Miejskich",
            "desc":"Małe biuro przy północnej dzielnicy zbiera zgłoszenia mieszkańców i rozdziela krótkie patrole poza murami.",
            "exits":{},
        },
    }
    ROOMS.update(city_rooms)

    def connect(a, da, b, db):
        ROOMS[a].setdefault("exits", {})[da] = b
        ROOMS[b].setdefault("exits", {})[db] = a

    # Dzielnica rzemieślnicza przy Kuźni.
    connect("forge", "east", "artisan_lane", "west")
    connect("artisan_lane", "north", "tailor_workshop", "south")
    connect("artisan_lane", "east", "carpenter_workshop", "west")
    connect("artisan_lane", "south", "mason_yard", "north")
    connect("carpenter_workshop", "east", "leatherworker_workshop", "west")
    connect("carpenter_workshop", "south", "potter_workshop", "north")
    connect("potter_workshop", "west", "mason_yard", "east")

    # Południowa dzielnica mieszkalna.
    connect("south_street", "west", "lantern_alley", "east")
    connect("lantern_alley", "west", "residential_lane", "east")
    connect("lantern_alley", "south", "city_bakery", "north")
    connect("residential_lane", "west", "well_square", "east")
    connect("residential_lane", "south", "healer_house", "north")
    connect("well_square", "south", "courier_office", "north")
    connect("courier_office", "east", "healer_house", "west")

    # Dzielnica portowa.
    connect("harbor", "north", "dockside_lane", "south")
    connect("dockside_lane", "west", "harbor_warehouse", "east")
    connect("dockside_lane", "east", "ropewalk", "west")
    connect("ropewalk", "east", "shipwright_yard", "west")
    connect("shipwright_yard", "south", "dockside_lane", "north")

    # Uczeni i patrole.
    connect("training", "east", "scholar_lane", "west")
    connect("scholar_lane", "east", "cartographer_house", "west")
    connect("scholar_lane", "south", "city_watch_office", "north")

    outskirts = {
        "city_outskirts_gate": ("Przedbramie Południowe", "Droga tuż za murami rozdziela się na sad, pola i trakt prowadzący ku Łąkom."),
        "caravan_road": ("Droga Karawan", "Ubity trakt nosi ślady kół, końskich kopyt i pieszych podróżnych zmierzających do miasta."),
        "orchard_path": ("Droga Sadowa", "Niska kamienna ściana oddziela drogę od starych sadów należących do mieszkańców miasta."),
        "old_orchard": ("Stary Sad", "Pomiędzy jabłoniami i gruszami stoją porzucone kosze. Krzewy przyciągają drobną zwierzynę."),
        "mill_road": ("Droga do Młyna", "Boczna droga biegnie w stronę starego młyna i zakola rzeki."),
        "old_mill": ("Stary Młyn", "Koło wodne obraca się powoli przy kamiennym młynie, który nadal obsługuje okolicznych rolników."),
        "riverside_path": ("Ścieżka Nad Rzeką", "Wąska ścieżka ciągnie się wzdłuż trzcin i płytkiego brzegu rzeki."),
        "east_fields": ("Wschodnie Pola", "Niskie pola uprawne i miedze ciągną się aż do łagodnych wzgórz."),
        "shepherd_hill": ("Wzgórze Pasterzy", "Z trawiastego wzgórza widać mury miasta, Łąki i fragment Starego Traktu."),
        "roadside_shrine": ("Kapliczka Podróżnych", "Mała kamienna kapliczka stoi przy skrzyżowaniu dróg. Podróżni zostawiają tu świece i drobne monety."),
        "drainage_ditch": ("Stary Rów Obronny", "Wyschnięty fragment dawnego rowu otacza południową część murów i tworzy osłoniętą ścieżkę."),
        "abandoned_storehouse": ("Opuszczony Magazyn", "Zamknięty kiedyś magazyn ma wyłamane drzwi i ślady nieproszonych gości."),
        "charcoal_camp": ("Obóz Węglarzy", "Dymiące mielerze stoją przy skraju zagajnika. Węglarze wracają tu tylko w dzień."),
        "outer_wall_path": ("Ścieżka Pod Murami", "Patrolowa droga prowadzi wzdłuż zewnętrznej strony miejskich murów ku północnemu posterunkowi."),
    }
    for rid, (name, desc) in outskirts.items():
        ROOMS[rid] = {"zone":"Przedmieścia Miasta Dusz", "name":name, "desc":desc, "exits":{}}

    # Wstaw przedmieścia pomiędzy miasto i Łąki oraz dodaj boczną pętlę do Starego Traktu.
    ROOMS["south_gate"]["exits"]["south"] = "city_outskirts_gate"
    ROOMS["meadow"]["exits"]["north"] = "caravan_road"
    connect("south_gate", "south", "city_outskirts_gate", "north")
    connect("city_outskirts_gate", "south", "caravan_road", "north")
    connect("caravan_road", "south", "meadow", "north")
    connect("city_outskirts_gate", "west", "orchard_path", "east")
    connect("orchard_path", "west", "old_orchard", "east")
    connect("orchard_path", "south", "mill_road", "north")
    connect("mill_road", "west", "old_mill", "east")
    connect("mill_road", "south", "riverside_path", "north")
    connect("riverside_path", "east", "caravan_road", "west")
    connect("city_outskirts_gate", "east", "outer_wall_path", "west")
    connect("outer_wall_path", "south", "east_fields", "north")
    connect("east_fields", "south", "shepherd_hill", "north")
    connect("shepherd_hill", "west", "roadside_shrine", "east")
    connect("roadside_shrine", "north", "caravan_road", "east")
    connect("east_fields", "east", "drainage_ditch", "west")
    connect("drainage_ditch", "south", "abandoned_storehouse", "north")
    connect("abandoned_storehouse", "west", "charcoal_camp", "east")
    connect("charcoal_camp", "north", "shepherd_hill", "south")
    connect("outer_wall_path", "north", "north_watchpost", "south")

build_v0102_city_and_outskirts()

# ============================================================
# v0.24.0 - APTEKA POD SREBRNYM LIŚCIEM
# ============================================================
# Mikstury są osobnym asortymentem aptecznym. Karczma zachowuje kuchnię i
# Gotowanie, ale nie prowadzi już sprzedaży mikstur.
ROOMS["pharmacy"] = {
    "zone": "Miasto Dusz",
    "name": "Apteka Pod Srebrnym Liściem",
    "desc": (
        "Jasne półki wypełniają fiolki, suszone zioła i opisane butelki. "
        "To miejski sklep z podstawowymi miksturami i eliksirami."
    ),
    "exits": {"north": "inn"},
}
ROOMS["inn"].setdefault("exits", {})["south"] = "pharmacy"

SHOPS["market"] = [iid for iid in SHOPS.get("market", ()) if iid != "healing_potion"]
SHOPS["inn"] = [iid for iid in SHOPS.get("inn", ()) if iid != "healing_potion"]
SHOPS["pharmacy"] = [
    "healing_potion", "mana_potion",
    "greater_healing_potion", "greater_mana_potion",
    "vitality_elixir",
]
SHOP_SELLERS["pharmacy"] = "pharmacist_neris"
for _iid, _price in {
    "healing_potion": 100,
    "mana_potion": 140,
    "greater_healing_potion": 420,
    "greater_mana_potion": 520,
    "vitality_elixir": 800,
}.items():
    ITEMS[_iid]["price"] = _price
    ITEMS[_iid]["currency"] = "silver"

NPCS["pharmacist_neris"] = {
    "name": "Aptekarka Neris",
    "room": "pharmacy",
    "dialogue": (
        "Karczma jest od posiłku i odpoczynku. Mikstury kupisz tutaj. "
        "Jeśli zbierasz zioła, mam też dla ciebie regularne zlecenie."
    ),
    "quest": "v024_pharmacy_herbs",
}
QUESTS["v024_pharmacy_herbs"] = {
    "name": "Apteczne zapasy: Świeże zioła",
    "giver": "Aptekarka Neris",
    "kind": "collect_category", "target": "herb", "needed": 8,
    "description": (
        "Po przyjęciu zadania zbierz 8 dowolnych ziół i przynieś je Aptekarce Neris. "
        "Postęp zaczyna od 0/8 i liczy tylko nowe zbiory."
    ),
    "specialist_tool_type": "herbalism", "min_tool_level": 1,
    "reward_profession": "Zielarstwo", "reward_profession_xp": 500,
    "reward_tool_type": "herbalism", "reward_tool_xp": 350,
    "reward_silver": 450, "reward_gold": 0, "reward_mithril": 0,
    "reward_items": {"healing_potion": 1},
    "repeatable": True, "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
}

COMMAND_ALIASES.update({
    "kartografia": "cartography", "kartograf": "cartography",
    "cartography": "cartography", "mapy": "cartography",
})
GUIDE_DESTINATION_ALIASES.update({
    "apteka": "pharmacy",
    "apteka pod srebrnym lisciem": "pharmacy",
    "pharmacy": "pharmacy",
})

HELP_TOPICS["apteka"] = [
    "Apteka Pod Srebrnym Liściem leży na południe od Karczmy Pod Błękitnym Płomieniem.",
    "Karczma i Rynek nie sprzedają już mikstur. Podstawowe gotowe mikstury kupujesz u Aptekarki Neris.",
    "Komendy: sklep/list, kup <nazwa lub numer>, sprzedaj <nazwa>, quest list Neris.",
    "Oferta: Mikstura Leczenia, Mikstura Many, Wielkie Mikstury Leczenia/Many oraz Eliksir Witalności.",
    "Alchemia nadal pozwala wytwarzać mikstury samodzielnie i pozostaje ważna dla wyższych receptur.",
    "Neris ma powtarzalny co 60 minut quest na 8 świeżo zebranych ziół, zawsze od 0/8.",
    "Nawigacja: prowadz apteka albo walk pharmacy.",
]
HELP_TOPIC_ALIASES.update({
    "pharmacy": "apteka", "aptekarz": "apteka", "aptekarstwo": "apteka",
})
if "nawigacja" in HELP_TOPICS:
    HELP_TOPICS["nawigacja"].append(
        "Aktywny trop Mapy Skarbu obsługuje prowadz skarb; przy kilku tropach podaj numer, np. prowadz skarb 2."
    )
if "sklepy" in HELP_TOPICS:
    HELP_TOPICS["sklepy"].append(
        "Mikstury kupuje się w Aptece Pod Srebrnym Liściem, nie w Karczmie ani na Rynku. Użyj prowadz apteka."
    )
if "alchemia" in HELP_TOPICS:
    HELP_TOPICS["alchemia"].append(
        "Podstawowe gotowe mikstury można kupić w Aptece. Karczma i Rynek nie prowadzą już sprzedaży mikstur."
    )

# Nowi mieszkańcy i fachowcy. Są pokojowi i nie są celami walki.
NPCS.update({
    "tailor_lysa": {
        "name":"Krawcowa Lysa", "room":"tailor_workshop",
        "dialogue":"Szyję płaszcze, torby i mundury straży. Najwięcej pracy mam wtedy, gdy karawany przywożą nowe tkaniny.",
        "quest":"city_tailor_guard_delivery",
    },
    "carpenter_edric": {
        "name":"Cieśla Edric", "room":"carpenter_workshop",
        "dialogue":"Miasto ciągle potrzebuje desek do dachów, wozów i rusztowań. Dobre drewno nigdy się nie marnuje.",
        "quest":"city_carpenter_timber",
    },
    "leatherworker_soren": {
        "name":"Kaletnik Soren", "room":"leatherworker_workshop",
        "dialogue":"Naprawiam pasy, sakwy i uprzęże. W warsztacie zawsze znajdzie się robota, nawet gdy na Rynku jest spokojnie.",
    },
    "mason_kelda": {
        "name":"Kamieniarka Kelda", "room":"mason_yard",
        "dialogue":"Mury miasta stoją tak długo, jak długo ktoś pilnuje zaprawy i pękniętych kamieni.",
    },
    "potter_ves": {
        "name":"Garncarz Ves", "room":"potter_workshop",
        "dialogue":"Karczma tłucze dzbany szybciej, niż ja je wypalam. To chyba znak, że interes idzie dobrze.",
    },
    "baker_odo": {
        "name":"Piekarz Odo", "room":"city_bakery",
        "dialogue":"Straż przy bramach dostaje świeży chleb każdego ranka. Czasem brakuje mi rąk do roznoszenia dostaw.",
        "quest":"city_baker_gate_delivery",
    },
    "healer_sava": {
        "name":"Uzdrowicielka Sava", "room":"healer_house",
        "dialogue":"Leczę drobne rany i przygotowuję opatrunki. Świeże zioła z okolic miasta szybko schodzą.",
        "quest":"city_healer_herbs",
    },
    "courier_ina": {
        "name":"Kurierka Ina", "room":"courier_office",
        "dialogue":"Znam każdą ulicę i prawie każdy trakt. Najkrótsza droga nie zawsze jest najbezpieczniejsza.",
    },
    "warehouse_master_berek": {
        "name":"Magazynier Berek", "room":"harbor_warehouse",
        "dialogue":"Każda skrzynia ma znak właściciela. Bez porządku port zamieniłby się w jeden wielki stos towaru.",
    },
    "ropemaker_tina": {
        "name":"Powroźniczka Tina", "room":"ropewalk",
        "dialogue":"Dobra lina musi trzymać i statek, i wóz. Skręcanie jej wygląda prosto dopiero po latach praktyki.",
    },
    "shipwright_marek": {
        "name":"Szkutnik Marek", "room":"shipwright_yard",
        "dialogue":"Kadłub mówi, gdzie dostał falą. Ja tylko muszę umieć go słuchać.",
        "quest":"city_shipwright_fisher_delivery",
    },
    "cartographer_eren": {
        "name":"Kartograf Eren", "room":"cartographer_house",
        "dialogue":"Aktualizuję mapy na podstawie meldunków zwiadowców i podróżnych. Mam kilka zleceń: dostawy map, pomiary rubieży i oznaczanie sekretów.",
        "quest":"city_cartographer_guard_delivery",
    },
    "watchman_dalen": {
        "name":"Strażnik Dalen", "room":"city_watch_office",
        "dialogue":"Patrole pod murami zgłaszają drobnych rabusiów. To nie armia, ale lekceważeni szybko robią się odważniejsi.",
        "quest":"city_outskirts_thieves",
    },
    "orchardist_miro": {
        "name":"Sadownik Miro", "room":"old_orchard",
        "dialogue":"Sad jest stary, ale wciąż owocuje. Gorzej z wilkami, które zaczęły podchodzić pod drzewa.",
        "quest":"city_outskirts_wolves",
    },
})

# Przedmioty do krótkich dostaw miejskich.
ITEMS.update({
    "city_guard_uniform_order": {"name":"Zamówienie na mundury straży", "type":"quest", "price":None, "desc":"Dokument Krawcowej Lysy dla Kwatermistrza Harka."},
    "city_bread_crate": {"name":"Skrzynka świeżego chleba", "type":"quest", "price":None, "desc":"Poranna dostawa Piekarza Oda dla południowej bramy."},
    "city_harbor_repair_list": {"name":"Lista napraw kutrów", "type":"quest", "price":None, "desc":"Lista Szkutnika Marka dla Rybaka Borysa."},
    "city_patrol_map": {"name":"Zaktualizowana mapa patroli", "type":"quest", "price":None, "desc":"Nowa mapa Kartografa Erena dla Kapitana Arvena."},
    "city_harbor_chart": {"name":"Mapa magazynów portowych", "type":"quest", "price":None, "desc":"Plan portowych magazynów przygotowany przez Kartografa Erena dla Magazyniera Berka."},
    "city_mine_route_map": {"name":"Mapa trasy do Kopalni Głębinowej", "type":"quest", "price":None, "desc":"Mapa bezpiecznej drogi z Miasta Dusz do kopalni dla Górnika Torena."},
})

QUESTS.update({
    "city_tailor_guard_delivery": {
        "name":"Miejska przysługa: Mundury dla straży", "giver":"Krawcowa Lysa", "kind":"deliver_npc",
        "target_npc":"guard_quartermaster_harek", "quest_item":"city_guard_uniform_order",
        "accept_items":{"city_guard_uniform_order":1}, "needed":1,
        "description":"Zanieś zamówienie Krawcowej Lysy Kwatermistrzowi Harkowi w Zbrojowni Straży. Zadanie odnawia się co 60 minut.",
        "reward_stat_progress":20, "reward_silver":180, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_baker_gate_delivery": {
        "name":"Miejska przysługa: Chleb na południową bramę", "giver":"Piekarz Odo", "kind":"deliver_npc",
        "target_npc":"south_gate_guard_lena", "quest_item":"city_bread_crate",
        "accept_items":{"city_bread_crate":1}, "needed":1,
        "description":"Dostarcz skrzynkę świeżego chleba Strażniczce Lenie przy Południowej Bramie. Zadanie odnawia się co 60 minut.",
        "reward_stat_progress":20, "reward_silver":160, "reward_gold":0, "reward_mithril":0,
        "reward_items":{"healing_potion":1}, "repeatable":True,
        "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS, "event_progress_only":True,
    },
    "city_shipwright_fisher_delivery": {
        "name":"Miejska przysługa: Lista napraw portowych", "giver":"Szkutnik Marek", "kind":"deliver_npc",
        "target_npc":"fisher_tomas", "quest_item":"city_harbor_repair_list",
        "accept_items":{"city_harbor_repair_list":1}, "needed":1,
        "description":"Przekaż Rybakowi Borysowi na Targu Rybnym listę kutrów wymagających naprawy.",
        "reward_stat_progress":25, "reward_silver":220, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":False, "event_progress_only":True,
    },
    "city_cartographer_guard_delivery": {
        "name":"Miejska przysługa: Nowa mapa patroli", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"captain_arven", "quest_item":"city_patrol_map",
        "accept_items":{"city_patrol_map":1}, "needed":1,
        "description":"Zanieś Kapitanowi Arvenowi w Strażnicy Głównej zaktualizowaną mapę patroli.",
        "reward_stat_progress":30, "reward_silver":260, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_harbor_delivery": {
        "name":"Kartograf Eren: Plan portowych magazynów", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"warehouse_master_berek", "quest_item":"city_harbor_chart",
        "accept_items":{"city_harbor_chart":1}, "needed":1,
        "description":"Dostarcz Magazynierowi Berkowi w Porcie mapę magazynów i nabrzeży przygotowaną przez Erena.",
        "reward_stat_progress":25, "reward_silver":240, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_mine_delivery": {
        "name":"Kartograf Eren: Droga do kopalni", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"miner_toren", "quest_item":"city_mine_route_map",
        "accept_items":{"city_mine_route_map":1}, "needed":1,
        "description":"Zanieś Górnikowi Torenowi przy wejściu do kopalni nową mapę bezpiecznej trasy z miasta.",
        "reward_stat_progress":30, "reward_silver":280, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_frontier_survey": {
        "name":"Kartograf Eren: Pięć nowych sektorów", "giver":"Kartograf Eren",
        "kind":"explore_frontier", "target":"any", "needed":5,
        "description":"Po przyjęciu zadania odkryj 5 nowych sektorów proceduralnych rubieży i wróć do Kartografa Erena.",
        "reward_stat_progress":45, "reward_silver":650, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_secret_marks": {
        "name":"Kartograf Eren: Znak poza mapą", "giver":"Kartograf Eren",
        "kind":"discover_secret", "target":"any", "needed":1,
        "description":"Po przyjęciu zadania otrzymasz Mapę Skarbu Rubieży. Użyj jej, dotrzyj do wskazanego sektora, odkryj 1 nowy sekret proceduralnego świata i wróć do Kartografa Erena.",
        "accept_items":{"quest_map_eren_secret_marks":1}, "accept_items_always":True,
        "reward_stat_progress":55, "reward_silver":900, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_carpenter_timber": {
        "name":"Miejska robota: Drewno na rusztowania", "giver":"Cieśla Edric", "kind":"collect_category",
        "target":"wood", "needed":10,
        "description":"Po przyjęciu zadania pozyskaj 10 sztuk dowolnego drewna i przynieś je Cieśli Edricowi.",
        "specialist_tool_type":"woodcutting", "min_tool_level":1,
        "reward_profession":"Drwalstwo", "reward_profession_xp":450,
        "reward_tool_type":"woodcutting", "reward_tool_xp":360,
        "reward_silver":240, "reward_gold":0, "reward_mithril":0, "reward_items":{},
        "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_healer_herbs": {
        "name":"Miejska robota: Zioła dla lecznicy", "giver":"Uzdrowicielka Sava", "kind":"collect_category",
        "target":"herb", "needed":10,
        "description":"Po przyjęciu zadania zbierz 10 dowolnych ziół i przynieś je Uzdrowicielce Savie.",
        "specialist_tool_type":"herbalism", "min_tool_level":1,
        "reward_profession":"Zielarstwo", "reward_profession_xp":450,
        "reward_tool_type":"herbalism", "reward_tool_xp":360,
        "reward_silver":240, "reward_gold":0, "reward_mithril":0, "reward_items":{"healing_potion":1},
        "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_outskirts_thieves": {
        "name":"Patrol przedmieść: Drobni rabusie", "giver":"Strażnik Dalen", "kind":"kill",
        "target":"outskirts_thief", "needed":6,
        "description":"Pokonaj 6 Rabusiów z Przedmieść po przyjęciu zadania i wróć do Strażnika Dalena.",
        "reward_stat_progress":40, "reward_silver":420, "reward_gold":1, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_outskirts_wolves": {
        "name":"Sad pod presją: Wilki pod murami", "giver":"Sadownik Miro", "kind":"kill",
        "target":"outskirts_wolf", "needed":5,
        "description":"Pokonaj 5 Wilków z Przedmieść po przyjęciu zadania i wróć do Sadownika Mira.",
        "reward_stat_progress":35, "reward_silver":360, "reward_gold":0, "reward_mithril":0,
        "reward_items":{"healing_potion":1}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
})

# v0.24.0: pięć dotychczasowych zleceń Erena pozostaje niezależnych i
# godzinnych. Poniższa seria jest nowym, jednorazowym łańcuchem mistrzowskim.
ITEMS["v024_eren_master_atlas"] = {
    "name": "Wielki Atlas Erena", "type": "quest", "price": None,
    "desc": "Wielki atlas rubieży przygotowany przez Erena dla Kartografki Lysy.",
}
QUESTS.update({
    "v024_eren_master_1": {
        "name": "Wielki Atlas I: Dwanaście nowych sektorów", "giver": "Kartograf Eren",
        "kind": "explore_frontier", "target": "any", "needed": 12,
        "description": "Odkryj 12 nowych sektorów proceduralnych rubieży po przyjęciu zadania.",
        "reward_silver": 5000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 8,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_2": {
        "name": "Wielki Atlas II: Drogi poza mapą", "giver": "Kartograf Eren",
        "kind": "discover_secret", "target": "any", "needed": 2,
        "description": "Odkryj 2 nowe sekrety proceduralnego świata po przyjęciu zadania.",
        "requires_quest": "v024_eren_master_1",
        "reward_silver": 8500, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 2},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 12,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_3": {
        "name": "Wielki Atlas III: Małe głębiny", "giver": "Kartograf Eren",
        "kind": "mini_dungeon", "target": "any", "needed": 2,
        "description": "Dotrzyj do finałowej komnaty 2 nowych proceduralnych mini-lochów.",
        "requires_quest": "v024_eren_master_2",
        "reward_silver": 12000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 1, "soul_elixir": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 16,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_4": {
        "name": "Wielki Atlas IV: Żywy świat", "giver": "Kartograf Eren",
        "kind": "world_event", "target": "any", "needed": 3,
        "description": "Odwiedź 3 nowe aktywne wydarzenia świata po przyjęciu zadania.",
        "requires_quest": "v024_eren_master_3",
        "reward_silver": 16000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 2, "soul_elixir": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 20,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_5": {
        "name": "Wielki Atlas V: Przekazanie dzieła", "giver": "Kartograf Eren",
        "kind": "deliver_npc", "target_npc": "cartographer_lysa",
        "quest_item": "v024_eren_master_atlas", "accept_items": {"v024_eren_master_atlas": 1},
        "needed": 1,
        "description": "Dostarcz Wielki Atlas Erena Kartografce Lysie w Bibliotece.",
        "requires_quest": "v024_eren_master_4",
        "reward_silver": 25000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 3, "soul_elixir": 2},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 30,
        "repeatable": False, "event_progress_only": True,
    },
})
NPCS["cartographer_eren"]["quest_chain"] = tuple(
    f"v024_eren_master_{i}" for i in range(1, 6)
)
NPCS["cartographer_eren"]["dialogue"] = (
    "Mam pięć godzinnych zleceń kartograficznych oraz pięcioetapową serię Wielkiego Atlasu. "
    "Jeśli chcesz pracować nad mapami dłużej, zapytaj o listę questów."
)

MOB_TEMPLATES.update({
    "outskirts_thief": {
        "name":"Rabuś z Przedmieść", "max_hp":70, "damage":7, "damage_type":"physical",
        "silver":28, "gold":0, "mithril":0, "stat_reward":28, "soul_reward":135,
        "drops":{"healing_potion":0.04}, "quest_target":"outskirts_thief",
    },
    "outskirts_wolf": {
        "name":"Wilk z Przedmieść", "max_hp":56, "damage":6, "damage_type":"physical",
        "silver":18, "gold":0, "mithril":0, "stat_reward":23, "soul_reward":118,
        "drops":{"wolf_fang":0.18}, "quest_target":"outskirts_wolf",
    },
    "outskirts_boar": {
        "name":"Dzik z Pól", "max_hp":68, "damage":7, "damage_type":"physical",
        "silver":22, "gold":0, "mithril":0, "stat_reward":25, "soul_reward":125,
        "drops":{}, "quest_target":None,
    },
    "outskirts_wasp": {
        "name":"Osa Sadowa", "max_hp":44, "damage":5, "damage_type":"physical",
        "silver":15, "gold":0, "mithril":0, "stat_reward":19, "soul_reward":100,
        "drops":{}, "quest_target":None,
    },
})

MOB_SPAWNS.extend([
    ("caravan_road","outskirts_thief"), ("caravan_road","outskirts_wolf"),
    ("orchard_path","outskirts_wolf"),
    ("mill_road","outskirts_thief"),
    ("old_mill","outskirts_boar"),
    ("riverside_path","outskirts_wolf"), ("riverside_path","outskirts_boar"),
    ("east_fields","outskirts_boar"), ("east_fields","outskirts_wasp"),
    ("shepherd_hill","outskirts_wolf"), ("shepherd_hill","outskirts_thief"),
    ("roadside_shrine","outskirts_thief"),
    ("drainage_ditch","outskirts_wasp"), ("drainage_ditch","outskirts_wolf"),
    ("abandoned_storehouse","outskirts_thief"), ("abandoned_storehouse","outskirts_thief"),
    ("charcoal_camp","outskirts_boar"), ("charcoal_camp","outskirts_thief"),
    ("outer_wall_path","outskirts_thief"), ("outer_wall_path","outskirts_wolf"),
])

# Audyt gęstości v0.10.2: puste pokoje Dziczy/Bagien/Pustyni są bezpiecznymi
# hubami NPC. W Podziemiach dwa przejścia bojowe były wyraźnie rzadsze od reszty.
MOB_SPAWNS.extend([
    ("cave_tunnel", "crystal_guardian"),
    ("crypt_entrance", "skeleton"),
])

# Wrogowie w zwykłym świecie mogą przemieszczać się między sąsiednimi pokojami.
# Bossowie, mini-bossowie, aktywnie walczące moby, miasta, huby NPC oraz wielkie
# piętra instancji pozostają stabilne, żeby ruch nie psuł bramek progresji.
MOB_WANDER_MIN_SECONDS = 45
MOB_WANDER_MAX_SECONDS = 110
MOB_WANDER_ROOM_CAP = 4
MOB_WANDER_BLOCKED_ZONES = {
    "Miasto Dusz", "Gildia Dusz", "Wioska Górska",
    "Krypta", "Mityczna Krypta", "Wieża Astralna", "Mityczna Wieża Astralna",
    "Twierdza Gigantów", "Kopalnia Głębinowa",
}
MOB_WANDER_SAFE_ROOMS = frozenset(
    {str(npc.get("room")) for npc in NPCS.values() if npc.get("room")}
    | set(SHOPS)
    | {"city_outskirts_gate", "caravan_camp", "swamp_hunter_post", "sewer_entrance"}
)


def mob_template_can_wander(template):
    if not template or int(template.get("max_hp", 0) or 0) <= 0:
        return False
    if template.get("stationary_mob") or template.get("mini_boss") or template.get("world_boss"):
        return False
    boss_flags = (
        "boss", "boss_mechanic", "crypt_boss", "astral_boss",
        "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
    )
    return not any(template.get(flag) for flag in boss_flags)


def mob_room_can_wander(room_id):
    room = ROOMS.get(room_id, {})
    zone = str(room.get("zone", ""))
    if not room or room_id in MOB_WANDER_SAFE_ROOMS:
        return False
    if room.get("procedural_infinite"):
        return False
    if zone in MOB_WANDER_BLOCKED_ZONES:
        return False
    if zone.startswith("Loch Profesyjny"):
        return False
    if any(token in zone for token in ("Krypta", "Wieża Astralna", "Twierdza Gigantów")):
        return False
    return True


def mob_wander_candidates(room_id):
    if not mob_room_can_wander(room_id):
        return []
    room = ROOMS[room_id]
    zone = room.get("zone")
    result = []
    for direction, target in room.get("exits", {}).items():
        if direction not in ("north", "south", "east", "west"):
            continue
        target_room = ROOMS.get(target)
        if not target_room or target_room.get("zone") != zone:
            continue
        if not mob_room_can_wander(target):
            continue
        result.append(target)
    return result

HELP_TOPICS["miasto"] = [
    "Miasto Dusz ma rozbudowane dzielnice: rzemieślniczą, mieszkalną, portową oraz ulicę uczonych.",
    "Nowe warsztaty i budynki mają pokojowych NPC, krótkie dialogi i małe zadania miejskie.",
    "Południowa Brama prowadzi teraz przez Przedmieścia Miasta Dusz do Łąk.",
    "Przedmieścia tworzą zapętlony obszar z sadem, młynem, polami, ścieżką pod murami i alternatywnym dojściem do północnego posterunku.",
    "Samo Miasto Dusz pozostaje bezpieczne i bez wrogich spawnów.",
]
HELP_TOPICS["miasto"].append(
    "Apteka Pod Srebrnym Liściem znajduje się na południe od Karczmy. To jedyny miejski sklep z podstawowymi miksturami."
)
HELP_TOPICS["kartografia"] = [
    "Kartograf Eren ma 5 godzinnych zleceń oraz 5-etapową jednorazową serię Wielkiego Atlasu, razem 10 własnych questów.",
    "kartografia / cartography pokazuje postęp sektorów, sekretów, mini-lochów, wydarzeń i Map Skarbów.",
    "Mapa Skarbu Rubieży zapisuje aktywny trop; mapa skarbu pokazuje wszystkie tropy.",
    "prowadz skarb prowadzi bezpośrednio do jedynego tropu. Przy kilku użyj prowadz skarb <numer>.",
    "Znak poza mapą wydaje przy przyjęciu questową Mapę Erena. Wpisz użyj mapy, potem prowadz skarb, a po dotarciu do sektora sekret / secret. Po porzuceniu questa jego mapa i aktywny trop znikają. Questy kartograficzne zawsze startują 0/x i liczą nowe zdarzenia.",
    "Nawigacja do Erena: prowadz Eren. Lista jego zadań: quest list Eren.",
]
HELP_TOPIC_ALIASES.update({
    "kartograf": "kartografia", "cartography": "kartografia",
    "mapy skarbow": "kartografia", "mapy skarbów": "kartografia",
    "prowadz skarb": "kartografia",
})

HELP_TOPICS["ruchome_moby"] = [
    "Zwykłe moby w świecie mogą przechodzić do sąsiednich pomieszczeń tej samej strefy, ale nigdy nie rozpoczynają walki same.",
    "Moby nie wchodzą do Miasta Dusz, sklepów, pokojów NPC ani innych bezpiecznych hubów.",
    "Bossowie i mini-bossowie nie wędrują. Mob w aktywnej walce również pozostaje na miejscu.",
    "Wielkie piętra Krypt, Wież, Twierdzy i lochów profesyjnych zachowują stałą obsadę, aby nie psuć progresji i bramek bossów.",
    "Po śmierci wędrujący mob odradza się w swoim pierwotnym miejscu spawnu.",
]
HELP_TOPICS["balans_narzedzi"] = [
    "v0.10.2 wyrównuje tempo zdobywania leveli narzędzi zbierackich w czasie rzeczywistym.",
    "Kilof dostaje x3.0 Tool XP z normalnego wydobycia, Piła x2.4, Wędka x1.5, a Sierp zachowuje x1.0.",
    "Mnożniki dotyczą Tool XP z normalnych akcji; nie zwiększają Profession XP, ilości surowców ani nagród questowych.",
    "Narzędzia produkcyjne nie zostały przyspieszone, ponieważ ich realny koszt obejmuje materiały i różne wartości XP receptur.",
]
HELP_TOPIC_ALIASES.update({
    "miasto dusz":"miasto", "city":"miasto", "przedmiescia":"miasto", "przedmieścia":"miasto",
    "ruchome moby":"ruchome_moby", "wedrujace moby":"ruchome_moby", "wędrujące moby":"ruchome_moby",
    "balans narzedzi":"balans_narzedzi", "balans narzędzi":"balans_narzedzi", "tool balance":"balans_narzedzi",
})

HELP_TOPICS["wielkie_lochy"] = [
    "v0.11.0: wszystkie piętrowe Krypty i lochy są generowane dynamicznie od pierwszego poziomu, dopiero gdy gracz do nich wchodzi.",
    "Dotyczy to obu Krypt, obu Wież Astralnych, Twierdzy Gigantów, Kopalni Głębinowej i czterech lochów profesyjnych.",
    "v0.10.0 usuwa małe liniowe piętra z głównych instancji.",
    "Krypta, Mityczna Krypta, Wieża Astralna, Mityczna Wieża Astralna i Twierdza Gigantów mają po 15 pomieszczeń na piętro.",
    "Lochy profesyjne mają po 10 pomieszczeń na poziom.",
    "Schody na następne piętro są w końcowej komnacie, a nie przy wejściu.",
    "Na piętrach co 10 boss pilnuje przejścia dalej; po pierwszym trwałym zaliczeniu jego późniejszy respawn nie blokuje postaci.",
    "Dynamiczne piętra ponad dawnym końcem są generowane w tym samym dużym układzie.",
    "Bojowe piętra mają więcej równoczesnych mobów; wszystkie rudy i Górnictwo są skupione w jednej Kopalni Głębinowej.",
    "Prowadzenie nadal zatrzymuje się przed wejściem do lochu i nie rozwiązuje mapy za gracza.",
]
HELP_TOPIC_ALIASES.update({
    "wielkie lochy": "wielkie_lochy", "massive dungeons": "wielkie_lochy",
    "duze lochy": "wielkie_lochy", "duże lochy": "wielkie_lochy",
    "dynamiczne lochy": "wielkie_lochy", "dynamiczne krypty": "wielkie_lochy",
    "proceduralne lochy": "wielkie_lochy", "dynamic dungeons": "wielkie_lochy",
})

# Platynowy Kartograf zawsze śledzi cały aktualny statyczny świat.
_v0100_tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
if _v0100_tiers:
    _v0100_tiers = [(req, rank) for req, rank in _v0100_tiers if rank != "Platinum"]
    _v0100_tiers.append((len(ROOMS), "Platinum"))
    ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(_v0100_tiers)

EXPLORATION_ZONE_ROOMS = {}
for _room_id, _room in ROOMS.items():
    EXPLORATION_ZONE_ROOMS.setdefault(_room["zone"], []).append(_room_id)
for _zone in EXPLORATION_ZONE_ROOMS:
    EXPLORATION_ZONE_ROOMS[_zone].sort()

TRACKED_EXPLORATION_ZONES = {
    zone: tuple(room_ids)
    for zone, room_ids in EXPLORATION_ZONE_ROOMS.items()
    if len(room_ids) >= EXPLORATION_ZONE_MIN_ROOMS
}
ALL_EXPLORATION_ROOMS = tuple(sorted(ROOMS))

EXPLORATION_REWARD_ITEMS = {}
for _zone, _room_ids in TRACKED_EXPLORATION_ZONES.items():
    _reward_item_id = f"exploration_relic_{_collection_slug(_zone)}"
    EXPLORATION_REWARD_ITEMS[_zone] = _reward_item_id
    ITEMS.setdefault(
        _reward_item_id,
        {
            "name": f"Pamiątka Odkrywcy: {_zone}",
            "type": "collectible",
            "price": None,
            "rarity": "unique",
            "rarity_name": "Unikalny",
            "exploration_reward": True,
            "desc": (
                f"Unikalna pamiątka za odkrycie 100 procent strefy {_zone}. "
                "Nie jest przedmiotem do sprzedaży ani elementem ekwipunku."
            ),
        },
    )


def _build_set_catalog():
    catalog = {}
    item_to_set = {}
    for item_id, item in ITEMS.items():
        entry_id = None
        entry_name = None
        piece_key = item_id
        if item.get("regional_set"):
            set_id = str(item["regional_set"])
            entry_id = f"regional:{set_id}"
            entry_name = REGIONAL_SET_BONUSES.get(set_id, {}).get(
                "name", f"Regionalny set {set_id}"
            )
        elif item.get("class_set_name"):
            set_name = str(item.get("class_set_name"))
            req = str(item.get("required_class") or set_name)
            entry_id = f"class:{req}"
            entry_name = f"Zestaw {set_name} ({req})"
            # Wszystkie tiery Biegłości liczą się jako te same 8 logicznych części setu.
            piece_key = str(item.get("class_set_piece") or item.get("slot") or item_id)
        elif item.get("crypt_set_tier"):
            tier = int(item["crypt_set_tier"])
            entry_id = f"crypt:{tier}"
            entry_name = f"Zestaw Krypty Tier {tier}"
            piece_key = str(item.get("crypt_base_item") or item_id)
        elif item.get("astral_set_tier"):
            tier = int(item["astral_set_tier"])
            entry_id = f"astral:{tier}"
            entry_name = f"Astralny Zestaw Kręgu {tier}"
        if not entry_id:
            continue
        row = catalog.setdefault(entry_id, {"name": entry_name, "pieces": set()})
        row["pieces"].add(piece_key)
        item_to_set[item_id] = entry_id
    for row in catalog.values():
        row["pieces"] = tuple(sorted(row["pieces"]))
    return catalog, item_to_set


SET_COLLECTION_CATALOG, SET_ENTRY_BY_ITEM = _build_set_catalog()

def boss_codex_drop_is_unique(item_id):
    item = ITEMS.get(str(item_id), {})
    if not item:
        return False
    rarity = str(item.get("rarity", "")).lower()
    return bool(
        item.get("named_loot")
        or item.get("legendary_set_loot")
        or item.get("legendary_class_relic")
        or item.get("boss_relic_floor") is not None
        or item.get("astral_relic_floor") is not None
        or rarity in ("legendary", "mythic", "eternal", "unique")
    )

NAMED_LOOT_CATALOG = {
    item_id: item["name"]
    for item_id, item in ITEMS.items()
    if (
        item.get("named_loot")
        or item.get("boss_relic_floor") is not None
        or item.get("astral_relic_floor") is not None
        or item_id == "bandit_chief_signet"
        or item_id in WORLD_BOSS_UNIQUES
    )
}

BOSS_COLLECTION_CATALOG = {
    mob_id: data["name"]
    for mob_id, data in MOB_TEMPLATES.items()
    if any(
        data.get(flag)
        for flag in (
            "world_boss", "mini_boss", "crypt_boss", "astral_boss",
            "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
        )
    )
}

RARE_MOB_COLLECTION_CATALOG = {
    mob_id: data["name"]
    for mob_id, data in MOB_TEMPLATES.items()
    if data.get("rare_mob")
}

CHEST_COLLECTION_CATALOG = {
    room_id: cfg["name"]
    for room_id, cfg in TREASURE_CHESTS.items()
}

FISH_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(FISH_RESOURCE_IDS) if item_id in ITEMS
}
MINERAL_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(ORE_RESOURCE_IDS) if item_id in ITEMS
}
HERB_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(HERB_RESOURCE_IDS) if item_id in ITEMS
}
GEM_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"]
    for item_id in sorted(set(RAW_GEM_IDS) | set(CUT_GEM_IDS)) if item_id in ITEMS
}
MATERIAL_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"]
    for item_id in sorted(
        set(WOOD_RESOURCE_IDS) | {iid for iid, data in ITEMS.items() if data.get("type") == "craft_material"}
    ) if item_id in ITEMS
}
UNIQUE_ITEM_COLLECTION_CATALOG = {
    item_id: data["name"]
    for item_id, data in ITEMS.items()
    if (
        data.get("type") == "collectible"
        or item_id in NAMED_LOOT_CATALOG
        or (str(data.get("rarity", "")).lower() == "unique" and not item_id.startswith("corpse_"))
    )
}

EQUIPMENT_COLLECTION_CATALOG = {
    item_id: data["name"]
    for item_id, data in ITEMS.items()
    if data.get("type") in ("armor", "weapon")
}

COLLECTION_CATALOGS = {
    "fish": FISH_COLLECTION_CATALOG,
    "minerals": MINERAL_COLLECTION_CATALOG,
    "herbs": HERB_COLLECTION_CATALOG,
    "gems": GEM_COLLECTION_CATALOG,
    "bosses": BOSS_COLLECTION_CATALOG,
    "rare": RARE_MOB_COLLECTION_CATALOG,
    "materials": MATERIAL_COLLECTION_CATALOG,
    "unique": UNIQUE_ITEM_COLLECTION_CATALOG,
    "equipment": EQUIPMENT_COLLECTION_CATALOG,
    # Widoki dodatkowe z wcześniejszych wersji.
    "named": NAMED_LOOT_CATALOG,
    "sets": {key: value["name"] for key, value in SET_COLLECTION_CATALOG.items()},
    "chests": CHEST_COLLECTION_CATALOG,
}


# ============================================================
# v0.9.22 - QUEST MOB DENSITY
# Questy typu kill z potrzebą >1 nie powinny zmuszać do czekania na pojedynczy
# respawn. Dla celu questu liczymy również moby oznaczone quest_target/quest_targets
# i dokładamy brakujące instancje w istniejących pokojach. Bossowie (needed=1)
# pozostają pojedynczymi przeciwnikami.
def _v0922_expand_quest_mob_spawns():
    def quest_tags(mob_id):
        template = MOB_TEMPLATES.get(mob_id, {})
        tags = {mob_id}
        primary = template.get("quest_target")
        if primary:
            tags.add(primary)
        tags.update(template.get("quest_targets") or ())
        return tags

    added = []
    for quest_id, quest in QUESTS.items():
        if quest.get("kind") != "kill":
            continue
        needed = max(1, int(quest.get("needed", 1) or 1))
        if needed <= 1:
            continue
        target = str(quest.get("target", ""))
        if not target:
            continue
        eligible = [
            (room_id, mob_id)
            for room_id, mob_id in MOB_SPAWNS
            if target in quest_tags(mob_id)
        ]
        if not eligible:
            continue
        # Im większy quest, tym więcej równoczesnych celów, ale bez zalewania pokoju.
        desired = min(8, max(3, (needed + 1) // 2))
        if len(eligible) >= desired:
            continue
        seed = list(eligible)
        index = 0
        while len(eligible) < desired:
            room_id, mob_id = seed[index % len(seed)]
            MOB_SPAWNS.append((room_id, mob_id))
            eligible.append((room_id, mob_id))
            added.append((quest_id, target, room_id, mob_id))
            index += 1
    return added


V0922_ADDED_QUEST_MOB_SPAWNS = _v0922_expand_quest_mob_spawns()

# v0.9.21 - COLLECTION CODEX 2.0 dynamic group indexes
# ============================================================
def _build_collection_v2_groups():
    class_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups["Ogólne"] = set()
    material_groups = {tier["key"]: set() for tier in CORPSE_MATERIAL_TIERS}
    set_groups = {}
    set_names = {}
    for item_id, item in ITEMS.items():
        if item.get("type") not in ("armor", "weapon"):
            continue
        req_class = str(item.get("required_class") or "")
        if req_class in class_groups:
            class_groups[req_class].add(item_id)
        if (
            str(item.get("rarity", "")).lower() == "legendary"
            or item.get("legendary_set_loot")
            or item.get("legendary_class_relic")
        ):
            legendary_groups[req_class if req_class in CLASS_EQUIPMENT_SETS else "Ogólne"].add(item_id)
        material = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
        if material in material_groups:
            material_groups[material].add(item_id)

        group_id = None
        group_name = None
        if item.get("class_set_name"):
            mastery = int(item.get("required_mastery", 1) or 1)
            group_id = f"class:{req_class}:{item.get('class_set_name')}:{mastery}"
            group_name = f"{item.get('class_set_name')} — {req_class}, Biegłość {mastery}"
        elif item.get("regional_set"):
            sid = str(item["regional_set"])
            group_id = f"regional:{sid}"
            group_name = REGIONAL_SET_BONUSES.get(sid, {}).get("name", f"Set regionalny {sid}")
        elif item.get("crypt_set_tier"):
            tier = int(item["crypt_set_tier"])
            group_id = f"crypt:{tier}"
            group_name = f"Zestaw Krypty Tier {tier}"
        elif item.get("astral_set_tier"):
            tier = int(item["astral_set_tier"])
            group_id = f"astral:{tier}"
            group_name = f"Astralny Zestaw Kręgu {tier}"
        if group_id:
            set_groups.setdefault(group_id, set()).add(item_id)
            set_names[group_id] = group_name
    return (
        {k: frozenset(v) for k, v in class_groups.items()},
        {k: frozenset(v) for k, v in legendary_groups.items()},
        {k: frozenset(v) for k, v in material_groups.items()},
        {k: frozenset(v) for k, v in set_groups.items()},
        set_names,
    )

(
    COLLECTION_V2_CLASS_GROUPS,
    COLLECTION_V2_LEGENDARY_GROUPS,
    COLLECTION_V2_MATERIAL_GROUPS,
    COLLECTION_V2_SET_GROUPS,
    COLLECTION_V2_SET_NAMES,
) = _build_collection_v2_groups()

COLLECTION_V2_MATERIAL_LABELS = {
    tier["key"]: tier["label"] for tier in CORPSE_MATERIAL_TIERS
}

# ============================================================
# v0.8.76 - persistent Bestiary
# ============================================================
def canonical_bestiary_template_id(template_id):
    """Collapse procedural elite/rare affixes into the underlying species.

    The world contains thousands of generated combat variants.  The Bestiary
    intentionally tracks the actual species instead of requiring a separate
    entry for every affix copy.
    """
    template_id = str(template_id or "")
    seen = set()
    while template_id and template_id not in seen:
        seen.add(template_id)
        template = MOB_TEMPLATES.get(template_id, {})
        base_id = template.get("rare_base_template") or template.get("elite_base_template")
        if not base_id or base_id == template_id:
            break
        template_id = str(base_id)
    return template_id

BESTIARY_CATALOG = {}
BESTIARY_SPAWN_ROOMS = {}
for _bestiary_room_id, _bestiary_template_id in MOB_SPAWNS:
    _bestiary_id = canonical_bestiary_template_id(_bestiary_template_id)
    if _bestiary_id not in MOB_TEMPLATES:
        continue
    BESTIARY_CATALOG[_bestiary_id] = MOB_TEMPLATES[_bestiary_id]["name"]
    BESTIARY_SPAWN_ROOMS.setdefault(_bestiary_id, set()).add(_bestiary_room_id)

# Platinum zawsze oznacza faktyczne 100% aktualnej wersji świata / Bestiariusza.
ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = (
    (100, "Bronze"), (500, "Silver"), (1000, "Gold"),
    (len(ALL_EXPLORATION_ROOMS), "Platinum"),
)
ACHIEVEMENT_TRACKS["bestiary_unique"]["tiers"] = (
    (50, "Bronze"), (250, "Silver"), (500, "Gold"),
    (len(BESTIARY_CATALOG), "Platinum"),
)

def bestiary_resistance_text(template):
    """Describe only resistance data that really exists in combat data."""
    parts = []
    resistances = template.get("resistances") or {}
    if isinstance(resistances, dict):
        labels = {"physical": "fizyczne", "magic": "magiczne"}
        for key, value in sorted(resistances.items()):
            try:
                pct = int(round(float(value) * 100)) if abs(float(value)) <= 1 else int(round(float(value)))
            except (TypeError, ValueError):
                continue
            parts.append(f"{labels.get(str(key), str(key))} {pct}%")
    immunities = template.get("immunities") or ()
    if isinstance(immunities, str):
        immunities = (immunities,)
    if immunities:
        parts.append("odporność całkowita: " + ", ".join(map(str, immunities)))
    weaknesses = template.get("weaknesses") or ()
    if isinstance(weaknesses, str):
        weaknesses = (weaknesses,)
    if weaknesses:
        parts.append("słabość: " + ", ".join(map(str, weaknesses)))
    return "; ".join(parts) if parts else "brak specjalnych odporności"

MINI_BOSS_IDS = frozenset(
    mob_id for mob_id, data in MOB_TEMPLATES.items() if data.get("mini_boss")
)

# Mapa wpisów kolekcji do stref do komendy progress region.
REGION_COLLECTION_ENTRIES = {
    zone: {"named": set(), "bosses": set(), "rare": set(), "chests": set()}
    for zone in EXPLORATION_ZONE_ROOMS
}

_spawn_zones = {}
for _room_id, _mob_id in MOB_SPAWNS:
    _zone = ROOMS.get(_room_id, {}).get("zone")
    if _zone:
        _spawn_zones.setdefault(_mob_id, set()).add(_zone)

for _mob_id in BOSS_COLLECTION_CATALOG:
    for _zone in _spawn_zones.get(_mob_id, ()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("bosses", set()).add(_mob_id)

for _rare_id, _rare_data in MOB_TEMPLATES.items():
    if _rare_id not in RARE_MOB_COLLECTION_CATALOG:
        continue
    _base = _rare_data.get("rare_base_template", _rare_id)
    for _zone in _spawn_zones.get(_base, ()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("rare", set()).add(_rare_id)

for _room_id in CHEST_COLLECTION_CATALOG:
    _zone = ROOMS.get(_room_id, {}).get("zone")
    if _zone:
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("chests", set()).add(_room_id)

for _mob_id, _mob in MOB_TEMPLATES.items():
    _named_drops = set(_mob.get("drops", {})).intersection(NAMED_LOOT_CATALOG)
    if not _named_drops:
        continue
    _base = _mob.get("rare_base_template") or _mob.get("elite_base_template") or _mob_id
    for _zone in _spawn_zones.get(_base, set()) | _spawn_zones.get(_mob_id, set()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("named", set()).update(_named_drops)


def loot_rarity_rank(item_id):
    item = ITEMS.get(item_id, {})
    return LOOT_RARITY_ORDER.get(str(item.get("rarity", "common")).lower(), 0)


def loot_filter_allows(mode, item_id):
    mode = str(mode or "all").lower()
    rank = loot_rarity_rank(item_id)
    if mode == "off":
        return False
    if mode == "rare+":
        return rank >= 1
    if mode == "epic+":
        return rank >= 2
    if mode == "legendary":
        return rank >= 3
    return True


HELP_TOPIC_ALIASES.update({
    "geody": "geody", "geodes": "geody", "geoda": "geody", "gemquality": "geody",
})
HELP_TOPICS["geody"] = [
    "Geody są rzadkim dodatkowym znaleziskiem podczas Górnictwa i trafiają do Sakwy Górnika.",
    "Geoda Kamienna: Kilof 20+, głębokość 10+; Kryształowa: 80+/60+; Astralna: 160+/150+.",
    "geody / geodes - pokaż posiadane geody.",
    "open geode / otwórz geodę / otworz geode - otwórz najlepszą posiadaną geodę; możesz podać jej nazwę.",
    "Jakości klejnotów: Surowy -> Czysty -> Doskonały -> Perfekcyjny. Wyższa jakość daje mocniejszy bonus po szlifowaniu.",
]
if "gornictwo" in HELP_TOPICS:
    HELP_TOPICS["gornictwo"].append("Kilof 20+ może znajdować geody; wpisz geody albo open geode / otwórz geodę.")
if "profesje" in HELP_TOPICS:
    HELP_TOPICS["profesje"].append("Wędka/Kilof/Piła/Sierp rozwijają się obecnie 1-600; dawna część krzywej 1-400 pozostaje zachowana, a 401-600 jest jej dalszą progresją.")

COMMAND_ALIASES.update({
    "bestiariusz": "bestiary", "bestiary": "bestiary",
    "postep": "progress", "postęp": "progress", "progress": "progress",
    "eksploracja": "exploration", "exploration": "exploration",
    "osiagniecia": "achievements", "osiągnięcia": "achievements",
    "achievement": "achievements", "achievements": "achievements",
    "tytuly": "titles", "tytuły": "titles", "titles": "titles",
    "tytul": "title", "tytuł": "title", "title": "title",
    "kolekcja": "collection", "collection": "collection",
    "collectioncodex": "collection", "collection_codex": "collection",
    "historiadropow": "drophistory", "historiadropów": "drophistory",
    "drophistory": "drophistory", "dropy": "drophistory",
    "lootfilter": "lootfilter", "filtrlootu": "lootfilter",
    "regionprogress": "regionprogress", "postepregionu": "regionprogress",
})

