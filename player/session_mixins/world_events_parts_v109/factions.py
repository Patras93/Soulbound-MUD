# -*- coding: utf-8 -*-
"""Modul v109: factions; oryginalne metody bez zmian AST."""
from .dependencies import *

class FactionsV109Mixin:

    async def add_faction_reputation_v016(self, faction_id, amount=1, reason=""):
            if faction_id not in V016_FACTIONS:
                return 0
            old = self.server.db.faction_reputation_v016(self.account_id, faction_id)
            from systems.live_olc26_world import faction_reward
            amount = faction_reward(faction_id, amount)
            from systems.live_olc27_master import faction_extra
            amount = faction_extra(faction_id, amount)
            new = self.server.db.add_faction_reputation_v016(self.account_id, faction_id, amount)
            old_rank = v0160_faction_rank(old)
            new_rank = v0160_faction_rank(new)
            if new_rank != old_rank:
                await self.send(f"Reputacja: {V016_FACTIONS[faction_id]['name']} — {new_rank}, {new} pkt.")
            for threshold in V016_FACTION_THRESHOLDS:
                if not (old < threshold <= new):
                    continue
                reward_key = f"{faction_id}:{threshold}"
                if not self.server.db.add_collection_entry(self.account_id, "faction_rewards_v016", reward_key):
                    continue
                if threshold == 25:
                    await self.unlock_title(f"faction:{reward_key}", f"Przyjaciel: {V016_FACTIONS[faction_id]['name']}")
                elif threshold == 75:
                    self.server.db.add_item(self.account_id, V014_TREASURE_MAP_ITEM, 1)
                    await self.send(f"Nagroda frakcji: {ITEMS[V014_TREASURE_MAP_ITEM]['name']} x1.")
                elif threshold == 150:
                    badge = f"v016_badge_{faction_id}"
                    self.server.db.add_item(self.account_id, badge, 1)
                    await self.record_item_collection(badge, source=V016_FACTIONS[faction_id]["name"], announce=True)
                elif threshold == 300:
                    self.server.db.add_item(self.account_id, "soul_elixir", 3)
                    await self.unlock_title(f"faction:{reward_key}", f"Mistrz: {V016_FACTIONS[faction_id]['name']}")
                    await self.send("Nagroda frakcji: Eliksir Duszy x3.")
            return new

    async def show_factions_v016(self, args=""):
            query = normalize_lookup_text(args)
            await self.send("FRAKCJE ŚWIATA")
            matched = False
            for faction_id, data in V016_FACTIONS.items():
                if query and query not in (normalize_lookup_text(faction_id), normalize_lookup_text(data["name"])) and query not in normalize_lookup_text(data["name"]):
                    continue
                matched = True
                rep = self.server.db.faction_reputation_v016(self.account_id, faction_id)
                await self.send(f"{data['name']}: {rep} pkt, ranga {v0160_faction_rank(rep)}. {data['desc']}")
            if query and not matched:
                await self.send("Nie rozpoznaję takiej frakcji.")

    async def show_legendary_rares_v016(self):
            now = time.time()
            entries = v0160_active_legendary_rares(now)
            remaining = max(0, int(entries[0]["expires_at"]-now)) if entries else 0
            await self.send(f"LEGENDARY RARE — rotacja za około {remaining} sekund.")
            for i,e in enumerate(entries,1):
                template=MOB_TEMPLATES[e["template_id"]]
                await self.send(f"{i}. {template['name']}. Ostatni trop: {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}. Może wędrować po zmaterializowanej części biomu.")
            await self.send("Legendary rare są pasywne i nie atakują pierwsze.")

    async def show_travelers_v016(self):
            await self.send("WĘDRUJĄCY NPC")
            for npc_id,data in V016_TRAVELERS.items():
                rid=v0160_traveler_room(npc_id)
                room=ROOMS.get(rid,{})
                await self.send(f"{data['name']}: {room.get('name', rid)}, strefa {room.get('zone','nieznana')}.")

    async def show_faction_stories_v017(self, args=""):
            query = normalize_lookup_text(args)
            rows = {row["quest_id"]: row for row in self.server.db.quest_rows(self.account_id)}
            await self.send("HISTORIE FRAKCJI")
            shown = 0
            for faction_id, chain in V017_FACTION_STORY_QUESTS.items():
                faction_name = V016_FACTIONS[faction_id]["name"]
                title = V017_FACTION_STORIES[faction_id]["title"]
                if query and query not in normalize_lookup_text(faction_id) and query not in normalize_lookup_text(faction_name) and query not in normalize_lookup_text(title):
                    continue
                completed = sum(1 for qid in chain if rows.get(qid, {}).get("status") == "completed")
                active = [qid for qid in chain if rows.get(qid, {}).get("status") == "active"]
                state = f"ukończone {completed}/6"
                if active:
                    qid = active[0]
                    row = rows[qid]
                    state += f", aktywny: {QUESTS[qid]['name']} {row['progress']}/{QUESTS[qid]['needed']}"
                elif completed == 6:
                    state += ", historia zakończona"
                await self.send(f"{faction_name} — {title}: {state}.")
                shown += 1
            if not shown:
                await self.send("Nie rozpoznaję takiej historii frakcji.")
