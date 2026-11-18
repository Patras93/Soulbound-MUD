# -*- coding: utf-8 -*-
"""Real Fame identity and queue compatibility tests; no live server payout."""
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems import fame_v1702 as old
from systems.v115.fame_kill_intake import stage_real_fame_kill
from systems.v115 import fame_queue

class FameIntakeTests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.a=SimpleNamespace(account_id=123)
        self.b=SimpleNamespace(account_id=124)
        self.mob=SimpleNamespace(home_room_id='test_room',room_id='test_room',template_id='test_boss')
        self.template={'name':'Próba Bossa','boss':True}
        self.mock_catalog=patch.object(old,'fame_catalog',return_value={'Kraina':('test_boss',)})
        self.mock_identity=patch.object(old,'_fame_target_identity',return_value=('Kraina','test_boss'))
        self.mock_catalog.start();self.mock_identity.start()
        self.addCleanup(self.mock_catalog.stop);self.addCleanup(self.mock_identity.stop)
    def test_delayed_first_clear_and_distinct_players(self):
        got=stage_real_fame_kill(self.conn,[self.a,self.b],self.mob,self.template,now=1000)
        self.assertEqual(len(got),2)
        records=self.conn.execute('SELECT account_id,due_at,status,reward_xp FROM v115_fame_delivery ORDER BY account_id').fetchall()
        self.assertEqual(len(records),2)
        for account,due,status,xp in records:
            self.assertGreaterEqual(due,1060);self.assertLessEqual(due,1300)
            self.assertEqual((status,xp),('WAITING',0))
        self.assertFalse(self.conn.execute("SELECT name FROM sqlite_master WHERE name='fame_bosses_v1702'").fetchone())
    def test_duplicate_is_rejected(self):
        self.assertEqual(len(stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1000)),1)
        self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1001),[])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM v115_fame_delivery').fetchone()[0],1)
    def test_legacy_first_clear_is_respected(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,boss_id TEXT,region TEXT)')
        self.conn.execute('INSERT INTO fame_bosses_v1702 VALUES(123,?,?)',('test_boss','Kraina'))
        self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1000),[])
    def test_regular_enemy_rejected(self):
        self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,{'name':'Rat'},now=1000),[])
    def test_summoned_enemy_rejected(self):
        self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,{'boss':True,'uoss_superboss_add':True},now=1000),[])
    def test_runtime_summon_rejected(self):
        self.mob.uoss_summon_parent_v1144='owner'
        self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1000),[])
    def test_unresolved_canonical_identity(self):
        with patch.object(old,'_fame_target_identity',return_value=None):
            self.assertEqual(stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1000),[])
    def test_malformed_recipient_is_rejected(self):
        with self.assertRaises(ValueError):
            stage_real_fame_kill(self.conn,[SimpleNamespace(account_id=None)],self.mob,self.template,now=1000)
    def test_queue_no_sound_or_session_import(self):
        from pathlib import Path
        from systems.v115 import fame_kill_intake
        code=Path(fame_kill_intake.__file__).read_text(encoding='utf8')
        self.assertNotIn('sound_events',code)
        self.assertNotIn('await session',code)
    def test_delayed_fame_not_ready_before_exp(self):
        stage_real_fame_kill(self.conn,[self.a],self.mob,self.template,now=1000)
        self.assertEqual(fame_queue.due_events(self.conn,123,now=1059),[])
        self.assertEqual(self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')

if __name__=='__main__':unittest.main()
