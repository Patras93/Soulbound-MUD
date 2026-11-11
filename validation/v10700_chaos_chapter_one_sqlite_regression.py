# -*- coding: utf-8 -*-
"""SQLite: zaakceptowane questy v107, zbiór surowców, historie niezależnych kont."""
from __future__ import annotations
import sqlite3
from validation.v10700_chaos_chapter_one_regression import fixture
from world.v10700_chaos_chapter_one import install, CHAPTER_ONE, prefix
from storage.db_quests import DatabaseQuestMixin, QUESTS


def run():
    reg=fixture();install(*reg)
    _,mobs,spawns,npcs,quests,items,_,*_=reg
    new={k:v for k,v in quests.items() if k.startswith('v10700_chaos_')}
    assert len(new)==200 and not (new.keys() & QUESTS.keys())
    QUESTS.update(new)
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.executescript('''
    CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT,
      progress INTEGER DEFAULT 0, completed_at INTEGER DEFAULT 0,
      completion_count INTEGER DEFAULT 0, PRIMARY KEY(account_id, quest_id));
    CREATE TABLE quest_resource_progress_v0929(account_id INTEGER, quest_id TEXT,
      target_id TEXT, progress INTEGER,PRIMARY KEY(account_id,quest_id,target_id));
    ''')
    db=DatabaseQuestMixin();db.conn=conn
    checks=0
    def check(ok,why):
        nonlocal checks
        assert ok,why
        checks+=1
    try:
        for slug,*_ in CHAPTER_ONE:
            p=prefix(slug)
            hunt=f'{p}_hunt_01'
            target=quests[hunt]['target']
            need=quests[hunt]['needed']
            db.start_quest(200,hunt);db.start_quest(201,hunt)
            check(db.quest(200,hunt)['status']=='active','quest accepted')
            for index in range(need):
                check(db.increment_quest(200,target)==[(hunt,index+1)],'true kill counter')
            check(db.increment_quest(200,target)==[],'no credit beyond goal')
            check(db.quest(201,hunt)['progress']==0,'second account unaffected')
            db.complete_quest(200,hunt)
            check(db.quest(200,hunt)['status']=='completed','native completion')
            check(db.quest(200,hunt)['completion_count']==1,'completion history persists')
            db.restart_quest(200,hunt)
            check(db.quest(200,hunt)['progress']==0 and db.quest(200,hunt)['completion_count']==1,
                  'restarted hunt retains previous history')
            material=f'{p}_collect_01'
            db.start_quest(200,material)
            key=quests[material]['target']
            check(any(v.get('drops',{}).get(key,0)>0 for v in mobs.values()),
                  'material can be obtained from real enemy')
            db.set_quest_progress(200,material,quests[material]['needed'])
            check(db.quest(200,material)['progress']==quests[material]['needed'],
                  'native collect progress persists')
            elite=f'{p}_hunt_15'
            db.start_quest(200,elite)
            check(quests[elite]['repeatable']==False and quests[elite]['needed']==1,
                  'elite target one-time solo quest')
            check(db.increment_quest(200,quests[elite]['target'])==[(elite,1)],
                  'native elite kill counted')
        print('V107 ROZDZIAL I SQLITE:',checks,'PASS, 5 regionów, osobne konta')
        return checks
    finally:
        conn.close()
        for k in new: QUESTS.pop(k,None)

if __name__=='__main__':run()
