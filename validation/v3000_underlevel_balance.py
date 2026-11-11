# -*- coding: utf-8 -*-
"""Soulbound 3.00.0: challenge below recommended combat stage.

Isolated production-function regression. No network, live player DB or writes.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from systems.adaptive_combat import (
    adaptive_encounter_stage_v2325,
    adaptive_underlevel_pressure_v3000,
    adaptive_combined_pressure_v3000,
    adaptive_dungeon_pressure_v2325,
    adaptive_target_incoming_fraction_v11330,
    adaptive_target_max_hp_v11330,
    adaptive_beginner_incoming_target_v2005,
)


def run_regression():
    checks = 0

    def check(condition, explanation):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError('BALANS 3.00.0: ' + explanation)

    check(adaptive_underlevel_pressure_v3000({}, 1) == (100, 1.0), 'no stage')
    check(adaptive_underlevel_pressure_v3000({'training_dummy': True, 'crypt_floor': 1000}, 1)
          == (100, 1.0), 'training dummy')
    check(adaptive_underlevel_pressure_v3000({'recommended_level': 40}, None)
          == (100, 1.0), 'unknown hero level')

    for rank in ('normal', 'elite', 'rare', 'mini', 'boss', 'world_boss'):
        for level in (1, 10, 40, 100, 200, 400, 800, 1400):
            same = {'rank': rank, 'recommended_level': level}
            check(adaptive_combined_pressure_v3000(same, level) == (100, 1.0),
                  f'{rank} same level {level} unchanged')
            check(adaptive_combined_pressure_v3000(same, level + 50) == (100, 1.0),
                  f'{rank} overlevelled {level} unchanged')
            five_above = {'rank': rank, 'recommended_level': level + 5}
            check(adaptive_underlevel_pressure_v3000(five_above, level) == (100, 1.0),
                  f'{rank} first five levels grace')
            # No changes to XP/drop, real boss mechanics or class bonuses.
            higher = {'rank': rank, 'recommended_level': level + 55}
            hp, dmg = adaptive_combined_pressure_v3000(higher, level)
            check(hp > 100 and dmg > 1.0, f'{rank} lvl {level} challenged')
            check(adaptive_target_max_hp_v11330(100, 1000, higher, party_level=level)
                  > adaptive_target_max_hp_v11330(100, 1000, higher, party_level=level+55),
                  f'{rank} lvl {level} party HP scales')
            check(adaptive_target_incoming_fraction_v11330(higher, 1, player_level=level)
                  > adaptive_target_incoming_fraction_v11330(higher, 1, player_level=level+55),
                  f'{rank} lvl {level} outgoing threat scales')

    # Previously only stages 100+ were covered: stage 20/50/90 now matters.
    for stage, low in ((20, 1), (30, 10), (50, 20), (90, 20), (100, 40),
                       (200, 50), (400, 100), (800, 200)):
        template = {'rank': 'normal', 'generator_level': stage}
        check(adaptive_combined_pressure_v3000(template, low)[0] > 100,
              f'stage {stage} is not free at player {low}')
        check(adaptive_combined_pressure_v3000(template, low)[1] > 1,
              f'stage {stage} hits player {low} harder')
        check(adaptive_combined_pressure_v3000(template, stage) == (100, 1.0),
              f'legitimate level {stage} remains fair')

    # Monotone curves: wider mismatch cannot mean weaker enemy.
    for hero in (1, 20, 50, 100, 300, 700):
        last_hp, last_dmg = 100, 1.0
        for stage in (hero + 5, hero + 6, hero + 10, hero + 25,
                      hero + 50, hero + 100, hero + 300, hero + 700):
            hp, damage = adaptive_combined_pressure_v3000({'recommended_level': stage}, hero)
            check(hp >= last_hp and damage >= last_dmg,
                  f'nonmonotone at level {hero}, stage {stage}')
            last_hp, last_dmg = hp, damage

    for marker in ('recommended_mastery', 'recommended_level', 'generator_level',
                   'terrain_room_stage_v0362', 'v019_stage', 'crypt_floor',
                   'mythic_crypt_floor', 'uoss_deep_dungeon_floor'):
        stage = {marker: 200}
        check(adaptive_encounter_stage_v2325(stage) == 200, marker + ' stage located')
        check(adaptive_combined_pressure_v3000(stage, 50)[0] >=
              adaptive_dungeon_pressure_v2325(stage, 50)[0],
              marker + ' historical guarantees retained')
        check(adaptive_combined_pressure_v3000({'rank': 'normal'}, 50, room=stage)[0] > 100,
              marker + ' room fallback threat')

    for rank in ('normal', 'boss'):
        opponent = {'rank': rank, 'recommended_level': 50}
        check(adaptive_combined_pressure_v3000(opponent, 8)[0] > 100,
              rank + ' dangerous for level8')
    raw = 9
    low_template = {'rank': 'normal', 'damage': 9, 'recommended_level': 5}
    strong_template = {'rank': 'normal', 'damage': 9, 'recommended_level': 50}
    check(adaptive_beginner_incoming_target_v2005(low_template, 8, raw, 150) <= 13.5,
          'real beginner protection remains')
    check(adaptive_beginner_incoming_target_v2005(strong_template, 8, raw, 150) == 150,
          'level-50 area does not inherit beginner immunity')
    check(adaptive_beginner_incoming_target_v2005(low_template, 8, raw, 150,
          room={'recommended_level':50}) == 150,
          'room metadata overrides novice safety')

    # No float overflow for unlimited floor numbers or uncapped stat builds.
    deep = {'crypt_floor': 10**400}
    check(adaptive_combined_pressure_v3000(deep, 100)[0] > 100,
          'infinite floor arithmetic')
    check(adaptive_target_max_hp_v11330(1000, 10**400, deep, party_level=100) > 10**400,
          'uncapped player damage and floor pressure')
    check(adaptive_combined_pressure_v3000({'recommended_level':10**400}, 10**400)
          == (100, 1.0), 'uncapped character level math')

    # Actual incoming-hit method (including room fallback) and consider forecast.
    from validation.v2005_beginner_encounters import _CharacterSession
    live_fn = _CharacterSession.adaptive_enemy_damage_multiplier_v11330
    forecast_fn = _CharacterSession.consider_adaptive_preview_v11331
    room_table = live_fn.__globals__['ROOMS']
    original = room_table.get('test')
    try:
        room_table['test'] = {'recommended_level': 50}
        player = _CharacterSession(8, 1000)
        mob = SimpleNamespace(template_id='bandit', room_id='test',
                              hp=75, adaptive_party_size_v11330=1)
        template = {'max_hp':75, 'rank':'normal', 'damage':9}
        check(player.adaptive_enemy_damage_multiplier_v11330(mob, template) > 1.56,
              'real low level monster attack does not hide behind novice cap')
        preview = forecast_fn(player, mob, template)
        check(preview['max_hp'] > 75 * 8,
              'consider forecasts higher HP from higher-level room')
        check(preview['enemy_hit'] > 13,
              'consider forecasts high-level enemy danger')
    finally:
        if original is None:
            room_table.pop('test', None)
        else:
            room_table['test'] = original

    source = (Path(__file__).resolve().parents[1] /
              'player/session_mixins/combat_damage.py').read_text('utf8')
    check('UWAGA: przeciwnik ma zalecany etap' in source,
          'NVDA consider warning exists')
    check('nie ma blokady poziomu' in source,
          'consider explicitly says no hard lock')
    return checks


if __name__ == '__main__':
    print(f'BALANS TRUDNOSCI v3.00.0: {run_regression()} checks PASS')
