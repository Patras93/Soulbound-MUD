# -*- coding: utf-8 -*-
"""Zgodna fasada v109; oryginalne nazwy metod i API zachowane."""
from __future__ import annotations
from .sky_parts_v109.dependencies import *
from .sky_parts_v109 import (
    SkySummonStateV109Mixin,
    SkyCompanionHealingV109Mixin,
    SkySummonCommandsV109Mixin,
    SkySummonSpecializationsV109Mixin,
    SkySummonCombatV109Mixin,
    SkyCitiesClassesV109Mixin,
)

class SessionSkyV1700Mixin(
    SkySummonStateV109Mixin,
    SkyCompanionHealingV109Mixin,
    SkySummonCommandsV109Mixin,
    SkySummonSpecializationsV109Mixin,
    SkySummonCombatV109Mixin,
    SkyCitiesClassesV109Mixin,
    SessionChaosV1800Mixin,
):
    """Zachowuje stary interfejs klasy, metody dziedziczone bez zmian."""
    pass
