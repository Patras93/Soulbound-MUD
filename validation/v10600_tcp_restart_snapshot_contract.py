# -*- coding: utf-8 -*-
"""Test read-only v106 TCP persistence comparisons without opening network sockets.

This verifies that the real restart test detects loss/duplication of quests,
coin rewards, inventory rewards and profession storage items.
"""
from __future__ import annotations
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch
from validation import v10600_tcp_world_smoke as tcp_smoke
from validation.v10600_tcp_world_smoke import _quest_persistence_snapshot


def run():
    checks=0
    def ok(value,msg):
        nonlocal checks
        if not value:raise AssertionError(msg)
        checks+=1
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-restart-contract-') as dirname:
        path=Path(dirname)/'disposable.sqlite'
        db=sqlite3.connect(path)
        db.executescript('''
          CREATE TABLE accounts(id INTEGER PRIMARY KEY,username TEXT NOT NULL);
          CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER);
          CREATE TABLE characters(account_id INTEGER,silver INTEGER,gold INTEGER);
          CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER);
          CREATE TABLE profession_storage(account_id INTEGER,item_id TEXT,quantity INTEGER);
          INSERT INTO accounts VALUES(1,'tcp1061'),(2,'tcp1062'),(3,'real_player');
          INSERT INTO quests VALUES(1,'v10600_story_1','completed',1),
                                   (2,'v10600_hunt_1','active',0),
                                   (3,'v10600_story_1','active',0);
          INSERT INTO characters VALUES(1,123,0),(2,1,0),(3,900,100);
          INSERT INTO inventory VALUES(1,'v10600_reward_1',2),(3,'v10600_reward_1',999);
          INSERT INTO profession_storage VALUES(1,'v10600_ore_1',3);
        ''')
        db.commit()
        # Na Windows samo `with sqlite3.connect(...)` NIE zamyka uchwytu.
        # Wymuszamy jawne close() i sprawdzamy je także na Linux/macOS.
        open_connections=[]
        original_connect=sqlite3.connect
        class TrackedConnection(sqlite3.Connection):
            explicit_close=False
            def close(self):
                self.explicit_close=True
                return super().close()
        def tracked_connect(*args,**kwargs):
            kwargs['factory']=TrackedConnection
            connection=original_connect(*args,**kwargs)
            open_connections.append(connection)
            return connection
        with patch.object(tcp_smoke.sqlite3,'connect',tracked_connect):
            reference=_quest_persistence_snapshot(path)
        ok(bool(open_connections) and all(c.explicit_close for c in open_connections),
           'snapshot closes all SQLite connections explicitly')
        open_connections.clear()
        ok(len(reference)==4,'four durable record groups')
        ok(len(reference[0])==2,'only synthetic TCP quests')
        ok(len(reference[1])==2,'only synthetic TCP wallets')
        ok(len(reference[2])==1,'only synthetic TCP inventory')
        ok(len(reference[3])==1,'only synthetic TCP crafting storage')
        ok(_quest_persistence_snapshot(path)==reference,'read-only stable')
        ok(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','integrity')
        pristine=sqlite3.connect(':memory:')
        db.backup(pristine)
        changes=(
            ('UPDATE quests SET status="active" WHERE account_id=1',0),
            ('UPDATE quests SET progress=2 WHERE account_id=1',0),
            ('UPDATE characters SET silver=silver+1 WHERE account_id=1',1),
            ('UPDATE characters SET gold=gold+1 WHERE account_id=1',1),
            ('UPDATE inventory SET quantity=3 WHERE account_id=1',2),
            ('UPDATE profession_storage SET quantity=4 WHERE account_id=1',3),
            ("INSERT INTO quests VALUES(1,'v10600_story_2','active',0)",0),
            ("INSERT INTO inventory VALUES(1,'v10600_reward_2',1)",2),
            ("INSERT INTO profession_storage VALUES(1,'v10600_ore_2',1)",3),
        )
        for query,position in changes:
            db.execute(query)
            db.commit()
            changed=_quest_persistence_snapshot(path)
            ok(changed!=reference,'detect state change: '+query)
            ok(changed[position]!=reference[position],'detect correct group: '+query)
            pristine.backup(db)
            ok(_quest_persistence_snapshot(path)==reference,'fixture restored from clean backup')
        db.execute('UPDATE characters SET silver=silver+1 WHERE account_id=3')
        db.commit()
        ok(_quest_persistence_snapshot(path)==reference,'non-test user excluded')
        pristine.close()
        db.close()
        ok(path.exists(),'test db still on disk')
    print('V106 TCP RESTART SQLITE SNAPSHOT CONTRACT:',checks,'PASS',flush=True)
    return checks

if __name__=='__main__':run()
