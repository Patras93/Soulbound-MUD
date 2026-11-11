# -*- coding: utf-8 -*-
"""Native per-account quest counter smoke test for stage7 insects."""
from __future__ import annotations
import sqlite3
from validation.v10700_insects_expansion_regression import fixture
from world.v10700_insects_expansion import install as stage6_install
from world.v10700_insects_wildlife_plus import install, PREFIX
from storage.db_quests import DatabaseQuestMixin, QUESTS


def run():
    reg=fixture();stage6_install(*reg);install(*reg)
    rooms,mobs,spawns,npcs,quests,items,topics,aliases=reg
    new={key:val for key,val in quests.items() if key.startswith(PREFIX+'_')}
    assert len(new)==20 and not (new.keys() & QUESTS.keys())
    QUESTS.update(new)
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.executescript('''
    CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT,
      progress INTEGER DEFAULT 0, completed_at INTEGER DEFAULT 0,
      completion_count INTEGER DEFAULT 0, PRIMARY KEY(account_id,quest_id));
    CREATE TABLE quest_resource_progress_v0929(account_id INTEGER, quest_id TEXT,
      target_id TEXT, progress INTEGER,PRIMARY KEY(account_id,quest_id,target_id));
    ''')
    db=DatabaseQuestMixin();db.conn=conn
    count=0
    def check(ok,msg):
        nonlocal count
        assert ok,msg
        count+=1
    try:
        hunt=f'{PREFIX}_hunt_01';goal=quests[hunt]['target']
        db.start_quest(2,hunt)
        db.start_quest(3,hunt)
        check(db.quest(2,hunt)['status']=='active','real quest start')
        for index in range(4):
            check(db.increment_quest(2,goal)==[(hunt,index+1)],'increment on real mob')
            check(db.quest(3,hunt)['progress']==0,'independent account')
        check(db.increment_quest(2,goal)==[],'no overcredit')
        db.complete_quest(2,hunt)
        check(db.quest(2,hunt)['status']=='completed','quest completed')
        check(db.quest(2,hunt)['completion_count']==1,'history count retained')
        check(db.repeat_quest_seconds_remaining(2,hunt,3600)>0,'repeat cooldown')
        db.restart_quest(2,hunt)
        check(db.quest(2,hunt)['progress']==0 and db.quest(2,hunt)['completion_count']==1,
              'restart preserves history')
        collect=f'{PREFIX}_collect_01'
        db.start_quest(2,collect)
        check(db.quest(2,collect)['status']=='active','material quest active')
        material=quests[collect]['target']
        check(any(m.get('drops',{}).get(material,0)>0 for m in mobs.values()),'actual drop material')
        db.set_quest_progress(2,collect,3)
        check(db.quest(2,collect)['progress']==3,'collect persisted')
        elite=f'{PREFIX}_hunt_14'
        db.start_quest(2,elite)
        check(quests[elite]['repeatable']==False and quests[elite]['needed']==1,
              'elite non-repeatable')
        check(db.increment_quest(2,quests[elite]['target'])==[(elite,1)],
              'elite kill increments once')
        check(db.quest(3,hunt)['progress']==0,'no cross-account leak')
        print('V107 OWADY PLUS SQLITE:', count,'PASS')
        return count
    finally:
        conn.close()
        for key in new:QUESTS.pop(key,None)

if __name__=='__main__':run()
