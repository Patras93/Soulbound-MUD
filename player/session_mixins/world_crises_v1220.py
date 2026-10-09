# -*- coding: utf-8 -*-
"""NVDA-friendly multi-stage world events in real v1.20 regions."""
from core.bootstrap_economy_professions import currency_price_text
from data.catalogs import ROOMS, ITEMS
from systems.world_crises_v1220 import CRISES, crisis_day, crisis_progress_message, crisis_reward
from world.great_world import V1200_REGIONAL_INDEX


class SessionWorldCrisesV1220Mixin:
    def crisis_region_here_v1220(self):
        if not self.character:
            return None
        return ROOMS.get(self.character.room_id, {}).get("v1200_region")

    async def handle_world_crises_v1220(self, args=""):
        if not self.character:
            return
        raw = str(args or "").strip()
        words = raw.split(maxsplit=1)
        action = words[0].lower() if words else "lista"
        key_here = self.crisis_region_here_v1220()
        if action in ("lista", "list", "", "pomoc", "help"):
            await self.send("WIELKIE WYDARZENIA ŚWIATA: codzienna obrona czterech krain. Solo lub drużyna, bez pułapek.")
            for key, event in CRISES.items():
                spec = V1200_REGIONAL_INDEX.get(key)
                if not spec:
                    continue
                row = self.server.db.crisis_status_v1220(self.account_id, key, crisis_day())
                stage = row["stage"] if row else 0
                if row and row["claimed"]:
                    stage = 5
                await self.send(f"{event['name']}. {crisis_progress_message(stage, row['kills'] if row else 0)} ")
            await self.send("W obozowisku: kryzys start. Potem kryzys status, kryzys ratuj, kryzys odbierz. help wielkie_wydarzenia.")
            return
        if action not in ("start", "rozpocznij", "status", "stan", "ratuj", "pomoc", "odbierz", "nagroda"):
            normalized = self.normalize_room_query(raw)
            for key, event in CRISES.items():
                if normalized in (key, self.normalize_room_query(event["name"])) or normalized in self.normalize_room_query(event["name"]):
                    spec = V1200_REGIONAL_INDEX.get(key)
                    if spec:
                        await self.send(f"{event['name']}: {event['story']} Obozowisko: {ROOMS[spec['town']]['name']}; boss w {ROOMS[spec['arena']]['name']}.")
                        route = self.shortest_path(self.character.room_id, spec["town"])
                        if route:
                            direction, room = route[0]
                            await self.send(f"Pierwszy krok trasy: {self.route_direction_name(direction)} — {ROOMS[room]['name']}.")
                        return
            await self.send("Nie znam tego wydarzenia. Wpisz wydarzenia.")
            return
        if not key_here or key_here not in CRISES:
            await self.send("Te wydarzenia odbywają się w czterech krainach Wielkiego Świata. Wpisz wydarzenia, aby poznać listę.")
            return
        spec = V1200_REGIONAL_INDEX[key_here]
        title = CRISES[key_here]["name"]
        at_camp = str(self.character.room_id) == str(spec["town"])
        day = crisis_day()
        row = self.server.db.crisis_status_v1220(self.account_id, key_here, day)
        if action in ("start", "rozpocznij"):
            if not at_camp:
                await self.send(f"Rozpocznij kryzys w: {ROOMS[spec['town']]['name']}.")
                return
            if self.server.db.crisis_start_v1220(self.account_id, key_here, day):
                await self.send(f"Rozpoczynasz {title}. Pokonaj 3 regionalnych przeciwników. Twoje postępy zapisują się automatycznie.")
                await self.server.broadcast_all(f"WYDARZENIE ŚWIATA: {self.character.name} rozpoczyna {title}! Obozowisko: {ROOMS[spec['town']]['name']}. Można walczyć solo lub z drużyną.", history_category="system")
            else:
                await self.send("To wydarzenie jest już dziś rozpoczęte albo ukończone. Wpisz kryzys status.")
            return
        if action in ("status", "stan"):
            await self.send(f"{title}: {crisis_progress_message(row['stage'], row['kills']) if row else 'Nieprzyjęte. Rozpocznij w obozie.'}")
            return
        if action in ("ratuj", "pomoc"):
            if not at_camp:
                await self.send("Ratunek możesz przeprowadzić po powrocie do obozowiska regionu.")
                return
            if not self.server.db.crisis_rescue_v1220(self.account_id, key_here, day):
                await self.send("Najpierw ukończ drugi etap: pokonaj czterech najeźdźców kryzysu. Status: kryzys status.")
                return
            await self.send(f"Ratunek zakończony: mieszkańcy są bezpieczni. Etap 3: pokonaj {ROOMS[spec['arena']]['name']}.")
            return
        if action in ("odbierz", "nagroda"):
            if not at_camp:
                await self.send("Nagroda czeka w obozowisku regionu.")
                return
            coins, quantity = crisis_reward(spec["stage"])
            if not self.server.db.crisis_claim_v1220(self.account_id, key_here, day, coins, spec["resource"], quantity):
                await self.send("Nagroda jeszcze nie jest gotowa albo została dziś już odebrana. Sprawdź: kryzys status.")
                return
            self.server.db.apply_shared_wallet_to_character(self.character)
            await self.send(f"KRYZYS UKOŃCZONY: {title}. Nagroda: {currency_price_text(coins)} i {quantity} szt. {ITEMS[spec['resource']]['name']}. Kolejna edycja następnego dnia (UTC).")
            await self.server.broadcast_all(f"WYDARZENIE ŚWIATA ZAKOŃCZONE: {self.character.name} odparł {title}!", history_category="system")
            return

    async def record_world_crisis_kill_v1220(self, mob, template):
        """Called once from mob_defeated for each eligible local party recipient."""
        if not self.character or not template:
            return
        key = template.get("v1200_region")
        spec = V1200_REGIONAL_INDEX.get(key)
        if not spec or str(self.character.room_id) != str(mob.room_id):
            return
        room_key = ROOMS.get(mob.room_id, {}).get("v1200_region")
        if room_key != key:
            return
        boss = str(mob.template_id) == str(spec["boss"])
        current = self.server.db.crisis_status_v1220(self.account_id, key, crisis_day())
        if not current:
            return
        if not boss and int(template.get("v1220_crisis_wave", 0) or 0) != current["stage"]:
            return
        result = self.server.db.crisis_kill_v1220(self.account_id, key, crisis_day(), boss=boss)
        if result:
            await self.send(f"KRYZYS {CRISES[key]['name']}: {crisis_progress_message(*result)}")
