# -*- coding: utf-8 -*-
"""Soulbound v0.31.14 — player-facing Forge & Materials 3.0."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import random
from core.bootstrap_economy_professions import required_tool_tier_for_level, tool_tier, tool_tier_bonus_chance, tool_tier_name
from core.mines_threat import ITEMS
from core.progression_600 import CHARACTER_MAX_LEVEL, PROFESSION_MAX_LEVEL
from network.protocol_gameplay_utils import (
    V0925_RUNES,
    V0925_SALVAGE_MATERIALS,
    find_by_name,
    normalize_lookup_text,
    roll_crafting_xp,
    v03041_salvage_material_key,
    v03042_equipment_level,
    v0925_equipment_socket_count,
)
from player.session_mixins.forge_guilds import SessionForgeGuildsMixin
from systems.crafting_expansion import RUNE_CRAFT_COSTS_V03114, SALVAGE3_V03114, TECH_SET_SPECS_V03114
from systems.crafting_quality import (
    crafting_mastery_category_v03054,
    crafting_mastery_level_v03054,
    player_item_display_name_v0335,
)
from systems.equipment_crafting import CRAFT_RECIPES, jewelry_socket_capacity
from systems.items_resources import BLACKSMITH_TIERS
from systems.tech_crafting import equipment_gem_socket_capacity_v03111
from world.dynamic_content import SALVAGE_SMELT_FALLBACK_V03113

class SessionCraftingExpansionV03114Mixin:
    def equipment_total_socket_capacity_v03114(self, item_id, item, kind="gem"):
        if kind=="rune": base=v0925_equipment_socket_count(item)
        else: base=equipment_gem_socket_capacity_v03111(item) if "equipment_gem_socket_capacity_v03111" in globals() else jewelry_socket_capacity(item)
        return max(0,int(base))+max(0,int(self.server.db.equipment_socket_bonus_v03114(self.account_id,item_id)))

    async def salvage_equipment_v0925(self, args=""):
        raw=str(args or "").strip()
        norm=normalize_lookup_text(raw)
        if norm in ("wszystko", "all", "everything"):
            return await self.salvage_all_v0356()
        # Preserve the old EQ list/default behavior.
        if not raw or normalize_lookup_text(raw) in ("list","lista","info"):
            await SessionForgeGuildsMixin.salvage_equipment_v0925(self,args)
            await self.send("ROZKŁADANIE EQ: można też rozkładać boardy, Tech EQ, stare Upgrade Kity i ciężkie części bossowe. Użyj rozloz <nazwa>.")
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
            await self.send("Nie udało się pobrać przedmiotu do rozkładania EQ."); return
        outputs=SALVAGE3_V03114[iid]
        for oid,qty in outputs.items(): self.server.db.add_storage_item(self.account_id,"craftbox",oid,qty)
        await self.send("ROZKŁADANIE EQ: "+item['name']+" -> "+", ".join(f"{ITEMS[o]['name']} x{q}" for o,q in outputs.items())+".")
        salvage_level=max(1,min(CHARACTER_MAX_LEVEL,int(item.get("required_character_level",item.get("required_mastery",item.get("min_profession_level",1))) or 1)))
        salvage_prof_xp=max(10,10+salvage_level//12+sum(int(q) for q in outputs.values())*2)
        messages,_prof_after,_tool_after=self.grant_profession_progress(
            "Kowalstwo",salvage_prof_xp,"crafting",0,tool_progress=False
        )
        for message in messages: await self.send(message)


    async def salvage_all_v0356(self):
        """v0.35.6: bezpieczne hurtowe rozkładanie wszystkich wolnych przedmiotów Salvage."""
        if not self.at_haldor_forge_v0925():
            await self.send("EQ rozkłada Haldor w Kuźni/Warsztacie Rzemieślniczym.")
            return False
        if self.combat_mob_key:
            await self.send("Nie możesz użyć salvage wszystko podczas aktywnej walki.")
            return False

        outputs_total = {}
        returned_runes = {}
        returned_gems = {}
        lost_gems = 0
        salvaged_total = 0
        salvaged_stacks = 0
        protected_skipped = 0
        equipped_skipped = 0
        progress_messages = []

        def add_total(mapping, item_id, qty):
            qty = max(0, int(qty or 0))
            if qty:
                mapping[item_id] = int(mapping.get(item_id, 0)) + qty

        def bulk_protected(item_id, item):
            # Moogle Board jest startowym, rasowym modułem Cyborga. Hurtowa komenda
            # go nie usuwa; nadal można rozłożyć go jawnie pojedynczą komendą.
            if item_id == "moogle_board":
                return True
            if item.get("no_salvage") or item.get("no_bulk_salvage"):
                return True
            if item.get("quest_item") or item.get("quest_treasure_map_for"):
                return True
            return False

        inventory_qty_v0717 = {
            str(row["item_id"]): int(row["quantity"] or 0)
            for row in self.server.db.inventory(self.account_id)
            if int(row["quantity"] or 0) > 0
        }
        equipped_qty_v0717 = {}
        for row in self.server.db.equipment(self.account_id):
            equipped_id = str(row["item_id"])
            equipped_qty_v0717[equipped_id] = equipped_qty_v0717.get(equipped_id, 0) + 1

        armor_plan = []
        for item_id, total in inventory_qty_v0717.items():
            item = ITEMS.get(item_id)
            if not item or item.get("type") != "armor":
                continue
            equipped = min(total, int(equipped_qty_v0717.get(item_id, 0)))
            free_qty = max(0, total - equipped)
            equipped_skipped += equipped
            if free_qty <= 0:
                continue
            if bulk_protected(item_id, item):
                protected_skipped += free_qty
                continue
            armor_plan.append((item_id, item, free_qty))

        # Salvage 3.0 ma również kilka nie-EQ komponentów technologicznych.
        # Armor z tego rejestru trafia już przez standardową ścieżkę wyżej.
        extended_plan = []
        for item_id, recipe_outputs in SALVAGE3_V03114.items():
            item = ITEMS.get(item_id, {})
            if item.get("type") == "armor":
                continue
            qty = int(self.available_recipe_item(item_id) or 0)
            if qty <= 0:
                continue
            if bulk_protected(item_id, item):
                protected_skipped += qty
                continue
            extended_plan.append((item_id, item, qty, recipe_outputs))

        if not armor_plan and not extended_plan:
            suffix = []
            if equipped_skipped:
                suffix.append(f"założone: {equipped_skipped}")
            if protected_skipped:
                suffix.append(f"chronione: {protected_skipped}")
            extra = (" Pominięto " + ", ".join(suffix) + ".") if suffix else ""
            await self.send("Nie masz wolnych przedmiotów nadających się do hurtowego Salvage." + extra)
            return False

        # Klasyczne EQ. Logika odzysku jest zgodna z pojedynczym Salvage 4.0,
        # ale raport jest agregowany, żeby NVDA nie czytał setek komunikatów.
        for item_id, item, free_qty in armor_plan:
            stack_done = 0
            for _ in range(free_qty):
                if int(self.free_equipment_quantity(item_id) or 0) <= 0:
                    break
                material = v03041_salvage_material_key(item)
                salvage_id = V0925_SALVAGE_MATERIALS[material][0]
                level = max(1, min(CHARACTER_MAX_LEVEL, int(
                    item.get("required_character_level", item.get("required_mastery", 1)) or 1
                )))
                rarity = str(item.get("rarity", "common") or "common").lower()
                rarity_bonus = {
                    "uncommon": 0, "rare": 1, "epic": 1, "legendary": 2,
                    "mythic": 3, "unique": 3, "eternal": 4, "crafted": 0,
                }.get(rarity, 0)
                salvage_qty = max(1, 1 + level // 100 + rarity_bonus)

                total_before = int(self.server.db.item_qty(self.account_id, item_id) or 0)
                last_copy = total_before <= 1
                rune_rows = list(self.server.db.equipment_runes_v0925(self.account_id, item_id)) if last_copy else []
                gem_rows = []
                if last_copy:
                    try:
                        slot = str(item.get("slot") or "")
                        if slot:
                            gem_rows = list(self.server.db.socketed_gems(self.account_id, slot, item_id))
                    except Exception:
                        gem_rows = []
                reforged = self.server.db.equipment_reforge(self.account_id, item_id) if last_copy else None

                if not self.server.db.remove_item(self.account_id, item_id, 1):
                    break

                self.server.db.add_storage_item(self.account_id, "craftbox", salvage_id, salvage_qty)
                add_total(outputs_total, salvage_id, salvage_qty)

                essence = 1 if level >= 100 else 0
                dust = 1 if level >= 200 else 0
                if rarity in ("legendary", "mythic", "unique", "eternal"):
                    essence += 1
                if level >= 300:
                    dust += 1
                if reforged:
                    essence += 1
                if essence:
                    self.server.db.add_storage_item(self.account_id, "craftbox", "reforge_essence", essence)
                    add_total(outputs_total, "reforge_essence", essence)
                if dust:
                    self.server.db.add_storage_item(self.account_id, "craftbox", "rune_dust", dust)
                    add_total(outputs_total, "rune_dust", dust)

                if last_copy:
                    for row in rune_rows:
                        rune_id = str(row["rune_id"])
                        if rune_id in ITEMS:
                            self.server.db.add_storage_item(self.account_id, "craftbox", rune_id, 1)
                            add_total(returned_runes, rune_id, 1)
                    try:
                        prow = self.server.db.profession(self.account_id, "Kowalstwo")
                        smith = max(1, min(PROFESSION_MAX_LEVEL, int(prow["level"])))
                    except Exception:
                        smith = 1
                    gem_chance = min(0.85, 0.25 + smith * 0.0015)
                    for row in gem_rows:
                        gem_id = str(row["gem_id"])
                        if random.random() <= gem_chance and gem_id in ITEMS:
                            self.server.db.add_storage_item(self.account_id, "craftbox", gem_id, 1)
                            add_total(returned_gems, gem_id, 1)
                        else:
                            lost_gems += 1
                    if gem_rows:
                        self.server.db.conn.execute(
                            "DELETE FROM equipment_gems WHERE account_id=? AND slot=? AND jewelry_item_id=?",
                            (self.account_id, str(item.get("slot") or ""), item_id),
                        )
                        self.server.db.conn.commit()
                    self.server.db.clear_equipment_crafting_v0925(self.account_id, item_id)

                salvage_prof_xp = max(8, 8 + level // 10 + rarity_bonus * 6)
                messages, _prof_after, _tool_after = self.grant_profession_progress(
                    "Kowalstwo", salvage_prof_xp, "crafting", 0, tool_progress=False
                )
                # Przy hurtowej operacji zachowaj komunikaty o awansach, ale nie spam XP za każdą sztukę.
                for message in messages:
                    low_message = normalize_lookup_text(message)
                    if "osiaga poziom" in low_message or "awansuje" in low_message or "awansujesz" in low_message:
                        progress_messages.append(message)

                salvaged_total += 1
                stack_done += 1
            if stack_done:
                salvaged_stacks += 1

        # Rozszerzone, nie-EQ Salvage 3.0.
        for item_id, item, qty, recipe_outputs in extended_plan:
            done = 0
            for _ in range(qty):
                if self.available_recipe_item(item_id) <= 0:
                    break
                if not self.consume_recipe_item(item_id, 1):
                    break
                for output_id, output_qty in recipe_outputs.items():
                    self.server.db.add_storage_item(self.account_id, "craftbox", output_id, output_qty)
                    add_total(outputs_total, output_id, output_qty)
                salvage_level = max(1, min(CHARACTER_MAX_LEVEL, int(
                    item.get("required_character_level", item.get("required_mastery", item.get("min_profession_level", 1))) or 1
                )))
                salvage_prof_xp = max(10, 10 + salvage_level // 12 + sum(int(q) for q in recipe_outputs.values()) * 2)
                messages, _prof_after, _tool_after = self.grant_profession_progress(
                    "Kowalstwo", salvage_prof_xp, "crafting", 0, tool_progress=False
                )
                for message in messages:
                    low_message = normalize_lookup_text(message)
                    if "osiaga poziom" in low_message or "awansuje" in low_message or "awansujesz" in low_message:
                        progress_messages.append(message)
                salvaged_total += 1
                done += 1
            if done:
                salvaged_stacks += 1

        if salvaged_total <= 0:
            await self.send("Salvage wszystko nie rozłożyło żadnego przedmiotu.")
            return False

        clan = self.server.db.clan_membership(self.account_id)
        if clan:
            self.server.db.clan_metric_add(int(clan["clan_id"]), "salvage", salvaged_total)
            self.server.db.clan_log(
                int(clan["clan_id"]), self.account_id,
                f"{self.character.name} użył Salvage Wszystko: {salvaged_total} przedmiotów."
            )

        output_parts = []
        for output_id, qty in sorted(
            outputs_total.items(), key=lambda row: normalize_lookup_text(ITEMS.get(row[0], {}).get("name", row[0]))
        ):
            output_parts.append(f"{player_item_display_name_v0335(output_id)} x{qty}")
        for rune_id, qty in sorted(returned_runes.items()):
            output_parts.append(f"zwrócona runa {player_item_display_name_v0335(rune_id)} x{qty}")
        for gem_id, qty in sorted(returned_gems.items()):
            output_parts.append(f"odzyskany klejnot {player_item_display_name_v0335(gem_id)} x{qty}")
        if lost_gems:
            output_parts.append(f"utracone klejnoty {lost_gems}")

        skipped = []
        if equipped_skipped:
            skipped.append(f"założone {equipped_skipped}")
        if protected_skipped:
            skipped.append(f"chronione {protected_skipped}")
        skipped_text = (" Pominięto: " + ", ".join(skipped) + ".") if skipped else ""

        await self.send(
            f"SALVAGE WSZYSTKO: rozłożono {salvaged_total} przedmiotów w {salvaged_stacks} pozycjach."
            + skipped_text
        )
        if output_parts:
            # Dzielimy długi raport na krótkie porcje, żeby czytnik ekranu nie dostał jednej ogromnej linii.
            chunk = []
            for part in output_parts:
                chunk.append(part)
                if len(chunk) >= 8:
                    await self.send("Odzysk: " + ", ".join(chunk) + ".")
                    chunk = []
            if chunk:
                await self.send("Odzysk: " + ", ".join(chunk) + ".")
        for message in dict.fromkeys(progress_messages):
            await self.send(message)
        return True

    def max_recipe_crafts_v03114(self, recipe):
        """Dokładny limit liczby wykonań receptury z aktualnych materiałów."""
        limits=[]
        for iid,q in (recipe.get("ingredients") or {}).items():
            q=max(1,int(q))
            limits.append(max(0, int(self.available_recipe_item(iid)))//q)

        pooled_pool=tuple(recipe.get("pooled_ingredient_pool") or ())
        pooled_needed=max(0,int(recipe.get("pooled_ingredient_count",0) or 0))
        if pooled_pool and pooled_needed:
            pooled_have=sum(max(0,int(self.available_recipe_item(iid))) for iid in pooled_pool)
            limits.append(pooled_have//pooled_needed)

        distinct_pool=tuple(recipe.get("distinct_ingredient_pool") or ())
        distinct_needed=max(0,int(recipe.get("distinct_ingredient_count",0) or 0))
        if distinct_pool and distinct_needed:
            quantities=[max(0,int(self.available_recipe_item(iid))) for iid in distinct_pool]
            upper=sum(quantities)//distinct_needed if distinct_needed else 0
            lo,hi=0,max(0,upper)
            while lo<hi:
                mid=(lo+hi+1)//2
                # Dla każdego wykonania potrzeba distinct_needed różnych rodzajów.
                # Jeden rodzaj może dać najwyżej jedną sztukę na każde wykonanie.
                possible=sum(min(qty,mid) for qty in quantities)>=mid*distinct_needed
                if possible: lo=mid
                else: hi=mid-1
            limits.append(lo)

        if not limits:
            return 0
        return max(0,min(limits))

    async def craft_many_v0614(self, recipe_id, recipe, requested=None):
        """v0.61.4: bezpieczne wielokrotne craftowanie przez istniejący silnik.

        Każde wykonanie nadal przechodzi przez perform_recipe, więc zachowuje
        losowy XP, jakość, krytyczny craft, bonus Tieru, questy i osiągnięcia.
        """
        possible=self.max_recipe_crafts_v03114(recipe)
        if possible<=0:
            await self.send("Nie masz składników na ani jedno wykonanie tej receptury.")
            return False
        target=possible if requested is None else min(max(1,int(requested)),possible)
        if requested is not None and int(requested)>possible:
            await self.send(
                f"CRAFT HURTOWY: prosisz o {int(requested)}, ale z aktualnych materiałów można wykonać {possible}. "
                f"Wykonuję maksymalnie {target}."
            )
        else:
            label="wszystko" if requested is None else str(target)
            await self.send(
                f"CRAFT HURTOWY: {recipe['name']}. Liczba wykonań: {label}; maksimum z materiałów: {possible}. "
                "XP, jakość, questy i bonusy są naliczane osobno za każde udane wykonanie."
            )
        done=0
        while done<target:
            if not await self.perform_recipe(recipe_id,CRAFT_RECIPES,"rzemiosło"):
                break
            done+=1
        await self.send(f"CRAFT HURTOWY zakończony: {done}/{target} udanych wykonań.")
        return done>0

    async def craft_item_v03114(self, query):
        raw=str(query or '').strip(); norm=normalize_lookup_text(raw)
        words=raw.split(maxsplit=1)
        if len(words)>=2 and normalize_lookup_text(words[0]) in ("max","wszystko","all","everything"):
            wanted=words[1]
            found=find_by_name(CRAFT_RECIPES,wanted)
            if not found:
                await self.send("Nie rozpoznaję receptury do craft wszystko.")
                return False
            rid,recipe=found
            return await self.craft_many_v0614(rid,recipe,None)
        if len(words)>=2 and words[0].isdigit():
            requested=int(words[0])
            if requested<=0:
                await self.send("Liczba wykonań craft musi być większa od zera.")
                return False
            wanted=words[1]
            found=find_by_name(CRAFT_RECIPES,wanted)
            if not found:
                await self.send("Nie rozpoznaję receptury do craft <ilość>.")
                return False
            rid,recipe=found
            return await self.craft_many_v0614(rid,recipe,requested)
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
            # v0.35.7: prawdziwy przetop hurtowy. Wszystkie dostępne rudy,
            # Stalowe Płyty i materiały Salvage są przetwarzane jako JEDNA
            # akcja, z jednym czasem oczekiwania i jednym wspólnym pakietem XP.
            if self.combat_mob_key:
                await self.send("Nie możesz użyć przetop wszystko podczas walki.")
                return False

            tool_type, tool_item_id, tool_name = self.recipe_tool_info(CRAFT_RECIPES, None)
            if self.server.db.item_qty(self.account_id, tool_item_id) <= 0:
                await self.send(f"Do przetapiania potrzebujesz: {tool_name}.")
                return False
            if self.character.room_id != "forge":
                await self.send("Przetapianie wykonasz w Kuźni.")
                return False

            profession = "Kowalstwo"
            profession_row = self.server.db.profession(self.account_id, profession)
            profession_level = int(profession_row["level"])
            tool_row = self.server.db.tool(self.account_id, tool_type)
            old_tool_level = int(tool_row["level"])
            current_tool_tier = tool_tier(old_tool_level)

            recipe_ids = [tier["ingot"] for tier in BLACKSMITH_TIERS]
            recipe_ids.append("recycled_steel_ingot")
            recipe_ids.extend(SALVAGE_SMELT_FALLBACK_V03113.values())
            recipe_ids = list(dict.fromkeys(recipe_ids))

            plan = []
            locked_crafts = 0
            for recipe_id in recipe_ids:
                recipe = CRAFT_RECIPES.get(recipe_id)
                if not recipe:
                    continue
                count = self.max_recipe_crafts_v03114(recipe)
                if count <= 0:
                    continue
                required_profession = max(
                    1, int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1)
                )
                required_tool_tier = required_tool_tier_for_level(required_profession)
                if profession_level < required_profession or current_tool_tier < required_tool_tier:
                    locked_crafts += count
                    continue
                if self.character.room_id not in recipe.get("stations", ()):
                    continue
                plan.append((recipe_id, recipe, count))

            if not plan:
                if locked_crafts:
                    await self.send(
                        "Masz materiały do przetopienia, ale wymagają wyższego Kowalstwa "
                        "lub Tieru Młota Rzemieślniczego."
                    )
                else:
                    await self.send("Brak materiałów do przetopienia.")
                return False

            total_crafts = sum(count for _rid, _recipe, count in plan)
            action_seconds = max(
                self.recipe_action_seconds(tool_type, profession_level, recipe)
                for _rid, recipe, _count in plan
            )
            await self.send(
                f"PRZETOP WSZYSTKO: {total_crafts} przetopów w jednej akcji. "
                f"{self.tool_action_label(tool_type)}: {action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

            outputs = {}
            total_output_items = 0
            total_profession_xp_base = 0
            total_tool_xp_base = 0
            bonus_chance = tool_tier_bonus_chance(old_tool_level)

            for _recipe_id, recipe, count in plan:
                # Pobierz cały stos składników tej receptury naraz.
                consumed = True
                for item_id, quantity in recipe.get("ingredients", {}).items():
                    need = int(quantity) * int(count)
                    if need > 0 and not self.consume_recipe_item(item_id, need):
                        consumed = False
                        break
                if not consumed:
                    await self.send("Nie udało się pobrać części materiałów. Przetop hurtowy przerwany.")
                    break

                output_id = recipe["output"]
                per_craft = max(1, int(recipe.get("quantity", 1) or 1))
                base_quantity = per_craft * count

                # Zachowaj średnią korzyść z bonusu Tieru bez wykonywania tysięcy
                # osobnych akcji/losowań.
                bonus_crafts = 0
                if bonus_chance > 0:
                    expected = count * float(bonus_chance)
                    bonus_crafts = int(expected)
                    if random.random() < (expected - bonus_crafts):
                        bonus_crafts += 1
                produced = base_quantity + bonus_crafts * per_craft

                self.server.db.add_item(self.account_id, output_id, produced)
                outputs[output_id] = int(outputs.get(output_id, 0)) + produced
                total_output_items += produced
                await self.record_item_collection(
                    output_id, source="Przetapianie", announce=True,
                    record_history=False, amount=produced
                )
                await self.announce_craft_quest_progress(output_id, produced)

                prof_base = int(recipe.get("profession_xp", 10) or 10) * count
                tool_base = int(recipe.get("tool_xp", 8) or 8) * count
                total_profession_xp_base += prof_base
                total_tool_xp_base += tool_base

            if not outputs:
                return False

            # Jedna akcja mastery/statystyk oraz jeden wspólny grant XP.
            first_recipe = plan[0][1]
            mastery_category = crafting_mastery_category_v03054(first_recipe, profession)
            mastery_before_row = self.server.db.crafting_mastery_v03054(
                self.account_id, profession, mastery_category
            )
            mastery_before = crafting_mastery_level_v03054(mastery_before_row["actions"])
            mastery_after_row = self.server.db.add_crafting_mastery_action_v03054(
                self.account_id, profession, mastery_category, critical=False, legendary=False
            )
            mastery_after = crafting_mastery_level_v03054(mastery_after_row["actions"])

            self.server.db.add_lifetime_stat(self.account_id, "craft_actions", 1)
            self.server.db.add_lifetime_stat(self.account_id, "crafted_items", total_output_items)
            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)

            pooled_profession_xp = roll_crafting_xp(max(1, total_profession_xp_base))
            pooled_tool_xp = roll_crafting_xp(max(1, total_tool_xp_base))
            messages, _profession_level_after, new_tool_level = self.grant_profession_progress(
                profession, pooled_profession_xp, tool_type, pooled_tool_xp
            )

            result_parts = [f"{ITEMS[item_id]['name']} x{qty}" for item_id, qty in outputs.items()]
            await self.send(
                f"PRZETOP WSZYSTKO zakończony: {total_crafts} przetopów jako jedna akcja."
            )
            chunk = []
            for part in result_parts:
                chunk.append(part)
                if len(chunk) >= 6:
                    await self.send("Uzyskano: " + ", ".join(chunk) + ".")
                    chunk = []
            if chunk:
                await self.send("Uzyskano: " + ", ".join(chunk) + ".")
            for message in messages:
                await self.send(message)
            if mastery_after > mastery_before:
                await self.send(
                    f"Crafting Mastery {profession}/{mastery_category}: "
                    f"{mastery_before} -> {mastery_after}."
                )
            if new_tool_level != old_tool_level:
                await self.send(
                    f"{tool_name} ma teraz poziom {new_tool_level}, "
                    f"Tier {tool_tier(new_tool_level)}: {tool_tier_name(tool_type, new_tool_level)}."
                )
            if locked_crafts:
                await self.send(
                    f"Pominięto {locked_crafts} możliwych przetopów wymagających wyższego "
                    "Kowalstwa lub Tieru Młota."
                )
            await self.sync_extended_achievements()
            return True
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
            input_text = " + ".join(
                f"{ITEMS.get(item_id, {}).get('name', item_id)} x{int(amount) * n}"
                for item_id, amount in rec.get("ingredients", {}).items()
            )
            output_id = rec.get("output")
            output_name = ITEMS.get(output_id, {}).get("name", rec.get("name", output_id))
            output_count = max(1, int(rec.get("quantity", 1) or 1)) * n
            await self.send(f"PRZETOP MAX: {input_text} -> {output_name} x{output_count}.")
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
            await self.send("RAFINACJA. Użycie: refine <stop>. Dostępne:")
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
