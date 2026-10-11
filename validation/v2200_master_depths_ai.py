# -*- coding: utf-8 -*-
"""v2.20.0: bounded AI, all mastery paths, transactional rewards and Ocean maps.

All fixtures are isolated: in-memory SQLite and disposable catalogs, no live DB.
Full NPC conversations/real TCP combats remain NOT TESTED by this suite.
"""
from __future__ import annotations
from collections import deque
from types import SimpleNamespace
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import tactical_ai_v2200 as tactics
from systems import profession_mastery_v2200 as master
from systems import ocean_depths_v2200 as depths


def run_regression():
    count=0
    def check(condition, message):
        nonlocal count
        assert condition, message
        count+=1
    check(len(master.SPECIALTIES)==14, 'all 14 professions')
    for profession,options in master.SPECIALTIES.items():
        check(len(options)==3 and len(set(options))==3, f'specialties {profession}')
        check(master.canonical(profession)==profession, f'canonical {profession}')
    check(tactics.ROLES==frozenset(('obronca','dowodca','uzdrowiciel','mag','lowca','wojownik','nekromanta')), 'roles')
    mob=lambda key,hp:SimpleNamespace(key=key,template_id='dummy',hp=hp,alive=True,room_id='test',engaged_by='p',combat_turn=3)
    protector,friend=mob('guard',100),mob('friend',25)
    check(tactics.select_support(protector,{'tactical_role_v2200':'obronca'},[protector,friend],100,lambda _:100)['kind']=='guard','guard')
    check(tactics.select_support(protector,{'tactical_role_v2200':'uzdrowiciel'},[friend],100,lambda _:100)['kind']=='heal','healer')
    friend.room_id='other'
    check(tactics.select_support(protector,{'tactical_role_v2200':'obronca'},[friend],100,lambda _:100) is None,'no foreign room')
    check(tactics.select_support(protector,{'tactical_role_v2200':'none'},[],100,lambda _:100) is None,'default role off')
    # Each contract uses its own account and the saved profession action count.
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER)')
    conn.executemany('INSERT INTO characters VALUES (?,?,0,0)',[(i,5000) for i in range(1,15)])
    master.init(conn);master.init(conn)
    check(len(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'profession_%_v2200'").fetchall())==2,'idempotent schema')
    for i,(profession,specialties) in enumerate(master.SPECIALTIES.items(),1):
        try:master.unlock(conn,i,profession,specialties[0],99,now=10000)
        except ValueError:count+=1
        else:raise AssertionError('must reject too-low level')
        check(master.unlock(conn,i,profession,specialties[0],100,now=10000)==100,'first unlock')
        try:master.unlock(conn,i,profession,specialties[0],100,now=10000)
        except ValueError:count+=1
        else:raise AssertionError('duplicate unlock')
        check(master.unlock(conn,i,profession,specialties[1],250,now=10000)==250,'second unlock')
        check(master.unlock(conn,i,profession,specialties[2],450,now=10000)==450,'third unlock')
        goal=master.start_order(conn,i,profession,450,100,now=10000)
        check(goal>=3,'nonempty order')
        check('0/' in master.status(conn,i,profession,100),'initial actions')
        try:master.claim(conn,i,profession,450,100,now=10100)
        except ValueError:count+=1
        else:raise AssertionError('not complete')
        balance_before=conn.execute('SELECT silver FROM characters WHERE account_id=?',(i,)).fetchone()[0]
        gained,balance_after=master.claim(conn,i,profession,450,100+goal,now=10100)
        check(gained>0 and balance_after==balance_before+gained,'reward delivered')
        check(conn.execute('SELECT silver FROM characters WHERE account_id=?',(i,)).fetchone()[0]==balance_after,'money durable')
        try:master.claim(conn,i,profession,450,100+goal,now=10100)
        except ValueError:count+=1
        else:raise AssertionError('double claim')
        try:master.start_order(conn,i,profession,450,200,now=10101)
        except ValueError:count+=1
        else:raise AssertionError('cooldown')
        check(master.start_order(conn,i,profession,450,200,now=10100+master.COOLDOWN)>0,'renewal')
        master.abandon(conn,i,profession)
        check(master.status(conn,i,profession,200)=='abandoned','abandon')
    # Reload on same SQLite database, ensuring no ephemeral ledger.
    check(conn.execute('SELECT COUNT(*) FROM profession_specialties_v2200').fetchone()[0]==42,'all specialties saved')
    check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','integrity')
    # Real room IDs and reciprocal graph: catch broken exits before deploy.
    room={'v2000_ocean_hub':{'exits':{'down':'nexus'} }};npcs={};shops={};mobs={};spawns=[];quests={};items={};sellers={}
    navy=SimpleNamespace(ENEMIES={}, MATERIALS={})
    stats=depths.install(room,npcs,shops,mobs,spawns,quests,items,sellers,navy)
    check(stats['rooms']==17 and stats['mobs']==16 and stats['quests']==4,'catalog sizes')
    for slug,*_ in depths.REGIONS:
        check(f'v2200_{slug}_boss' in mobs,'boss '+slug)
        check(f'v2200_{slug}_hunt' in quests,'hunt '+slug)
        check(f'glebiny_{slug}' in navy.ENEMIES,'fleet '+slug)
        check(navy.MATERIALS[f'glebiny_{slug}'] in items,'real material '+slug)
    expected={'north':'south','east':'west','south':'north','west':'east',
              'northeast':'southwest','southwest':'northeast'}
    for rid,definition in room.items():
        if rid=='v2000_ocean_hub':continue
        for direction,dest in definition['exits'].items():
            check(dest in room,f'missing exit {rid}->{dest}')
            back=expected[direction]
            check(room[dest]['exits'].get(back)==rid,f'broken reverse {rid}.{direction} -> {dest}.{back}')
    seen={'v2000_ocean_hub'};todo=deque(seen)
    while todo:
        rid=todo.popleft()
        for target in room[rid].get('exits',{}).values():
            if target in room and target not in seen:seen.add(target);todo.append(target)
    check(len(seen)==len(room),'reachable rooms')
    check(len(spawns)==16,'spawn count')
    check(all(v['reward_silver']>100 for v in quests.values()),'all new quests reward money')
    # The original catalogs must refuse a duplicate install.
    try:depths.install(room,npcs,shops,mobs,spawns,quests,items,sellers,navy)
    except RuntimeError:count+=1
    else:raise AssertionError('duplicate install allowed')
    return count


if __name__=='__main__':
    print('SOULBOUND 2.20.0 SCENARIOS:',run_regression(),'PASS')
