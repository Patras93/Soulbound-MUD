# -*- coding: utf-8 -*-
"""Modul v109: expeditions_transport; oryginalne metody bez zmian AST."""
from .dependencies import *

class ExpeditionsTransportV109Mixin:

    async def show_season_v018(self):
            season=v0180_season_state()
            remaining=max(0,int(season["expires_at"]-time.time()))
            await self.send(f"SEZON: {season['label']}. {season['desc']} Zmiana za około {remaining//60} minut.")
            await self.send("Sezon nie blokuje zawartości. Daje tylko małe premie ekologiczne do wybranych profesji.")

    async def show_expeditions_v018(self):
            await self.send("EKSPEDYCJE OCEANICZNE")
            discovered=self.server.db.discovered_room_ids(self.account_id)
            for key,data in V018_EXPEDITIONS.items():
                root=v0180_archipelago_room_id(key,0,0)
                state="odkryta" if root in discovered else "nieodkryta"
                await self.send(f"{key}: {data['name']}. Zalecana Biegłość {data['mastery']}. {state}. 16 sektorów.")
            await self.send("Wypłynięcie: ekspedycja <nazwa>. Start tylko z Portu Dusz lub Przystani Bractwa Wód.")

    async def start_expedition_v018(self, args=""):
            query=normalize_lookup_text(args)
            if self.combat_mob_key:
                await self.send("Nie możesz rozpocząć ekspedycji podczas walki."); return
            if self.character.room_id not in {"harbor","v016_waters_square"}:
                await self.send("Ekspedycje wypływają z Portu Dusz albo Nabrzeża Bractwa Wód."); return
            chosen=None
            for key,data in V018_EXPEDITIONS.items():
                if query in (normalize_lookup_text(key),normalize_lookup_text(data["name"])) or (query and query in normalize_lookup_text(data["name"])):
                    chosen=key; break
            if not chosen:
                await self.show_expeditions_v018(); return
            target=v0180_archipelago_room_id(chosen,0,0)
            self.server.world.ensure_runtime_room(target)
            old=self.character.room_id; self.previous_room_id=old; self.character.room_id=target
            self.server.db.save_character(self.character)
            await self.send(f"Wypływasz na ekspedycję: {V018_EXPEDITIONS[chosen]['name']}.")
            await self.look()

    async def handle_transport_v018(self, args=""):
            query=normalize_lookup_text(args)
            discovered=self.server.db.discovered_room_ids(self.account_id)
            if not query:
                await self.send("TRANSPORT — dostępne odkryte cele:")
                for key,rid in V018_TRANSPORT_HUBS.items():
                    if rid in discovered or rid in ("market","harbor","temple"):
                        await self.send(f"{key}: {ROOMS.get(rid,{}).get('name',rid)}")
                await self.send("Użycie: transport <cel>. Musisz stać w jednym z hubów transportowych.")
                return
            if self.combat_mob_key:
                await self.send("Nie możesz korzystać z transportu podczas walki."); return
            if self.character.room_id not in V018_TRANSPORT_ORIGINS:
                await self.send("Transport działa tylko z odkrytych hubów: miasta, osad frakcji i Bramy Rubieży Końca."); return
            chosen=None
            for key,rid in V018_TRANSPORT_HUBS.items():
                name=ROOMS.get(rid,{}).get("name",rid)
                if query in (normalize_lookup_text(key),normalize_lookup_text(name)) or (query and query in normalize_lookup_text(name)):
                    chosen=(key,rid); break
            if not chosen:
                await self.send("Nie rozpoznaję celu transportu. Wpisz transport bez argumentu."); return
            key,target=chosen
            if target not in discovered and target not in ("market","harbor","temple"):
                await self.send("Najpierw musisz odkryć ten hub normalną eksploracją."); return
            self.server.world.ensure_runtime_room(target)
            old=self.character.room_id; self.previous_room_id=old; self.character.room_id=target
            self.server.db.save_character(self.character)
            await self.send(f"Transport: docierasz do {ROOMS[target]['name']}.")
            await self.look()

    async def show_great_ruins_v018(self):
            ruins=v0180_all_great_ruins()
            discovered=self.server.db.discovered_room_ids(self.account_id)
            found=0
            for kind,x,y,size in ruins:
                if v0130_frontier_room_id(kind,x,y) in discovered:
                    found+=1
            await self.send(f"WIELKIE RUINY: {len(ruins)} możliwych kompleksów w świecie; odnalezione wejścia {found}.")
            await self.send("Każdy kompleks ma 20-40 pokoi, pętle i finałowego pasywnego strażnika. Brak pułapek.")

    async def show_legendary_events_v018(self):
            await self.send("LEGENDARNE WYDARZENIA ŚWIATA")
            for i,e in enumerate(v0180_active_legendary_events(),1):
                zone=V013_FRONTIER_SPECS[e["kind"]]["zone"]
                await self.send(f"{i}. {e['title']}. {zone}, sektor {e['x']+1}-{e['y']+1}. {e['desc']}")

    async def show_endless_v018(self):
            depth=v0180_endless_identity(self.character.room_id)
            if depth:
                await self.send(f"RUBIEŻ KOŃCA: sektor {depth}, pasmo trudności {v0180_endless_band(depth)}/{V018_ENDLESS_POWER_CAP_BAND}.")
            else:
                await self.send("RUBIEŻ KOŃCA: wejście znajduje się przy proceduralnej Bramie Korony. Prowadzenie: prowadź rubież końca.")
            await self.send("Mapa nie ma sztywnego końca, ale skalowanie walki ma twardy cap. PASSIVE WORLD i brak pułapek obowiązują wszędzie.")
