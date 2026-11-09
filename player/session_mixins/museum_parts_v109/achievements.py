# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — achievements. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumAchievementsV109Mixin:
    def loot_message_allowed(self, item_id):
            return loot_filter_allows(self.character.loot_filter, item_id)

    async def unlock_title(self, title_id, title_name, announce=True):
            is_new = self.server.db.unlock_title(
                self.account_id, title_id, title_name
            )
            if is_new and announce:
                await self.send(f"Nowy tytuł: {title_name}.")
            return is_new

    async def check_achievement_tiers(self, metric, value):
            definition = ACHIEVEMENT_TRACKS.get(metric)
            if not definition:
                return
            value = max(0, int(value))
            for threshold, tier in definition["tiers"]:
                if value < int(threshold):
                    continue
                achievement_id = f"{metric}:{tier.lower()}"
                if self.server.db.unlock_achievement(
                    self.account_id,
                    achievement_id,
                    definition["name"],
                    tier,
                ):
                    await self.send(
                        f"Osiągnięcie: {definition['name']}, {tier}."
                    )
                    reward_title = ACHIEVEMENT_TITLE_REWARDS.get((metric, tier))
                    if reward_title:
                        await self.unlock_title(
                            f"achievement:{achievement_id}", reward_title
                        )

    async def advance_achievement(self, metric, amount=1):
            if metric not in ACHIEVEMENT_TRACKS:
                return
            value = self.server.db.add_achievement_metric(
                self.account_id, metric, amount
            )
            await self.check_achievement_tiers(metric, value)

    async def set_achievement_progress(self, metric, value):
            if metric not in ACHIEVEMENT_TRACKS:
                return
            value = self.server.db.set_achievement_metric_max(
                self.account_id, metric, value
            )
            await self.check_achievement_tiers(metric, value)

    def current_rare_fish_stock(self):
            return sum(
                int(row["quantity"])
                for row in self.server.db.storage_rows(self.account_id, "net")
                if str(row["item_id"]) in RARE_FISH_VARIANT_IDS
            )

    def current_gem_stock(self):
            total = sum(
                int(row["quantity"])
                for row in self.server.db.storage_rows(self.account_id, "bag")
                if str(row["item_id"]) in RAW_GEM_IDS
            )
            total += sum(
                int(row["quantity"])
                for row in self.server.db.inventory(self.account_id)
                if str(row["item_id"]) in RAW_GEM_IDS or str(row["item_id"]) in CUT_GEM_IDS
            )
            return total

    async def sync_extended_achievements(self):
            # Rekonstruowalne metryki są synchronizowane z rzeczywistym trwałym stanem.
            await self.set_achievement_progress(
                "exploration_rooms",
                len(self.server.db.discovered_room_ids(self.account_id).intersection(ALL_EXPLORATION_ROOMS)),
            )
            masters = 0
            transcendents = 0
            for profession in dict.fromkeys(TOOL_PROFESSION_MAP.values()):
                row = self.server.db.profession(self.account_id, profession)
                level = int(row["level"])
                # Historyczny milestone v0.9.3 pozostaje przy 200 mimo rozszerzenia capu do 400.
                if level >= 200:
                    masters += 1
                if level >= profession_max_level(profession):
                    transcendents += 1
            await self.set_achievement_progress("profession_masters", masters)
            await self.set_achievement_progress("profession_transcendents", transcendents)
            bestiary_ids = {str(row["mob_template_id"]) for row in self.server.db.bestiary_rows(self.account_id)}
            await self.set_achievement_progress(
                "bestiary_unique", len(bestiary_ids.intersection(BESTIARY_CATALOG))
            )
            await self.set_achievement_progress(
                "multiclass_classes", len(self.active_class_names())
            )
            await self.set_achievement_progress("soul_level", self.character.soul_level)
            await self.set_achievement_progress("rare_fish_caught", self.current_rare_fish_stock())
            await self.set_achievement_progress("gems_found", self.current_gem_stock())
            bounty_state = self.server.db.bounty_board_state(self.account_id)
            await self.set_achievement_progress(
                "bounties_completed", bounty_state.get("completed_count", 0)
            )
            await self.sync_mastery_achievements_v0925()

    async def check_all_minibosses_achievement(self):
            if not MINI_BOSS_IDS:
                return
            discovered = self.server.db.collection_entry_ids(
                self.account_id, "bosses"
            )
            if not MINI_BOSS_IDS.issubset(discovered):
                return
            achievement_id = "all_minibosses"
            if self.server.db.unlock_achievement(
                self.account_id,
                achievement_id,
                "Wszystkie Mini-Bossy",
                "Platinum",
            ):
                await self.send("Osiągnięcie: Wszystkie Mini-Bossy, Platinum.")
                await self.unlock_title(
                    "achievement:all_minibosses", "Pogromca Mini-Bossów"
                )
