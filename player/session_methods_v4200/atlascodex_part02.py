# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def show_atlas(self, query=""):
        q = self.normalize_description_query(query)

        discovery_roots = (
            "odkrycia", "odkrycie", "globalny", "globalny atlas",
            "discovery", "discoveries", "world discovery",
        )
        if q in discovery_roots:
            await self.show_global_discovery_atlas_v1120("")
            return
        for prefix in ("odkrycia ", "odkrycie ", "globalny ", "discovery ", "discoveries "):
            if q.startswith(prefix):
                raw = str(query or "").strip()
                rest = raw.split(maxsplit=1)[1] if " " in raw else ""
                await self.show_global_discovery_atlas_v1120(rest)
                return

        if q in ("profesje", "profesja", "zawody", "jobs"):
            await self.show_profession_atlas_v1602("")
            return
        for prefix in ("profesje ", "profesja ", "jobs "):
            if q.startswith(prefix):
                await self.show_profession_atlas_v1602(q[len(prefix):])
                return
        if q in (
            "gornictwo", "drwalstwo", "zielarstwo", "gotowanie", "alchemia",
            "kowalstwo", "jubilerstwo", "krawiectwo", "garbarstwo", "stolarstwo",
            "zaklinanie", "archeologia", "kartografia",
        ):
            await self.show_profession_atlas_v1602(q)
            return

        if not q:
            await self.send("ATLAS")
            await self.send("Działy: odkrycia świata, profesje (14), ryby, drewno, rudy, geody, zioła.")
            await self.send(
                "Globalny Atlas: atlas odkrycia regiony / miasta / lochy / wyspy / superbossy. "
                "Profesje: atlas profesje lub atlas profesje <nazwa>. Surowce: atlas ryby, atlas rzeka, "
                "atlas drewno, atlas rudy, atlas geody, atlas zioła albo atlas <nazwa surowca>."
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
        # Legendary bestiary: progressively reveal real authored combat data.
        from systems.adventure_codex_v1270 import bestiary_knowledge_v1270
        for text in bestiary_knowledge_v1270(template, int(row['kills'])):
            await self.send(text)
        if template.get("boss_mechanic_text"):
            await self.send("Mechanika: " + str(template["boss_mechanic_text"]))

