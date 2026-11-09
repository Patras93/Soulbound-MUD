# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from config.balance import BLACKSMITH_QUEST_COOLDOWN_SECONDS, QUEST_REPEAT_COOLDOWN_SECONDS

from data.catalogs_v109.quests_01 import build_catalog as _quests_01
from data.catalogs_v109.quests_02 import build_catalog as _quests_02
from data.catalogs_v109.quests_03 import build_catalog as _quests_03

QUESTS = {}
QUESTS.update(_quests_01())
QUESTS.update(_quests_02())
QUESTS.update(_quests_03())

__all__ = ['QUESTS']
