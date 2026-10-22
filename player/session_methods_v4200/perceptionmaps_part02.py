# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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

            mercenary = self.visible_mercenary_for_look_v1226(query)
            if mercenary:
                owner, role, spec = mercenary
                progress = self.server.db.mercenary_progress_v1220(owner.account_id, role)
                from systems.mercenary_growth_v1220 import mercenary_owner_level_v1228
                await self.send(
                    f"{spec['name']}, {spec['role']}, poziom {mercenary_owner_level_v1228(owner.character)}. "
                    f"Najemnik towarzyszy postaci {owner.character.name}. "
                    f"Specjalizacja: {progress['specialization'] or 'brak'}."
                )
                return

            companion = self.visible_companion_for_look_v1801(query)
            if companion:
                owner, kind, name, hp, maximum, level, stance = companion
                await self.send(
                    f'{name}. Przywołany pomocnik postaci {owner.character.name}. '
                    f'Poziom {level}, HP {hp}/{maximum}, rozkaz: {stance}. '
                    'Walczy automatycznie i podąża za właścicielem.'
                )
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
        from systems.adventure_codex_v1270 import dungeon_floor_event_v1270
        from core.mines_threat import crypt_floor_number, mythic_crypt_floor_number
        _crypt_floor_v1270 = crypt_floor_number(self.character.room_id)
        _mythic_floor_v1270 = mythic_crypt_floor_number(self.character.room_id)
        _event_v1270 = dungeon_floor_event_v1270(
            _mythic_floor_v1270 or _crypt_floor_v1270 or 0,
            'Mityczna Krypta' if _mythic_floor_v1270 else 'Krypta')
        if _event_v1270:
            await self.send('ODKRYCIE PIĘTRA: ' + _event_v1270)
        from core.mine_tunnels import mine_tunnel_coords, MINE_DIRECTION_LABELS
        mine_pos_v1251 = mine_tunnel_coords(self.character.room_id, self.account_id)
        if mine_pos_v1251:
            opened_v1251 = self.server.db.mine_tunnel_directions_v1251(
                self.account_id, *mine_pos_v1251)
            if opened_v1251:
                await self.send('Twoje wykopane kierunki: ' +
                    ', '.join(MINE_DIRECTION_LABELS[d] for d in opened_v1251) + '.')
        # A ship is visible while its owner is present in a port or at sea.
        if hasattr(self, "ocean_port_name_v1000") and self.ocean_port_name_v1000(self.character.room_id):
            owned_accounts = {
                row[0] for row in self.server.db.conn.execute(
                    "SELECT account_id FROM ocean_ship_v1000 WHERE owned=1"
                )
            }
            ships = sorted(
                session.character.name
                for session in self.server.sessions
                if session.character
                and session.character.room_id == self.character.room_id
                and session.account_id is not None
                and session.account_id in owned_accounts
            )
            if ships:
                await self.send("Statki stoją przy nabrzeżu: " + ", ".join(ships) + ".")
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
        # v3.00.4: informacja o learn tylko w sali nauczyciela
        # jednej z AKTYWNYCH klas postaci (NVDA / look).
        _local_teacher_id, _local_teacher = self.teacher_here_for_active_class()
        if _local_teacher:
            await self.send(
                f"Nauczyciel klasy {_local_teacher['teacher_class']}: "
                "wpisz learn, aby zobaczyc lekcje, wymagania i ceny; "
                "learn <numer> albo learn <nazwa>, aby nauczyc sie skilla."
            )

        followers = self.nearby_mercenaries_v1226()
        if followers:
            mine = [spec["name"] for owner, _role, spec in followers if owner is self]
            others = [
                f"{spec['name']} ({spec['role']}, przy {owner.character.name})"
                for owner, _role, spec in followers if owner is not self
            ]
            if mine:
                await self.send(mercenary_follow_notice_v12210(mine))
            if others:
                await self.send("Najemnicy innych graczy: " + ", ".join(others) + ".")

        from systems.visible_companions_v1801 import nearby_companions_v1801
        companions = nearby_companions_v1801(self.server, self.character.room_id)
        if companions:
            mine = [f'{name} ({hp}/{maximum} HP)' for owner, _kind, name, hp, maximum, _lvl, _stance in companions if owner is self]
            others = [f'{name} ({owner.character.name}, {hp}/{maximum} HP)' for owner, _kind, name, hp, maximum, _lvl, _stance in companions if owner is not self]
            if mine:
                await self.send('Twoje przywołane istoty: ' + ', '.join(mine) + '.')
            if others:
                await self.send('Przywołania innych graczy: ' + ', '.join(others) + '.')

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
                + ("Masz klucz. Wpisz skrzynia lub odklucz." if _has_key else "Zamknięta. Klucz wypada z ciała bossa tego piętra.")
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

        # v12.00.6: explicitly identify downed party allies for NVDA.
        # Never confuse an unrelated player with a party member.
        _my_party = self.party_key()
        others = [
            (session.character.name + " (POWALONY — można wskrzesić)"
             if (_my_party is not None and session.party_key() == _my_party
                 and session.is_downed_v0371()) else session.character.name)
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
                    f"{index}. {info['name']} — etap {info['stage']}/{CHARACTER_MAX_LEVEL}; "
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
                f"REGION {index}: {info['name']}. Biom {info['biome']}; etap bazowy {info['stage']}/{CHARACTER_MAX_LEVEL}. "
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
            f"Lokacja: {room.get('name') or 'Nieznana lokacja'}. Strefa: {room.get('zone', 'brak')}."
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
                    f", boss do około {int(boss_power)}/{CHARACTER_MAX_LEVEL}"
                    if boss_power is not None else ""
                )
                exits.append(
                    f"{base}{zone_text}, zagrożenie {threat_label}, zwykły próg około "
                    f"{target_power}/{CHARACTER_MAX_LEVEL}{boss_text}"
                )
            else:
                exits.append(base)
        # v0.71.9: NVDA/client compatibility. Some clients do not reliably expose
        # every line from one multiline send(). First announce every direction in
        # one short line, then send each exit as a separate message so no direction
        # can disappear from the accessibility buffer.
        direction_labels = [self.route_direction_name(direction) for direction in room["exits"]]
        await self.send("Kierunki: " + ", ".join(direction_labels) + ".")
        await self.send("Wyjścia:")
        for exit_line in exits:
            await self.send(exit_line)


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

