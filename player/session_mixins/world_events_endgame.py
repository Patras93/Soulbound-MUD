# -*- coding: utf-8 -*-
"""Weather, factions, events, ascension and endgame systems."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import random
import time
from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, currency_unit_multiplier
from network.protocol_gameplay_utils import find_by_name
from player.session_mixins.equipment_stats import CLASS_MASTERY_MAX_LEVEL, REGIONAL_SET_BONUSES, v0210_world_tier_multipliers
from player.session_mixins.io_auth_character import CLASSES
from player.session_mixins.museum_bounty import (
    ITEMS,
    MOB_TEMPLATES,
    QUESTS,
    ROOMS,
    currency_reading_text,
    normalize_lookup_text,
    player_item_display_name_v0335,
)
from storage.db_schema import FISH_RESOURCE_IDS, legacy_currency_to_coins
from systems.items_resources import fish_rarity_label, format_fish_length, format_fish_weight
from world.generation_systems import (
    V013_FRONTIER_ROOMS_PER_BIOME,
    V013_FRONTIER_SPECS,
    V014_EVENT_DEFS as V014_WORLD_EVENT_DEFS,
    V014_TREASURE_MAP_ITEM,
    V015_BIOME_MASTERY_THRESHOLDS,
    V015_WEATHER_POOLS,
    V016_FACTIONS,
    V016_FACTION_THRESHOLDS,
    V016_TRAVELERS,
    V017_ARTIFACTS,
    V017_BIOME_SET_NAMES,
    V017_FACTION_STORIES,
    V017_FACTION_STORY_QUESTS,
    V018_ENDLESS_POWER_CAP_BAND,
    V018_EXPEDITIONS,
    V018_TRANSPORT_HUBS,
    V018_TRANSPORT_ORIGINS,
    V020_ARTIFACT_MAX_TIER,
    V020_ARTIFACT_UPGRADE_COSTS,
    V020_ARTIFACT_VARIANTS,
    V020_ENDGAME_GOALS,
    V020_GAUNTLETS,
    V020_GAUNTLET_LOBBY,
    V020_MEGADUNGEONS,
    v0130_frontier_room_id,
    v0130_frontier_room_identity,
    v0130_frontier_room_ids,
    v0140_active_world_events,
    v0140_event_for_room,
    v0140_surface_secret_room_ids,
    v0150_biome_mastery_title,
    v0150_dynamic_world_offer,
    v0150_environment_bonus,
    v0150_time_state,
    v0150_weather_state,
    v0160_active_legendary_rares,
    v0160_active_world_bosses,
    v0160_faction_rank,
    v0160_traveler_room,
    v0180_active_legendary_events,
    v0180_all_great_ruins,
    v0180_archipelago_room_id,
    v0180_endless_band,
    v0180_endless_identity,
    v0180_season_state,
    v0200_active_mythic_world_bosses,
    v0200_artifact_owned_tier,
    v0200_mega_gate_id,
    v0200_mega_identity,
    v0200_mega_is_boss_index,
)
from world.runtime_progression import (
    V021_ASCENSION_MAX_RANK,
    V021_MYTHIC_SET_NAMES,
    V021_WORLD_TIER_ASCENSION_REQUIREMENT,
    V021_WORLD_TIER_MAX,
    V022_LEGENDARY_KINDS,
    V022_PROJECT_CATEGORY_LABELS,
    V022_PROJECT_RESOURCE_SOURCES,
    V022_WORLD_PROJECTS,
    V027_LEGENDARY_MIN_MASTERY,
    v0210_ascension_xp_to_next,
    v0210_endless_gauntlet_identity,
    v0210_endless_gauntlet_room_id,
    v022_fish_rarity_score,
    v022_legendary_contract_offer,
    v022_project_reward,
)
from world.world_state import v0290_active_world_events


class SessionWorldEventsEndgameMixin:

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
                await self.grant_soul_xp(int(active['reward_soul_xp']))
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

    async def add_faction_reputation_v016(self, faction_id, amount=1, reason=""):
            if faction_id not in V016_FACTIONS:
                return 0
            old = self.server.db.faction_reputation_v016(self.account_id, faction_id)
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

    async def show_world_bosses_v016(self):
            now = time.time()
            bosses = v0160_active_world_bosses(now)
            remaining = max(0, int(bosses[0]["expires_at"]-now)) if bosses else 0
            await self.send(f"BOSSOWIE ŚWIATA — rotacja za około {remaining} sekund.")
            for i, e in enumerate(bosses,1):
                template = MOB_TEMPLATES[e["template_id"]]
                await self.send(f"{i}. {template['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie world bossy są pasywne. Walkę rozpoczyna wyłącznie gracz.")

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

    def v0210_total_ascension_rank(self):
            return sum(int(r["rank"] or 0) for r in self.server.db.ascension_rows_v021(self.account_id) if str(r["track"]).startswith("class:"))

    def v0210_any_class_at_400(self):
            row=self.server.db.conn.execute("SELECT MAX(level) AS mx FROM class_progress WHERE account_id=?",(self.account_id,)).fetchone()
            return int(row["mx"] or 0)>=CLASS_MASTERY_MAX_LEVEL if row else False

    async def show_ascension_v021(self,args=""):
            q=normalize_lookup_text(args); rows={str(r["track"]):r for r in self.server.db.ascension_rows_v021(self.account_id)}
            await self.send("WZNIESIENIE KLAS — po Biegłości 600, bez resetu")
            shown=0
            for cname,_,_,_ in CLASSES:
                if q and q not in normalize_lookup_text(cname): continue
                prow=self.server.db.class_progress_row(self.account_id,cname)
                level=int(prow["level"] if prow else 1)
                row=rows.get(f"class:{cname}"); rank=int(row["rank"] or 0) if row else 0; xp=int(row["xp"] or 0) if row else 0
                if level<CLASS_MASTERY_MAX_LEVEL and not q: continue
                nxt=v0210_ascension_xp_to_next(rank)
                await self.send(f"{cname}: Biegłość {level}/{CLASS_MASTERY_MAX_LEVEL}; Wzniesienie {rank}/{V021_ASCENSION_MAX_RANK}; " + (f"XP {xp} z {nxt}." if nxt else "maksymalna Ranga Wzniesienia.")); shown+=1
            if not shown: await self.send("Żadna klasa nie osiągnęła jeszcze Biegłości 600.")
            await self.send(f"Łączna Ranga Wzniesienia: {self.v0210_total_ascension_rank()}.")

    async def handle_world_tier_v021(self,args=""):
            current=self.v0210_world_tier(); raw=str(args or "").strip()
            if not raw:
                m=v0210_world_tier_multipliers(current); total=self.v0210_total_ascension_rank()
                await self.send(f"WORLD TIER {current}/{V021_WORLD_TIER_MAX}. Efektywne HP przeciwników x{m['effective_hp']:.2f}, obrażenia x{m['enemy_damage']:.2f}, nagrody x{m['reward']:.2f}. Łączne Wzniesienie: {total}.")
                await self.send("Ustawienie: worldtier <1-10>. PASSIVE WORLD nadal obowiązuje."); return
            if self.combat_mob_key:
                await self.send("World Tier można zmienić tylko poza walką."); return
            if not raw.isdigit():
                await self.send("Użycie: worldtier <1-10>."); return
            tier=int(raw)
            if not 1<=tier<=V021_WORLD_TIER_MAX:
                await self.send("World Tier musi być od 1 do 10."); return
            if tier>=2 and not self.v0210_any_class_at_400():
                await self.send("World Tier 2+ wymaga co najmniej jednej klasy z Biegłością 600."); return
            need=V021_WORLD_TIER_ASCENSION_REQUIREMENT[tier]; total=self.v0210_total_ascension_rank()
            if total<need:
                await self.send(f"World Tier {tier} wymaga łącznej Rangi Wzniesienia {need}. Masz {total}."); return
            self.server.db.set_world_tier_v021(self.account_id,tier); m=v0210_world_tier_multipliers(tier)
            await self.send(f"Ustawiono World Tier {tier}. Efektywne HP x{m['effective_hp']:.2f}, obrażenia przeciwników x{m['enemy_damage']:.2f}, nagrody x{m['reward']:.2f}.")

    async def show_mythic_sets_v021(self,args=""):
            q=normalize_lookup_text(args); counts=self.v0210_mythic_set_counts(); shown=0
            await self.send("MITYCZNE ZESTAWY 8-CZĘŚCIOWE")
            for key,name in V021_MYTHIC_SET_NAMES.items():
                if q and q not in normalize_lookup_text(key) and q not in normalize_lookup_text(name): continue
                count=int(counts.get(key,0)); await self.send(f"{name}: {count}/13. Progi: 2 HP/Mana +6%; 4 obrażenia +6%; 6 obrona +8%; 8 dodatkowo +5% do wszystkich trzech."); shown+=1
            if not shown: await self.send("Nie rozpoznaję takiego mitycznego zestawu.")

    def v0210_live_endless_gauntlet_boss(self,room_id):
            self.server.world.refresh()
            return next((m for m in self.server.world.mobs.values() if m.alive and m.room_id==room_id and MOB_TEMPLATES.get(m.template_id,{}).get("v021_endless_gauntlet")),None)

    def v0210_endless_gauntlet_blocked(self,room_id,direction):
            return v0210_endless_gauntlet_identity(room_id) is not None and direction=="north" and self.v0210_live_endless_gauntlet_boss(room_id) is not None

    async def handle_endless_gauntlet_v021(self,args=""):
            best=self.server.db.endless_gauntlet_best_v021(self.account_id); raw=normalize_lookup_text(args)
            if raw in ("status","info"):
                await self.send(f"ENDLESS GAUNTLET: najlepsza ukończona runda {best}. Co 5 rund rośnie pasmo trudności; maksymalne pasmo 100."); return
            if self.character.room_id!=V020_GAUNTLET_LOBBY:
                await self.send("Endless Gauntlet rozpoczyna się w Sali Boss Gauntletów przy Straży Rubieży."); return
            start=max(1,best+1) if raw in ("dalej","continue","kontynuuj") else 1
            target=v0210_endless_gauntlet_room_id(start); self.server.world.ensure_runtime_room(target)
            self.previous_room_id=self.character.room_id; self.character.room_id=target; self.server.db.save_character(self.character)
            await self.send(f"Wchodzisz do Endless Gauntletu, runda {start}. Boss nie atakuje pierwszy."); await self.look()

    async def show_mythic_progression_v021(self):
            total=self.v0210_total_ascension_rank(); wt=self.v0210_world_tier(); best=self.server.db.endless_gauntlet_best_v021(self.account_id)
            t10=sum(1 for fid in V017_ARTIFACTS if v0200_artifact_owned_tier(self.server.db,self.account_id,fid)[0]>=10)
            full=sum(1 for key,count in self.v0210_mythic_set_counts().items() if count>=8)
            await self.send("MITYCZNA PROGRESJA")
            await self.send(f"Łączna Ranga Wzniesienia: {total}. World Tier: {wt}/10. Endless Gauntlet: najlepsza runda {best}. Artefakty Tier 10: {t10}/5. Sety mityczne z końcowym bonusem 8/13: {full}/5.")

    def v022_project_key(self, raw):
            q=normalize_lookup_text(raw)
            aliases={"port":"port","port dusz":"port","bridge":"bridge","most":"bridge","most polnocny":"bridge","tower":"tower","wieza":"tower","wieza kartografow":"tower","settlement":"settlement","osada":"settlement","osada konca swiata":"settlement"}
            if q in aliases: return aliases[q]
            for key,spec in V022_WORLD_PROJECTS.items():
                if q==key or q in normalize_lookup_text(spec["name"]): return key
            return None

    async def show_world_projects_v022(self, args=""):
            q=str(args or "").strip(); key=self.v022_project_key(q) if q else None
            if q and not key:
                await self.send("Nie rozpoznaję projektu. Dostępne: port, bridge, tower, settlement."); return
            keys=[key] if key else list(V022_WORLD_PROJECTS)
            await self.send("PROJEKTY ŚWIATA — wspólne, trwałe projekty całego serwera")
            for pkey in keys:
                spec=V022_WORLD_PROJECTS[pkey]; state=self.server.db.world_project_state_v022(pkey); contrib=self.server.db.world_project_contribution_v022(pkey,self.account_id)
                await self.send(f"{pkey}: {spec['name']}. {'UKOŃCZONY' if state['completed'] else 'w budowie'}. Twój wkład: {contrib['points']} pkt; wymagane do nagrody {spec['min_points']} pkt.")
                for cat,need in spec["requirements"].items():
                    have=min(int(need),int(state["progress"].get(cat,0) or 0)); label=V022_PROJECT_CATEGORY_LABELS[cat]
                    if cat=="coins": await self.send(f"  {label}: {currency_reading_text(have,0,0)} z {currency_reading_text(need,0,0)}.")
                    else: await self.send(f"  {label}: {have} z {need}.")
            await self.send("Użycie: projekt oddaj <projekt> <drewno|rudy|ryby|ziola> <ilość>; projekt wplac <projekt> <kwota> <nominał>; projekt odbierz <projekt>.")

    async def handle_world_project_v022(self,args=""):
            parts=str(args or "").strip().split()
            if not parts: await self.show_world_projects_v022(); return
            action=normalize_lookup_text(parts[0])
            if action not in ("oddaj","contribute","wplac","wpłać","deposit","odbierz","claim"):
                await self.show_world_projects_v022(" ".join(parts)); return
            if len(parts)<2:
                await self.send("Podaj projekt: port, bridge, tower albo settlement."); return
            key=self.v022_project_key(parts[1])
            if not key: await self.send("Nie rozpoznaję projektu."); return
            spec=V022_WORLD_PROJECTS[key]; state=self.server.db.world_project_state_v022(key)
            if action in ("odbierz","claim"):
                if not state["completed"]: await self.send("Ten projekt nie jest jeszcze ukończony."); return
                c=self.server.db.world_project_contribution_v022(key,self.account_id)
                if c["reward_claimed"]: await self.send("Nagroda za ten projekt została już odebrana."); return
                if c["points"]<int(spec["min_points"]): await self.send(f"Do nagrody potrzeba osobistego wkładu {spec['min_points']} pkt. Masz {c['points']}."); return
                if not self.server.db.mark_world_project_reward_claimed_v022(key,self.account_id): await self.send("Nagroda jest już odebrana."); return
                reward=v022_project_reward(key); [await self.send(_m) for _m in self.add_character_xp_with_event(reward["character_xp"])]; await self.grant_class_xp(reward["class_xp"]); await self.grant_soul_xp(reward["soul_xp"]); self.character.silver=min(CURRENCY_SQLITE_SAFE_TOTAL,self.character.silver+reward["coins"]); self.server.db.save_character(self.character)
                self.server.db.unlock_title(self.account_id,f"v022_project_{key}",spec["title"]); self.server.db.add_lifetime_stat(self.account_id,"world_projects_claimed",1)
                await self.send(f"Odbierasz nagrodę projektu {spec['name']}: {reward['class_xp']} Class XP, {reward['soul_xp']} Soul XP, {currency_reading_text(reward['coins'],0,0)} i tytuł {spec['title']}."); return
            if state["completed"]: await self.send("Projekt jest już ukończony."); return
            if action in ("wplac","wpłać","deposit"):
                if len(parts)<4 or not parts[2].isdigit(): await self.send("Użycie: projekt wplac <projekt> <kwota> <srebro|zloto|mithril>."); return
                amount=int(parts[2]); mult=currency_unit_multiplier(parts[3]);
                if amount<=0 or mult is None: await self.send("Nieprawidłowa kwota lub nominał."); return
                coins=amount*mult; remaining=max(0,int(spec["requirements"].get("coins",0))-int(state["progress"].get("coins",0) or 0)); coins=min(coins,remaining)
                wallet=legacy_currency_to_coins(self.character.silver,self.character.gold,self.character.mithril)
                if coins<=0: await self.send("Projekt nie potrzebuje już waluty."); return
                if wallet<coins: await self.send("Nie masz wystarczającej ilości waluty."); return
                wallet-=coins; self.character.silver=wallet; self.character.gold=0; self.character.mithril=0; self.server.db.save_character(self.character)
                pts=max(1,coins//1_000_000); result=self.server.db.add_world_project_contribution_v022(key,self.account_id,"coins",coins,pts)
                await self.send(f"Wpłacasz {currency_reading_text(result['accepted'],0,0)} na {spec['name']}. Twój wkład +{pts} pkt.")
            else:
                if len(parts)<4 or not parts[3].isdigit(): await self.send("Użycie: projekt oddaj <projekt> <drewno|rudy|ryby|ziola> <ilość>."); return
                cmap={"drewno":"wood","wood":"wood","rudy":"ore","ruda":"ore","ore":"ore","ryby":"fish","fish":"fish","ziola":"herbs","zioła":"herbs","herbs":"herbs"}; cat=cmap.get(normalize_lookup_text(parts[2])); amount=int(parts[3])
                if cat not in spec["requirements"]: await self.send("Ten projekt nie potrzebuje tego rodzaju zasobu."); return
                if amount<=0: await self.send("Ilość musi być dodatnia."); return
                container,get_ids=V022_PROJECT_RESOURCE_SOURCES[cat]; ids=tuple(get_ids()); remaining=max(0,int(spec["requirements"][cat])-int(state["progress"].get(cat,0) or 0)); amount=min(amount,remaining)
                have=self.server.db.total_items_across_storage_and_inventory(self.account_id,ids,container=container); take=min(amount,have)
                if take<=0: await self.send("Nie masz odpowiednich zasobów albo ten etap jest już wypełniony."); return
                if not self.server.db.consume_items_across_storage_and_inventory(self.account_id,ids,take,container=container): await self.send("Nie udało się przekazać zasobów."); return
                result=self.server.db.add_world_project_contribution_v022(key,self.account_id,cat,take,take); await self.send(f"Przekazujesz {take} sztuk: {V022_PROJECT_CATEGORY_LABELS[cat]}. Twój wkład +{take} pkt.")
            if result.get("newly_completed"):
                try:
                    self.server.db.record_server_project_v03811(
                        self.account_id, self.character.name, key
                    )
                except Exception:
                    pass
                for ss in list(self.server.sessions):
                    if getattr(ss,"character",None): await ss.send(f"WORLD PROJECT UKOŃCZONY: {spec['name']}! Współtwórcy z wymaganym wkładem mogą użyć projekt odbierz {key}.")

    def generate_legendary_contracts_v022(self):
            stage=max(V027_LEGENDARY_MIN_MASTERY,self.highest_active_class_mastery()); kinds=list(V022_LEGENDARY_KINDS); random.shuffle(kinds); return [v022_legendary_contract_offer(k,stage) for k in kinds[:3]]

    def ensure_legendary_contracts_v022(self):
            state=self.server.db.legendary_contract_state_v022(self.account_id)
            if not state["offers"]:
                state["offers"]=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=state["active"],completed_count=state["completed_count"])
            return state

    async def show_legendary_contracts_v022(self):
            if self.highest_active_class_mastery()<V027_LEGENDARY_MIN_MASTERY: await self.send(f"Legendarne kontrakty odblokowują się przy wygenerowanej Biegłości {V027_LEGENDARY_MIN_MASTERY} dowolnej aktywnej klasy."); return
            state=self.ensure_legendary_contracts_v022(); await self.send(f"LEGENDARNE KONTRAKTY. Ukończone: {state['completed_count']}.")
            active=state["active"]
            if active: await self.send(f"Aktywny: {active['label']}. Postęp {int(active.get('progress',0))} z {active['needed']}. Nagrody: {active['reward_class_xp']} Class XP, {active['reward_soul_xp']} Soul XP, {currency_reading_text(active['reward_coins'],0,0)}.")
            else: await self.send("Aktywny: brak.")
            for i,o in enumerate(state["offers"],1): await self.send(f"{i}. {o['label']}. Start 0 z {o['needed']}. Nagrody: {o['reward_class_xp']} Class XP, {o['reward_soul_xp']} Soul XP, {currency_reading_text(o['reward_coins'],0,0)}.")

    async def handle_legendary_contracts_v022(self,args=""):
            if self.highest_active_class_mastery()<V027_LEGENDARY_MIN_MASTERY: await self.show_legendary_contracts_v022(); return
            raw=normalize_lookup_text(args); state=self.ensure_legendary_contracts_v022(); active=state["active"]
            if not raw or raw in ("lista","list","status","info"): await self.show_legendary_contracts_v022(); return
            if raw in ("aktywne","aktywny","active","postep","postęp"):
                if not active: await self.send("Brak aktywnego legendarnego kontraktu."); return
                await self.send(f"{active['label']}: {int(active.get('progress',0))} z {active['needed']}."); return
            if raw in ("odbierz","claim"):
                if not active or int(active.get('progress',0))<int(active.get('needed',1)): await self.send("Legendarny kontrakt nie jest gotowy do odebrania."); return
                [await self.send(_m) for _m in self.add_character_xp_with_event(int(active.get('reward_character_xp',0)))]; await self.grant_class_xp(int(active['reward_class_xp'])); await self.grant_soul_xp(int(active['reward_soul_xp'])); self.character.silver=min(CURRENCY_SQLITE_SAFE_TOTAL,self.character.silver+int(active['reward_coins'])); self.server.db.save_character(self.character)
                completed=state["completed_count"]+1; self.server.db.add_lifetime_stat(self.account_id,"legendary_contracts_completed",1); offers=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=offers,active={},completed_count=completed)
                await self.send(f"LEGENDARNY KONTRAKT UKOŃCZONY. Nagroda: {active['reward_class_xp']} Class XP, {active['reward_soul_xp']} Soul XP i {currency_reading_text(active['reward_coins'],0,0)}."); return
            if raw in ("odswiez","odśwież","refresh"):
                if active: await self.send("Nie można odświeżyć ofert przy aktywnym legendarnym kontrakcie."); return
                offers=self.generate_legendary_contracts_v022(); self.server.db.save_legendary_contract_state_v022(self.account_id,offers=offers,active={},completed_count=state["completed_count"]); await self.show_legendary_contracts_v022(); return
            txt=raw
            for pref in ("accept ","przyjmij ","wez ","weź "):
                if txt.startswith(pref): txt=txt[len(pref):].strip(); break
            if txt.isdigit():
                if active: await self.send("Masz już aktywny legendarny kontrakt."); return
                idx=int(txt)-1
                if not 0<=idx<len(state["offers"]): await self.send("Nie ma takiego numeru oferty."); return
                active=dict(state["offers"][idx]); active["progress"]=0; self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=active,completed_count=state["completed_count"]); await self.send(f"Przyjęto: {active['label']}. Postęp 0 z {active['needed']}."); return
            await self.send("Użycie: legendarycontracts accept <1-3>; aktywne; odbierz; odswiez.")

    async def advance_legendary_contract_v022(self,kind,amount=1):
            state=self.server.db.legendary_contract_state_v022(self.account_id); active=state["active"]
            if not active or str(active.get("kind"))!=str(kind): return False
            old=int(active.get("progress",0)); need=int(active.get("needed",1)); new=min(need,old+max(0,int(amount)))
            if new<=old: return False
            active["progress"]=new; self.server.db.save_legendary_contract_state_v022(self.account_id,offers=state["offers"],active=active,completed_count=state["completed_count"])
            await self.send(f"Legendarny kontrakt: {active['label']}. Postęp {new} z {need}." + (" Cel wykonany — użyj legendarycontracts odbierz." if new>=need else "")); return True

    async def show_fish_records_v022(self,args=""):
            q=str(args or "").strip()
            if q:
                candidates={fid:{"name":ITEMS.get(fid,{}).get("name",fid)} for fid in FISH_RESOURCE_IDS if fid in ITEMS}; found=find_by_name(candidates,q)
                if not found: await self.send("Nie znam takiego gatunku ryby."); return
                fid,fish=found; personal=self.server.db.fish_journal_entry(self.account_id,fid); glob=self.server.db.fish_global_record_v022(fid)
                await self.send(f"REKORD GATUNKU: {fish['name']} — rzadkość {fish_rarity_label(fid)}.")
                if personal: await self.send(f"Twój rekord: {format_fish_length(personal['best_length_mm'])}, {format_fish_weight(personal['best_weight_g'])}.")
                else: await self.send("Twój rekord: brak połowu tego gatunku.")
                if glob: await self.send(f"Rekord serwera długości: {format_fish_length(glob['best_length_mm'])} — {glob['length_holder']}. Rekord masy: {format_fish_weight(glob['best_weight_g'])} — {glob['weight_holder']}.")
                else: await self.send("Rekord serwera: brak.")
                return
            rows=self.server.db.fish_journal_rows(self.account_id); await self.send("REKORDY WĘDKARSKIE")
            if rows:
                longest=max(rows,key=lambda r:int(r['best_length_mm'] or 0)); heaviest=max(rows,key=lambda r:int(r['best_weight_g'] or 0)); rarest=max(rows,key=lambda r:(v022_fish_rarity_score(str(r['fish_id'])),int(r['best_weight_g'] or 0)))
                await self.send(f"Twój najdłuższy okaz: {player_item_display_name_v0335(longest['fish_id'])}, {format_fish_length(longest['best_length_mm'])}.")
                await self.send(f"Twój najcięższy okaz: {player_item_display_name_v0335(heaviest['fish_id'])}, {format_fish_weight(heaviest['best_weight_g'])}.")
                await self.send(f"Twój najrzadszy odkryty gatunek: {player_item_display_name_v0335(rarest['fish_id'])}, {fish_rarity_label(rarest['fish_id'])}.")
            else: await self.send("Nie masz jeszcze zapisanych połowów.")
            personal_rare=self.server.db.fish_rarest_personal_v022(self.account_id)
            if personal_rare: await self.send(f"Twój najrzadszy okaz: {player_item_display_name_v0335(personal_rare['item_id'] or personal_rare['fish_id'])}; {personal_rare['rarity_label']}; {format_fish_weight(personal_rare['weight_g'])}.")
            rare=self.server.db.fish_rarest_global_v022()
            if rare: await self.send(f"Najrzadszy okaz serwera: {player_item_display_name_v0335(rare['item_id'] or rare['fish_id'])}; {rare['rarity_label']}; {format_fish_weight(rare['weight_g'])}; złowił {rare['holder_name']}.")
            top=self.server.db.fish_global_top_v022(5)
            if top:
                await self.send("Najcięższe rekordy gatunków na serwerze:")
                for i,row in enumerate(top,1): await self.send(f"{i}. {player_item_display_name_v0335(row['fish_id'])}: {format_fish_weight(row['best_weight_g'])} — {row['weight_holder']}.")
            await self.send("Szczegóły gatunku: rekordyryb <nazwa ryby>.")

    def v0200_live_blocking_boss(self, room_id, *, mega=False, gauntlet=False):
            self.server.world.refresh()
            for mob in self.server.world.mobs.values():
                if not mob.alive or mob.room_id != room_id: continue
                t=MOB_TEMPLATES.get(mob.template_id,{})
                if mega and t.get("v020_megadungeon_boss"): return mob
                if gauntlet and t.get("v020_gauntlet"): return mob
            return None

    def v0200_megadungeon_blocked(self, room_id, direction):
            ident=v0200_mega_identity(room_id)
            if not ident: return False
            key,index=ident
            if direction != "north" or not v0200_mega_is_boss_index(key,index): return False
            target=ROOMS.get(room_id,{}).get("exits",{}).get(direction); target_ident=v0200_mega_identity(target)
            if not target_ident or target_ident[1] <= index: return False
            dungeon_kind=f"v020_mega_{key}"
            if self.server.db.boss_floor_cleared(self.account_id,dungeon_kind,index): return False
            return self.v0200_live_blocking_boss(room_id,mega=True) is not None

    def v0200_gauntlet_blocked(self, room_id, direction):
            room=ROOMS.get(room_id,{})
            if not room.get("v020_gauntlet") or direction != "north": return False
            return self.v0200_live_blocking_boss(room_id,gauntlet=True) is not None

    async def show_megadungeons_v020(self):
            await self.send("MEGALOCHY ENDGAME")
            discovered=self.server.db.discovered_room_ids(self.account_id)
            for key,spec in V020_MEGADUNGEONS.items():
                gate=v0200_mega_gate_id(key); state="odkryty" if gate in discovered else "nieodkryty"
                clears=self.server.db.highest_boss_floor_cleared(self.account_id,f"v020_mega_{key}")
                await self.send(f"{key}: {spec['name']}. {spec['size']} pokoi; start Biegłość około {spec['stage']}; {state}; najwyższy zaliczony próg {clears}.")
            await self.send("Boss co 25 pokoi blokuje tylko dalszą sekcję przy pierwszym zaliczeniu. Brak pułapek.")

    async def show_gauntlets_v020(self):
            await self.send("BOSS GAUNTLETY")
            clears=self.server.db.collection_entry_ids(self.account_id,"gauntlet_clears_v020")
            for key,data in V020_GAUNTLETS.items():
                await self.send(f"{key}: {data['name']}. 5 rund, etapy {data['stages'][0]}-{data['stages'][-1]}. Finał zaliczony: {'tak' if key in clears else 'nie'}.")
            await self.send("Wejdź do Sali Boss Gauntletów przy Straży Rubieży i użyj: gauntlet <nazwa>.")

    async def start_gauntlet_v020(self,args=""):
            if self.character.room_id != V020_GAUNTLET_LOBBY:
                await self.send("Boss gauntlet rozpoczyna się wyłącznie w Sali Boss Gauntletów przy Straży Rubieży."); return
            q=normalize_lookup_text(args); chosen=None
            for key,data in V020_GAUNTLETS.items():
                if q in (normalize_lookup_text(key),normalize_lookup_text(data['name'])) or (q and q in normalize_lookup_text(data['name'])): chosen=key; break
            if not chosen: await self.show_gauntlets_v020(); return
            target=f"v020_gauntlet_{chosen}_1"; self.previous_room_id=self.character.room_id; self.character.room_id=target; self.server.db.save_character(self.character)
            await self.send(f"Rozpoczynasz: {V020_GAUNTLETS[chosen]['name']}. Boss nie zaatakuje pierwszy."); await self.look()

    async def show_mythic_bosses_v020(self):
            now=time.time(); entries=v0200_active_mythic_world_bosses(now); remaining=max(0,int(entries[0]['expires_at']-now)) if entries else 0
            await self.send(f"MITYCZNE BOSSOWIE ŚWIATA — rotacja za około {remaining//60} minut.")
            for i,e in enumerate(entries,1):
                await self.send(f"{i}. {MOB_TEMPLATES[e['template_id']]['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie są pasywne. Dają mityczne materiały endgame.")

    async def artifact_upgrade_v020(self,args=""):
            query=normalize_lookup_text(args)
            candidates=[]
            for fid,data in V017_ARTIFACTS.items():
                tier,item_id=v0200_artifact_owned_tier(self.server.db,self.account_id,fid)
                if tier:
                    candidates.append((fid,data,tier,item_id))
            if not query:
                await self.send("ROZWÓJ ARTEFAKTÓW")
                if not candidates: await self.send("Nie posiadasz jeszcze artefaktu frakcyjnego."); return
                for fid,data,tier,item_id in candidates:
                    await self.send(f"{data['name']}: poziom {tier}/{V020_ARTIFACT_MAX_TIER}. " + ("Maksymalny." if tier>=V020_ARTIFACT_MAX_TIER else "Użyj ulepszartefakt <nazwa>."))
                return
            chosen=None
            for row in candidates:
                fid,data,tier,item_id=row
                if query in normalize_lookup_text(data['name']) or query in normalize_lookup_text(fid): chosen=row; break
            if not chosen:
                await self.send("Nie znajduję posiadanego artefaktu o tej nazwie."); return
            fid,data,tier,item_id=chosen
            if tier>=V020_ARTIFACT_MAX_TIER: await self.send(f"Ten artefakt ma już maksymalny poziom {V020_ARTIFACT_MAX_TIER}."); return
            if any(row["item_id"] == item_id for row in self.equipped_item_rows()):
                await self.send("Najpierw zdejmij artefakt. Ulepszanie nie zmienia założonego przedmiotu w locie."); return
            next_tier=tier+1; req=V020_ARTIFACT_UPGRADE_COSTS[next_tier]; missing=[]
            for iid,qty in req.items():
                if iid=="coins": continue
                have=self.server.db.item_qty(self.account_id,iid)
                if have<qty: missing.append(f"{ITEMS[iid]['name']} {have}/{qty}")
            coins=int(req.get("coins",0)); wallet=self.character_wallet_silver_value()
            if wallet<coins: missing.append(f"waluta {currency_reading_text(wallet,0,0)} / {currency_reading_text(coins,0,0)}")
            if missing:
                await self.send("Brakuje: "+"; ".join(missing)+"."); return
            # Nie ma RNG/faila: dopiero po pełnej walidacji pobieramy koszt i zamieniamy przedmiot.
            for iid,qty in req.items():
                if iid!="coins": self.server.db.remove_item(self.account_id,iid,qty)
            self.character.silver=wallet-coins; self.character.gold=0; self.character.mithril=0
            self.server.db.remove_item(self.account_id,item_id,1)
            new_item=V020_ARTIFACT_VARIANTS[fid][next_tier-1]; self.server.db.add_item(self.account_id,new_item,1); self.server.db.save_character(self.character)
            await self.record_item_collection(new_item,source="Rozwój artefaktu",announce=True)
            await self.send(f"Artefakt rozwinięty bez ryzyka: {ITEMS[new_item]['name']}. Koszt waluty: {currency_reading_text(coins,0,0)}.")

    async def show_endgame_goals_v020(self):
            mega=len(self.server.db.collection_entry_ids(self.account_id,"mega_boss_kills_v020"))
            gaunt=int(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020") and len(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020")) or 0)
            mythic=len(self.server.db.collection_entry_ids(self.account_id,"mythic_world_kills_v020"))
            t5=sum(1 for fid in V017_ARTIFACTS if v0200_artifact_owned_tier(self.server.db,self.account_id,fid)[0]>=5)
            vals={"mega_bosses":mega,"gauntlet_finals":gaunt,"mythic_world":mythic,"artifact_t5":t5}
            await self.send("DŁUGOTERMINOWE CELE ENDGAME")
            for key,need,label in V020_ENDGAME_GOALS: await self.send(f"{label}: {min(vals[key],need)} z {need}.")

    async def show_artifacts_v017(self):
            await self.send("ARTEFAKTY FRAKCYJNE")
            discovered = self.server.db.collection_entry_ids(self.account_id, "unique")
            for faction_id, data in V017_ARTIFACTS.items():
                item_id = data["item_id"]
                owned = self.server.db.item_qty(self.account_id, item_id) > 0 or item_id in discovered
                equipped = any(row["item_id"] == item_id for row in self.equipped_item_rows())
                state = "założony" if equipped else ("odkryty" if owned else "nieodkryty")
                await self.send(f"{data['name']} — {V016_FACTIONS[faction_id]['name']}. {state}. {data['effect']}")

    async def show_biome_sets_v017(self, args=""):
            query = normalize_lookup_text(args)
            counts = self.regional_set_counts()
            await self.send("ZESTAWY BIOMOWE")
            shown = 0
            for kind, name in V017_BIOME_SET_NAMES.items():
                if query and query not in normalize_lookup_text(kind) and query not in normalize_lookup_text(name) and query not in normalize_lookup_text(V013_FRONTIER_SPECS[kind]["zone"]):
                    continue
                sid = f"v017_{kind}"
                count = int(counts.get(sid, 0))
                cfg = REGIONAL_SET_BONUSES[sid]
                await self.send(
                    f"{name}: {count}/6 założonych. Biom: {V013_FRONTIER_SPECS[kind]['zone']}. "
                    f"2/6 HP/Mana +{int(round((cfg['hp']-1)*100))}%, "
                    f"4/6 obrażenia +{int(round((cfg['damage']-1)*100))}%, "
                    f"6/6 obrona +{int(round((cfg['defense']-1)*100))}%."
                )
                shown += 1
            if not shown:
                await self.send("Nie rozpoznaję takiego zestawu biomowego.")

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
            for number, event in enumerate(events, 1):
                zone = V013_FRONTIER_SPECS[event["kind"]]["zone"]
                await self.send(
                    f"{number}. {event['title']}. {zone}, sektor {event['x']+1}-{event['y']+1}. {event['desc']}"
                )
            await self.send("Wszystkie eventy są opcjonalne. Żaden mob nie zaczyna walki sam.")
            await self.show_dynamic_events_v029()
