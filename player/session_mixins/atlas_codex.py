# -*- coding: utf-8 -*-
"""Descriptions, atlas, bestiary and world codex."""

class SessionAtlasCodexMixin:

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
                parts.append("Cena kupna: " + currency_reading_text(price_coins, 0, 0) + ".")

            if item.get("sell_silver") or item.get("sell_gold") or item.get("sell_mithril"):
                parts.append(
                    "Wartość sprzedaży: "
                    + currency_reading_text(
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

    def normalize_description_query(self, value):
            table = str.maketrans(
                "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
                "acelnoszzACELNOSZZ"
            )
            return value.strip().lower().translate(table)

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

    def atlas_fish_min_level(self, item_id, habitat):
            """Najniższy level Wędki, przy którym gatunek realnie trafia do puli."""
            item = ITEMS.get(item_id, {})
            base_id = item.get("base_resource_id", item_id)
            for level in range(1, TOOL_MAX_LEVEL + 1):
                if base_id in self.fishing_available_pool(level, habitat):
                    return level
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

    def atlas_item_locations(self, item_id):
            result = []
            seen = set()
            for place, _tool, _level in self.atlas_resource_requirement_rows(item_id):
                if place not in seen:
                    seen.add(place)
                    result.append(place)
            return result

    def atlas_resource_min_level(self, item_id):
            rows = self.atlas_resource_requirement_rows(item_id)
            if not rows:
                return None, None
            tool = rows[0][1]
            level = min(row[2] for row in rows)
            return tool, level

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

    def atlas_names(self, item_ids):
            return ", ".join(
                sorted(
                    (ITEMS[item_id]["name"] for item_id in item_ids),
                    key=str.lower,
                )
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

    async def show_atlas(self, query=""):
            q = self.normalize_description_query(query)

            if not q:
                await self.send("ATLAS SUROWCÓW")
                await self.send("Działy: ryby, drewno, rudy, geody, zioła.")
                await self.send(
                    "Atlas pokazuje teraz wymagany level profesji i prawdziwe miejsce występowania. "
                    "Użycie: atlas ryby, atlas rzeka, atlas drewno, atlas rudy, atlas geody, atlas zioła "
                    "albo atlas <nazwa surowca>."
                )
                return

            if q in ("ryby", "fish", "wedkarstwo"):
                await self.send(f"ATLAS RYB. Łącznie gatunków: {len(FISH_ATLAS_ALL)}.")
                groups = (
                    ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                    ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                    ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                    ("ocean", "OCEAN", ("ocean_platform",), OCEAN_FISH_ATLAS),
                )
                for habitat, title, rooms, items in groups:
                    places = ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                    await self.send_atlas_group_with_levels(
                        title, places, items, "fish", habitat, "Wędka", chunk_size=12
                    )
                if "field_blind_sewer_eel" in ITEMS:
                    await self.send("TERENOWA RYBA: Ślepy Węgorz Kanałowy [Wędka 30+; Czarny Kanał pod Miastem Dusz].")
                await self.send(
                    "Zatopiona Grota także zawiera ryby morskie i oceaniczne; dokładna minimalna głębokość jest podawana przy atlas <nazwa ryby>."
                )
                await self.send(
                    "Wpisz atlas <nazwa ryby>, aby usłyszeć dokładny minimalny level Wędki i wszystkie łowiska."
                )
                return

            fish_groups = {
                "rzeka": ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                "river": ("river", "RZEKA", ("riverbank", "stone_bridge"), RIVER_FISH_ATLAS),
                "jezioro": ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                "lake": ("lake", "JEZIORO", ("lake_shore",), LAKE_FISH_ATLAS),
                "morze": ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                "sea": ("sea", "MORZE", ("sea_pier",), SEA_FISH_ATLAS),
                "ocean": ("ocean", "OCEAN", ("ocean_platform",), OCEAN_FISH_ATLAS),
            }
            if q in fish_groups:
                habitat, title, rooms, items = fish_groups[q]
                places = ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                await self.send_atlas_group_with_levels(
                    title, places, items, "fish", habitat, "Wędka", chunk_size=12
                )
                return

            if q in ("drewno", "wood", "drwalstwo"):
                await self.send(f"ATLAS DREWNA. Łącznie rodzajów: {len(WOOD_ATLAS_ALL)}.")
                wood_groups = (
                    ("beginner", "OBÓZ DRWALA I SREBRNA ŁĄKA", ("lumberjack_camp", "meadow"), WOOD_BEGINNER_ATLAS),
                    ("forest", "GAJ SZEPTÓW I STARY TRAKT", ("whisper_grove", "old_road"), WOOD_FOREST_ATLAS),
                    ("deep", "GŁĘBIA GAJU", ("deep_grove",), WOOD_DEEP_ATLAS),
                )
                for key, title, rooms, items in wood_groups:
                    places = ", ".join(ROOMS[r]["name"] for r in rooms)
                    await self.send_atlas_group_with_levels(
                        title, places, items, "wood", key, "Piła", chunk_size=12
                    )
                if "field_ironbark_root" in ITEMS:
                    await self.send("TERENOWE DREWNO: Korzeń Żelaznokory [Piła 50+; Legowisko Bestii].")
                await self.send(
                    "Pradawny Las również korzysta z puli Głębi Gaju; wymagany ostęp zależy od levelu danego drewna."
                )
                await self.send(
                    "Wpisz atlas <nazwa drewna>, aby usłyszeć level Piły wymagany osobno w każdej lokacji."
                )
                return

            if q in ("rudy", "ruda", "ore", "gornictwo"):
                await self.send(f"ATLAS RUD. Łącznie rud i minerałów: {len(ORE_ATLAS_ALL)}.")
                entries = []
                for item_id in sorted(
                    ORE_ATLAS_ALL,
                    key=lambda value: (
                        ORE_ATLAS_LEVELS.get(value, 1),
                        self.normalize_description_query(ITEMS[value]["name"]),
                    ),
                ):
                    level = ORE_ATLAS_LEVELS.get(item_id, 1)
                    floor_min = ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1)
                    where = f"Kopalnia Głębinowa {floor_min}+"
                    entries.append(
                        f"{ITEMS[item_id]['name']} [Kilof {level}+; {where}]"
                    )
                chunk_size = 8
                total = (len(entries) + chunk_size - 1) // chunk_size
                for index in range(0, len(entries), chunk_size):
                    part = index // chunk_size + 1
                    await self.send(
                        f"RUDY, część {part} z {total}: "
                        + "; ".join(entries[index:index + chunk_size])
                        + "."
                    )
                if "field_tomb_silver" in ITEMS:
                    await self.send("RUDY SPECJALNE W TEJ SAMEJ KOPALNI: Srebro Grobowe [Kilof 80+; poziom 80+]; Ruda Lodowego Kryształu [Kilof 100+; poziom 100+].")
                gem_rows = []
                for definition in GEM_DEFINITIONS:
                    raw_id = f"raw_gem_{definition['key']}"
                    if raw_id in ITEMS:
                        gem_rows.append(
                            f"{ITEMS[raw_id]['name']} [Kilof {definition['mining_level']}+; głębokość {definition['min_floor']}+]"
                        )
                if gem_rows:
                    await self.send("KLEJNOTY Z GÓRNICTWA: " + "; ".join(gem_rows) + ".")
                    await self.send(
                        "Jakość klejnotu może być Surowa, Czysta, Doskonała lub Perfekcyjna. "
                        "Lepszy Kilof i wyższe Górnictwo zwiększają szansę wyższej jakości."
                    )
                await self.send(
                    "Geody: Kamienna [Kilof 20+, głębokość 10+], Kryształowa [80+/60+], "
                    "Astralna [160+/150+]. Wpisz atlas geody."
                )
                await self.send(
                    "Mithril nie jest rudą w Sakwie. Od Kilofa 80, Górnictwa 80 i poziomu kopalni 80 "
                    "może wypaść bezpośrednio jako waluta do wspólnego portfela. "
                    "Szansa rośnie od 0,5 procent do 2 procent na poziomie 600 i nie zastępuje zwykłej rudy."
                )
                return

            if q in ("geody", "geoda", "geode", "geodes"):
                await self.send("ATLAS GEOD.")
                for geode_id, cfg in GEODE_DEFINITIONS.items():
                    await self.send(
                        f"{cfg['name']} [Kilof {cfg['min_tool']}+; głębokość {cfg['min_floor']}+]. "
                        f"Może zawierać klejnoty do poziomu {cfg['max_gem_level']}."
                    )
                await self.send(
                    "Geody są dodatkowym rzutem Górnictwa i nie zastępują rudy ani zwykłego klejnotu. "
                    "Otwieranie: open geode / otwórz geodę."
                )
                return

            if q in ("ziola", "zioła", "herbs", "herb", "zielarstwo", "rosliny", "rośliny", "plants"):
                await self.send(f"ATLAS ZIÓŁ I ROŚLIN. Łącznie: {len(HERB_ATLAS_ALL)}.")
                herb_groups = (
                    ("meadow", "ŁĄKI I CHATA ZIELARKI", ("herbalist_hut", "meadow", "flower_meadow"), HERB_MEADOW_ATLAS),
                    ("water", "TERENY NAD WODĄ", ("riverbank", "lake_shore", "lakeside_meadow"), HERB_WATER_ATLAS),
                    ("forest", "GAJ SZEPTÓW I STARY TRAKT", ("whisper_grove", "old_road"), HERB_FOREST_ATLAS),
                    ("deep", "GŁĘBIA GAJU", ("deep_grove",), HERB_DEEP_ATLAS),
                )
                for key, title, rooms, items in herb_groups:
                    places = ", ".join(ROOMS[r]["name"] for r in rooms)
                    await self.send_atlas_group_with_levels(
                        title, places, items, "herb", key, "Sierp", chunk_size=12
                    )
                if "field_grave_moss" in ITEMS:
                    await self.send("TERENOWE ROŚLINY: Mech Nagrobny [Sierp 20+; Stary Cmentarz]; Cierń Pustki [Sierp 60+; Ruiny Kultystów].")
                dedicated = []
                for room_id, herb_id in HERB_SPECIFIC_MEADOWS.items():
                    if room_id in ROOMS and herb_id in ITEMS:
                        dedicated.append(f"{ITEMS[herb_id]['name']} — {ROOMS[room_id]['name']} [Sierp 1+]")
                if dedicated:
                    await self.send("ŁĄKI TEMATYCZNE: " + "; ".join(dedicated) + ".")
                await self.send(
                    "Ogród Alchemika również korzysta z puli Głębi Gaju; wymagany sektor zależy od levelu danego zioła."
                )
                await self.send(
                    "Wpisz atlas <nazwa zioła>, aby usłyszeć wszystkie lokacje i minimalny level Sierpa dla każdej z nich."
                )
                return

            resources = {
                item_id: ITEMS[item_id]
                for item_id in (
                    FISH_STORAGE_IDS
                    | ORE_STORAGE_IDS
                    | MINING_STORAGE_IDS
                    | WOOD_STORAGE_IDS
                    | HERB_STORAGE_IDS
                )
            }
            found = find_by_name(resources, query)
            if not found:
                # v0.8.75: prosta nazwa klejnotu (np. "diament") pasuje do kilku
                # jakości naraz. W takim wypadku atlas pokazuje wariant bazowy,
                # zamiast uznawać wyszukiwanie za niejednoznaczne. Konkretna jakość
                # nadal działa normalnie, np. "atlas czysty diament".
                q_lookup = normalize_lookup_text(query)
                gem_matches = []
                for definition in GEM_DEFINITIONS:
                    gem_names = (
                        definition["key"],
                        definition["raw_name"],
                        definition["cut_name"],
                        definition["raw_name"].replace("Surowy ", "", 1),
                        definition["cut_name"].replace("Szlifowany ", "", 1),
                    )
                    if any(
                        q_lookup == normalize_lookup_text(name)
                        for name in gem_names
                    ):
                        gem_matches.append(definition)
                if len(gem_matches) == 1:
                    base_gem_id = f"raw_gem_{gem_matches[0]['key']}"
                    found = (base_gem_id, ITEMS[base_gem_id])
            if not found:
                await self.send(
                    "Atlas nie rozpoznaje tego surowca. Wpisz atlas ryby, atlas drewno, atlas rudy, atlas geody albo atlas zioła."
                )
                return

            item_id, item = found
            base_id = item.get("base_resource_id", item_id)
            base_item = ITEMS.get(base_id, item)
            await self.send(f"ATLAS: {item['name']}.")
            if item.get("rare_resource_variant"):
                await self.send(f"Bazowy surowiec: {base_item['name']}.")
            if base_id in FISH_RESOURCE_IDS:
                await self.send("Typ: ryba. Trafia do Siatki na ryby.")
            elif base_id in WOOD_RESOURCE_IDS:
                await self.send("Typ: drewno. Trafia na Stos drewna.")
            elif base_id in HERB_RESOURCE_IDS:
                await self.send("Typ: zioło lub roślina. Trafia do Torby Zielarskiej.")
            elif item_id in RAW_GEM_IDS:
                await self.send("Typ: surowy klejnot Górnictwa. Trafia do Sakwy Górnika.")
            elif item_id in GEODE_IDS:
                await self.send("Typ: geoda Górnictwa. Trafia do Sakwy Górnika.")
            else:
                await self.send("Typ: ruda lub minerał. Trafia do Sakwy górniczej.")

            if item_id in RAW_GEM_IDS:
                gem_key = item.get("gem_key")
                definition = next((d for d in GEM_DEFINITIONS if d["key"] == gem_key), None)
                if definition:
                    quality = item.get("gem_quality", "raw")
                    await self.send(
                        f"Górnictwo: Kilof {definition['mining_level']}+; efektywna głębokość kopalni {definition['min_floor']}+. "
                        f"Jakość: {GEM_QUALITY_INFO.get(quality, GEM_QUALITY_INFO['raw'])['label']}. "
                        "Klejnot jest dodatkowym znaleziskiem obok normalnej rudy i trafia do Sakwy Górnika."
                    )
                    return
            if item_id in GEODE_IDS:
                cfg = GEODE_DEFINITIONS[item_id]
                await self.send(
                    f"Górnictwo: Kilof {cfg['min_tool']}+; efektywna głębokość {cfg['min_floor']}+. "
                    "Geoda jest dodatkowym znaleziskiem. Otwórz ją przez open geode / otwórz geodę."
                )
                return
            rows = self.atlas_resource_requirement_rows(base_id)
            if rows:
                tool, minimum = self.atlas_resource_min_level(base_id)
                await self.send(f"Minimalny wymagany poziom: {tool} {minimum}+.")
                for place, row_tool, level in rows:
                    await self.send(f"{place}: {row_tool} poziom {level}+.")
            else:
                await self.send("Brak danych o miejscu pozyskania tego surowca.")

    def codex_boss_ids(self):
            result = set()
            for mob_id, mob in MOB_TEMPLATES.items():
                if (
                    mob_id.startswith("crypt_boss_")
                    or mob_id.startswith("astral_boss_")
                    or mob_id.startswith("mythic_crypt_boss_")
                    or mob_id.startswith("mythic_astral_boss_")
                    or mob.get("world_boss")
                    or mob.get("boss_mechanic")
                ):
                    result.add(mob_id)
            return result

    def codex_relic_ids(self):
            cache = getattr(type(self).codex_relic_ids, "_v0717_cache", None)
            if not isinstance(cache, tuple) or cache[0] != len(ITEMS):
                result = frozenset(
                    item_id for item_id, item in ITEMS.items()
                    if (
                        item.get("boss_relic_floor") is not None
                        or item_id.startswith("astral_relic_")
                        or item.get("rarity") == "unique"
                    )
                )
                cache = (len(ITEMS), result)
                type(self).codex_relic_ids._v0717_cache = cache
            return set(cache[1])

    async def send_codex_name_list(
            self, title, names, chunk_size=20
        ):
            names = sorted(
                set(names),
                key=self.normalize_description_query,
            )
            await self.send(
                f"{title}. Łącznie: {len(names)}."
            )
            if not names:
                await self.send("Brak wpisów.")
                return

            chunk_size = max(1, int(chunk_size))
            total = (
                len(names) + chunk_size - 1
            ) // chunk_size
            for index in range(0, len(names), chunk_size):
                part = index // chunk_size + 1
                await self.send(
                    f"Część {part} z {total}: "
                    + ", ".join(
                        names[index:index + chunk_size]
                    )
                    + "."
                )

    def bestiary_spawn_room_ids(self, mob_template_id):
            base_id = canonical_bestiary_template_id(mob_template_id)
            return tuple(sorted(BESTIARY_SPAWN_ROOMS.get(base_id, ())))

    def bestiary_drop_lines(self, mob_template_id):
            base_id = canonical_bestiary_template_id(mob_template_id)
            template = MOB_TEMPLATES.get(base_id, {})
            result = []
            key_id = boss_key_for_template(template)
            if key_id and key_id in ITEMS:
                result.append(f"{ITEMS[key_id]['name']} — gwarantowany w ciele")
            for item_id, chance in sorted(
                (template.get("drops") or {}).items(),
                key=lambda row: normalize_lookup_text(ITEMS.get(row[0], {"name": row[0]}).get("name", row[0])),
            ):
                name = player_item_display_name_v0335(item_id)
                result.append(f"{name} — około {float(chance) * 100:.1f}%")
            return result

    async def show_bestiary(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            rows = self.server.db.bestiary_rows(self.account_id)
            known_ids = {str(row["mob_template_id"]) for row in rows}
            total_kills = sum(int(row["kills"]) for row in rows)
            total_entries = len(BESTIARY_CATALOG)
            unlocked = len(known_ids.intersection(BESTIARY_CATALOG))
            pct = int(unlocked * 100 / max(1, total_entries))

            if not raw:
                await self.send(
                    f"BESTIARIUSZ: {unlocked} z {total_entries} gatunków, {pct}%. "
                    f"Łączne zaliczone zabicia: {total_kills}."
                )
                await self.send(
                    "Pierwsze zabicie odblokowuje wpis. Elite i proceduralne Rare liczą się do bazowego gatunku, więc Bestiariusz nie wymaga tysięcy kopii affixów."
                )
                await self.send(
                    "Komendy: bestiariusz lista / bestiary list; bestiariusz rekordy / bestiary records; bestiariusz <mob> / bestiary <mob>."
                )
                return

            if norm in ("lista", "list", "odkryte", "unlocked"):
                if not rows:
                    await self.send("Bestiariusz jest pusty. Pokonaj pierwszego przeciwnika, aby odblokować wpis.")
                    return
                entries = []
                for row in rows:
                    mob_id = str(row["mob_template_id"])
                    if mob_id not in BESTIARY_CATALOG:
                        continue
                    entries.append((BESTIARY_CATALOG[mob_id], int(row["kills"])))
                entries.sort(key=lambda x: normalize_lookup_text(x[0]))
                await self.send(f"ODKRYTE WPISY BESTIARIUSZA: {len(entries)}.")
                chunk = []
                for name, kills in entries:
                    chunk.append(f"{name} ({kills})")
                    if len(chunk) >= 18:
                        await self.send(", ".join(chunk) + ".")
                        chunk = []
                if chunk:
                    await self.send(", ".join(chunk) + ".")
                return

            if norm in ("rekordy", "records", "record", "czasy", "times"):
                timed = [row for row in rows if row["fastest_kill_ms"] is not None and str(row["mob_template_id"]) in BESTIARY_CATALOG]
                timed.sort(key=lambda row: int(row["fastest_kill_ms"]))
                if not timed:
                    await self.send("Nie masz jeszcze zapisanych rekordów czasu zabicia.")
                    return
                await self.send("NAJLEPSZE CZASY BESTIARIUSZA:")
                for index, row in enumerate(timed[:20], 1):
                    mob_id = str(row["mob_template_id"])
                    await self.send(
                        f"{index}. {BESTIARY_CATALOG[mob_id]}: {int(row['fastest_kill_ms']) / 1000.0:.2f} s; zabicia {int(row['kills'])}."
                    )
                return

            unlocked_mapping = {
                mob_id: MOB_TEMPLATES[mob_id]
                for mob_id in known_ids
                if mob_id in MOB_TEMPLATES
            }
            found = find_by_name(unlocked_mapping, raw)
            if not found:
                # Distinguish an unknown name from a real but not-yet-killed creature
                all_found = find_by_name(
                    {mob_id: MOB_TEMPLATES[mob_id] for mob_id in BESTIARY_CATALOG}, raw
                )
                if all_found:
                    await self.send("Ten wpis Bestiariusza jest jeszcze nieodkryty. Najpierw pokonaj tego przeciwnika.")
                else:
                    await self.send("Bestiariusz nie rozpoznaje takiego przeciwnika.")
                return

            mob_id, template = found
            row = self.server.db.bestiary_entry(self.account_id, mob_id)
            if not row:
                await self.send("Ten wpis Bestiariusza jest jeszcze nieodkryty.")
                return
            kind = "boss" if (mob_id in BOSS_COLLECTION_CATALOG or v0863_is_boss_template(template)) else ("mini-boss" if template.get("mini_boss") else "zwykły przeciwnik")
            await self.send(f"BESTIARIUSZ: {template['name']}. Typ: {kind}.")
            fastest = row["fastest_kill_ms"]
            fastest_text = f"{int(fastest) / 1000.0:.2f} s" if fastest is not None else "brak zapisanego czasu"
            await self.send(f"Zabicia: {int(row['kills'])}. Rekord pokonania: {fastest_text}.")
            dtype = "magiczne" if template.get("damage_type") == "magic" else "fizyczne"
            await self.send(
                f"HP: {int(template.get('max_hp', 0))}. Bazowe obrażenia: {int(template.get('damage', 0))}. "
                f"Typ ataku: {dtype}. Odporności: {bestiary_resistance_text(template)}."
            )
            room_ids = self.bestiary_spawn_room_ids(mob_id)
            if room_ids:
                zones = sorted({ROOMS[rid]["zone"] for rid in room_ids if rid in ROOMS}, key=normalize_lookup_text)
                names = sorted({ROOMS[rid]["name"] for rid in room_ids if rid in ROOMS}, key=normalize_lookup_text)
                await self.send("Regiony występowania: " + ", ".join(zones) + ".")
                if len(names) <= 12:
                    await self.send("Lokacje: " + ", ".join(names) + ".")
                else:
                    await self.send("Lokacje: " + ", ".join(names[:12]) + f"; oraz {len(names) - 12} dalszych.")
            drops = self.bestiary_drop_lines(mob_id)
            if drops:
                await self.send("Dropy: " + "; ".join(drops) + ".")
            else:
                await self.send("Dropy specjalne: brak stałych wpisów; nadal może wystąpić materiałowe EQ z ciała zgodnie z siłą przeciwnika.")
            if template.get("boss_mechanic_text"):
                await self.send("Mechanika: " + str(template["boss_mechanic_text"]))

    async def show_world_codex(self, query=""):
            q = self.normalize_description_query(query)
            bosses = self.codex_boss_ids()
            normal_mobs = set(MOB_TEMPLATES) - bosses
            relics = self.codex_relic_ids()

            if not q:
                await self.send("CODEX ŚWIATA")
                await self.send(
                    f"Ryby: {len(FISH_RESOURCE_IDS)} gatunków bazowych. "
                    f"Rzadkie warianty ryb: "
                    f"{len(RARE_FISH_VARIANT_IDS)}."
                )
                await self.send(
                    f"Rośliny i zioła: {len(HERB_RESOURCE_IDS)} bazowych. "
                    f"Rzadkie warianty roślin: "
                    f"{len(RARE_HERB_VARIANT_IDS)}."
                )
                await self.send(
                    f"Drewno: {len(WOOD_RESOURCE_IDS)} bazowych rodzajów. "
                    f"Rzadkie warianty drewna: "
                    f"{len(RARE_WOOD_VARIANT_IDS)}."
                )
                await self.send(
                    f"Rudy i minerały: {len(ORE_RESOURCE_IDS)}. "
                    f"Rodzaje żył: {len(MINING_VEINS)}."
                )
                await self.send(
                    f"Zwykłe moby: {len(normal_mobs)}. "
                    f"Bossowie: {len(bosses)}. "
                    f"Relikty i unikalne trofea: {len(relics)}."
                )
                await self.send(
                    "Działy: codex ryby, codex rośliny, codex drewno, "
                    "codex rudy, codex warianty, codex moby, "
                    "codex bossowie, codex relikty."
                )
                await self.send(
                    "Możesz też wpisać codex <nazwa>, aby wyszukać "
                    "konkretny zasób, mob, bossa albo relikt."
                )
                return

            if q in ("ryby", "ryba", "fish"):
                await self.send_complete_atlas_list(
                    "CODEX RYB - GATUNKI BAZOWE",
                    FISH_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty każdego gatunku: "
                    "Albinos x2 wartości, Złoty okaz x4, "
                    "Olbrzymi okaz x3, Pradawny okaz x8."
                )
                await self.send(
                    "Szansa na rzadki wariant rośnie wraz z levelem "
                    "Wędki: około 8 do 12 procent."
                )
                return

            if q in (
                "rosliny", "rośliny", "ziola", "zioła",
                "herbs", "plants",
            ):
                await self.send_complete_atlas_list(
                    "CODEX ROŚLIN I ZIÓŁ - BAZOWE",
                    HERB_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty: Bujna x2 wartości, "
                    "Lśniąca x4, Pradawna x6, Legendarna x10."
                )
                await self.send(
                    "Szansa na wariant rośnie z levelem Sierpa."
                )
                return

            if q in ("drewno", "wood", "drzewa", "drzewo"):
                await self.send_complete_atlas_list(
                    "CODEX DREWNA - BAZOWE",
                    WOOD_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rzadkie warianty drzew: Bujne x2 wartości, "
                    "Pradawne x4, Kryształowe x6, Legendarne x10."
                )
                await self.send(
                    "Szansa na wariant rośnie z levelem Piły."
                )
                return

            if q in ("rudy", "ruda", "ore", "mineral", "mineraly"):
                await self.send_complete_atlas_list(
                    "CODEX RUD I MINERAŁÓW",
                    ORE_RESOURCE_IDS,
                    chunk_size=20,
                )
                await self.send(
                    "Rodzaje żył: Zwykła x1, Bogata x2, "
                    "Kryształowa x3, Legendarna x5 urobku."
                )
                await self.send(
                    "Im wyższy level Kilofa, tym większa szansa na "
                    "Bogate, Kryształowe i Legendarne żyły."
                )
                return

            if q in ("warianty", "rare", "rzadkie"):
                await self.send("CODEX RZADKICH WARIANTÓW")
                await self.send(
                    "Ryby: Albinos, Złoty okaz, Olbrzymi okaz, "
                    "Pradawny okaz."
                )
                await self.send(
                    "Drzewa i drewno: Bujne, Pradawne, "
                    "Kryształowe, Legendarne."
                )
                await self.send(
                    "Rośliny: Bujna, Lśniąca, Pradawna, Legendarna."
                )
                await self.send(
                    "Górnictwo: Zwykła, Bogata, Kryształowa "
                    "i Legendarna żyła."
                )
                return

            if q in ("moby", "mob", "potwory", "przeciwnicy"):
                await self.send_codex_name_list(
                    "CODEX MOBÓW",
                    (
                        MOB_TEMPLATES[mob_id]["name"]
                        for mob_id in normal_mobs
                    ),
                    chunk_size=20,
                )
                return

            if q in ("bossowie", "boss", "bosses"):
                await self.send_codex_name_list(
                    "CODEX BOSSÓW",
                    (
                        MOB_TEMPLATES[mob_id]["name"]
                        for mob_id in bosses
                    ),
                    chunk_size=20,
                )
                return

            if q in ("relikty", "relikt", "relic", "relics"):
                await self.send_codex_name_list(
                    "CODEX RELIKTÓW I TROFEÓW",
                    (
                        ITEMS[item_id]["name"]
                        for item_id in relics
                    ),
                    chunk_size=20,
                )
                return

            searchable_ids = set(FISH_STORAGE_IDS) | set(ORE_STORAGE_IDS) | set(WOOD_STORAGE_IDS) | set(HERB_STORAGE_IDS) | set(relics)
            searchable_items = {item_id: ITEMS[item_id] for item_id in searchable_ids if item_id in ITEMS}
            found = find_by_name(searchable_items, query)
            if found:
                item_id, item = found
                await self.send(f"CODEX: {item['name']}.")
                await self.send(item.get("desc", "Brak opisu."))
                if item.get("rare_resource_variant"):
                    base_id = item.get("base_resource_id")
                    base_name = ITEMS.get(
                        base_id, {"name": base_id}
                    )["name"]
                    await self.send(
                        f"Rzadki wariant: "
                        f"{item.get('rare_resource_label')}. "
                        f"Bazowy zasób: {base_name}. "
                        f"Mnożnik wartości: x"
                        f"{item.get('rare_value_multiplier', 1)}."
                    )
                places = self.atlas_item_locations(item_id)
                if places:
                    await self.send(
                        "Występowanie: "
                        + ", ".join(places)
                        + "."
                    )
                tool, minimum = self.atlas_resource_min_level(item_id)
                if tool is not None:
                    await self.send(
                        f"Minimalny wymagany poziom: {tool} {minimum}+. "
                        "Dokładne poziomy dla każdej lokacji: atlas "
                        f"{item['name']}."
                    )
                return

            found_mob = find_by_name(MOB_TEMPLATES, query)
            if found_mob:
                mob_id, mob = found_mob
                kind = (
                    "boss"
                    if mob_id in bosses
                    else "zwykły mob"
                )
                dtype = (
                    "magiczne"
                    if mob.get("damage_type") == "magic"
                    else "fizyczne"
                )
                await self.send(
                    f"CODEX: {mob['name']}. Typ: {kind}."
                )
                await self.send(
                    f"HP: {mob.get('max_hp', 0)}. "
                    f"Bazowe obrażenia: {mob.get('damage', 0)}. "
                    f"Typ obrażeń: {dtype}."
                )
                await self.send(
                    f"Nagrody: Soul XP {mob.get('soul_reward', 0)}, "
                    f"Class XP {mob.get('class_xp_reward', max(50, int(mob.get('stat_reward', 0)) * 10))}, "
                    f"Bazowy EXP każdej statystyki +{mob.get('stat_reward', 0)}."
                )
                rooms = sorted({
                    ROOMS[room_id]["name"]
                    for room_id, template_id in MOB_SPAWNS
                    if template_id == mob_id and room_id in ROOMS
                })
                if rooms:
                    await self.send("Występowanie: " + ", ".join(rooms) + ".")
                drops = [
                    f"{player_item_display_name_v0335(item_id)} około {int(chance * 100)} procent"
                    for item_id, chance in mob.get("drops", {}).items()
                ]
                if drops:
                    await self.send("Drop: " + ", ".join(drops) + ".")
                if mob.get("boss_mechanic_text"):
                    await self.send(
                        "Mechanika: "
                        + mob["boss_mechanic_text"]
                    )
                if kind == "boss":
                    await self.send(
                        "Boss ma fazy przy 75, 50 i 25 procent HP. "
                        "NVDA dostaje krótki komunikat przy każdej zmianie fazy."
                    )
                return

            await self.send(
                "Codex nie znalazł takiego wpisu. "
                "Wpisz codex bez argumentu, aby usłyszeć działy."
            )

    async def describe_target(self, query):
            q = query.strip()

            if not q:
                room = ROOMS[self.character.room_id]
                await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
                features = self.room_special_features(self.character.room_id)
                if features:
                    await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
                await self.show_exits()
                return

            normalized = self.normalize_description_query(q)

            normalized_systems = {
                self.normalize_description_query(k): v
                for k, v in SYSTEM_DESCRIPTIONS.items()
            }
            normalized_stats = {
                self.normalize_description_query(k): v
                for k, v in STAT_DESCRIPTIONS.items()
            }
            if normalized in normalized_stats:
                await self.send(normalized_stats[normalized])
                return
            if normalized in normalized_systems:
                await self.send(normalized_systems[normalized])
                return

            found = self.find_description_entry(ITEMS, q)
            if found:
                item_id, item = found
                await self.send(self.format_item_description(item_id, item))
                return

            found = self.find_description_entry(NPCS, q)
            if found:
                npc_id, npc = found
                room = ROOMS[npc["room"]]
                desc = NPC_DESCRIPTIONS.get(npc_id, npc.get("dialogue", ""))
                await self.send(f"{npc['name']}. {desc}")
                await self.send(f"Stała lokacja: {room['name']}.")
                if npc.get("quest"):
                    quest = QUESTS[npc["quest"]]
                    await self.send(f"Powiązane zadanie: {quest['name']}. {quest['description']}")
                return

            found = self.find_description_entry(MOB_TEMPLATES, q)
            if found:
                mob_id, mob = found
                dtype = "magiczne" if mob.get("damage_type") == "magic" else "fizyczne"
                await self.send(f"{mob['name']}. {MOB_DESCRIPTIONS.get(mob_id, '')}")
                await self.send(
                    f"HP: {mob['max_hp']}. Bazowe obrażenia: {mob['damage']}. Typ obrażeń: {dtype}."
                )
                await self.send(
                    "Nagroda podstawowa: "
                    + currency_reading_text(
                        mob.get("silver", 0), mob.get("gold", 0), mob.get("mithril", 0)
                    )
                    + f"; bazowy EXP każdej statystyki +{mob.get('stat_reward',0)}; "
                    + f"Soul XP +{mob.get('soul_reward',0)}."
                )
                drops = []
                for item_id, chance in mob.get("drops", {}).items():
                    drops.append(f"{player_item_display_name_v0335(item_id)} około {int(chance * 100)} procent")
                if drops:
                    await self.send("Możliwe dropy: " + ", ".join(drops) + ".")
                return

            found = self.find_description_entry(ROOMS, q)
            if found:
                room_id, room = found
                await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
                exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
                await self.send("Wyjścia: " + exits + ".")
                features = self.room_special_features(room_id)
                if features:
                    await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
                return

            found = self.find_description_entry(QUESTS, q)
            if found:
                quest_id, quest = found
                await self.send(
                    f"Zadanie: {quest['name']}. Zleca: {quest['giver']}. {quest['description']}"
                )
                rewards = []
                if quest.get("reward_stat_progress"):
                    rewards.append(f"{quest['reward_stat_progress']} EXP każdej statystyki")
                if quest.get("reward_profession_xp"):
                    rewards.append(
                        f"{quest['reward_profession_xp']} XP profesji {quest.get('reward_profession','')}"
                    )
                if quest.get("reward_tool_xp"):
                    tool = "Wędki" if quest.get("reward_tool_type") == "fishing" else "Kilofa"
                    rewards.append(f"{quest['reward_tool_xp']} XP {tool}")
                if (
                    quest.get("reward_silver")
                    or quest.get("reward_gold")
                    or quest.get("reward_mithril")
                ):
                    rewards.append(
                        currency_reading_text(
                            quest.get("reward_silver", 0),
                            quest.get("reward_gold", 0),
                            quest.get("reward_mithril", 0),
                        )
                    )
                for item_id, qty in quest.get("reward_items", {}).items():
                    rewards.append(f"{player_item_display_name_v0335(item_id)} x{qty}")
                if rewards:
                    await self.send("Nagrody: " + ", ".join(rewards) + ".")
                return

            race_map = {
                race[0]: {
                    "name": race[0], "desc": race[1],
                    "strength": race[2], "dexterity": race[3],
                    "constitution": race[4], "intelligence": race[5],
                    "willpower": race[6], "charisma": 10,
                }
                for race in RACES
            }
            found = self.find_description_entry(race_map, q)
            if found:
                _, race = found
                await self.send(f"Rasa: {race['name']}. {race['desc']}")
                await self.send(
                    f"Startowe statystyki: Siła {race['strength']}, "
                    f"Zręczność {race['dexterity']}, Kondycja {race['constitution']}, "
                    f"Inteligencja {race['intelligence']}, Siła Woli {race['willpower']}, "
                    f"Charyzma {race['charisma']}."
                )
                await self.send(
                    race_class_recommendation_text(race['name']) +
                    " To rekomendacja, nie ograniczenie wyboru klasy."
                )
                return

            class_map = {
                cls[0]: {"name": cls[0], "type": cls[1], "weapon": cls[2], "base": cls[3]}
                for cls in CLASSES
            }
            found = self.find_description_entry(class_map, q)
            if found:
                _, cls = found
                kind = "fizyczna" if cls["type"] == "physical" else "magiczna"
                await self.send(
                    f"Klasa: {cls['name']}. Typ: {kind}. {CLASS_DESCRIPTIONS.get(cls['name'], '')}"
                )
                await self.send(
                    f"Broń Duszy: {cls['weapon']}. Bazowa moc Broni Duszy: {cls['base']}."
                )
                await self.send("Rozwój klasy: wszystkie sześć statystyk rośnie automatycznie.")
                skills = CLASS_SKILLS.get(cls["name"], [])
                if skills:
                    await self.send(
                        "Umiejętności: " + "; ".join(
                            f"{s['name']} do nauki od Biegłości klasy {s['unlock']}" for s in skills
                        ) + "."
                    )
                return

            help_key = HELP_TOPIC_ALIASES.get(normalized, normalized)
            if help_key in HELP_TOPICS:
                await self.show_help(help_key)
                return

            await self.send(
                "Nie znalazłem takiego opisu. Spróbuj dokładniejszej nazwy albo wpisz help opisy."
            )

    async def show_name_declension(self):
            await self.send(f"ODMIANA IMIENIA: {self.character.name_nom}")
            await self.send(f"Mianownik: {self.character.name_nom}.")
            await self.send(f"Dopełniacz: {self.character.name_gen}.")
            await self.send(f"Celownik: {self.character.name_dat}.")
            await self.send(f"Biernik: {self.character.name_acc}.")
            await self.send(f"Narzędnik: {self.character.name_ins}.")
            await self.send(f"Miejscownik: {self.character.name_loc}.")
            await self.send(f"Wołacz: {self.character.name_voc}.")
