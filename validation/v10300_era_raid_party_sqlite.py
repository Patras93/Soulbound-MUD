# -*- coding: utf-8 -*-
"""Two-account raid kill-credit and isolation through real SQLite quest methods.

Does not simulate party damage/AI: combat's recipient loop is tested by its
actual downstream DB API, independently for both recipients. This protects
against shared-credit regressions and account leakage at all 33 raid bosses.
"""
from __future__ import annotations
import sqlite3
from world.v10300_era_bez_granic import install as install_eras, ERAS
from world.v10300_era_raids import install as install_raids
from storage.db_quests import DatabaseQuestMixin
import storage.db_quests as dbmod


def run():
    rooms={'v3000_eternal_6':{'exits':{}}}; mobs={};spawns=[];npcs={};quests={};items={};recipes={};areas=[]
    install_eras(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    install_raids(rooms,mobs,spawns,npcs,quests,items,recipes)
    class DB(DatabaseQuestMixin):
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('''CREATE TABLE quests(
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0, completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,quest_id));
                CREATE TABLE quest_resource_progress_v0929(
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                resource_id TEXT NOT NULL DEFAULT '',progress INTEGER NOT NULL DEFAULT 0);
            ''')
    db=DB(); old=dbmod.QUESTS; dbmod.QUESTS=quests
    checks=0
    def ck(condition,label):
        nonlocal checks
        if not condition:raise AssertionError(label)
        checks+=1
    try:
        for slug,*_ in ERAS:
            prefix=f'v10300_{slug}'
            for stage in (1,2,3):
                questid=f'{prefix}_raid_quest_{stage}'
                bossid=f'{prefix}_raid_boss_{stage}'
                ck(quests[questid]['target']==bossid, f'wrong quest target: {questid}')
                ck((f'{prefix}_raid_{stage}',bossid) in spawns,f'nonspawned raid boss: {bossid}')
                if stage > 1:
                    ck(quests[questid].get('requires_quest')==f'{prefix}_raid_quest_{stage-1}',f'broken raid chain: {questid}')
                for account in (101,202):
                    ck(db.start_quest(account,questid) is not False, f'could not start {account}: {questid}')
                    ck(db.quest(account,questid)['progress']==0,f'prekill progress: {account} {questid}')
                # A combat kill awarded to one eligible party member does not
                # implicitly credit their party: every recipient gets its own call.
                one=db.increment_quest(101,bossid)
                ck((questid,1) in one,f'first party recipient not credited {questid}: {one}')
                ck(db.quest(101,questid)['progress']==1,f'first recipient progress {questid}')
                ck(db.quest(202,questid)['progress']==0,f'party credit leaked without event {questid}')
                two=db.increment_quest(202,bossid)
                ck((questid,1) in two,f'second party recipient not credited {questid}: {two}')
                ck(db.quest(202,questid)['progress']==1,f'second recipient progress {questid}')
                for account in (101,202):
                    ck(db.increment_quest(account,bossid)==[],f'duplicate credit {account} {questid}')
                db.complete_quest(101,questid)
                ck(db.quest(101,questid)['status']=='completed',f'solo completion missing {questid}')
                ck(db.quest(202,questid)['status']=='active',f'party completion leaked {questid}')
                db.complete_quest(202,questid)
                ck(db.quest(202,questid)['status']=='completed',f'party second completion {questid}')
                ck(db.quest(101,questid)['completion_count']==1,f'duplicate reward one {questid}')
                ck(db.quest(202,questid)['completion_count']==1,f'duplicate reward two {questid}')
        ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        ck(len(ERAS)==11,'missing a regional raid')
    finally:
        dbmod.QUESTS=old
        db.conn.close()
    return checks

if __name__=='__main__':
    print(f'ERA 103 PARTY RAID TWO-ACCOUNT SQLITE: {run()} checks PASS', flush=True)
