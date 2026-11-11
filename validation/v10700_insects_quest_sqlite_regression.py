# -*- coding: utf-8 -*-
"""v107 insect mission counters in native SQLite quest mixin (private in-memory DB)."""
from __future__ import annotations

import sqlite3
from world.v10700_insects_expansion import PREFIX, install
from validation.v10700_insects_expansion_regression import fixture
from storage.db_quests import DatabaseQuestMixin, QUESTS


def run():
    rooms, mobs, spawns, npcs, quests, items, topics, aliases = fixture()
    install(rooms, mobs, spawns, npcs, quests, items, topics, aliases)
    # Native DatabaseQuestMixin reads shared live quest catalogue. In this isolated
    # process replace only our new IDs; restore all in-memory data before exit.
    added = {k:v for k,v in quests.items() if k.startswith(PREFIX+'_')}
    assert set(added).isdisjoint(QUESTS), 'test refuses to overwrite real quest IDs'
    QUESTS.update(added)
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT,
            progress INTEGER DEFAULT 0, completed_at INTEGER DEFAULT 0,
            completion_count INTEGER DEFAULT 0, PRIMARY KEY(account_id,quest_id));
        CREATE TABLE quest_resource_progress_v0929(account_id INTEGER, quest_id TEXT,
            target_id TEXT, progress INTEGER,
            PRIMARY KEY(account_id,quest_id,target_id));
    ''')
    db = DatabaseQuestMixin()
    db.conn = conn
    checks = 0
    def check(ok, msg):
        nonlocal checks
        assert ok,msg
        checks += 1
    try:
        qid=f'{PREFIX}_hunt_01'; target=quests[qid]['target']
        collect=f'{PREFIX}_collect_01'
        for account in (7, 12):
            db.start_quest(account,qid)
            check(db.quest(account,qid)['progress']==0, 'independent quest start')
        for step in range(4):
            result=db.increment_quest(7,target)
            check(result==[(qid,step+1)], 'real kill increments exactly once')
            check(db.quest(12,qid)['progress']==0, 'second player not credited')
        check(db.increment_quest(7,target)==[],'overkill cannot duplicate progress')
        check(db.quest(7,qid)['progress']==4,'quest completed objective')
        db.complete_quest(7,qid)
        check(db.quest(7,qid)['status']=='completed', 'quest turn-in completed')
        check(db.quest(7,qid)['completion_count']==1,'completion count durable')
        check(db.repeat_quest_seconds_remaining(7,qid,3600)>0,
              'repeatable quest keeps cooldown')
        db.restart_quest(7,qid)
        check(db.quest(7,qid)['progress']==0 and db.quest(7,qid)['completion_count']==1,
              'repeat restarts progress but keeps history')
        db.start_quest(7,collect)
        check(db.quest(7,collect)['status']=='active' and
              db.quest(7,collect)['progress']==0,'collect objective persisted')
        check(quests[collect]['target'] in items and any(m.get('drops',{}).get(quests[collect]['target'],0)>0 for m in mobs.values()),
              'material drops from an actual mob')
        db.set_quest_progress(7,collect,3)
        check(db.quest(7,collect)['progress']==3,'collect progress stored')
        check(db.quest(12,qid)['progress']==0,'no account mixing after repeat')
        print('V107 OWADY: QUESTY SQLITE',checks,'kontroli PASS')
        return checks
    finally:
        conn.close()
        for key in added:
            QUESTS.pop(key, None)

if __name__=='__main__':run()
