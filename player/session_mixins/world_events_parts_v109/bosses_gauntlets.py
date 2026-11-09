# -*- coding: utf-8 -*-
"""Modul v109: bosses_gauntlets; oryginalne metody bez zmian AST."""
from .dependencies import *

class BossesGauntletsV109Mixin:

    async def show_world_bosses_v016(self):
            now = time.time()
            bosses = v0160_active_world_bosses(now)
            remaining = max(0, int(bosses[0]["expires_at"]-now)) if bosses else 0
            await self.send(f"BOSSOWIE ŚWIATA — rotacja za około {remaining} sekund.")
            for i, e in enumerate(bosses,1):
                template = MOB_TEMPLATES[e["template_id"]]
                await self.send(f"{i}. {template['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie world bossy są pasywne. Walkę rozpoczyna wyłącznie gracz.")

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

    async def show_superbosses_v11135(self, args=""):
            query = normalize_lookup_text(args)
            rows = []
            for key, data in UOSS_SUPERBOSS_ENCOUNTERS_V11134.items():
                name = str(data.get("name", key))
                if query and query not in normalize_lookup_text(key) and query not in normalize_lookup_text(name):
                    continue
                cleared = superboss_cleared_v11135(self.server.db, self.account_id, key)
                level_req = int(data.get("unlock_level", 0) or 0)
                unlocked = not level_req or int(self.character.character_level) >= level_req
                if data.get("unlock") == "explore_deep_dungeon":
                    unlock_entries = self.server.db.collection_entry_ids(
                        self.account_id, "deep_dungeon_discovery"
                    )
                    unlocked = "floor_100" in unlock_entries
                mode = str(data.get("mode", "solo"))
                state = "blokada po pokonaniu" if cleared else ("odblokowany" if unlocked else "zablokowany")
                rows.append((name, mode, state, data))
            if not rows:
                await self.send("Nie znajduję takiego Super Bossa.")
                return
            await self.send("SUPER BOSSOWIE UOSSMUD")
            for name, mode, state, data in rows:
                extra = []
                if data.get("recommended_level"): extra.append(f"zalecany Level {data['recommended_level']}")
                if data.get("deep_dungeon_unlock_floor"):
                    extra.append(
                        f"wymaga osobistego dotarcia do Deep Dungeon "
                        f"piętro {data['deep_dungeon_unlock_floor']}"
                    )
                if data.get("lockout_hours"):
                    extra.append(f"lockout {data['lockout_hours']} h po zabiciu")
                if data.get("personal_token"): extra.append(f"osobista nagroda: {data['personal_token']}")
                if data.get("helpers"): extra.append("pomocnik: " + " albo ".join(data["helpers"]) + "; wybór: pomocnik primm/popoi")
                elif data.get("helper"): extra.append("pomocnik: " + str(data["helper"]))
                _series=superboss_series_progress_v11138(self.server.db,self.account_id,next((k for k,v in UOSS_SUPERBOSS_ENCOUNTERS_V11134.items() if v is data),""))
                if _series: extra.append(f"seria {_series[0]}/{_series[1]}")
                await self.send(f"{name}: {mode}, {state}" + (". " + "; ".join(extra) if extra else "") + ".")
            await self.send("Po pokonaniu konkretnego Super Bossa obowiązuje 24-godzinna blokada ponownego wejścia; restart/deploy jej nie resetuje.")
            await self.send(
                "Super Bossowie oznaczeni jako drużynowi dopuszczają także wejście solo. "
                "W party lider używa superboss <nazwa>, a kwalifikujący się członkowie "
                "stojący razem z liderem są przenoszeni na arenę wspólnie."
            )

    async def enter_superboss_v11138(self, args=""):
            query=normalize_lookup_text(args)
            chosen=None
            for key,data in UOSS_SUPERBOSS_ENCOUNTERS_V11134.items():
                if query and (
                    query in normalize_lookup_text(key)
                    or query in normalize_lookup_text(data["name"])
                ):
                    chosen=(key,data)
                    break
            if not chosen:
                await self.send(
                    "Użycie: superboss <nazwa>. Listę pokazuje: superbosses."
                )
                return

            key,data=chosen
            mode=str(data.get("mode","solo"))
            party_key=self.party_key()

            if mode=="solo":
                entrants=[self]
            else:
                if party_key is not None and party_key != self.account_id:
                    leader=self.server.session_by_account(party_key)
                    leader_name=(
                        leader.character.name
                        if leader and getattr(leader,"character",None)
                        else "lider drużyny"
                    )
                    await self.send(
                        "Tylko lider może przenieść drużynę na arenę Super Bossa. "
                        f"Lider: {leader_name}."
                    )
                    return

                if party_key is None:
                    entrants=[self]
                else:
                    entrants=[
                        member
                        for member in self.server.party_sessions(
                            self.account_id,
                            same_room=self.character.room_id,
                        )
                        if (
                            member
                            and not member.closed
                            and getattr(member,"character",None)
                            and member.current_hp>0
                        )
                    ]
                    if self not in entrants and self.current_hp>0:
                        entrants.append(self)

                # UOSSMUD-compatible rule: party-oriented Super Bosses also allow solo entry.
                # If a real party enters, its existing party-size rules still apply.

                min_players=int(data.get("min_players",0) or 0)
                max_players=int(data.get("max_players",0) or 0)
                if min_players and len(entrants)>1 and len(entrants)<min_players:
                    await self.send(
                        f"{data['name']} wymaga co najmniej {min_players} "
                        "graczy przy wejściu drużynowym; wejście solo jest dozwolone."
                    )
                    return
                if max_players and len(entrants)>max_players:
                    await self.send(
                        f"{data['name']} dopuszcza maksymalnie "
                        f"{max_players} graczy."
                    )
                    return

            for member in entrants:
                entry_error=superboss_member_entry_error_v11331(member,key)
                if entry_error:
                    await self.send(
                        "Nie przenoszę na arenę, ponieważ wymagania nie są "
                        f"spełnione: {entry_error}"
                    )
                    return

            target=f"uoss_superboss_arena_{key}_v11136"
            self.server.world.ensure_runtime_room(target)
            origin=self.character.room_id
            moved=[]
            for member in entrants:
                member.previous_room_id=member.character.room_id
                member.character.room_id=target
                member.server.db.save_character(member.character)
                moved.append(member.character.name)

            if len(entrants)>1:
                for member in entrants:
                    await member.send(
                        f"{self.character.name} jako lider przenosi drużynę "
                        f"na arenę Super Bossa: {data['name']}. "
                        "Boss nie atakuje pierwszy."
                    )
                await self.send(
                    f"Przeniesiono razem {len(entrants)} graczy: "
                    + ", ".join(moved) + "."
                )
            else:
                await self.send(
                    f"Wchodzisz na arenę Super Bossa: {data['name']}. "
                    "Boss nie atakuje pierwszy."
                )

            if party_key is not None and mode!="solo":
                all_party=list(self.server.party_sessions(self.account_id))
                elsewhere=[
                    member.character.name
                    for member in all_party
                    if (
                        member
                        and getattr(member,"character",None)
                        and member.character.room_id not in (origin,target)
                    )
                ]
                if elsewhere:
                    await self.send(
                        "Nie przeniesiono członków poza lokacją lidera: "
                        + ", ".join(elsewhere) + "."
                    )

            for member in entrants:
                await member.look()

    async def choose_superboss_helper_v11138(self,args=""):
            q=normalize_lookup_text(args)
            if not q:
                await self.send(
                    "Użycie: pomocnik <nazwa>, np. pomocnik popoi. "
                    "Możesz też powiedzieć źródłową frazę, np. say Join me, Popoi."
                )
                return
            hired=await self.try_hire_uoss_helper_v11160(f"join me {q}")
            if not hired:
                await self.send(
                    "Nie ma tutaj takiego pomocnika Super Bossa albo ten pomocnik "
                    "nie odpowiada na tę frazę. Sprawdź NPC w lokacji."
                )

    async def exchange_weapon_spoils_v11141(self, args=""):
            if not weapon_pair_exchange_ready_v11141(self.server.db,self.account_id):
                await self.send("Traveler w Kalm wymaga obu trofeów: Desert Rose z Ruby WEAPON oraz Earth Harp z Emerald WEAPON.")
                return
            marker="ruby_emerald_pair_reward"
            if marker in self.server.db.collection_entry_ids(self.account_id,"uoss_kalm_exchanges_v11141"):
                await self.send("Traveler w Kalm już wydał ci nagrodę za tę parę trofeów.")
                return
            self.server.db.remove_item(self.account_id,"uoss_desert_rose",1)
            self.server.db.remove_item(self.account_id,"uoss_earth_harp",1)
            self.server.db.add_item(self.account_id,"uoss_weapon_pair_reward",1)
            self.server.db.add_collection_entry(self.account_id,"uoss_kalm_exchanges_v11141",marker)
            await self.send("Traveler w Kalm odbiera Desert Rose i Earth Harp. Otrzymujesz: Planet's Guardian Relic.")

    async def show_mythic_bosses_v020(self):
            now=time.time(); entries=v0200_active_mythic_world_bosses(now); remaining=max(0,int(entries[0]['expires_at']-now)) if entries else 0
            await self.send(f"MITYCZNE BOSSOWIE ŚWIATA — rotacja za około {remaining//60} minut.")
            for i,e in enumerate(entries,1):
                await self.send(f"{i}. {MOB_TEMPLATES[e['template_id']]['name']}. {V013_FRONTIER_SPECS[e['kind']]['zone']}, sektor {e['x']+1}-{e['y']+1}.")
            await self.send("Wszystkie są pasywne. Dają mityczne materiały endgame.")
