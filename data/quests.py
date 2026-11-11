# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from config.balance import BLACKSMITH_QUEST_COOLDOWN_SECONDS, QUEST_REPEAT_COOLDOWN_SECONDS

from world.quests.base_01 import build_catalog as _quests_01
from world.quests.base_02 import build_catalog as _quests_02
from world.quests.base_03 import build_catalog as _quests_03

QUESTS = {}
QUESTS.update(_quests_01())
QUESTS.update(_quests_02())
QUESTS.update(_quests_03())

__all__ = ['QUESTS']
