# -*- coding: utf-8 -*-
"""Recipes and core crafting actions."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import random
from core.bootstrap_economy_professions import (
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
    required_tool_tier_for_level,
    tool_tier,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS, TOOL_SHOP_ROOMS
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text, roll_crafting_xp
from systems.content_registry import NPCS
from systems.game_feel_rewards import craft_inspiration_v11324
from systems.market_dynamics_v1250 import material_grade_v1250, material_quality_upgrade_v1250, masterpiece_promote_v12812
from systems.crafting_expansion import CRAFT_MATERIAL_STORAGE_IDS
from systems.crafting_quality import (
    CRAFT_CRIT_AFFIX_NAMES_V03054,
    CRAFT_QUALITY_V03054,
    crafting_critical_chance_v03054,
    crafting_mastery_category_v03054,
    crafting_mastery_level_v03054,
    crafting_output_is_quality_equipment_v03054,
    crafting_quality_output_v03054,
    crafting_quality_roll_v03054,
)
from systems.equipment_crafting import ALCHEMY_RECIPES, COOK_RECIPES, CRAFT_RECIPES, JEWELCRAFT_RECIPES, SHOP_SELLERS
from systems.items_resources import BLACKSMITH_TIERS
from world.dynamic_content import SALVAGE_SMELT_FALLBACK_V03113


class SessionCraftingMixin:
    def available_recipe_item(self, item_id):
            container = self.recipe_container_for_item(item_id)
            storage = (
                self.server.db.storage_qty(self.account_id, container, item_id)
                if container else 0
            )
            return storage + self.server.db.item_qty(self.account_id, item_id)

    def consume_recipe_item(self, item_id, quantity):
            remaining = max(0, int(quantity))
            container = self.recipe_container_for_item(item_id)

            if container and remaining > 0:
                stored = self.server.db.storage_qty(
                    self.account_id, container, item_id
                )
                take = min(stored, remaining)
                if take > 0:
                    if not self.server.db.remove_storage_item(
                        self.account_id, container, item_id, take
                    ):
                        return False
                    remaining -= take

            if remaining > 0:
                if not self.server.db.remove_item(
                    self.account_id, item_id, remaining
                ):
                    return False
                remaining = 0

            return True

    def recipe_station_text(self, stations):
            return " lub ".join(ROOMS[room_id]["name"] for room_id in stations)

    def recipe_distinct_ingredient_choices(self, recipe):
            pool = tuple(recipe.get("distinct_ingredient_pool") or ())
            needed = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
            available = [
                item_id for item_id in pool
                if self.available_recipe_item(item_id) > 0
            ]
            return available[:needed]

    def recipe_pooled_ingredient_choices(self, recipe):
            """Wybiera dowolną liczbę sztuk z jednej puli, także kilka tego samego ID."""
            pool = tuple(recipe.get("pooled_ingredient_pool") or ())
            needed = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
            selected = []
            remaining = needed
            for item_id in pool:
                if remaining <= 0:
                    break
                available = max(0, int(self.available_recipe_item(item_id)))
                take = min(remaining, available)
                if take > 0:
                    selected.extend([item_id] * take)
                    remaining -= take
            return selected

    def recipe_ingredients_text(self, recipe):
            parts = [
                f"{ITEMS[item_id]['name']} x{quantity}"
                for item_id, quantity in recipe["ingredients"].items()
            ]
            distinct_pool = tuple(recipe.get("distinct_ingredient_pool") or ())
            distinct_count = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
            if distinct_pool and distinct_count:
                label = recipe.get("distinct_ingredient_label", "różne składniki")
                examples = ", ".join(ITEMS[item_id]["name"] for item_id in distinct_pool)
                parts.append(f"{distinct_count} {label} ({examples})")
            pooled_pool = tuple(recipe.get("pooled_ingredient_pool") or ())
            pooled_count = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
            if pooled_pool and pooled_count:
                label = recipe.get("pooled_ingredient_label", "dowolne składniki z puli")
                parts.append(f"{pooled_count} {label}")
            return ", ".join(parts)

    async def show_recipes(self, mode=""):
            _raw_mode = self.normalize_description_query(mode)
            if not _raw_mode:
                await self.send("RECEPTURY — WYBIERZ PROFESJĘ")
                await self.send("receptury kowalstwo")
                await self.send("receptury drwalstwo")
                await self.send("receptury gotowanie")
                await self.send("receptury alchemia")
                await self.send("receptury jubilerstwo")
                await self.send("receptury krawiectwo")
                await self.send("receptury garbarstwo")
                await self.send("receptury stolarstwo")
                await self.send("receptury zaklinanie")
                await self.send("Receptury nie są łączone w jedną mieszaną listę; każda profesja ma osobną sekcję.")
                return
            if _raw_mode.startswith(("zaklinanie ", "enchanting ")):
                parts = _raw_mode.split(maxsplit=1)
                await self.v03053_show_recipes(parts[0], parts[1])
                return
            if _raw_mode in ("krawiectwo", "tailoring", "garbarstwo", "leatherworking", "stolarstwo", "carpentry", "zaklinanie", "enchanting"):
                await self.v03053_show_recipes(_raw_mode)
                return
            mode = _raw_mode
            craft_modes = {
                "craft", "stworz", "rzemioslo", "kowalstwo",
                "smithing", "blacksmithing", "kuj",
            }
            cook_modes = {
                "cook", "gotuj", "gotowanie",
            }
            alchemy_modes = {
                "alchemy", "alchemia",
            }
            jewel_modes = {
                "jubilerstwo", "jewelcrafting", "jewelry",
                "bizuteria", "biżuteria", "jub",
            }

            if mode in ("drwalstwo", "drwalnictwo", "drwal", "woodcutting", "deski", "tarcica"):
                await self.send("RECEPTURY DRWALNICTWA — obrabiaj <deska>; obrabiaj max <deska>.")
                from systems.professions import V03053_CRAFT_RECIPES
                for recipe in list(CRAFT_RECIPES.values()) + list(V03053_CRAFT_RECIPES.values()):
                    if recipe.get("profession") != "Drwalstwo" or recipe.get("tool_type") != "woodcutting":
                        continue
                    await self.send(
                        f"{recipe['name']}. Składniki: {self.recipe_ingredients_text(recipe)}. "
                        f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                        f"{self.recipe_level_requirement_text(CRAFT_RECIPES, recipe)}"
                    )
                return
            if mode in craft_modes:
                show_craft = True
                show_cook = False
                show_alchemy = False
                show_jewel = False
            elif mode in cook_modes:
                show_craft = False
                show_cook = True
                show_alchemy = False
                show_jewel = False
            elif mode in alchemy_modes:
                show_craft = False
                show_cook = False
                show_alchemy = True
                show_jewel = False
            elif mode in jewel_modes:
                show_craft = False
                show_cook = False
                show_alchemy = False
                show_jewel = True
            else:
                await self.send("Nie rozpoznaję grupy receptur. Dostępne: drwalstwo, kowalstwo, gotowanie, alchemia, jubilerstwo, krawiectwo, garbarstwo, stolarstwo, zaklinanie.")
                return

            if show_craft:
                await self.send("RECEPTURY RZEMIOSŁA I KOWALSTWA")
                for recipe in CRAFT_RECIPES.values():
                    if recipe.get("profession") == "Drwalstwo":
                        continue
                    await self.send(
                        f"{recipe['name']}. Składniki: "
                        f"{self.recipe_ingredients_text(recipe)}. "
                        f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                        f"{self.recipe_level_requirement_text(CRAFT_RECIPES, recipe)} "
                        f"{recipe['desc']}"
                    )

            if show_cook:
                await self.send("RECEPTURY GOTOWANIA")
                for recipe in COOK_RECIPES.values():
                    await self.send(
                        f"{recipe['name']}. Składniki: "
                        f"{self.recipe_ingredients_text(recipe)}. "
                        f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                        f"{self.recipe_level_requirement_text(COOK_RECIPES, recipe)} "
                        f"{recipe['desc']}"
                    )

            if show_alchemy:
                await self.send("RECEPTURY ALCHEMII")
                for recipe in ALCHEMY_RECIPES.values():
                    await self.send(
                        f"{recipe['name']}. Składniki: "
                        f"{self.recipe_ingredients_text(recipe)}. "
                        f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                        f"{self.recipe_level_requirement_text(ALCHEMY_RECIPES, recipe)} "
                        f"{recipe['desc']}"
                    )

            if show_jewel:
                await self.send("RECEPTURY JUBILERSTWA")
                for recipe in JEWELCRAFT_RECIPES.values():
                    await self.send(
                        f"{recipe['name']}. Składniki: "
                        f"{self.recipe_ingredients_text(recipe)}. "
                        f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                        f"{self.recipe_level_requirement_text(JEWELCRAFT_RECIPES, recipe)} "
                        f"{recipe['desc']}"
                    )

    async def process_wood_v1108(self, query=""):
            """Obróbka wszystkich desek: Drwalstwo + Piła, bez Kowalstwa."""
            from systems.professions import V03053_CRAFT_RECIPES
            raw = str(query or "").strip()
            plank_recipes = {
                k: v for k, v in CRAFT_RECIPES.items()
                if v.get("profession") == "Drwalstwo" and v.get("tool_type") == "woodcutting"
            }
            extra = {
                k: v for k, v in V03053_CRAFT_RECIPES.items()
                if v.get("profession") == "Drwalstwo" and v.get("tool_type") == "woodcutting"
            }
            if not raw or normalize_lookup_text(raw) in ("lista", "list", "info", "receptury"):
                await self.send("OBRÓBKA DREWNA — Drwalstwo i Piła, Obóz Drwala.")
                await self.send("Wykonaj: obrabiaj <nazwa deski>. Hurtowo: obrabiaj max <nazwa deski>.")
                for recipe in (*plank_recipes.values(), *extra.values()):
                    await self.send(f"{recipe['name']}: {self.recipe_ingredients_text(recipe)}.")
                return False
            many = False
            words = raw.split(maxsplit=1)
            if len(words) == 2 and normalize_lookup_text(words[0]) in ("max", "wszystko", "all"):
                many = True
                raw = words[1]
            matched = find_by_name(plank_recipes, raw)
            recipes = plank_recipes
            if not matched:
                matched = find_by_name(extra, raw)
                recipes = extra
            if not matched:
                await self.send("Nie znam takiej deski. Wpisz obrabiaj lista lub receptury drwalstwo.")
                return False
            rid, rec = matched
            if not many:
                return await self.perform_recipe(rid, recipes, "obróbka drewna")
            maximum = self.max_recipe_crafts_v03114(rec)
            if maximum < 1:
                await self.send("Nie masz materiałów na obróbkę ani jednej deski.")
                return False
            await self.send(f"OBRÓBKA MAX: {rec['name']}, do {maximum} wykonań.")
            done = 0
            while done < maximum:
                if not await self.perform_recipe(rid, recipes, "obróbka drewna"):
                    break
                done += 1
            await self.send(f"OBRÓBKA MAX: {done}/{maximum} wykonano.")
            return done > 0

    def recipe_profession_name(self, recipes, recipe=None):
            if recipe and recipe.get("profession"):
                return str(recipe["profession"])
            if recipes is CRAFT_RECIPES:
                return "Kowalstwo"
            if recipes is ALCHEMY_RECIPES:
                return "Alchemia"
            if recipes is JEWELCRAFT_RECIPES:
                return "Jubilerstwo"
            return "Gotowanie"

    def recipe_tool_info(self, recipes, recipe=None):
            if recipe and recipe.get("tool_type"):
                mapping = {
                    "fishing": ("fishing_rod", "Wędka"),
                    "mining": ("pickaxe", "Kilof"),
                    "woodcutting": ("saw", "Piła"),
                    "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
                    "cooking": ("chef_knife", "Nóż Kucharski"),
                    "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
                    "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
                    "jewelcrafting": ("jeweler_pliers", "Szczypce Jubilerskie"),
                    "tailoring": ("tailor_kit", "Zestaw Krawiecki"),
                    "leatherworking": ("tanning_knife", "Nóż Garbarski"),
                    "carpentry": ("carpenter_tools", "Narzędzia Ciesielskie"),
                    "enchanting": ("runic_focus", "Fokus Runiczny"),
                    "archaeology": ("archaeology_brush", "Pędzel Archeologa"),
                    "cartography_profession": ("surveyor_compass", "Kompas Mierniczy"),
                }
                tool_type = str(recipe["tool_type"])
                if tool_type in mapping:
                    item_id, name = mapping[tool_type]
                else:
                    # v24: custom profession tools are validated by the live
                    # OLC registry, not listed in the original 14 static tools.
                    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP
                    item_id = recipe.get('tool_item_id')
                    meta = ITEMS.get(item_id, {})
                    if (tool_type not in TOOL_PROFESSION_MAP or
                            meta.get('type') != 'tool' or meta.get('tool_type') != tool_type):
                        raise ValueError('Nieprawidłowy typ narzędzia nowej profesji.')
                    name = meta['name']
                return tool_type, recipe.get("tool_item_id", item_id), recipe.get("tool_name", name)
            if recipes is CRAFT_RECIPES:
                return "crafting", "crafting_hammer", "Młot Rzemieślniczy"
            if recipes is ALCHEMY_RECIPES:
                return "alchemy", "alchemy_mortar", "Moździerz Alchemiczny"
            if recipes is JEWELCRAFT_RECIPES:
                return "jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie"
            return "cooking", "chef_knife", "Nóż Kucharski"

    def recipe_level_requirement_text(self, recipes, recipe):
            profession = self.recipe_profession_name(recipes, recipe)
            required = max(1, int(
                recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1
            ))
            _tool_type, _tool_item, tool_name = self.recipe_tool_info(recipes, recipe)
            required_tier = required_tool_tier_for_level(required)
            return (
                f"Wymaga: {profession} poziom {required} oraz "
                f"{tool_name} Tier {required_tier}+."
            )

    async def perform_recipe(self, query, recipes, action_name):
            if self.combat_mob_key:
                await self.send(
                    f"Nie możesz wykonywać akcji {action_name} podczas walki."
                )
                return False

            found = find_by_name(recipes, query)
            if not found:
                await self.send("Nie rozpoznaję tej receptury. Wpisz receptury.")
                return False
            recipe_id, recipe = found

            tool_type, tool_item_id, tool_name = self.recipe_tool_info(recipes, recipe)
            if self.server.db.item_qty(self.account_id, tool_item_id) <= 0:
                shop_room = TOOL_SHOP_ROOMS.get(tool_item_id)
                room_name = ROOMS.get(shop_room, {}).get("name", "właściwym sklepie profesji")
                seller_id = SHOP_SELLERS.get(shop_room)
                seller_name = NPCS.get(seller_id, {}).get("name", "specjalisty profesji")
                await self.send(
                    f"Do tej receptury potrzebujesz: {tool_name}. "
                    f"Kupisz narzędzie u {seller_name}, lokacja: {room_name}."
                )
                return False

            tool_row = self.server.db.tool(self.account_id, tool_type)
            old_tool_level = int(tool_row["level"])

            profession = self.recipe_profession_name(recipes, recipe)
            profession_row = self.server.db.profession(self.account_id, profession)
            profession_level = int(profession_row["level"])
            required_profession = max(
                1,
                int(recipe.get("min_profession_level", recipe.get("min_tool_level", 1)) or 1),
            )
            if profession_level < required_profession:
                await self.send(
                    f"{recipe['name']} wymaga {profession} poziom "
                    f"{required_profession}, a masz {profession_level}."
                )
                return False

            required_tool_tier = required_tool_tier_for_level(required_profession)
            current_tool_tier = tool_tier(old_tool_level)
            if current_tool_tier < required_tool_tier:
                await self.send(
                    f"{recipe['name']} wymaga {tool_name} Tier "
                    f"{required_tool_tier}+, a masz Tier {current_tool_tier}."
                )
                return False

            if self.character.room_id not in recipe["stations"]:
                await self.send(
                    f"Tę recepturę wykonasz w: "
                    f"{self.recipe_station_text(recipe['stations'])}."
                )
                return False

            missing = []
            for item_id, quantity in recipe["ingredients"].items():
                have = self.available_recipe_item(item_id)
                if have < quantity:
                    missing.append(
                        f"{ITEMS[item_id]['name']}: masz {have}, potrzeba {quantity}"
                    )

            distinct_pool = tuple(recipe.get("distinct_ingredient_pool") or ())
            distinct_needed = max(0, int(recipe.get("distinct_ingredient_count", 0) or 0))
            distinct_choices = self.recipe_distinct_ingredient_choices(recipe)
            if distinct_pool and len(distinct_choices) < distinct_needed:
                names = ", ".join(ITEMS[item_id]["name"] for item_id in distinct_pool)
                missing.append(
                    f"różne gatunki: masz {len(distinct_choices)}, potrzeba {distinct_needed}; "
                    f"liczą się {names}"
                )

            pooled_pool = tuple(recipe.get("pooled_ingredient_pool") or ())
            pooled_needed = max(0, int(recipe.get("pooled_ingredient_count", 0) or 0))
            pooled_choices = self.recipe_pooled_ingredient_choices(recipe)
            if pooled_pool and len(pooled_choices) < pooled_needed:
                label = recipe.get("pooled_ingredient_label", "składniki z puli")
                missing.append(
                    f"{label}: masz {len(pooled_choices)}, potrzeba {pooled_needed}"
                )

            if missing:
                await self.send("Brakuje składników:")
                for line in missing:
                    await self.send(line + ".")
                if recipe_id == "jewel_iron_ring":
                    in_bag = self.server.db.storage_qty(self.account_id, "bag", "iron_ore")
                    in_inventory = self.server.db.item_qty(self.account_id, "iron_ore")
                    await self.send(
                        f"Żelazny Pierścień Jubilerski: 2 rudy żelaza na jeden pierścień. "
                        f"Masz: Sakwa Górnika {in_bag}, ekwipunek {in_inventory}, "
                        f"razem {in_bag + in_inventory}. "
                        "Zlecenie Mirelli na 2 pierścienie wymaga łącznie 4 rud. "
                        "Rudy kupisz w Kuźni Dusz."
                    )
                return False

            action_seconds = self.recipe_action_seconds(
                tool_type, profession_level, recipe
            )
            await self.send(
                f"Rozpoczynasz {action_name}. "
                f"{self.tool_action_label(tool_type)}: "
                f"{action_seconds} sekund."
            )
            if (
                normalize_lookup_text(action_name) == "przetapianie"
                and hasattr(self, "smelt_wait_v1124")
            ):
                await self.smelt_wait_v1124(action_seconds)
            else:
                # v102.00.9: distinguish deliberate craft wait from engine work.
                _wait_start_v102009 = __import__('time').perf_counter()
                try:
                    await asyncio.sleep(action_seconds)
                finally:
                    self._perf_intentional_wait_v102009 = getattr(
                        self, '_perf_intentional_wait_v102009', 0.0
                    ) + (__import__('time').perf_counter() - _wait_start_v102009)

            for item_id, quantity in recipe["ingredients"].items():
                if not self.consume_recipe_item(item_id, quantity):
                    await self.send(
                        "Nie udało się pobrać składników. Receptura przerwana."
                    )
                    return False

            if distinct_pool and distinct_needed:
                distinct_choices = self.recipe_distinct_ingredient_choices(recipe)
                if len(distinct_choices) < distinct_needed:
                    await self.send(
                        "Nie masz już wymaganych różnych składników. Receptura przerwana."
                    )
                    return False
                for item_id in distinct_choices[:distinct_needed]:
                    if not self.consume_recipe_item(item_id, 1):
                        await self.send(
                            "Nie udało się pobrać różnych składników. Receptura przerwana."
                        )
                        return False

            if pooled_pool and pooled_needed:
                pooled_choices = self.recipe_pooled_ingredient_choices(recipe)
                if len(pooled_choices) < pooled_needed:
                    await self.send(
                        "Nie masz już wymaganej liczby składników z puli. Receptura przerwana."
                    )
                    return False
                for item_id in pooled_choices[:pooled_needed]:
                    if not self.consume_recipe_item(item_id, 1):
                        await self.send(
                            "Nie udało się pobrać składników z puli. Receptura przerwana."
                        )
                        return False

            output_id = recipe["output"]
            quantity = int(recipe.get("quantity", 1))

            # v0.30.54: mastery jest osobne od levelu profesji i narzędzia.
            mastery_category = crafting_mastery_category_v03054(recipe, profession)
            mastery_row = self.server.db.crafting_mastery_v03054(
                self.account_id, profession, mastery_category
            )
            mastery_before = crafting_mastery_level_v03054(mastery_row["actions"])
            _o_kurde_craft_v11324 = craft_inspiration_v11324(
                profession_level, old_tool_level, mastery_before, random.random()
            )
            _o_kurde_craft_xp_v11324 = (
                float(_o_kurde_craft_v11324["xp_multiplier"])
                if _o_kurde_craft_v11324 else 1.0
            )
            quality_key = crafting_quality_roll_v03054(
                profession_level, old_tool_level, mastery_before
            )
            # v1.25: valuable ingredients can promote the final craft by one
            # actual tier, using the existing quality item ID and equipment stats.
            material_ids_v1250 = tuple(recipe.get('ingredients') or ())
            material_ids_v1250 += tuple(recipe.get('distinct_ingredient_pool') or ())
            material_ids_v1250 += tuple(recipe.get('pooled_ingredient_pool') or ())
            grade_v1250 = material_grade_v1250(material_ids_v1250, ITEMS)
            quality_key = material_quality_upgrade_v1250(
                quality_key, grade_v1250, random.random())
            # v1.26: a genuine cooperation chain: levels of mining, smithing,
            # enchanting and archaeology add a chance to refine rare materials.
            # Uses the same authored crafted-quality variants; no duplicate EQ.
            if grade_v1250 >= 2:
                from systems.craft_chain_v1260 import craft_chain_bonus_v1260
                chain_levels = [int(r['level']) for r in self.server.db.conn.execute(
                    'SELECT level FROM professions WHERE account_id=? AND profession IN '
                    '(?,?,?,?)', (self.account_id,'Górnictwo','Kowalstwo','Zaklinanie','Archeologia'))]
                quality_key = craft_chain_bonus_v1260(
                    quality_key, grade_v1250, chain_levels, random.random())
            quality_key, _masterpiece_v12812 = masterpiece_promote_v12812(
                quality_key, profession_level, old_tool_level, mastery_before,
                grade_v1250, random.random()
            )
            critical_chance = crafting_critical_chance_v03054(
                profession_level, mastery_before
            )
            critical_craft = random.random() < min(.25, critical_chance + .0075 * grade_v1250)
            crafted_output_id, critical_affix = crafting_quality_output_v03054(
                output_id, quality_key, critical_craft, mastery_before
            )
            # v55: existing materials, profession checks, quality and crit stay
            # authoritative; only the successfully crafted EQ is strengthened.
            from systems.endless_crafting_v5500 import endless_crafted_equipment_v5500
            crafted_output_id = endless_crafted_equipment_v5500(
                crafted_output_id, profession_level, old_tool_level
            )

            tier = tool_tier(old_tool_level)
            bonus_chance = tool_tier_bonus_chance(old_tool_level)

            bonus_quantity = 0
            if bonus_chance > 0 and random.random() < bonus_chance:
                bonus_quantity = quantity

            total_quantity = quantity + bonus_quantity
            from systems.live_olc28_expansion import craft_yield
            total_quantity = craft_yield(profession, total_quantity)
            from systems.live_olc32_finale import crafting_bonus
            total_quantity = crafting_bonus(recipe_id, self.character.room_id, total_quantity)
            from systems.live_olc35_finale import city_craft_bonus
            _guild35=self.guild_row_v0926()
            total_quantity = city_craft_bonus(self.server.db.conn, int(_guild35['clan_id']) if _guild35 else None, total_quantity)
            self.server.db.add_item(
                self.account_id, crafted_output_id, total_quantity
            )
            if ITEMS.get(crafted_output_id, {}).get('infinite_depth_source') == 'forge':
                crafted_v55 = ITEMS[crafted_output_id]
                await self.send(
                    f'REZONANS RZEMIOSLA: etap {crafted_v55["source_progression_stage"]}; '
                    f'wymagana Bieglosc {crafted_v55["required_mastery"]}. '
                    'Materialy zuzyto wedlug receptury.'
                )
            # OLC33: award a configured material only after a successful craft.
            from systems.live_olc33_mechanics import craft_byproduct
            _byproduct33 = craft_byproduct(self,recipe_id)
            if _byproduct33:
                self.server.db.add_item(self.account_id,_byproduct33[0],_byproduct33[1])
                await self.record_item_collection(
                    _byproduct33[0],source='Produkt uboczny rzemiosła',
                    announce=True,amount=_byproduct33[1])
            # OLC34: an additional, independently authored exploration material.
            from systems.live_olc34_integration import profession_find
            _material34=profession_find(self,recipe_id)
            if _material34:
                self.server.db.add_item(self.account_id,_material34[0],_material34[1])
                await self.record_item_collection(
                    _material34[0],source='Odkrycie rzemieslnicze',
                    announce=True,amount=_material34[1])
            # Kolekcje/questy śledzą bazowy przedmiot, aby wariant jakości nie
            # rozbijał istniejących celów i progresji.
            await self.record_item_collection(
                output_id, source="Rzemiosło", announce=True,
                record_history=False, amount=total_quantity
            )
            mastery_after_row = self.server.db.add_crafting_mastery_action_v03054(
                self.account_id, profession, mastery_category,
                critical=bool(critical_affix),
                legendary=(quality_key == "legendary"),
            )
            mastery_after = crafting_mastery_level_v03054(mastery_after_row["actions"])
            if quality_key == "legendary" and hasattr(self.server.db, 'add_server_chronicle_event_v03811'):
                self.server.db.add_server_chronicle_event_v03811(
                    'mistrzowski_craft',
                    f'{self.character.name} stworzył legendarny przedmiot: '
                    f'{ITEMS.get(crafted_output_id, ITEMS.get(output_id, {})).get("name", crafted_output_id)}.',
                    account_id=self.account_id, actor_name=self.character.name,
                    subject_id=output_id, subject_name=ITEMS.get(output_id,{}).get('name',output_id),
                    importance=3, event_key=f'legendary:craft:{self.account_id}:{output_id}')
            self.server.db.add_lifetime_stat(self.account_id, "craft_actions", 1)
            self.server.db.add_lifetime_stat(self.account_id, "crafted_items", total_quantity)
            self.server.db.add_lifetime_stat(self.account_id, "profession_actions", 1)

            destination = (
                "Szkatułki Rzemieślniczej"
                if output_id in CRAFT_MATERIAL_STORAGE_IDS
                else "zwykłego ekwipunku"
            )
            crafted_name = ITEMS.get(crafted_output_id, ITEMS[output_id])["name"]
            if normalize_lookup_text(action_name) == "przetapianie":
                consumed_text = " + ".join(
                    f"{ITEMS.get(item_id, {}).get('name', item_id)} x{int(amount)}"
                    for item_id, amount in recipe.get("ingredients", {}).items()
                )
                await self.send(
                    f"Przetapiasz: {consumed_text} -> {crafted_name} x{quantity}. "
                    f"Przedmiot trafia do {destination}."
                )
            else:
                await self.send(
                    f"{action_name.capitalize()}: {crafted_name} "
                    f"x{quantity}. Przedmiot trafia do {destination}."
                )
            if recipe_id == "jewel_iron_ring":
                remaining_iron = self.available_recipe_item("iron_ore")
                await self.send(
                    f"Żelazny Pierścień Jubilerski: zużyto 2 rudy żelaza; "
                    f"zostało {remaining_iron}. Jeśli wykonujesz dwa pierścienie na zlecenie Mirelli, "
                    "potrzeba 4 rud łącznie. Warianty jakości pierścienia też zaliczają zlecenie."
                )
            if _masterpiece_v12812 and crafting_output_is_quality_equipment_v03054(output_id):
                await self.send(f'ARCYDZIEŁO! Materiał, mistrzostwo i narzędzie podniosły jakość: {crafted_name}.')
            if crafting_output_is_quality_equipment_v03054(output_id):
                quality_name = CRAFT_QUALITY_V03054[quality_key]["name"]
                await self.send(
                    f"Jakość craftu: {quality_name}. "
                    f"Mastery {profession}/{mastery_category}: {mastery_after}/100."
                )
                if critical_affix:
                    crafted_item = ITEMS.get(crafted_output_id,{})
                    amount = int(crafted_item.get("craft_critical_affix_amount_v03054",0) or 0)
                    stat_name = CRAFT_CRIT_AFFIX_NAMES_V03054.get(critical_affix,critical_affix)
                    await self.send(
                        f"KRYTYCZNY CRAFT: dodatkowy affix {stat_name} +{amount}."
                    )
                if mastery_after > mastery_before:
                    await self.send(
                        f"Crafting Mastery rośnie: {mastery_before} -> {mastery_after}."
                    )

            if bonus_quantity > 0:
                if tool_type == "cooking":
                    await self.send(
                        f"Bonus Tieru {tier} Noża Kucharskiego: "
                        f"przygotowujesz dodatkowo "
                        f"{ITEMS[output_id]['name']} "
                        f"x{bonus_quantity}."
                    )
                elif tool_type == "alchemy":
                    await self.send(
                        f"Bonus Tieru {tier} Moździerza Alchemicznego: "
                        f"warzysz dodatkowo "
                        f"{ITEMS[output_id]['name']} "
                        f"x{bonus_quantity}."
                    )
                elif tool_type == "jewelcrafting":
                    await self.send(
                        f"Bonus Tieru {tier} Szczypiec Jubilerskich: "
                        f"wykonujesz dodatkowo "
                        f"{ITEMS[output_id]['name']} "
                        f"x{bonus_quantity}."
                    )
                elif tool_type == "woodcutting":
                    await self.send(
                        f"Bonus Tieru {tier} Piły: "
                        f"obrabiasz dodatkowo "
                        f"{ITEMS[output_id]['name']} "
                        f"x{bonus_quantity}."
                    )
                else:
                    await self.send(
                        f"Bonus Tieru {tier} {tool_name}: "
                        f"wytwarzasz dodatkowo "
                        f"{ITEMS[output_id]['name']} "
                        f"x{bonus_quantity}."
                    )

            # v0.31.15: every successful recipe emits exactly one craft event.
            # This fixes quest progress for all profession families, including
            # blacksmith helmet/body orders and newer tailoring/leatherworking/
            # carpentry/enchanting recipes. The base output ID is intentional so
            # quality variants still count for the original quest target.
            await self.announce_craft_quest_progress(
                output_id,
                total_quantity,
            )
            # v1.12.0: każde udane wykonanie receptury liczy jeden craft do
            # aktywnego godzinnego zadania klasowego. Bonusowa ilość produktu
            # nie daje dodatkowych punktów, żeby Tier narzędzia nie skracał celu.
            await self.advance_class_guild_quest_v11132("craft", 1)

            # v1.13.58: legacy recipes without authored XP no longer fall
            # back to the same ~8-15 XP regardless of difficulty.  Use the
            # canonical recipe/content level so harder materials and recipes
            # always start from a larger raw award.
            _xp_content_level = self.profession_content_level_v11342(
                item_id=output_id, recipe=recipe,
            )
            tool_xp = (
                roll_crafting_xp(recipe["tool_xp"])
                if "tool_xp" in recipe
                else max(8, 8 + _xp_content_level // 6) + random.randint(0, max(2, _xp_content_level // 40))
            )
            profession_xp = (
                roll_crafting_xp(recipe["profession_xp"])
                if "profession_xp" in recipe
                else max(10, 10 + _xp_content_level // 4) + random.randint(0, max(3, _xp_content_level // 30))
            )
            tool_xp = max(1, int(round(tool_xp * _o_kurde_craft_xp_v11324)))
            profession_xp = max(
                1, int(round(profession_xp * _o_kurde_craft_xp_v11324))
            )
            if _o_kurde_craft_v11324:
                await self.send(
                    "O KURDE — MISTRZOWSKA INSPIRACJA: "
                    f"XP {profession} i {tool_name} x{_o_kurde_craft_xp_v11324:.2f}. "
                    "Nie zużywasz dodatkowych składników i nie powstaje darmowy duplikat EQ."
                )
            content_level = self.profession_content_level_v11342(
                item_id=output_id,
                recipe=recipe,
            )
            messages, _profession_level_after, new_tool_level = self.grant_profession_progress(
                profession,
                profession_xp,
                tool_type,
                tool_xp,
                content_level=content_level, content_key=output_id,
                jewel_recipe=(dict(recipe, gem_quality=ITEMS.get(recipe['output'], {}).get('gem_quality', 'raw'))
                              if recipes is JEWELCRAFT_RECIPES else None),
            )
            for message in messages:
                await self.send(message)

            await self.sync_extended_achievements()
            if new_tool_level != old_tool_level:
                await self.send(
                    f"{tool_name} ma teraz poziom {new_tool_level}, "
                    f"Tier {tool_tier(new_tool_level)}: "
                    f"{tool_tier_name(tool_type, new_tool_level)}."
                )

            return True

    async def show_crafting_mastery_v03054(self, query=""):
            rows = list(self.server.db.crafting_masteries_v03054(self.account_id))
            q = normalize_lookup_text(query or "")
            if q:
                rows = [r for r in rows if q in normalize_lookup_text(r["profession"]) or q in normalize_lookup_text(r["category"])]
            await self.send("CRAFTING MASTERY")
            if not rows:
                await self.send("Nie masz jeszcze mastery. Wykonaj pierwszą udaną recepturę.")
                return
            for row in rows:
                level = crafting_mastery_level_v03054(row["actions"])
                await self.send(
                    f"{row['profession']} / {row['category']}: mastery {level}/100, "
                    f"crafty {row['actions']}, krytyczne {row['criticals']}, legendarne {row['legendary_count']}."
                )
            await self.send(
                "Mastery jest niezależne od levelu profesji i narzędzia. "
                "Większe mastery zwiększa szansę na wyższą jakość i krytyczny craft."
            )

    async def show_jewelcrafting_info(self):
            await self.send("JUBILERSTWO")
            row = self.server.db.profession(
                self.account_id, "Jubilerstwo"
            )
            level = int(row["level"])
            max_level = profession_max_level("Jubilerstwo")
            rank = profession_rank(level, "Jubilerstwo")
            xp_text = (
                "maksimum"
                if level >= max_level
                else (
                    f"{row['xp']} z "
                    f"{self.profession_xp_to_next(level, 'Jubilerstwo')}"
                )
            )
            await self.send(
                f"Poziom {level} z {max_level}. "
                f"Ranga {rank} z {profession_max_rank('Jubilerstwo')}: "
                f"{profession_rank_name('Jubilerstwo', level)}. "
                f"XP: {xp_text}. Akcje: {row['actions']}."
            )
            await self.show_single_tool("jewelcrafting")
            await self.send(
                "Szczypce Jubilerskie kupisz wyłącznie u Jubilerki Mirelli "
                "w Pracowni Jubilerskiej."
            )
            await self.send(
                "Receptury: wpisz receptury jubilerstwo. "
                "Wykonywanie: jub <nazwa receptury>."
            )
            await self.send(
                "Jubilerka Mirella prowadzi 9-etapowy łańcuch zleceń "
                "od Żelaza do Eternium."
            )

    async def show_blacksmithing_info(self):
            await self.send("KOWALSTWO")
            row = self.server.db.profession(
                self.account_id, "Kowalstwo"
            )
            level = int(row["level"])
            max_level = profession_max_level("Kowalstwo")
            rank = profession_rank(level, "Kowalstwo")
            xp_text = (
                "maksimum"
                if level >= max_level
                else (
                    f"{row['xp']} z "
                    f"{self.profession_xp_to_next(level, 'Kowalstwo')}"
                )
            )
            await self.send(
                f"Kowalstwo: poziom {level} z "
                f"{max_level}. "
                f"Ranga {rank} z "
                f"{profession_max_rank('Kowalstwo')}: "
                f"{profession_rank_name('Kowalstwo', level)}. "
                f"XP: {xp_text}."
            )
            await self.show_single_tool("crafting")
            await self.send(
                "Kowalstwo rozwija się podczas przetapiania metalu "
                "i kucia przedmiotów w Kuźni Dusz."
            )
            await self.send(
                "Komendy: kowalstwo, przetop <metal>, przetop max <metal>, "
                "przetop wszystko, przetop status, przetop stop, "
                "kuj <receptura>, craft <receptura>, ulepsz <EQ>, "
                "ulepsz lista, receptury kowalstwo."
            )
            await self.send(
                "Materiały przechodzą od Żelaza, Srebra i Złota "
                "aż do Kobaltu, Run, Smoczej Stali, Astralu, "
                "Pustki i Eternium."
            )
            await self.send(
                "U Haldora możesz też ulepszać każde armor EQ od +1 do +10. "
                "Ulepszenia zwiększają obronę, a co dwa poziomy także główną statystykę części. "
                "Kosztem są fragmenty odzyskiwane przez rozkładanie EQ; nie ma ryzyka zniszczenia."
            )
            await self.send(
                "Mistrz Rzemiosła Haldor daje powtarzalne "
                "zlecenia Kowalstwa/Rzemiosła. "
                "Każde odnawia się dokładnie co 60 minut."
            )

    async def show_cooking_info(self):
            await self.send("GOTOWANIE")
            row=self.server.db.profession(self.account_id,"Gotowanie")
            level=int(row["level"])
            maximum=profession_max_level("Gotowanie")
            await self.send(
                f"Gotowanie: poziom {level} z {maximum}. "
                f"Ranga {profession_rank(level,'Gotowanie')} z "
                f"{profession_max_rank('Gotowanie')}: "
                f"{profession_rank_name('Gotowanie',level)}. "
                f"XP: {self.profession_xp_status_text_v11343('Gotowanie')}. "
                f"Akcje: {int(row['actions'])}."
            )
            await self.show_single_tool("cooking")
            await self.send(
                "Gotowanie jest osobną profesją poziom 1-600. Jej poziom skraca czas przygotowania potraw i blokuje receptury; poziom Noża nie skraca czasu."
            )
            await self.send(
                "Gotować możesz w Karczmie Pod Błękitnym Płomieniem "
                "albo na Targu Rybnym."
            )
            await self.send(
                "Komendy: gotuj <potrawa>, receptury cook, gotowanie."
            )
            await self.send(
                "Niższe receptury prowadzą przez początek progresji, a pełny endgame Gotowania rozwija się aż do poziomu 600."
            )
            await self.send(
                "Wyższy Tier Noża może przygotować dodatkową porcję, ale nie skraca czasu. "
                "Gotowanie daje osobno XP profesji Gotowanie i XP Noża Kucharskiego."
            )

    def resolve_smelt_recipe(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            iron_scrap_aliases = {
                "odlamki zelaza", "odłamki żelaza", "odlamek zelaza", "odłamek żelaza",
                "zelazne odlamki", "żelazne odłamki", "iron scrap", "iron scraps",
                "iron fragment", "iron fragments",
            }
            if wanted in {self.normalize_description_query(x) for x in iron_scrap_aliases}:
                recipe = CRAFT_RECIPES.get("recycled_iron_ingot")
                if recipe:
                    return ("recycled_iron_ingot", recipe)

            plate_aliases = {
                "plyty", "płyty", "plyta", "płyta",
                "stalowe plyty", "stalowe płyty",
                "stalowa plyta", "stalowa płyta",
                "stalowa plyta z pancerza", "stalowa płyta z pancerza",
                "steel plate", "steel plates", "armor plate", "armor plates",
            }
            if wanted in {self.normalize_description_query(x) for x in plate_aliases}:
                recipe = CRAFT_RECIPES.get("recycled_steel_ingot")
                if recipe:
                    return ("recycled_steel_ingot", recipe)

            salvage_aliases_v03113 = {
                "recycled_steel_scrap_ingot_v03113": ("stal", "steel", "odlamki stali", "odłamki stali", "steel scrap", "steel scraps"),
                "recycled_cobalt_ingot_v03113": ("fragment kobaltu", "fragmenty kobaltu", "cobalt fragment", "cobalt fragments"),
                "recycled_runic_ingot_v03113": ("fragment runiczny", "fragmenty runiczne", "runic fragment", "runic fragments"),
                "recycled_dragonsteel_ingot_v03113": ("fragment smoczej stali", "fragmenty smoczej stali", "dragonsteel fragment", "dragonsteel fragments"),
                "recycled_astral_ingot_v03113": ("fragment astralny", "fragmenty astralne", "astral fragment", "astral fragments"),
                "recycled_void_ingot_v03113": ("fragment pustki", "fragmenty pustki", "void fragment", "void fragments"),
                "recycled_eternium_ingot_v03113": ("fragment eternium", "fragmenty eternium", "eternium fragment", "eternium fragments"),
            }
            for salvage_recipe_id, aliases in salvage_aliases_v03113.items():
                if wanted in {self.normalize_description_query(x) for x in aliases}:
                    recipe = CRAFT_RECIPES.get(salvage_recipe_id)
                    if recipe:
                        return (salvage_recipe_id, recipe)

            extra_aliases = {
                "iron": (
                    "zelazo", "żelazo", "zelazna", "żelazna",
                    "ruda zelaza", "ruda żelaza", "iron",
                ),
                "silver": (
                    "srebro", "srebrna", "ruda srebra", "silver",
                ),
                "gold": (
                    "zloto", "złoto", "zlota", "złota",
                    "ruda zlota", "ruda złota", "gold",
                ),
                "cobalt": (
                    "kobalt", "kobaltowa", "ruda kobaltu", "cobalt",
                ),
                "runic": (
                    "runa", "runiczna", "runiczny", "kamien runiczny",
                    "kamień runiczny", "runestone", "runic",
                ),
                "dragonsteel": (
                    "smocza stal", "smoczej stali", "dragonsteel",
                ),
                "astral": (
                    "astral", "astralna", "astralny",
                ),
                "void": (
                    "pustka", "pustki", "void",
                ),
                "eternium": (
                    "eternium",
                ),
            }

            exact = []
            partial = []

            for tier in BLACKSMITH_TIERS:
                recipe_id = tier["ingot"]
                recipe = CRAFT_RECIPES.get(recipe_id)
                if not recipe:
                    continue

                names = [
                    recipe_id,
                    recipe.get("name", ""),
                    tier["key"],
                    tier.get("name", ""),
                    tier["ore"],
                    ITEMS.get(tier["ore"], {}).get("name", ""),
                    ITEMS.get(recipe_id, {}).get("name", ""),
                ]
                names.extend(extra_aliases.get(tier["key"], ()))

                normalized = {
                    self.normalize_description_query(name)
                    for name in names
                    if name
                }

                if wanted in normalized:
                    exact.append((recipe_id, recipe))
                elif any(
                    wanted in name
                    for name in normalized
                ):
                    partial.append((recipe_id, recipe))

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None

    async def smelt_item(self, query):
            query = str(query or "").strip()

            if not query:
                await self.send(
                    "Użycie: przetop <metal albo ruda>. "
                    "Przykłady: przetop żelazo, przetop srebro, "
                    "przetop odłamki żelaza, przetop płyty, przetop kobalt, przetop Eternium."
                )
                return False

            found = self.resolve_smelt_recipe(query)
            if not found:
                await self.send(
                    "Nie rozpoznaję metalu do przetopienia. "
                    "Dostępne: żelazo, odłamki żelaza, srebro, złoto, stal, stalowe płyty, kobalt, "
                    "runa, smocza stal, astral, pustka, Eternium. "
                    "Jeśli zabraknie rudy, przetop automatycznie sprawdzi Szkatułkę -> Salvage."
                )
                return False

            recipe_id, recipe = found

            # v0.31.13: dla zwykłego `przetop <metal>` najpierw używamy
            # świeżej rudy. Jeśli jej brakuje, automatycznie próbujemy
            # odpowiedniego materiału ze Szkatułki -> Salvage.
            enough_primary = all(
                self.available_recipe_item(item_id) >= int(quantity)
                for item_id, quantity in recipe.get("ingredients", {}).items()
            )
            if not enough_primary:
                fallback_id = SALVAGE_SMELT_FALLBACK_V03113.get(recipe.get("output"))
                fallback = CRAFT_RECIPES.get(fallback_id) if fallback_id else None
                if fallback and all(
                    self.available_recipe_item(item_id) >= int(quantity)
                    for item_id, quantity in fallback.get("ingredients", {}).items()
                ):
                    await self.send(
                        "Brakuje zwykłej rudy. Pobieram materiał odzyskany przez "
                        "Salvage ze Szkatułki Rzemieślniczej."
                    )
                    recipe_id, recipe = fallback_id, fallback

            return await self.perform_recipe(
                recipe["name"],
                CRAFT_RECIPES,
                "przetapianie",
            )

    async def craft_item(self, query):
            return await self.perform_recipe(query, CRAFT_RECIPES, "rzemiosło")

    async def jewelcraft_item(self, query):
            return await self.perform_recipe(
                query,
                JEWELCRAFT_RECIPES,
                "jubilerstwo",
            )

    async def cook_item(self, query):
            return await self.perform_recipe(query, COOK_RECIPES, "gotowanie")

    async def alchemy_item(self, query):
            return await self.perform_recipe(query, ALCHEMY_RECIPES, "alchemia")

    async def handle_custom_activities_v3500(self, query=''):
        from systems.live_olc35_finale import ACTIVE
        activities=ACTIVE['activities']
        name=str(query or '').strip()
        if not name or name.casefold() in ('lista','list','info'):
            await self.send(f'CZYNNOŚCI OLC35: {len(activities)} dostępnych. Użyj: czynnosci live_ID.')
            for key,row in sorted(activities.items()):
                await self.send(f'{key}: {row["name"]} (receptura {row["recipe"]}).')
            return
        activity=activities.get(name)
        if activity is None:
            await self.send('Nie ma takiej czynności. Użyj: czynnosci lista.')
            return
        from data.crafting_recipes import CRAFT_RECIPES
        rid=activity['recipe']
        recipe=CRAFT_RECIPES.get(rid)
        if recipe is None:
            await self.send('Receptura nie jest dostępna. Zgłoś to administratorowi.')
            return
        return await self.perform_recipe(rid,{rid:recipe},activity['name'])
