# -*- coding: utf-8 -*-
"""v4.21.0: final requirement-only progression safety, every level 1..800.

No SQLite, no XP awards, no level changes. All comparisons exercise the exact
runtime methods; the former x10 historical layer is verified in v3310/v3314.
"""
from __future__ import annotations
from config.balance import (
    V4210_REQUIREMENT_FACTORS, v4210_required_xp,
    profession_xp_requirement_v1401, tool_xp_requirement_v1402,
    scale_stat_requirement_v1408, STAT_XP_REQUIREMENT_MULTIPLIER,
)
from core.progression_resources import (
    character_xp_to_next, class_mastery_xp_to_next,
    soul_xp_to_next, skill_xp_to_next, soul_weapon_mastery_xp_to_next,
    v0190_requirement,
)
from core.player_math import SAFE_INT, late_game_xp_requirement
from validation.tool_xp_v1402 import TOOL_TYPES_V1402
from config.balance import PROFESSION_XP_REQUIREMENT_MULTIPLIERS


def run_regression():
    assert V4210_REQUIREMENT_FACTORS == {
        'character':6, 'class':6, 'soul':10, 'skill':50,
        'weapon':15,'stat':13,'profession':4,'tool':4,'ascension':2,
    }
    checks=1
    player_axes={
        'character':character_xp_to_next,'class':class_mastery_xp_to_next,
        'soul':soul_xp_to_next,'skill':skill_xp_to_next,
        'weapon':soul_weapon_mastery_xp_to_next,
    }
    samples={}
    for axis,fn in player_axes.items():
        previous=0
        for level in range(1,800):
            actual=fn(level)
            assert actual>=previous>=(0), (axis,level,previous,actual)
            assert actual>0 and actual<=SAFE_INT, (axis,level,actual)
            assert actual%10==0 or actual==SAFE_INT, (axis,level,actual)
            assert actual>=v4210_required_xp(1,axis,level)
            previous=actual
            checks+=4
        assert fn(800)==0
        samples[axis]=sum(fn(level) for level in range(1,25))
        checks+=1
    # A single high-value AP/quest/boss reward of 18.9m EXP no longer reaches 25
    # on any player axis even if granted wholly to that axis.
    assert all(x>18_900_000 for x in samples.values()),samples
    # Equal-gain reference: character, class, Soul and combat skills advance
    # with roughly equivalent early cumulative requirements (<=1.55x spread).
    assert max(samples.values())*100 <= min(samples.values())*155, samples
    checks+=2
    assert len(PROFESSION_XP_REQUIREMENT_MULTIPLIERS)==14
    assert len(TOOL_TYPES_V1402)==14
    checks+=2
    for name in PROFESSION_XP_REQUIREMENT_MULTIPLIERS:
        prev=0
        for level in range(1,800):
            now=profession_xp_requirement_v1401(v0190_requirement('profession',level),name,level)
            assert now>=prev and now>0
            prev=now;checks+=1
    for tool in TOOL_TYPES_V1402:
        prev=0
        for level in range(1,800):
            now=tool_xp_requirement_v1402(v0190_requirement('tool',level),tool,level)
            assert now>=prev and now>0
            prev=now;checks+=1
    # Stats are not capped at 800; next-value requirement grows beyond 800.
    prev=0
    for level in list(range(1,800))+[800,801,1000,2000,5000,1000000]:
        base=round(v0190_requirement('stat',level)*STAT_XP_REQUIREMENT_MULTIPLIER)
        terminal=round(v0190_requirement('stat',599)*STAT_XP_REQUIREMENT_MULTIPLIER)
        now=scale_stat_requirement_v1408(late_game_xp_requirement(level,base,terminal),level)
        assert now>=prev and now>0 and now<=SAFE_INT, (level,prev,now)
        prev=now;checks+=1
    for axis in V4210_REQUIREMENT_FACTORS:
        for level in (1,25,100,400,799):
            assert v4210_required_xp(SAFE_INT,axis,level)==SAFE_INT
            checks+=1
    return checks


if __name__=='__main__':
    print(f'ROWNE EXP v4.21.0: {run_regression()} checks PASS')
