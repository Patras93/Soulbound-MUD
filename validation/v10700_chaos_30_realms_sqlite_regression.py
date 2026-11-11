# -*- coding: utf-8 -*-
"""Realny licznik SQLite dla 25 nowych krain v107, różni gracze i cele."""
from __future__ import annotations
import sqlite3
from validation.v10700_chaos_chapter_one_regression import fixture
from world.v10700_chaos_chapter_one import install as install_first,prefix
from world.v10700_chaos_chapters_2_6 import install as install_next
from world.v10700_region_index_chapters_2_6 import ALL_NEXT
from storage.db_quests import DatabaseQuestMixin, QUESTS


def run():
    v=fixture();install_first(*v);install_next(*v)
    _,mobs,spawns,npcs,quests,items,*_=v
    ids={qid:q for qid,q in quests.items() if qid.startswith('v10700_chaos_') and
         qid not in QUESTS}
    assert len(ids)==1200
    QUESTS.update(ids)
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.executescript('''
    CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,
     progress INTEGER DEFAULT 0,completed_at INTEGER DEFAULT 0,
     completion_count INTEGER DEFAULT 0,PRIMARY KEY(account_id,quest_id));
    CREATE TABLE quest_resource_progress_v0929(account_id INTEGER,quest_id TEXT,
     target_id TEXT,progress INTEGER,PRIMARY KEY(account_id,quest_id,target_id));
    ''')
    db=DatabaseQuestMixin();db.conn=conn
    checks=0
    def check(ok,msg):
        nonlocal checks
        assert ok,msg
        checks+=1
    try:
        for i,(slug,*_) in enumerate(ALL_NEXT):
            p=prefix(slug)
            account=4100+i
            hunt=p+'_hunt_01';q=quests[hunt];target=q['target']
            db.start_quest(account,hunt);db.start_quest(account+100,hunt)
            check(db.quest(account,hunt)['status']=='active','quest accepted '+slug)
            for n in range(q['needed']):
                check(db.increment_quest(account,target)==[(hunt,n+1)],'kill credit '+slug)
            check(db.increment_quest(account,target)==[],'max quest count '+slug)
            check(db.quest(account+100,hunt)['progress']==0,'isolated account '+slug)
            db.complete_quest(account,hunt)
            check(db.quest(account,hunt)['completion_count']==1,'history '+slug)
            db.restart_quest(account,hunt)
            check(db.quest(account,hunt)['progress']==0 and
                  db.quest(account,hunt)['completion_count']==1,'repeat safe '+slug)
            collect=p+'_collect_01';material=quests[collect]['target']
            check(material in items and any(m.get('drops',{}).get(material,0)>0
                  for m in mobs.values()),'real drop '+slug)
            db.start_quest(account,collect)
            db.set_quest_progress(account,collect,quests[collect]['needed'])
            check(db.quest(account,collect)['progress']==quests[collect]['needed'],
                  'collect stored '+slug)
            elite=p+'_hunt_15'
            db.start_quest(account,elite)
            check(quests[elite]['needed']==1 and not quests[elite]['repeatable'],
                  'one-time elite '+slug)
            check(db.increment_quest(account,quests[elite]['target'])==[(elite,1)],
                  'elite credited '+slug)
        print(f'V107 SQLITE 25 NOWYCH KRAIN: {checks} PASS')
        return checks
    finally:
        conn.close()
        for qid in ids:QUESTS.pop(qid,None)

if __name__=='__main__':run()
