# -*- coding: utf-8 -*-
"""v2.00.0 release checks; real linked rooms and SQLite kill/claim invariants."""
from __future__ import annotations
import sqlite3
from systems.parallel_worlds_v2000 import (install_parallel_worlds_v2000,REALMS,ISLANDS,ARENAS)
from systems import eras_pve_v2000 as pve


def run_regression():
    checks=0
    def check(expr,message):
        nonlocal checks
        assert expr,message
        checks+=1
    rooms={'v1900_dim_hub':{'name':'stub','exits':{}}};npcs={};shops={};mobs={};spawns=[];quests={};items={};sellers={}
    stats=install_parallel_worlds_v2000(rooms,npcs,shops,mobs,spawns,quests,items,sellers)
    check(stats['rooms']==103,'authored rooms')
    check(len(mobs)==78,'mob templates')
    check(len(items)==21,'faction rank rewards')
    check(len(quests)==15,'quest integration')
    check(len(npcs)==7,'NPCs')
    inverse={'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up'}
    for rid,room in rooms.items():
        for direction,dest in room['exits'].items():
            check(dest in rooms,(rid,direction,dest,'missing'))
            check(rooms[dest]['exits'].get(inverse[direction])==rid,(rid,direction,dest,'nonreciprocal'))
    for rid,mid in spawns:
        check(rid in rooms and mid in mobs,(rid,mid,'spawn'))
        check(isinstance(mobs[mid].get('drops'),dict),mid)
    for spec in REALMS:
        slug=spec[0]
        check(f'v2000_{slug}_boss' in mobs,slug)
    for spec in ISLANDS:
        check(f'v2000_sea_{spec[0]}_boss' in mobs,spec[0])
    for slug,*_ in ARENAS:
        check(f'v2000_arena_boss_{slug}' in mobs,slug)
        for w in range(3):check(f'v2000_arena_wave_{slug}_{w}' in mobs,(slug,w))
    check('v2000_ocean_hub' in rooms,'port')
    check('v2000_arena_hall' in rooms,'arena entrance')
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    try:
        conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,silver INTEGER NOT NULL DEFAULT 0,gold INTEGER NOT NULL DEFAULT 0,mithril INTEGER NOT NULL DEFAULT 0)')
        conn.execute('CREATE TABLE inventory(account_id INTEGER NOT NULL,item_id TEXT NOT NULL, quantity INTEGER NOT NULL, PRIMARY KEY(account_id,item_id))')
        conn.executemany('INSERT INTO characters(account_id,silver,gold,mithril) VALUES(?,?,?,?)',[(101,0,12,0),(102,0,0,0)])
        pve.init(conn)
        pve.init(conn)
        check(len(conn.execute("SELECT name FROM sqlite_master WHERE name LIKE 'v2000_%'").fetchall())==3,'idempotent schema')
        target=pve.faction_start(conn,101,'sny',now=1000)
        check(target=='v2000_sny_mob_8','faction target')
        pve.faction_start(conn,102,'sny',now=1000)
        check(not pve.record_kill(conn,[101,102],'v2000_smoki_mob_8'),'other target')
        check(len(pve.record_kill(conn,[101,102],'v2000_sny_mob_8'))==2,'party contract credit')
        check(not pve.record_kill(conn,[101,102],'v2000_sny_mob_8'),'no duplicate credit')
        coins,rep,balance=pve.claim_faction(conn,101,'sny',now=1200)
        check(coins==360*5500 and rep==25 and balance==coins+1200,'faction payout preserves older gold')
        try:pve.claim_faction(conn,101,'sny',now=1200)
        except ValueError:checks+=1
        else:raise AssertionError('double faction payout')
        try:pve.faction_start(conn,101,'sny',now=1201)
        except ValueError:checks+=1
        else:raise AssertionError('contract cooldown')
        for t in (5000,9000,13000):
            pve.faction_start(conn,101,'sny',now=t)
            pve.record_kill(conn,[101],'v2000_sny_mob_8')
            pve.claim_faction(conn,101,'sny',now=t+10)
        check(pve.fame_status(conn,101)['sny']==100,'reputation 100')
        rank,iid,rep=pve.claim_rank(conn,101,'sny')
        check(rank==1 and iid in items,'faction artifact first rank')
        check(conn.execute('SELECT quantity FROM inventory WHERE account_id=101 AND item_id=?',(iid,)).fetchone()[0]==1,'rank delivered')
        try:pve.claim_rank(conn,101,'sny')
        except ValueError:checks+=1
        else:raise AssertionError('duplicate rank claim')
        challenge=pve.arena_start(conn,101,'zelazna',now=1000)
        check(challenge=='v2000_arena_boss_zelazna','arena target')
        check(bool(pve.record_kill(conn,[101],'v2000_arena_boss_zelazna')),'boss credit before waves (AoE safe)')
        check(conn.execute("SELECT state FROM v2000_arena_trials WHERE account_id=101 AND challenge='zelazna'").fetchone()[0]==1,'boss alone no payout')
        check(not pve.record_kill(conn,[101],'v2000_arena_boss_zelazna'),'boss one-time only')
        for j in range(3):
            check(bool(pve.record_kill(conn,[101],f'v2000_arena_wave_zelazna_{j}')),'distinct wave')
            check(not pve.record_kill(conn,[101],f'v2000_arena_wave_zelazna_{j}'),'repeat wave')
        check(conn.execute("SELECT state FROM v2000_arena_trials WHERE account_id=101 AND challenge='zelazna'").fetchone()[0]==2,'completed after all kinds regardless of AoE order')
        check(not pve.record_kill(conn,[101],'v2000_arena_boss_zelazna'),'no duplicate boss')
        prize,wins,balance=pve.claim_arena(conn,101,'zelazna',now=2000)
        check(prize==280*11000 and wins==1 and balance>=coins+1200+prize,'arena payout')
        try:pve.claim_arena(conn,101,'zelazna',now=2001)
        except ValueError:checks+=1
        else:raise AssertionError('duplicate arena payout')
        try:pve.arena_start(conn,101,'zelazna',now=2001)
        except ValueError:checks+=1
        else:raise AssertionError('arena cooldown')
        check(conn.execute('SELECT silver FROM characters WHERE account_id=102').fetchone()[0]==0,'no unearned reward')
        # The boss may also fall LAST; party credit belongs only to members
        # who actually accepted the same trial (no extra world-wide grants).
        pve.arena_start(conn,101,'zywiolow',now=3000)
        pve.arena_start(conn,102,'zywiolow',now=3000)
        for j in range(3):
            check(len(pve.record_kill(conn,[101,102],f'v2000_arena_wave_zywiolow_{j}'))==2,'party waves')
        check(len(pve.record_kill(conn,[101,102],'v2000_arena_boss_zywiolow'))==2,'party boss last')
        p1,w1,b1=pve.claim_arena(conn,101,'zywiolow',now=3050)
        p2,w2,b2=pve.claim_arena(conn,102,'zywiolow',now=3050)
        check(p1==p2 and w1==w2==1 and b1>b2,'per-account party payout')

        check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    finally:conn.close()
    return checks

if __name__=='__main__':
    print('PARALLEL WORLDS v2.00.0:',run_regression(),'checks PASS')
