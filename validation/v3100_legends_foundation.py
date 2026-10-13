# -*- coding: utf-8 -*-
"""v3.10.0: real registration + topology + quest/safe preservation test.

Fast checks run in isolated copies, without importing the server or live DB.
Full checks inspect actual server catalogs after gameplay bootstrap.
"""
from __future__ import annotations
import ast
import copy
from collections import deque
from pathlib import Path
from world.legends_v3100 import REALMS, CLASS_NAMES, PROFESSIONS, OLD_STORIES, install
ROOT = Path(__file__).resolve().parents[1]


def _verify(rooms, npcs, mobs, spawns, quests, items, stats):
    count = 0
    def check(ok, msg):
        nonlocal count
        if not ok:
            raise AssertionError('LEGENDY v3.10.0: ' + msg)
        count += 1

    check(stats == {'rooms': 141, 'npcs': 53, 'mobs': 48, 'spawns': 80, 'quests': 168, 'items': 8}, 'counts')
    check(len(REALMS) == 8 and len(CLASS_NAMES) == 14 and len(PROFESSIONS)==14, 'eight/14/14')
    check('v3100_hall' in rooms and 'v3100_gates' in rooms, 'navigation hubs')
    check(any('v3100_hall' in v.get('exits',{}).values() for v in rooms.values()),'safe entrance')
    new_rooms = {rid for rid in rooms if rid.startswith('v3100_')}
    reached={'square'}
    fringe=deque(['square'])
    while fringe:
        src=fringe.popleft()
        for dest in rooms[src].get('exits',{}).values():
            if dest not in reached and dest in rooms:
                reached.add(dest);fringe.append(dest)
    for rid in new_rooms:
        check(rid in reached, 'unreachable: '+rid)
    directions = {'north':'south','south':'north','east':'west','west':'east',
        'northeast':'southwest','southwest':'northeast','northwest':'southeast',
        'southeast':'northwest','up':'down','down':'up'}
    for rid in new_rooms:
        for dr,dest in rooms[rid]['exits'].items():
            check(dest in rooms and rooms[dest].get('exits',{}).get(directions[dr])==rid, 'nonreversible '+rid+dr)
    mids={m for r,m in spawns}
    for qid,q in quests.items():
        if not qid.startswith('v3100_'):
            continue
        check(q.get('giver') in {v['name'] for v in npcs.values()}, 'missing NPC giver '+qid)
        check(q['needed']>0, 'empty goal '+qid)
        check(q['kind'] in {'kill','collect','talk_npc'}, 'unsupported kind '+qid)
        check(int(q['reward_silver'])>0 and int(q['character_xp_reward'])>0, 'unrewarded '+qid)
        check(q.get('requires_quest') is None or q['requires_quest'] in quests, 'broken prerequisite '+qid)
        if q['kind']=='kill':
            check(q['target'] in mobs and (not q['target'].startswith('v3100_') or q['target'] in mids),'unspawned mob '+qid)
        if q['kind']=='collect':
            check(q['target'] in items, 'missing item '+qid)
        if q['kind']=='talk_npc':
            check(q['target_npc'] in npcs, 'no target NPC '+qid)
        if q.get('repeatable'):
            check(q['repeat_cooldown']==3600, 'no independent repeat '+qid)
    for slug,*_ in REALMS:
        prefix='v3100_'+slug
        for q in (f'{prefix}_story_{i}' for i in range(1,6)):
            check(q in quests, 'missing story '+q)
        for q in (f'{prefix}_expedition_{i}' for i in range(1,3)):
            check(q in quests, 'missing expedition '+q)
        for q in (f'{prefix}_chronicle_{i}' for i in range(1,4)):
            check(q in quests and quests[q]['repeatable'], 'missing chronicle '+q)
        check(f'{prefix}_boss' in mobs and mobs[f'{prefix}_boss']['world_boss'],'missing boss '+slug)
        check(any('Ekspedycja:' in rooms[r]['zone'] for r in new_rooms if r.startswith(prefix)), 'missing expedition rooms '+slug)
    for i,_ in enumerate(CLASS_NAMES):
        for ch in (1,2):
            qid=f'v3100_class_{i:02d}_quest_{ch}'
            check(qid in quests and quests[qid]['required_class']==CLASS_NAMES[i], 'class campaign '+qid)
    for i,_ in enumerate(PROFESSIONS):
        for ch in (1,2):
            qid=f'v3100_prof_{i:02d}_order_{ch}'
            check(qid in quests and quests[qid]['reward_profession']==PROFESSIONS[i][0], 'profession '+qid)
    for i,_ in enumerate(OLD_STORIES):
        for ch in range(1,5):
            check(f'v3100_old_{i}_{ch}' in quests,'old world story')
    return count


def run_regression_fast():
    from data.catalogs import ROOMS, NPCS, MOB_TEMPLATES, ITEMS, QUESTS
    if 'v3100_hall' in ROOMS:
        # predeploy_check imports the real server first; catalogs are now LIVE.
        # Do not attempt a second installation into its already-populated dicts.
        import server
        return run_regression_full(server)
    original = (ROOMS, NPCS, MOB_TEMPLATES, ITEMS, QUESTS)
    clones=[copy.deepcopy(x) for x in original]
    rooms,npcs,mobs,items,quests=clones
    history=[copy.deepcopy(x) for x in clones]
    spawns=[]; help_topics={}; help_aliases={}
    stats=install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases)
    checks=_verify(rooms,npcs,mobs,spawns,quests,items,stats)
    for old,after in zip(history,clones):
        for k,v in old.items():
            if after[k] != v:
                candidate=copy.deepcopy(v)
                new_exits={dr:to for dr,to in after[k].get('exits',{}).items()
                           if to=='v3100_hall'}
                assert len(new_exits)==1, 'legacy room modified outside one safe gate '+k
                candidate['exits'].update(new_exits)
                assert candidate==after[k], 'legacy room overwritten outside safe gate '+k
        checks+=1
    assert help_topics.get('legendy') and help_aliases.get('legenda')=='legendy'
    checks+=2
    for path in ('world/equipment_help.py','world/legends_v3100.py','predeploy_check.py','predeploy_full.py','server.py'):
        ast.parse((ROOT / path).read_text(encoding='utf8'))
        checks+=1
    assert 'install as _install_legends_v3100' in (ROOT/'server.py').read_text(encoding='utf8')
    checks+=1
    return checks


def _check_sqlite_quest_isolation():
    import sqlite3
    from storage.db_quests import DatabaseQuestMixin
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.executescript("""
        CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,
           progress INTEGER DEFAULT 0,completed_at INTEGER DEFAULT 0,
           completion_count INTEGER DEFAULT 0,PRIMARY KEY(account_id,quest_id));
        CREATE TABLE quest_resource_progress_v0929(account_id INTEGER,quest_id TEXT,
           target_id TEXT,progress INTEGER,PRIMARY KEY(account_id,quest_id,target_id));
    """)
    db=DatabaseQuestMixin()
    db.conn=conn
    qid='v3100_crowns_story_1'; monster='v3100_crowns_enemy_0'
    db.start_quest(10,qid)
    db.start_quest(11,qid)
    assert db.quest(10,qid)['progress']==db.quest(11,qid)['progress']==0
    for _ in range(4):
        changed=db.increment_quest(10,monster)
        assert changed and changed[-1][0]==qid
    assert db.quest(10,qid)['progress']==4
    assert db.quest(11,qid)['progress']==0
    assert db.increment_quest(10,monster)==[]
    db.complete_quest(10,qid)
    assert db.quest(10,qid)['status']=='completed'
    assert db.quest(10,qid)['completion_count']==1
    assert db.quest(11,qid)['status']=='active'
    chrono='v3100_crowns_chronicle_1'
    db.start_quest(10,chrono)
    assert db.quest(10,chrono)['progress']==0
    db.set_quest_progress(10,chrono,8)
    db.complete_quest(10,chrono)
    assert db.repeat_quest_seconds_remaining(10,chrono,3600)>0
    db.restart_quest(10,chrono)
    assert db.quest(10,chrono)['progress']==0
    assert db.quest(10,chrono)['completion_count']==1
    conn.close()
    return 17


def run_regression_full(server):
    rooms=server.ROOMS;npcs=server.NPCS;mobs=server.MOB_TEMPLATES
    quests=server.QUESTS; items=server.ITEMS;spawns=server.MOB_SPAWNS
    V3100_LEGENDS_STATS=server.V3100_LEGENDS_STATS
    checks=_verify(rooms,npcs,mobs,spawns,quests,items,V3100_LEGENDS_STATS)
    from world.generation_systems import EXPLORATION_ZONE_ROOMS
    for spec in REALMS:
        region=spec[1]
        assert any(k==region for k in EXPLORATION_ZONE_ROOMS),'missing EP zone '+region
        checks+=1
    checks += _check_sqlite_quest_isolation()
    return checks

if __name__ == '__main__':
    print('LEGENDY v3.10.0 FAST:',run_regression_fast(),'checks PASS')
