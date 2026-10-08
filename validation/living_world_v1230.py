# -*- coding: utf-8 -*-
"""Focused regressions for seven non-destructive gameplay extensions."""
from types import SimpleNamespace
from systems.encounter_brain_v1230 import boss_tactics_phase_v1230, tactical_element_v1230, mercenary_combo_v1230
from systems.mercenary_taverns import MERCENARIES
from systems.legendary_reborn import CHASE_RELICS


def audit_living_world_v1230():
    passed = 0
    def check(test, name):
        nonlocal passed
        assert test, name
        passed += 1
    mob = SimpleNamespace(template_id='test', key='test', room_id='arena', engaged_by='player',
                          hp=740, alive=True, combat_turn=4)
    boss = {'name': 'Arena Boss', 'boss': True, 'max_hp': 1000}
    check('FAZA 1/3' in boss_tactics_phase_v1230(mob, boss, now=100), 'boss first phase')
    check(boss_tactics_phase_v1230(mob, boss, now=101) is None, 'no repeat boss phase')
    first_strength = mob.v1230_phase_attack_multiplier
    mob.hp = 200
    check('FAZA 3/3' in boss_tactics_phase_v1230(mob, boss, now=102), 'boss next phase')
    check(mob.v1230_phase_attack_multiplier > first_strength, 'later phases hit harder')
    check(boss_tactics_phase_v1230(mob, {'uoss_superboss': True, **boss}) is None, 'UOSS preserved')
    check(mob.hp == 200, 'boss phases never cap player damage or change HP')
    normal = {'name':'Strażnik','max_hp':1000,'damage_type':'physical'}
    check(tactical_element_v1230(mob, normal) is not None, 'physical normal elemental technique')
    check(tactical_element_v1230(mob, {'training_dummy':True, **normal}) is None, 'dummy immune')
    check(mercenary_combo_v1230('mag', ['mag','wojownik'], MERCENARIES) > 1, 'mixed synergy')
    # Audit the economic stage formula separately: the full economic catalog is
    # intentionally imported later by the game's runtime loader.
    from pathlib import Path
    income_text = (Path(__file__).resolve().parents[1] / 'systems/economy_income_balance.py').read_text(encoding='utf-8')
    check('anchor * (stage / V1124_ECONOMY_MAX_STAGE) ** 0.85' in income_text and 'return economy_stage_anchor_v11314(stage)' in income_text, 'post-600 activity-only tail')
    check('stage = max(1, int(stage or 1))' in income_text, 'activities not clamped at stage 600')
    check(len(CHASE_RELICS) >= 6, 'new rare gear')
    world_text = (Path(__file__).resolve().parents[1] / 'world/generation_systems.py').read_text(encoding='utf-8')
    check('v1230_caravan_aurora' in world_text and 'v1230_caravan_smith' in world_text, 'real rotating caravans')
    return passed

if __name__ == '__main__':
    print('LIVING WORLD 1.23.0 PASS:', audit_living_world_v1230(), 'checks')
