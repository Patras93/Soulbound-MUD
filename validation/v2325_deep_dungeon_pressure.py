# -*- coding: utf-8 -*-
"""v2.32.5 — Underlevelled dungeon combat integration, no live database.

Tests the actual extracted production encounter HP method without creating a
world or touching save files. Also checks the production CONSIDER and incoming
combat methods through the existing v2.00.5 isolated preview fixture.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import SimpleNamespace

from systems.adaptive_combat import (
    adaptive_dungeon_floor_v2325, adaptive_dungeon_pressure_v2325,
    adaptive_encounter_stage_v2325,
    adaptive_target_max_hp_v11330, adaptive_target_incoming_fraction_v11330,
    adaptive_reward_multiplier_v11330, adaptive_combat_rank_v11330,
    adaptive_combined_pressure_v3000,
)


def _production_hp_method():
    path = Path(__file__).resolve().parents[1] / 'player/session_mixins/combat_damage.py'
    source = ast.parse(path.read_text(encoding='utf-8'))
    klass = next(n for n in source.body if isinstance(n, ast.ClassDef)
                 and n.name == 'SessionCombatDamageMixin')
    method = next(n for n in klass.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'apply_adaptive_mob_scale_v11330')
    cls = ast.ClassDef(name='Combat', bases=[], keywords=[], body=[method], decorator_list=[])
    namespace = {
        'sys': sys, 'MOB_TEMPLATES': {},
        'ROOMS': {},
        'adaptive_target_max_hp_v11330': adaptive_target_max_hp_v11330,
        'adaptive_reward_multiplier_v11330': adaptive_reward_multiplier_v11330,
        'adaptive_combat_rank_v11330': adaptive_combat_rank_v11330,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])),
                 str(path), 'exec'), namespace)
    return namespace['Combat'], namespace['MOB_TEMPLATES']


def run_regression():
    count = 0

    def check(ok, label):
        nonlocal count
        count += 1
        if not ok:
            raise AssertionError('v2.32.5: ' + label)

    dungeon_fields = (
        'crypt_floor', 'mythic_crypt_floor', 'astral_floor',
        'mythic_astral_floor', 'giant_fortress_floor', 'magitek_floor',
        'profession_dungeon_floor', 'uoss_deep_dungeon_floor',
    )
    for key in dungeon_fields:
        check(adaptive_dungeon_floor_v2325({key: 400}) == 400, f'floor tag {key}')
        hp, incoming = adaptive_dungeon_pressure_v2325({key: 400}, 100)
        check((hp, incoming) == (340, 2.045), f'deep v2.32.5 pressure {key}')
        check(adaptive_dungeon_pressure_v2325({key: 400}, 400) == (100, 1.0),
              f'same-floor {key} unaffected')

    # Authored high-level outdoor areas have the SAME underlevel challenge.
    # Low-level areas, training targets and unrelated legacy flags stay intact.
    for marker in ('generator_level', 'terrain_room_stage_v0362',
                   'recommended_mastery', 'recommended_level', 'v019_stage'):
        outdoors = {marker: 400, 'rank': 'normal'}
        check(adaptive_encounter_stage_v2325(outdoors) == 400,
              'read high-level outdoors via ' + marker)
        check(adaptive_dungeon_pressure_v2325(outdoors, 100) == (340, 2.045),
              'high-level outdoors scaled via ' + marker)
        check(adaptive_dungeon_pressure_v2325(outdoors, 400) == (100, 1.0),
              'on-level outdoor encounters unchanged ' + marker)
    for outdoors in ({'generator_level': 85},
                     {'rank': 'world_boss', 'v019_stage': 0},
                     {'training_dummy': True, 'crypt_floor': 500}, {}):
        check(adaptive_dungeon_pressure_v2325(outdoors, 100) == (100, 1.0),
              'low world/legacy/training unchanged')
    check(adaptive_encounter_stage_v2325({'rank': 'normal'},
           {'generator_level': 400}) == 400, 'room fallback for high-level terrain')
    check(adaptive_encounter_stage_v2325({'generator_level': 400},
           {'recommended_level': 300}) == 400, 'template boss higher than room')
    check(adaptive_encounter_stage_v2325({'crypt_floor': 300},
           {'recommended_mastery': 400}) == 400, 'deepest authored level wins')
    check(adaptive_dungeon_pressure_v2325({'rank': 'normal'}, 100,
           room={'recommended_level': 400}) == (340, 2.045),
          'untagged spawns inherit high-level area threat')
    check(adaptive_dungeon_pressure_v2325({'training_dummy': True}, 100,
           room={'recommended_level': 400}) == (100, 1.0),
          'training dummy immune even in higher region')
    check(adaptive_dungeon_pressure_v2325({'generator_level': 400}, 100,
           room={'training_dummy': True}) == (100, 1.0),
          'training room does not create danger')
    check(adaptive_target_max_hp_v11330(1000, 10000, {'rank': 'normal'},
           party_level=100, room={'recommended_level': 400}) >= (
              80_000 * adaptive_combined_pressure_v3000({'rank':'normal'}, 100, {'recommended_level': 400})[0] // 100),
          'high-level room in target HP computation')
    check(adaptive_target_incoming_fraction_v11330({'rank': 'normal'}, 4,
           player_level=100, room={'recommended_level': 400})
          > adaptive_target_incoming_fraction_v11330({'rank': 'normal'}, 4,
           player_level=100), 'region raises actual incoming damage')
    for floor, expected_hp in ((100, 100), (125, 100), (200, 150),
                               (300, 235), (400, 340), (600, 610)):
        t = {'crypt_floor': floor, 'rank': 'normal'}
        check(adaptive_dungeon_pressure_v2325(t, 100)[0] == expected_hp,
              f'floor {floor} against lvl 100')
        actual = adaptive_target_max_hp_v11330(1000, 10_000, t, party_level=100)
        effective_hp = adaptive_combined_pressure_v3000(t, 100)[0]
        check(actual >= 80_000 * effective_hp // 100 and effective_hp >= expected_hp,
              f'floor {floor} increases encounter lifetime without weakening v2.32.5')

    floor400 = {'crypt_floor': 400, 'rank': 'normal', 'max_hp': 1000, 'damage': 90}
    floor100 = {'crypt_floor': 100, 'rank': 'normal', 'max_hp': 1000, 'damage': 90}
    check(adaptive_target_incoming_fraction_v11330(floor400, 4, player_level=100)
          > adaptive_target_incoming_fraction_v11330(floor100, 4, player_level=100),
          'monster deals more relevant damage deep in crypt')
    check(adaptive_target_incoming_fraction_v11330(floor400, 4, player_level=400)
          == adaptive_target_incoming_fraction_v11330(floor100, 4, player_level=100),
          'full-level member survives at regular pressure')
    check(adaptive_target_max_hp_v11330(1000, 10_000, floor400, party_level=400)
          == 80_000, 'lvl400 party loses mismatch premium')
    check(adaptive_target_max_hp_v11330(1000, 10_000, floor400)
          == 80_000, 'legacy callers still work')
    check(adaptive_target_max_hp_v11330(1000, 10**400, floor400, party_level=100)
          >= 8 * 10**400 * adaptive_combined_pressure_v3000(floor400, 100)[0] // 100,
          'HP has no float overflow and is uncapped beyond 10**400')
    check(adaptive_dungeon_floor_v2325({'crypt_floor': 10**15}) == 10**15,
          'infinite floors are not artificially bounded')

    Combat, mob_templates = _production_hp_method()
    mob_templates['deep_test'] = floor400
    mob_templates['shallow_test'] = floor100

    class Member:
        def __init__(self, level):
            self.character = SimpleNamespace(character_level=level)

    class Fighter(Combat):
        def __init__(self, members):
            self.character = SimpleNamespace(character_level=members[0].character.character_level)
            self.party = members
            self.server = SimpleNamespace(sessions=[])
            self.dps = 10_000
        def adaptive_party_members_v11330(self, mob):
            return self.party
        def adaptive_party_dps_v1261(self, members):
            return self.dps
        def adaptive_mob_has_active_fighters_v1261(self, mob):
            return False

    # Production integration: inherited difficulty from a high-level outdoor
    # room, even if its old mob template has no combat-stage metadata.
    mob_templates['field_low'] = {'rank': 'normal', 'max_hp': 1000, 'damage': 90}
    Combat.apply_adaptive_mob_scale_v11330.__globals__['ROOMS']['field400'] = {
        'name': 'Ekspowisko 400', 'recommended_level': 400,
    }
    region_fighter = Fighter([Member(100)] * 4)
    region_mob = SimpleNamespace(template_id='field_low', key='region',
                                 room_id='field400', hp=1000, alive=True)
    check(region_fighter.apply_adaptive_mob_scale_v11330(region_mob)['max_hp']
          == adaptive_target_max_hp_v11330(1000, 10000, mob_templates['field_low'], party_level=100, room={'recommended_level':400}),
          'real combat inherits lvl400 outdoor location stage')
    region_mob.hp -= 20_000
    check(region_fighter.apply_adaptive_mob_scale_v11330(region_mob)['max_hp']
          == adaptive_target_max_hp_v11330(1000, 10000, mob_templates['field_low'], party_level=100, room={'recommended_level':400})
          and region_mob.hp == adaptive_target_max_hp_v11330(1000, 10000, mob_templates['field_low'], party_level=100, room={'recommended_level':400}) - 20_000,
          'active outdoor fight does not heal or rescale twice')
    # The original Ocean 2.0 mob authoring explicitly records its level; old
    # ocean rooms can lack recommended_level even at late route sections.
    ocean_src = Path(__file__).resolve().parents[1] / 'world/ocean_expansion.py'
    ocean_ast = ast.parse(ocean_src.read_text('utf-8'))
    ocean_fn = next(node for node in ocean_ast.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'v1000_mob')
    ocean_env = {'MOB_TEMPLATES': {}, 'V1000_NEW_MOBS': [],
                 'catalog_assign': lambda row, label, catalog, keys:
                    catalog.__setitem__(keys[0], row)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ocean_fn], type_ignores=[])),
                 str(ocean_src), 'exec'), ocean_env)
    ocean_env['v1000_mob']('ocean_400', 'Oceanski wojownik', 400)
    check(ocean_env['MOB_TEMPLATES']['ocean_400']['generator_level'] == 400,
          'old Ocean 2.0 mobs receive authentic combat-stage metadata')
    check(adaptive_dungeon_pressure_v2325(ocean_env['MOB_TEMPLATES']['ocean_400'],
                                         100) == (340, 2.045),
          'old ocean encounter scales for underlevelled party')

    fighter = Fighter([Member(100), Member(100), Member(100), Member(100)])
    mob = SimpleNamespace(template_id='deep_test', key='m', room_id='deep',
                          hp=1000, alive=True)
    scaled = fighter.apply_adaptive_mob_scale_v11330(mob)
    check(scaled['max_hp'] == adaptive_target_max_hp_v11330(1000, 10000, floor400, party_level=100), 'real combat scales party lvl100 floor400')
    check(scaled['party_size'] == 4, 'all real players counted')
    check(mob.hp == scaled['max_hp'], 'monster HP filled to full scaled maximum')
    again = fighter.apply_adaptive_mob_scale_v11330(mob)
    check(again['max_hp'] == scaled['max_hp'] and mob.hp == scaled['max_hp'],
          'repeat ticks never multiply HP again')
    # An actual high-level ally helps the group, without punishing level-100 peers
    # or silently dividing their individual outgoing damage.
    fighter.party.append(Member(400))
    bridged = fighter.apply_adaptive_mob_scale_v11330(mob)
    check(bridged['max_hp'] == 80_000 and mob.hp == 80_000,
          'highest-level party member eliminates encounter mismatch after handoff')
    fighter.party = [Member(100), Member(100)]
    fighter.dps = 10**400
    mob.hp = 80_000
    massive = fighter.apply_adaptive_mob_scale_v11330(mob)
    check(massive['max_hp'] >= 8 * 10**400 * adaptive_combined_pressure_v3000(floor400, 100)[0] // 100,
          'real underlevel combat supports arbitrarily powerful players')

    from validation.v2005_beginner_encounters import _CharacterSession
    preview_global_rooms = _CharacterSession.consider_adaptive_preview_v11331.__globals__['ROOMS']
    preview_global_rooms['field400'] = {'recommended_mastery': 400}
    preview_global_rooms['field100'] = {'recommended_mastery': 100}
    region_player = _CharacterSession(100, 1000)
    region_preview = region_player.consider_adaptive_preview_v11331(
        SimpleNamespace(hp=1000, template_id='field_low', room_id='field400'),
        mob_templates['field_low'])
    check(region_preview['max_hp'] == adaptive_target_max_hp_v11330(1000, 1, mob_templates['field_low'], party_level=100, room={'recommended_mastery':400}),
          'CONSIDER previews outdoor stage without engaging mob')
    region_enemy = SimpleNamespace(template_id='field_low', room_id='field400',
                                   adaptive_party_size_v11330=4)
    low_enemy = SimpleNamespace(template_id='field_low', room_id='field100',
                                adaptive_party_size_v11330=4)
    check(region_player.adaptive_enemy_damage_multiplier_v11330(
          region_enemy, mob_templates['field_low'])
          > region_player.adaptive_enemy_damage_multiplier_v11330(
          low_enemy, mob_templates['field_low']),
          'real incoming damage respects room stage when template has no level')

    player = _CharacterSession(100, 1000)
    preview = player.consider_adaptive_preview_v11331(
        SimpleNamespace(hp=1000, template_id='deep_test'), floor400)
    check(preview['max_hp'] == adaptive_target_max_hp_v11330(
        1000, 100, floor400, party_level=100), 'CONSIDER shows real depth-scaled HP')
    enemy_mob = SimpleNamespace(adaptive_party_size_v11330=4,
                                template_id='deep_test')
    deep_damage = player.adaptive_enemy_damage_multiplier_v11330(enemy_mob, floor400)
    shallow_damage = player.adaptive_enemy_damage_multiplier_v11330(enemy_mob, floor100)
    check(deep_damage > shallow_damage, 'real enemy hit strength rises on floor400')
    same_level = _CharacterSession(400, 1000)
    check(same_level.adaptive_enemy_damage_multiplier_v11330(enemy_mob, floor400)
          == shallow_damage, 'experienced defender keeps old encounter pressure')
    # Beginner outdoor protection continues to work even with the new helper.
    check(_CharacterSession(8, 1000).adaptive_enemy_damage_multiplier_v11330(
        SimpleNamespace(adaptive_party_size_v11330=1, template_id='bandit'),
        {'rank': 'normal', 'damage': 9}) <= 1.56, 'low level outdoor protection')
    return count


if __name__ == '__main__':
    print(f'DEEP DUNGEON PRESSURE v2.32.5: {run_regression()} checks PASS')
