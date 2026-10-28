# -*- coding: utf-8 -*-
"""No artificial level-800 EXP plateau; keep CAP and bank mechanics intact."""
from pathlib import Path
from systems.experience_cap_v2009 import (KINDS, experience_cap_v2009,
    capped_experience_v2009, combat_overcap_v2009)
from systems.multi_cap_v23215 import (multi_cap_level_value_v23217,
    multi_cap_level_increment_v23217)
from core.balance_math import AXIS_CURVES, axis_requirement, SAFE_INT
from systems.experience_bank_v2011 import banked_experience_v2011
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
import sqlite3
from unittest.mock import patch


def run():
    checks = 0
    for kind in KINDS:
        at_800 = experience_cap_v2009(kind, 800)
        at_801 = experience_cap_v2009(kind, 801)
        at_1000 = experience_cap_v2009(kind, 1000)
        assert 0 < at_800 < at_801 < at_1000
        assert at_801 == 2 * multi_cap_level_value_v23217(801)
        assert capped_experience_v2009(at_801*4,kind,801) == at_801
        assert capped_experience_v2009(at_801*4,kind,801,True) == at_801*2
        checks += 4
    from core.balance_math import axis_gain
    for axis in AXIS_CURVES:
        assert axis_gain(axis, 801, 1.0) > axis_gain(axis, 800, 1.0)
        assert axis_gain(axis, 900, 1.0) > axis_gain(axis, 801, 1.0)
        checks += 2
    assert multi_cap_level_increment_v23217(801) > multi_cap_level_increment_v23217(800)
    assert multi_cap_level_increment_v23217(811) > multi_cap_level_increment_v23217(801)
    checks += 2
    # Existing levels 1..800 must preserve the authored XP math exactly.
    for axis in AXIS_CURVES:
        for level in (1,25,300,600,799,800):
            base, growth, power = AXIS_CURVES[axis]
            expected = min(SAFE_INT,max(1,int(round(base + growth*(level**power)))))
            assert axis_requirement(axis,level) == expected, (axis,level)
            checks += 1
        # After 800, non-stat axes now grow rather than freeze.
        assert axis_requirement(axis,801) > axis_requirement(axis,800)
        assert axis_requirement(axis,900) > axis_requirement(axis,801)
        checks += 2
    # The actual level-up API must keep calculating XP above 800 only after
    # the owner changes saved caps to "bezlimitu". Old capped players remain capped.
    from core import live_level_caps_v5200 as caps
    from core.progression_resources import (character_xp_to_next,
        class_mastery_xp_to_next,soul_xp_to_next,skill_xp_to_next)
    funcs=(character_xp_to_next,class_mastery_xp_to_next,
           soul_xp_to_next,skill_xp_to_next)
    with patch.dict(caps._state, {'postac':800,'bieglosc':800,'dusza':800,'skille':800}):
        for fn in funcs:
            assert fn(800) == 0
            checks += 1
    with patch.dict(caps._state, {'postac':None,'bieglosc':None,'dusza':None,'skille':None}):
        for fn in funcs:
            assert 0 < fn(799) < fn(800) < fn(801)
            assert fn(900) > fn(801)
            checks += 2

    # Boss overcap must use the actual level, no virtual lvl-800 player.
    # A simple floor-based template follows the v0190 mob-stage dispatcher.
    # The actual runtime patches this binding to its loaded Admin Live cap.
    with patch('core.progression_resources.CHARACTER_MAX_LEVEL', 2000):
        assert not combat_overcap_v2009({'boss':True,'generator_level':950},1000)
        assert combat_overcap_v2009({'boss':True,'generator_level':1050},1000)
    checks += 2
    # EXP Bank remains per-award, 1:1 repayment and TEXT storage for overcap.
    class TempBank(DatabaseExperienceBankV2011Mixin):
        def __init__(self,conn):self.conn=conn
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
    conn.execute('INSERT INTO accounts VALUES (1)')
    db=TempBank(conn)
    db.create_experience_bank_schema_v2011()
    cap=experience_cap_v2009('character',900)
    assert banked_experience_v2011(db,1,cap*5,'character',900)==cap
    assert db.experience_bank_rows_v2011(1)==[('character','',cap*4)]
    assert banked_experience_v2011(db,1,1,'character',900)==2
    assert db.experience_bank_rows_v2011(1)==[('character','',cap*4-1)]
    checks += 4
    conn.close()
    # Work within SQLite-safe values; no database migrations, player-data edits.
    source=(Path(__file__).resolve().parents[1]/'systems/experience_bank_v2011.py').read_text(encoding='utf-8')
    assert 'cap = (total_cap if total_cap is not None else experience_cap_v2009(kind, level))' in source
    checks += 1
    return checks

if __name__=='__main__':
    print('EXP NO LIMIT v102.00.12:',run(),'checks PASS',flush=True)
