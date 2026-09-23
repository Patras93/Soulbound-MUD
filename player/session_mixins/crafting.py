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

            if not mode:
                show_craft = show_cook = show_alchemy = show_jewel = True
            elif mode in craft_modes:
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
                show_craft = show_cook = show_alchemy = show_jewel = True

            if show_craft:
                await self.send("RECEPTURY RZEMIOSŁA I KOWALSTWA")
                for recipe in CRAFT_RECIPES.values():
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
                }
                tool_type = str(recipe["tool_type"])
                item_id, name = mapping[tool_type]
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
                return False

            action_seconds = self.recipe_action_seconds(
                tool_type, profession_level, recipe
            )
            await self.send(
                f"Rozpoczynasz {action_name}. "
                f"{self.tool_action_label(tool_type)}: "
                f"{action_seconds} sekund."
            )
            await asyncio.sleep(action_seconds)

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
            quality_key = crafting_quality_roll_v03054(
                profession_level, old_tool_level, mastery_before
            )
            critical_chance = crafting_critical_chance_v03054(
                profession_level, mastery_before
            )
            critical_craft = random.random() < critical_chance
            crafted_output_id, critical_affix = crafting_quality_output_v03054(
                output_id, quality_key, critical_craft, mastery_before
            )

            tier = tool_tier(old_tool_level)
            bonus_chance = tool_tier_bonus_chance(old_tool_level)

            bonus_quantity = 0
            if bonus_chance > 0 and random.random() < bonus_chance:
                bonus_quantity = quantity

            total_quantity = quantity + bonus_quantity
            self.server.db.add_item(
                self.account_id, crafted_output_id, total_quantity
            )
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

            tool_xp = (
                roll_crafting_xp(recipe["tool_xp"])
                if "tool_xp" in recipe
                else 8 + random.randint(0, 4)
            )
            profession_xp = (
                roll_crafting_xp(recipe["profession_xp"])
                if "profession_xp" in recipe
                else 10 + random.randint(0, 5)
            )
            messages, _profession_level_after, new_tool_level = self.grant_profession_progress(
                profession, profession_xp, tool_type, tool_xp
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
            await self.send(
                "Narzędzie: Szczypce Jubilerskie, poziom 1-600 i 60 Tierów. "
                "Kupisz je wyłącznie u Jubilerki Mirelli w Pracowni Jubilerskiej."
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
                "Komendy: kowalstwo, przetop <metal>, "
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
