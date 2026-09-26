# -*- coding: utf-8 -*-
"""Soulbound v1.00.0 - Ocean 2.0 session actions."""
from __future__ import annotations

import random
import time

from core.classes_skills import ROOMS
from systems.crafting_quality import player_item_display_name_v0335
from world.ocean_expansion import ROUTES, PORTS, DEEP_OCEAN_ROOMS, TREASURE_ROOMS


class SessionOceanV1000Mixin:
    V1000_SHIP_BASE_COST = 25_000
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
                    f"STATEK: nie posiadasz statku. Kupno kosztuje {self.V1000_SHIP_BASE_COST} srebra. Wpisz statek kup w porcie."
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
                await self.send(f"Potrzebujesz {self.V1000_SHIP_BASE_COST} srebra.")
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
                await self.send(f"Ulepszenie na poziom {level+1} kosztuje {cost} srebra.")
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
        self.server.db.conn.execute(
            "UPDATE ocean_ship_v1000 SET voyages=voyages+1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
            (self.account_id,),
        )
        self.server.db.conn.commit()

    def ocean_trade_offers_v1000(self):
        # Static authored routes keep contracts readable and deterministic.
        return (
            ("rafy", "ocean_platform", "fog_square", "Skrzynie soli i lin", 35_000, 1),
            ("mgla", "fog_square", "star_port_market", "Mglisty bursztyn", 65_000, 2),
            ("gwiazda", "star_port_market", "v0800_harbor", "Astralne przyrządy", 120_000, 3),
            ("korona", "ocean_platform", "silver_crown_harbor", "Towary królewskiej kompanii", 220_000, 4),
            ("powrot", "silver_crown_harbor", "star_port_market", "Srebrne mechanizmy portowe", 300_000, 5),
        )

    async def ocean_trade_v1000(self, args=""):
        text = str(args or "").strip().lower()
        if text.startswith("morski "):
            text = text.split(maxsplit=1)[1]
        row = self.server.db.conn.execute(
            "SELECT * FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,)
        ).fetchone()
        if text in ("oddaj", "dostarcz", "deliver"):
            if not row or not row["contract_key"]:
                await self.send("Nie masz aktywnego kontraktu morskiego.")
                return
            if self.character.room_id != row["destination_room"]:
                await self.send(f"Ładunek trzeba dostarczyć do: {ROOMS.get(row['destination_room'],{}).get('name',row['destination_room'])}.")
                return
            reward = int(row["reward_silver"])
            wallet = self.character_wallet_silver_value()
            self.character.silver = wallet + reward
            self.character.gold = 0
            self.character.mithril = 0
            self.server.db.conn.execute("DELETE FROM ocean_trade_contract_v1000 WHERE account_id=?", (self.account_id,))
            self.server.db.save_character(self.character)
            await self.send(f"HANDEL MORSKI: dostawa zakończona. Otrzymujesz {reward} srebra.")
            return
        if text.startswith("wez ") or text.startswith("weź ") or text.startswith("take "):
            if row and row["contract_key"]:
                await self.send("Masz już aktywny kontrakt morski.")
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
            cargo_level = self.ocean_ship_level_v1000("cargo")
            if cargo_level < required:
                await self.send(f"Ten kontrakt wymaga Ładowni poziom {required}; masz {cargo_level}.")
                return
            self.server.db.conn.execute(
                "INSERT OR REPLACE INTO ocean_trade_contract_v1000(account_id,contract_key,origin_room,destination_room,cargo_label,reward_silver,required_cargo,accepted_at) VALUES(?,?,?,?,?,?,?,?)",
                (self.account_id,key,origin,dest,cargo_label,reward,required,int(time.time())),
            )
            self.server.db.conn.commit()
            await self.send(f"Przyjmujesz ładunek: {cargo_label}. Cel: {ROOMS[dest]['name']}. Nagroda: {reward} srebra.")
            return
        if row and row["contract_key"]:
            await self.send(
                f"AKTYWNY HANDEL MORSKI: {row['cargo_label']}. Cel: {ROOMS.get(row['destination_room'],{}).get('name',row['destination_room'])}. Nagroda {row['reward_silver']} srebra."
            )
        offers = [o for o in self.ocean_trade_offers_v1000() if o[1] == self.character.room_id]
        await self.send("HANDEL MORSKI — OFERTY W TYM PORCIE")
        if not offers:
            await self.send("W tym miejscu nie ma nowych ładunków. Kontrakty zaczynają się w głównych portach.")
            return
        for i, (_key, _origin, dest, cargo_label, reward, required) in enumerate(offers, 1):
            await self.send(f"{i}. {cargo_label} -> {ROOMS[dest]['name']}. Ładownia {required}+. Nagroda {reward} srebra.")
        await self.send("Przyjęcie: handel morski wez <nr>. Oddanie: handel morski oddaj.")

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
            reward = 45_000 + self.ocean_ship_level_v1000("navigation") * 20_000
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
            await self.send(f"ODNAJDUJESZ SKARB: {reward} srebra oraz {player_item_display_name_v0335(item_id)}.")
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
