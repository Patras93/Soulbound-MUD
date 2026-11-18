# -*- coding: utf-8 -*-
"""v115 regional quest completion: native SQLite + real event bus."""
import asyncio
import inspect
import sqlite3
import unittest
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import patch

from events.bootstrap import build_default_event_bus
from events.contracts import QuestCompletedEvent
from storage.db_quests import DatabaseQuestMixin
from systems.content_registry import QUESTS
from systems.v115.high_level_world import REGIONS
from systems.v115.playable_regions import room_id
from systems.v115.objective_progress import total
from systems.v115.quest_completion_bridge import record_v115_completed_quest
from validation.test_v10400_atomic_live_character_xp import fixture

REGION=REGIONS[0].key
QID=next(iter(QUESTS))

class QuestCompletionRegionalTests(unittest.TestCase):
    def setUp(self):
        self.db, self.c=fixture()
        self.db.quest=MethodType(DatabaseQuestMixin.quest,self.db)
        self.db.complete_quest=MethodType(DatabaseQuestMixin.complete_quest,self.db)
        self.db.conn.execute('''CREATE TABLE quests (
            account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
            status TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
            completed_at INTEGER NOT NULL DEFAULT 0,
            completion_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(account_id,quest_id))''')
        self.db.conn.execute('''INSERT INTO quests(account_id,quest_id,status)
                           VALUES(1,?,'active')''',(QID,))
        self.db.conn.commit()
        self.c.room_id=room_id(REGION,0,0)
        self.messages=[]
        self.errors=[]
        async def send(text): self.messages.append(text)
        self.server=SimpleNamespace(db=self.db,report_runtime_error=lambda e,**kw:self.errors.append(e))
        self.session=SimpleNamespace(account_id=1,character=self.c,server=self.server,send=send)
        self.event=QuestCompletedEvent(session=self.session, quest_id=QID,quest=QUESTS[QID])

    def tearDown(self): self.db.conn.close()
    def wallet(self):
        return int(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0])
    def claim_rows(self):
        return self.db.conn.execute('SELECT COUNT(*) FROM v115_objective_claims').fetchone()[0]
    def complete(self): self.db.complete_quest(1,QID)

    def test_no_credit_before_true_native_completion(self):
        self.assertEqual(record_v115_completed_quest(self.session,QID),(0,0,0,0))
        self.assertEqual(self.wallet(),100)

    def test_real_complete_once_and_replay_without_double_payout(self):
        self.complete()
        earned=record_v115_completed_quest(self.session,QID)
        self.assertEqual(earned[0],1)
        self.assertEqual(total(self.db.conn,1,REGION,'complete_quest'),1)
        self.assertGreater(self.wallet(),100)
        self.assertEqual(self.wallet(),self.c.silver)
        wallet=self.wallet()
        self.assertEqual(record_v115_completed_quest(self.session,QID),(0,0,0,0))
        self.assertEqual(self.wallet(),wallet)

    def test_repeated_native_completion_has_new_event_id(self):
        self.complete()
        record_v115_completed_quest(self.session,QID)
        self.db.conn.execute('UPDATE quests SET status="active" WHERE quest_id=?',(QID,))
        self.db.conn.commit()
        self.complete()
        result=record_v115_completed_quest(self.session,QID)
        self.assertEqual(result[0],1)
        self.assertEqual(total(self.db.conn,1,REGION,'complete_quest'),2)
        self.assertEqual(record_v115_completed_quest(self.session,QID),(0,0,0,0))

    def test_old_room_never_creates_objective_tables(self):
        self.c.room_id='graveyard'
        self.complete()
        self.assertEqual(record_v115_completed_quest(self.session,QID),(0,0,0,0))
        self.assertFalse(self.db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_objective_events'").fetchone())

    def test_invalid_sender_and_room_rejected(self):
        self.complete()
        self.c.account_id=2
        with self.assertRaises(ValueError):record_v115_completed_quest(self.session,QID)
        self.c.account_id=1
        self.c.room_id='v115_region_01_p_99_99'
        from unittest.mock import patch
        with patch('systems.v115.quest_completion_bridge.ROOMS',{self.c.room_id:{'v115_region_key':REGION}}):
            with self.assertRaises(ValueError):record_v115_completed_quest(self.session,QID)
        self.c.room_id=room_id(REGION,0,0)
        with self.assertRaises(ValueError):record_v115_completed_quest(self.session,'not_a_quest')

    def test_sqlite_failure_restores_wallet_and_progress(self):
        self.complete()
        self.db.conn.execute("CREATE TRIGGER fail_v115_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'fail'); END")
        with self.assertRaises(sqlite3.IntegrityError):record_v115_completed_quest(self.session,QID)
        self.assertEqual(self.c.silver,100)
        self.assertEqual(self.wallet(),100)
        self.assertEqual(total(self.db.conn,1,REGION,'complete_quest'),0)
        self.db.conn.execute('DROP TRIGGER fail_v115_wallet')
        self.assertEqual(record_v115_completed_quest(self.session,QID)[0],1)

    def test_real_event_bus_noncritical_listener_and_short_notice(self):
        self.complete()
        bus=build_default_event_bus(self.server)
        listeners=bus.listeners_for(QuestCompletedEvent)
        self.assertEqual(len(listeners),1)
        self.assertFalse(listeners[0].critical)
        asyncio.run(bus.publish(self.event))
        self.assertEqual(total(self.db.conn,1,REGION,'complete_quest'),1)
        self.assertEqual(len(self.messages),1)
        self.assertIn('Horyzonty:',self.messages[0])
        asyncio.run(bus.publish(self.event))
        self.assertEqual(len(self.messages),1)
        self.assertFalse(self.errors)

    def test_optional_reward_failure_cannot_undo_native_quest(self):
        self.complete()
        self.db.conn.execute("CREATE TRIGGER fail_v115_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'fail'); END")
        bus=build_default_event_bus(self.server)
        response=asyncio.run(bus.publish(self.event))
        self.assertEqual(len(response['errors']),1)
        self.assertEqual(len(self.errors),1)
        self.assertEqual(self.db.quest(1,QID)['status'],'completed')
        self.assertEqual(self.db.quest(1,QID)['completion_count'],1)
        self.assertEqual(self.wallet(),100)

    def test_no_audio_and_actual_native_publish_path(self):
        base=Path(__file__).resolve().parents[1]
        script=(base/'player/session_mixins/quest_commands.py').read_text('utf-8')
        self.assertIn('QuestCompletedEvent(session=self, quest_id=quest_id, quest=q)',script)
        bridge=(base/'systems/v115/quest_completion_bridge.py').read_text('utf-8')
        self.assertNotIn('sound_events',bridge)
        self.assertNotIn('SOUND_EVENT',bridge)

if __name__=='__main__':unittest.main()
