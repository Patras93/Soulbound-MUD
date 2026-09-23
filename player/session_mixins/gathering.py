# -*- coding: utf-8 -*-
"""Auto gathering, profession views and gathering loot."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import random
from core.bootstrap_economy_professions import (
    PROFESSION_RANK_NAMES,
    TOOL_TIER_NAMES,
    generator_core_v027,
    profession_for_tool_type,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
    profession_rank_thresholds,
    tool_max_level,
    tool_tier,
    tool_tier_access_level,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS, ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import (
    PROFESSION_MAX_LEVEL,
    TOOL_MAX_LEVEL,
    TOOL_MAX_TIER,
    TOOL_TIER_BONUS_CHANCES,
    TOOL_TIER_THRESHOLDS,
)
from core.progression_resources import (
    FISHING_ECOLOGY_PREFERRED_IDS,
    FISHING_HABITAT_LABELS,
    FISHING_ROOMS,
    FISHING_WATER_TYPE_OVERRIDES,
    FISH_RESOURCE_IDS,
    HERBALISM_ROOMS,
    HERB_RESOURCE_IDS,
    LAKE_FISHING_ROOMS,
    LAKE_FISH_ATLAS,
    OCEAN_FISHING_ROOMS,
    OCEAN_FISH_ATLAS,
    ORE_RESOURCE_IDS,
    RIVER_FISHING_ROOMS,
    RIVER_FISH_ATLAS,
    SEA_FISHING_ROOMS,
    SEA_FISH_ATLAS,
    WOODCUTTING_ROOMS,
    WOOD_RESOURCE_IDS,
    is_mining_room,
    mine_floor_number,
    mining_ore_weights,
)
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.dungeons_regions import profession_dungeon_floor
from systems.equipment_crafting import roll_mined_gem_quality
from systems.items_resources import (
    base_fish_species_id,
    fish_rarity_label,
    fish_species_habitats,
    fish_species_rarity,
    format_fish_length,
    format_fish_weight,
)


class SessionGatheringMixin:

    async def stop_auto_fishing(self, announce=True, immediate=True):
            self.auto_fishing = False
            task = self.auto_fishing_task

            if immediate:
                self.auto_fishing_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-łowienie wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-łowienie wyłączone. "
                        "Trwający połów zostanie dokończony, ale następny już się nie rozpocznie."
                    )
                return

            self.auto_fishing_task = None
            if announce:
                await self.send("Auto-łowienie wyłączone.")

    async def auto_fishing_loop(self):
            try:
                while self.auto_fishing and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-łowienie zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "fishing_rod"
                    ) <= 0:
                        await self.send(
                            "Auto-łowienie zatrzymane: nie masz Wędki."
                        )
                        break
                    if self.character.room_id not in FISHING_ROOMS:
                        await self.send(
                            "Auto-łowienie zatrzymane: nie stoisz przy łowisku."
                        )
                        break

                    await self.fish(from_auto=True)

            except asyncio.CancelledError:
                pass
            except Exception as exc:
                try:
                    await self.send(
                        f"Auto-łowienie zatrzymane przez błąd wewnętrzny: "
                        f"{type(exc).__name__}: {exc}."
                    )
                except Exception:
                    pass
                try:
                    import traceback
                    print("AUTO_FISHING_ERROR\n" + traceback.format_exc(), flush=True)
                except Exception:
                    pass
            finally:
                self.auto_fishing = False
                if self.auto_fishing_task is asyncio.current_task():
                    self.auto_fishing_task = None

    async def set_auto_fishing(self, enabled):
            if enabled:
                if self.auto_fishing:
                    await self.send("Auto-łowienie jest już włączone.")
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-łowienia podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "fishing_rod"
                ) <= 0:
                    await self.send(
                        "Do auto-łowienia potrzebujesz Wędki."
                    )
                    return

                if self.character.room_id not in FISHING_ROOMS:
                    await self.send(
                        "Auto-łowienie możesz włączyć tylko przy łowisku. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_fishing = True
                self.auto_fishing_task = asyncio.create_task(
                    self.auto_fishing_loop()
                )
                await self.send(
                    "Auto-łowienie włączone. Łowi tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz low off albo fish off, aby je zatrzymać."
                )
                return

            if not self.auto_fishing and not self.auto_fishing_task:
                await self.send("Auto-łowienie jest już wyłączone.")
                return
            await self.stop_auto_fishing(
                announce=True, immediate=False
            )

    async def stop_auto_mining(self, announce=True, immediate=True):
            self.auto_mining = False
            task = self.auto_mining_task

            if immediate:
                self.auto_mining_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-kopanie wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-kopanie wyłączone. "
                        "Trwające wydobycie zostanie dokończone, ale następne już się nie rozpocznie."
                    )
                return

            self.auto_mining_task = None
            if announce:
                await self.send("Auto-kopanie wyłączone.")

    async def auto_mining_loop(self):
            try:
                while self.auto_mining and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-kopanie zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "pickaxe"
                    ) <= 0:
                        await self.send(
                            "Auto-kopanie zatrzymane: nie masz Kilofa."
                        )
                        break
                    if not is_mining_room(self.character.room_id):
                        await self.send(
                            "Auto-kopanie zatrzymane: nie stoisz w miejscu wydobycia."
                        )
                        break

                    if await self.auto_mine_descend_if_unlocked():
                        continue

                    await self.mine(from_auto=True)

            except asyncio.CancelledError:
                pass
            except Exception as exc:
                try:
                    await self.send(
                        f"Auto-kopanie zatrzymane przez błąd wewnętrzny: "
                        f"{type(exc).__name__}: {exc}."
                    )
                except Exception:
                    pass
                try:
                    import traceback
                    print("AUTO_MINING_ERROR\n" + traceback.format_exc(), flush=True)
                except Exception:
                    pass
            finally:
                self.auto_mining = False
                if self.auto_mining_task is asyncio.current_task():
                    self.auto_mining_task = None

    async def set_auto_mining(self, enabled):
            if enabled:
                if self.auto_mining:
                    await self.send("Auto-kopanie jest już włączone.")
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-kopania podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "pickaxe"
                ) <= 0:
                    await self.send(
                        "Do auto-kopania potrzebujesz Kilofa."
                    )
                    return

                if not is_mining_room(self.character.room_id):
                    await self.send(
                        "Auto-kopanie możesz włączyć tylko w miejscu wydobycia. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_mining = True
                self.auto_mining_task = asyncio.create_task(
                    self.auto_mining_loop()
                )
                await self.send(
                    "Auto-kopanie włączone. Jeśli jesteś w części wejściowej Kopalni Głębinowej, "
                    "automat sam zejdzie przez Wejście, Tunel i Komnatę na poziom 1 Kopalni Głębinowej. "
                    "Potem po przebiciu każdej ściany sam schodzi na następny odblokowany poziom. "
                    "Wpisz kop off albo mine off, aby je zatrzymać."
                )
                return

            if not self.auto_mining and not self.auto_mining_task:
                await self.send("Auto-kopanie jest już wyłączone.")
                return
            await self.stop_auto_mining(
                announce=True, immediate=False
            )

    async def stop_auto_woodcutting(self, announce=True, immediate=True):
            self.auto_woodcutting = False
            task = self.auto_woodcutting_task

            if immediate:
                self.auto_woodcutting_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-Drwalstwo wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-Drwalstwo wyłączone. "
                        "Trwające cięcie zostanie dokończone, ale następne już się nie rozpocznie."
                    )
                return

            self.auto_woodcutting_task = None
            if announce:
                await self.send("Auto-Drwalstwo wyłączone.")

    async def auto_woodcutting_loop(self):
            try:
                while self.auto_woodcutting and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "saw"
                    ) <= 0:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: nie masz Piły."
                        )
                        break
                    if self.character.room_id not in WOODCUTTING_ROOMS:
                        await self.send(
                            "Auto-Drwalstwo zatrzymane: nie stoisz przy drzewach."
                        )
                        break

                    await self.woodcut(from_auto=True)

            except asyncio.CancelledError:
                pass
            except Exception as exc:
                try:
                    await self.send(
                        f"Auto-Drwalstwo zatrzymane przez błąd wewnętrzny: "
                        f"{type(exc).__name__}: {exc}."
                    )
                except Exception:
                    pass
                try:
                    import traceback
                    print("AUTO_WOODCUTTING_ERROR\n" + traceback.format_exc(), flush=True)
                except Exception:
                    pass
            finally:
                self.auto_woodcutting = False
                if self.auto_woodcutting_task is asyncio.current_task():
                    self.auto_woodcutting_task = None

    async def set_auto_woodcutting(self, enabled):
            if enabled:
                if self.auto_woodcutting:
                    await self.send(
                        "Auto-Drwalstwo jest już włączone."
                    )
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-Drwalstwa podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "saw"
                ) <= 0:
                    await self.send(
                        "Do auto-Drwalstwa potrzebujesz Piły."
                    )
                    return

                if self.character.room_id not in WOODCUTTING_ROOMS:
                    await self.send(
                        "Auto-Drwalstwo możesz włączyć tylko przy drzewach. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_herbalism or self.auto_herbalism_task:
                    await self.stop_auto_herbalism(announce=False)

                self.auto_woodcutting = True
                self.auto_woodcutting_task = asyncio.create_task(
                    self.auto_woodcutting_loop()
                )
                await self.send(
                    "Auto-Drwalstwo włączone. Ścina tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz tnij off albo woodcut off, aby je zatrzymać."
                )
                return

            if not self.auto_woodcutting and not self.auto_woodcutting_task:
                await self.send(
                    "Auto-Drwalstwo jest już wyłączone."
                )
                return
            await self.stop_auto_woodcutting(
                announce=True, immediate=False
            )

    async def stop_auto_herbalism(self, announce=True, immediate=True):
            self.auto_herbalism = False
            task = self.auto_herbalism_task

            if immediate:
                self.auto_herbalism_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if announce:
                    await self.send("Auto-Zielarstwo wyłączone.")
                return

            if task and not task.done():
                if announce:
                    await self.send(
                        "Auto-Zielarstwo wyłączone. "
                        "Trwający zbiór zostanie dokończony, ale następny już się nie rozpocznie."
                    )
                return

            self.auto_herbalism_task = None
            if announce:
                await self.send("Auto-Zielarstwo wyłączone.")

    async def auto_herbalism_loop(self):
            try:
                while self.auto_herbalism and not self.closed:
                    if self.combat_mob_key:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: rozpoczęła się walka."
                        )
                        break
                    if self.server.db.item_qty(
                        self.account_id, "herbalist_sickle"
                    ) <= 0:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: nie masz Sierpa Zielarskiego."
                        )
                        break
                    if self.character.room_id not in HERBALISM_ROOMS:
                        await self.send(
                            "Auto-Zielarstwo zatrzymane: nie stoisz w miejscu z ziołami."
                        )
                        break

                    await self.gather_herb(from_auto=True)

            except asyncio.CancelledError:
                pass
            except Exception as exc:
                try:
                    await self.send(
                        f"Auto-Zielarstwo zatrzymane przez błąd wewnętrzny: "
                        f"{type(exc).__name__}: {exc}."
                    )
                except Exception:
                    pass
                try:
                    import traceback
                    print("AUTO_HERBALISM_ERROR\n" + traceback.format_exc(), flush=True)
                except Exception:
                    pass
            finally:
                self.auto_herbalism = False
                if self.auto_herbalism_task is asyncio.current_task():
                    self.auto_herbalism_task = None

    async def set_auto_herbalism(self, enabled):
            if enabled:
                if self.auto_herbalism:
                    await self.send(
                        "Auto-Zielarstwo jest już włączone."
                    )
                    return
                if self.combat_mob_key:
                    await self.send(
                        "Nie możesz rozpocząć auto-Zielarstwa podczas walki."
                    )
                    return
                if self.server.db.item_qty(
                    self.account_id, "herbalist_sickle"
                ) <= 0:
                    await self.send(
                        "Do auto-Zielarstwa potrzebujesz Sierpa Zielarskiego."
                    )
                    return

                if self.character.room_id not in HERBALISM_ROOMS:
                    await self.send(
                        "Auto-Zielarstwo możesz włączyć tylko w miejscu z ziołami. "
                        "Automat nie chodzi sam."
                    )
                    return

                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)

                self.auto_herbalism = True
                self.auto_herbalism_task = asyncio.create_task(
                    self.auto_herbalism_loop()
                )
                await self.send(
                    "Auto-Zielarstwo włączone. Zbiera tylko w aktualnym miejscu "
                    "i nie chodzi samodzielnie. "
                    "Wpisz zbieraj off, aby je zatrzymać."
                )
                return

            if not self.auto_herbalism and not self.auto_herbalism_task:
                await self.send(
                    "Auto-Zielarstwo jest już wyłączone."
                )
                return
            await self.stop_auto_herbalism(
                announce=True, immediate=False
            )

    async def show_profession_ranks(self):
            for profession in (
                "Wędkarstwo", "Górnictwo", "Drwalstwo",
                "Zielarstwo", "Gotowanie", "Alchemia",
                "Kowalstwo", "Jubilerstwo",
            ):
                await self.send(f"RANGI: {profession.upper()}")
                thresholds = profession_rank_thresholds(profession)
                max_rank = profession_max_rank(profession)
                max_level = profession_max_level(profession)

                for rank, minimum in enumerate(thresholds, 1):
                    if rank < max_rank:
                        maximum = thresholds[rank] - 1
                        level_text = f"level {minimum}-{maximum}"
                    else:
                        level_text = f"level {minimum}-{max_level}"

                    await self.send(
                        f"Ranga {rank}: "
                        f"{PROFESSION_RANK_NAMES[profession][rank - 1]}. "
                        f"{level_text}."
                    )

    async def show_professions(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            professions = (
                "Wędkarstwo", "Górnictwo", "Drwalstwo", "Zielarstwo",
                "Gotowanie", "Alchemia", "Kowalstwo", "Jubilerstwo",
                "Krawiectwo", "Garbarstwo", "Stolarstwo", "Zaklinanie",
            )
            await self.send("PROFESJE INFO" if detailed else "PROFESJE")
            for name in professions:
                row = self.server.db.profession(self.account_id, name)
                level = int(row["level"])
                max_level = profession_max_level(name)
                rank = profession_rank(level, name)
                max_rank = profession_max_rank(name)
                rank_name = profession_rank_name(name, level)
                if not detailed:
                    await self.send(
                        f"{name}: poziom {level}/{max_level}, ranga {rank}/{max_rank}: {rank_name}."
                    )
                    continue
                thresholds = profession_rank_thresholds(name)
                if rank < max_rank:
                    next_rank = f"Następna ranga od levelu {thresholds[rank]}."
                else:
                    next_rank = "Ranga maksymalna."
                xp_text = (
                    "maksimum" if level >= max_level else
                    f"{row['xp']} z {self.profession_xp_to_next(level, name)}"
                )
                await self.send(
                    f"{name}: poziom {level}/{max_level}. Ranga {rank}/{max_rank}: {rank_name}. "
                    f"XP {xp_text}. Akcje {row['actions']}. {next_rank}"
                )
            if detailed:
                await self.send(
                    "Maksimum wszystkich dwunastu profesji: poziom 600."
                )
                await self.send(
                    "Poziom profesji skraca czas pracy i blokuje receptury/zlecenia. "
                    "Poziom narzędzia odblokowuje lepsze surowce oraz zwiększa rare/quality i bonus urobku. "
                    "Wpisz narzedzia info po Tiery i bonusy."
                )
            else:
                await self.send("Wpisz profesje info po XP, akcje, progi rang i zasady.")

    async def show_tool_tiers(self):
            for tool_type, title in (
                ("fishing", "WĘDKI"),
                ("mining", "KILOFA"),
                ("woodcutting", "PIŁY"),
                ("crafting", "MŁOTA RZEMIEŚLNICZEGO"),
                ("cooking", "NOŻA KUCHARSKIEGO"),
                ("herbalism", "SIERPA ZIELARSKIEGO"),
                ("alchemy", "MOŹDZIERZA ALCHEMICZNEGO"),
                ("jewelcrafting", "SZCZYPIEC JUBILERSKICH"),
                ("tailoring", "ZESTAWU KRAWIECKIEGO"),
                ("leatherworking", "NOŻA GARBARSKIEGO"),
                ("carpentry", "NARZĘDZI CIESIELSKICH"),
                ("enchanting", "FOKUSU RUNICZNEGO"),
            ):
                await self.send(f"NAZWY TIERÓW {title}")
                for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                    if tier < TOOL_MAX_TIER:
                        maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                        level_text = f"level {minimum}-{maximum}"
                    else:
                        level_text = f"level {minimum}"
                    bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
                    await self.send(
                        f"Tier {tier}: {TOOL_TIER_NAMES[tool_type][tier - 1]}. "
                        f"{level_text}. Bonus {bonus} procent."
                    )

    def tool_info_definition(self, tool_type):
            definitions = {
                "fishing": ("fishing_rod", "Wędka"),
                "mining": ("pickaxe", "Kilof"),
                "woodcutting": ("saw", "Piła"),
                "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
                "cooking": ("chef_knife", "Nóż Kucharski"),
                "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
                "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
                "jewelcrafting": ("jeweler_pliers", "Szczypce Jubilerskie"),
            }
            return definitions.get(tool_type)

    def tool_bonus_label(self, tool_type):
            if tool_type == "cooking":
                return "Szansa na dodatkową potrawę"
            if tool_type == "crafting":
                return "Szansa na dodatkowy produkt receptury"
            if tool_type == "alchemy":
                return "Szansa na dodatkową miksturę"
            if tool_type == "herbalism":
                return "Szansa na dodatkowe zioło"
            if tool_type == "jewelcrafting":
                return "Szansa na dodatkową biżuterię"
            return "Bonus dodatkowego urobku"

    def profession_level_for_tool(self, tool_type):
            profession = profession_for_tool_type(tool_type)
            if not profession:
                return 1
            row = self.server.db.profession(self.account_id, profession)
            return max(1, min(profession_max_level(profession), int(row["level"])))

    def profession_action_seconds(self, tool_type, profession_level):
            return generator_core_v027.profession_action_seconds(tool_type, profession_level)

    def tool_action_seconds(self, tool_type, profession_level):
            """Alias zgodności: od v0.8.66 argument oznacza poziom PROFESJI, nie narzędzia."""
            return self.profession_action_seconds(tool_type, profession_level)

    def recipe_action_seconds(self, tool_type, profession_level, recipe):
            """Generator Core owns both profession tempo and recipe-stage complexity."""
            base = generator_core_v027.profession_action_seconds(tool_type, profession_level)
            required = max(1, min(PROFESSION_MAX_LEVEL, int(recipe.get("generator_level", 1) or 1)))
            progress_gap = max(0, required - int(profession_level))
            generated_penalty = int(round(3.0 * progress_gap / float(PROFESSION_MAX_LEVEL)))
            return max(1, int(base + generated_penalty))

    def tool_action_label(self, tool_type):
            return {
                "fishing": "Czas zarzucenia i połowu",
                "mining": "Czas wydobycia",
                "woodcutting": "Czas cięcia",
                "crafting": "Czas wytwarzania",
                "cooking": "Czas gotowania",
                "herbalism": "Czas zbioru",
                "alchemy": "Czas warzenia",
                "jewelcrafting": "Czas wykonania biżuterii",
                "tailoring": "Czas szycia",
                "leatherworking": "Czas garbowania",
                "carpentry": "Czas pracy stolarskiej",
                "enchanting": "Czas zaklinania",
            }.get(tool_type, "Czas akcji")

    def tool_xp_remaining_to_level(self, level, xp, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0
            return max(
                0,
                self.tool_xp_to_next(level, tool_type) - int(xp),
            )

    def tool_xp_remaining_to_next_tier(self, level, xp, tool_type=None):
            tier = tool_tier(level)
            if tier >= TOOL_MAX_TIER:
                return 0, 0

            target_level = TOOL_TIER_THRESHOLDS[tier]
            levels_remaining = max(0, target_level - level)

            total_xp = self.tool_xp_remaining_to_level(level, xp, tool_type)
            for current_level in range(level + 1, target_level):
                total_xp += self.tool_xp_to_next(current_level, tool_type)

            return levels_remaining, total_xp

    async def show_single_tool(self, tool_type):
            definition = self.tool_info_definition(tool_type)
            if not definition:
                await self.send("Nieznane narzędzie.")
                return

            item_id, name = definition
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                await self.send(f"{name}: nie posiadasz tego narzędzia.")
                if tool_type == "fishing":
                    await self.send(
                        "Wędkę kupisz tylko u Mistrza Wędkarstwa Nerisa "
                        "w Szkole Wędkarstwa."
                    )
                elif tool_type == "mining":
                    await self.send(
                        "Kilof kupisz tylko u Górnika Torena przy "
                        "Wejściu do Kryształowej Jaskini."
                    )
                elif tool_type == "woodcutting":
                    await self.send(
                        "Piłę kupisz tylko u Mistrza Drwalstwa Orena "
                        "w Leśniczówce."
                    )
                elif tool_type == "crafting":
                    await self.send(
                        "Młot Rzemieślniczy kupisz tylko u Mistrza "
                        "Rzemiosła Haldora w Warsztacie Rzemieślniczym."
                    )
                elif tool_type == "cooking":
                    await self.send(
                        "Nóż Kucharski kupisz tylko u Kucharza Marcela "
                        "w Kuchni Błękitnego Płomienia."
                    )
                elif tool_type == "herbalism":
                    await self.send(
                        "Sierp Zielarski kupisz tylko u Mistrzyni "
                        "Zielarstwa Seny w Ogrodzie Zielarskim."
                    )
                elif tool_type == "alchemy":
                    await self.send(
                        "Moździerz Alchemiczny kupisz tylko u Mistrza "
                        "Alchemii Orina w Laboratorium Alchemicznym."
                    )
                elif tool_type == "jewelcrafting":
                    await self.send(
                        "Szczypce Jubilerskie kupisz tylko u Jubilerki Mirelli "
                        "w Pracowni Jubilerskiej."
                    )
                return

            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            xp = int(row["xp"])
            uses = int(row["uses"])
            tier = tool_tier(level)
            max_level = tool_max_level(tool_type)
            tier_name = tool_tier_name(tool_type, level)
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)
            bonus_label = self.tool_bonus_label(tool_type)

            await self.send(f"NARZĘDZIE: {name}.")
            await self.send(
                f"Aktualna nazwa narzędzia: {tier_name}."
            )
            await self.send(
                f"Poziom: {level} z {max_level}. "
                f"Użycia: {uses}."
            )
            profession = profession_for_tool_type(tool_type)
            profession_level = self.profession_level_for_tool(tool_type)
            await self.send(
                f"{self.tool_action_label(tool_type)}: "
                f"{self.profession_action_seconds(tool_type, profession_level)} sekund. "
                f"Tempo daje {profession} poziom {profession_level}; poziom narzędzia nie skraca czasu."
            )

            if level >= max_level:
                await self.send("XP: maksimum. Do następnego levelu: maksimum.")
            else:
                needed = self.tool_xp_to_next(level, tool_type)
                remaining = self.tool_xp_remaining_to_level(level, xp, tool_type)
                await self.send(
                    f"XP obecnego levelu: {xp} z {needed}. "
                    f"Do następnego levelu brakuje {remaining} XP."
                )

            await self.send(
                f"Obecny Tier: {tier} z {TOOL_MAX_TIER}. "
                f"Nazwa: {tier_name}. "
                f"{bonus_label}: {bonus_percent} procent."
            )

            if tier >= TOOL_MAX_TIER:
                await self.send("Tier maksymalny. Nie ma następnego Tieru.")
            else:
                target_level = TOOL_TIER_THRESHOLDS[tier]
                next_tier = tier + 1
                next_name = TOOL_TIER_NAMES[tool_type][next_tier - 1]
                levels_remaining, xp_remaining = (
                    self.tool_xp_remaining_to_next_tier(
                        level, xp, tool_type
                    )
                )
                await self.send(
                    f"Następny Tier: {next_tier}, {next_name}, "
                    f"od levelu {target_level}. "
                    f"Brakuje {levels_remaining} leveli i łącznie "
                    f"{xp_remaining} XP narzędzia."
                )

            await self.send(f"TIERY NARZĘDZIA: {name}.")
            for tier_number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                if tier_number < TOOL_MAX_TIER:
                    maximum = TOOL_TIER_THRESHOLDS[tier_number] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    if tool_type == "crafting":
                        level_text = (
                            f"level {minimum}-{TOOL_MAX_LEVEL}"
                        )
                    else:
                        level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"

                tier_bonus = int(
                    TOOL_TIER_BONUS_CHANCES[tier_number - 1] * 100
                )
                marker = " Obecny." if tier_number == tier else ""
                await self.send(
                    f"Tier {tier_number}: "
                    f"{TOOL_TIER_NAMES[tool_type][tier_number - 1]}. "
                    f"{level_text}. Bonus {tier_bonus} procent.{marker}"
                )

    async def show_tools(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            tools = [
                ("fishing", "fishing_rod", "Wędka", "Neris", "Szkoła Wędkarstwa"),
                ("mining", "pickaxe", "Kilof", "Toren", "Wejście do Kryształowej Jaskini"),
                ("woodcutting", "saw", "Piła", "Oren", "Leśniczówka"),
                ("crafting", "crafting_hammer", "Młot Rzemieślniczy", "Haldor", "Warsztat Rzemieślniczy"),
                ("cooking", "chef_knife", "Nóż Kucharski", "Marcel", "Kuchnia Błękitnego Płomienia"),
                ("herbalism", "herbalist_sickle", "Sierp Zielarski", "Sena", "Ogród Zielarski"),
                ("alchemy", "alchemy_mortar", "Moździerz Alchemiczny", "Orin", "Laboratorium Alchemiczne"),
                ("jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie", "Mirella", "Pracownia Jubilerska"),
                ("tailoring", "tailor_kit", "Zestaw Krawiecki", "Lysa", "Pracownia Krawiecka"),
                ("leatherworking", "tanning_knife", "Nóż Garbarski", "Soren", "Warsztat Kaletnika"),
                ("carpentry", "carpenter_tools", "Narzędzia Ciesielskie", "Edric", "Warsztat Ciesielski"),
                ("enchanting", "runic_focus", "Fokus Runiczny", "Kwatermistrz Arkanów", "Komnata Arkanów"),
            ]
            await self.send("NARZĘDZIA INFO" if detailed else "NARZĘDZIA")
            for tool_type, item_id, name, seller, location in tools:
                owned = self.server.db.item_qty(self.account_id, item_id) > 0
                if not owned:
                    if detailed:
                        await self.send(f"{name}: brak. Sprzedawca: {seller}, {location}.")
                    else:
                        await self.send(f"{name}: brak.")
                    continue
                row = self.server.db.tool(self.account_id, tool_type)
                level = int(row["level"])
                max_level = tool_max_level(tool_type)
                tier = tool_tier(level)
                tier_name = tool_tier_name(tool_type, level)
                if not detailed:
                    await self.send(
                        f"{name}: poziom {level}/{max_level}, Tier {tier}/{TOOL_MAX_TIER}: {tier_name}."
                    )
                    continue
                bonus_percent = int(tool_tier_bonus_chance(level) * 100)
                xp_text = (
                    "maksimum" if level >= max_level else
                    f"{row['xp']} z {self.tool_xp_to_next(level, tool_type)}"
                )
                if tier < TOOL_MAX_TIER:
                    next_text = f"Następny Tier od levelu {TOOL_TIER_THRESHOLDS[tier]}."
                else:
                    next_text = "Tier maksymalny."
                await self.send(
                    f"{name}: {tier_name}. Poziom {level}/{max_level}. Tier {tier}/{TOOL_MAX_TIER}. "
                    f"XP {xp_text}. Użycia {row['uses']}. "
                    f"{self.tool_action_label(tool_type)}: {self.profession_action_seconds(tool_type, self.profession_level_for_tool(tool_type))} sekund "
                    f"(tempo z {profession_for_tool_type(tool_type)}). "
                    f"{self.tool_bonus_label(tool_type)}: {bonus_percent} procent. {next_text} "
                    f"Sprzedawca: {seller}, {location}."
                )
            if detailed:
                await self.send(
                    "Każde narzędzie sprzedaje wyłącznie NPC własnej profesji. Narzędzia nie mają durability."
                )
            else:
                await self.send("Wpisz narzedzia info po XP, bonusy, czas akcji i sprzedawców.")

    def fishing_water_type(self, room_id=None):
            room_id = room_id or self.character.room_id
            if room_id not in FISHING_ROOMS:
                return None
            if room_id in FISHING_WATER_TYPE_OVERRIDES:
                return FISHING_WATER_TYPE_OVERRIDES[room_id]
            dungeon, _floor = profession_dungeon_floor(room_id)
            if dungeon == "sunken_grotto":
                return "Zatopiona grota"
            if room_id in RIVER_FISHING_ROOMS:
                return "Rzeka"
            if room_id in LAKE_FISHING_ROOMS:
                return "Jezioro"
            if room_id in SEA_FISHING_ROOMS:
                return "Morze"
            if room_id in OCEAN_FISHING_ROOMS:
                return "Ocean"
            return "Łowisko"

    def fishing_habitat(self, room_id=None):
            room_id = room_id or self.character.room_id
            if room_id in RIVER_FISHING_ROOMS: return "river"
            if room_id in LAKE_FISHING_ROOMS: return "lake"
            if room_id in SEA_FISHING_ROOMS: return "sea"
            if room_id in OCEAN_FISHING_ROOMS: return "ocean"
            return None

    def fishing_available_pool(self, tool_level, habitat=None):
            habitat = habitat or self.fishing_habitat()
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            access_level = tool_tier_access_level(tool_level)
            habitat_ids = {
                "river": tuple(RIVER_FISH_ATLAS),
                "lake": tuple(LAKE_FISH_ATLAS),
                "sea": tuple(SEA_FISH_ATLAS),
                "ocean": tuple(OCEAN_FISH_ATLAS),
            }.get(habitat, ())
            return generator_core_v027.resource_pool(
                habitat_ids, ITEMS, access_level, f"fishing:{habitat or 'unknown'}"
            )

    def fishing_ecology_pool(self, tool_level, habitat=None, room_id=None):
            room_id = room_id or self.character.room_id
            habitat = habitat or self.fishing_habitat(room_id)
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            if not habitat:
                return ()
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective_level = tool_level
            if dungeon == "sunken_grotto":
                effective_level = min(tool_level, max(1, int(dungeon_floor) * 10))
            # v0.30.39: ekologia łowiska nie wycina już odblokowanych gatunków.
            # Pula zawsze pozostaje kumulacyjna; preferencje wpływają tylko na wagę.
            return tuple(self.fishing_available_pool(effective_level, habitat))

    def fishing_loot(self, tool_level, habitat="river"):
            room_id = self.character.room_id
            pool = self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=room_id)
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(
                pool, ITEMS, tool_level, f"fishing:{habitat}:{room_id}"
            )
            preferred = FISHING_ECOLOGY_PREFERRED_IDS.get(room_id) or set()
            if preferred:
                # Typowe gatunki danego stanowiska są częstsze, ale żaden wcześniej
                # odblokowany gatunek tego habitatu nie dostaje wagi 0.
                weights = [
                    float(weight) * (2.75 if item_id in preferred else 1.0)
                    for item_id, weight in zip(pool, weights)
                ]
            return random.choices(pool, weights=weights, k=1)[0]

    async def show_water_info(self):
            habitat = self.fishing_habitat()
            water_type = self.fishing_water_type()
            if not habitat or not water_type:
                await self.send(
                    "Tutaj nie ma łowiska. Komenda woda działa tylko w miejscu, "
                    "w którym można łowić."
                )
                return

            tool = self.server.db.tool(self.account_id, "fishing")
            tool_level = int(tool["level"])
            pool = tuple(self.fishing_ecology_pool(tool_level, habitat=habitat, room_id=self.character.room_id))
            room = ROOMS.get(self.character.room_id, {})
            await self.send(
                f"ŁOWISKO: {water_type}. Lokacja: {room.get('name') or 'Nieznana lokacja'}."
            )
            await self.send(
                f"Ekosystem ryb: {FISHING_HABITAT_LABELS.get(habitat, habitat)}. "
                f"Wędka poziom {tool_level}, Tier {tool_tier(tool_level)}. "
                f"Dostępnych teraz gatunków: {len(pool)}."
            )

            known = self.server.db.fish_journal_ids(self.account_id)
            pool_species = {base_fish_species_id(item_id) for item_id in pool}
            known_here = sorted(
                pool_species & known,
                key=lambda item_id: normalize_lookup_text(ITEMS[item_id]["name"]),
            )
            unknown_count = max(0, len(pool_species) - len(known_here))
            await self.send(
                f"Dziennik ryb w tym łowisku: odkryte {len(known_here)}, "
                f"nieodkryte {unknown_count}."
            )
            if known_here:
                await self.send(
                    "Znane gatunki tutaj: "
                    + ", ".join(ITEMS[item_id]["name"] for item_id in known_here)
                    + "."
                )

            habitat_ids = {
                "river": tuple(RIVER_FISH_ATLAS), "lake": tuple(LAKE_FISH_ATLAS),
                "sea": tuple(SEA_FISH_ATLAS), "ocean": tuple(OCEAN_FISH_ATLAS),
            }.get(habitat, ())
            locked = sorted(
                (int(ITEMS[iid].get("generator_level", 1) or 1), iid)
                for iid in habitat_ids if iid in ITEMS
                if int(ITEMS[iid].get("generator_level", 1) or 1) > tool_tier_access_level(tool_level)
            )
            if locked:
                next_level, next_item = locked[0]
                await self.send(
                    f"Kolejny gatunek wymaga wyższego Tieru Wędki; "
                    f"najbliższy próg zasobu to poziom {next_level}: {ITEMS[next_item]['name']}."
                )
            else:
                await self.send("Masz odblokowane wszystkie ryby tego ekosystemu.")

            await self.send(
                "Ryby nie mają twardego limitu sztuk. Łowisko nie wyczerpuje się od łowienia."
            )

    async def show_fish_journal(self, args=""):
            rows = self.server.db.fish_journal_rows(self.account_id)
            query = self.normalize_description_query(args)
            if not query:
                discovered = len(rows)
                legendary = sum(
                    1 for row in rows
                    if fish_species_rarity(str(row["fish_id"])) == "legendary"
                )
                total_caught = sum(max(0, int(row["caught_count"] or 0)) for row in rows)
                await self.send(
                    f"DZIENNIK RYB: odkryte gatunki {discovered} z {len(FISH_RESOURCE_IDS)}. "
                    f"Zarejestrowane połowy {total_caught}. Legendarne gatunki {legendary}."
                )
                await self.send(
                    "Wpisz dziennikryb lista, aby przeczytać odkryte gatunki, "
                    "albo dziennikryb <nazwa ryby>, aby sprawdzić rekordy."
                )
                return

            if query in ("lista", "list", "all", "wszystkie"):
                if not rows:
                    await self.send("Dziennik ryb jest pusty. Złów pierwszy gatunek.")
                    return
                ordered = sorted(
                    rows,
                    key=lambda row: normalize_lookup_text(
                        ITEMS.get(str(row["fish_id"]), {}).get("name", str(row["fish_id"]))
                    ),
                )
                await self.send(f"ODKRYTE GATUNKI RYB: {len(ordered)}.")
                for row in ordered:
                    fish_id = str(row["fish_id"])
                    name = ITEMS.get(fish_id, {}).get("name", fish_id)
                    rarity = fish_rarity_label(fish_id)
                    count = max(0, int(row["caught_count"] or 0))
                    best_l = max(0, int(row["best_length_mm"] or 0))
                    best_w = max(0, int(row["best_weight_g"] or 0))
                    if best_l > 0 and best_w > 0:
                        record = (
                            f" Rekord: {format_fish_length(best_l)}, "
                            f"{format_fish_weight(best_w)}."
                        )
                    else:
                        record = " Rekord rozmiaru od v0.9.5 jeszcze nie zapisany."
                    await self.send(
                        f"{name}. Rzadkość: {rarity}. Złowiono {count}.{record}"
                    )
                return

            candidates = {
                fish_id: {"name": ITEMS.get(fish_id, {}).get("name", fish_id)}
                for fish_id in FISH_RESOURCE_IDS
                if fish_id in ITEMS
            }
            found = find_by_name(candidates, args)
            if not found:
                await self.send("Nie znam takiego gatunku ryby.")
                return
            fish_id, fish = found
            row = self.server.db.fish_journal_entry(self.account_id, fish_id)
            if not row:
                await self.send(
                    f"{fish['name']}: gatunek jeszcze nieodkryty w Dzienniku ryb."
                )
                return
            habitats = fish_species_habitats(fish_id)
            habitat_text = ", ".join(habitats) if habitats else "specjalne łowisko"
            best_l = max(0, int(row["best_length_mm"] or 0))
            best_w = max(0, int(row["best_weight_g"] or 0))
            await self.send(
                f"{fish['name']}. Rzadkość: {fish_rarity_label(fish_id)}. "
                f"Złowiono {int(row['caught_count'] or 0)}. Wody: {habitat_text}."
            )
            if best_l > 0 or best_w > 0:
                await self.send(
                    f"Rekord długości: {format_fish_length(best_l)}. "
                    f"Rekord masy: {format_fish_weight(best_w)}."
                )
            else:
                await self.send(
                    "Gatunek pochodzi ze starszego zapisu; rekord długości i masy "
                    "zacznie się od pierwszego połowu w v0.9.5."
                )

    def mining_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            floor = mine_floor_number(room_id)
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            if dungeon == "crystal_mine":
                floor = min(TOOL_MAX_LEVEL, max(1, int(dungeon_floor) * 10))
            tool_access_level = tool_tier_access_level(tool_level)
            effective_level = tool_access_level if floor is None else min(tool_access_level, max(1, int(floor)))
            # v0.34.4: progi wydobycia są autorską semantyką gry i muszą
            # pochodzić z ORE_ATLAS_LEVELS / ORE_MINE_FLOOR_MINIMUMS.
            # Generator Core może balansować liczby i wagi, ale nie może
            # przesuwać odblokowań zasobów przez generator_level przedmiotu.
            pool = []
            for ore_id in ORE_RESOURCE_IDS:
                if ore_id not in ITEMS:
                    continue
                need_tool = int(ORE_ATLAS_LEVELS.get(ore_id, 1) or 1)
                if tool_access_level < need_tool:
                    continue
                if floor is not None:
                    need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(ore_id, need_tool) or need_tool)
                    if int(floor) < need_floor:
                        continue
                pool.append(ore_id)
            if not pool:
                return None
            pool = tuple(sorted(pool, key=lambda iid: (int(ORE_ATLAS_LEVELS.get(iid, 1) or 1), iid)))
            weights = mining_ore_weights(
                pool, effective_level, f"mining:{room_id}"
            )
            return random.choices(pool, weights=weights, k=1)[0]

    def mining_gem_drop(self, tool_level, profession_level, room_id=None):
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            profession_level = max(1, min(PROFESSION_MAX_LEVEL, int(profession_level)))
            room_id = room_id or self.character.room_id
            floor = mine_floor_number(room_id)
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            if dungeon == "crystal_mine":
                floor = min(TOOL_MAX_LEVEL, max(1, int(dungeon_floor) * 10))
            # v0.30.26: rodzaj surowego klejnotu zależy od Tieru Kilofa.
            # Górnictwo nadal wpływa na jakość/szansę, ale nie odblokowuje
            # nowych rodzajów klejnotów pomiędzy progami Tieru narzędzia.
            effective = tool_tier_access_level(tool_level)
            if floor is not None:
                effective = min(effective, max(1, int(floor)))
            base_gems = tuple(
                iid for iid, item in ITEMS.items()
                if item.get("type") == "gem_raw" and not item.get("gem_quality")
            )
            pool = generator_core_v027.resource_pool(
                base_gems, ITEMS, effective, f"gems:{room_id}"
            )
            gem_skill = min(tool_level, profession_level)
            chance = min(0.18, 0.035 + 0.11 * (gem_skill / float(PROFESSION_MAX_LEVEL)))
            chance *= 0.85 + 0.30 * generator_core_v027.stable_unit(f"gems:{room_id}")
            if not pool or random.random() >= chance:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"gems:{room_id}")
            base_id = random.choices(pool, weights=weights, k=1)[0]
            quality = roll_mined_gem_quality(tool_level, profession_level)
            if quality and quality != "normal":
                candidate = f"{base_id}_{quality}"
                if candidate in ITEMS:
                    return candidate
            return base_id

    def woodcutting_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective = tool_tier_access_level(tool_level)
            if dungeon == "ancient_forest":
                effective = min(effective, max(1, int(dungeon_floor) * 10))
            pool = generator_core_v027.resource_pool(
                tuple(WOOD_RESOURCE_IDS), ITEMS, effective, f"wood:{room_id}"
            )
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"wood:{room_id}")
            return random.choices(pool, weights=weights, k=1)[0]

    def herbalism_loot(self, tool_level, room_id=None):
            room_id = room_id or self.character.room_id
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            dungeon, dungeon_floor = profession_dungeon_floor(room_id)
            effective = tool_tier_access_level(tool_level)
            if dungeon == "alchemy_garden":
                effective = min(effective, max(1, int(dungeon_floor) * 10))
            pool = generator_core_v027.resource_pool(
                tuple(HERB_RESOURCE_IDS), ITEMS, effective, f"herb:{room_id}"
            )
            if not pool:
                return None
            weights = generator_core_v027.resource_weights(pool, ITEMS, effective, f"herb:{room_id}")
            return random.choices(pool, weights=weights, k=1)[0]
