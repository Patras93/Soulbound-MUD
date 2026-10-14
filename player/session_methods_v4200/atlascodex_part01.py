# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def item_runtime_description(self, item_id, item):
        desc = str(item.get("desc") or "").strip()
        if desc:
            return desc
        if item.get("crypt_set_tier") and item.get("crypt_base_item") != item_id:
            tier = int(item.get("crypt_set_tier", 0) or 0)
            rarity = str(item.get("rarity_name") or item.get("rarity") or "")
            affix = CRYPT_AFFIXES.get(item.get("affix"), item.get("affix") or "brak")
            amount = int(item.get("affix_amount", 0) or 0)
            defense = int(item.get("defense", 0) or 0)
            return (f"Ekwipunek z Krypty. Tier {tier}. Rzadkość: {rarity}. "
                    f"Obrona +{defense}. Bonus: {affix} +{amount}. Zestaw Krypty Tier {tier}.")
        if item.get("corpse_random_variant") and item.get("corpse_material"):
            mastery = int(item.get("required_mastery", 1) or 1)
            defense = int(item.get("defense", 0) or 0)
            stats = ", ".join(
                f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                for stat, amount in (item.get("stats") or {}).items()
            ) or "brak"
            props = ", ".join(
                f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount}%"
                for prop, amount in (item.get("properties") or {}).items()
            ) or "brak"
            return (
                "Losowe materiałowe EQ z ciała przeciwnika. Materiał wyznacza poziom mocy, "
                f"a slot i wariant mają własny profil statów. Wymaga Levelu postaci {mastery}. "
                f"Obrona +{defense}. Statystyki: {stats}. Właściwości: {props}."
            )
        if item.get("class_shop_item") and item.get("required_class"):
            class_name = str(item.get("required_class") or "")
            mastery = max(1, int(item.get("required_mastery", 1) or 1))
            set_name = str(item.get("class_set_name") or "Klasowy")
            defense = int(item.get("defense", 0) or 0)
            stats = []
            if item.get("affix"):
                stats.append(f"{CLASS_SET_STAT_NAMES.get(item['affix'], item['affix'])} +{int(item.get('affix_amount', 0) or 0)}")
            for stat, amount in (item.get("stats") or {}).items():
                stats.append(f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}")
            stat_text = ", ".join(stats) if stats else "brak"
            return (
                f"Wyposażenie klasowe dla {class_name}. Linia: {set_name}. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Obrona +{defense}. Podstawowe statystyki EQ: {stat_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        return ""


def format_item_description(self, item_id, item):
        parts = [f"{item['name']}. Typ: {item.get('type', 'przedmiot')}.", self.item_runtime_description(item_id, item)]

        if item.get("type") == "armor":
            parts.append(
                f"Slot: {EQUIPMENT_SLOT_NAMES.get(item.get('slot'), item.get('slot', 'brak'))}. "
                f"Obrona fizyczna: +{item.get('defense', 0)}."
            )
            capacity = jewelry_socket_capacity(item)
            if capacity > 0:
                parts.append(
                    f"Gniazda na klejnoty: {capacity}."
                )
            if item.get("rarity_name"):
                parts.append(
                    f"Rzadkość: {item['rarity_name']}."
                )
            if item.get("required_class"):
                req_level = max(1, int(item.get("required_character_level", item.get("required_mastery", 1)) or 1))
                parts.append(
                    f"Wymagana aktywna klasa: {item['required_class']}. "
                    f"Wymagany Poziom postaci: {req_level}."
                )
            elif int(item.get("required_character_level", item.get("required_mastery", 1)) or 1) > 1:
                parts.append(
                    f"Wymagany Poziom postaci: {int(item.get('required_character_level', item.get('required_mastery', 1)) or 1)}."
                )
            if item.get("class_shop_item") and item.get("required_class"):
                class_name = item["required_class"]
                parts.append(
                    f"Część zestawu klasowego {class_name}: "
                    f"Zestaw {item.get('class_set_name', class_name)}. "
                    "Progi zestawu: 2, 4, 6 i 8 części."
                )
            if item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(
                    item["affix"], item["affix"]
                )
                parts.append(
                    f"Losowy bonus: {affix_name} "
                    f"+{item.get('affix_amount', 0)}."
                )
            if item.get("stats"):
                stats_text = ", ".join(
                    f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                    for stat, amount in item["stats"].items()
                )
                parts.append(f"Statystyki materiałowe: {stats_text}.")
                if int(item["stats"].get("dexterity", 0)) > 0:
                    parts.append(
                        "Zręczność zwiększa szansę na trafienie krytyczne: "
                        "10 daje 5 procent, 40 daje 20 procent, 80 daje 30 procent, "
                        "a dalszy przyrost maleje do limitu 35 procent."
                    )
            if item.get("properties"):
                properties_text = ", ".join(
                    f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount:g}%"
                    for prop, amount in item["properties"].items()
                )
                parts.append(f"Właściwości materiałowe: {properties_text}.")
            if item.get("corpse_material"):
                parts.append(
                    f"Materiał łupu: {item.get('corpse_material')}."
                )
            if item.get("crypt_set_tier"):
                parts.append(
                    f"Zestaw Krypty Tier "
                    f"{item['crypt_set_tier']}."
                )
        elif item.get("type") == "tool":
            tool = "Wędka" if item.get("tool_type") == "fishing" else "Kilof"
            parts.append(f"Narzędzie profesji: {tool}. Ma własny poziom 1-600 i osobny XP.")
        elif "heal" in item:
            parts.append(f"Leczenie: {item['heal']} HP.")
        elif "soul_xp" in item:
            parts.append(f"Po użyciu daje {item['soul_xp']} Soul XP.")

        if item.get("price") is not None:
            price_coins = self.shop_item_base_value_silver(item)
            parts.append("Cena kupna: " + currency_price_text(price_coins) + ".")

        if item.get("sell_silver") or item.get("sell_gold") or item.get("sell_mithril"):
            parts.append(
                "Wartość sprzedaży: "
                + currency_price_text(
                    item.get("sell_silver", 0),
                    item.get("sell_gold", 0),
                    item.get("sell_mithril", 0),
                )
                + "."
            )

        return " ".join(p for p in parts if p)


def room_special_features(self, room_id):
        features = []
        if room_id in RIVER_FISHING_ROOMS:
            features.append("łowisko rzeczne")
        if room_id in LAKE_FISHING_ROOMS:
            features.append("łowisko jeziorowe")
        if room_id in SEA_FISHING_ROOMS:
            features.append("łowisko morskie")
        if room_id in OCEAN_FISHING_ROOMS:
            features.append("łowisko oceaniczne")
        if is_mining_room(room_id):
            features.append("miejsce wydobycia")
            floor = mine_floor_number(room_id)
            if floor is not None:
                features.append(
                    f"Kopalnia Głębinowa poziom {floor}, bez górnego limitu"
                )
        if room_id in SHOPS:
            features.append("sklep")
        if v0160_npcs_in_room(room_id):
            features.append("NPC")
        if any(spawn_room == room_id for spawn_room, _ in MOB_SPAWNS):
            features.append("przeciwnicy")
        return features


def find_description_entry(self, mapping, query, name_field="name"):
        q = self.normalize_description_query(query)
        if not q:
            return None
        exact = []
        partial = []
        for key, value in mapping.items():
            name = value[name_field] if isinstance(value, dict) else str(value)
            nk = self.normalize_description_query(str(key))
            nn = self.normalize_description_query(name)
            if q == nk or q == nn:
                exact.append((key, value))
            elif q in nk or q in nn:
                partial.append((key, value))
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


def atlas_resource_requirement_rows(self, item_id):
        """Zwraca (miejsce, narzędzie, minimalny level) dla zasobu."""
        item = ITEMS.get(item_id, {})
        base_id = item.get("base_resource_id", item_id)
        rows = []

        # Specjalne miejsca są treścią świata; wymagany level zawsze pochodzi
        # z Generator Core przedmiotu, nigdy z osobnej tabeli liczb.
        field_places = {
            "field_grave_moss": ("Ogród Księżycowego Mchu, Stary Cmentarz", "Sierp"),
            "field_void_thorn": ("Ogród Cierni Pustki, Ruiny Kultystów", "Sierp"),
            "field_ironbark_root": ("Legowisko Bestii", "Piła"),
            "field_tomb_silver": ("Kopalnia Głębinowa", "Kilof"),
            "field_blind_sewer_eel": ("Czarny Kanał pod Miastem Dusz", "Wędka"),
            "field_frost_crystal_ore": ("Kopalnia Głębinowa", "Kilof"),
        }
        if base_id in field_places:
            place, tool = field_places[base_id]
            generated = int(ITEMS.get(base_id, {}).get("generator_level", 1) or 1)
            return [(place, tool, generated)]


        fish_groups = (
            ("river", "Rzeka", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
            ("lake", "Jezioro", ("lake_shore",), LAKE_FISH_ATLAS),
            ("sea", "Morze", ("sea_pier",), SEA_FISH_ATLAS),
            ("ocean", "Ocean", ("ocean_platform",), OCEAN_FISH_ATLAS),
        )
        if base_id in FISH_RESOURCE_IDS:
            for habitat, label, rooms, ids in fish_groups:
                if base_id not in ids:
                    continue
                level = self.atlas_fish_min_level(base_id, habitat)
                if level is None:
                    continue
                places = ", ".join(
                    ROOMS[room_id]["name"] for room_id in rooms if room_id in ROOMS
                )
                if places:
                    rows.append((f"{label}: {places}", "Wędka", int(level)))
                # Profesyjny loch Wędkarstwa ma ograniczenie efektywnego levelu
                # do 10 punktów na każdą głębokość.
                if habitat == "sea":
                    grotto_floor = max(1, (int(level) + 9) // 10)
                    if grotto_floor <= 10:
                        rows.append((
                            f"Zatopiona Grota od głębokości {grotto_floor}",
                            "Wędka", int(level)
                        ))
                elif habitat == "ocean":
                    grotto_floor = max(11, (int(level) + 9) // 10)
                    if grotto_floor <= 20:
                        rows.append((
                            f"Zatopiona Grota od głębokości {grotto_floor}",
                            "Wędka", int(level)
                        ))
            return rows

        if base_id in WOOD_RESOURCE_IDS:
            for room_id, level_map in WOOD_ATLAS_ROOM_MIN_LEVELS.items():
                level = level_map.get(base_id)
                if level is not None and room_id in ROOMS:
                    rows.append((ROOMS[room_id]["name"], "Piła", int(level)))
            deep_level = WOOD_ATLAS_ROOM_MIN_LEVELS.get("deep_grove", {}).get(base_id)
            if deep_level is not None:
                forest_floor = max(1, (int(deep_level) + 9) // 10)
                rows.append((
                    f"Pradawny Las od ostępu {forest_floor}",
                    "Piła", int(deep_level)
                ))
            return sorted(rows, key=lambda row: (row[2], self.normalize_description_query(row[0])))

        if base_id in HERB_RESOURCE_IDS:
            for room_id, level_map in HERB_ATLAS_ROOM_MIN_LEVELS.items():
                level = level_map.get(base_id)
                if level is not None and room_id in ROOMS:
                    rows.append((ROOMS[room_id]["name"], "Sierp", int(level)))
            deep_level = HERB_ATLAS_ROOM_MIN_LEVELS.get("deep_grove", {}).get(base_id)
            if deep_level is not None:
                garden_floor = max(1, (int(deep_level) + 9) // 10)
                rows.append((
                    f"Ogród Alchemika od sektora {garden_floor}",
                    "Sierp", int(deep_level)
                ))
            return sorted(rows, key=lambda row: (row[2], self.normalize_description_query(row[0])))

        if base_id in ORE_RESOURCE_IDS:
            level = int(ORE_ATLAS_LEVELS.get(base_id, 1))
            floor_min = int(ORE_MINE_FLOOR_MINIMUMS.get(base_id, 1))
            rows.append((f"Kopalnia Głębinowa od poziomu {floor_min}", "Kilof", level))
            return rows

        return rows


def atlas_group_level(self, item_id, kind, key):
        item = ITEMS.get(item_id, {})
        base_id = item.get("base_resource_id", item_id)
        if kind == "fish":
            return self.atlas_fish_min_level(base_id, key)
        if kind == "wood":
            rooms = {
                "beginner": ("lumberjack_camp", "meadow"),
                "forest": ("whisper_grove", "old_road"),
                "deep": ("deep_grove",),
            }.get(key, ())
            levels = [
                WOOD_ATLAS_ROOM_MIN_LEVELS.get(room_id, {}).get(base_id)
                for room_id in rooms
            ]
        elif kind == "herb":
            rooms = {
                "meadow": ("herbalist_hut", "meadow", "flower_meadow"),
                "water": ("riverbank", "lake_shore", "lakeside_meadow"),
                "forest": ("whisper_grove", "old_road"),
                "deep": ("deep_grove",),
            }.get(key, ())
            levels = [
                HERB_ATLAS_ROOM_MIN_LEVELS.get(room_id, {}).get(base_id)
                for room_id in rooms
            ]
            # Tematyczne łąki należą do sekcji łąk; nie obniżają
            # wymagań tego samego zioła w lesie, nad wodą ani w Głębi Gaju.
            if key == "meadow":
                for room_id, herb_id in HERB_SPECIFIC_MEADOWS.items():
                    if herb_id == base_id:
                        levels.append(1)
        else:
            return None
        levels = [int(value) for value in levels if value is not None]
        return min(levels) if levels else None


async def send_atlas_group_with_levels(
        self, title, location_text, item_ids, kind, key, tool_name, chunk_size=12
    ):
        entries = []
        for item_id in sorted(
            item_ids,
            key=lambda value: self.normalize_description_query(ITEMS[value]["name"]),
        ):
            level = self.atlas_group_level(item_id, kind, key)
            if level is None:
                entries.append(ITEMS[item_id]["name"])
            else:
                entries.append(f"{ITEMS[item_id]['name']} [{tool_name} {level}+]")
        await self.send(f"{title}. Miejsce: {location_text}. Gatunków/surowców: {len(entries)}.")
        if not entries:
            await self.send("Brak pozycji.")
            return
        chunk_size = max(1, int(chunk_size))
        total = (len(entries) + chunk_size - 1) // chunk_size
        for index in range(0, len(entries), chunk_size):
            part = index // chunk_size + 1
            await self.send(
                f"{title}, część {part} z {total}: "
                + ", ".join(entries[index:index + chunk_size])
                + "."
            )


async def send_complete_atlas_list(
        self, title, item_ids, chunk_size=20
    ):
        names = sorted(
            (ITEMS[item_id]["name"] for item_id in item_ids),
            key=self.normalize_description_query,
        )
        await self.send(
            f"{title}. Łącznie pozycji: {len(names)}."
        )
        if not names:
            await self.send("Brak pozycji.")
            return

        chunk_size = max(1, int(chunk_size))
        total_parts = (
            len(names) + chunk_size - 1
        ) // chunk_size

        for index in range(0, len(names), chunk_size):
            part = index // chunk_size + 1
            chunk = names[index:index + chunk_size]
            await self.send(
                f"Część {part} z {total_parts}: "
                + ", ".join(chunk)
                + "."
            )


async def show_profession_atlas_v1602(self, query=""):
        """A live registry-backed index, not a copied 600-level recipe list."""
        from core.progression_600 import PROFESSION_MAX_LEVEL, TOOL_MAX_LEVEL
        from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
        from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
        from systems.professions import V03053_CRAFT_RECIPES, V1215_ENCHANT_RECIPES
        from systems.equipment_crafting import (
            CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES,
        )
        from systems.content_registry import NPCS, QUESTS
        from core.classes_skills import ROOMS
        professions = {
            self.normalize_description_query(name): (name, tool, npc, action)
            for name, tool, npc, action in PROFESSION_QUEST_SPECS_V0700
        }
        lookup = self.normalize_description_query(query or "")
        if lookup in ("lista", "wszystkie", "all", ""):
            await self.send(
                f"ATLAS PROFESJI: {len(professions)} profesji. "
                f"Rozwój profesji 1-{PROFESSION_MAX_LEVEL}, narzędzi 1-{TOOL_MAX_LEVEL}; "
                "wyższy wymagany EXP od poziomu 50, bez obcinania nagród."
            )
            for name, tool, npc, action in PROFESSION_QUEST_SPECS_V0700:
                await self.send(f"{name}: atlas profesje {self.normalize_description_query(name)}.")
            await self.send("Atlas konkretnej profesji opisuje zadania, specjalistę, komendy i aktualny katalog receptur. Surowce: atlas rudy / ryby / drewno / zioła / geody.")
            return
        if lookup == "wedkarstwo" or lookup == "wedkarz":
            lookup = "wedkarstwo"
        if lookup not in professions:
            await self.send("Nie ma takiej profesji w atlasie. Użyj atlas profesje, żeby poznać wszystkie 14 nazw.")
            return
        name, tool, npc, action = professions[lookup]
        npc_info = NPCS.get(npc, {})
        specialist = npc_info.get("name", npc)
        room_id = npc_info.get("room", "")
        room_name = ROOMS.get(room_id, {}).get("name", "") if room_id else ""
        await self.send(f"ATLAS PROFESJI — {name.upper()}. Poziom 1-{PROFESSION_MAX_LEVEL}; narzędzie 1-{TOOL_MAX_LEVEL}.")
        await self.send(f"Cel: {action}. Specjalista: {specialist}" + (f", lokacja: {room_name}." if room_name else "."))
        await self.send("Postęp: profesje info / narzedzia info. Zadania: quest list <NPC> i zamowienia; zamowienie porzuc anuluje aktywny kontrakt. Nagrody EXP za czynności pozostają bez zmian.")
        commands = {
            "fishing": "low, low on, low off; atlas ryby i atlas ocean",
            "mining": "kop, kop on, kop off, kop north|south|east|west|up|down; atlas rudy i atlas geody; kopalnia",
            "woodcutting": "tnij, tnij on, tnij off; atlas drewno",
            "herbalism": "zbieraj, zbieraj on, zbieraj off; atlas zioła",
            "crafting": "craft <receptura> [ilość], przetop, receptury kowalstwo",
            "cooking": "gotuj <receptura>, receptury gotowanie",
            "alchemy": "warz <receptura>, receptury alchemia",
            "jewelcrafting": "jubilerstwo / szlifuj, receptury jubilerstwo",
            "tailoring": "szyj <receptura>, receptury krawiectwo",
            "leatherworking": "garbuj <receptura>, receptury garbarstwo",
            "carpentry": "stolarka <receptura>, receptury stolarstwo",
            "enchanting": "zaklinaj <slot> <typ> [poziom], receptury zaklinanie",
            "archaeology": "wykop, atlas odkrycia ruiny",
            "cartography_profession": "mapuj, atlas odkrycia regiony",
        }
        await self.send("Komendy: " + commands.get(tool, "profesje info") + ". Pomoc: help " + lookup + ".")
        recipes = []
        if tool == "crafting":
            recipes = [row for row in CRAFT_RECIPES.values()
                       if row.get("profession") in (None, "Kowalstwo")]
        elif tool == "woodcutting":
            recipes = [row for row in CRAFT_RECIPES.values()
                       if row.get("profession") == "Drwalstwo"]
        elif tool == "cooking":
            recipes = list(COOK_RECIPES.values())
        elif tool == "alchemy":
            recipes = list(ALCHEMY_RECIPES.values())
        elif tool == "jewelcrafting":
            recipes = list(JEWELCRAFT_RECIPES.values())
        elif tool == "enchanting":
            recipes = list(V1215_ENCHANT_RECIPES.values())
        elif tool in ("tailoring", "leatherworking", "carpentry"):
            recipes = [row for row in V03053_CRAFT_RECIPES.values() if row.get("profession") == name]
        if recipes:
            await self.send(f"Receptury katalogowe {name}: {len(recipes)}. Sprawdź pełne i aktualne wymagania: receptury {lookup}.")
            ordered = sorted(recipes, key=lambda r: (int(r.get("min_profession_level", r.get("min_level", 1)) or 1), str(r.get("name", ""))))
            samples = ordered[:2] + ordered[-3:] if len(ordered)>5 else ordered
            for row in samples:
                await self.send(f"Przykład: {row.get('name','Receptura')}, poziom {row.get('min_profession_level', row.get('min_level', 1))}.")
        else:
            await self.send("Ta profesja opiera się na zbieraniu lub odkrywaniu, a nie na katalogu wyrobów. Szczegóły: help " + lookup + ".")
        related = sum(
            1 for quest in QUESTS.values()
            if quest.get("required_profession") == name
            or quest.get("reward_profession") == name
            or quest.get("specialist_tool_type") == tool
        )
        await self.send(f"Powiązane zadania profesji w aktualnym katalogu: {related}. Zadania przyjęte i postęp sprawdzaj przez quest.")

