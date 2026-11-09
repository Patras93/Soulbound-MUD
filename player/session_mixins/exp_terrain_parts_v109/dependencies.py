# -*- coding: utf-8 -*-
"""EXP area recommendations and terrain information."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import re
from core.classes_skills import ROOMS
from core.mines_threat import (
    DYNAMIC_KILL_XP_MAX_MULTIPLIER,
    DYNAMIC_KILL_XP_MIN_MULTIPLIER,
    EXP_AREA_BASE_CATEGORY,
    EXP_AREA_TARGET_POWER,
    EXP_ZONE_AREA_ID,
    ITEMS,
    v0866_room_threat_profile,
    v0866_threat_label,
    v0866_zone_threat_profile,
)
from core.progression_600 import CHARACTER_MAX_LEVEL, SOUL_MAX_LEVEL
from core.progression_resources import FISHING_ROOMS, HERBALISM_ROOMS, WOODCUTTING_ROOMS, is_mining_room, v0190_mob_stage
from systems.content_registry import MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from world.dynamic_content import EXP_AREAS



# Jawny eksport wspólnych globali, w tym pomocniczych nazw z podkreślnikiem.
__all__ = tuple(k for k in globals() if not k.startswith("__"))
