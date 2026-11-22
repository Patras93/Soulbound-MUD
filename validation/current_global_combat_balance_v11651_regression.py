# -*- coding: utf-8 -*-
"""Regression for world-wide excessive HP stacking introduced by v116.00.50.

Exercises all rank types, 1/2/4/6 real players and active hires/summons,
level bands 1..unbounded, both Crypt variants, towers and open-world stages.
Uses authored template copies only; never accesses production databases or TCP.
"""
from __future__ import annotations

from copy import deepcopy
from core.balance_math import mob_hp
from systems.adaptive_combat import (
    adaptive_combat_rank_v11330,
    authored_stage_challenge_multiplier_v11650,
    authored_stage_combat_level_v11651,
)


def run():
    checks = 0

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(f'GLOBAL BALANCE v116.00.51: {label}')

    # The complaint is about 2 level-73 players with 3 hires apiece on
    # floor 60. v116.50 multiplied already-strong floor HP by x33.6251.
    crypt60 = {'crypt_floor': 60, 'generator_level': 139,
               'name': 'Strażnik Nieskończonej Krypty', 'max_hp': 139071,
               'damage': 320, 'rank': 'normal'}
    before = deepcopy(crypt60)
    check(authored_stage_combat_level_v11651(crypt60) == 80,
          'floor 60 / generator stage 139 must not double-count 79 levels')
    regular = authored_stage_challenge_multiplier_v11650(
        crypt60, 73, real_players=2, mercenaries=6, companions=2)
    check(1.0 < regular <= 1.30, 'two level-73 fighters must not face x33 HP')
    check(int(crypt60['max_hp'] * regular) < 200000,
          'floor-60 realistic baseline must stay under 200k, not 4.7 million')
    check(crypt60 == before, 'authoring immutable: XP, combat rank and drops untouched')
    check(authored_stage_challenge_multiplier_v11650(
          crypt60, 73, real_players=6, mercenaries=18, companions=6) <= 1.65,
          'six players and helpers must not make normal floor-60 mob a raid boss')
    check(authored_stage_challenge_multiplier_v11650(
          crypt60, 85, real_players=6, mercenaries=18, companions=6) == 1.,
          'players above floor combat recommendation must get no extra HP')
    check(authored_stage_challenge_multiplier_v11650(
          crypt60, 68, real_players=2, mercenaries=6, companions=2) < 1.4,
          'floor 60 also accessible to slightly lower-level characters')
    check(authored_stage_challenge_multiplier_v11650(
          crypt60, 1, real_players=6, mercenaries=18, companions=6) <= 2.3,
          'absurdly underleveled characters still cannot inflate HP beyond x2.3')

    for rank in ('normal', 'elite', 'rare', 'mini', 'boss', 'world_boss'):
        for level in (1, 20, 40, 68, 73, 100, 200, 400, 800, 2000, 10000):
            for offset in (-20, -5, 0, 5, 6, 10, 30, 100, 500, 2000):
                stage = max(1, level + offset)
                template = {'generator_level': stage, 'rank': rank,
                            'max_hp': 333, 'damage': 22,
                            'character_xp_reward': 50, 'quest_target': 'target'}
                original = dict(template)
                previous = 1.0
                for real_players, hires, summons in (
                        (1,0,0), (2,6,2), (4,12,4), (6,18,6)):
                    value = authored_stage_challenge_multiplier_v11650(
                        template, level, real_players=real_players,
                        mercenaries=hires, companions=summons)
                    check(1.0 <= value <= 2.3,
                          f'{rank} stage {stage} level {level} party {real_players} x{value}')
                    check(value >= previous,
                          f'more actual fighters cannot reduce HP: {rank} stage {stage}')
                    if stage <= level + 5:
                        check(value == 1.0, 'same/low level authored stat remains untouched')
                    previous = value
                check(template == original, 'scaling must not mutate authored template')
    for floor in (1, 10, 20, 40, 50, 60, 70, 80, 100, 200, 400, 800, 2000):
        t={'crypt_floor': floor, 'generator_level':79+floor, 'rank':'normal'}
        check(authored_stage_combat_level_v11651(t) == floor + 20,
              f'normal crypt floor {floor} recommendation')
        t={'mythic_crypt_floor': floor, 'generator_level':115+floor, 'rank':'normal'}
        check(authored_stage_combat_level_v11651(t) == floor + 115,
              f'mythic crypt floor {floor} recommendation')
        check(1 <= authored_stage_challenge_multiplier_v11650(t, 73, 2, 6, 2) <= 2.3,
              f'mythic floor {floor} bounded')
    for rank in ('normal','elite','rare','mini','boss','world_boss'):
        t={'crypt_floor':60, 'generator_level':139,'rank':rank,
           'max_hp':int(mob_hp(139, rank) * (7 + 60 / 32))}
        ratio=authored_stage_challenge_multiplier_v11650(
            t,73,real_players=2,mercenaries=6,companions=2)
        check(ratio <= 1.3,
              f'crypt floor 60 rank {rank}: authored boss rank handles own toughness')
        check(adaptive_combat_rank_v11330(t)==rank,'boss rank preserved')
    # In other authored regions, stage remains a genuine combat recommendation,
    # but extra HP is universally capped even for extremely advanced zones.
    for field in ('generator_level','recommended_level','recommended_mastery',
                  'terrain_room_stage_v0362','v019_stage'):
        t={field:250,'max_hp':5000,'damage':100}
        check(authored_stage_combat_level_v11651(t) == 250, f'world area {field}')
        check(1.0 <= authored_stage_challenge_multiplier_v11650(
              t,73,real_players=6,mercenaries=18,companions=6) <= 2.3,
              f'world area {field} universal HP ceiling')
    for field in ('astral_floor','mythic_astral_floor','magitek_floor',
                  'giant_fortress_floor','profession_dungeon_floor','uoss_deep_dungeon_floor'):
        t={field:230, 'max_hp':25000, 'damage':200}
        check(authored_stage_combat_level_v11651(t) == 230,
              f'{field} existing floor recommendation unchanged')
        check(1.0 <= authored_stage_challenge_multiplier_v11650(
              t,73,real_players=6,mercenaries=18,companions=6) <= 2.3,
              f'{field} bounded party HP')
    check(authored_stage_challenge_multiplier_v11650(
          {'training_dummy':True,'generator_level':5000},1,
          6,18,6)==1.0,'training dummy never inflated')
    check(authored_stage_challenge_multiplier_v11650({},73)==1.0,
          'unknown stage does not scale')
    # Six real characters are the only connection quota; helper counts never
    # affect this quota nor mutate combat damage, XP or persistent records.
    print(f'GLOBAL COMBAT BALANCE v116.00.51: {checks} PASS',flush=True)
    return checks


if __name__=='__main__':
    run()
