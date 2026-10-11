# -*- coding: utf-8 -*-
"""v2.00.6: regression of real unlevelled mob stage and starter-region policy."""
from __future__ import annotations
import ast
import copy
from pathlib import Path

from core import balance_math
from core.progression_resources import v0190_apply_combat_template
from data.catalog_mutations import catalog_assign
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS


def _real_terrain_method():
    """Exercise the production terrain method without starting a live server."""
    source = Path(__file__).resolve().parents[1] / 'world/world_state.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'World')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == '_terrain_scaled_template_v0362')
    method.decorator_list = []
    module = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
        name='World', bases=[], keywords=[], body=[method], decorator_list=[]
    )], type_ignores=[]))
    context = {
        'ROOMS': ROOMS,
        'MOB_TEMPLATES': {k: v.copy() for k, v in MOB_TEMPLATES.items()},
        'CHARACTER_MAX_LEVEL': 800,
        'balance_math': balance_math,
        '_catalog_mut': __import__('data.catalog_mutations', fromlist=['catalog_assign']),
    }
    exec(compile(module, str(source), 'exec'), context)
    return context['World'](), context['MOB_TEMPLATES']


def run_regression():
    checks = 0
    # Starter examples MUST no longer inherit stages from a hash of their names.
    for mob_id in ('goblin','goblin_brute','goblin_scout','goblin_shaman',
                   'bandit','bandit_scout','bandit_marauder','shadow_wolf','training_dummy'):
        original = copy.deepcopy(MOB_TEMPLATES[mob_id])
        runtime = v0190_apply_combat_template(original)
        assert 1 <= runtime['generator_level'] <= 28, (mob_id, runtime['generator_level'])
        # Full server startup installs additional global difficulty wrappers;
        # they may legitimately increase authored HP/damage, but must not
        # stack their multiplier on repeated refresh of the same mob.
        first = (runtime['generator_level'], runtime['max_hp'], runtime['damage'])
        v0190_apply_combat_template(runtime)
        second = (runtime['generator_level'], runtime['max_hp'], runtime['damage'])
        assert first == second, (mob_id, first, second)
        assert runtime['max_hp'] > 0 and runtime['damage'] > 0
        checks += 3
    # High-level authored bosses/regions and procedural floors always win.
    for t in ({'name':'Guard of final realm','generator_level':500, 'max_hp':300000,'damage':5000},
              {'name':'Deep Floor Mob','crypt_floor':350,'max_hp':20000,'damage':500},
              {'name':'High procedural mob','procedural_region_stage':250,'max_hp':20000,'damage':500}):
        observed = v0190_apply_combat_template(copy.deepcopy(t))
        assert observed['generator_level'] >= 250, observed
        checks += 1
    # Cycle regression: the old v0866 route must not recursively re-enter
    # the same unlevelled template when imported by another module.
    from core import progression_resources as progression
    old_global = getattr(progression, 'v0866_mob_progression_power', None)
    def recursive_compatibility(t):
        return progression.v0190_apply_combat_template(t)['generator_level']
    try:
        progression.v0866_mob_progression_power = recursive_compatibility
        for mob_id in ('goblin', 'bandit', 'shadow_wolf'):
            t = copy.deepcopy(MOB_TEMPLATES[mob_id])
            t.pop('generator_level', None)
            t.pop('v019_stage', None)
            observed = progression.v0190_apply_combat_template(t)['generator_level']
            assert 1 <= observed <= 30, (mob_id, observed)
            checks += 1
    finally:
        if old_global is None:
            del progression.v0866_mob_progression_power
        else:
            progression.v0866_mob_progression_power = old_global
    # Each starter area has an explicit, progressive region profile.
    expected = {
        'training':1, 'goblin_camp':16, 'goblin_cave_mouth':18,
        'goblin_fungus_gallery':20, 'goblin_throne_cave':40,
        'bandit_camp':17, 'bandit_inner_camp':32,
        'bandit_command_tent':40, 'ruined_watchtower':20,
    }
    for rid, stage in expected.items():
        assert ROOMS[rid]['generator_level'] == stage, (rid, ROOMS[rid])
        assert ROOMS[rid]['region_stage_v2006'] == stage
        checks += 2
    # Production area-loader must never clobber reviewed low-level stages.
    for roomid in ('goblin_camp', 'bandit_camp', 'goblin_throne_cave', 'ruined_watchtower'):
        saved = copy.deepcopy(ROOMS[roomid])
        observed = balance_math.runtime_room_level(roomid, saved, ROOMS)
        assert observed == ROOMS[roomid]['generator_level'], (roomid, observed)
        checks += 1
    # Dynamically added outskirts no longer randomly become level 300+.
    for zone, stage in [('Przedmieścia Miasta Dusz', 3), ('Miasto Dusz', 1),
                        ('Łąki', 5), ('Dzicz', 12)]:
        room = {'zone': zone, 'name': 'Próba terenu', 'exits': {}}
        observed = balance_math.runtime_room_level('__v2006_no_links__', room, {})
        assert observed == stage, (zone, observed)
        checks += 1
    # An explicit late-game stage always wins, even with a beginner-ish name.
    ranked = {'zone': 'Dzicz', 'generator_level': 280, 'recommended_mastery': 290}
    assert balance_math.runtime_room_level('deep_wilderness_boss_room', ranked, {}) == 290
    checks += 1
    # Real terrain clone picks up ROOM stage, not player count or follower level.
    world, templates = _real_terrain_method()
    for room, mob, limit in [('goblin_camp','goblin',20),
                             ('goblin_throne_cave','goblin',45),
                             ('bandit_camp','bandit',21),
                             ('bandit_inner_camp','bandit',37)]:
        base = v0190_apply_combat_template(copy.deepcopy(MOB_TEMPLATES[mob]))
        templates[mob] = base
        spawned = world._terrain_scaled_template_v0362(room, mob)
        stage = templates[spawned]['generator_level']
        assert stage <= limit, (room, mob, stage)
        assert stage >= ROOMS[room]['generator_level'], (room, mob, stage)
        checks += 2
    # No class/XP/stat/resource/drops/unique item metadata is deleted from base.
    for mob_id in ('goblin','bandit','goblin_warchief','bandit_captain'):
        t = v0190_apply_combat_template(copy.deepcopy(MOB_TEMPLATES[mob_id]))
        for key in ('drops','stat_reward','soul_reward'):
            assert key in t, (mob_id,key)
        checks += 3
    return checks


if __name__ == '__main__':
    print(f'REGIONAL WORLD v2.00.6: {run_regression()} checks PASS')
