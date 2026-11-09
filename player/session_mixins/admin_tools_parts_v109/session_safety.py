# -*- coding: utf-8 -*-
"""v109: oryginalne metody administratora, niezmieniona logika i uprawnienia."""
from __future__ import annotations

class AdminSessionSafetyV109Mixin:
    async def prepare_character_wipe(self):
            """Wyczyść stan sesyjny bez zapisywania usuwanej postaci."""
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            for task_name in ("rest_task", "auto_fishing_task", "auto_mining_task", "auto_woodcutting_task", "auto_herbalism_task", "combat_task"):
                task = getattr(self, task_name, None)
                if task and not task.done():
                    task.cancel()
                setattr(self, task_name, None)
            self.resting = False
            self.auto_fishing = self.auto_mining = self.auto_woodcutting = self.auto_herbalism = False
            if self.character:
                await self.leave_party(announce=False)
            self.combat_mob_key = None
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0

    async def unlock_context(self, args=""):
            q = self.normalize_description_query(args)
            if q in ("max", "dusza max", "soul max", "bron duszy max", "broń duszy max"):
                await self.unlock(multi=True)
                return
            if q in ("soul", "dusza", "bron duszy", "broń duszy"):
                await self.unlock()
                return
            if self.boss_floor_chest_here() is not None:
                await self.unlock_boss_floor_chest()
                return
            await self.unlock()

