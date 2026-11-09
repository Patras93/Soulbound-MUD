# -*- coding: utf-8 -*-
"""Modul v109: world_rotation; oryginalne metody bez zmian AST."""
from .dependencies import *

class WorldRotationV109Mixin:

    async def show_dynamic_events_v029(self):
            now = time.time()
            events = v0290_active_world_events(now)
            remaining = max(0, int(events[0]["expires_at"] - now)) if events else 0
            await self.send(f"DYNAMICZNE WYDARZENIA — rotacja za około {remaining} sekund.")
            if not events:
                await self.send("Brak aktywnych wydarzeń.")
                return
            for number, event in enumerate(events, 1):
                room = ROOMS.get(event["room_id"], {})
                await self.send(
                    f"{number}. {event['title']}. {room.get('name') or 'Nieznana lokacja'}. "
                    f"Etap {event['stage']}. Ranga {event['rank']}. Liczba przeciwników {event['count']}."
                )
            await self.send("Wszystkie aktywne wydarzenia są pasywne do chwili ataku.")

    async def show_nemesis_v029(self):
            row = self.server.db.nemesis_row_v029(self.account_id)
            if not row:
                await self.send("Nie masz jeszcze Nemesis. Przeciwnik może nim zostać, jeśli pokona cię w walce.")
                return
            if not int(row["active"] or 0):
                await self.send(
                    f"Ostatni Nemesis został pokonany. Łącznie pokonane Nemesis: {int(row['defeats'] or 0)}. "
                    "Nowy może powstać przy kolejnej porażce z przeciwnikiem."
                )
                return
            room_id = str(row["room_id"])
            self.server.world.ensure_runtime_room(room_id)
            room_name = ROOMS.get(room_id, {}).get("name") or "Nieznana lokacja"
            await self.send(
                f"NEMESIS: {row['nemesis_name']}. Ranga {int(row['rank'])}. Etap {int(row['level'])}. "
                f"Pokonał cię {int(row['kills_player'])} razy. Lokalizacja: {room_name}."
            )
            if str(self.character.room_id) == room_id:
                self.server.world.ensure_v029_nemesis(row)
                await self.send("Nemesis jest tutaj.")
                return
            path = self.shortest_path(self.character.room_id, room_id)
            if path:
                first = path[0] if path else None
                if first:
                    direction, next_room = first
                    await self.send(
                        f"Trasa ma {len(path)} kroków. Pierwszy kierunek: {self.route_direction_name(direction)} "
                        f"do {ROOMS.get(next_room, {}).get('name', next_room)}."
                    )
            else:
                await self.send("Cel istnieje, ale jego dynamiczna trasa nie jest jeszcze zmaterializowana. Wejdź ponownie do regionu i użyj nemesis.")

    async def show_world_events(self):
            await self.show_double_xp_event()
            now = time.time()
            events = v0140_active_world_events(now)
            remaining = max(0, int(events[0]["expires_at"] - now)) if events else 0
            await self.send(f"WYDARZENIA ŚWIATA — następna rotacja za około {remaining} sekund.")
            action_for = {
                "fish_run":"low", "herb_bloom":"zbieraj", "rich_vein":"kop",
                "forest_growth":"tnij", "ancient_dig":"wykop",
            }
            for number, event in enumerate(events, 1):
                zone = V013_FRONTIER_SPECS[event["kind"]]["zone"]
                command = f" Komenda na miejscu: {action_for[event['type']]}." if event["type"] in action_for else ""
                await self.send(
                    f"{number}. {event['title']}. {zone}, sektor {event['x']+1}-{event['y']+1}. {event['desc']}{command}"
                )
            await self.send("Wydarzenia sa opcjonalne; bossowie nie zaczynaja walki sami. Sektor musisz odwiedzic przed koncem rotacji.")
            legendary = v0180_active_legendary_events(now)
            if legendary:
                await self.send("LEGENDARNE WYDARZENIA — rotacja co cztery godziny; szczegóły: legendarnewydarzenia.")
                for event in legendary:
                    zone = V013_FRONTIER_SPECS[event["kind"]]["zone"]
                    tool_command = {"mining":"kop", "woodcutting":"tnij", "fishing":"low", "herbalism":"zbieraj"}.get(event.get("tool"), "walka")
                    await self.send(f"{event['title']}: {zone}, sektor {event['x']+1}-{event['y']+1}; {tool_command}.")
            from world.great_world import v1200_rotating_events
            regional = v1200_rotating_events(now)
            await self.send(f"KRÓLESTWA: {len(regional)} aktywne wydarzenia. Dokladne lokalizacje: krainy wydarzenia.")
            from systems.world_events_v12812 import active_city_event_v12812
            city_event = active_city_event_v12812(now)
            await self.send(f"NAJAZD PODZIEMI: {city_event['name']}. Lokalizacja: {ROOMS.get(city_event['room_id'], {}).get('name', city_event['room_id'])}.")
            from systems.era_legends_v1600 import active_invasion_v1600
            invasion = active_invasion_v1600(now)
            await self.send(f"INWAZJA: {invasion['title']}. Szczegóły: era60 inwazje.")
            try:
                from systems.world_invasions_v10400 import status_text as _invasion_status_v104
                await self.send(_invasion_status_v104(self.server.db.conn, now))
                from systems.world_invasions_v10400 import reward_status as _invasion_reward_v104
                if self.character:
                    await self.send(_invasion_reward_v104(self.server.db.conn, self.account_id, now))
            except Exception as exc:
                print(f'V104_INVASION_STATUS_ERROR: {type(exc).__name__}: {exc}', flush=True)
                await self.send('INWAZJA V104: status tymczasowo niedostępny.')
            await self.send("KRYZYSY CZTERECH KRAIN: kryzys lista, kryzys start, kryzys status, kryzys ratuj, kryzys odbierz.")
            await self.send("ARCHEOLOGIA: wykop w ruinach lub przy aktywnym stanowisku wykopaliskowym.")
            await self.show_dynamic_events_v029()
            await self.send("KARAWANY: Wędrujący kupcy zmieniają lokalizację co 15 minut. Oferta jest dostępna przez komendę sklep, gdy karawana stoi obok.")
            for npc_id, data in V016_TRAVELERS.items():
                if npc_id.startswith('v1230_caravan_'):
                    caravan_room = v0160_traveler_room(npc_id, now)
                    await self.send(f"{data['name']}: {ROOMS.get(caravan_room, {}).get('name', caravan_room)}.")
