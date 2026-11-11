# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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


async def discover_instance_secret(self, args=""):
        # v1.19.0: czytelne podkomendy, bez zmiany starego odkrywania.
        if str(args or "").strip():
            await self.world_secrets_command_v1190(args)
            return
        inside = secret_room_identity_v1190(self.character.room_id)
        if inside:
            role, kind, floor = inside
            if role == "archive":
                await self.send("Tajemniczy NPC czeka w archiwum. Wpisz rozmawiaj <imię> lub sekret wydarzenie. Wyjścia: zachód, dół.")
            elif role == "vault":
                await self.send("LEGENDARNY SKARBIEC. Pokonaj strażnika, użyj sekret dziedzictwo, a skrzynię otwórz komendą skrzynia. Wyjście: południe.")
            else:
                await self.send("Sekretna komnata strażnika. Skarbiec jest tutaj. Aby dostać się do archiwum, pokonaj strażnika i idź na wschód. W dół wrócisz na to samo piętro.")
            return
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
                await self.sync_global_discovery_atlas_v1120(announce=True)
                await self.send(
                    f"ODKRYWASZ SEKRET: {surface['name']}. Ukryte przejście zostało zapamiętane. "
                    "Wpisz sekret ponownie, aby wejść do środka."
                )
            return

        if v0140_secret_room_identity(self.character.room_id):
            await self.send("Jesteś w ukrytej komnacie rubieży. Możesz porozmawiać z tajemniczym NPC, sprawdzić sekret wydarzenie lub zejść w dół, aby wrócić.")
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
            if self.combat_mob_key:
                await self.send("Najpierw zakończ walkę, aby przejść przez sekretne drzwi.")
                return
            chamber = secret_room_id_v1190(kind, floor)
            if not self.server.world.ensure_runtime_room(chamber):
                await self.send(f"Sekret zapisany, ale komnata jest chwilowo niedostępna: {name}.")
                return
            await self.send(f"Otwierasz ukryte przejście: {name}. Wracasz na to samo piętro przez wyjście w dół.")
            # Unrecognized direction avoids erroneously moving the party up
            # an existing dungeon stair. Each player unlocks this secret.
            await self.walk_room_transition("secret", chamber, guided=False, show_room=True)


async def world_secrets_command_v1190(self, args=""):
        raw = self.normalize_description_query(str(args or "").strip())
        inside = secret_room_identity_v1190(self.character.room_id)
        if raw in ("pomoc", "help", "?", "komendy"):
            await self.send("Sekrety: sekret (odkryj lub wejdź), sekret trop, sekret lista, sekret wydarzenie, w skarbcu: sekret dziedzictwo. W komnacie: otwórz skrzynię; w archiwum: rozmawiaj <imię>. Nie ma losowych pułapek.")
            return
        if raw in ("lista", "odkryte", "historia"):
            found = []
            for kind in INSTANCE_MAP_DEFS:
                for row in self.server.db.instance_secret_rows(self.account_id, kind):
                    found.append((kind, int(row["floor"]), str(row["secret_name"])))
            found.sort(key=lambda item: (item[0], item[1]))
            await self.send(f"SEKRETY INSTANCJI: odkryto {len(found)}. Ostatnie 20 na liście:")
            for kind, floor, name in found[-20:]:
                await self.send(f"{INSTANCE_MAP_DEFS[kind]['label']}, piętro {floor}: {name}.")
            return
        if raw in ("trop", "wskazowka", "wskazówka", "status"):
            surface = v0140_surface_secret_info(self.character.room_id)
            if surface:
                await self.send(f"TROP SEKRETU: {surface['name']}. Wpisz sekret, aby odkryć lub wejść.")
                return
            if inside:
                await self.send("Jesteś w sekrecie świata. Wpisz sekret bez argumentów, aby poznać dostępne możliwości.")
                return
            kind, floor = instance_room_identity(self.character.room_id)
            name = instance_secret_name(kind, floor) if kind and floor is not None else None
            await self.send(f"TROP SEKRETU: {name}. Wpisz sekret." if name else "W tej lokacji nie znajdujesz nowego tropu. Szukaj specjalnych pięter instancji i sekretów rubieży.")
            return
        if raw in ("dziedzictwo", "relikt", "receptura"):
            if not inside or inside[0] != "vault":
                await self.send("Zapomnianej receptury szukaj w Zakazanym Skarbcu na sekretnym piętrze lochu.")
                return
            guards = [mob for mob in self.server.world.room_mobs(self.character.room_id)
                      if mob.alive and MOB_TEMPLATES.get(mob.template_id, {}).get("v1250_vault_guard")]
            if guards:
                await self.send("Najpierw pokonaj strażnika skarbca, żeby poznać dziedzictwo.")
                return
            claimed = self.server.db.add_collection_entry(
                self.account_id, "legendary_vault_heritage_v12811", self.character.room_id)
            if not claimed:
                await self.send("Dziedzictwo tego skarbca zostało już przez ciebie odzyskane.")
                return
            self.server.db.add_item(self.account_id, "v12811_ancient_blueprint", 1)
            await self.record_item_collection("v12811_ancient_blueprint",
                                              source="Dziedzictwo legendarnego skarbca", announce=True)
            await self.send("O KURDE — LEGENDARNA RECEPTURA! Znajdujesz Zapis Zapomnianej Receptury. Trafia do plecaka."
                            " W Kuźni można z niego wykonać Relikt Odkrywcy wraz z czterema rzadkimi składnikami profesji.")
            return
        if raw in ("wydarzenie", "event", "znalezisko"):
            surface_room = v0140_secret_room_identity(self.character.room_id)
            if (not inside or inside[0] != "archive") and not surface_room:
                await self.send("Rzadkich wydarzeń szukaj w Archiwum Szeptów lub w ukrytych komnatach rubieży.")
                return
            today = datetime.now(timezone.utc).date()
            room_id = self.character.room_id
            if not world_secret_roll_v1190(room_id, today):
                await self.send("Archiwum dziś milczy. Nie ma tu aktywnego rzadkiego wydarzenia.")
                return
            event_id = f"{room_id}:{today.isoformat()}"
            if not self.server.db.add_collection_entry(self.account_id, "secret_events_v1190", event_id):
                await self.send("Odkryto już dzisiejszy ślad kronik w tym archiwum.")
                return
            if "soul_shard" in ITEMS:
                self.server.db.add_item(self.account_id, "soul_shard", 1)
                await self.record_item_collection("soul_shard", source="Archiwum Szeptów", announce=True)
                await self.send("RZADKIE WYDARZENIE: odnajdujesz Odłamek Duszy. Trafił do ekwipunku.")
            else:
                await self.send("RZADKIE WYDARZENIE: odkrywasz dawną inskrypcję. Zapisano odkrycie.")
            return
        await self.send("Nieznana opcja. Wpisz sekret pomoc.")


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
        await self.send(
            "Skrzynia Bossa stoi tylko w dokładnym pokoju bossa checkpointu, "
            "nie przy zejściu ani w innych pokojach piętra. Klucz jest w ciele "
            "bossa. Po otwarciu skrzynia znika aż do kolejnego zabicia tego bossa."
        )
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
        await self.send(
            "Skrzynia Bossa stoi tylko w dokładnym pokoju bossa checkpointu. "
            "Klucz jest w ciele tego bossa; po otwarciu skrzynia znika aż do "
            "kolejnego zabicia bossa."
        )
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

