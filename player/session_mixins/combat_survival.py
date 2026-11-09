# -*- coding: utf-8 -*-
"""Combat escape and player-death handling.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from events.contracts import PlayerDiedEvent
from systems.monster_magic import monster_magic_clear_v1151
from systems.combat_profile_records import (
    death_cause_text_v11341,
    record_combat_profile_v11341,
)

from .combat_survival_parts_v109 import CombatEscapeV109Mixin, CombatDeathV109Mixin

class SessionCombatSurvivalMixin(CombatEscapeV109Mixin, CombatDeathV109Mixin):
    pass


