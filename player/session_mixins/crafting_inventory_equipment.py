# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: crafting_inventory_equipment."""

class SessionCraftingInventoryEquipmentMixin:
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
                f"Wymaga: {profession} level {required} oraz "
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
                    f"{recipe['name']} wymaga {profession} level "
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
                    f"{tool_name} ma teraz level {new_tool_level}, "
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
                f"Level {level} z {max_level}. "
                f"Ranga {rank} z {profession_max_rank('Jubilerstwo')}: "
                f"{profession_rank_name('Jubilerstwo', level)}. "
                f"XP: {xp_text}. Akcje: {row['actions']}."
            )
            await self.send(
                "Narzędzie: Szczypce Jubilerskie, level 1-400 i 40 Tierów. "
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
                f"Kowalstwo: level {level} z "
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
                "Gotowanie jest osobną profesją level 1-400. Jej poziom skraca czas przygotowania potraw i blokuje receptury; level Noża nie skraca czasu."
            )
            await self.send(
                "Gotować możesz w Karczmie Pod Błękitnym Płomieniem "
                "albo na Targu Rybnym."
            )
            await self.send(
                "Komendy: gotuj <potrawa>, receptury cook, gotowanie."
            )
            await self.send(
                "Niższe receptury prowadzą przez początek progresji, a pełny endgame Gotowania rozwija się aż do poziomu 400."
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

    def equipped_quantity_of_item(self, item_id):
            return sum(
                1 for row in self.server.db.equipment(self.account_id)
                if row["item_id"] == item_id
            )

    def free_equipment_quantity(self, item_id):
            return max(
                0,
                self.server.db.item_qty(self.account_id, item_id)
                - self.equipped_quantity_of_item(item_id),
            )

    def resolve_transferable_equipment(self, query):
            transferable = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    item.get("type") == "armor"
                    and not is_character_bound_item(item_id)
                    and self.free_equipment_quantity(item_id) > 0
                )
            }
            return find_by_name(transferable, query)

    def free_transferable_quantity(self, item_id):
            total = self.server.db.item_qty(self.account_id, item_id)
            item = ITEMS.get(item_id, {})
            if item.get("type") == "armor":
                total -= self.equipped_quantity_of_item(item_id)
            return max(0, int(total))

    def resolve_transferable_inventory_item(self, query):
            transferable = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    self.free_transferable_quantity(item_id) > 0
                    and not is_character_bound_item(item_id)
                    and item.get("type") != "quest"
                )
            }
            return find_by_name(transferable, query)

    def parse_player_currency_transfer(self, payload):
            """Zwraca (amount_silver, opis) lub None, gdy payload nie jest walutą."""
            words = str(payload or "").strip().split()
            if len(words) < 2:
                return None
            amount = None
            unit = None
            if words[0].isdigit():
                amount = int(words[0])
                unit = " ".join(words[1:])
            elif words[-1].isdigit():
                amount = int(words[-1])
                unit = " ".join(words[:-1])
            else:
                return None
            multiplier = currency_unit_multiplier(unit)
            if multiplier is None:
                return None
            if amount <= 0:
                return (0, "")
            total = amount * int(multiplier)
            if total > CURRENCY_SQLITE_SAFE_TOTAL:
                return (CURRENCY_SQLITE_SAFE_TOTAL + 1, "")
            return total, currency_reading_text(total, 0, 0, full_names=True)

    async def give_player(self, raw):
            """Przekazuje walutę albo zwykły przedmiot graczowi stojącemu obok."""
            text = str(raw or "").strip()
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await self.send(
                    "Użycie: daj <gracz> <przedmiot>; daj <gracz> <ilość> <przedmiot>; "
                    "daj <gracz> <ilość> złota."
                )
                return

            target_name, payload = parts[0].strip(), parts[1].strip()
            target = self.server.find_character_session(target_name)
            if target is None or target.closed or not target.character:
                await self.send(f"Gracz {target_name} nie jest teraz online.")
                return
            if target is self or target.account_id == self.account_id:
                await self.send("Nie możesz przekazać przedmiotu ani waluty samemu sobie.")
                return
            if target.character.room_id != self.character.room_id:
                await self.send(
                    f"{target.character.name} nie znajduje się w tej samej lokacji. "
                    "Przekazywanie działa tylko między graczami stojącymi obok."
                )
                return

            currency = self.parse_player_currency_transfer(payload)
            if currency is not None:
                amount_silver, description = currency
                if amount_silver <= 0:
                    await self.send("Kwota musi być większa od zera.")
                    return
                if amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
                    await self.send("Ta kwota jest zbyt duża.")
                    return
                sender_total = int(self.server.db.shared_wallet_for_character(self.account_id)[0])
                if sender_total < amount_silver:
                    await self.send(
                        "Nie masz wystarczającej ilości waluty. Masz: "
                        + currency_reading_text(sender_total, 0, 0, full_names=True)
                        + "."
                    )
                    return
                if not self.server.db.transfer_shared_currency(
                    self.account_id, target.account_id, amount_silver
                ):
                    await self.send("Nie udało się przekazać waluty. Nic nie zostało zmienione.")
                    return
                self.server.db.apply_shared_wallet_to_character(self.character)
                self.server.db.apply_shared_wallet_to_character(target.character)
                await self.send(
                    f"Przekazujesz graczowi {target.character.name}: {description}.",
                    history_category="system",
                )
                await target.send(
                    f"{self.character.name} przekazuje ci: {description}.",
                    history_category="system",
                )
                return

            qty = 1
            item_query = payload
            item_parts = payload.split(maxsplit=1)
            if item_parts and item_parts[0].isdigit():
                qty = int(item_parts[0])
                item_query = item_parts[1].strip() if len(item_parts) > 1 else ""
            if qty <= 0 or not item_query:
                await self.send("Ilość przedmiotów musi być dodatnia i trzeba podać nazwę przedmiotu.")
                return

            found = self.resolve_transferable_inventory_item(item_query)
            if not found:
                owned = {
                    item_id: item
                    for item_id, item in ITEMS.items()
                    if self.server.db.item_qty(self.account_id, item_id) > 0
                }
                owned_found = find_by_name(owned, item_query)
                if owned_found:
                    item_id, item = owned_found
                    if is_character_bound_item(item_id):
                        await self.send(
                            f"{item['name']} jest przypisany do postaci i nie może być przekazany."
                        )
                    elif item.get("type") == "quest":
                        await self.send(
                            f"{item['name']} jest przedmiotem questowym i nie może być przekazany."
                        )
                    elif self.free_transferable_quantity(item_id) <= 0:
                        await self.send(
                            f"{item['name']} jest założony. Najpierw zdejmij wolną sztukę z EQ."
                        )
                    else:
                        await self.send("Tego przedmiotu nie można teraz przekazać.")
                else:
                    await self.send(
                        "Nie rozpoznaję takiego przedmiotu w twoim inventory. "
                        "Podaj pełną nazwę; ilość wpisz przed nazwą, np. daj Arven 3 Mikstura Leczenia."
                    )
                return

            item_id, item = found
            free_qty = self.free_transferable_quantity(item_id)
            if free_qty < qty:
                await self.send(
                    f"Masz tylko {free_qty} wolnych sztuk: {item['name']}."
                )
                return

            if not self.server.db.transfer_inventory_item(
                self.account_id, target.account_id, item_id, qty
            ):
                await self.send("Nie udało się przekazać przedmiotu. Nic nie zostało zmienione.")
                return

            # Zachowaj istniejące dane reforgingu/run tylko wtedy, gdy ostatnia
            # sztuka konkretnego EQ opuszcza konto nadawcy.
            if (
                item.get("type") == "armor"
                and self.server.db.item_qty(self.account_id, item_id) <= 0
            ):
                self.server.db.transfer_equipment_crafting_v0925(
                    self.account_id, target.account_id, item_id
                )

            quantity_text = f"{qty} x " if qty != 1 else ""
            await self.send(
                f"Przekazujesz graczowi {target.character.name}: {quantity_text}{item['name']}.",
                history_category="system",
            )
            await target.send(
                f"{self.character.name} przekazuje ci: {quantity_text}{item['name']}.",
                history_category="system",
            )

    async def give_equipment(self, raw):
            # Zgodność wsteczna z dawną nazwą handlera v0.9.17.
            await self.give_player(raw)

    async def inventory(self):
            rows = self.server.db.inventory(self.account_id)
            await self.send(
                "Waluta: "
                + currency_reading_text(
                    self.character.silver, self.character.gold, self.character.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(
                "Siatka na ryby, Sakwa górnicza, Stos drewna, Torba Zielarska "
                "i Szkatułka Rzemieślnicza są osobnymi magazynami; użyj siatka/net, "
                "sakwa/bag, drewno/stos, ziola/herbs oraz szkatułka/craftbox."
            )
            if not rows:
                await self.send("Ekwipunek jest pusty.")
                return
            await self.send("Ekwipunek:")
            for row in rows:
                item = ITEMS.get(row["item_id"], {"name": row["item_id"], "desc": ""})
                bound_text = (
                    " Przypisany do postaci; nie można oddać ani wyrzucić."
                    if is_character_bound_item(row["item_id"])
                    else ""
                )
                await self.send(
                    f"{item['name']} x{row['quantity']}. "
                    f"{item.get('desc','')}{bound_text}"
                )

    async def equipment(self, mode=""):
            mode = self.normalize_description_query(mode)
            if mode in ("auto", "automatycznie", "najlepsze", "best"):
                await self.auto_equip_best_v03040()
                return
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            rows = self.server.db.equipment(self.account_id)

            await self.send("EQ INFO" if detailed else "EQ")
            c = self.character
            soul_line = (
                f"Broń Duszy: {c.soul_weapon}. "
                f"Soul Level {c.soul_level}/{SOUL_MAX_LEVEL}. "
                f"Soul Tier {c.soul_tier}/{SOUL_MAX_TIER}. "
                f"Moc {c.soul_power()}."
            )
            if detailed:
                if c.soul_level < SOUL_MAX_LEVEL:
                    soul_line += f" Soul XP {c.soul_xp} z {c.soul_xp_to_next()}."
                else:
                    soul_line += " Soul XP maksimum."
                soul_line += f" Bonus klasowy: {c.soul_weapon_class_bonus_text()}."
            await self.send(soul_line)

            if not rows:
                await self.send("Nie masz założonego dodatkowego wyposażenia.")
        
            slot_names = {
                "head": "Głowa", "body": "Korpus", "hands": "Dłonie",
                "legs": "Nogi", "feet": "Stopy", "charm": "Talizman",
                "charm1": "Talizman 1", "charm2": "Talizman 2",
                "ring": "Pierścień", "ring1": "Pierścień 1",
                "ring2": "Pierścień 2", "necklace": "Naszyjnik",
                "earring1": "Kolczyk 1", "earring2": "Kolczyk 2",
                "shoulders": "Naramienniki", "belt": "Pas", "cloak": "Peleryna",
                "bracers": "Karwasze", "relic": "Relikt", "board": "Board",
            }
            for row in rows:
                item = ITEMS.get(row["item_id"])
                upgrade_level = self.server.db.equipment_upgrade_level_v03042(
                    self.account_id, row["item_id"]
                ) if item else 0
                base_name = item["name"] if item else row["item_id"]
                name = v03042_upgraded_display_name(base_name, upgrade_level)
                defense = (
                    int(item.get("defense", 0) or 0)
                    + v03042_upgrade_defense_bonus(item, upgrade_level)
                    if item else 0
                )
                slot_name = slot_names.get(row["slot"], row["slot"])
                if not detailed:
                    socket_short = ""
                    if item and item.get("slot") in ("ring", "necklace"):
                        capacity = jewelry_socket_capacity(item)
                        occupied = len(self.socketed_gem_rows_for_item(row["slot"], row["item_id"]))
                        socket_short = f" Gniazda {occupied}/{capacity}."
                    await self.send(f"{slot_name}: {name}. Obrona +{defense}.{socket_short}")
                    continue

                extra = ""
                if item and upgrade_level > 0:
                    upgrade_stat = v03042_upgrade_primary_stat(
                        item,
                        str((self.server.db.equipment_reforge(self.account_id, row["item_id"]) or {}).get("affix") or item.get("affix") or ""),
                    )
                    upgrade_amount = v03042_upgrade_stat_bonus(upgrade_level)
                    stat_label = CLASS_SET_STAT_NAMES.get(upgrade_stat, upgrade_stat)
                    extra += (
                        f" Ulepszenie Kowalstwa +{upgrade_level}/{V03042_EQ_UPGRADE_MAX}: "
                        f"obrona po ulepszeniu +{defense}"
                        + (f", {stat_label} +{upgrade_amount}." if upgrade_amount > 0 else ".")
                    )
                if item and item.get("rarity_name"):
                    extra += f" Rzadkość: {item['rarity_name']}."
                if item and item.get("affix"):
                    affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
                    extra += f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
                if item and item.get("stats"):
                    fixed_stats = ", ".join(
                        f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                        for stat, amount in item.get("stats", {}).items()
                        if int(amount or 0) != 0
                    )
                    if fixed_stats:
                        extra += f" Statystyki bazowe: {fixed_stats}."
                if row["item_id"] == "moogle_board" and item and item.get("cyborg_board_scaling") == "mec_mastery":
                    _mb = moogle_board_stat_bonus_v0313(self.class_mastery_level("Mec"))
                    extra += f" Skalowanie Moogle Board: Biegłość Meca {self.class_mastery_level('Mec')}/400, +{_mb} do Siły, Zręczności, Kondycji, Inteligencji i Siły Woli."
                if item and item.get("slot") in ("ring", "necklace"):
                    extra += " " + self.jewelry_socket_text(row["slot"], row["item_id"], item)
                await self.send(f"{slot_name}: {name}. Obrona +{defense}.{extra}")

            if not detailed:
                await self.send(
                    f"Łączna obrona fizyczna: {self.defense()}. Wpisz eq info po bonusy, sety i sockety."
                )
                return

            bonuses = self.equipment_bonus_totals()
            await self.send(
                f"Łączna obrona fizyczna: {self.defense()}. Obrona magiczna: {self.magic_defense()}."
            )
            await self.send(
                "Łączne bonusy EQ i socketów: "
                f"Siła +{bonuses['strength']}, Zręczność +{bonuses['dexterity']}, "
                f"Kondycja +{bonuses['constitution']}, Inteligencja +{bonuses['intelligence']}, "
                f"Siła Woli +{bonuses['willpower']}, HP +{bonuses['hp']}, Mana +{bonuses['mana']}."
            )
            await self.send(
                f"Efektywne staty: Siła {self.effective_strength()}, Zręczność {self.effective_dexterity()}, "
                f"Kondycja {self.effective_constitution()}, Inteligencja {self.effective_intelligence()}, "
                f"Siła Woli {self.effective_willpower()}."
            )
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())
            for line in self.class_set_status_lines():
                await self.send(line)
            for line in self.regional_set_status_lines():
                await self.send(line)
            await self.send("Regionalne sety mają progi 2/4/6. Komenda sety pokazuje progi 2/4/6/8 wszystkich zestawów klasowych.")
            await self.send("Komenda gniazda pokazuje dokładnie osadzone klejnoty w biżuterii.")

    async def show_class_sets(self, query=""):
            q = self.normalize_description_query(query)
            counts = self.class_set_counts()

            if q in ("", "aktywne", "active"):
                await self.send("SETY KLASOWE")
                any_set = False
                for class_name in self.active_class_names():
                    count = int(counts.get(class_name, 0))
                    if count <= 0:
                        continue
                    any_set = True
                    await self.send(
                        f"{class_name}: {count}/14 części. Bonusy kończą się na progu 8. "
                        f"{self.class_set_threshold_text(class_name)}."
                    )
                if not any_set:
                    await self.send("Nie masz założonej części aktywnego setu klasowego.")
                await self.send(
                    "Wpisz sety info po wszystkie 12 zestawów albo sety <klasa>."
                )
                return

            if q in ("info", "wszystkie", "all", "pelne", "pełne"):
                await self.send("SETY KLASOWE 2/4/6/8 - WSZYSTKIE KLASY")
                for class_name in CLASS_EQUIPMENT_SETS:
                    set_name = CLASS_EQUIPMENT_SETS[class_name]["set_name"]
                    await self.send(
                        f"{class_name}, Zestaw {set_name}. "
                        f"{self.class_set_threshold_text(class_name)}."
                    )
                return

            found = None
            for class_name in CLASS_EQUIPMENT_SETS:
                if q == self.normalize_description_query(class_name):
                    found = class_name
                    break
            if not found:
                await self.send(
                    "Nie rozpoznaję klasy. Wpisz sety info po listę wszystkich 12 zestawów."
                )
                return

            set_name = CLASS_EQUIPMENT_SETS[found]["set_name"]
            count = int(counts.get(found, 0))
            await self.send(
                f"SET {found}: Zestaw {set_name}. Masz założone {count}/14 części; bonusy aktywują się na 2/4/6/8."
            )
            await self.send(self.class_set_threshold_text(found) + ".")
            await self.send(
                "Czternaście logicznych części to: głowa, korpus, dłonie, nogi, stopy, talizman, "
                "pierścień, naszyjnik, kolczyki, naramienniki, pas, peleryna, karwasze i relikt. "
                "Drugi taki sam talizman, pierścień ani kolczyk nie zwiększa licznika setu."
            )

    def equipment_item_score(self, item):
            if not item:
                return (-1, -1, -1, "")
            rarity_order = {
                "common": 0,
                "crafted": 1,
                "rare": 2,
                "epic": 3,
                "legendary": 4,
                "mythic": 5,
                "unique": 6,
                "eternal": 7,
            }
            stat_power = int(item.get("affix_amount", 0) or 0) + sum(
                max(0, int(v or 0)) for v in (item.get("stats") or {}).values()
            )
            return (
                int(item.get("defense", 0) or 0),
                rarity_order.get(item.get("rarity"), 0),
                stat_power,
                normalize_lookup_text(item.get("name", "")),
            )

    def auto_equipment_score_v03040(self, item, item_id=None):
            """Porównanie indywidualnej mocy EQ dla opcjonalnego trybu auto.

            Nie zmienia balansu przedmiotów. Uwzględnia obronę, bazowe staty,
            właściwości procentowe, affix, rarity oraz pojemność gniazd biżuterii.
            """
            if not item or item.get("type") != "armor":
                return (-1, -1, -1, -1, -1, "")
            rarity_order = {
                "common": 0, "crafted": 1, "uncommon": 1, "rare": 2,
                "epic": 3, "legendary": 4, "mythic": 5, "unique": 6,
                "eternal": 7,
            }
            upgrade_level = (
                self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id)
                if item_id else 0
            )
            defense = max(0, int(item.get("defense", 0) or 0)) + v03042_upgrade_defense_bonus(item, upgrade_level)
            stats = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
            stats += v03042_upgrade_stat_bonus(upgrade_level)
            props = sum(max(0, int(v or 0)) for v in (item.get("properties") or {}).values())
            affix = max(0, int(item.get("affix_amount", 0) or 0))
            rarity = rarity_order.get(str(item.get("rarity") or "").lower(), 0)
            sockets = 0
            if item.get("slot") in ("ring", "earring", "necklace"):
                try:
                    sockets = max(0, int(jewelry_socket_capacity(item)))
                except Exception:
                    sockets = 0
            total = defense * 12 + stats * 8 + props * 10 + affix * 8 + rarity * 5 + sockets * 3
            return (
                total, defense, stats + affix, props, rarity,
                normalize_lookup_text(item.get("name", "")),
            )

    def auto_equipment_eligible_v03040(self, item):
            if not item or item.get("type") != "armor":
                return False
            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                return False
            if not self.equipment_mastery_requirement_met(item):
                return False
            return True

    async def auto_equip_best_v03040(self):
            """Jednym poleceniem zakłada indywidualnie najmocniejsze dostępne EQ.

            Działa wyłącznie na posiadanych i aktualnie dozwolonych przedmiotach.
            Podwójne sloty respektują faktyczną liczbę posiadanych kopii.
            """
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz automatycznie zmieniać EQ podczas aktywnej walki. "
                    "Najpierw zakończ walkę albo użyj flee."
                )
                return

            active_classes = set(self.active_class_names())
            owned = {}
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                qty = int(self.server.db.item_qty(self.account_id, item_id) or 0)
                if qty <= 0:
                    continue
                required_class = item.get("required_class")
                if required_class and required_class not in active_classes:
                    continue
                required_race = item.get("required_race")
                if required_race and str(self.character.race) != str(required_race):
                    continue
                if not self.equipment_mastery_requirement_met(item):
                    continue
                owned[item_id] = (item, qty)

            if not owned:
                await self.send("AUTO EQ: nie masz żadnego dostępnego EQ do założenia.")
                return

            changes = []
            returned_gems = []
            single_slots = (
                "head", "body", "hands", "legs", "feet", "necklace",
                "shoulders", "belt", "cloak", "bracers", "relic", "board",
            )

            for slot in single_slots:
                candidates = [
                    (self.auto_equipment_score_v03040(item, item_id), item_id, item)
                    for item_id, (item, qty) in owned.items()
                    if qty > 0 and item.get("slot") == slot
                ]
                if not candidates:
                    continue
                candidates.sort(key=lambda row: row[0], reverse=True)
                _score, best_id, best_item = candidates[0]
                old_id = self.server.db.equipped_item(self.account_id, slot)
                old_item = ITEMS.get(old_id) if old_id else None
                if old_id == best_id:
                    continue
                if old_item and self.auto_equipment_score_v03040(old_item, old_id) >= self.auto_equipment_score_v03040(best_item, best_id):
                    continue
                if slot == "necklace" and old_id:
                    returned_gems.extend(await self.return_socketed_gems(slot, old_id))
                self.server.db.equip(self.account_id, slot, best_id)
                changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", best_item.get("name", best_id)))

            duals = {
                "ring": ("ring1", "ring2"),
                "charm": ("charm1", "charm2"),
                "earring": ("earring1", "earring2"),
            }
            for logical_slot, pair in duals.items():
                expanded = []
                for item_id, (item, qty) in owned.items():
                    if item.get("slot") != logical_slot:
                        continue
                    for _ in range(min(2, max(0, int(qty)))):
                        expanded.append((self.auto_equipment_score_v03040(item, item_id), item_id, item))
                if not expanded:
                    continue
                expanded.sort(key=lambda row: row[0], reverse=True)
                selected = expanded[:2]

                # Zachowaj obecne pozycje, jeśli dana sztuka nadal należy do najlepszej dwójki.
                remaining = {}
                selected_rows = {}
                for score, item_id, item in selected:
                    remaining[item_id] = remaining.get(item_id, 0) + 1
                    selected_rows.setdefault(item_id, (score, item))
                desired = {}
                for slot in pair:
                    cur = self.server.db.equipped_item(self.account_id, slot)
                    if cur and remaining.get(cur, 0) > 0:
                        desired[slot] = cur
                        remaining[cur] -= 1
                rest = []
                for score, item_id, item in selected:
                    if remaining.get(item_id, 0) > 0:
                        rest.append((score, item_id, item))
                        remaining[item_id] -= 1
                for slot in pair:
                    if slot not in desired and rest:
                        _score, item_id, _item = rest.pop(0)
                        desired[slot] = item_id

                for slot in pair:
                    target_id = desired.get(slot)
                    if not target_id:
                        continue
                    old_id = self.server.db.equipped_item(self.account_id, slot)
                    if old_id == target_id:
                        continue
                    target_item = ITEMS[target_id]
                    old_item = ITEMS.get(old_id) if old_id else None
                    # Gdy slot nie należy do docelowej najlepszej dwójki, wymiana jest bezpieczna.
                    if logical_slot in ("ring", "earring") and old_id:
                        returned_gems.extend(await self.return_socketed_gems(slot, old_id))
                    self.server.db.equip(self.account_id, slot, target_id)
                    changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", target_item.get("name", target_id)))

            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())

            if not changes:
                await self.send("AUTO EQ: masz już najmocniejsze dostępne indywidualne części według statystyk EQ.")
                return

            await self.send(f"AUTO EQ: zmieniono {len(changes)} slotów.")
            for slot, old_name, new_name in changes:
                await self.send(
                    f"{EQUIPMENT_SLOT_NAMES.get(slot, slot)}: {old_name} -> {new_name}."
                )
            if returned_gems:
                await self.send(
                    f"Z wymienionej biżuterii zwrócono {len(returned_gems)} klejnotów do Szkatułki Rzemieślniczej."
                )
            await self.send(
                "Auto EQ porównuje indywidualną moc części: obronę, statystyki, właściwości, affix, rarity i gniazda. "
                "Nie zmienia przedmiotów niedostępnych przez Level postaci lub klasę."
            )

    def owned_armor_for_slot(self, slot):
            candidates = []
            if slot in ("ring1", "ring2"):
                logical_slot = "ring"
            elif slot in ("charm1", "charm2"):
                logical_slot = "charm"
            elif slot in ("earring1", "earring2"):
                logical_slot = "earring"
            else:
                logical_slot = slot
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                if item.get("slot") != logical_slot:
                    continue
                # Lista wyboru pokazuje wszystkie posiadane części tego slotu,
                # również te jeszcze zablokowane Biegłością/klasą. Dzięki temu
                # komenda slotowa nigdy nie "wybiera za gracza" tylko dlatego,
                # że część posiadanych opcji jest chwilowo niedostępna. Walidacja
                # klasy i Biegłości następuje dopiero po podaniu konkretnej nazwy.
                quantity = self.server.db.item_qty(
                    self.account_id, item_id
                )
                if quantity <= 0:
                    continue

                score = self.equipment_item_score(item)
                candidates.append((score, item_id, item))

            candidates.sort(key=lambda entry: entry[0], reverse=True)
            return candidates

    def resolve_equipment_for_equip(self, query):
            """Resolve only an explicitly selected item.

            v0.9.16 deliberately does not pick the strongest item for the player.
            Slot-only commands are handled in equip_item so they can list choices.
            """
            owned_armor = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    item.get("type") == "armor"
                    and self.server.db.item_qty(self.account_id, item_id) > 0
                )
            }
            return find_by_name(owned_armor, query)

    def explicit_dual_slot_and_item_query(self, query):
            """Return (slot, remaining item query) for numbered ring/charm/earring syntax.

            Accepted examples:
            - załóż pierścień 1 <nazwa>
            - załóż <nazwa> pierścień 1
            - equip ring2 <name>
            - equip <name> charm1
            """
            raw = str(query or "").strip()
            normalized = self.normalize_description_query(raw)
            aliases = (
                ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
                ("ring 1", "ring1"), ("ring1", "ring1"),
                ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
                ("ring 2", "ring2"), ("ring2", "ring2"),
                ("talizman 1", "charm1"), ("charm 1", "charm1"), ("charm1", "charm1"),
                ("talizman 2", "charm2"), ("charm 2", "charm2"), ("charm2", "charm2"),
                ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
                ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
            )
            for alias, slot in aliases:
                alias_norm = self.normalize_description_query(alias)
                prefix = alias_norm + " "
                suffix = " " + alias_norm
                if normalized.startswith(prefix):
                    # Slice by words rather than normalized character count so Polish diacritics are safe.
                    alias_words = len(alias.split())
                    rest = " ".join(raw.split()[alias_words:]).strip()
                    return slot, rest
                if normalized.endswith(suffix):
                    alias_words = len(alias.split())
                    rest = " ".join(raw.split()[:-alias_words]).strip()
                    return slot, rest
            return None, raw

    def equipment_choices_text(self, candidates):
            names = []
            seen = set()
            for _score, _item_id, item in candidates:
                name = item.get("name", "")
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
            return ", ".join(names)

    def equipped_jewelry(self, slot):
            if slot in ("ring", "earring"):
                pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
                slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]
            valid = ("ring1", "ring2", "earring1", "earring2", "necklace")
            if slot not in valid:
                return None, None
            item_id = self.server.db.equipped_item(self.account_id, slot)
            item = ITEMS.get(item_id) if item_id else None
            if slot in ("ring1", "ring2"):
                logical = "ring"
            elif slot in ("earring1", "earring2"):
                logical = "earring"
            else:
                logical = slot
            if not item or item.get("slot") != logical:
                return None, None
            return item_id, item

    def socketed_gem_rows_for_item(self, slot, item_id):
            return list(
                self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                    item_id,
                )
            )

    def jewelry_socket_text(self, slot, item_id, item):
            capacity = jewelry_socket_capacity(item)
            if capacity <= 0:
                return "Brak gniazd."

            rows = self.socketed_gem_rows_for_item(
                slot,
                item_id,
            )
            if not rows:
                return f"Gniazda: 0 z {capacity} zajętych."

            names = [
                ITEMS.get(row["gem_id"], {"name": row["gem_id"]})["name"]
                for row in rows
            ]
            return (
                f"Gniazda: {len(rows)} z {capacity} zajętych. "
                f"Klejnoty: {', '.join(names)}."
            )

    async def return_socketed_gems(self, slot, item_id=None):
            rows = list(
                self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                    item_id,
                )
                if item_id
                else self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                )
            )
            if not rows:
                return []

            self.server.db.clear_socketed_gems(
                self.account_id,
                slot,
            )
            returned = []
            for row in rows:
                gem_id = row["gem_id"]
                if gem_id in ITEMS:
                    self.server.db.add_item(
                        self.account_id,
                        gem_id,
                        1,
                    )
                    returned.append(gem_id)
            return returned

    async def show_geodes(self):
            await self.send("GEODY")
            rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
            total = 0
            for geode_id, cfg in GEODE_DEFINITIONS.items():
                qty = rows.get(geode_id, 0)
                total += qty
                await self.send(
                    f"{cfg['name']}: {qty}. Kilof {cfg['min_tool']}+, głębokość {cfg['min_floor']}+."
                )
            if total:
                await self.send("Otwieranie: open geode / otwórz geodę. Możesz też podać nazwę, np. otwórz geodę kryształową.")
            else:
                await self.send("Nie masz obecnie geod w Sakwie Górnika.")

    def _find_owned_geode(self, query=""):
            rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
            owned = {gid: ITEMS[gid] for gid in GEODE_IDS if rows.get(gid, 0) > 0}
            if not owned:
                return None
            q = self.normalize_description_query(str(query or "").strip())
            for token in ("geoda", "geode", "geodę", "geodee"):
                q = q.replace(token, " ").strip()
            if q:
                found = find_by_name(owned, q)
                if found:
                    return found[0]
            # Bez nazwy otwieramy najlepszą posiadaną geodę.
            priority = ("astral_geode", "crystal_geode", "stone_geode")
            return next((gid for gid in priority if gid in owned), None)

    async def open_geode(self, query=""):
            geode_id = self._find_owned_geode(query)
            if not geode_id:
                await self.send("Nie masz takiej geody w Sakwie Górnika. Wpisz geody / geodes.")
                return False
            if not self.server.db.remove_storage_item(self.account_id, "bag", geode_id, 1):
                await self.send("Nie udało się pobrać geody z Sakwy Górnika.")
                return False
            cfg = GEODE_DEFINITIONS[geode_id]
            eligible = [d for d in GEM_DEFINITIONS if int(d["level"]) <= int(cfg["max_gem_level"])]
            weights = list(range(len(eligible), 0, -1))
            low_qty, high_qty = cfg["gem_qty"]
            quantity = random.randint(int(low_qty), int(high_qty))
            rewards = []
            for _ in range(quantity):
                definition = random.choices(eligible, weights=weights, k=1)[0]
                quality = random.choices(GEM_QUALITY_ORDER, weights=cfg["quality_weights"], k=1)[0]
                gem_id = gem_quality_item_id("raw", definition["key"], quality)
                self.store_profession_resource(gem_id, 1)
                await self.record_item_collection(
                    gem_id, source=cfg["name"], announce=True, record_history=False
                )
                rewards.append(ITEMS[gem_id]["name"])
            gold_low, gold_high = cfg["gold"]
            gold = random.randint(int(gold_low), int(gold_high))
            if gold > 0:
                self.character.gold += gold
            shard = False
            if geode_id == "astral_geode" and random.random() < 0.08:
                self.server.db.add_item(self.account_id, "soul_shard", 1)
                shard = True
            self.server.db.save_character(self.character)
            await self.send(f"Otwierasz {cfg['name']}. Klejnoty: " + ", ".join(rewards) + ".")
            if gold > 0:
                await self.send("W geodzie znajdujesz także " + currency_reading_text(0, gold, 0) + ".")
            if shard:
                await self.send("Rzadkie znalezisko: Odłamek Duszy x1.")
            return True

    async def show_gems(self):
            await self.send("KAMIENIE SZLACHETNE")
            await self.send(
                "Surowe kamienie wypadają dodatkowo podczas Górnictwa i trafiają do Sakwy Górnika. "
                "Po oszlifowaniu stają się materiałem jubilerskim i automatycznie trafiają do Szkatułki Rzemieślniczej."
            )
            await self.send(
                "Jakości: Surowy, Czysty, Doskonały, Perfekcyjny. Lepszy Kilof i wyższe Górnictwo "
                "zwiększają szansę jakości; Perfekcyjny pozostaje rzadkim jackpotem. Geody dają dodatkową "
                "szansę na klejnoty: geody / geodes."
            )
            for definition in GEM_DEFINITIONS:
                await self.send(
                    f"{definition['raw_name']} -> "
                    f"{definition['cut_name']}. "
                    f"Wymaga Górnictwa {definition['mining_level']} "
                    f"i głębokości {definition['min_floor']}. "
                    f"Szlifowanie: Jubilerstwo {definition['level']}. "
                    f"Bonus: "
                    f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} "
                    f"+{definition['amount']}."
                )

    async def cut_gem(self, query):
            q = self.normalize_description_query(query)
            if not q:
                await self.send(
                    "Użycie: szlifuj <kamień>. "
                    "Przykład: szlifuj rubin."
                )
                return False

            candidates = {}
            for recipe_id, recipe in JEWELCRAFT_RECIPES.items():
                if not recipe.get("gem_cut_recipe"):
                    continue
                output = ITEMS[recipe["output"]]
                raw_id = next(iter(recipe["ingredients"]))
                raw = ITEMS[raw_id]
                candidates[recipe_id] = {
                    "name": output["name"],
                    "aliases": (
                        raw["name"],
                        output["name"],
                        recipe_id.replace("cut_", ""),
                    ),
                    "recipe": recipe,
                }

            found = find_by_name(candidates, query)
            if not found:
                await self.send(
                    "Nie rozpoznaję kamienia do szlifowania. "
                    "Wpisz kamienie."
                )
                return False

            _recipe_id, entry = found
            return await self.perform_recipe(
                entry["recipe"]["name"],
                JEWELCRAFT_RECIPES,
                "szlifowanie",
            )

    async def socket_gem(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz osadzać klejnotów podczas walki."
                )
                return False

            raw = str(query or "").strip()
            if not raw:
                await self.send(
                    "Użycie: osadz <klejnot> <pierścień/kolczyk/naszyjnik>. "
                    "Przykład: osadz rubin kolczyk 1."
                )
                return False

            normalized = self.normalize_description_query(raw)
            slot = None
            slot_tokens = (
                ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
                ("ring 1", "ring1"), ("ring1", "ring1"),
                ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
                ("ring 2", "ring2"), ("ring2", "ring2"),
                ("pierścień", "ring"), ("pierscien", "ring"),
                ("ring", "ring"),
                ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
                ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
                ("kolczyk", "earring"), ("kolczyki", "earring"), ("earring", "earring"),
                ("naszyjnik", "necklace"), ("necklace", "necklace"),
                ("głowa", "head"), ("glowa", "head"), ("head", "head"),
                ("ciało", "body"), ("cialo", "body"), ("body", "body"),
                ("ręce", "hands"), ("rece", "hands"), ("hands", "hands"),
                ("nogi", "legs"), ("legs", "legs"), ("stopy", "feet"), ("feet", "feet"),
                ("barki", "shoulders"), ("shoulders", "shoulders"), ("pas", "belt"), ("belt", "belt"),
                ("płaszcz", "cloak"), ("plaszcz", "cloak"), ("cloak", "cloak"),
                ("karwasze", "bracers"), ("bracers", "bracers"), ("relikt", "relic"), ("relic", "relic"),
                ("board", "board"),
            )
            gem_query = raw
            for token, resolved in slot_tokens:
                token_norm = self.normalize_description_query(token)
                if normalized.endswith(" " + token_norm):
                    slot = resolved
                    words = raw.split()
                    token_words = len(token.split())
                    gem_query = " ".join(words[:-token_words]).strip()
                    break
                if normalized == token_norm:
                    slot = resolved
                    gem_query = ""
                    break

            if not slot:
                await self.send(
                    "Na końcu podaj slot EQ, np. ring1, necklace, body, head, bracers albo board."
                )
                return False

            if slot in ("ring", "earring"):
                pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
                slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]

            item_id = self.server.db.equipped_item(self.account_id, slot)
            item = ITEMS.get(item_id) if item_id else None
            if not item:
                await self.send(f"Nie masz założonego przedmiotu w slocie {EQUIPMENT_SLOT_NAMES.get(slot, slot)}.")
                return False
            capacity = self.equipment_total_socket_capacity_v03114(item_id, item, "gem")
            if capacity <= 0:
                await self.send(f"{item['name']} nie ma gniazd na klejnoty.")
                return False
            rows = self.socketed_gem_rows_for_item(
                slot,
                item_id,
            )
            if len(rows) >= capacity:
                await self.send(
                    f"{item['name']} ma wszystkie gniazda zajęte: "
                    f"{len(rows)} z {capacity}."
                )
                return False

            owned_gems = {
                gem_id: ITEMS[gem_id]
                for gem_id in CUT_GEM_IDS
                if self.available_recipe_item(gem_id) > 0
            }
            found = find_by_name(owned_gems, gem_query)
            if not found:
                await self.send(
                    "Nie masz takiego oszlifowanego klejnotu."
                )
                return False

            gem_id, gem = found
            if not self.consume_recipe_item(gem_id, 1):
                await self.send("Nie masz tego klejnotu w Szkatułce Rzemieślniczej.")
                return False

            used = {
                int(row["socket_index"])
                for row in rows
            }
            socket_index = next(
                i for i in range(1, capacity + 1)
                if i not in used
            )
            self.server.db.add_socketed_gem(
                self.account_id,
                slot,
                item_id,
                socket_index,
                gem_id,
            )

            self.current_hp = min(
                self.current_hp,
                self.max_hp(),
            )
            self.current_mana = min(
                self.current_mana,
                self.max_mana(),
            )

            affix_name = CRYPT_AFFIXES.get(
                gem.get("affix"),
                gem.get("affix"),
            )
            await self.send(
                f"Osadzasz {gem['name']} w {item['name']}. "
                f"Gniazdo {socket_index} z {capacity}. "
                f"Bonus: {affix_name} "
                f"+{gem.get('affix_amount', 0)}."
            )
            return True

    async def show_socketed_gems(self):
            await self.send("GNIAZDA EQ 2.0")
            found_any = False
            for row in self.equipped_item_rows():
                slot=row["slot"]; item_id=row["item_id"]; item=ITEMS.get(item_id)
                if not item:
                    continue
                capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"gem")
                rune_capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"rune")
                if capacity<=0 and rune_capacity<=0:
                    continue
                found_any=True
                gems=self.socketed_gem_rows_for_item(slot,item_id) if capacity>0 else []
                runes=list(self.server.db.equipment_runes_v0925(self.account_id,item_id)) if rune_capacity>0 else []
                await self.send(f"{EQUIPMENT_SLOT_NAMES.get(slot,slot)}: {item['name']}. Klejnoty {len(gems)}/{capacity}. Runy {len(runes)}/{rune_capacity}.")
            if not found_any:
                await self.send("Nie masz założonego EQ z gniazdami.")

    def automatic_dual_slot_v03020(self, logical_slot):
            """Pick first free ring/charm/earring slot; when full, replace the weaker equipped piece."""
            pairs = {
                "ring": ("ring1", "ring2"),
                "charm": ("charm1", "charm2"),
                "earring": ("earring1", "earring2"),
            }
            paired = pairs[logical_slot]
            for slot in paired:
                if not self.server.db.equipped_item(self.account_id, slot):
                    return slot
            scored = []
            for order, slot in enumerate(paired):
                item_id = self.server.db.equipped_item(self.account_id, slot)
                item = ITEMS.get(item_id, {})
                scored.append((self.equipment_item_score(item), order, slot))
            scored.sort(key=lambda row: (row[0], row[1]))
            return scored[0][2]

    async def equip_shortcut_dual_v03020(self, logical_slot, query=""):
            pairs = {
                "ring": ("ring1", "ring2", "pierścienie", "zp"),
                "charm": ("charm1", "charm2", "talizmany", "zt"),
                "earring": ("earring1", "earring2", "kolczyki", "zkol"),
            }
            s1, s2, noun, shortcut = pairs[logical_slot]
            candidates = self.owned_armor_for_slot(s1)
            if not candidates:
                await self.send(f"Nie masz żadnego EQ w kategorii {noun}.")
                return
            raw = str(query or "").strip()
            if not raw:
                n1 = ITEMS.get(self.server.db.equipped_item(self.account_id, s1), {}).get("name", "pusty")
                n2 = ITEMS.get(self.server.db.equipped_item(self.account_id, s2), {}).get("name", "pusty")
                await self.send(f"{noun.capitalize()}. Slot 1: {n1}. Slot 2: {n2}. Wybierz numer przedmiotu:")
                for idx, (_score, item_id, item) in enumerate(candidates, 1):
                    await self.send(f"{idx}. {item.get('name', item_id)}. Level postaci {int(item.get('required_character_level', item.get('required_mastery',1)) or 1)}.")
                return
            if raw.isdigit():
                idx = int(raw)
                if not 1 <= idx <= len(candidates):
                    await self.send(f"Nie ma pozycji {idx}. Zakres: 1-{len(candidates)}.")
                    return
                _score, item_id, item = candidates[idx-1]
            else:
                pool = {item_id:item for _score,item_id,item in candidates}
                found = find_by_name(pool, raw)
                if not found:
                    await self.send(f"Nie rozpoznaję przedmiotu. Wpisz {shortcut}, aby dostać listę.")
                    return
                item_id, item = found
            await self.equip_item(item.get("name", item_id))

    async def equip_shortcut_slot_v03016(self, slot, query=""):
            """NVDA-friendly numbered slot picker.

            Sam skrót pokazuje numerowaną listę. Skrót + numer zakłada wybraną
            pozycję. Skrót + nazwa nadal działa, ale wyłącznie w obrębie tego slotu.
            """
            slot = str(slot or "")
            candidates = self.owned_armor_for_slot(slot)
            if not candidates:
                await self.send(
                    f"Nie masz żadnego EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}."
                )
                return
            raw = str(query or "").strip()
            if not raw:
                current_id = self.server.db.equipped_item(self.account_id, slot)
                current_name = ITEMS.get(current_id, {}).get("name") if current_id else None
                await self.send(
                    f"EQ {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                    f"Aktualnie: {current_name or 'pusty slot'}. Wybierz numer:"
                )
                for idx, (_score, item_id, item) in enumerate(candidates, 1):
                    mastery = int(item.get("required_mastery", 1) or 1)
                    marker = " [ZAŁOŻONE]" if item_id == current_id else ""
                    await self.send(
                        f"{idx}. {item.get('name', item_id)}. "
                        f"Level postaci {int(item.get('required_character_level', mastery) or mastery)}. "
                        f"{CLASS_SET_STAT_NAMES.get(item.get('affix'), item.get('affix'))} "
                        f"+{int(item.get('affix_amount', 0) or 0)}; "
                        + ", ".join(
                            f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{int(amount or 0)}"
                            for stat, amount in (item.get("stats") or {}).items()
                        )
                        + marker
                    )
                return

            found = None
            if raw.isdigit():
                index = int(raw)
                if 1 <= index <= len(candidates):
                    _score, item_id, item = candidates[index - 1]
                    found = (item_id, item)
                else:
                    await self.send(f"Nie ma pozycji {index}. Zakres: 1-{len(candidates)}.")
                    return
            else:
                pool = {item_id: item for _score, item_id, item in candidates}
                found = find_by_name(pool, raw)
                if not found:
                    await self.send(
                        f"Nie rozpoznaję EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                        "Wpisz sam skrót, aby dostać numerowaną listę."
                    )
                    return

            item_id, item = found
            if slot in ("ring1", "ring2", "charm1", "charm2", "earring1", "earring2"):
                await self.equip_item(f"{slot} {item.get('name', item_id)}")
            else:
                await self.equip_item(item.get("name", item_id))

    async def equip_item(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                    "Najpierw użyj flee albo zakończ walkę."
                )
                return

            raw_query = str(query or "").strip()
            normalized = self.normalize_description_query(raw_query)
            if not normalized:
                await self.send(
                    "Użycie: załóż <pełna nazwa EQ>. Pierścienie, talizmany i kolczyki wybierają wolny slot automatycznie; "
                    "ręczny slot 1/2 nadal działa. Skróty: zp, zt i zkol. Całość automatycznie: załóż auto albo eq auto."
                )
                return
            if normalized in ("auto", "automatycznie", "najlepsze", "best"):
                await self.auto_equip_best_v03040()
                return

            # Slot-only commands never choose the best item automatically.
            requested_slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
            if requested_slot:
                if requested_slot in ("ring", "charm", "earring"):
                    await self.equip_shortcut_dual_v03020(requested_slot)
                    return

                candidates = self.owned_armor_for_slot(requested_slot)
                if not candidates:
                    await self.send(
                        f"Nie masz żadnego pancerza w slocie {EQUIPMENT_SLOT_NAMES[requested_slot]}."
                    )
                    return

                current_id = self.server.db.equipped_item(self.account_id, requested_slot)
                choices = self.equipment_choices_text(candidates)
                if current_id:
                    current = ITEMS.get(current_id, {"name": current_id})
                    await self.send(
                        f"Slot {EQUIPMENT_SLOT_NAMES[requested_slot]} jest zajęty przez: {current['name']}. "
                        "Nic nie zostało zmienione. Podaj pełną nazwę przedmiotu, który chcesz założyć, "
                        "albo najpierw użyj zdejmij " + EQUIPMENT_SLOT_NAMES[requested_slot] + "."
                    )
                    if choices:
                        await self.send(f"Posiadane opcje dla tego slotu: {choices}.")
                    return

                if len(candidates) != 1:
                    await self.send(
                        f"Masz kilka przedmiotów dla slotu {EQUIPMENT_SLOT_NAMES[requested_slot]}. "
                        "Gra nie wybiera najlepszego automatycznie. Podaj pełną nazwę wybranego EQ."
                    )
                    if choices:
                        await self.send(f"Posiadane opcje: {choices}.")
                    return
                _score, item_id, item = candidates[0]
                found = (item_id, item)
                explicit_slot = requested_slot
            else:
                explicit_slot, item_query = self.explicit_dual_slot_and_item_query(raw_query)
                if explicit_slot and not item_query:
                    candidates = self.owned_armor_for_slot(explicit_slot)
                    choices = self.equipment_choices_text(candidates)
                    current_id = self.server.db.equipped_item(self.account_id, explicit_slot)
                    if current_id:
                        current = ITEMS.get(current_id, {"name": current_id})
                        await self.send(
                            f"Slot {EQUIPMENT_SLOT_NAMES[explicit_slot]} jest zajęty przez: {current['name']}. "
                            "Nic nie zostało zmienione. Podaj pełną nazwę wybranego przedmiotu."
                        )
                    elif len(candidates) == 1:
                        _score, item_id, item = candidates[0]
                        found = (item_id, item)
                    else:
                        await self.send(
                            f"Wybierz konkretny przedmiot dla slotu {EQUIPMENT_SLOT_NAMES[explicit_slot]}. "
                            "Gra nie wybiera najlepszego automatycznie."
                        )
                        if choices:
                            await self.send(f"Posiadane opcje: {choices}.")
                        return
                    if current_id:
                        if choices:
                            await self.send(f"Posiadane opcje: {choices}.")
                        return
                else:
                    found = self.resolve_equipment_for_equip(item_query)

            if not found:
                await self.send(
                    "Nie rozpoznaję posiadanego EQ. Podaj pełną nazwę przedmiotu. "
                    "Pierścienie, talizmany i kolczyki nie wymagają podawania slotu 1/2."
                )
                return

            item_id, item = found
            if item.get("type") != "armor":
                await self.send("Tego przedmiotu nie można założyć.")
                return

            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                await self.send(
                    f"{item['name']} wymaga aktywnej klasy {required_class}."
                )
                return

            required_race = item.get("required_race")
            if required_race and str(self.character.race) != str(required_race):
                await self.send(
                    f"{item['name']} może używać tylko rasa {required_race}."
                )
                return

            required_mastery = max(1, int(item.get("required_mastery", 1)))
            if not self.equipment_mastery_requirement_met(item):
                await self.send(
                    f"{item['name']}: {self.equipment_mastery_requirement_text(item)}"
                )
                return

            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                await self.send("Nie masz tego przedmiotu.")
                return

            logical_slot = item["slot"]
            if logical_slot == "ring":
                actual_slot = explicit_slot if explicit_slot in ("ring1", "ring2") else self.automatic_dual_slot_v03020("ring")
            elif logical_slot == "charm":
                actual_slot = explicit_slot if explicit_slot in ("charm1", "charm2") else self.automatic_dual_slot_v03020("charm")
            elif logical_slot == "earring":
                actual_slot = explicit_slot if explicit_slot in ("earring1", "earring2") else self.automatic_dual_slot_v03020("earring")
            else:
                actual_slot = logical_slot
                if explicit_slot and explicit_slot != actual_slot:
                    await self.send(
                        f"{item['name']} nie pasuje do slotu {EQUIPMENT_SLOT_NAMES.get(explicit_slot, explicit_slot)}."
                    )
                    return

            if logical_slot in ("ring", "charm", "earring"):
                paired = {
                    "ring": ("ring1", "ring2"),
                    "charm": ("charm1", "charm2"),
                    "earring": ("earring1", "earring2"),
                }[logical_slot]
                already_equipped = sum(
                    1 for row in self.equipped_item_rows()
                    if row["slot"] in paired and row["item_id"] == item_id and row["slot"] != actual_slot
                )
                if self.server.db.item_qty(self.account_id, item_id) <= already_equipped:
                    await self.send(
                        "Do drugiego slotu potrzebujesz drugiej sztuki tego samego przedmiotu."
                    )
                    return

            old_item_id = self.server.db.equipped_item(self.account_id, actual_slot)
            if old_item_id == item_id:
                await self.send(f"{item['name']} jest już założony w tym slocie.")
                return

            returned_gems = []
            if actual_slot in ("ring1", "ring2", "earring1", "earring2", "necklace") and old_item_id:
                returned_gems = await self.return_socketed_gems(actual_slot, old_item_id)

            # Replacing is explicit by chosen item; v0.30.20 may auto-pick the free/weaker ring or charm slot.
            self.server.db.equip(self.account_id, actual_slot, item_id)
            replaced_item = ITEMS.get(old_item_id) if old_item_id else None
            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())

            if replaced_item:
                await self.send(
                    f"Na twoje polecenie zdejmujesz: {replaced_item['name']}. "
                    f"Zakładasz wybrany przedmiot w tym samym slocie."
                )

            rarity = f" Rzadkość: {item['rarity_name']}." if item.get("rarity_name") else ""
            affix = ""
            if item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
                affix = f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
            fixed_stats = ""
            if item.get("stats"):
                fixed_text = ", ".join(
                    f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                    for stat, amount in item.get("stats", {}).items()
                    if int(amount or 0) != 0
                )
                if fixed_text:
                    fixed_stats = f" Statystyki bazowe: {fixed_text}."
            await self.send(
                f"Zakładasz: {item['name']}. "
                f"Slot: {EQUIPMENT_SLOT_NAMES.get(actual_slot, actual_slot)}. "
                f"Obrona przedmiotu +{item.get('defense', 0)}.{rarity}{affix}{fixed_stats}"
            )
            if returned_gems:
                await self.send(
                    "Z poprzedniej biżuterii wyjęto i zwrócono do Szkatułki Rzemieślniczej: "
                    + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
                )
            await self.send(f"Obrona fizyczna wynosi teraz {self.defense()}.")
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())

    async def unequip_item(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                    "Najpierw użyj flee albo zakończ walkę."
                )
                return

            normalized = self.normalize_description_query(str(query or "").strip())
            slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
            if slot in ("ring", "charm", "earring"):
                noun = {"ring":"pierścień", "charm":"talizman", "earring":"kolczyk"}[slot]
                await self.send(f"Podaj konkretny slot: zdejmij {noun} 1 albo zdejmij {noun} 2.")
                return
            if slot not in EQUIPMENT_SLOT_NAMES:
                await self.send(
                    "Użycie: zdejmij <slot>, np. zdejmij hełm, zdejmij pierścień 1, "
                    "zdejmij kolczyk 2, zdejmij talizman 2 albo zdejmij naszyjnik."
                )
                return

            item_id = self.server.db.equipped_item(self.account_id, slot)
            if not item_id:
                await self.send(f"Slot {EQUIPMENT_SLOT_NAMES[slot]} jest już pusty.")
                return
            item = ITEMS.get(item_id, {"name": item_id})
            returned_gems = []
            if slot in ("ring1", "ring2", "earring1", "earring2", "necklace"):
                returned_gems = await self.return_socketed_gems(slot, item_id)
            self.server.db.unequip(self.account_id, slot)
            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())
            await self.send(
                f"Zdejmujesz: {item['name']}. Slot {EQUIPMENT_SLOT_NAMES[slot]} jest teraz pusty."
            )
            if returned_gems:
                await self.send(
                    "Wyjęte klejnoty wracają do Szkatułki Rzemieślniczej: "
                    + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
                )

    def find_consumable_for_use(self, query):
            q = self.normalize_description_query(query)
            if not q:
                return None, []

            # v0.24.3: prosty skrót `użyj mapy`. Jeśli aktywny quest Erena
            # ma własną mapę, używamy najpierw jej; zwykła Mapa Skarbu nadal działa poza questem.
            if q in {"mapa", "mapy", "mape", "mapę", "mapa skarbu", "mape skarbu", "mapę skarbu", "treasure map"}:
                quest_map_id = globals().get("V0243_EREN_SECRET_MAP_ITEM")
                if quest_map_id and self.server.db.item_qty(self.account_id, quest_map_id) > 0:
                    return (quest_map_id, ITEMS[quest_map_id]), []
                return (V014_TREASURE_MAP_ITEM, ITEMS[V014_TREASURE_MAP_ITEM]), []

            # Celowe krótkie aliasy wymagane dla szybkiej obsługi NVDA.
            direct_aliases = {
                "mikstura": "healing_potion",
                "miksture": "healing_potion",
                "miksturę": "healing_potion",
                "potion": "healing_potion",
                "eliksir": "soul_elixir",
                "elixir": "soul_elixir",
                "eliksir duszy": "soul_elixir",
                "soul elixir": "soul_elixir",
                "mana": "mana_potion",
                "mikstura many": "mana_potion",
                "mana potion": "mana_potion",
            }
            item_id = direct_aliases.get(q)
            if item_id:
                return (item_id, ITEMS[item_id]), []

            consumables = {
                item_id: item
                for item_id, item in ITEMS.items()
                if item.get("type") == "consumable"
            }

            exact = []
            partial = []
            for item_id, item in consumables.items():
                names = (
                    item_id,
                    item.get("name", ""),
                )
                normalized_names = [
                    self.normalize_description_query(name)
                    for name in names
                ]
                if q in normalized_names:
                    exact.append((item_id, item))
                elif any(q in name for name in normalized_names):
                    partial.append((item_id, item))

            if exact:
                return exact[0], []
            if len(partial) == 1:
                return partial[0], []
            if len(partial) > 1:
                return None, partial
            return None, []

    async def use_item(self, query):
            raw_query = str(query or "").strip()
            lowered = raw_query.lower()

            # Wygodna składnia dla umiejętności:
            # użyj umiejętność <nazwa> [cel]
            # use skill <name> [target]
            skill_prefixes = (
                "skill ",
                "umiejętność ",
                "umiejetnosc ",
                "zdolność ",
                "zdolnosc ",
                "czar ",
                "spell ",
            )
            for prefix in skill_prefixes:
                if lowered.startswith(prefix):
                    skill_query = raw_query[len(prefix):].strip()
                    if not skill_query:
                        await self.send(
                            "Użycie: użyj umiejętność <nazwa> [cel] "
                            "albo use skill <name> [target]."
                        )
                        return
                    await self.use_class_skill(skill_query)
                    return

            found, ambiguous = self.find_consumable_for_use(raw_query)

            if ambiguous:
                names = ", ".join(item["name"] for _, item in ambiguous)
                await self.send(
                    f"Nazwa pasuje do kilku przedmiotów: {names}. "
                    "Podaj dokładniejszą nazwę."
                )
                return

            if not found:
                skill, _target = self.find_skill_from_input(raw_query)
                if skill:
                    await self.use_class_skill(raw_query)
                    return

                await self.send(
                    "Nie rozpoznaję przedmiotu ani umiejętności. "
                    "Przykłady: użyj mikstura; użyj umiejętność <nazwa> [cel]; "
                    "use skill <name> [target]."
                )
                return

            item_id, item = found

            if item.get("treasure_map"):
                if self.combat_mob_key:
                    await self.send("Nie możesz odczytywać mapy skarbu podczas walki.")
                    return
                await self.use_v0140_treasure_map(item_id)
                return

            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                await self.send(f"Nie masz przedmiotu: {item['name']}.")
                return

            if item.get("type") != "consumable":
                await self.send("Tego przedmiotu nie używa się w ten sposób.")
                return

            if "heal" in item or "mana" in item:
                max_hp = self.max_hp()
                max_mana = self.max_mana()

                missing_hp = max(0, max_hp - self.current_hp)
                missing_mana = max(0, max_mana - self.current_mana)

                can_restore_hp = (
                    item.get("heal", 0) > 0
                    and missing_hp > 0
                )
                can_restore_mana = (
                    item.get("mana", 0) > 0
                    and max_mana > 0
                    and missing_mana > 0
                )

                if not can_restore_hp and not can_restore_mana:
                    if max_mana > 0:
                        await self.send("Masz pełne HP i Manę.")
                    else:
                        await self.send("Masz pełne życie.")
                    return

                self.server.db.remove_item(
                    self.account_id, item_id, 1
                )

                healed = 0
                restored_mana = 0

                if can_restore_hp:
                    healed = min(
                        item.get("heal", 0), missing_hp
                    )
                    self.current_hp += healed

                if can_restore_mana:
                    restored_mana = min(
                        item.get("mana", 0), missing_mana
                    )
                    self.current_mana += restored_mana

                parts = []
                if healed:
                    parts.append(f"{healed} HP")
                if restored_mana:
                    parts.append(f"{restored_mana} Many")

                await self.send(
                    f"Używasz {item['name']}. Odzyskujesz "
                    + " i ".join(parts) + "."
                )
                await self.send(
                    f"HP {self.current_hp} z {max_hp}."
                )
                if max_mana > 0:
                    await self.send(
                        f"Mana {self.current_mana} z {max_mana}."
                    )

                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if "soul_xp" in item:
                self.server.db.remove_item(
                    self.account_id, item_id, 1
                )
                await self.send(
                    f"Używasz {item['name']}."
                )
                await self.grant_soul_xp(
                    item["soul_xp"]
                )
                self.server.db.save_character(self.character)

                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            await self.send(
                "Ten przedmiot nie ma efektu do użycia."
            )

    def current_shop_offers(self, class_filter=""):
            room_id = self.character.room_id
            class_names = CLASS_SHOP_CLASSES_BY_ROOM.get(room_id)
            if not class_names:
                return list(SHOPS.get(room_id, ()))

            selected = list(class_names)
            query = normalize_lookup_text(class_filter or "")
            if query:
                matched = [
                    class_name for class_name in class_names
                    if query in normalize_lookup_text(class_name)
                    or normalize_lookup_text(class_name) in query
                ]
                if matched:
                    selected = matched
                else:
                    return []

            offers = []
            for class_name in selected:
                # v0.30.35: klasowe EQ odblokowuje Level postaci, nie Biegłość klasy.
                character_level = max(1, min(CHARACTER_MAX_LEVEL, int(self.character.character_level)))
                unlocked_tier = class_equipment_unlocked_tier(character_level)
                offers.extend(
                    CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
                    .get(class_name, {})
                    .get(unlocked_tier, ())
                )
            return offers

    def shop_offer_lock_text(self, item_id, item):
            """Krótki stan dostępności do czytania na numerowanej liście sklepu."""
            states = []
            if is_character_bound_item(item_id) and self.server.db.item_qty(self.account_id, item_id) > 0:
                states.append("już posiadasz")
            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                states.append(f"wymaga aktywnej klasy {required_class}")
            if item.get("type") == "armor" and not self.equipment_mastery_requirement_met(item):
                required_level = self.equipment_character_level_requirement(item)
                states.append(f"wymaga Levelu postaci {required_level}")
            return "; ".join(states)

    def equipped_items_for_shop_item(self, item):
            """Zwraca założone przedmioty zajmujące logicznie ten sam slot co oferta."""
            if item.get("type") != "armor":
                return []
            logical = item.get("slot")
            if logical == "ring":
                valid_slots = {"ring", "ring1", "ring2"}
            elif logical == "charm":
                valid_slots = {"charm", "charm1", "charm2"}
            elif logical == "earring":
                valid_slots = {"earring", "earring1", "earring2"}
            else:
                valid_slots = {logical}
            results = []
            for row in self.server.db.equipment(self.account_id):
                if row["slot"] not in valid_slots:
                    continue
                equipped = ITEMS.get(row["item_id"])
                if equipped:
                    results.append((row["slot"], row["item_id"], equipped))
            return results

    async def shop_info(self, query, class_filter=""):
            """Pełny podgląd pozycji sklepu przed zakupem, szczególnie wygodny dla NVDA."""
            room_id = self.character.room_id
            offers = self.current_shop_offers(class_filter)
            if not offers:
                await self.send("W tej lokacji nie ma sklepu.")
                return

            raw = str(query or "").strip()
            if not raw:
                await self.send("Użycie: shop info <numer>, na przykład shop info 1.")
                return

            found = None
            numeric = re.fullmatch(r"\d+", raw)
            if numeric:
                number = int(raw)
                if number < 1 or number > len(offers):
                    await self.send(
                        f"Nie ma pozycji {number} w tym sklepie. Zakres: 1-{len(offers)}."
                    )
                    return
                item_id = offers[number - 1]
                found = (number, item_id, ITEMS[item_id])
            else:
                possible = {item_id: ITEMS[item_id] for item_id in offers}
                by_name = find_by_name(possible, raw)
                if by_name:
                    item_id, item = by_name
                    found = (offers.index(item_id) + 1, item_id, item)

            if not found:
                await self.send(
                    "Nie rozpoznaję tej pozycji sklepu. Wpisz shop po numerowaną listę, "
                    "potem shop info <numer>."
                )
                return

            number, item_id, item = found
            base_price = self.shop_item_base_value_silver(item)
            cashback = self.shop_cashback_silver(item)
            final_price = max(0, base_price - cashback)
            await self.send(f"SHOP INFO {number}. {item['name']}.")
            await self.send(self.format_item_description(item_id, item))
            if cashback > 0:
                await self.send(
                    "Cena katalogowa: " + currency_reading_text(base_price, 0, 0)
                    + ". Zwrot z rabatu Charyzmy: " + currency_reading_text(cashback, 0, 0)
                    + ". Efektywny koszt: " + currency_reading_text(final_price, 0, 0) + "."
                )
            else:
                await self.send("Koszt zakupu: " + currency_reading_text(base_price, 0, 0) + ".")

            lock_text = self.shop_offer_lock_text(item_id, item)
            if lock_text:
                await self.send("Stan zakupu: " + lock_text + ".")
            else:
                await self.send("Stan zakupu: możesz kupić ten przedmiot.")

            if item.get("type") == "armor":
                equipped = self.equipped_items_for_shop_item(item)
                new_def = int(item.get("defense", 0) or 0)
                if not equipped:
                    await self.send("Porównanie EQ: w tym slocie nic nie masz założonego.")
                else:
                    await self.send("Porównanie z aktualnym EQ:")
                    for slot, equipped_id, current in equipped:
                        old_def = int(current.get("defense", 0) or 0)
                        diff = new_def - old_def
                        diff_text = f"+{diff}" if diff > 0 else str(diff)
                        slot_name = EQUIPMENT_SLOT_NAMES.get(slot, slot)
                        await self.send(
                            f"{slot_name}: {current['name']}. Obrona +{old_def}. "
                            f"Nowy przedmiot: +{new_def}. Różnica {diff_text}."
                        )
                        # Pełne statystyki obecnego przedmiotu są ważniejsze niż zgadywana ocena mocy.
                        await self.send("Obecne EQ: " + self.format_item_description(equipped_id, current))
            await self.send(f"Kupno: kup {number}. Powrót do listy: shop.")

    async def shop(self, args=""):
            room_id = self.character.room_id
            class_names = CLASS_SHOP_CLASSES_BY_ROOM.get(room_id, ())
            raw_args = (args or "").strip()

            # shop info 1 / sklep info 1 / list info 1
            info_match = re.match(r"^(?:info|informacje|opis|details|szczegoly|szczegóły)(?:\s+(.+))?$", raw_args, flags=re.IGNORECASE)
            if info_match:
                await self.shop_info(info_match.group(1) or "")
                return

            class_filter = raw_args
            offers = self.current_shop_offers(class_filter)
            if not offers:
                if class_filter and class_names:
                    await self.send(
                        "W tej sali nie ma sklepu wskazanej klasy. Dostępne: "
                        + ", ".join(class_names) + "."
                    )
                else:
                    await self.send("W tej lokacji nie ma sklepu.")
                return
            seller_id = SHOP_SELLERS.get(self.character.room_id)
            seller = NPCS.get(seller_id) if seller_id else None
            seller_text = f" Sprzedawca: {seller['name']}." if seller else ""
            class_heading = f" Klasa: {class_filter}." if class_filter and class_names else ""
            await self.send(
                f"Oferta sklepu.{class_heading} Rabat Charyzmy: "
                f"{self.character.shop_discount_percent()} procent.{seller_text}"
            )
            for number, item_id in enumerate(offers, 1):
                item = ITEMS[item_id]
                price_coins = self.shop_item_base_value_silver(item)
                cashback = self.shop_cashback_silver(item)
                effective = max(0, price_coins - cashback)
                price_text = currency_reading_text(effective, 0, 0)
                lock_text = self.shop_offer_lock_text(item_id, item)
                state = f" — {lock_text}" if lock_text else ""
                await self.send(f"{number}. {item['name']} — cena {price_text}{state}.")
            await self.send(
                "Podgląd przed zakupem: shop info <numer>, np. shop info 1. "
                "Kupno: kup <numer> lub kup <numer> <ilość>. "
                "Sprzedaż: sprzedaj <nazwa>."
            )

    async def buy(self, query):
            raw_query = (query or "").strip()
            normalized_query = normalize_lookup_text(raw_query)
            requested_tool = TOOL_BUY_ALIASES.get(normalized_query)

            offers = self.current_shop_offers()
            if not offers:
                if requested_tool:
                    target_room = TOOL_SHOP_ROOMS[requested_tool]
                    await self.send(
                        f"{ITEMS[requested_tool]['name']} kupisz w lokacji "
                        f"{ROOMS[target_room]['name']}. "
                        f"Możesz użyć walk {target_room.replace('_', ' ')}."
                    )
                    return
                await self.send("W tej lokacji nie ma sklepu.")
                return

            possible = {item_id: ITEMS[item_id] for item_id in offers}
            quantity = 1
            found = None

            # Zakup numerem z aktualnej, ponumerowanej listy sklepu.
            # Przykłady: kup 9, kup 9 3.
            numeric_match = re.fullmatch(r"\s*(\d+)(?:\s+(\d+))?\s*", raw_query)
            if numeric_match:
                offer_number = int(numeric_match.group(1))
                if numeric_match.group(2):
                    quantity = int(numeric_match.group(2))
                if quantity < 1:
                    await self.send("Liczba sztuk musi być większa od zera.")
                    return
                if offer_number < 1 or offer_number > len(offers):
                    await self.send(
                        f"Nie ma pozycji {offer_number} w tym sklepie. "
                        f"Wpisz shop albo list, aby usłyszeć ofertę od 1 do {len(offers)}."
                    )
                    return
                item_id = offers[offer_number - 1]
                found = (item_id, ITEMS[item_id])

            if not found and requested_tool and requested_tool in possible:
                found = (requested_tool, possible[requested_tool])
            if not found:
                found = find_by_name(possible, raw_query)

            if not found:
                if requested_tool:
                    target_room = TOOL_SHOP_ROOMS[requested_tool]
                    await self.send(
                        f"{ITEMS[requested_tool]['name']} nie jest sprzedawana tutaj. "
                        f"Kupisz ją w lokacji {ROOMS[target_room]['name']}."
                    )
                    return
                await self.send(
                    "Tego przedmiotu nie ma w ofercie. "
                    "Możesz też kupować numerem, na przykład kup 9."
                )
                return

            item_id, item = found

            if is_character_bound_item(item_id):
                if quantity != 1:
                    await self.send(
                        f"{item['name']} jest przypisany do postaci i można kupić tylko jedną sztukę."
                    )
                    return
                owned_quantity = self.server.db.item_qty(
                    self.account_id, item_id
                )
                if owned_quantity > 0:
                    await self.send(
                        f"{item['name']} jest już przypisany do tej postaci. "
                        "Każde narzędzie profesji można kupić tylko raz."
                    )
                    return

            required_class = item.get("required_class")
            if (
                required_class
                and required_class
                not in self.active_class_names()
            ):
                await self.send(
                    f"{item['name']} jest wyposażeniem klasy "
                    f"{required_class}. Aktywuj tę klasę, aby kupić "
                    "ten przedmiot."
                )
                return

            required_mastery = max(1, int(item.get("required_mastery", 1)))
            if not self.equipment_mastery_requirement_met(item):
                await self.send(
                    f"{item['name']}: {self.equipment_mastery_requirement_text(item)}"
                )
                return

            unit_price = self.shop_item_base_value_silver(item)
            total_price = unit_price * quantity
            current = self.character_wallet_silver_value()
            if current < total_price:
                await self.send(
                    "Masz za mało pieniędzy. Potrzeba "
                    + currency_reading_text(total_price, 0, 0)
                    + f" za {quantity} szt. Masz "
                    + currency_reading_text(current, 0, 0) + "."
                )
                return
            self.character.silver = current - total_price
            self.character.gold = 0
            self.character.mithril = 0
            cashback = self.shop_cashback_silver(item) * quantity
            if cashback > 0:
                self.character.silver += cashback
            if item_id in (FISH_STORAGE_IDS | MINING_STORAGE_IDS | WOOD_STORAGE_IDS | HERB_STORAGE_IDS):
                self.store_profession_resource(item_id, quantity)
            else:
                self.server.db.add_item(self.account_id, item_id, quantity)
            if item.get("type") == "tool":
                self.server.db.ensure_tool(self.account_id, item["tool_type"])
            self.server.db.save_character(self.character)
            if quantity == 1:
                await self.send(f"Kupujesz {item['name']} za " + currency_reading_text(total_price, 0, 0) + ".")
            else:
                await self.send(
                    f"Kupujesz {quantity} szt. {item['name']} za "
                    + currency_reading_text(total_price, 0, 0) + "."
                )
            if cashback > 0:
                await self.send(
                    "Rabat Charyzmy: sprzedawca zwraca ci "
                    + currency_reading_text(cashback, 0, 0) + "."
                )

    async def show_teachers(self):
            teachers = [
                (npc_id, npc) for npc_id, npc in NPCS.items()
                if npc.get("teacher_class")
            ]
            await self.send("Nauczyciele klasowi mają osobne sale w Gildii Dusz. Nauka jest płatna:")
            for number, (npc_id, npc) in enumerate(teachers, 1):
                own = (
                    " Aktywna klasa."
                    if npc["teacher_class"] in self.active_class_names()
                    else ""
                )
                room_name = ROOMS[npc["room"]]["name"]
                await self.send(
                    f"{number}. {npc['name']}. Klasa: {npc['teacher_class']}. "
                    f"Lokacja: {room_name}.{own}"
                )
            await self.send(
                "Użyj prowadz <nazwa lokacji>, aby dojść do odpowiedniej sali, "
                "potem talk <nauczyciel>. Każdy skill pokazuje cenę nauki."
            )

    async def teacher_lesson(self, npc):
            class_name = npc["teacher_class"]
            learned = self.server.db.learned_skill_ids(self.account_id)

            await self.send(
                f"Lekcja klasy {class_name}. {CLASS_DESCRIPTIONS.get(class_name, '')}"
            )

            for number, skill in enumerate(CLASS_SKILLS.get(class_name, []), 1):
                progress = ""
                if class_name not in self.active_class_names():
                    status = f"wymaga aktywnej klasy {class_name} i Biegłości {skill['unlock']}"
                elif skill["id"] in learned:
                    row = self.server.db.skill_progress(self.account_id, skill["id"])
                    status = "już nauczona"
                    if int(row["level"]) >= SKILL_MAX_LEVEL:
                        progress = f" Skill Level {SKILL_MAX_LEVEL}, maksymalny."
                    else:
                        progress = (
                            f" Skill Level {row['level']}, XP {row['xp']} z "
                            f"{skill_xp_to_next(int(row['level']))}."
                        )
                elif self.class_mastery_level(class_name) >= int(skill["unlock"]):
                    status = "możesz nauczyć się teraz"
                else:
                    status = f"zablokowana do Biegłości klasy {skill['unlock']}"

                mana = f" Mana {skill.get('mana', 0)}." if skill.get("mana", 0) else ""
                training_cost = self.skill_training_cost_silver(skill)
                training_discount = self.character.guild_training_discount(class_name)
                training_cost = max(1, int(round(training_cost * (1.0 - training_discount))))
                cost_text = (
                    ""
                    if skill["id"] in learned
                    else f" Cena nauki po rabacie Gildii: {self.training_cost_text(training_cost)}."
                )
                await self.send(
                    f"{number}. {skill['name']}. {status}.{progress} "
                    f"Cooldown bazowy {skill['cooldown']} sekund.{mana} "
                    f"{skill['desc']}{cost_text}"
                )

            if class_name in self.active_class_names():
                role = (
                    "głównej" if class_name == self.character.class_name
                    else "dodatkowej aktywnej"
                )
                await self.send(
                    f"To jest nauczyciel twojej {role} klasy {class_name}. "
                    f"Aktualna Biegłość klasy {class_name}: {self.class_mastery_level(class_name)}."
                )
                await self.send(
                    "Nauka: learn <numer>, naucz <pełna nazwa> albo "
                    "naturalnie, np. naucz leczenie, naucz tarcza, "
                    "naucz ciecie, naucz pocisk, naucz ogien. "
                    f"Każdy nauczony skill rozwija własny Skill Level 1-{SKILL_MAX_LEVEL}. "
                    "Nauka jest płatna; cena jest podana przy każdym skillu."
                )
            else:
                await self.send(
                    f"Klasa {class_name} nie jest teraz aktywna. "
                    "Dodaj ją przez multiclass add <klasa>, aby móc się uczyć."
                )
