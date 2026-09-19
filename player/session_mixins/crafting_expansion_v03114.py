# -*- coding: utf-8 -*-
"""Soulbound v0.31.14 — player-facing Forge & Materials 3.0."""
class SessionCraftingExpansionV03114Mixin:
    def equipment_total_socket_capacity_v03114(self, item_id, item, kind="gem"):
        if kind=="rune": base=v0925_equipment_socket_count(item)
        else: base=equipment_gem_socket_capacity_v03111(item) if "equipment_gem_socket_capacity_v03111" in globals() else jewelry_socket_capacity(item)
        return max(0,int(base))+max(0,int(self.server.db.equipment_socket_bonus_v03114(self.account_id,item_id)))

    async def salvage_equipment_v0925(self, args=""):
        raw=str(args or "").strip()
        # Preserve the old EQ list/default behavior.
        if not raw or normalize_lookup_text(raw) in ("list","lista","info"):
            await SessionForgeGuildsMixin.salvage_equipment_v0925(self,args)
            await self.send("SALVAGE 3.0: można też rozkładać boardy, Tech EQ, stare Upgrade Kity i ciężkie części bossowe. Użyj rozloz <nazwa>.")
            return
        # Armor first, exactly as before.
        found=self.resolve_owned_equipment_v0925(raw,free_only=True)
        if found:
            return await SessionForgeGuildsMixin.salvage_equipment_v0925(self,args)
        pool={iid:ITEMS[iid] for iid in SALVAGE3_V03114 if self.available_recipe_item(iid)>0}
        found=find_by_name(pool,raw)
        if not found:
            return await SessionForgeGuildsMixin.salvage_equipment_v0925(self,args)
        iid,item=found
        if not self.consume_recipe_item(iid,1):
            await self.send("Nie udało się pobrać przedmiotu do Salvage 3.0."); return
        outputs=SALVAGE3_V03114[iid]
        for oid,qty in outputs.items(): self.server.db.add_storage_item(self.account_id,"craftbox",oid,qty)
        await self.send("SALVAGE 3.0: "+item['name']+" -> "+", ".join(f"{ITEMS[o]['name']} x{q}" for o,q in outputs.items())+".")
        salvage_level=max(1,min(400,int(item.get("required_character_level",item.get("required_mastery",item.get("min_profession_level",1))) or 1)))
        salvage_prof_xp=max(10,10+salvage_level//12+sum(int(q) for q in outputs.values())*2)
        messages,_prof_after,_tool_after=self.grant_profession_progress(
            "Kowalstwo",salvage_prof_xp,"crafting",0,tool_progress=False
        )
        for message in messages: await self.send(message)

    def max_recipe_crafts_v03114(self, recipe):
        limits=[]
        for iid,q in recipe.get("ingredients",{}).items():
            q=max(1,int(q)); limits.append(self.available_recipe_item(iid)//q)
        if not limits: return 0
        return max(0,min(limits))

    async def craft_item_v03114(self, query):
        raw=str(query or '').strip(); norm=normalize_lookup_text(raw)
        if norm.startswith("max "):
            wanted=raw.split(maxsplit=1)[1]
            found=find_by_name(CRAFT_RECIPES,wanted)
            if not found: await self.send("Nie rozpoznaję receptury do craft max."); return False
            rid,recipe=found; count=self.max_recipe_crafts_v03114(recipe)
            if count<=0: await self.send("Nie masz składników na ani jedną sztukę tej receptury."); return False
            await self.send(f"CRAFT MAX: {recipe['name']}. Możliwe teraz: {count}. Wykonuję kolejno do wyczerpania składników.")
            done=0
            while done<count:
                if not await self.perform_recipe(rid,CRAFT_RECIPES,"rzemiosło"): break
                done+=1
            await self.send(f"CRAFT MAX zakończony: {done}/{count}."); return done>0
        return await self.perform_recipe(raw,CRAFT_RECIPES,"rzemiosło")

    async def material_conversion_v03114(self):
        await self.send("MATERIAL CONVERSION UI — materiały, które możesz teraz przerobić/przetopić:")
        anyrow=False
        for tier in BLACKSMITH_TIERS:
            rec=CRAFT_RECIPES.get(tier['ingot']);
            if not rec: continue
            qty=self.max_recipe_crafts_v03114(rec)
            fallback_id=SALVAGE_SMELT_FALLBACK_V03113.get(rec.get('output')); fb=CRAFT_RECIPES.get(fallback_id) if fallback_id else None
            salvage_qty=self.max_recipe_crafts_v03114(fb) if fb else 0
            if qty or salvage_qty:
                anyrow=True; await self.send(f"{rec['name']}: z rudy {qty}, z Salvage {salvage_qty}.")
        for rid,rec in CRAFT_RECIPES.items():
            if not rid.startswith('refine_'): continue
            qty=self.max_recipe_crafts_v03114(rec)
            if qty: anyrow=True; await self.send(f"Refining: {rec['name']} x{qty} możliwe.")
        if not anyrow: await self.send("Brak materiałów wystarczających do konwersji.")

    async def smelt_item_v03114(self, query):
        raw=str(query or '').strip(); norm=normalize_lookup_text(raw)
        if not raw:
            await self.send(
                "Użycie: przetop <metal albo ruda>. "
                "Dostępne: żelazo, odłamki żelaza, srebro, złoto, stal, stalowe płyty, "
                "kobalt, runa, smocza stal, astral, pustka, Eternium. "
                "Dodatkowo: przetop max <metal> oraz przetop wszystko."
            )
            return False
        if norm in ("wszystko","all"):
            total=0
            # Safety: only salvage fallback recipes; normal ores are not consumed by 'all'.
            for fallback_id in dict.fromkeys(SALVAGE_SMELT_FALLBACK_V03113.values()):
                rec=CRAFT_RECIPES.get(fallback_id)
                if not rec: continue
                n=self.max_recipe_crafts_v03114(rec)
                for _ in range(n):
                    ok=await self.perform_recipe(fallback_id,CRAFT_RECIPES,"przetapianie")
                    if not ok: break
                    total+=1
            await self.send(f"PRZETOP WSZYSTKO: wykonano {total} przetopów materiałów Salvage."); return total>0
        if norm.startswith("max "):
            wanted=raw.split(maxsplit=1)[1]
            found=self.resolve_smelt_recipe(wanted)
            if not found: await self.send("Nie rozpoznaję metalu dla przetop max."); return False
            rid,rec=found
            # same primary -> salvage fallback preference as normal smelt
            if self.max_recipe_crafts_v03114(rec)<=0:
                fb=SALVAGE_SMELT_FALLBACK_V03113.get(rec.get('output'))
                if fb and CRAFT_RECIPES.get(fb): rid,rec=fb,CRAFT_RECIPES[fb]
            n=self.max_recipe_crafts_v03114(rec)
            if n<=0: await self.send("Brak materiału do przetopienia."); return False
            await self.send(f"PRZETOP MAX: {rec['name']} x{n}.")
            done=0
            for _ in range(n):
                if not await self.perform_recipe(rid,CRAFT_RECIPES,"przetapianie"): break
                done+=1
            await self.send(f"PRZETOP MAX zakończony: {done}/{n}."); return done>0
        found=self.resolve_smelt_recipe(raw)
        if not found:
            await self.send("Nie rozpoznaję metalu do przetopienia."); return False
        rid,rec=found
        if self.max_recipe_crafts_v03114(rec)<=0:
            fb=SALVAGE_SMELT_FALLBACK_V03113.get(rec.get('output'))
            if fb and CRAFT_RECIPES.get(fb) and self.max_recipe_crafts_v03114(CRAFT_RECIPES[fb])>0:
                rid,rec=fb,CRAFT_RECIPES[fb]
                await self.send("Brakuje zwykłej rudy. Pobieram materiał ze Szkatułki -> Salvage.")
        return await self.perform_recipe(rid,CRAFT_RECIPES,"przetapianie")

    async def refine_v03114(self, query=""):
        raw=str(query or '').strip()
        recipes={rid:r for rid,r in CRAFT_RECIPES.items() if rid.startswith('refine_')}
        if not raw:
            await self.send("REFINING 2.0. Użycie: refine <stop>. Dostępne:")
            for r in recipes.values(): await self.send(f"{r['name']}: {self.recipe_ingredients_text(r)}.")
            return
        if normalize_lookup_text(raw).startswith("max "):
            wanted=raw.split(maxsplit=1)[1]; found=find_by_name(recipes,wanted)
            if not found: await self.send("Nieznany stop."); return
            rid,rec=found; n=self.max_recipe_crafts_v03114(rec); done=0
            for _idx in range(n):
                if not await self.perform_recipe(rid,recipes,"rafinowanie"): break
                done+=1
            await self.send(f"REFINE MAX: wykonano {done}/{n}."); return
        await self.perform_recipe(raw,recipes,"rafinowanie")

    async def socket_craft_v03114(self, query=""):
        if not self.at_haldor_forge_v0925(): await self.send("Socket Crafting wykonuje Haldor w Kuźni/Warsztacie Rzemieślniczym."); return
        found=self.resolve_owned_equipment_v0925(query,False)
        if not found: await self.send("Użycie: socketcraft <pełna nazwa posiadanego EQ>."); return
        iid,item=found; bonus=self.server.db.equipment_socket_bonus_v03114(self.account_id,iid)
        if bonus>=2: await self.send(f"{item['name']} ma już maksymalny bonus Socket Crafting: +2 gniazda."); return
        lvl=v03042_equipment_level(item); cost=1 if bonus==0 else 2
        if self.available_recipe_item('socket_core_v03114')<cost: await self.send(f"Potrzeba Rdzeń Gniazda x{cost}."); return
        refined='hardened_steel_ingot' if lvl<200 else ('astral_alloy' if lvl<320 else 'eternium_alloy')
        if self.available_recipe_item(refined)<1: await self.send(f"Potrzeba także: {ITEMS[refined]['name']} x1."); return
        self.consume_recipe_item('socket_core_v03114',cost); self.consume_recipe_item(refined,1)
        new=self.server.db.add_equipment_socket_v03114(self.account_id,iid,2)
        await self.send(f"Socket Crafting: {item['name']} otrzymuje trwałe dodatkowe gniazdo. Bonus gniazd +{new}/2.")

    async def handle_runes_v03114(self,args=""):
        raw=str(args or '').strip(); parts=raw.split(maxsplit=2); action=normalize_lookup_text(parts[0]) if parts else ''
        if action in ('stworz','stwórz','craft','wykuj'):
            if len(parts)<2: await self.send("Użycie: runy stworz <typ>."); return
            if not self.at_haldor_forge_v0925(): await self.send("Runy wykuwa Haldor w Kuźni."); return
            key=normalize_lookup_text(parts[1]).replace('życie','zycie'); key={"power":"moc","guard":"ochrona","life":"zycie","focus":"mana","agility":"unik","fortitude":"hart"}.get(key,key)
            if key not in V0925_RUNES: await self.send("Nieznany typ runy."); return
            costs=RUNE_CRAFT_COSTS_V03114.get(key,{"rune_dust":5}); missing=[f"{ITEMS[i]['name']} {self.available_recipe_item(i)}/{q}" for i,q in costs.items() if self.available_recipe_item(i)<q]
            if missing: await self.send("Rune Crafting: brakuje "+", ".join(missing)+"."); return
            for i,q in costs.items(): self.consume_recipe_item(i,q)
            rid=V0925_RUNES[key][0]; self.server.db.add_storage_item(self.account_id,'craftbox',rid,1)
            await self.send(f"Rune Crafting: wykuwasz {ITEMS[rid]['name']}. Koszt: "+", ".join(f"{ITEMS[i]['name']} x{q}" for i,q in costs.items())+"."); return
        return await SessionForgeGuildsMixin.handle_runes_v0925(self,args)

    async def vmax_upgrade_v03114(self,args=""):
        d,c=self.server.db.vmax_upgrades_v03114(self.account_id); norm=normalize_lookup_text(args or '')
        if not norm:
            await self.send(f"V-MAX UPGRADE PATH: Przedłużenie {d}/3 (+{d*10} s), Chłodzenie {c}/2 (-{c*8} s Overheat). Użycie: vmaxupgrade duration albo vmaxupgrade cooling."); return
        if norm in ('duration','czas','przedluzenie','przedłużenie'):
            if d>=3: await self.send("Przedłużenie V-MAX jest już maksymalne 3/3."); return
            iid='vmax_duration_module'; kind='duration'
        elif norm in ('cooling','chlodzenie','chłodzenie'):
            if c>=2: await self.send("Chłodzenie V-MAX jest już maksymalne 2/2."); return
            iid='vmax_cooling_module'; kind='cooling'
        else: await self.send("Użycie: vmaxupgrade duration albo vmaxupgrade cooling."); return
        if self.available_recipe_item(iid)<1: await self.send(f"Nie masz: {ITEMS[iid]['name']}. Wykonaj go przez techcraft."); return
        self.consume_recipe_item(iid,1); d,c=self.server.db.add_vmax_upgrade_v03114(self.account_id,kind)
        await self.send(f"V-MAX ulepszony. Przedłużenie {d}/3, Chłodzenie {c}/2.")

    async def show_tech_sets_v03114(self):
        counts=self.regional_set_counts(); await self.send("TECH EQ SETY 2/4/6/8")
        for sid,(name,cls,race,bonus) in TECH_SET_SPECS_V03114.items():
            n=counts.get(sid,0); req=(f"klasa {cls}" if cls else f"rasa {race}")
            await self.send(f"{name}: {n}/8, {req}. 2/8 HP/Mana +{int((bonus['hp']-1)*100)}%; 4/8 obrażenia +{int((bonus['damage']-1)*100)}%; 6/8 obrona +{int((bonus['defense']-1)*100)}%; 8/8 pełna synchronizacja +{int((bonus['complete']-1)*100)}% do HP/obrażeń/obrony.")
