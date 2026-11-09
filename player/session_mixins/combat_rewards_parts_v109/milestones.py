# -*- coding: utf-8 -*-
"""Oryginalne metody wydzielone w v109 bez zmiany algorytmow."""
from __future__ import annotations
import random
from data.items import ITEMS
from systems.equipment_crafting import LEGENDARY_CLASS_RELIC_BY_CLASS_TIER,LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER
from world.economy_quests import legendary_loot_mastery_for_floor,milestone_boss_tier

class CombatMilestoneV109Mixin:
    def class_for_milestone_loot(self):
                active = self.active_class_names()
                if active:
                    return active[0]
                return self.character.class_name

    async def grant_milestone_boss_loot(self, template, floor):
                marker = milestone_boss_tier(floor)
                if not marker:
                    return
                class_name = self.class_for_milestone_loot()
                if class_name not in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER:
                    return
                mastery = legendary_loot_mastery_for_floor(floor)
                set_pool = list(LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER[class_name][mastery])
                discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
                missing = [item_id for item_id in set_pool if item_id not in discovered_eq]
                set_item = random.choice(missing or set_pool)
                self.server.db.add_item(self.account_id, set_item, 1)
                await self.record_item_collection(
                    set_item, source=template.get("name", "Boss kamienia milowego"), announce=True
                )
                boss_id = str(template.get("template_id") or "")
                if boss_id:
                    self.server.db.add_boss_codex_drop(self.account_id, boss_id, set_item)
                await self.send(
                    f"Loot setowy klasy {class_name}: {ITEMS[set_item]['name']}. "
                    f"Wymaga Biegłości {mastery}."
                )
                if marker == 100:
                    relic_id = LEGENDARY_CLASS_RELIC_BY_CLASS_TIER[class_name][mastery]
                    self.server.db.add_item(self.account_id, relic_id, 1)
                    await self.record_item_collection(
                        relic_id, source=template.get("name", "Boss setnego piętra"), announce=True
                    )
                    if boss_id:
                        self.server.db.add_boss_codex_drop(self.account_id, boss_id, relic_id)
                    await self.send(
                        f"Legendarny loot klasy {class_name}: {ITEMS[relic_id]['name']}. "
                        f"Wymaga Biegłości {mastery}."
                    )

