# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.combatskills_part01 as _sb420_src_01
# SessionCombatSkillsMixin.combat_skill_mana_cost_v11191 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.offensive_skill_damage_type_v11190 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.offensive_skill_effective_stat_value_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.offensive_skill_core_stat_power_v11188 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.offensive_skill_core_power_v11185 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.healing_skill_build_multiplier_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.healing_skill_amount_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.regen_tick_power_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.apply_satellite_linker_round_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.apply_active_regen_round_v11196 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.offensive_skill_damage_multiplier_v11186 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.apply_superboss_helper_after_skill_v11192 -> player/session_methods_v4200/combatskills_part01.py
# SessionCombatSkillsMixin.handle_aoe_setting_v11120 -> player/session_methods_v4200/combatskills_part01.py
import player.session_methods_v4200.combatskills_part02 as _sb420_src_02
# SessionCombatSkillsMixin.use_class_skill -> player/session_methods_v4200/combatskills_part02.py

# -*- coding: utf-8 -*-
"""Class-skill execution for Soulbound combat.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import random
import time

from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
from systems.party_synergies import (
    party_synergy_damage_multiplier_v11338,
    party_synergy_healing_multiplier_v11338,
    party_synergy2_apply_hit_v11339,
)
from systems.elemental_combat import skill_element_v11339
from systems.soul_ancients_v1330 import evolution_power_multiplier
from systems.soul_evolutions_v1332 import role_evolution
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import class_type_for_name, skill_power_multiplier
from core.bootstrap_economy_professions import GLOBAL_SKILL_BUFF_DURATION_SECONDS
from core.player_math import (
    character_attribute_power,
    character_offensive_build_multiplier,
    mec_vmax_duration_seconds,
)
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from network.protocol_gameplay_utils import normalize_lookup_text
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.economy_quests import v0863_execute_threshold
from world.uoss_superboss_runtime import superboss_attack_gate_v11137, superboss_helper_profile_v11137

class SessionCombatSkillsMixin:
    def combat_skill_mana_cost_v11191(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method combat_skill_mana_cost_v11191")

    def offensive_skill_damage_type_v11190(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method offensive_skill_damage_type_v11190")

    def offensive_skill_effective_stat_value_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method offensive_skill_effective_stat_value_v11196")

    def offensive_skill_core_stat_power_v11188(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method offensive_skill_core_stat_power_v11188")

    def offensive_skill_core_power_v11185(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method offensive_skill_core_power_v11185")

    def healing_skill_build_multiplier_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method healing_skill_build_multiplier_v11196")

    def healing_skill_amount_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method healing_skill_amount_v11196")

    def regen_duration_seconds_v11196(self, skill_level):
        """Soulbound adaptation for source-defined 'short period' Regen duration.

        UOSS supplies no seconds. Keep the existing 30-second buff scale as the
        low-level anchor and extend it to 90 seconds at Skill Level 600.
        This is Soulbound balance, not a claimed UOSS number.
        """
        level=max(1,min(SKILL_MAX_LEVEL,int(skill_level)))
        progress=(level-1)/float(max(1,SKILL_MAX_LEVEL-1))
        return max(1,int(round(30.0+60.0*(progress ** 0.82))))

    def regen_tick_power_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method regen_tick_power_v11196")

    def satellite_linker_duration_rounds_v11196(self, skill_level, skill):
        """Explicit Soulbound duration adaptation for source-defined short duration."""
        level=max(1,min(SKILL_MAX_LEVEL,int(skill_level)))
        progress=(level-1)/float(max(1,SKILL_MAX_LEVEL-1))
        start=max(1,int(skill.get("soulbound_duration_rounds_level1",3) or 3))
        end=max(start,int(skill.get("soulbound_duration_rounds_level600",8) or 8))
        return max(1,int(round(start+(end-start)*(progress ** 0.82))))

    async def apply_satellite_linker_round_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method apply_satellite_linker_round_v11196")

    async def apply_active_regen_round_v11196(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method apply_active_regen_round_v11196")

    def offensive_skill_damage_multiplier_v11186(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method offensive_skill_damage_multiplier_v11186")

    async def apply_superboss_helper_skill_damage_v11189(self, target):
        """Legacy hook: active helpers now act once per boss round, not per skill."""
        return 0

    async def apply_superboss_helper_after_skill_v11192(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method apply_superboss_helper_after_skill_v11192")

    def offensive_aoe_enabled_v11120(self):
        row = self.server.db.conn.execute(
            "SELECT offensive_aoe_enabled FROM player_combat_settings_v11120 WHERE account_id=?",
            (self.account_id,),
        ).fetchone()
        return True if row is None else bool(row["offensive_aoe_enabled"])

    async def handle_aoe_setting_v11120(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method handle_aoe_setting_v11120")

    async def use_class_skill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_class_skill")

# v4.20.0: exact historical implementations rebound onto original class.
SessionCombatSkillsMixin.combat_skill_mana_cost_v11191 = _sb420_bind(_sb420_src_01.combat_skill_mana_cost_v11191, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.offensive_skill_damage_type_v11190 = _sb420_bind(_sb420_src_01.offensive_skill_damage_type_v11190, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.offensive_skill_effective_stat_value_v11196 = _sb420_bind(_sb420_src_01.offensive_skill_effective_stat_value_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.offensive_skill_core_stat_power_v11188 = _sb420_bind(_sb420_src_01.offensive_skill_core_stat_power_v11188, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.offensive_skill_core_power_v11185 = _sb420_bind(_sb420_src_01.offensive_skill_core_power_v11185, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.healing_skill_build_multiplier_v11196 = _sb420_bind(_sb420_src_01.healing_skill_build_multiplier_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.healing_skill_amount_v11196 = _sb420_bind(_sb420_src_01.healing_skill_amount_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.regen_tick_power_v11196 = _sb420_bind(_sb420_src_01.regen_tick_power_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.apply_satellite_linker_round_v11196 = _sb420_bind(_sb420_src_01.apply_satellite_linker_round_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.apply_active_regen_round_v11196 = _sb420_bind(_sb420_src_01.apply_active_regen_round_v11196, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.offensive_skill_damage_multiplier_v11186 = _sb420_bind(_sb420_src_01.offensive_skill_damage_multiplier_v11186, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.apply_superboss_helper_after_skill_v11192 = _sb420_bind(_sb420_src_01.apply_superboss_helper_after_skill_v11192, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.handle_aoe_setting_v11120 = _sb420_bind(_sb420_src_01.handle_aoe_setting_v11120, globals(), "SessionCombatSkillsMixin")
SessionCombatSkillsMixin.use_class_skill = _sb420_bind(_sb420_src_02.use_class_skill, globals(), "SessionCombatSkillsMixin")



# OLC 16: optional on-hit status adapter for selected edited/created skills.
# Historical method body and its AST fingerprint remain completely unchanged.
from systems.live_olc19_status_skills import cast_with_olc_status_v1900 as _olc19_cast
_OLC19_HISTORICAL_CAST = SessionCombatSkillsMixin.use_class_skill
from functools import wraps as _olc19_wraps
@_olc19_wraps(_OLC19_HISTORICAL_CAST)
async def _olc19_status_cast(self, raw):
    return await _olc19_cast(self, raw, _OLC19_HISTORICAL_CAST)
SessionCombatSkillsMixin.use_class_skill = _olc19_status_cast
