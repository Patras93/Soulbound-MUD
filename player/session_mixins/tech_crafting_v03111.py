# -*- coding: utf-8 -*-
"""Soulbound v0.31.12 tech/crafting UI mixin."""
class SessionTechCraftingV03111Mixin:
    async def tech_salvage_v03111(self, query=""):
        raw=str(query or "").strip()
        if not raw or normalize_lookup_text(raw) in ("list","lista","info"):
            await self.send("MACHINE SALVAGE 2.0. Rozkładanie: techsalvage <komponent>. Cięższe części wracają do podstawowych Servo/Circuit/Power Cell/Plating w Szkatułce -> Technologia.")
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
        now=time.time(); vmax=max(0,int(float(getattr(self,'v0319_vmax_until',0.0) or 0.0)-now+0.999)); over=max(0,int(float(getattr(self,'v0319_overheat_until',0.0) or 0.0)-now+0.999))
        will=int(getattr(self.character,'willpower',0) or 0)
        if vmax>0:
            await self.send(f"V-MAX: AKTYWNY. Pozostało {vmax} s. Will {will}. Efekty: Protect, Shell, Haste, Regen, Preach, Praise, Permanence.")
            await self.send("Zmiany V-MAX: Cosmic Rave = 5 losowych trafień; Shoot-All = większy damage/crit; Starlight Shower = niedyminishing AoE; Kamikaze Crush = wyższy limit HP; Heal Beam = party heal.")
        elif over>0:
            await self.send(f"V-MAX: OVERHEAT. Pozostało {over} s. Wszystkie statystyki bojowe osłabione; V-MAX zablokowany.")
        else:
            duration=max(12,min(45,18+will//8))
            await self.send(f"V-MAX: gotowy. Przy obecnym Will {will} przewidywany czas działania: {duration} s. Po wygaśnięciu wchodzi Overheat.")
