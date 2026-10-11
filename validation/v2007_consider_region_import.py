# -*- coding: utf-8 -*-
"""v2.00.7: reproduce the live CONSIDER NameError without starting a server.

Extract the actual async consider_mob implementation together with its real
module-level room import: never inject ROOMS into the test namespace by hand,
otherwise an accidentally removed import would not be detected.
"""
from __future__ import annotations

import ast
import asyncio
import copy
from pathlib import Path
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from core.progression_600 import CHARACTER_MAX_LEVEL


def _production_consider_class():
    source = Path(__file__).resolve().parents[1] / 'player/session_mixins/combat_damage.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionCombatDamageMixin')
    method = next(n for n in original.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'consider_mob')
    real_room_imports = [
        n for n in tree.body
        if isinstance(n, ast.ImportFrom) and n.module in ('data.rooms', 'data.catalogs')
        and any(alias.name == 'ROOMS' for alias in n.names)
    ]
    # No artificial ROOMS global: import list comes only from production code.
    cls = ast.ClassDef(name='SessionCombatDamageMixin', bases=[], keywords=[],
                       body=[method], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=real_room_imports + [cls], type_ignores=[]))
    env = {'MOB_TEMPLATES': MOB_TEMPLATES, 'CHARACTER_MAX_LEVEL': CHARACTER_MAX_LEVEL}
    exec(compile(module, str(source), 'exec'), env)
    assert env.get('ROOMS') is ROOMS, 'consider_mob requires a real module-level ROOMS import'
    return env['SessionCombatDamageMixin']


async def _exercise(cls, room_id, query):
    class World:
        mob = SimpleNamespace(template_id='goblin')
        def refresh(self):
            pass
        def room_mobs(self, _room):
            return [self.mob]
        def find_mob(self, _room, name):
            return self.mob if 'goblin' in str(name).lower() else None

    class Session(cls):
        def __init__(self):
            self.character = SimpleNamespace(room_id=room_id)
            self.server = SimpleNamespace(world=World())
            self.messages = []
        async def send(self, message):
            self.messages.append(message)
        def protected_friendly_npc(self, raw):
            return None
        def consider_rating(self, mob, template):
            return {
                'label': 'umiarkowany', 'enemy_hit': 7, 'player_hit': 20,
                'player_action': 20, 'player_hits': 1, 'party_action': 20,
                'turns_to_kill': 3, 'turns_to_die': 8, 'advice': 'Uważaj.',
                'adaptive': {
                    'already_scaled': False, 'current_hp': 60, 'max_hp': 60,
                    'base_max_hp': 60, 'hp_multiplier': 1.0, 'rank': 'normal',
                    'party_size': 1, 'reward_multiplier': 1.0,
                },
            }
        def dynamic_kill_xp_profile(self, _template, *, room_id):
            return {'label': 'normalny', 'multiplier': 1.0, 'power': 14, 'target': 16}

    player = Session()
    await player.consider_mob(query)
    return player.messages


def run_regression():
    checks = 0
    cls = _production_consider_class()
    checks += 1
    mob_before = copy.deepcopy(MOB_TEMPLATES['goblin'])
    rooms_before = {room_id: copy.deepcopy(ROOMS[room_id]) for room_id in
                    ('goblin_camp', 'goblin_throne_cave', 'temple_basement')}

    for room_id, expected_stage in (('goblin_camp', 16), ('goblin_throne_cave', 40)):
        msgs = asyncio.run(_exercise(cls, room_id, 'goblin'))
        assert msgs[0].startswith('CONSIDER: Goblin'), msgs
        checks += 1
        assert any(f'etap lokacji {expected_stage}' in m for m in msgs), msgs
        checks += 1
        assert any('etap przeciwnika' in m for m in msgs)
        checks += 1
        assert any('Adaptive Combat' in m for m in msgs), msgs
        checks += 1
        assert msgs[-1].startswith('Consider jest tylko oceną'), msgs[-1]
        checks += 1

    # Old rooms without region metadata must keep their full pre-v2.00.6 text.
    msgs = asyncio.run(_exercise(cls, 'temple_basement', 'goblin'))
    assert not any(m.startswith('Teren:') for m in msgs), msgs
    checks += 1
    assert any('Adaptive Combat' in m for m in msgs)
    checks += 1
    assert msgs[-1].startswith('Consider jest tylko oceną'), msgs[-1]
    checks += 1

    # Missing target returns early, still without an exception or starting a fight.
    msgs = asyncio.run(_exercise(cls, 'goblin_camp', 'nieistniejacy-potwor'))
    assert len(msgs) == 1 and 'Nie widzę tutaj' in msgs[0], msgs
    checks += 1
    assert MOB_TEMPLATES['goblin'] == mob_before
    checks += 1
    for room_id, room in rooms_before.items():
        assert ROOMS[room_id] == room, room_id
        checks += 1
    return checks


if __name__ == '__main__':
    print(f'CONSIDER REGION v2.00.7: {run_regression()} checks PASS')
