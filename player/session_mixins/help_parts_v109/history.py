# -*- coding: utf-8 -*-
"""Oryginalne metody wydzielone w v109 bez zmiany algorytmow."""
# -*- coding: utf-8 -*-
"""HELP, changelog and skill help."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import os
from difflib import get_close_matches
from core.classes_skills import effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import skill_xp_to_next
from player.session_mixins.exploration_progress import ALL_EXPLORATION_ROOMS, ROOMS, normalize_lookup_text
from player.session_mixins.io_auth_character import CLASS_SKILLS
from player.session_mixins.museum_bounty import BESTIARY_CATALOG
from storage.db_schema import FISH_RESOURCE_IDS
from systems.content_registry import LATEST_CHANGES, LATEST_CHANGES_TITLE
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES
from world.world_state import _FINAL_SKILL_HELP_EXACT_INDEX, _FINAL_SKILL_HELP_SEARCH_ROWS



class HelpHistoryV109Mixin:
    async def show_lifetime_statistics(self):
            stats = self.server.db.lifetime_stats(self.account_id)
            # Pola, które mają już starsze trwałe źródło, są synchronizowane w górę
            # przy odczycie. Chroni to save'y po ręcznych migracjach i nie dubluje danych.
            deaths = max(stats.get("deaths", 0), int(self.character.deaths or 0))
            self.server.db.set_lifetime_stat_max(self.account_id, "deaths", deaths)
            explored = len(self.server.db.discovered_room_ids(self.account_id))
            self.server.db.set_lifetime_stat_max(self.account_id, "rooms_discovered", explored)
            bestiary_rows = self.server.db.bestiary_rows(self.account_id)
            unique_bestiary = len({str(row["mob_template_id"]) for row in bestiary_rows})
            self.server.db.set_lifetime_stat_max(self.account_id, "bestiary_unique", unique_bestiary)
            stats = self.server.db.lifetime_stats(self.account_id)

            await self.send(f"HISTORIA POSTACI: {self.character.name}.")
            await self.send(
                "Walka: zwycięstwa "
                f"{stats.get('combat_victories', 0)}, zabite moby {stats.get('kills_total', 0)}, "
                f"bossowie {stats.get('boss_kills', 0)}, rare moby {stats.get('rare_kills', 0)}, "
                f"śmierci {stats.get('deaths', 0)}."
            )
            await self.send(
                "Zadania: ukończone questy "
                f"{stats.get('quests_completed', 0)}, ukończone kontrakty {stats.get('bounties_completed', 0)}."
            )
            await self.send(
                "Profesje: akcje łącznie "
                f"{stats.get('profession_actions', 0)}, craftingi {stats.get('craft_actions', 0)}, "
                f"wytworzone przedmioty {stats.get('crafted_items', 0)}."
            )
            await self.send(
                "Zbiory od v0.9.4: ryby "
                f"{stats.get('fish_caught', 0)}, rudy i minerały {stats.get('ore_mined', 0)}, "
                f"drewno {stats.get('wood_gathered', 0)}, zioła {stats.get('herbs_gathered', 0)}, "
                f"klejnoty {stats.get('gems_found', 0)}."
            )
            await self.send(
                f"Świat: odkryte lokacje {stats.get('rooms_discovered', 0)} z {len(ALL_EXPLORATION_ROOMS)}, "
                f"Bestiariusz {stats.get('bestiary_unique', 0)} z {len(BESTIARY_CATALOG)}, "
                f"rzadkie ryby {stats.get('rare_fish_caught', 0)}."
            )
            await self.send(
                f"Wędkarstwo v0.9.5: odkryte gatunki {stats.get('fish_species_discovered', 0)} z {len(FISH_RESOURCE_IDS)}, "
                f"legendarne połowy {stats.get('legendary_fish_caught', 0)}, "
                f"nowe rekordy {stats.get('fish_record_updates', 0)}."
            )
            await self.send(
                "Starsze pewne dane zostały odtworzone z zapisów gry. Dokładne ilości sztuk "
                "ryb, rud, drewna, ziół i wytworzonych przedmiotów są liczone od v0.9.4."
            )

    def full_changelog_lines(self):
            module_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = (
                os.path.join(module_dir, "CHANGELOG_PL.txt"),
                os.path.join(os.getcwd(), "CHANGELOG_PL.txt"),
            )

            for changelog_path in candidates:
                try:
                    if not os.path.exists(changelog_path):
                        continue
                    with open(changelog_path, "r", encoding="utf-8") as handle:
                        lines = [line.rstrip("\r\n") for line in handle]
                    if any(line.strip() for line in lines):
                        return lines
                except (OSError, UnicodeError):
                    continue

            lines = [LATEST_CHANGES_TITLE]
            lines.extend("- " + line for line in LATEST_CHANGES)
            return lines

