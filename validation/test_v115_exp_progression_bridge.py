# -*- coding: utf-8 -*-
"""Tests for actual SQLite savepoints and failure recovery, not live TCP."""
import sqlite3
import unittest
from unittest.mock import patch
from contextlib import contextmanager
from types import SimpleNamespace
from systems.v115 import fame_queue
from systems.v115.fame_exp_progression import settle_fame_exp_progression

class DeferredSQLite:
    def __init__(self): self.raw=sqlite3.connect(':memory:'); self.depth=0
    def execute(self,*args): return self.raw.execute(*args)
    @contextmanager
    def deferred_commits(self):
        self.depth+=1
        try:
            yield self
        finally:
            self.depth-=1

class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.db=SimpleNamespace(conn=DeferredSQLite())
        self.db.conn.execute('CREATE TABLE balances (account_id INTEGER PRIMARY KEY, xp INTEGER NOT NULL)')
        self.db.conn.execute('INSERT INTO balances VALUES(7,0)')
        self.character=SimpleNamespace(account_id=7,character_xp=0)
        self.t=12000
        self.assertTrue(fame_queue.schedule_fame(self.db.conn,7,'K','B','Boss',reward_xp=250,now=self.t))
        self.due=self.t+fame_queue.deterministic_delay(7,'K','B')
    def fake_settle(self, db, character, account_id, **kwargs):
        amount=kwargs['character_xp']
        db.conn.execute('UPDATE balances SET xp=xp+? WHERE account_id=?',(amount,account_id))
        character.character_xp+=amount
        return {'character':(amount,[])}
    def call(self, **kwargs):
        args=dict(character_xp=250,soul_xp=150,class_xp=0,stat_xp=10,now=self.due)
        args.update(kwargs)
        return settle_fame_exp_progression(self.db,self.character,7,'K','B',**args)
    def test_not_before_due(self):
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',self.fake_settle):
            self.assertIsNone(self.call(now=self.due-1))
        self.assertEqual(self.character.character_xp,0)
    def test_success_and_exactly_once(self):
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',self.fake_settle):
            self.assertEqual(self.call()['character'][0],250)
            self.assertIsNone(self.call(now=self.due+1))
        self.assertEqual(self.db.conn.execute('SELECT xp FROM balances').fetchone()[0],250)
        row=self.db.conn.execute('SELECT status,fame_due_at FROM v115_fame_delivery').fetchone()
        self.assertEqual(row,('FAME_READY',self.due+2))
    def test_exception_rollback_sql_and_memory(self):
        def broken(db,char,account,**kw):
            self.fake_settle(db,char,account,**kw)
            raise RuntimeError('broken progression')
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',broken):
            with self.assertRaises(RuntimeError): self.call()
        self.assertEqual(self.character.character_xp,0)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM balances').fetchone()[0],0)
        self.assertEqual(self.db.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')
    def test_reopen_prevents_duplicate(self):
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',self.fake_settle):
            self.call()
        copy=sqlite3.connect(':memory:'); copy.executescript('\n'.join(self.db.conn.raw.iterdump()))
        self.assertEqual(copy.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'FAME_READY')
    def test_reject_plain_sqlite(self):
        db=SimpleNamespace(conn=sqlite3.connect(':memory:'))
        with self.assertRaises(TypeError): settle_fame_exp_progression(db,self.character,7,'K','B',character_xp=1,soul_xp=0,class_xp=0,stat_xp=0)
    def test_reject_invalid(self):
        with self.assertRaises(ValueError): self.call(character_xp=-1)
        with self.assertRaises(ValueError): self.call(character_xp=0.25)
    def test_no_audio(self):
        from pathlib import Path
        import systems.v115.fame_exp_progression as module
        self.assertNotIn('sound_events',Path(module.__file__).read_text(encoding='utf-8'))

if __name__=='__main__': unittest.main()
