# -*- coding: utf-8 -*-
"""42 actual quest targets credited through storage.db_quests in isolated SQLite.

Party kill handling is represented by per-recipient API calls, not by simulated
combat or a TCP server. Confirmed both players independent and one turn-in each.
"""
import sqlite3
import storage.db_quests as dbmod
from storage.db_quests import DatabaseQuestMixin
from world import dynamic_content as world
from world.v10400_raids_12_25 import RAIDS


def run():
    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''
            CREATE TABLE quests(account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
              completed_at INTEGER NOT NULL DEFAULT 0, completion_count INTEGER NOT NULL DEFAULT 0,
              PRIMARY KEY(account_id,quest_id));
            CREATE TABLE quest_resource_progress_v0929(
              account_id INTEGER NOT NULL,quest_id TEXT NOT NULL,
              resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
            ''')
    checks=0
    def ok(value,message):
        nonlocal checks
        if not value:raise AssertionError(message)
        checks+=1
    db=DB()
    previous=dbmod.QUESTS
    dbmod.QUESTS=world.QUESTS
    try:
        for number,*_ in RAIDS:
            prefix=f'v10400_raid_{number:02d}'
            for s in (1,2,3):
                qid=f'{prefix}_raid_quest_{s}'
                boss=f'{prefix}_boss_{s}'
                ok(world.QUESTS[qid]['target']==boss,f'quest target {qid}')
                for account in (101,202):
                    ok(db.start_quest(account,qid) is not False,f'quest start {qid}/{account}')
                    ok(db.quest(account,qid)['progress']==0,f'initial progress {qid}/{account}')
                credited=db.increment_quest(101,boss)
                ok((qid,1) in credited,f'first player credit {qid}')
                ok(db.quest(202,qid)['progress']==0,f'party leakage {qid}')
                ok((qid,1) in db.increment_quest(202,boss),f'other player credit {qid}')
                for account in (101,202):
                    ok(db.increment_quest(account,boss)==[],f'duplicate kill credit {qid}/{account}')
                db.complete_quest(101,qid)
                ok(db.quest(101,qid)['status']=='completed',f'completed first {qid}')
                ok(db.quest(202,qid)['status']=='active',f'leaked turn-in {qid}')
                db.complete_quest(202,qid)
                ok(db.quest(202,qid)['status']=='completed',f'completed second {qid}')
                ok(db.quest(101,qid)['completion_count']==1 and db.quest(202,qid)['completion_count']==1,
                   f'no double reward {qid}')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    finally:
        dbmod.QUESTS=previous
        db.conn.close()
    return checks

if __name__=='__main__':
    print(f'V104 PARTY SQLite 42 BOSSÓW: {run()} kontroli PASS',flush=True)
