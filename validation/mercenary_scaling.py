# -*- coding: utf-8 -*-
"""v1.21.3 regression: cross-class mercenaries use owner effective power."""
import asyncio
import ast
import time
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_taverns import mercenary_owner_power_v1213, MERCENARIES
from systems.mercenary_growth_v1220 import mercenary_level, mercenary_attack_multiplier, mercenary_action_xp, mercenary_unlocked


def audit_mercenary_scaling_v1213():
    checks, errors = 0, []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)

    for own_phys, own_magic, want in (
        (40000, 1000, 40000),   # warrior hiring a mage
        (1000, 40000, 40000),   # mage hiring a warrior
        (40000, 40000, 40000),  # hybrid is not double counted
        (9000, 1000, 9000),
        (12000, 1000, 12000),   # upgraded physical equipment
        (1000, 12000, 12000),   # upgraded magical equipment
        (0, 0, 1),
    ):
        check(mercenary_owner_power_v1213(own_phys, own_magic) == want,
              f'owner power {own_phys}/{own_magic}')
    for role, spec in MERCENARIES.items():
        check(spec['attack_type'] in ('physical', 'magic'), f'{role} attack type retained')
        check(float(spec['power']) > 0, f'{role} role power retained')

    # Isolate and execute the actual async method from source. The game's
    # full session class needs bootstrapped world globals, so importing it in
    # the fast audit would initialize an incomplete world.
    source_file = Path(__file__).resolve().parents[1] / 'player/session_mixins/mercenary_taverns.py'
    tree = ast.parse(source_file.read_text(encoding='utf8'))
    session_class = next(node for node in tree.body
                         if isinstance(node, ast.ClassDef) and node.name == 'SessionMercenaryTavernsMixin')
    actual_turn = next(node for node in session_class.body
                       if isinstance(node, ast.AsyncFunctionDef) and node.name == 'mercenary_combat_turn_v1170')
    import copy
    actual_turn = copy.deepcopy(actual_turn)
    actual_turn.decorator_list = []
    events = []

    def inspect_adjust(template, power, damage_type, role):
        events.append((damage_type, role))
        return power, None

    namespace = {
        'time': time,
        'COOLDOWN': 5.0,
        'MERCENARIES': MERCENARIES,
        'pick_next_contract': __import__('systems.mercenary_taverns', fromlist=['pick_next_contract']).pick_next_contract,
        'mercenary_owner_power_v1213': mercenary_owner_power_v1213,
        'mercenary_level': mercenary_level,
        'mercenary_attack_multiplier': mercenary_attack_multiplier,
        'mercenary_action_xp': mercenary_action_xp,
        'mercenary_unlocked': mercenary_unlocked,
        'superboss_healing_blocked_v11179': lambda target: False,
        'MOB_TEMPLATES': {'merc_cross_test': {'max_hp': 2000000, 'damage': 1, 'rank': 'boss'}},
        'v0314_adjust_damage_vs_template': inspect_adjust,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[actual_turn], type_ignores=[])),
                 str(source_file), 'exec'), namespace)

    class Sample: 
        mercenary_combat_turn_v1170 = namespace['mercenary_combat_turn_v1170']
        def __init__(self, role, physical, magic):
            self.character = SimpleNamespace(name='Test', room_id='merc_cross_test', character_level=200)
            self.current_hp = 100000
            self.skill_guard = 1  # guard support does not displace offensive action
            self.account_id = 1
            self._mercenary_next_action_v1170 = 0.0
            self._mercenary_last_role_v1170 = None
            self._physical = physical
            self._magic = magic
            self.messages = []
            self.server = SimpleNamespace(
                db=SimpleNamespace(mercenary_contracts=lambda _account, _now: [{'role': role, 'expires_at': 0}],
                    mercenary_progress_v1220=lambda _account,_role: {'xp':0,'specialization':'','actions':0},
                    mercenary_gain_xp_v1220=lambda _account,_role,_xp: {'xp':_xp,'specialization':'','actions':1}),
                party_sessions=lambda _account, same_room=None: [self],
                party_combat_broadcast=self.broadcast,
            )

        def physical_power(self):
            return self._physical

        def spell_power(self):
            return self._magic

        def max_hp(self):
            return 100000

        async def apply_boss_defense(self, mob, amount):
            return amount

        def mob_effective_max_hp_v11330(self, mob):
            return 2000000

        async def broadcast(self, origin, message, detail='normal'):
            self.messages.append(message)

    async def run_turn(role, physical, magic):
        session = Sample(role, physical, magic)
        mob = SimpleNamespace(template_id='merc_cross_test', room_id='merc_cross_test', hp=2000000, alive=True)
        await session.mercenary_combat_turn_v1170(mob)
        return (2000000 - mob.hp, session.messages)

    try:
        for role in MERCENARIES:
            p_damage, p_msgs = asyncio.run(run_turn(role, 40000, 1000))
            m_damage, m_msgs = asyncio.run(run_turn(role, 1000, 40000))
            high_damage, _ = asyncio.run(run_turn(role, 60000, 1000))
            check(p_damage > 0, f'{role}: physical owner deals nonzero damage')
            check(m_damage == p_damage, f'{role}: mixed hiring equalized owner power')
            check(high_damage > p_damage, f'{role}: effective EQ power increases mercenary damage')
            check(bool(p_msgs) and bool(m_msgs), f'{role}: messages emitted')
            check(all(0 < value <= 30000 for value in (p_damage, m_damage, high_damage)), f'{role}: 1.5 percent boss cap')
        for attack_type, role in events:
            desired = 'magic' if any(spec['role'] == role and spec['attack_type'] == 'magic' for spec in MERCENARIES.values()) else 'physical'
            check(attack_type == desired, f'{role}: damage channel retained')
    finally:
        events.clear()

    return {'checks': checks, 'error_count': len(errors), 'errors': errors}


if __name__ == '__main__':
    report = audit_mercenary_scaling_v1213()
    print(report)
    if report['error_count']:
        raise SystemExit(1)
