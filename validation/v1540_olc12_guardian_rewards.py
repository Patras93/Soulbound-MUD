# -*- coding: utf-8 -*-
"""v15.40.0: real OLC validation, snapshot, payout and UOSS isolation."""
import copy
import sqlite3
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from systems.guardian_rewards_v1540 import (
    REWARD_FIELDS_V1540, validate_guardian_rewards_v1540,
    guardian_reward_snapshot_v1540, grant_guardian_currency_v1540, default_guardian_rewards_v1540,
)
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_boss_phases import eligible_boss


def run():
    checks = 0
    reward = {'xp': 123456, 'silver': 200, 'gold': 3, 'mithril': 0}
    assert REWARD_FIELDS_V1540 == set(reward); checks += 1
    assert validate_guardian_rewards_v1540(reward) == reward; checks += 1
    assert guardian_reward_snapshot_v1540({'boss': True}) is None; checks += 1
    assert default_guardian_rewards_v1540({'level':100, 'source_xp':4000000}) == {'xp':500000,'silver':0,'gold':0,'mithril':0}; checks += 1
    for invalid in ({'xp': 12}, {'xp': 10, 'silver': 0, 'gold': 0, 'mithril': True},
                    {'xp': -1, 'silver': 0, 'gold': 0, 'mithril': 0},
                    {'xp': 1.5, 'silver': 0, 'gold': 0, 'mithril': 0},
                    {'xp': 10**13, 'silver': 0, 'gold': 0, 'mithril': 0},
                    ['xp','silver','gold','mithril']):
        try: validate_guardian_rewards_v1540(invalid)
        except ValueError: checks += 1
        else: raise AssertionError('Invalid reward accepted')
    c = SimpleNamespace(silver=100, gold=5, mithril=8)
    assert grant_guardian_currency_v1540(c, reward) == (200, 3, 0); checks += 1
    assert (c.silver, c.gold, c.mithril) == (300, 8, 8); checks += 1
    assert grant_guardian_currency_v1540(c, None) == (0, 0, 0); checks += 1
    assert (c.silver, c.gold, c.mithril) == (300, 8, 8); checks += 1
    assert guardian_reward_snapshot_v1540({'olc_boss_guardian_rewards':reward}) == reward; checks += 1
    assert eligible_boss(MOB_TEMPLATES['bandit_captain']); checks += 1

    conn = sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *args:None)
    srv = SimpleNamespace(world=world, sessions=[])
    svc = LiveContentV1204(SimpleNamespace(conn=conn))
    original = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    try:
        import json
        svc.stage_edit('mob','bandit_captain','olc_boss_guardian_rewards',json.dumps(reward))
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_guardian_rewards'] == reward; checks += 1
        for bad in ('{"xp": 4}', '{"xp": -1, "silver":0, "gold":0,"mithril":0}',
                    '{"xp":0,"silver":0,"gold":0,"mithril":false}'):
            before=copy.deepcopy(svc.draft)
            try: svc.stage_edit('mob','bandit_captain','olc_boss_guardian_rewards',bad)
            except ValueError: checks += 1
            else: raise AssertionError('Invalid OLC accepted')
            assert svc.draft == before; checks += 1
        # Source-authored UOSS boss: never eligible for ordinary OLC.
        protected = next((k for k,v in MOB_TEMPLATES.items()
                          if v.get('uoss_unique_superboss_key')=='black_rabite'),None)
        if protected:
            before = copy.deepcopy(svc.draft)
            try: svc.stage_edit('mob',protected,'olc_boss_guardian_rewards',json.dumps(reward))
            except ValueError: checks += 1
            else: raise AssertionError('UOSS edited by ordinary boss OLC')
            assert svc.draft == before; checks += 1
        assert 'Aktywowano' in svc.apply(srv,'v1540_validation'); checks += 1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_guardian_rewards'] == reward; checks += 1
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        assert reopened.active['mob_edits']['bandit_captain']['olc_boss_guardian_rewards']==reward; checks += 1
        reopened.stage_edit('mob','bandit_captain','olc_boss_guardian_rewards','auto')
        assert 'olc_boss_guardian_rewards' not in reopened.draft['mob_edits'].get('bandit_captain',{});checks += 1
        assert 'Aktywowano' in reopened.apply(srv,'v1540_validation');checks+=1
        assert 'olc_boss_guardian_rewards' not in MOB_TEMPLATES['bandit_captain']; checks += 1
        reopened._remove(world)
    finally:
        svc._remove(world)
        assert MOB_TEMPLATES['bandit_captain'] == original
        conn.close()
    # The source-authored UOSS add has no OLC ordinary guardian marker.
    from data.mobs import MOB_TEMPLATES as templates
    unique = [x for x in templates.values() if x.get('uoss_superboss_add')]
    assert unique and all(not x.get('boss_companion_v1281') for x in unique);checks+=1
    return checks

if __name__ == '__main__':
    print('V15.40.0 OLC 12.0:',run(),'checks PASS')
