# -*- coding: utf-8 -*-
"""XP rewards must be disconnected from next-level thresholds, 1..800."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from systems.milestone_cap_rewards_v2103 import (
    fame_cap_awards_v2103, explorer_award_per_point_v4211, exploration_point_xp_v2103)
from systems.experience_cap_v2009 import experience_cap_v2009
from systems.multi_cap_v23215 import multi_cap_level_value_v23217
from core.progression_resources import character_xp_to_next
from systems.dungeon_experience_v1285 import dungeon_recipient_xp_v1286
from systems.dungeon_xp_reference_v4211 import authored_base_dungeon_xp_v4211
from core import balance_math


def _session(level):
    return SimpleNamespace(account_id=11,
      server=SimpleNamespace(db=SimpleNamespace(multi_cap_v23215=lambda account: 248500 + 500*level)),
      character=SimpleNamespace(character_level=level, soul_level=level),
      active_class_names=lambda: ('Wojownik', 'Mag'),
      class_mastery_level=lambda name: level)


def run_regression():
    checks = 0
    for level in range(1,801):
        session = _session(level)
        fame = fame_cap_awards_v2103(session)
        ep = explorer_award_per_point_v4211(level)
        cap = experience_cap_v2009('character', level)
        assert fame['character'] == 248500 + 500*level
        assert fame == dict.fromkeys(('character','soul','stat','class_total'), fame['character'])
        assert 120 <= ep['character'] <= 220
        assert len(set(ep.values())) == 1
        assert cap == multi_cap_level_value_v23217(level)
        assert exploration_point_xp_v2103(session.character) == 120
        checks += 6
    # Generated combat/quest/profession rewards also have isolated curves.
    baseline_generated = {(axis, level): balance_math.axis_gain(axis,level,1.75)
                         for axis in ('character','class','soul','stat','skill','profession','tool')
                         for level in (1,25,48,100,500,799,800)}
    with patch('core.balance_math.axis_requirement',side_effect=AssertionError('award called requirement')), \
         patch.dict(balance_math.AXIS_CURVES, {'character':(100000000,1e10,1.9)}):
        assert baseline_generated == {(axis,level):balance_math.axis_gain(axis,level,1.75)
                                      for axis,level in baseline_generated}
    checks += len(baseline_generated)
    # Deliberately corrupt XP requirement functions: not a single reward may change.
    before = [(fame_cap_awards_v2103(_session(v)), explorer_award_per_point_v4211(v),
               experience_cap_v2009('soul',v),
               dungeon_recipient_xp_v1286({'crypt_floor':v,'generator_level':v},'character',123,v))
              for v in (1,5,10,25,48,100,500,799,800)]
    with patch('core.progression_resources.character_xp_to_next', side_effect=AssertionError('reward used threshold')), \
         patch('core.progression_resources.soul_xp_to_next', side_effect=AssertionError('reward used threshold')), \
         patch('core.progression_resources.v0190_requirement', side_effect=AssertionError('reward used threshold')), \
         patch('config.balance.v4210_required_xp', side_effect=AssertionError('reward used threshold')):
        after = [(fame_cap_awards_v2103(_session(v)), explorer_award_per_point_v4211(v),
                  experience_cap_v2009('soul',v),
               dungeon_recipient_xp_v1286({'crypt_floor':v,'generator_level':v},'character',123,v))
              for v in (1,5,10,25,48,100,500,799,800)]
    assert before == after
    checks += len(before)
    # All three dungeon reward paths and the immutable authoring table.
    for level in range(1,800):
        for axis in ('character','class','soul'):
            assert authored_base_dungeon_xp_v4211(axis,level)>0
            assert dungeon_recipient_xp_v1286({'crypt_floor':level,'generator_level':level},axis,1,level)>0
            checks += 2
    # EP count remains a location property; payout does not grow with player level.
    character = _session(1).character
    assert exploration_point_xp_v2103(character) == exploration_point_xp_v2103(_session(800).character)
    checks += 1
    # An excessive number of room EPs does NOT skip 48 levels.
    assert 10_000 * explorer_award_per_point_v4211(1)['character'] < sum(character_xp_to_next(n) for n in range(1,48))
    checks += 1
    # Source audit: all reward modules must not import requirement or cap-as-reward.
    root = Path(__file__).resolve().parents[1]
    reward_source = (root / 'systems/milestone_cap_rewards_v2103.py').read_text('utf8')
    assert 'xp_to_next' not in reward_source and 'experience_cap_v2009' not in reward_source
    cap_source = (root / 'systems/experience_cap_v2009.py').read_text('utf8')
    assert 'xp_to_next' not in cap_source and 'v0190_requirement' not in cap_source
    assert 'xp_to_next' not in (root / 'systems/dungeon_experience_v1285.py').read_text('utf8')
    assert 'xp_to_next' not in (root / 'systems/dungeon_xp_reference_v4211.py').read_text('utf8')
    checks += 4
    return checks


if __name__ == '__main__':
    print(f'INDEPENDENT REWARD EXP v4.21.1: {run_regression()} checks PASS')
