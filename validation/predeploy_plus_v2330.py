# -*- coding: utf-8 -*-
"""ULTIMATE 60 PLUS: assertion-based property checks of actual game functions.

Called as part of existing gate 60, never on a live DB or production socket.
The in-memory inventory / quest fixtures deliberately use the actual DB mixins.
"""
from __future__ import annotations
from contextlib import closing
import random
import sqlite3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def combat_properties():
    from systems.adaptive_combat import (
        adaptive_dungeon_pressure_v2325 as pressure,
        adaptive_target_max_hp_v11330 as hp,
        adaptive_reward_multiplier_v11330 as reward,
        adaptive_target_incoming_fraction_v11330 as incoming,
    )
    checks = 0
    rng = random.Random(2330)
    for _ in range(550):
        level = rng.randint(1, 1000)
        floor = rng.randint(1, 1600)
        depth = {'crypt_floor': floor, 'rank': 'normal'}
        pct, harm = pressure(depth, level)
        assert pct >= 100 and harm >= 1.0, ('negative pressure', floor, level)
        # Greater dungeon depth must not become safer for the same character.
        harder, harder_harm = pressure({'crypt_floor': floor + 50}, level)
        assert harder >= pct and harder_harm >= harm, ('floor inverted', floor, level)
        # Higher character levels must not experience *more* level penalty.
        stronger, stronger_harm = pressure(depth, level + 50)
        assert stronger <= pct and stronger_harm <= harm, ('level inverted', floor, level)
        assert pressure({'training_dummy': True, 'crypt_floor': floor}, level) == (100, 1.0)
        dps = rng.randint(1, 10 ** 15)
        first = hp(1000, dps, depth, party_level=level)
        second = hp(1000, dps * 2, depth, party_level=level)
        assert second >= first >= 1000, ('scaling hp inverted', floor, level)
        assert reward(1000, second) >= reward(1000, first) >= 1.0
        assert incoming(depth, 4, player_level=level) >= incoming(depth, 1, player_level=level)
        checks += 8
    print(f'PLUS combat: {checks} deterministic actual-function assertions PASS', flush=True)
    return checks


def inventory_transfer_properties():
    from storage.db_inventory import DatabaseInventoryMixin
    class DB(DatabaseInventoryMixin):
        def __init__(self, conn): self.conn = conn
    checks = 0
    rng = random.Random(23301)
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript('''
            CREATE TABLE inventory(account_id INTEGER NOT NULL,item_id TEXT NOT NULL,
              quantity INTEGER NOT NULL,PRIMARY KEY(account_id,item_id));
            CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER NOT NULL,
              item_id TEXT NOT NULL,paid_silver INTEGER NOT NULL,quantity INTEGER NOT NULL,
              PRIMARY KEY(account_id,item_id,paid_silver));
            INSERT INTO inventory VALUES(1,'plus_test_nonmaterial',1200);
            INSERT INTO inventory VALUES(2,'plus_test_nonmaterial',0);
            INSERT INTO inventory VALUES(3,'plus_test_nonmaterial',0);
        ''')
        db = DB(conn)
        def balances():
            return tuple(db.item_qty(a,'plus_test_nonmaterial') for a in (1,2,3))
        for _ in range(240):
            src = rng.randint(1,3)
            dst = rng.randint(1,3)
            qty = rng.randint(1,90)
            old = balances()
            ok = db.transfer_inventory_item(src,dst,'plus_test_nonmaterial',qty)
            new = balances()
            assert ok == (src != dst and old[src-1] >= qty)
            assert all(v >= 0 for v in new) and sum(new) == 1200
            if not ok: assert new == old
            checks += 4
        # Trigger failure proves that an interrupted transfer cannot duplicate
        # an item or remove it from the sender after transaction rollback.
        src = next(a for a in (1,2,3) if db.item_qty(a,'plus_test_nonmaterial') > 0)
        dst = 1 if src != 1 else 2
        conn.execute('''CREATE TRIGGER plus_abort_transfer BEFORE UPDATE ON inventory
            WHEN NEW.account_id = %d BEGIN SELECT RAISE(ABORT,'test rollback'); END''' % dst)
        conn.execute('''CREATE TRIGGER plus_abort_insert BEFORE INSERT ON inventory
            WHEN NEW.account_id = %d BEGIN SELECT RAISE(ABORT,'test rollback'); END''' % dst)
        before = balances()
        caught=False
        try:
            db.transfer_inventory_item(src,dst,'plus_test_nonmaterial',1)
        except sqlite3.IntegrityError:
            caught=True  # Expected SQLite trigger abort during transfer.
        assert caught, 'Failed transfer incorrectly succeeded'
        assert balances() == before, 'Rollback lost/duplicated an item'
        conn.execute('DROP TRIGGER plus_abort_transfer')
        conn.execute('DROP TRIGGER plus_abort_insert')
        checks += 2
    print(f'PLUS item transfer: {checks} conservation/rollback assertions PASS', flush=True)
    return checks


def quest_isolation_properties():
    from data.quests import QUESTS
    from storage.db_quests import DatabaseQuestMixin
    class DB(DatabaseQuestMixin):
        def __init__(self, conn): self.conn = conn
    qid, quest = next(((k,v) for k,v in sorted(QUESTS.items()) if v.get('kind')=='kill'
                       and v.get('target') not in (None, '*')
                       and int(v.get('needed',0) or 0) >= 2), (None,None))
    if not qid:
        raise AssertionError('No kill quest can be regression-tested')
    target=quest['target']; needed=int(quest['needed'])
    checks=0
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.row_factory=sqlite3.Row
        conn.executescript('''
          CREATE TABLE quests(account_id INTEGER NOT NULL,quest_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',progress INTEGER NOT NULL DEFAULT 0,
            completed_at INTEGER NOT NULL DEFAULT 0,completion_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(account_id,quest_id));
          CREATE TABLE quest_resource_progress_v0929(account_id INTEGER NOT NULL,
            quest_id TEXT NOT NULL,resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
        ''')
        db=DB(conn)
        for account in (1111,2222):
            db.start_quest(account,qid)
        for _ in range(min(needed+5,250)):
            old=db.quest(1111,qid)['progress']
            db.increment_quest(1111,target)
            new=db.quest(1111,qid)['progress']
            assert new==min(needed,old+1)
            assert db.quest(2222,qid)['progress']==0
            checks+=2
        assert db.abandon_quest(1111,qid)
        assert db.quest(1111,qid)['progress']==0
        assert db.quest(2222,qid)['status']=='active'
        db.restart_quest(1111,qid)
        assert db.quest(1111,qid)['status']=='active'
        checks+=4
    print(f'PLUS quest isolation: {checks} real-quest progression assertions PASS', flush=True)
    return checks


def main():
    n=combat_properties()+inventory_transfer_properties()+quest_isolation_properties()
    if n < 5000:
        raise AssertionError('PLUS did not execute full property suite')
    print(f'ULTIMATE 60 PLUS: {n} sub-assertions PASS', flush=True)
    return n

if __name__=='__main__':
    main()
