# -*- coding: utf-8 -*-
"""Modul v109: frontier_weather; oryginalne metody bez zmian AST."""
from .dependencies import *

class FrontierWeatherV109Mixin:

    async def register_v0140_world_event_visit(self, room_id):
            event = v0140_event_for_room(room_id)
            if not event:
                return False
            is_new = self.server.db.add_collection_entry(
                self.account_id, "world_events_v0140", event["token"]
            )
            if is_new:
                await self.advance_v0140_quest_progress("world_event", event["type"], 1)
                await self.advance_bounty("event", event["type"], 1)
                await self.advance_dynamic_world_quest_v015("event", event["type"], 1)
                self.server.db.add_collection_entry(self.account_id, "event_types_v015", event["type"])
                await self.add_faction_reputation_v016("cartographers", 1, reason="world_event")
            return is_new

    async def show_weather_v015(self):
            identity = v0130_frontier_room_identity(self.character.room_id)
            phase = v0150_time_state()
            if not identity:
                await self.send(f"Pora świata: {phase['label']}. W stałym rdzeniu pogoda jest spokojna i nie wpływa na dostępność zawartości.")
                return
            weather = v0150_weather_state(self.character.room_id)
            await self.send(f"Pora świata: {phase['label']}. Pogoda: {weather['label']}.")
            for tool, label in (("fishing","Wędkarstwo"),("herbalism","Zielarstwo"),("mining","Górnictwo"),("woodcutting","Drwalstwo")):
                bonus = v0150_environment_bonus(self.character.room_id, tool)
                if bonus["xp_mult"] > 1.0:
                    await self.send(f"{label}: +{int(round((bonus['xp_mult']-1.0)*100))}% XP z warunków świata.")
            await self.send("Pogoda nie blokuje questów, ruchu, walki ani profesji. Brak pułapek pogodowych.")

    def biome_mastery_state_v015(self, kind):
            if kind not in V013_FRONTIER_SPECS:
                return (0, V013_FRONTIER_ROOMS_PER_BIOME, 0)
            discovered = self.server.db.discovered_room_ids(self.account_id)
            ids = set(v0130_frontier_room_ids(kind))
            count = len(ids.intersection(discovered))
            total = len(ids)
            pct = int(count * 100 / max(1,total))
            return count, total, pct

    async def check_biome_mastery_v015(self, kind):
            if kind not in V013_FRONTIER_SPECS:
                return
            count,total,pct = self.biome_mastery_state_v015(kind)
            for threshold in V015_BIOME_MASTERY_THRESHOLDS:
                if pct < threshold:
                    continue
                entry = f"{kind}:{threshold}"
                if self.server.db.add_collection_entry(self.account_id, "biome_mastery_v015", entry):
                    title = v0150_biome_mastery_title(kind, threshold)
                    await self.send(f"Biome Mastery: {V013_FRONTIER_SPECS[kind]['zone']} {threshold}%. {count} z {total} sektorów.")
                    await self.unlock_title(f"biome:{entry}", title)

    async def show_biome_mastery_v015(self, args=""):
            query = normalize_lookup_text(args)
            selected = None
            if query:
                for kind,spec in V013_FRONTIER_SPECS.items():
                    if query in (normalize_lookup_text(kind), normalize_lookup_text(spec['zone'])):
                        selected = kind; break
            kinds = (selected,) if selected else tuple(V013_FRONTIER_SPECS)
            await self.send("BIOME MASTERY")
            for kind in kinds:
                await self.check_biome_mastery_v015(kind)
                count,total,pct = self.biome_mastery_state_v015(kind)
                await self.send(f"{V013_FRONTIER_SPECS[kind]['zone']}: {count} z {total}, {pct}%.")

    async def show_collection_world_v015(self):
            await self.send("KODEKS KOLEKCJI — ŚWIAT")
            for kind in V013_FRONTIER_SPECS:
                await self.check_biome_mastery_v015(kind)
            mastery = self.server.db.collection_entry_ids(self.account_id, "biome_mastery_v015")
            weather = self.server.db.collection_entry_ids(self.account_id, "weather_v015")
            secrets = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            discovered_rooms = self.server.db.discovered_room_ids(self.account_id)
            minis = {rid for rid in discovered_rooms if ROOMS.get(rid, {}).get("v0140_mini_final")}
            event_tokens = self.server.db.collection_entry_ids(self.account_id, "world_events_v0140")
            events = {token.split(":", 2)[1] for token in event_tokens if token.count(":") >= 2}
            total_weather = sum(len(set(pool)) for pool in V015_WEATHER_POOLS.values())
            await self.send(f"Biome Mastery: {len(mastery)} z {len(V013_FRONTIER_SPECS)*len(V015_BIOME_MASTERY_THRESHOLDS)} progów.")
            await self.send(f"Poznane wzorce pogody: {len(weather)} z {total_weather} kombinacji biom-pogoda.")
            await self.send(f"Sekrety świata: {len(secrets)} z {len(v0140_surface_secret_room_ids())}.")
            await self.send(f"Finały mini-lochów odkryte: {len(minis)}.")
            await self.send(f"Typy eventów odwiedzone: {len(events)} z {len(V014_WORLD_EVENT_DEFS)}.")

    async def handle_dynamic_world_quest_v015(self, args=""):
            raw = normalize_lookup_text(args)
            row = self.server.db.dynamic_world_quest_v015(self.account_id)
            active = dict(row) if row else None
            offer = v0150_dynamic_world_offer(self.account_id)
            if raw in ("", "oferta", "offer"):
                if active:
                    await self.send(f"Aktywne zadanie świata: {active['label']}. Postęp {active['progress']} z {active['needed']}.")
                await self.send(f"Aktualna oferta: {offer['label']}. Cel {offer['needed']}. Nagroda: {offer['reward_soul_xp']} Soul XP i " + currency_reading_text(0, int(offer['reward_gold']), 0) + ".")
                await self.send("Komendy: worldquest accept, worldquest aktywne, worldquest odbierz, worldquest porzuc.")
                return
            if raw in ("accept","przyjmij","przyjmij zadanie"):
                if active:
                    await self.send("Masz już aktywne dynamiczne zadanie świata.")
                    return
                self.server.db.save_dynamic_world_quest_v015(self.account_id, offer)
                await self.send(f"Przyjęto: {offer['label']}. Postęp 0 z {offer['needed']}.")
                return
            if raw in ("aktywne","active","status"):
                if not active:
                    await self.send("Nie masz aktywnego dynamicznego zadania świata.")
                    return
                await self.send(f"{active['label']}. Postęp {active['progress']} z {active['needed']}." + (" Cel wykonany; użyj worldquest odbierz." if active['completed'] else ""))
                return
            if raw in ("porzuc","porzuć","abandon"):
                if not active:
                    await self.send("Nie masz aktywnego zadania.")
                    return
                self.server.db.clear_dynamic_world_quest_v015(self.account_id)
                await self.send("Porzucono dynamiczne zadanie świata.")
                return
            if raw in ("odbierz","claim","nagroda"):
                if not active or not active['completed']:
                    await self.send("Dynamiczne zadanie świata nie jest jeszcze ukończone.")
                    return
                dynamic_stage=max(0,int(active.get("stage",0) or 0))
                if dynamic_stage<=0:
                    key_parts=str(active.get("quest_key") or "").split(":")
                    biome_key=key_parts[3] if len(key_parts)>3 else ""
                    dynamic_stage=max(
                        1,
                        int(
                            V013_FRONTIER_SPECS.get(biome_key,{}).get(
                                "base_mastery",1
                            )
                            or 1
                        ),
                    )
                await self.grant_soul_xp(
                    int(active["reward_soul_xp"]),
                    content_level=dynamic_stage,
                    content_scaled=True,
                )
                self.character.gold += int(active['reward_gold'])
                self.server.db.save_character(self.character)
                self.server.db.add_lifetime_stat(self.account_id, "dynamic_world_quests_completed", 1)
                label = active['label']
                self.server.db.clear_dynamic_world_quest_v015(self.account_id)
                await self.send(f"Ukończono dynamiczne zadanie: {label}. Nagroda odebrana.")
                return
            await self.send("Użycie: worldquest; worldquest accept; worldquest aktywne; worldquest odbierz; worldquest porzuc.")

    async def advance_dynamic_world_quest_v015(self, kind, target=None, amount=1):
            row = self.server.db.dynamic_world_quest_v015(self.account_id)
            if not row:
                return False
            active = dict(row)
            if active.get("completed"):
                return False
            qtype = str(active.get("quest_type") or "")
            if qtype != str(kind or ""):
                return False
            wanted = str(active.get("target") or "any")
            if wanted not in ("any", str(target)):
                return False
            old = max(0,int(active.get("progress",0)))
            needed = max(1,int(active.get("needed",1)))
            new = min(needed, old + max(0,int(amount)))
            if new <= old:
                return False
            active["progress"] = new
            active["completed"] = new >= needed
            self.server.db.save_dynamic_world_quest_v015(self.account_id, active)
            await self.send(f"Dynamiczne zadanie: {active['label']}. Postęp {new} z {needed}." + (" Cel wykonany." if new >= needed else ""))
            return True
