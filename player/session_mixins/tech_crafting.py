# -*- coding: utf-8 -*-
"""Soulbound v0.31.13 tech/crafting UI mixin."""
class SessionTechCraftingV03111Mixin:
    async def tech_salvage_v03111(self, query=""):
        raw=str(query or "").strip()
        if not raw or normalize_lookup_text(raw) in ("list","lista","info"):
            await self.send("ROZKŁADANIE TECHNOLOGICZNE. Rozkładanie: techsalvage <komponent>. Cięższe części wracają do podstawowych Servo/Circuit/Power Cell/Plating w Szkatułce -> Technologia.")
            for iid,outputs in TECH_SALVAGE_RECIPES.items():
                out=", ".join(f"{ITEMS[k]['name']} x{v}" for k,v in outputs.items())
                await self.send(f"{ITEMS[iid]['name']} -> {out}.")
            return
        possible={iid:ITEMS[iid] for iid in TECH_SALVAGE_RECIPES}
        found=find_by_name(possible,raw)
        if not found:
            await self.send("Nie rozpoznaję komponentu do Tech Salvage. Wpisz techsalvage."); return
        iid,item=found
        if self.available_recipe_item(iid)<=0:
            await self.send(f"Nie masz: {item['name']}."); return
        if not self.consume_recipe_item(iid,1):
            await self.send("Nie udało się pobrać komponentu."); return
        outputs=TECH_SALVAGE_RECIPES[iid]
        for out_id,qty in outputs.items():
            self.server.db.add_storage_item(self.account_id,"craftbox",out_id,qty)
        await self.send("Tech Salvage: " + item["name"] + " -> " + ", ".join(f"{ITEMS[k]['name']} x{v}" for k,v in outputs.items()) + ".")
        salvage_level=max(1,min(CHARACTER_MAX_LEVEL,int(item.get("required_character_level",item.get("required_mastery",150)) or 150)))
        salvage_prof_xp=max(14,14+salvage_level//14+sum(int(v) for v in outputs.values())*2)
        messages,_prof_after,_tool_after=self.grant_profession_progress(
            "Kowalstwo",salvage_prof_xp,"crafting",0,tool_progress=False
        )
        for message in messages: await self.send(message)

    async def tech_craft_v03111(self, query=""):
        raw=str(query or "").strip()
        if not raw:
            await self.send("TECH CRAFTING. Użycie: techcraft <nazwa>. Dostępne receptury:")
            for recipe in TECH_CRAFT_RECIPES.values():
                await self.send(f"{recipe['name']}. {self.recipe_ingredients_text(recipe)}. Wymaga Kowalstwa {recipe.get('min_profession_level',1)}.")
            return
        await self.perform_recipe(raw, TECH_CRAFT_RECIPES, "Tech Crafting")

    async def vmax_status_v03111(self):
        await self.mec_refresh_vmax_v0319()
        now=time.time(); vmax=max(0,int(float(getattr(self,'v0319_vmax_until',0.0) or 0.0)-now+0.999)); party_vmax=max(0,int(float(getattr(self,'v03511_party_vmax_until',0.0) or 0.0)-now+0.999)); over=max(0,int(float(getattr(self,'v0319_overheat_until',0.0) or 0.0)-now+0.999))
        will=int(getattr(self.character,'willpower',0) or 0)
        vd,vc=self.server.db.vmax_upgrades_v03114(self.account_id)
        if vmax>0:
            await self.send(f"V-MAX: AKTYWNY. Pozostało {vmax} s. Will {will}. Upgrade: czas {vd}/3, chłodzenie {vc}/2. Efekty: Protect, Shell, Haste, Regen, Preach, Praise, Permanence.")
            await self.send("Zmiany V-MAX: Cosmic Rave = 5 losowych trafień; Shoot-All = większy damage/crit; Starlight Shower = niedyminishing AoE; Kamikaze Crush = wyższy limit HP; Heal Beam = party heal.")
        elif party_vmax>0:
            await self.send(f"V-MAX DRUŻYNY: aktywne wsparcie jeszcze {party_vmax} s. Otrzymujesz +30 procent do skilli/spelli oraz Protect, Shell i Regen. Specjalne zmiany skilli Meca wymagają własnej aktywacji V-MAX.")
        elif over>0:
            await self.send(f"V-MAX: OVERHEAT. Pozostało {over} s. Wszystkie statystyki bojowe osłabione; V-MAX zablokowany.")
        else:
            duration=min(105,25+will//8+10*vd)
            await self.send(f"V-MAX: gotowy. Przy obecnym Will {will} przewidywany czas działania: {duration} s. Po wygaśnięciu wchodzi Overheat; obecnie {max(4,20-8*vc)} s.")
