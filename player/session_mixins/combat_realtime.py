# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.combatrealtime_part01 as _sb420_src_01
# SessionCombatRealtimeMixin.ensure_realtime_combat -> player/session_methods_v4200/combatrealtime_part01.py
# SessionCombatRealtimeMixin.boss_summon_wave_v1301 -> player/session_methods_v4200/combatrealtime_part01.py
# SessionCombatRealtimeMixin.grant_soul_weapon_mastery_hit_xp -> player/session_methods_v4200/combatrealtime_part01.py
# SessionCombatRealtimeMixin.apply_uoss_helper_turn_v1146 -> player/session_methods_v4200/combatrealtime_part01.py
# SessionCombatRealtimeMixin.realtime_player_action -> player/session_methods_v4200/combatrealtime_part01.py
import player.session_methods_v4200.combatrealtime_part02 as _sb420_src_02
# SessionCombatRealtimeMixin.realtime_combat_loop -> player/session_methods_v4200/combatrealtime_part02.py
import player.session_methods_v4200.combatrealtime_part03 as _sb420_src_03
# SessionCombatRealtimeMixin.attack -> player/session_methods_v4200/combatrealtime_part03.py

# -*- coding: utf-8 -*-
"""Realtime combat lifecycle and basic attacks.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import asyncio
import random
import time

from core.classes_skills import SOUL_WEAPON_ATTACK_TECHNIQUES
from core.progression_600 import SOUL_WEAPON_MASTERY_MAX_LEVEL, soul_weapon_trait_totals_v11193
from core.progression_resources import (
    soul_weapon_mastery_bonuses,
    v0190_mob_stage,
    v0190_scaled_gain,
)
from core.player_math import (
    basic_attack_hits_from_speed,
    character_offensive_build_multiplier,
)
from data.mobs import MOB_TEMPLATES
from systems.game_feel_rewards import mob_attack_flavor_v11324
from systems.elite_variants import (
    elite_enemy_action_multiplier_v11338,
    elite_regen_amount_v11338,
)
from systems.encounter_brain_v1230 import boss_tactics_phase_v1230, tactical_element_v1230, ordinary_tactics_v1230
from systems.boss_companions_v1281 import boss_companion_due_v1281
from systems.soul_ancients_v1330 import weapon_resonance_percent
from systems.soul_evolutions_v1332 import council_allies
from systems.monster_ecology_v1250 import ecology_turn_v1250, adaptive_skills_v1250, adaptive_defense_v1250, adaptive_cadence_v1250
from systems.monster_ai import (
    monster_ai_plan_v1160, monster_ai_execute_v1160,
    monster_ai_eligible_v1160, monster_ai_necromancer_v1160,
    monster_ai_attack_multiplier_v1160, monster_ai_lifesteal_v1160,
    monster_ai_room_candidates_v1901, monster_ai_due_v1901,
)
from systems.summon_status_v1808 import summon_status_enemy_turn_v1808
from systems.titans_v2100 import titan_round_v2100, titan_attack_multiplier_v2100
from systems.monster_magic import (
    monster_magic_apply_v1151, monster_magic_tick_v1151,
    monster_magic_player_action_v1151, monster_magic_action_interval_v1151,
    monster_magic_incoming_multiplier_v1151, monster_magic_clear_v1151,
)
from systems.elemental_combat import (
    elemental_mob_attack_profile_v11339,
    elemental_target_ward_multiplier_v11339,
    elemental_target_ward_text_v11339,
)
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.uoss_superboss_runtime import (
    superboss_attack_gate_v11137, superboss_helper_profile_v11137,
    superboss_phase_event_v11138, superboss_incoming_multiplier_v11138,
    superboss_source_round_event_v11160, superboss_exact_ability_effect_v11160,
    superboss_source_ability_v11162, superboss_source_summons_v11162,
    superboss_source_attack_multiplier_v11162, superboss_source_status_v11162,
    superboss_apply_source_status_v11173, superboss_combat_start_effects_v11176,
    superboss_add_round_event_v11176, superboss_clear_source_statuses_v11176,
    superboss_source_timed_effect_v11179, superboss_advance_timed_effects_v11179,
    superboss_healing_blocked_v11179, superboss_helper_action_v1146,
    superboss_helper_release_v1146,
)

class SessionCombatRealtimeMixin:
    async def stop_realtime_combat(self):
                """Zatrzymaj pętlę walki bez pozostawiania zadania w tle."""
                task = self.combat_task
                self.combat_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal task cancellation
                        pass

    async def ensure_realtime_combat(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method ensure_realtime_combat")

    async def boss_summon_wave_v1301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method boss_summon_wave_v1301")

    async def grant_soul_weapon_mastery_hit_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_soul_weapon_mastery_hit_xp")

    def basic_attack_hit_count_v11196(self):
                """Final Speed drives Soul Weapon multi-hit; Haste doubles the series."""
                return basic_attack_hits_from_speed(
                    self.speed(),
                    haste=self.beneficial_status_active_v11154("haste"),
                )

    async def apply_uoss_helper_turn_v1146(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method apply_uoss_helper_turn_v1146")

    async def realtime_player_action(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method realtime_player_action")

    async def realtime_combat_loop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method realtime_combat_loop")

    async def attack(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method attack")

# v4.20.0: exact historical implementations rebound onto original class.
SessionCombatRealtimeMixin.ensure_realtime_combat = _sb420_bind(_sb420_src_01.ensure_realtime_combat, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.boss_summon_wave_v1301 = _sb420_bind(_sb420_src_01.boss_summon_wave_v1301, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.grant_soul_weapon_mastery_hit_xp = _sb420_bind(_sb420_src_01.grant_soul_weapon_mastery_hit_xp, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.apply_uoss_helper_turn_v1146 = _sb420_bind(_sb420_src_01.apply_uoss_helper_turn_v1146, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.realtime_player_action = _sb420_bind(_sb420_src_01.realtime_player_action, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.realtime_combat_loop = _sb420_bind(_sb420_src_02.realtime_combat_loop, globals(), "SessionCombatRealtimeMixin")
SessionCombatRealtimeMixin.attack = _sb420_bind(_sb420_src_03.attack, globals(), "SessionCombatRealtimeMixin")


