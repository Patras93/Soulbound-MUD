# -*- coding: utf-8 -*-
"""Real quest SQLite ledger: all 600 v105 kill quests and 40 physical bosses.

Tests quest acceptance, real increment_quest processing, completion and
isolation for two accounts. This is NOT real battle or TCP and never touches
production SQLite. Quest rewards after defeating monsters are tested separately.
"""
from __future__ import annotations
from collections import Counter
import sqlite3
import storage.db_quests as dbmod
from storage.db_quests import DatabaseQuestMixin
from world.dynamic_content import QUESTS,MOB_TEMPLATES,MOB_SPAWNS
from world.v10500_region_index import REGIONS


class TemporaryQuestDB(DatabaseQuestMixin):
    def __init__(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE quests(account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
          completed_at INTEGER NOT NULL DEFAULT 0, completion_count INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY(account_id,quest_id));
        CREATE TABLE quest_resource_progress_v0929(
          account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
          resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
        ''')


def run():
    quests=[];boss_ids=set()
    for slug,*_ in REGIONS:
        p='v10500_'+slug
        quests.extend(f'{p}_story_{i:02d}' for i in range(1,21))
        quests.extend(f'{p}_hunt_{i:02d}' for i in range(1,11))
        boss_ids.update((p+'_boss_1',p+'_boss_2'))
    assert len(quests)==600 and len(boss_ids)==40
    db=TemporaryQuestDB()
    old=dbmod.QUESTS;dbmod.QUESTS=QUESTS
    checks=0;completed=Counter()
    try:
        for qid in quests:
            q=QUESTS[qid]
            assert q['kind']=='kill' and q['target'] in MOB_TEMPLATES,qid;checks+=1
            target=q['target'];needed=int(q['needed'])
            assert (0<needed<=6) and any(t==target for _,t in MOB_SPAWNS),qid;checks+=1
            assert db.start_quest(101,qid) is not False,qid;checks+=1
            assert db.quest(101,qid)['status']=='active' and db.quest(101,qid)['progress']==0;checks+=1
            for n in range(needed):
                credited=db.increment_quest(101,target)
                assert (qid,n+1) in credited,(qid,credited,n);checks+=1
            # Repeated kill may have progressed other quests but not completed this one.
            assert db.quest(101,qid)['progress']==needed,qid;checks+=1
            db.complete_quest(101,qid)
            row=db.quest(101,qid)
            assert row['status']=='completed' and row['completion_count']==1,qid;checks+=1
            completed['boss' if target in boss_ids else 'normal']+=1
        for boss in sorted(boss_ids):
            # A new separate character may earn the same boss quest without
            # affecting the first player's completed quest or reward count.
            qid=next(qid for qid in quests if QUESTS[qid]['target']==boss)
            assert db.start_quest(202,qid) is not False;checks+=1
            assert db.quest(202,qid)['progress']==0;checks+=1
            credit=db.increment_quest(202,boss)
            assert (qid,1) in credit,(qid,credit);checks+=1
            assert db.quest(101,qid)['status']=='completed';checks+=1
            assert db.increment_quest(202,boss)==[],(qid,'duplicate boss quest progress');checks+=1
            db.complete_quest(202,qid)
            assert db.quest(202,qid)['completion_count']==1;checks+=1
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
        assert completed['normal']+completed['boss']==600;checks+=1
        return checks,dict(completed)
    finally:
        dbmod.QUESTS=old
        db.conn.close()

if __name__=='__main__':
    count,types=run()
    print(f'V105 QUEST SQLITE 600 KILL QUESTS: {count} PASS; {types}; two-account boss rewards isolated',flush=True)
