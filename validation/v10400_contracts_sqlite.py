# -*- coding: utf-8 -*-
"""Native quest SQLite test for all 30 v104 repeatable endgame contracts."""
import sqlite3
import storage.db_quests as dbmod
from storage.db_quests import DatabaseQuestMixin
from world.v10400_krainy_5001_10000 import REGIONS


def run():
    from world import dynamic_content as world
    checks=0
    def ok(value,label):
        nonlocal checks
        if not value:raise AssertionError(label)
        checks+=1
    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''CREATE TABLE quests(account_id INTEGER NOT NULL,
                 quest_id TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',
                 progress INTEGER NOT NULL DEFAULT 0, completed_at INTEGER NOT NULL DEFAULT 0,
                 completion_count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(account_id,quest_id));
               CREATE TABLE quest_resource_progress_v0929(account_id INTEGER NOT NULL,
                 quest_id TEXT NOT NULL,resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
            ''')
    db=DB();old=dbmod.QUESTS;dbmod.QUESTS=world.QUESTS
    try:
        for slug,*_ in REGIONS:
            for typ in ('daily','weekly','invasion'):
                qid=f'v10400_contract_{slug}_{typ}'
                q=world.QUESTS[qid]
                for account in (101,202):
                    db.start_quest(account,qid)
                    ok(db.quest(account,qid)['status']=='active',f'active {qid}:{account}')
                for _ in range(q['needed']):
                    credit=db.increment_quest(101,q['target'])
                ok((qid,q['needed']) in credit,f'target progress {qid}')
                ok(db.quest(202,qid)['progress']==0,f'no party leakage {qid}')
                db.complete_quest(101,qid)
                ok(db.quest(101,qid)['completion_count']==1,f'completed once {qid}')
                remaining=db.repeat_quest_seconds_remaining(101,qid,q['repeat_cooldown'])
                ok(0 < remaining <= q['repeat_cooldown'], f'calendar cooldown {qid}')
                ok(db.quest(202,qid)['status']=='active',f'other player still active {qid}')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
    finally:
        dbmod.QUESTS=old;db.conn.close()
    return checks

if __name__=='__main__':print(f'V104 CONTRACT SQLITE {run()} PASS',flush=True)
