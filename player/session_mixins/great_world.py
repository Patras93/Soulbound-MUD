# -*- coding: utf-8 -*-
"""Short, read-only v1.20.0 regional atlas commands designed for NVDA."""
from __future__ import annotations

from data.catalogs import ROOMS
from world.great_world import V1200_GATE, V1200_REGIONAL_INDEX, V1200_REGIONS, V1210_EXPEDITION_INDEX, v1200_rotating_events


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

    async def market_quotes_command_v1260(self, args=''):
        from systems.market_quotes_v1260 import market_quotes_v1260
        for line in market_quotes_v1260():
            await self.send(line)

    async def grand_expedition_v1260(self, args=''):
        from systems.grand_expedition_v1260 import STAGES
        mode=str(args or '').strip().casefold()
        db=self.server.db
        if mode in ('start','rozpocznij','przyjmij'):
            started=db.grand_expedition_start_v1260(self.account_id)
            await self.send('WIELKA WYPRAWA: start. Trasa: miasto, ocean, loch, kopalnia. '
                            'Solo i drużynowo, normalne przejścia.' if started else
                            'Wielka wyprawa jest już aktywna. Wpisz wielkawyprawa postep.')
            return
        state=db.grand_expedition_state_v1260(self.account_id)
        if not state:
            await self.send('WIELKA WYPRAWA: brak aktywnej wyprawy. Komenda: wielkawyprawa start.')
            return
        stage=int(state['stage'])
        if mode in ('odbierz','nagroda','claim'):
            if stage<4 or state['completed']:
                await self.send('Nagroda niedostępna. Wpisz wielkawyprawa postep.')
                return
            cycle=db.grand_expedition_claim_v1260(self.account_id)
            if cycle is None:
                await self.send('Ta nagroda została już odebrana.')
                return
            level=max(1,int(getattr(self.character,'character_level',1) or 1))
            payout=max(1000,int((level + 25)**2 * (1 + cycle*.1)))
            self.character.gold += payout
            db.save_character(self.character)
            await self.send(f'WIELKA WYPRAWA UKOŃCZONA! Nagroda: {payout} złota. '
                            'Możesz rozpocząć kolejną wielkawyprawa start.')
            return
        await self.send(f'WIELKA WYPRAWA: cykl {state["cycle"]}, {stage} z 4 etapów zaliczonych.')
        if state['completed']:
            await self.send('Ukończona. Wpisz wielkawyprawa start, aby rozpocząć kolejną.')
        elif stage>=4:
            await self.send('Wszystkie etapy gotowe. Wpisz wielkawyprawa odbierz.')
        else:
            await self.send(f'Następny etap: {STAGES[stage][1]} Wykonuj zwykłe przejścia; '
                            'postęp zapisuje się automatycznie.')

    async def grand_expedition_visit_v1260(self, room_id):
        from systems.grand_expedition_v1260 import expedition_region_v1260, STAGES
        from core.classes_skills import ROOMS
        category=expedition_region_v1260(room_id,ROOMS.get(room_id,{}))
        if not category:
            return
        stage=self.server.db.grand_expedition_visit_v1260(self.account_id,category)
        if stage:
            await self.send(f'WIELKA WYPRAWA: etap {stage} z 4 zaliczony! '
                            + ('Możesz użyć wielkawyprawa odbierz.' if stage==4
                               else f'Następny cel: {STAGES[stage][1]}'))

    async def legendary_expeditions_v1210(self, args=""):
        """NVDA-safe read-only status of real quests and traversable expeditions."""
        if not self.character:
            await self.send("Legendarne wyprawy: najpierw wybierz postać.")
            return
        query = self.normalize_room_query(args)
        if query in ("", "lista", "pomoc", "help"):
            await self.send("LEGENDARNE WYPRAWY 1.21.0: cztery szlaki. Bez pułapek i wymogu drużyny.")
            for spec in V1210_EXPEDITION_INDEX.values():
                await self.send(f"{spec['title']}; region {spec['region']}; etap {spec['stage']}. "
                                "Cztery zadania i godzinny kontrakt.")
            await self.send("Użycie: legendarnewyprawy <nazwa>, legendarnewyprawy postep; "
                            "quest list u Mistrza Wyprawy, aby przyjąć zadanie.")
            return
        if query in ("postep", "postęp", "osiagniecia", "kronika", "status"):
            if self.account_id is None:
                await self.send("Wybierz postać, aby odczytać trwały postęp.")
                return
            await self.send("KRONIKA LEGENDARNYCH WYPRAW: ukończone etapy i kontrakty z bazy postaci.")
            for spec in V1210_EXPEDITION_INDEX.values():
                states=[]
                for qid in spec['quests']:
                    row=self.server.db.quest(self.account_id,qid)
                    states.append((row['status'] if row else "nieprzyjęte"))
                b=self.server.db.quest(self.account_id,spec['contract'])
                await self.send(f"{spec['title']}: etapy " + ", ".join(
                    f"{i+1} {state}" for i,state in enumerate(states)) +
                    f". Kontrakt: {b['status'] if b else 'nieprzyjęty'}.")
            return
        for key,spec in V1210_EXPEDITION_INDEX.items():
            if query in (key,self.normalize_room_query(spec['title'])) or query in self.normalize_room_query(spec['title']):
                await self.send(f"WYPRAWA: {spec['title']}. Etap {spec['stage']}, {spec['region']}. "
                                f"Wejście: {ROOMS[spec['entry']]['name']}. "
                                f"Boss: {ROOMS[spec['rooms'][-1]]['name']}.")
                route=self.shortest_path(self.character.room_id,spec['entry'])
                if route is None:
                    await self.send("Brak połączenia na aktualnej mapie.")
                elif not route:
                    await self.send("Jesteś przy wejściu do wyprawy.")
                else:
                    direction,room=route[0]
                    await self.send(f"Trasa: {len(route)} przejść. "
                                    f"Pierwszy krok: {self.route_direction_name(direction)} do {ROOMS[room]['name']}.")
                await self.send("Wróć do Mistrza Wyprawy po każdym etapie; skarbiec jest przy bossie.")
                return
        await self.send("Nie znam takiej wyprawy. Wpisz legendarnewyprawy, żeby przeczytać listę.")
