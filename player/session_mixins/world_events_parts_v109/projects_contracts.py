# -*- coding: utf-8 -*-
"""Modul v109: projects_contracts; oryginalne metody bez zmian AST."""
from .dependencies import *

class ProjectsContractsV109Mixin:

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
                reward=v022_project_reward(key)
                project_stage=max(1,min(800,int(spec.get("stage",1) or 1)))
                [
                    await self.send(_m)
                    for _m in self.add_character_xp_with_event(
                        reward["character_xp"],
                        content_level=project_stage,
                        content_scaled=True,
                    )
                ]
                await self.grant_class_xp(
                    reward["class_xp"],
                    content_level=project_stage,
                    content_scaled=True,
                )
                await self.grant_soul_xp(
                    reward["soul_xp"],
                    content_level=project_stage,
                    content_scaled=True,
                )
                self.character.silver=min(
                    CURRENCY_SQLITE_SAFE_TOTAL,
                    self.character.silver+reward["coins"],
                )
                self.server.db.save_character(self.character)
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
                except Exception as exc:
                    print(f"WORLD_PROJECT_RECORD_ERROR: {type(exc).__name__}: {exc}", flush=True)
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
                legendary_stage=max(
                    1,min(800,int(active.get("stage",1) or 1))
                )
                [
                    await self.send(_m)
                    for _m in self.add_character_xp_with_event(
                        int(active.get("reward_character_xp",0)),
                        content_level=legendary_stage,
                        content_scaled=True,
                    )
                ]
                await self.grant_class_xp(
                    int(active["reward_class_xp"]),
                    content_level=legendary_stage,
                    content_scaled=True,
                )
                await self.grant_soul_xp(
                    int(active["reward_soul_xp"]),
                    content_level=legendary_stage,
                    content_scaled=True,
                )
                self.character.silver=min(
                    CURRENCY_SQLITE_SAFE_TOTAL,
                    self.character.silver+int(active["reward_coins"]),
                )
                self.server.db.save_character(self.character)
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
