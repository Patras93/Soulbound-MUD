# -*- coding: utf-8 -*-
"""v104 stage 9: real participation and once-per-rotation award; RAM SQLite only.

Never connects to TCP, user databases or the host game server.
"""
from __future__ import annotations
from types import SimpleNamespace
import sqlite3
from systems.world_invasions_v10400 import (
    create_schema, rotation, status, record_real_defeat, reward_status,
    REWARD_ITEM_ID, REQUIRED_PER_FRONT,
)


def run():
    checks = 0
    def ok(value, why):
        nonlocal checks
        if not value:
            raise AssertionError(why)
        checks += 1
    now = 1793350800
    slot = rotation(now)
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY)')
    db.execute('CREATE TABLE inventory (account_id INTEGER, item_id TEXT, quantity INTEGER, '
               'PRIMARY KEY(account_id,item_id), FOREIGN KEY(account_id) REFERENCES accounts(id))')
    db.executemany('INSERT INTO accounts(id) VALUES (?)', [(1,), (2,), (3,), (4,)])
    create_schema(db)
    create_schema(db)
    ok(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','schema valid')

    def mob(slug,kind,n):
        return SimpleNamespace(alive=False, template_id=f'v10400_{slug}_{kind}',
                               room_id=f'v10400_{slug}_10', key=f'worldspawn_{slug}_{kind}_{n}',
                               respawn_at=float(now+100+n))
    def people(*ids):return tuple(SimpleNamespace(account_id=i) for i in ids)
    fronts=slot['fronts']
    for ix,slug in enumerate(fronts):
        for n in range(REQUIRED_PER_FRONT):
            fight=mob(slug,'mob_3',n)
            participants = people(*( (1,2) if ix==0 else ((2,3) if ix==1 else (3,))))
            got=record_real_defeat(db,fight,{'name':'potwór'},now=now,recipients=participants)
            ok(got == ('front',slug,n+1),f'front {slug} kill {n}')
            ok(record_real_defeat(db,fight,{'name':'potwór'},now=now,recipients=people(4)) is None,
               f'dup kill {slug} {n}')
    ok(db.execute('SELECT COUNT(*) FROM world_invasion_participants_v10400').fetchone()[0]==3,
       'only actual players, once each')
    ok(db.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]==0,'no early rewards')
    final_slug=fronts[-1]
    boss=mob(final_slug,'boss_2',200)
    got=record_real_defeat(db,boss,{'name':'finał'},now=now,recipients=people(2,4))
    ok(got==('final',final_slug,REQUIRED_PER_FRONT),'boss finishes')
    ok(status(db,now)['completed'],'completed flag')
    for uid in (1,2,3,4):
        row=db.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                       (uid,REWARD_ITEM_ID)).fetchone()
        ok(row is not None and row[0]==1,f'player {uid} gets one seal')
        ok('pieczęcie zwycięstwa 1' in reward_status(db,uid,now),f'NVDA count {uid}')
    ok(db.execute('SELECT COUNT(*) FROM world_invasion_rewards_v10400').fetchone()[0]==4,
       'one receipt per participant')
    ok(record_real_defeat(db,boss,{'name':'finał'},now=now,recipients=people(4)) is None,
       'no duplicate final')
    ok(db.execute('SELECT SUM(quantity) FROM inventory').fetchone()[0]==4,
       'no duplicated items')

    # Force a constraint failure on a new rotation: neither reward receipt nor
    # victory may persist when delivery fails. Retry must succeed afterward.
    later=slot['expires_at']+10
    nextslot=rotation(later)
    for slug in nextslot['fronts']:
        for n in range(REQUIRED_PER_FRONT):
            record_real_defeat(db,mob(slug,'mob_3',n),{'name':'real'},now=later,recipients=people(1))
    db.execute('CREATE TRIGGER block_seal BEFORE INSERT ON inventory '
               f"WHEN NEW.item_id='{REWARD_ITEM_ID}' BEGIN SELECT RAISE(ABORT,'no award'); END")
    # Player 1 already has a seal, which triggers UPDATE rather than INSERT.
    db.execute('CREATE TRIGGER block_seal_update BEFORE UPDATE ON inventory '
               f"WHEN NEW.item_id='{REWARD_ITEM_ID}' BEGIN SELECT RAISE(ABORT,'no award'); END")
    testboss=mob(nextslot['fronts'][-1],'boss_2',999)
    try:
        record_real_defeat(db,testboss,{'name':'boss'},now=later,recipients=people(1))
    except sqlite3.DatabaseError:
        checks += 1
    else:
        raise AssertionError('failed reward silently accepted')
    ok(not status(db,later)['completed'],'failure rolls back victory')
    ok(db.execute('SELECT COUNT(*) FROM world_invasion_rewards_v10400 WHERE slot=?',
                  (nextslot['slot'],)).fetchone()[0]==0,'failure rolls back receipts')
    db.execute('DROP TRIGGER block_seal')
    db.execute('DROP TRIGGER block_seal_update')
    ok(record_real_defeat(db,testboss,{'name':'boss'},now=later,recipients=people(1))[0]=='final',
       'same fight retry is recoverable')
    ok(db.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',
                  (REWARD_ITEM_ID,)).fetchone()[0]==2,'one seal per each completed rotation')
    ok(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite consistency')
    db.close()
    return checks

if __name__=='__main__':
    print(f'V104 ETAP 9 NAGRODY INWAZJI: {run()} PASS')
