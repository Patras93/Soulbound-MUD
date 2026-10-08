# -*- coding: utf-8 -*-
"""Short, read-only v1.20.0 regional atlas commands designed for NVDA."""
from __future__ import annotations

from data.catalogs import ROOMS
from world.great_world import V1200_GATE, V1200_REGIONAL_INDEX, V1200_REGIONS, v1200_rotating_events


class SessionGreatWorldV1200Mixin:
    async def great_world_v1200(self, args=""):
        if not self.character:
            await self.send("Krainy: najpierw wybierz postać.")
            return
        query = self.normalize_room_query(args)
        if query in ("", "lista", "regiony", "status", "pomoc"):
            await self.send("WIELKI ŚWIAT v1.20.0 — 4 krainy. Wejście: Rozdroże Czterech Wiatrów.")
            for _, spec in V1200_REGIONAL_INDEX.items():
                await self.send(f"{spec['name']}: etap {spec['stage']}; boss: "
                                f"{ROOMS[spec['arena']]['name']}; osada: {ROOMS[spec['town']]['name']}.")
            await self.send("Użyj: krainy wydarzenia; krainy <nazwa>; "
                            "nawigacja cel Rozdroże Czterech Wiatrów.")
            return
        if query in ("wydarzenia", "wydarzenie", "event", "eventy"):
            import time
            now = time.time()
            events = v1200_rotating_events(now)
            await self.send(f"WYDARZENIA WIELKIEGO ŚWIATA: {len(events)}. Zmiana za około {int((events[0]['expires_at']-now)//60) if events else 0} minut.")
            for event in events:
                room=ROOMS[event['room_id']]
                await self.send(f"{event['title']}; {room['name']}, {room['zone']}; "
                                f"typ {event['rank']}; liczba przeciwników {event['count']}.")
            await self.send("Wydarzenia są rzeczywistymi walkami po wejściu do lokacji. Nie rozpoczynają ataku same.")
            return
        for key,spec in V1200_REGIONAL_INDEX.items():
            if query in (self.normalize_room_query(key), self.normalize_room_query(spec['name'])) or query in self.normalize_room_query(spec['name']):
                await self.send(f"KRAINA: {spec['name']}. Zalecany etap od {spec['stage']}. "
                                f"Wejście: {ROOMS[spec['entry']]['name']}; osada: {ROOMS[spec['town']]['name']}; "
                                f"boss: {ROOMS[spec['arena']]['name']}. 16 terenów, 3 zadania.")
                path = self.shortest_path(self.character.room_id, spec['entry'])
                if path is None:
                    await self.send("Nie znalazłem połączenia w aktualnej mapie.")
                elif not path:
                    await self.send("Jesteś na wejściu do tej krainy.")
                else:
                    direction, room = path[0]
                    await self.send(f"Trasa: {len(path)} przejść. Pierwszy krok: "
                                    f"{self.route_direction_name(direction)} — {ROOMS[room]['name']}.")
                return
        await self.send("Nie znam takiej krainy. Wpisz krainy, aby przeczytać nazwy.")
