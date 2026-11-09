# -*- coding: utf-8 -*-
"""Modul v109: ascension; oryginalne metody bez zmian AST."""
from .dependencies import *

class AscensionV109Mixin:

    def v0210_total_ascension_rank(self):
            return sum(int(r["rank"] or 0) for r in self.server.db.ascension_rows_v021(self.account_id) if str(r["track"]).startswith("class:"))

    def v0210_any_class_at_400(self):
            row=self.server.db.conn.execute("SELECT MAX(level) AS mx FROM class_progress WHERE account_id=?",(self.account_id,)).fetchone()
            return int(row["mx"] or 0)>=CLASS_MASTERY_MAX_LEVEL if row else False

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
                await self.send(f"World Tier 2+ wymaga co najmniej jednej klasy z Biegłością {CLASS_MASTERY_MAX_LEVEL}."); return
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

    async def show_endgame_goals_v020(self):
            mega=len(self.server.db.collection_entry_ids(self.account_id,"mega_boss_kills_v020"))
            gaunt=int(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020") and len(self.server.db.collection_entry_ids(self.account_id,"gauntlet_final_kills_v020")) or 0)
            mythic=len(self.server.db.collection_entry_ids(self.account_id,"mythic_world_kills_v020"))
            t5=sum(1 for fid in V017_ARTIFACTS if v0200_artifact_owned_tier(self.server.db,self.account_id,fid)[0]>=5)
            vals={"mega_bosses":mega,"gauntlet_finals":gaunt,"mythic_world":mythic,"artifact_t5":t5}
            await self.send("DŁUGOTERMINOWE CELE ENDGAME")
            for key,need,label in V020_ENDGAME_GOALS: await self.send(f"{label}: {min(vals[key],need)} z {need}.")
