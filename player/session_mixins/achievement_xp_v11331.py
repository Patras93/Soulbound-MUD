# -*- coding: utf-8 -*-
"""v113.00.31: atomic, one-time category XP for actual achievement unlocks."""
from __future__ import annotations

from world.dynamic_content import ACHIEVEMENT_TRACKS, ACHIEVEMENT_TITLE_REWARDS
from systems.achievement_rewards_v11331 import award_achievement_experience_v11331
from systems.v115.optional_sound import (
    sound_reward_queue_checkpoint_v11329, sound_reward_queue_rollback_v11329,
)


class SessionAchievementXpV11331Mixin:
    async def check_achievement_tiers(self, metric, value):
        definition = ACHIEVEMENT_TRACKS.get(metric)
        if definition is None:
            return
        value = max(0, int(value))
        for threshold, tier in definition['tiers']:
            if value < int(threshold):
                continue
            achievement_id = f'{metric}:{tier.lower()}'
            db = self.server.db
            account_id = self.account_id
            # One SQLite transaction: new achievement + all the actual EXP
            # axes. The original method remains in the historical Mixin for
            # source/AST compatibility. Previously unlocked tiers pay nothing.
            old_character = dict(vars(self.character)) if self.character is not None else None
            checkpoint = sound_reward_queue_checkpoint_v11329(db, account_id)
            try:
                with db.conn.deferred_commits():
                    is_new = db.unlock_achievement(
                        account_id, achievement_id, definition['name'], tier)
                    rewards = (award_achievement_experience_v11331(self, metric, tier)
                               if is_new else [])
            except BaseException:
                if old_character is not None:
                    vars(self.character).clear()
                    vars(self.character).update(old_character)
                sound_reward_queue_rollback_v11329(db, account_id, checkpoint)
                raise
            if is_new:
                await self.send(f"Osiągnięcie: {definition['name']}, {tier}.")
                if rewards:
                    await self.send('Nagroda EXP: ' + ', '.join(rewards) + '.')
                reward_title = ACHIEVEMENT_TITLE_REWARDS.get((metric, tier))
                if reward_title:
                    await self.unlock_title(f'achievement:{achievement_id}', reward_title)
