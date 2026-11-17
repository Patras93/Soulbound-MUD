# -*- coding: utf-8 -*-
"""v114 real-gametime XP continuation, isolated from production SQLite."""
from __future__ import annotations

def run():
    from player.character import Character
    from core.progression_resources import character_xp_to_next, class_mastery_xp_to_next
    from core.balance_math import axis_gain
    from core.live_level_caps_v5200 import cap
    from core.progression_policy_v114 import install_deploy_policy
    from systems.progression_xp_unbounded_v114 import requirement
    before={axis:fn(100) for axis,fn in (('character',character_xp_to_next),('class',class_mastery_xp_to_next))}
    policy=install_deploy_policy()
    assert policy['postac'] is None and policy['bieglosc'] is None
    assert cap('ulepszenia_eq') == 10
    checks=0
    for kind,fn in (('character',character_xp_to_next),('class',class_mastery_xp_to_next)):
        previous=0
        assert fn(100)==before[kind];checks+=1
        for level in (101,102,199,599,799,800,801,1000,2000,5000,60000,1_000_000):
            expected=requirement(kind,level,before[kind])
            actual=fn(level)
            assert expected==actual and actual>previous, (kind,level,expected,actual,previous)
            assert actual<9_000_000_000_000_000_000
            previous=actual
            checks+=2
        assert 0 < (fn(1_000_000)-fn(800)) / (axis_gain(kind,1_000_000)-axis_gain(kind,800)) < 501
        checks+=1
        try: requirement(kind, 1_000_000_000, before[kind])
        except OverflowError: pass  # AUDIT_INTENTIONAL_PASS: fail loudly at SQLite storage bound
        else: raise AssertionError('Silent SQLite XP saturation')
        checks+=1
    # Real Character.add_character_xp must level without relying on admin flags.
    actor=object.__new__(Character)
    actor.character_level=1999
    actor.character_xp=0
    needed=character_xp_to_next(1999)
    actor.add_character_xp(needed)
    assert actor.character_level==2000 and actor.character_xp==0
    checks+=1
    return checks

if __name__=='__main__':
    print('v114 CHAR + CLASS XP CONTINUATION: %d checks PASS'%run())
