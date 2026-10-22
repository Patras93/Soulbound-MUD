# -*- coding: utf-8 -*-
"""v12.00.2: real dungeon combat stages and final HP/damage/EXP invariants.

No writes to live SQLite. Includes repeated-refresh checks on transient copies.
"""
from __future__ import annotations


def run_regression():
    import server
    from systems.content_registry import MOB_TEMPLATES, ROOMS
    from world.global_difficulty_overdrive import v0190_apply_combat_template, v0190_combat_reward
    from world.economy_quests import (
        create_infinite_crypt_floor_definition,
        create_infinite_giant_fortress_floor_definition,
        create_infinite_magitek_floor_definition,
    )
    from world.magitek_infinite import magitek_floor_stage
    from systems.dungeon_experience_v1285 import dungeon_recipient_xp_v1286

    checks = 0
    def verify(name, predicate):
        nonlocal checks
        if not predicate:
            raise AssertionError(name)
        checks += 1

    def stats(template):
        return (int(template.get('max_hp', 0) or 0),
                int(template.get('damage', 0) or 0),
                int(v0190_combat_reward(template, 'class')),
                int(v0190_combat_reward(template, 'character')))

    for prefix, minimum, start, end, inc in (
        ('crypt_floor_mob_', 80, 1, 200, 1),
        ('giant_fortress_mob_', 91, 1, 50, 2),
        ('astral_floor_mob_', 100, 100, 200, 1),
        ('mythic_crypt_mob_', 116, 1, 200, 1),
        ('mythic_astral_mob_', 136, 1, 200, 1),
    ):
        previous_stage = 0
        for floor in range(start, end+1):
            t = MOB_TEMPLATES.get(f'{prefix}{floor}')
            verify(f'{prefix}{floor} exists', isinstance(t, dict))
            # Historical audits may regenerate this floor and replace its
            # template with an unrefreshed definition. Combat ALWAYS runs
            # the final refresh before a mob is spawned. Inspect that exact
            # runtime result on an isolated copy, without changing registries.
            t = dict(t)
            v0190_apply_combat_template(t)
            level = int(t.get('generator_level',0) or 0)
            verify(f'{prefix}{floor} level >= {minimum}', level >= minimum)
            verify(f'{prefix}{floor} stage non-decreasing', level >= previous_stage)
            h,d,x,ch = stats(t)
            for field,val in (('HP',h),('damage',d),('Class EXP',x),('Character EXP',ch)):
                verify(f'{prefix}{floor}: {field} positive',val>0)
            previous_stage=level
            # Recalculating statically or on respawn must never compound boosts.
            if floor in (start,start+1,end):
                t_copy = dict(t)
                v0190_apply_combat_template(t_copy)
                verify(f'{prefix}{floor}: idempotent',stats(t_copy)==(h,d,x,ch))

    def runtime_copy(tid):
        t = dict(MOB_TEMPLATES[tid])
        v0190_apply_combat_template(t)
        return t
    c = runtime_copy('crypt_floor_mob_1')
    mc = runtime_copy('mythic_crypt_mob_1')
    g = runtime_copy('giant_fortress_mob_1')
    at = runtime_copy('astral_floor_mob_100')
    mt = runtime_copy('mythic_astral_mob_1')
    verify('Crypt level 20 not starter HP', int(c['max_hp']) >= 60000)
    verify('Crypt level 20 not starter DMG', int(c['damage']) >= 300)
    verify('Crypt high reward at stage 80', v0190_combat_reward(c,'class') >= 40000)
    verify('Mythic crypt stronger', int(mc['max_hp']) > int(c['max_hp']) and int(mc['damage']) > int(c['damage']))
    verify('Giant fortress is advanced', int(g['max_hp'])>=30000 and int(g['damage'])>=200)
    verify('Astral tower stage 100 combat', int(at['max_hp'])>=50000 and int(at['damage'])>=250)
    verify('Mythic astral stronger', int(mt['max_hp'])>int(at['max_hp']) and int(mt['damage'])>int(at['damage']))
    verify('Character level 80 meaningful XP',dungeon_recipient_xp_v1286(c,'class',v0190_combat_reward(c,'class'),80)>=40000)

    for floor in (1,2,10,50,201,601):
        room_id, spawns = create_infinite_crypt_floor_definition(floor)
        tid=next(tid for _,tid in spawns if tid == f'crypt_floor_mob_{floor}')
        t = dict(MOB_TEMPLATES[tid])
        v0190_apply_combat_template(t)
        verify(f'lazy crypt {floor} endgame stage',int(t.get('generator_level',0))>=79+floor if floor <= 721 else int(t.get('generator_level',0))>=800)
        verify(f'lazy crypt {floor} mob combat',min(stats(t)[:3])>0)
        verify(f'lazy crypt {floor} boss checkpoints preserved', floor%10!=0 or any('boss' in tid for _,tid in spawns))
    for floor in (1,2,10,51,201):
        rid,spawns=create_infinite_giant_fortress_floor_definition(floor)
        t=MOB_TEMPLATES[spawns[0][1]]
        v0190_apply_combat_template(t)
        verify(f'lazy Giant {floor} stage',int(t['generator_level'])>=89+2*floor)
        verify(f'lazy Giant {floor} HP/dmg',min(stats(t)[:2])>0)
    for floor in (1,2,10,60,201):
        rid,spawns=create_infinite_magitek_floor_definition(floor)
        t=MOB_TEMPLATES[spawns[0][1]]
        v0190_apply_combat_template(t)
        stage=magitek_floor_stage(floor)
        verify(f'magitek {floor} accurate stage',int(t['generator_level'])==stage)
        verify(f'magitek {floor} room stage',int(ROOMS[rid]['recommended_mastery'])==stage)
        verify(f'magitek {floor} reward and combat',min(stats(t))>0)
        verify(f'magitek {floor} check no nerf',stats(t)[0]>50000)
    # Profession instances / simple world monsters intentionally untouched.
    from world import v410_infinite_floors as dungeon_generation
    verify('Profession dungeons still exist', callable(dungeon_generation.create_infinite_profession_dungeon_floor_definition))
    return checks

if __name__ == '__main__':
    print('V12.00.2 DUNGEON ENDGAME:',run_regression(),'PASS')
