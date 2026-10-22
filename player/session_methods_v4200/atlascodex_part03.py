# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
                "Albinos x3 wartości, Złoty okaz x8, "
                "Olbrzymi okaz x5, Pradawny okaz x15."
            )
            await self.send(
                "Od ok. 4 procent najprostszych wariantów; najlepsze wymagają "
                "odpowiedniego poziomu Wędki, Wędkarstwa i gatunku. "
                "Pradawny okaz ma maksymalnie 0,12 procent szansy."
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
                "Rzadkie warianty: Bujna x3 wartości, "
                "Lśniąca x7, Pradawna x12, Legendarna x20."
            )
            await self.send(
                "Szansa na wariant zależy od poziomu Sierpa, Zielarstwa "
                "oraz jakości rośliny. Legendarna wymaga co najmniej poziomu 360."
            )
            return

        if q in ("drewno", "wood", "drzewa", "drzewo"):
            await self.send_complete_atlas_list(
                "CODEX DREWNA - BAZOWE",
                WOOD_RESOURCE_IDS,
                chunk_size=20,
            )
            await self.send(
                "Rzadkie warianty drzew: Bujne x3 wartości, "
                "Pradawne x7, Kryształowe x12, Legendarne x20."
            )
            await self.send(
                "Szansa na wariant zależy od Piły, Drwalstwa oraz jakości drewna. "
                "Legendarne wymaga co najmniej poziomu 360."
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
                "Szanse zależą od Kilofa, Górnictwa i głębokości. "
                "Legendarna żyła wymaga poziomu 180 i ma najwyżej 0,65 procent szansy."
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
                    f"{quest['reward_profession_xp']} bazowego XP profesji {quest.get('reward_profession','')} (wypłata skalowana)"
                )
            if quest.get("reward_tool_xp"):
                tool = "Wędki" if quest.get("reward_tool_type") == "fishing" else "Kilofa"
                rewards.append(f"{quest['reward_tool_xp']} bazowego XP {tool} (wypłata skalowana)")
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

