# -*- coding: utf-8 -*-
"""SQLite :memory: quests v103, real DatabaseQuestMixin, no player data.

Validates persistence and actual kill event credit for raid bosses. NPC
conversations, resource drops and final award redemption require Windows TCP.
"""
from __future__ import annotations
import sqlite3


def run():
    from world.v10300_era_bez_granic import install as era_install
    from world.v10300_era_raids import install as raid_install
    import storage.db_quests as dbmod
    from storage.db_quests import DatabaseQuestMixin
    rooms={'v3000_eternal_6':{'exits':{}}};mobs={};spawns=[];npcs={};quests={};items={};recipes={};areas=[]
    era_install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    raid_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    checks=0
    def ok(v,why):
        nonlocal checks
        assert v,why
        checks+=1
    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''
                CREATE TABLE quests(account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
                    completed_at INTEGER NOT NULL DEFAULT 0,completion_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(account_id,quest_id));
                CREATE TABLE quest_resource_progress_v0929(account_id INTEGER NOT NULL,
                    quest_id TEXT NOT NULL,resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
            ''')
    db=DB();old=dbmod.QUESTS
    dbmod.QUESTS=quests
    try:
        for idx,(qid,quest) in enumerate(sorted(quests.items()),1):
            db.start_quest(idx,qid)
            first=db.quest(idx,qid)
            ok(first['status']=='active' and first['progress']==0,f'start {qid}')
            if qid.endswith(('raid_quest_1','raid_quest_2','raid_quest_3')):
                event=db.increment_quest(idx,quest['target'])
                ok((qid,1) in event,f'kill credit {qid}: {event}')
                ok(db.quest(idx,qid)['progress']==1,f'kill progress {qid}')
                ok(db.increment_quest(idx,quest['target'])==[],f'no duplicate credit {qid}')
            else:
                db.set_quest_progress(idx,qid,int(quest.get('needed',1)))
                ok(db.quest(idx,qid)['progress']==int(quest.get('needed',1)),f'progress {qid}')
            db.complete_quest(idx,qid)
            ok(db.quest(idx,qid)['status']=='completed',f'complete {qid}')
            ok(db.quest(idx,qid)['completion_count']==1,f'count {qid}')
            db.restart_quest(idx,qid)
            ok(db.quest(idx,qid)['status']=='active' and db.quest(idx,qid)['progress']==0,f'restart {qid}')
            ok(db.abandon_quest(idx,qid),f'abandon {qid}')
            ok(db.quest(idx,qid)['status']=='abandoned' and db.quest(idx,qid)['completion_count']==1,f'history {qid}')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
    finally:
        dbmod.QUESTS=old
        db.conn.close()
    ok(len(quests)==385,f'expected 385 quests, got {len(quests)}')
    return checks,len(quests)

if __name__=='__main__':
    n,q=run()
    print(f'ERA SQLITE: {n} checks PASS across {q} quests; no reward redemption tested',flush=True)
