# -*- coding: utf-8 -*-
"""Soulbound v1.00.0 - Ocean 2.0 session actions."""
from __future__ import annotations

import random
import time
from collections import deque

from core.classes_skills import ROOMS
from core.bootstrap_economy_professions import currency_reading_text
from systems.crafting_quality import player_item_display_name_v0335
from systems.economy_income_balance import v1138_activity_income
from world.ocean_expansion import ROUTES, PORTS, DEEP_OCEAN_ROOMS, TREASURE_ROOMS


class SessionOceanV1000Mixin:
    V1000_SHIP_BASE_COST = 25_000

    def ocean_economy_stage_v1138(self):
        try:
            mastery = int(self.highest_active_class_mastery())
        except Exception:
            mastery = 1
        return max(
            1,
            int(getattr(self.character, "character_level", 1) or 1),
            int(getattr(self.character, "soul_level", 1) or 1),
            mastery,
        )
    V1000_SHIP_MAX_LEVEL = 5

    def ocean_ship_row_v1000(self):
        row = self.server.db.conn.execute(
            "SELECT * FROM ocean_ship_v1000 WHERE account_id=?", (self.account_id,)
        ).fetchone()
        if row is None:
            self.server.db.conn.execute(
                "INSERT OR IGNORE INTO ocean_ship_v1000(account_id,owned,hull,sails,cargo,navigation) VALUES(?,0,1,1,1,1)",
                (self.account_id,),
            )
            self.server.db.conn.commit()
            row = self.server.db.conn.execute(
                "SELECT * FROM ocean_ship_v1000 WHERE account_id=?", (self.account_id,)
            ).fetchone()
        return row

    def ocean_ship_owned_v1000(self):
        return bool(int(self.ocean_ship_row_v1000()["owned"]))

    def ocean_ship_level_v1000(self, key):
        row = self.ocean_ship_row_v1000()
        return int(row[key]) if key in ("hull", "sails", "cargo", "navigation") else 0

    def ocean_port_name_v1000(self, room_id):
        for _key, (rid, label) in PORTS.items():
            if rid == room_id:
                return label
        return None

    def ocean_route_available_here_v1000(self):
        room_id = self.character.room_id
        out = []
        for key, route in ROUTES.items():
            if room_id in (route["origin"], route["destination"]):
                out.append((key, route))
        return out

    async def show_ship_v1000(self, args=""):
        args = str(args or "").strip().lower()
        row = self.ocean_ship_row_v1000()
        owned = bool(int(row["owned"]))
        if not args or args in ("info", "status"):
            if not owned:
                await self.send(
                    f"STATEK: nie posiadasz statku. Kupno kosztuje {currency_reading_text(self.V1000_SHIP_BASE_COST)}. Wpisz statek kup w porcie."
                )
                return
            await self.send(
                f"STATEK: Kadłub {row['hull']}/5, Żagle {row['sails']}/5, Ładownia {row['cargo']}/5, Nawigacja {row['navigation']}/5. "
                f"Rejsy {row['voyages']}, głębinowe połowy {row['deep_catches']}, skarby {row['treasures']}."
            )
            await self.send("Ulepszanie: statek ulepsz kadlub|zagle|ladownia|nawigacja.")
            return
        if args in ("kup", "buy"):
            if owned:
                await self.send("Masz już własny statek.")
                return
            if not self.ocean_port_name_v1000(self.character.room_id):
                await self.send("Statek możesz kupić wyłącznie w jednym z głównych portów Ocean 2.0.")
                return
            wallet = self.character_wallet_silver_value()
            if wallet < self.V1000_SHIP_BASE_COST:
                await self.send(f"Potrzebujesz {currency_reading_text(self.V1000_SHIP_BASE_COST)}.")
                return
            self.character.silver = wallet - self.V1000_SHIP_BASE_COST
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.conn.execute(
                "UPDATE ocean_ship_v1000 SET owned=1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
                (self.account_id,),
            )
            self.server.db.save_character(self.character)
            await self.send("Kupujesz własny statek. Kadłub, Żagle, Ładownia i Nawigacja zaczynają na poziomie 1.")
            return
        parts = args.split()
        if len(parts) == 2 and parts[0] in ("ulepsz", "upgrade"):
            aliases = {
                "kadlub":"hull", "kadłub":"hull", "hull":"hull",
                "zagle":"sails", "żagle":"sails", "sails":"sails",
                "ladownia":"cargo", "ładownia":"cargo", "cargo":"cargo",
                "nawigacja":"navigation", "navigation":"navigation",
            }
            key = aliases.get(parts[1])
            if not key:
                await self.send("Nieznany moduł. Użyj: kadlub, zagle, ladownia albo nawigacja.")
                return
            if not owned:
                await self.send("Najpierw kup statek.")
                return
            level = int(row[key])
            if level >= self.V1000_SHIP_MAX_LEVEL:
                await self.send("Ten moduł ma już maksymalny poziom 5.")
                return
            cost = 12_500 * (level + 1) * (level + 1)
            wallet = self.character_wallet_silver_value()
            if wallet < cost:
                await self.send(f"Ulepszenie na poziom {level+1} kosztuje {currency_reading_text(cost)}.")
                return
            self.character.silver = wallet - cost
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.conn.execute(
                f"UPDATE ocean_ship_v1000 SET {key}=?,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
                (level + 1, self.account_id),
            )
            self.server.db.save_character(self.character)
            labels = {"hull":"Kadłub", "sails":"Żagle", "cargo":"Ładownia", "navigation":"Nawigacja"}
            await self.send(f"{labels[key]} statku osiąga poziom {level+1}/5.")
            return
        await self.send("Użycie: statek, statek kup, statek ulepsz kadlub|zagle|ladownia|nawigacja.")

    async def sail_v1000(self, args=""):
        args = str(args or "").strip().lower()
        if not self.ocean_ship_owned_v1000():
            await self.send("Do żeglugi Ocean 2.0 potrzebujesz własnego statku. Wpisz statek kup w porcie.")
            return
        here = self.ocean_route_available_here_v1000()
        if not args or args in ("lista", "list", "info"):
            await self.send("TRASY MORSKIE DOSTĘPNE Z TEGO PORTU")
            if not here:
                await self.send("Nie jesteś w porcie startowym żadnej trasy. Użyj ex, aby dopłynąć do portu.")
                return
            nav = self.ocean_ship_level_v1000("navigation")
            hull = self.ocean_ship_level_v1000("hull")
            for key, route in here:
                status = "dostępna" if nav >= route["navigation_required"] and hull >= route["hull_required"] else "zablokowana"
                await self.send(
                    f"{key}: {route['name']}. Nawigacja {route['navigation_required']}+, Kadłub {route['hull_required']}+. {status}."
                )
            await self.send("Wpisz zegluj <nazwa>. Potem używaj ex i kierunków — szlak jest częścią świata, nie teleportem.")
            return
        match = None
        for key, route in here:
            if args == key or args in route["name"].lower():
                match = (key, route)
                break
        if not match:
            await self.send("Nie ma takiej trasy z tego portu. Wpisz zegluj lista.")
            return
        key, route = match
        nav = self.ocean_ship_level_v1000("navigation")
        hull = self.ocean_ship_level_v1000("hull")
        if nav < route["navigation_required"] or hull < route["hull_required"]:
            await self.send(
                f"Trasa wymaga Nawigacji {route['navigation_required']} i Kadłuba {route['hull_required']}. Masz {nav} i {hull}."
            )
            return
        room_id = self.character.room_id
        direction = route["origin_direction"] if room_id == route["origin"] else route["destination_direction"]
        await self.send(f"Rozpoczynasz rejs: {route['name']}. To prawdziwa trasa; po wejściu używaj ex i kierunków.")
        await self.move(direction)
        if self.character.room_id == room_id:
            return
        self.server.db.conn.execute(
            "UPDATE ocean_ship_v1000 SET voyages=voyages+1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
            (self.account_id,),
        )
        self.server.db.conn.commit()

    def ocean_trade_offers_v1000(self):
        # Static authored routes keep contracts readable and deterministic,
        # but the payout floor follows current progression so Ocean 2.0
        # does not become obsolete economically.
        stage = self.ocean_economy_stage_v1138()
        # v1.13.42: cztery kontrakty w każdym z siedmiu portów.
        # Są tu kursy lokalne, średnie i dalekomorskie, w obie strony.
        rows = (
            # Port Dusz.
            ("dusze", "harbor", "ocean_platform", "Zapasy dla oceanicznych załóg", 500_000, 1),
            ("dusze_mgla", "harbor", "fog_square", "Beczki świątynnego oleju", 1_600_000, 2),
            ("dusze_gwiazda", "harbor", "star_port_market", "Relikwiarze nawigatorów", 3_500_000, 3),
            ("dusze_korona", "harbor", "silver_crown_harbor", "Dyplomatyczne skrzynie Portu Dusz", 7_500_000, 4),

            # Platforma Oceaniczna.
            ("rafy", "ocean_platform", "fog_square", "Skrzynie soli i lin", 1_000_000, 1),
            ("platforma_gwiazda", "ocean_platform", "star_port_market", "Części astrolabiów", 2_800_000, 2),
            ("korona", "ocean_platform", "silver_crown_harbor", "Towary królewskiej kompanii", 10_000_000, 4),
            ("platforma_cicha", "ocean_platform", "quiet_haven_dock", "Moduły głębinowych pomp", 18_000_000, 5),

            # Port Mglistych Wysp.
            ("mgla", "fog_square", "star_port_market", "Mglisty bursztyn", 2_500_000, 2),
            ("mgla_platforma", "fog_square", "ocean_platform", "Zwoje map prądów", 1_200_000, 1),
            ("mgla_dusze", "fog_square", "harbor", "Skrzynie ziół z wysp", 2_200_000, 2),
            ("mgla_korona", "fog_square", "silver_crown_harbor", "Bursztynowe insygnia kupieckie", 9_000_000, 4),

            # Gwiezdny Port.
            ("gwiazda", "star_port_market", "v0800_harbor", "Astralne przyrządy", 5_000_000, 3),
            ("gwiazda_mgla", "star_port_market", "fog_square", "Gwiezdne szkło", 2_600_000, 2),
            ("gwiazda_dusze", "star_port_market", "harbor", "Kryształy obserwacyjne", 8_000_000, 4),
            ("gwiazda_korona", "star_port_market", "silver_crown_harbor", "Astralne zegary dworskie", 14_000_000, 5),

            # Przystań Siedmiu Latarni.
            ("latarnie_gwiazda", "v0800_harbor", "star_port_market", "Soczewki latarniane", 4_500_000, 2),
            ("latarnie_mgla", "v0800_harbor", "fog_square", "Olej siedmiu latarni", 6_500_000, 3),
            ("latarnie_platforma", "v0800_harbor", "ocean_platform", "Mechanizmy sygnałowe", 10_000_000, 4),
            ("latarnie_korona", "v0800_harbor", "silver_crown_harbor", "Latarniane rdzenie ceremonialne", 17_000_000, 5),

            # Wielki Port Srebrnej Korony.
            ("korona_platforma", "silver_crown_harbor", "ocean_platform", "Królewskie części okrętowe", 8_000_000, 3),
            ("powrot", "silver_crown_harbor", "star_port_market", "Srebrne mechanizmy portowe", 15_000_000, 5),
            ("korona_cicha", "silver_crown_harbor", "quiet_haven_dock", "Srebrne narzędzia stoczniowe", 6_000_000, 3),
            ("korona_dusze", "silver_crown_harbor", "harbor", "Skarbiec poselstwa Korony", 20_000_000, 5),

            # Mały Port Wschodni w Cichej Przystani.
            ("cicha", "quiet_haven_dock", "silver_crown_harbor", "Towary z Cichej Przystani", 6_000_000, 3),
            ("cicha_platforma", "quiet_haven_dock", "ocean_platform", "Suszone zapasy dalekomorskie", 12_000_000, 4),
            ("cicha_mgla", "quiet_haven_dock", "fog_square", "Wschodnie tkaniny żaglowe", 14_000_000, 4),
            ("cicha_gwiazda", "quiet_haven_dock", "star_port_market", "Ciche instrumenty nawigacyjne", 22_000_000, 5),
        )
        offers = []
        for key, origin, dest, label, authored, required in rows:
            path = self.ocean_contract_path_v1001(origin, dest)
            distance_steps = max(1, len(path) - 1) if path else 1
            # Ładownia opisuje trudność ładunku, a dystans nagradza faktycznie
            # dłuższe rejsy. Authored reward pozostaje bezpieczną dolną granicą.
            difficulty = (
                0.75
                + required * 0.18
                + min(1.75, distance_steps * 0.025)
            )
            reward = max(
                int(authored),
                v1138_activity_income(stage, "ocean_trade", difficulty),
            )
            offers.append((key, origin, dest, label, reward, required))
        return tuple(offers)

    def ocean_contract_path_v1001(self, origin, destination):
        """Shortest sea-only port path, including every sector of its lanes."""
        links = {}
        for route in ROUTES.values():
            lane = (route["origin"], *route["rooms"], route["destination"])
            for start, end in zip(lane, lane[1:]):
                links.setdefault(start, set()).add(end)
                links.setdefault(end, set()).add(start)
        queue = deque([(origin,)])
        visited = {origin}
        while queue:
            path = queue.popleft()
            if path[-1] == destination:
                return path
            for next_room in sorted(links.get(path[-1], ())):
                if next_room not in visited:
                    visited.add(next_room)
                    queue.append((*path, next_room))
        return ()

    def ocean_contract_step_v1001(self, old_room, new_room):
        """Track adjacent sea movement from the origin, including earlier authored lanes."""
        row = self.server.db.conn.execute(
            "SELECT origin_room,destination_room,route_progress,route_current_room,arrival_verified "
            "FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,),
        ).fetchone()
        if not row or int(row["arrival_verified"]):
            return
        path = self.ocean_contract_path_v1001(row["origin_room"], row["destination_room"])
        links = {}
        lanes = [
            (route["origin"], *route["rooms"], route["destination"])
            for route in ROUTES.values()
        ]
        lanes.extend((
            ("ocean_platform", *(f"fog_crossing_{i:02d}" for i in range(1, 5)), "fog_dock", "fog_square"),
            ("fog_dock", *(f"ardelia_crossing_{i:02d}" for i in range(1, 7)), "silver_crown_harbor"),
            ("star_port_market", "v0800_star_pier", *(f"v0800_open_sea_{i:02d}" for i in range(1, 4)), "v0800_harbor"),
        ))
        for lane in lanes:
            for start, end in zip(lane, lane[1:]):
                if end in ROOMS.get(start, {}).get("exits", {}).values():
                    links.setdefault(start, set()).add(end)
                    links.setdefault(end, set()).add(start)
        progress = int(row["route_progress"])
        current = row["route_current_room"] or (path[progress] if 0 < progress < len(path) else row["origin_room"])
        was_underway = progress > 0

        # Każdy rzeczywisty morski sektor może być objazdem. Kontrakt nie ma
        # zerować się tylko dlatego, że gracz wpłynął na inne wody niż
        # najkrótsza ścieżka wyliczona dla kontraktu.
        port_rooms = {room_id for room_id, _label in PORTS.values()}
        maritime_rooms = set(links)
        maritime_rooms.update(port_rooms)

        def is_maritime_room(room_id):
            room = ROOMS.get(room_id, {})
            return bool(
                room_id in maritime_rooms
                or room.get("requires_ship")
                or room.get("deep_ocean_fishing")
                or room.get("ocean_route")
            )

        # A visit to the submerged ruins is a detour from a sea sector, not
        # abandonment of the voyage. Returning to that sector resumes it.
        if progress and (
            old_room == current and ROOMS.get(new_room, {}).get("underwater")
            or new_room == current and ROOMS.get(old_room, {}).get("underwater")
        ):
            return None

        if current == old_room and new_room in links.get(old_room, ()):
            progress += 1
            current = new_room
        elif old_room == row["origin_room"] and new_room in links.get(old_room, ()):
            progress = 1
            current = new_room
        elif was_underway and current == old_room and is_maritime_room(new_room):
            # Legalny morski objazd / przejście na inny akwen: zachowujemy
            # kontrakt i kontynuujemy liczenie od aktualnego sektora.
            progress += 1
            current = new_room
        elif not was_underway and old_room == row["origin_room"] and is_maritime_room(new_room):
            progress = 1
            current = new_room
        else:
            progress = 0
            current = ""
        verified = int(progress > 0 and current == row["destination_room"])
        self.server.db.conn.execute(
            "UPDATE ocean_trade_contract_v1000 SET route_progress=?,route_current_room=?,arrival_verified=? WHERE account_id=?",
            (progress, current, verified, self.account_id),
        )
        self.server.db.conn.commit()
        if verified:
            return "complete"
        if progress == 1:
            return "started"
        if progress == 0 and was_underway:
            return "lost"
        return None

    async def ocean_trade_v1000(self, args=""):
        text = str(args or "").strip().lower()
        if text.startswith("morski "):
            text = text.split(maxsplit=1)[1]
        row = self.server.db.conn.execute(
            "SELECT * FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,)
        ).fetchone()
        if text in ("porzuc", "porzuć", "anuluj", "cancel", "abandon"):
            if not row or not row["contract_key"]:
                await self.send("Nie masz aktywnego kontraktu morskiego.")
                return
            cargo_label = row["cargo_label"]
            destination_name = ROOMS.get(row["destination_room"], {}).get("name", row["destination_room"])
            self.server.db.conn.execute(
                "DELETE FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,)
            )
            self.server.db.conn.commit()
            await self.send(
                f"HANDEL MORSKI: porzucasz kontrakt '{cargo_label}' do {destination_name}. "
                "Ładunek zostaje anulowany; nie otrzymujesz nagrody."
            )
            return
        if text in ("oddaj", "dostarcz", "deliver"):
            if not row or not row["contract_key"]:
                await self.send("Nie masz aktywnego kontraktu morskiego.")
                return
            if self.character.room_id != row["destination_room"]:
                await self.send(f"Ładunek trzeba dostarczyć do: {ROOMS.get(row['destination_room'],{}).get('name',row['destination_room'])}.")
                return
            if not int(row["arrival_verified"]):
                progress = int(row["route_progress"])
                last_room = row["route_current_room"]
                await self.send(
                    f"Kontrakt nie ma potwierdzonego dopłynięcia. Zaliczone kroki: {progress}. "
                    f"Ostatni zaliczony sektor: {ROOMS.get(last_room, {}).get('name', 'port nadania')}. "
                    "Jeżeli postęp wynosi 0, wróć do portu nadania i rozpocznij rejs."
                )
                return
            reward = int(row["reward_silver"])
            wallet = self.character_wallet_silver_value()
            self.character.silver = wallet + reward
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.conn.execute("DELETE FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,))
            self.server.db.save_character(self.character)
            await self.send(f"HANDEL MORSKI: dostawa zakończona. Otrzymujesz {currency_reading_text(reward)}.")
            return
        if text.startswith("wez ") or text.startswith("weź ") or text.startswith("take "):
            if row and row["contract_key"]:
                await self.send("Masz już aktywny kontrakt morski.")
                return
            if not self.ocean_ship_owned_v1000():
                await self.send("Do przyjęcia ładunku morskiego potrzebujesz własnego statku. Wpisz statek kup w porcie.")
                return
            try:
                number = int(text.split()[-1])
            except Exception:
                number = 0
            offers = [o for o in self.ocean_trade_offers_v1000() if o[1] == self.character.room_id]
            if number < 1 or number > len(offers):
                await self.send("Nie ma takiej oferty w tym porcie. Wpisz handel morski.")
                return
            key, origin, dest, cargo_label, reward, required = offers[number-1]
            if not self.ocean_contract_path_v1001(origin, dest):
                await self.send("Szlak tego kontraktu jest niedostępny. Zgłoś błąd administratorowi.")
                return
            cargo_level = self.ocean_ship_level_v1000("cargo")
            if cargo_level < required:
                await self.send(f"Ten kontrakt wymaga Ładowni poziom {required}; masz {cargo_level}.")
                return
            accepted_at = int(time.time())
            self.server.db.conn.execute(
                "INSERT OR REPLACE INTO ocean_trade_contract_v1000(account_id,contract_key,origin_room,destination_room,cargo_label,reward_silver,required_cargo,accepted_at) VALUES(?,?,?,?,?,?,?,?)",
                (self.account_id,key,origin,dest,cargo_label,reward,required,accepted_at),
            )
            self.server.db.conn.commit()
            await self.send(f"Przyjmujesz ładunek: {cargo_label}. Cel: {ROOMS[dest]['name']}. Nagroda: {currency_reading_text(reward)}.")

            # v1.00.16: tak jak zwykłe questy, lider drużyny dzieli przyjęcie
            # kontraktu morskiego z żywymi członkami stojącymi w tym samym porcie.
            # Każdy otrzymuje własny wpis i własny postęp/nagrodę. Istniejącego
            # aktywnego kontraktu członka nigdy nie nadpisujemy.
            party_key = self.server.party_key_for_account(self.account_id)
            if party_key is not None and int(party_key) == int(self.account_id):
                recipients = [
                    session
                    for session in self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    )
                    if session is not self
                    and session.character
                    and not session.closed
                    and int(getattr(session, "current_hp", 0) or 0) > 0
                ]
                accepted_names = []
                skipped_names = []
                for member in sorted(
                    recipients, key=lambda session: session.character.name.lower()
                ):
                    member_row = self.server.db.conn.execute(
                        "SELECT contract_key FROM ocean_trade_contract_v1000 WHERE account_id=?",
                        (member.account_id,),
                    ).fetchone()
                    if member_row and member_row["contract_key"]:
                        skipped_names.append(member.character.name)
                        await member.send(
                            f"Lider {self.character.name} przyjmuje handel morski: {cargo_label}, "
                            "ale masz już własny aktywny kontrakt morski."
                        )
                        continue
                    self.server.db.conn.execute(
                        "INSERT OR REPLACE INTO ocean_trade_contract_v1000(account_id,contract_key,origin_room,destination_room,cargo_label,reward_silver,required_cargo,accepted_at) VALUES(?,?,?,?,?,?,?,?)",
                        (member.account_id,key,origin,dest,cargo_label,reward,required,accepted_at),
                    )
                    accepted_names.append(member.character.name)
                    await member.send(
                        f"Lider {self.character.name} przyjmuje dla drużyny handel morski: "
                        f"{cargo_label}. Cel: {ROOMS[dest]['name']}. "
                        f"Nagroda: {currency_reading_text(reward)}."
                    )
                self.server.db.conn.commit()
                if accepted_names:
                    await self.send(
                        "Kontrakt morski przyjęła razem z tobą drużyna: "
                        + ", ".join(accepted_names)
                        + "."
                    )
                if skipped_names:
                    await self.send(
                        "Nie wszyscy mogli otrzymać kontrakt morski. Pominięto: "
                        + ", ".join(skipped_names)
                        + "."
                    )
            return
        if row and row["contract_key"]:
            await self.send(
                f"AKTYWNY HANDEL MORSKI: {row['cargo_label']}. Cel: {ROOMS.get(row['destination_room'],{}).get('name',row['destination_room'])}. Nagroda {currency_reading_text(row['reward_silver'])}."
            )
            await self.send(
                f"Postęp rejsu: {int(row['route_progress'])} kroków. "
                f"Ostatni zaliczony sektor: {ROOMS.get(row['route_current_room'], {}).get('name', 'port nadania')}. "
                f"Dopłynięcie: {'potwierdzone' if int(row['arrival_verified']) else 'niepotwierdzone'}."
            )
        offers = [o for o in self.ocean_trade_offers_v1000() if o[1] == self.character.room_id]
        await self.send("HANDEL MORSKI — OFERTY W TYM PORCIE")
        if not offers:
            await self.send("W tym miejscu nie ma nowych ładunków. Kontrakty zaczynają się w głównych portach.")
            return
        for i, (_key, origin, dest, cargo_label, reward, required) in enumerate(offers, 1):
            distance = max(1, len(self.ocean_contract_path_v1001(origin, dest)) - 1)
            await self.send(
                f"{i}. {cargo_label} -> {ROOMS[dest]['name']}. "
                f"Rejs {distance} odcinków. Ładownia {required}+. "
                f"Nagroda {currency_reading_text(reward)}."
            )
        await self.send("Przyjęcie: handel morski wez <nr>. Oddanie: handel morski oddaj. Porzucenie: handel morski porzuc.")

    def maybe_grant_ocean_treasure_map_v1000(self):
        if self.character.room_id not in DEEP_OCEAN_ROOMS:
            return None
        existing = self.server.db.conn.execute(
            "SELECT * FROM ocean_treasure_map_v1000 WHERE account_id=?", (self.account_id,)
        ).fetchone()
        if existing and not int(existing["found"]):
            return None
        if random.random() >= 0.08:
            return None
        targets = list(DEEP_OCEAN_ROOMS) + list(TREASURE_ROOMS)
        target = random.choice(targets)
        name = f"Mapa skarbu: {ROOMS[target]['name']}"
        self.server.db.conn.execute(
            "INSERT OR REPLACE INTO ocean_treasure_map_v1000(account_id,target_room,map_name,found,created_at) VALUES(?,?,?,0,CURRENT_TIMESTAMP)",
            (self.account_id,target,name),
        )
        self.server.db.conn.commit()
        return name

    async def ocean_treasure_v1000(self, args=""):
        text = str(args or "").strip().lower()
        row = self.server.db.conn.execute(
            "SELECT * FROM ocean_treasure_map_v1000 WHERE account_id=?", (self.account_id,)
        ).fetchone()
        if text in ("szukaj", "kop", "search", "dig"):
            if not row or int(row["found"]):
                await self.send("Nie masz aktywnej mapy skarbu.")
                return
            if self.character.room_id != row["target_room"]:
                await self.send("Mapa wskazuje inne miejsce. Wpisz skarby, aby odczytać wskazówkę.")
                return
            navigation = self.ocean_ship_level_v1000("navigation")
            stage = self.ocean_economy_stage_v1138()
            reward = max(
                45_000 + navigation * 20_000,
                v1138_activity_income(
                    stage,
                    "ocean_treasure",
                    1.0 + navigation * 0.12,
                ),
            )
            wallet = self.character_wallet_silver_value()
            self.character.silver = wallet + reward
            self.character.gold = 0
            self.character.mithril = 0
            item_id = "v1000_abyss_pearl" if random.random() < 0.75 else "v1000_sunken_relic"
            self.server.db.add_item(self.account_id, item_id, 1)
            self.server.db.conn.execute(
                "UPDATE ocean_treasure_map_v1000 SET found=1 WHERE account_id=?", (self.account_id,)
            )
            self.server.db.conn.execute(
                "UPDATE ocean_ship_v1000 SET treasures=treasures+1 WHERE account_id=?", (self.account_id,)
            )
            self.server.db.save_character(self.character)
            await self.send(f"ODNAJDUJESZ SKARB: {currency_reading_text(reward)} oraz {player_item_display_name_v0335(item_id)}.")
            return
        if not row or int(row["found"]):
            await self.send("Nie masz aktywnej mapy skarbu. Mapy mogą wypaść podczas głębinowych połowów na Ocean 2.0.")
            return
        target = row["target_room"]
        nav = self.ocean_ship_level_v1000("navigation")
        if nav >= 4:
            hint = ROOMS.get(target, {}).get("name", target)
        else:
            hint = ROOMS.get(target, {}).get("zone", "Ocean 2.0")
        await self.send(f"MAPA SKARBU: {row['map_name']}. Wskazówka nawigacyjna: {hint}. Na miejscu wpisz skarby szukaj.")
