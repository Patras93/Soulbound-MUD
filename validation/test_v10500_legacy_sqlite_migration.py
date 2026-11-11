# -*- coding: utf-8 -*-
"""Migracja semantyki Prób: REALNA SQLite, brak kasowania starych zapisów."""
import asyncio
import os
import sqlite3
import tempfile
import types
import unittest
from types import SimpleNamespace
from core.progression_600 import SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS, SOUL_TRIAL_QUEST_IDS
from world.dynamic_content import QUESTS
from player.session_methods_v4200.skilllearning_part01 import unlock as source_unlock

class V105HistoricalTrials(unittest.TestCase):
    def test_historical_quest_rows_survive_unlock_max(self):
        self.assertEqual(SOUL_MAX_TIER,3000)
        with tempfile.TemporaryDirectory(prefix='sb105_legacy_sqlite_') as temp:
            path=os.path.join(temp,'old_character.db')
            db=sqlite3.connect(path)
            db.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY, soul_tier INTEGER, soul_level INTEGER)')
            db.execute('CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT, '
                       'progress INTEGER, completion_count INTEGER, PRIMARY KEY(account_id,quest_id))')
            db.execute('INSERT INTO characters VALUES(1,1,195)')
            # This player already completed legacy trials 2 and 3; no data loss allowed.
            db.executemany('INSERT INTO quests VALUES(?,?,?,?,?)', [
                (1,SOUL_TRIAL_QUEST_IDS[2],'completed',6,1),
                (1,SOUL_TRIAL_QUEST_IDS[3],'completed',5,1),
                (1,SOUL_TRIAL_QUEST_IDS[7],'active',3,0),
            ])
            db.commit()
            saved=[];messages=[];room=[]
            def save_character(c):
                db.execute('UPDATE characters SET soul_tier=?,soul_level=? WHERE account_id=1',
                           (c.soul_tier,c.soul_level));db.commit();saved.append(c.soul_tier)
            async def broadcast_room(*args,**kwargs):room.append((args,kwargs))
            class Fake:
                def __init__(self):
                    self.character=SimpleNamespace(soul_tier=1,soul_level=195,room_id='temple',
                              name='Stary Gracz',class_name='Wojownik',soul_power=lambda:300)
                    self.server=SimpleNamespace(db=SimpleNamespace(save_character=save_character),
                                                broadcast_room=broadcast_room)
                async def send(self,msg):messages.append(msg)
                def soul_tier_quest_completed(self,t):
                    row=db.execute('SELECT status FROM quests WHERE account_id=1 AND quest_id=?',
                                   (SOUL_TRIAL_QUEST_IDS[t],)).fetchone()
                    return bool(row and row[0]=='completed')
            globals_=dict(source_unlock.__globals__)
            globals_.update(SOUL_MAX_TIER=SOUL_MAX_TIER,SOUL_TIER_THRESHOLDS=SOUL_TIER_THRESHOLDS,
                            SOUL_TRIAL_QUEST_IDS=SOUL_TRIAL_QUEST_IDS,QUESTS=QUESTS)
            method=types.FunctionType(source_unlock.__code__,globals_,'unlock',argdefs=(False,))
            fake=Fake()
            # T2-T9 are free, despite old completed/active quest history.
            asyncio.run(method(fake,True))
            self.assertEqual(saved,[9]);self.assertIn('Próba Tieru 10',messages[-1])
            before=db.execute('SELECT quest_id,status,progress,completion_count FROM quests ORDER BY quest_id').fetchall()
            db.execute('INSERT INTO quests VALUES(?,?,?,?,?)',
                       (1,SOUL_TRIAL_QUEST_IDS[10],'completed',1,1));db.commit()
            asyncio.run(method(fake,True))
            self.assertEqual(saved,[9,19]);self.assertEqual(fake.character.soul_tier,19)
            after=db.execute('SELECT quest_id,status,progress,completion_count FROM quests '
                             'WHERE quest_id!=? ORDER BY quest_id',
                             (SOUL_TRIAL_QUEST_IDS[10],)).fetchall()
            self.assertEqual(before,after,'historical quest progress changed')
            # Next milestone blocked until level AND trial, even on repeated call.
            asyncio.run(method(fake,True))
            self.assertEqual(saved,[9,19]);self.assertEqual(len(room),2)
            self.assertEqual(db.execute('SELECT soul_tier FROM characters').fetchone()[0],19)
            db.close()
            reopened=sqlite3.connect(path)
            self.assertEqual(reopened.execute('SELECT soul_tier FROM characters').fetchone()[0],19)
            self.assertEqual(reopened.execute('SELECT COUNT(*) FROM quests').fetchone()[0],4)
            reopened.close()

if __name__=='__main__':unittest.main()
