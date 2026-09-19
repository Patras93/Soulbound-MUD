# -*- coding: utf-8 -*-
"""Soulbound v0.30.47 Session mixin: perception_maps."""

class SessionPerceptionMapsMixin:
    def visible_player_for_look(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            exact = []
            partial = []
            for session in self.server.sessions:
                if (
                    not session.character
                    or session.character.room_id != self.character.room_id
                ):
                    continue
                normalized = self.normalize_description_query(
                    session.character.name
                )
                if wanted == normalized:
                    exact.append(session)
                elif wanted in normalized:
                    partial.append(session)

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def visible_npc_for_look(self, query):
            current = v0160_npcs_in_room(self.character.room_id)
            return self.find_description_entry(current, query)

    def visible_mob_for_look(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            exact = []
            partial = []
            for mob in self.server.world.room_mobs(
                self.character.room_id
            ):
                template = MOB_TEMPLATES[mob.template_id]
                name = self.normalize_description_query(
                    template["name"]
                )
                template_id = self.normalize_description_query(
                    mob.template_id
                )
                entry = (mob, template)
                if wanted in {name, template_id}:
                    exact.append(entry)
                elif wanted in name or wanted in template_id:
                    partial.append(entry)

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    def visible_item_for_look(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            candidates = {}

            for row in self.server.db.inventory(self.account_id):
                item_id = row["item_id"]
                item = ITEMS.get(item_id)
                if not item:
                    continue
                entry = candidates.setdefault(
                    item_id,
                    {
                        "item": item,
                        "quantity": 0,
                        "equipped": [],
                        "shop": False,
                    },
                )
                entry["quantity"] += int(row["quantity"])

            for row in self.server.db.equipment(self.account_id):
                item_id = row["item_id"]
                item = ITEMS.get(item_id)
                if not item:
                    continue
                entry = candidates.setdefault(
                    item_id,
                    {
                        "item": item,
                        "quantity": 0,
                        "equipped": [],
                        "shop": False,
                    },
                )
                entry["equipped"].append(row["slot"])

            for item_id in self.current_shop_offers():
                item = ITEMS.get(item_id)
                if not item:
                    continue
                entry = candidates.setdefault(
                    item_id,
                    {
                        "item": item,
                        "quantity": 0,
                        "equipped": [],
                        "shop": False,
                    },
                )
                entry["shop"] = True

            exact = []
            partial = []
            for item_id, entry in candidates.items():
                item = entry["item"]
                normalized_id = self.normalize_description_query(item_id)
                normalized_name = self.normalize_description_query(
                    item.get("name", item_id)
                )
                result = (item_id, entry)

                if wanted in {normalized_id, normalized_name}:
                    exact.append(result)
                elif (
                    wanted in normalized_id
                    or wanted in normalized_name
                ):
                    partial.append(result)

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    async def look_at_player(self, session):
            character = session.character
            classes = character.active_class_names()
            await self.send(f"{character.name}. Gracz.")
            await self.send(
                f"Rasa: {character.race}. "
                f"Klasa: {', '.join(classes)}. "
                f"Soul Level {character.soul_level}. "
                f"Soul Tier {character.soul_tier}."
            )
            await self.send(
                f"Broń Duszy: {character.soul_weapon}."
            )
            if character.active_title:
                await self.send(f"Tytuł: {character.active_title}.")

    async def look_at_npc(self, npc_id, npc):
            await self.send(f"{npc['name']}. NPC.")
            desc = NPC_DESCRIPTIONS.get(
                npc_id,
                npc.get("dialogue", ""),
            )
            if desc:
                await self.send(desc)

            quest_ids = []
            if npc.get("quest"):
                quest_ids.append(npc["quest"])
            quest_ids.extend(npc.get("quest_chain") or ())
            quest_ids.extend(npc.get("specialist_quests") or ())
            quest_ids = list(dict.fromkeys(quest_ids))

            if quest_ids:
                names = [
                    QUESTS[qid]["name"]
                    for qid in quest_ids
                    if qid in QUESTS
                ]
                if names:
                    await self.send(
                        "Powiązane zadania: "
                        + ", ".join(names)
                        + "."
                    )

    async def look_at_mob(self, mob, template):
            dtype = (
                "magiczne"
                if template.get("damage_type") == "magic"
                else "fizyczne"
            )
            await self.send(
                f"{template['name']}. Przeciwnik."
            )
            await self.send(
                f"HP: {mob.hp} z {template['max_hp']}. "
                f"Bazowe obrażenia: {template.get('damage', 0)}. "
                f"Typ obrażeń: {dtype}."
            )

            if template.get("rare_troll"):
                await self.send("Rzadki wariant trolla.")
            if template.get("rare_mob"):
                await self.send("Rzadki przeciwnik: zwiększone HP, obrażenia i nagrody.")

            if template.get("elite_affix_text"):
                await self.send(
                    "Elitarny affix: "
                    + template["elite_affix_text"]
                )

            if template.get("boss_mechanic_text"):
                await self.send(
                    "Mechanika: "
                    + template["boss_mechanic_text"]
                )

    async def look_at_item(self, item_id, entry):
            item = entry["item"]
            await self.send(
                self.format_item_description(item_id, item)
            )

            context = []
            quantity = int(entry.get("quantity", 0))
            if quantity > 0:
                context.append(f"Masz {quantity} szt.")

            for slot in entry.get("equipped", ()):
                context.append(
                    "Założony: "
                    + EQUIPMENT_SLOT_NAMES.get(slot, slot)
                )

            if entry.get("shop"):
                context.append(
                    "Dostępny w sklepie tej lokacji"
                )

            if context:
                await self.send(". ".join(context) + ".")

    async def look(self, query=""):
            # v0.9.12: po restarcie postać może być zapisana na proceduralnym
            # piętrze >200, którego nie pre-generujemy przy starcie serwera.
            self.server.world.ensure_runtime_room(self.character.room_id)
            _nemesis = self.server.db.nemesis_row_v029(self.account_id)
            if _nemesis and int(_nemesis["active"] or 0) and str(_nemesis["room_id"]) == str(self.character.room_id):
                self.server.world.ensure_v029_nemesis(_nemesis)
            query = str(query or "").strip()

            # v0.30.8: MUD/NVDA shorthand: `l dusza`, `sp dusza`, `spojrz dusza`.
            # Dusza jest interfejsem postaci, nie obiektem stojącym w pokoju.
            if query and normalize_lookup_text(query) in (
                "dusza", "soul", "bron duszy", "broń duszy", "soul weapon"
            ):
                await self.show_soul("")
                return

            if query:
                # v0.9.10: MUD-owe podglądanie zawartości ciała.
                # l in corpse / look in 2.corpse / l w 2.cialo
                in_match = re.match(r"^(?:in|inside|w|we)\s+(.+)$", query, flags=re.IGNORECASE)
                if in_match:
                    corpse_query = in_match.group(1).strip()
                    norm = normalize_lookup_text(corpse_query)
                    if norm in ("cialo", "zwloki", "body", "corpse"):
                        await self.show_corpses("")
                        return
                    corpse = self.server.world.find_corpse(
                        self.character.room_id, corpse_query
                    )
                    if corpse:
                        await self.show_corpses(corpse_query)
                        return

                player = self.visible_player_for_look(query)
                if player:
                    await self.look_at_player(player)
                    return

                npc = self.visible_npc_for_look(query)
                if npc:
                    npc_id, npc_data = npc
                    await self.look_at_npc(npc_id, npc_data)
                    return

                mob = self.visible_mob_for_look(query)
                if mob:
                    mob_state, template = mob
                    await self.look_at_mob(mob_state, template)
                    return

                item = self.visible_item_for_look(query)
                if item:
                    item_id, entry = item
                    await self.look_at_item(item_id, entry)
                    return

                await self.send(
                    "Nie widzisz tutaj takiego gracza, "
                    "NPC, przeciwnika ani przedmiotu."
                )
                return

            room = ROOMS[self.character.room_id]
            await self.send(
                f"{room['name']}. Strefa: {room['zone']}."
            )
            await self.send(room["desc"])
            profile_v025 = v0250_room_generator_profile(self.character.room_id)
            await self.send(
                f"Generator świata: {profile_v025['ambience']}; "
                f"punkt otoczenia: {profile_v025['feature']}."
            )
            identity_v015 = v0130_frontier_room_identity(self.character.room_id)
            if identity_v015:
                weather_v015 = v0150_weather_state(self.character.room_id)
                phase_v015 = v0150_time_state()
                await self.send(f"Pora: {phase_v015['label']}. Pogoda: {weather_v015['label']}.")
                season_v018 = v0180_season_state()
                await self.send(f"Sezon: {season_v018['label']}.")
                self.server.db.add_collection_entry(self.account_id, "weather_v015", f"{identity_v015[0]}:{weather_v015['weather']}")
                levent_v018 = v0180_legendary_event_for_room(self.character.room_id)
                if levent_v018:
                    await self.send(f"LEGENDARNE WYDARZENIE: {levent_v018['title']}. {levent_v018['desc']}")
                    self.server.db.add_collection_entry(self.account_id, "legendary_world_events_v018", levent_v018["token"])
            await self.discover_current_room(announce=True)
            event = v0140_event_for_room(self.character.room_id)
            if event:
                await self.send(f"AKTYWNE WYDARZENIE: {event['title']}. {event['desc']}")
                await self.register_v0140_world_event_visit(self.character.room_id)
            if room.get("v0140_surface_secret"):
                if self.character.room_id in self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140"):
                    await self.send("Znasz sekret tego sektora. Wpisz sekret, aby wejść do ukrytej lokacji.")
                else:
                    await self.send("W otoczeniu wyczuwasz nietypowy ślad. Możesz użyć sekret / secret.")

            npcs = [value["name"] for value in v0160_npcs_in_room(self.character.room_id).values()]
            if npcs:
                await self.send(
                    "NPC: " + ", ".join(npcs) + "."
                )

            mobs = self.server.world.room_mobs(
                self.character.room_id
            )
            if mobs:
                names = [
                    MOB_TEMPLATES[mob.template_id]["name"]
                    for mob in mobs
                ]
                await self.send(
                    "Przeciwnicy: "
                    + ", ".join(names)
                    + "."
                )

            _chest_opened = self.server.db.treasure_chest_opened_at(self.account_id, self.character.room_id)
            _chest_cfg, _chest_remaining = self.server.world.treasure_chest_status(self.character.room_id, _chest_opened)
            if _chest_cfg:
                if _chest_remaining <= 0:
                    await self.send(f"Skrzynia skarbów: {_chest_cfg['name']}. Gotowa. Wpisz skrzynia albo chest.")
                else:
                    await self.send(f"Skrzynia skarbów: {_chest_cfg['name']}. Pusta, odnowienie za około {_chest_remaining} sekund.")

            _boss_chest = self.boss_floor_chest_here()
            if _boss_chest:
                _kind, _floor, _power = _boss_chest
                _key = boss_floor_key_id(_kind, _floor)
                _has_key = self.server.db.item_qty(self.account_id, _key) > 0
                await self.send(
                    f"Skrzynia bossowa: {boss_floor_chest_name(_kind, _floor)}. "
                    + ("Masz klucz. Wpisz unlock albo odklucz." if _has_key else "Zamknięta. Klucz wypada z ciała bossa tego piętra.")
                )

            corpses = self.server.world.room_corpses(
                self.character.room_id
            )
            if corpses:
                numbered = ", ".join(
                    f"{number}. {corpse.mob_name}"
                    for number, corpse in enumerate(corpses, 1)
                )
                await self.send(
                    "Ciała: " + numbered + ". "
                    "Wpisz ciało, l in 2.corpse albo przeszukaj 2.cialo."
                )

            if self.crypt_descent_blocked_for_player(
                self.character.room_id
            ):
                boss = self.server.world.live_crypt_boss(
                    self.character.room_id
                )
                if boss:
                    await self.send(
                        f"Zejście niżej blokuje boss: "
                        f"{MOB_TEMPLATES[boss.template_id]['name']}."
                    )

            others = [
                session.character.name
                for session in self.server.sessions
                if (
                    session is not self
                    and session.character
                    and session.character.room_id
                    == self.character.room_id
                )
            ]
            if others:
                await self.send(
                    "Gracze tutaj: "
                    + ", ".join(
                        sorted(others, key=str.lower)
                    )
                    + "."
                )

            await self.show_exits()

    async def show_global_generator_v025(self, args=""):
            query = normalize_lookup_text(args or "").strip()
            if query in ("logika", "world logic", "geografia", "geography"):
                audit = WORLD_LOGIC_AUDIT
                await self.send(
                    f"WORLD LOGIC VALIDATOR v{audit.get('version')}. Lokacje: {audit.get('room_count')}. "
                    f"Osiągalne z Placu Dusz: {audit.get('reachable_from_square')}. "
                    f"Powrót do Placu Dusz: {audit.get('returnable_to_square')}. "
                    f"Przejścia między strefami: {audit.get('cross_zone_edges')}. "
                    f"Błędy: {audit.get('error_count')}; ostrzeżenia: {audit.get('warning_count')}."
                )
                return
            if query in ("topologia", "world topology", "swiat", "świat"):
                audit = WORLD_TOPOLOGY_AUDIT
                await self.send(f"UNIVERSAL WORLD TOPOLOGY GENERATOR v{audit.get('version')}. Wygenerowane strefy: {audit.get('zone_count')}. Wygenerowane dawne statyczne lokacje: {audit.get('generated_room_count')}. Błędy: {audit.get('error_count')}.")
                return
            if query in ("miasto", "city", "miasto dusz"):
                audit = WORLD_TOPOLOGY_AUDIT
                city = audit.get("zones", {}).get("Miasto Dusz", {})
                await self.send(f"MIASTO DUSZ — topologia generowana. Lokacje: {audit.get('city_room_count')}. Połączenia wewnętrzne: {audit.get('city_internal_links')}. Maksymalna głębokość od Placu Dusz: {city.get('max_depth', 0)}. Seed świata: {audit.get('seed')}.")
                return
            if query in ("regiony", "regions", "regiony proceduralne", "procedural regions"):
                await self.send("PROCEDURALNE REGIONY ŚWIATA")
                for index in sorted(V028_PROCEDURAL_REGIONS):
                    info = V028_PROCEDURAL_REGIONS[index]
                    boss_level = int(MOB_TEMPLATES[info["boss"]].get("generator_level", info["stage"]) or info["stage"])
                    quest_levels = [int(QUESTS[qid].get("generator_level", info["stage"]) or info["stage"]) for qid in info["quests"]]
                    await self.send(
                        f"{index}. {info['name']} — etap {info['stage']}/400; "
                        f"sektory {len(info['rooms'])}; sekrety {len(info['secrets'])}; "
                        f"miejsca zasobów {len(info['resource_rooms'])}; boss około Level {boss_level}; "
                        f"questy {quest_levels[0]}/{quest_levels[1]}/{quest_levels[2]}."
                    )
                await self.send("Szczegóły: generator region <numer>. Wejście do Bram Ekspedycji znajduje się na wschód od Pracowni Kartografa.")
                return
            if query.startswith("region ") or query.startswith("region_"):
                raw = query.split()[-1] if " " in query else query.rsplit("_", 1)[-1]
                try:
                    index = int(raw)
                except ValueError:
                    index = 0
                info = V028_PROCEDURAL_REGIONS.get(index)
                if not info:
                    await self.send(f"Nie ma takiego regionu. Dostępne numery: 1-{len(V028_PROCEDURAL_REGIONS)}.")
                    return
                theme = V028_BIOMES[info["biome"]]
                boss = MOB_TEMPLATES[info["boss"]]
                elite = MOB_TEMPLATES[info["elite"]]
                rare = MOB_TEMPLATES[info["rare"]]
                await self.send(
                    f"REGION {index}: {info['name']}. Biom {info['biome']}; etap bazowy {info['stage']}/400. "
                    f"Sektory {len(info['rooms'])}, sekrety {len(info['secrets'])}, miejsca zasobów {len(info['resource_rooms'])}."
                )
                resource_labels = {
                    "wood": "drewno", "herb_forest": "zioła leśne", "herb_water": "zioła wodne",
                    "herb_meadow": "zioła łąkowe", "fish_river": "ryby rzeczne", "fish_sea": "ryby morskie",
                    "fish_lake": "ryby jeziorne", "fish_ocean": "ryby oceaniczne",
                }
                resources_text = ", ".join(resource_labels.get(tag, str(tag)) for tag in theme["resources"])
                await self.send(
                    f"Zasoby biomu: {resources_text}. "
                    f"Elite: {elite['name']} Level {elite['generator_level']}; "
                    f"Rare: {rare['name']} Level {rare['generator_level']}; "
                    f"boss: {boss['name']} Level {boss['generator_level']}."
                )
                await self.send("Questy: " + "; ".join(
                    f"{QUESTS[qid]['name']} — Level {QUESTS[qid]['generator_level']}" for qid in info["quests"]
                ) + ".")
                return
            room_id = self.character.room_id
            self.server.world.ensure_runtime_room(room_id)
            room = ROOMS.get(room_id, {})
            profile = v0250_room_generator_profile(room_id)
            await self.send(
                f"GLOBAL GENERATOR 2.0. Seed serwera: {V0250_WORLD_SEED_ID}. "
                f"Lokacja: {room.get('name', room_id)}. Strefa: {room.get('zone', 'brak')}."
            )
            await self.send(
                f"Profil lokacji: {profile['ambience']}; punkt otoczenia: {profile['feature']}; "
                f"wariant {profile['variant']}."
            )
            floor = mine_floor_number(room_id)
            if floor is not None:
                mine_profile = v0250_mine_floor_profile(floor)
                await self.send(
                    f"Generator Kopalni: poziom {floor}; {mine_profile['shape']}; "
                    f"{mine_profile['strata']}; {mine_profile['sign']}."
                )
            inst = v0100_instance_spec(room_id)
            if inst:
                dungeon_profile = v0250_instance_floor_profile(inst['kind'], inst['floor'])
                await self.send(
                    f"Generator lochu: {dungeon_profile['layout']}; motyw: {dungeon_profile['motif']}."
                )

            applicable = []
            if room_id in FISHING_ROOMS:
                applicable.append(("fishing", "Wędkarstwo"))
            if is_mining_room(room_id):
                applicable.append(("mining", "Górnictwo"))
            if room_id in WOODCUTTING_ROOMS:
                applicable.append(("woodcutting", "Drwalstwo"))
            if room_id in HERBALISM_ROOMS:
                applicable.append(("herbalism", "Zielarstwo"))
            active = []
            for tool, label in applicable:
                hotspot = v0250_gather_hotspot(room_id, tool)
                if hotspot.get("label"):
                    active.append(f"{label}: {hotspot['label'].replace('Global Generator: ', '')}")
            if active:
                await self.send("Aktywne hotspoty: " + "; ".join(active) + ".")
            elif applicable:
                await self.send("Hotspoty profesji: obecnie brak lokalnego bonusu.")
            else:
                await self.send("Hotspoty profesji: ta lokacja nie jest miejscem zbieractwa.")
            await self.send(
                "Pozostałe generatory: proceduralne biomy, lochy i megalochy, dynamiczne questy, "
                "bounty/kontrakty, wydarzenia świata, pogoda, sezony, sekrety, skarby oraz warianty rare/elite."
            )

    async def show_exits(self, args=""):
            room = ROOMS[self.character.room_id]
            if not room["exits"]:
                await self.send("Wyjścia: brak.")
                return
            normalized = self.normalize_room_query(args) if args else ""
            detailed = normalized in ("info", "pelne", "pełne", "full", "cele", "targets")
            exits=[]
            for direction, target_id in room["exits"].items():
                # Lazy/runtime destinations (np. dalsze piętra) są materializowane tylko
                # po to, by NVDA mogło przeczytać prawdziwą nazwę celu zamiast surowego room_id.
                if target_id not in ROOMS:
                    world = getattr(self.server, "world", None)
                    if world is not None:
                        world.ensure_runtime_room(target_id)
                target = ROOMS.get(target_id, {})
                target_name = str(target.get("name") or str(target_id).replace("_", " "))
                direction_name = self.route_direction_name(direction)
                base = f"{direction_name}: {target_name}"

                target_level = int(target.get("recommended_mastery", 0) or 0)
                character_level = max(1, int(getattr(self.character, "character_level", 1) or 1))
                if target_level and character_level < target_level:
                    exits.append(
                        f"{base}, trudny teren, zalecany Level postaci {target_level}; wejście dozwolone"
                    )
                elif self.giant_fortress_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    exits.append(
                        f"{base}, zablokowane przez bossa Twierdzy Gigantów"
                    )
                elif self.crypt_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    exits.append(f"{base}, zablokowane przez bossa Krypty")
                elif self.astral_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    exits.append(f"{base}, zablokowane przez bossa Wieży")
                elif self.astral_entry_blocked(target_id):
                    exits.append(
                        f"{base}, wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}"
                    )
                elif detailed:
                    target_zone = target.get("zone", "")
                    zone_text = f", strefa {target_zone}" if target_zone else ""
                    fallback = 1
                    target_area = self.exp_area_for_room(target_id)
                    if target_area:
                        fallback = int(EXP_AREA_TARGET_POWER.get(target_area.get("id"), 1))
                    threat_profile = v0866_room_threat_profile(target_id, fallback=fallback)
                    target_power = int(threat_profile["target"])
                    boss_power = threat_profile.get("boss_max")
                    danger_power = max(
                        target_power,
                        int(boss_power) if boss_power is not None else target_power,
                    )
                    threat_label = v0866_threat_label(
                        danger_power, self.character_progression_power()
                    )
                    boss_text = (
                        f", boss do około {int(boss_power)}/400"
                        if boss_power is not None else ""
                    )
                    exits.append(
                        f"{base}{zone_text}, zagrożenie {threat_label}, zwykły próg około "
                        f"{target_power}/400{boss_text}"
                    )
                else:
                    exits.append(base)
            # v0.30.28: compatibility/NVDA mode. Send one simple multiline block
            # instead of a long punctuation-heavy sentence. Some MUD clients only
            # announced the local echo ("ex") and skipped the old formatted line.
            await self.send("Wyjścia:\r\n" + "\r\n".join(exits))

    async def show_instance_map_summary(self):
            await self.send("MAPY INSTANCJI")
            any_seen = False
            for kind, info in INSTANCE_MAP_DEFS.items():
                visited = self.server.db.instance_visited_floors(self.account_id, kind)
                if not visited:
                    continue
                any_seen = True
                highest = max(visited)
                start, end = instance_sector_bounds(kind, highest)
                sector_count = sum(1 for floor in visited if start <= floor <= end)
                pct = int(sector_count * 100 / 100)
                secrets = self.server.db.instance_secret_rows(self.account_id, kind)
                checkpoints = self.server.db.instance_checkpoint_floors(self.account_id, kind)
                await self.send(
                    f"{info['label']}: najwyższe piętro {highest}; sektor {start}-{end}: "
                    f"{sector_count} z 100, {pct}%; sekrety {len(secrets)}; "
                    f"checkpointy {len(checkpoints)}."
                )
            if not any_seen:
                await self.send("Nie masz jeszcze zapisanej mapy żadnej instancji.")
            else:
                await self.send("Szczegóły: mapa instancja <nazwa>. W instancji sama komenda mapa pokazuje jej bieżący sektor.")

    async def show_instance_map(self, kind_or_query="", floor=None):
            kind = kind_or_query if kind_or_query in INSTANCE_MAP_DEFS else normalize_instance_kind(kind_or_query)
            if not kind:
                kind, current_floor = instance_room_identity(self.character.room_id)
                if floor is None:
                    floor = current_floor
            if not kind or kind not in INSTANCE_MAP_DEFS:
                await self.send("Nie rozpoznaję instancji. Użyj mapa instancje, aby zobaczyć odkryte instancje.")
                return
            visited = self.server.db.instance_visited_floors(self.account_id, kind)
            if not visited:
                await self.send(f"{INSTANCE_MAP_DEFS[kind]['label']}: nie odkryto jeszcze żadnego piętra.")
                return
            highest = max(visited)
            if floor is None:
                current_kind, current_floor = instance_room_identity(self.character.room_id)
                floor = current_floor if current_kind == kind and current_floor is not None else highest
            start, end = instance_sector_bounds(kind, int(floor))
            sector_visited = sorted(f for f in visited if start <= f <= end)
            pct = int(len(sector_visited) * 100 / 100)
            secret_rows = [
                row for row in self.server.db.instance_secret_rows(self.account_id, kind)
                if start <= int(row["floor"]) <= end
            ]
            secret_total = len(instance_secret_floors(kind, start))
            checkpoints = sorted(
                floor_value for floor_value in self.server.db.instance_checkpoint_floors(self.account_id, kind)
                if start <= floor_value <= end
            )
            info = INSTANCE_MAP_DEFS[kind]
            await self.send(
                f"MAPA INSTANCJI: {info['label']}. Sektor {start}-{end}. "
                f"Odkryto {len(sector_visited)} ze 100 pięter, {pct}%. "
                f"Najwyższe odwiedzone piętro: {highest}."
            )
            current_kind, current_floor = instance_room_identity(self.character.room_id)
            if current_kind == kind and current_floor is not None:
                await self.send(f"Aktualnie jesteś na piętrze {current_floor}.")
            if checkpoints:
                tail = checkpoints[-15:]
                await self.send("Zapamiętane checkpointy w sektorze: " + ", ".join(map(str, tail)) + ".")
            else:
                await self.send("Zapamiętane checkpointy w tym sektorze: brak.")
            await self.send(f"Sekrety sektora: odkryto {len(secret_rows)} z {secret_total}.")
            for row in secret_rows:
                await self.send(f"Sekret, piętro {int(row['floor'])}: {row['secret_name']}.")
            missing = 100 - len(sector_visited)
            if missing:
                await self.send(f"Nieodkryte piętra w sektorze: {missing}. Ich szczegóły pozostają ukryte.")
            await self.send("Komendy: mapa; mapa instancje; mapa instancja <nazwa>; sekret / secret.")

    async def discover_instance_secret(self):
            # v0.14.0: ta sama dostępna komenda obsługuje także sekrety powierzchni.
            surface = v0140_surface_secret_info(self.character.room_id)
            if surface:
                discovered = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
                if self.character.room_id in discovered:
                    hidden = surface["hidden_room"]
                    self.server.world.ensure_runtime_room(hidden)
                    await self.send(f"Otwierasz odkryte przejście: {surface['name']}.")
                    await self.walk_room_transition("up", hidden, guided=False, show_room=True)
                    return
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "surface_secrets_v0140", self.character.room_id
                )
                if is_new:
                    self.server.db.add_collection_entry(
                        self.account_id, "treasure_targets_v0140", self.character.room_id
                    )
                    await self.advance_v0140_quest_progress("discover_secret", surface["kind"], 1)
                    await self.advance_bounty("secret", surface["kind"], 1)
                    await self.advance_dynamic_world_quest_v015("secret", surface["kind"], 1)
                    self.server.db.add_collection_entry(self.account_id, "secrets_v015", self.character.room_id)
                    self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", self.character.room_id)
                    await self.v0260_check_museum_rewards(announce=True)
                    await self.send(
                        f"ODKRYWASZ SEKRET: {surface['name']}. Ukryte przejście zostało zapamiętane. "
                        "Wpisz sekret ponownie, aby wejść do środka."
                    )
                return

            if v0140_secret_room_identity(self.character.room_id):
                await self.send("Jesteś już wewnątrz odkrytej sekretnej lokacji. Zejdź w dół, aby wrócić.")
                return

            kind, floor = instance_room_identity(self.character.room_id)
            if not kind or floor is None:
                await self.send("Nie znajdujesz tutaj ukrytego punktu mapy.")
                return
            name = instance_secret_name(kind, floor)
            if not name:
                await self.send("Nie znajdujesz tutaj ukrytego punktu mapy.")
                return
            is_new = self.server.db.mark_instance_secret(self.account_id, kind, floor, name)
            if is_new:
                idx = instance_secret_index(kind, floor)
                if idx is not None:
                    self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", f"instance:{kind}:{idx}")
                    await self.v0260_check_museum_rewards(announce=True)
                await self.send(f"Odkrywasz sekret: {name}. Mapa instancji została zaktualizowana.")
            else:
                await self.send(f"Ten sekret jest już zapisany na mapie: {name}.")

    async def show_map(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)

            current_kind, current_floor = instance_room_identity(self.character.room_id)
            if norm in ("skarbu", "skarb", "treasure", "treasure map", "mapa skarbu", "mapy skarbow", "mapy skarbów"):
                await self.show_v0140_treasure_targets()
                return
            if norm in ("instancje", "instances", "instanceall", "dungeons"):
                await self.show_instance_map_summary()
                return
            if norm.startswith("instancja ") or norm.startswith("instance "):
                query = raw.split(maxsplit=1)[1] if len(raw.split(maxsplit=1)) > 1 else ""
                await self.show_instance_map(query)
                return
            explicit_kind = normalize_instance_kind(raw) if raw else None
            if explicit_kind:
                await self.show_instance_map(explicit_kind)
                return
            if current_kind and (not norm or norm in ("instancja", "instance", "biezaca", "bieżąca", "current")):
                await self.show_instance_map(current_kind, current_floor)
                return

            discovered = self.server.db.discovered_room_ids(self.account_id)
            current = self.character.room_id
            world_count = sum(1 for room_id in ALL_EXPLORATION_ROOMS if room_id in discovered)
            world_total = len(ALL_EXPLORATION_ROOMS)
            world_pct = int(world_count * 100 / max(1, world_total))

            if norm in ("all", "wszystko", "swiat", "world", "regiony", "regions"):
                await self.send(
                    f"MAPA ODKRYTEGO ŚWIATA: {world_count} z {world_total} lokacji, {world_pct}%."
                )
                for zone in sorted(EXPLORATION_ZONE_ROOMS, key=normalize_lookup_text):
                    count, total, pct = self.exploration_percent(zone)
                    if zone in TRACKED_EXPLORATION_ZONES:
                        claimed = self.server.db.exploration_reward_claimed(self.account_id, zone)
                        reward = "nagroda odebrana" if claimed else ("nagroda gotowa" if pct >= 100 else "nagroda przy 100%")
                    else:
                        reward = "mała strefa bez osobnej nagrody 100%"
                    marker = " [TU]" if ROOMS[current]["zone"] == zone else ""
                    await self.send(f"{zone}{marker}: {count} z {total}, {pct}%; {reward}.")
                return

            zone = ROOMS[current]["zone"]
            if raw and norm not in ("region", "strefa", "current", "biezacy", "bieżący"):
                candidates = {name: {"name": name} for name in EXPLORATION_ZONE_ROOMS}
                found = find_by_name(candidates, raw)
                if not found:
                    await self.send(
                        "Nie rozpoznaję takiego regionu mapy. Wpisz mapa all / map all, aby usłyszeć regiony."
                    )
                    return
                zone = found[0]

            zone_rooms = tuple(EXPLORATION_ZONE_ROOMS.get(zone, ()))
            known = [room_id for room_id in zone_rooms if room_id in discovered]
            pct = int(len(known) * 100 / max(1, len(zone_rooms)))
            await self.send(
                f"MAPA: {zone}. Odkryto {len(known)} z {len(zone_rooms)} lokacji, {pct}%. "
                f"Cały świat: {world_pct}%."
            )
            if zone in TRACKED_EXPLORATION_ZONES:
                claimed = self.server.db.exploration_reward_claimed(self.account_id, zone)
                if claimed:
                    await self.send("Nagroda za 100% tego regionu została odebrana.")
                elif pct >= 100:
                    await self.send("Region jest ukończony; nagroda 100% powinna zostać przyznana automatycznie przy odkryciu ostatniej lokacji.")
                else:
                    await self.send(
                        "Za 100% regionu otrzymasz Soul XP, walutę, unikalną Pamiątkę Odkrywcy, tytuł i osiągnięcie."
                    )

            if not known:
                await self.send("Nie masz jeszcze odkrytych lokacji w tym regionie.")
                return
            entries = []
            for room_id in sorted(known, key=lambda rid: normalize_lookup_text(ROOMS[rid]["name"])):
                marker = " [TU]" if room_id == current else ""
                entries.append(ROOMS[room_id]["name"] + marker)
            chunk_size = 24
            for offset in range(0, len(entries), chunk_size):
                await self.send("Odkryte: " + "; ".join(entries[offset:offset + chunk_size]) + ".")
            hidden = len(zone_rooms) - len(known)
            if hidden:
                await self.send(f"Nieodkryte lokacje w tym regionie: {hidden}. Ich nazwy pozostają ukryte.")
            await self.send("Komendy: mapa / map; mapa all / map all; mapa <region> / map <region>.")

    async def show_crypt_info(self):
            floor = crypt_floor_number(self.character.room_id)
            await self.send(
                "KRYPTA NIESKOŃCZONA: brak ostatniego piętra. "
                "Bossowie są co 10 pięter bez końca."
            )
            await self.send(
                "Boss co 10 pięter blokuje zejście tylko do pierwszego pokonania przez tę postać."
            )
            await self.send(
                "Po pierwszym zabiciu bossa próg zostaje zapisany jako zaliczony. "
                "Gdy boss odrodzi się, można go farmić, ale nie blokuje już zejścia."
            )
            await self.send(
                "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra oraz sam próg przejścia. "
                "Respawn bossa pozostaje opcjonalnym celem do farmienia."
            )
            await self.send(
                "Portal uruchamiasz komendą portal <piętro> w Sali Krypty "
                "albo w Przedsionku Krypty."
            )
            await self.send(
                "Zwykłe moby Krypty zostawiają 1 element ekwipunku na ciele, "
                "bossowie 3."
            )
            await self.send("Na każdym piętrze bossa co 10 stoi Skrzynia Bossa. Właściwy klucz jest gwarantowany w ciele bossa; bez klucza skrzyni nie otworzysz. Użyj unlock / odklucz.")
            await self.send(
                "Moby nie są agresywne. Nie atakują gracza same."
            )

            highest = self.crypt_portal()
            if highest:
                await self.send(
                    f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
                )
            else:
                await self.send("Portale Krypty: jeszcze brak.")

            if floor:
                await self.send(
                    f"Aktualne piętro Krypty: {floor}. Nie ma maksymalnego piętra."
                )
                boss = self.server.world.live_crypt_boss(
                    self.character.room_id
                )
                if boss:
                    await self.send(
                        f"Boss żyje i blokuje zejście: "
                        f"{MOB_TEMPLATES[boss.template_id]['name']}."
                    )
                elif is_crypt_boss_floor(floor):
                    await self.send(
                        "Boss tego piętra jest obecnie pokonany. "
                        "Możesz zejść niżej do czasu jego respawnu."
                    )

    async def show_astral_info(self):
            floor = astral_floor_number(self.character.room_id)
            await self.send(
                f"WIEŻA ASTRALNA: od poziomu {ASTRAL_MIN_FLOOR} bez górnego limitu. "
                f"Wejście wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}."
            )
            await self.send(
                "Klimat Wieży to gwiezdne szkło, mgławice, konstelacje i astralna energia."
            )
            await self.send(
                "Boss stoi co 10 poziomów i blokuje drogę w górę, dopóki żyje."
            )
            await self.send(
                "Pokonanie bossa odblokowuje trwały Astralny Portal do jego poziomu."
            )
            await self.send(
                "Astralny Portal działa przy Astralnej Bramie komendą "
                "astralportal <poziom>."
            )
            await self.send(
                "Zwykłe moby Wieży zostawiają 1 element Astralnego ekwipunku, "
                "bossowie 3. Bossowie mają także własne unikalne relikty."
            )
            await self.send("Co 10 poziomów przy bossie stoi Skrzynia Bossa. Klucz jest w ciele tego bossa; bez klucza skrzyni nie otworzysz. Użyj unlock / odklucz.")
            await self.send(
                "Moby i bossowie Wieży nie są agresywni."
            )

            highest = self.astral_portal()
            if highest:
                await self.send(
                    f"Najwyższy checkpoint Wieży: poziom {highest}."
                )
            else:
                await self.send("Checkpointy Wieży: jeszcze brak.")

            if floor is not None:
                await self.send(
                    f"Aktualny poziom Wieży Astralnej: {floor}."
                )
                boss = self.server.world.live_astral_boss(
                    self.character.room_id
                )
                if boss:
                    await self.send(
                        f"Boss żyje i blokuje drogę w górę: "
                        f"{MOB_TEMPLATES[boss.template_id]['name']}."
                    )
