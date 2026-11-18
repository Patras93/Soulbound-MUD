# -*- coding: utf-8 -*-
import contextlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from systems.v115 import fame_repeat_rewards as repeat
from systems.v115 import fame_combat_runtime as runtime
from systems.v115 import fame_combat_capture as capture
from systems.v115 import fame_online_scheduler as scheduler
from systems.v115 import fame_snapshot_delivery as delivery
from systems.v115.fame_reward_snapshot import RewardSnapshot


class ProxyConnection:
    def __init__(self,path=':memory:'):
        self.sql = sqlite3.connect(path)
    def execute(self,*a,**k):return self.sql.execute(*a,**k)
    @contextlib.contextmanager
    def deferred_commits(self):
        try:
            yield
            self.sql.commit()
        except BaseException:
            self.sql.rollback()
            raise
    def close(self):self.sql.close()


class TestDelayedRepeatFame(unittest.TestCase):
    def setUp(self):
        self.conn=ProxyConnection()
        self.char=SimpleNamespace(account_id=88,name='Bohater',silver=0)
        self.session=SimpleNamespace(account_id=88,character=self.char)
        self.mob=SimpleNamespace(template_id='boss',room_id='graveyard',home_room_id='graveyard')
        self.template={'name':'Boss','rank':'boss'}
        self.kw=dict(character_xp=100,soul_xp=200,class_xp=300,stat_xp=400,
                     class_levels=(('Mag',100),),class_max_level=999999,overcap=False,now=1000)
        self.patch_a=patch.object(runtime,'resolve_fame_objective',return_value=('Cmentarz','boss'))
        self.patch_b=patch.object(capture,'resolve_fame_objective',return_value=('Cmentarz','boss'))
        self.patch_a.start();self.patch_b.start()
    def tearDown(self):
        self.patch_a.stop();self.patch_b.stop();self.conn.close()
    def stage(self):
        return runtime.stage_delayed_first_clear(self.conn,self.session,self.mob,self.template,**self.kw)
    def test_repeat_first_queues_fame_then_subsequent_kills_exp_only(self):
        self.assertTrue(self.stage())
        self.assertTrue(self.stage())
        self.assertTrue(self.stage())
        self.assertEqual(1,self.conn.execute('SELECT count(*) FROM v115_fame_delivery').fetchone()[0])
        self.assertEqual(2,self.conn.execute('SELECT count(*) FROM v115_fame_repeat_exp').fetchone()[0])
        self.assertEqual(2,len(scheduler.pending_online_accounts(self.conn))) if False else self.assertEqual({88},scheduler.pending_online_accounts(self.conn))
        self.assertEqual([],repeat.due_repeats(self.conn,88,'Bohater',now=1000))
        self.assertEqual(2,len(repeat.due_repeats(self.conn,88,'Bohater',now=1400)))
        self.assertEqual(2,len(repeat.due_repeats(self.conn,88,'Bohater',now=1400)))
    def test_legacy_fame_gets_repeat_exp_only(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702 (account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES (88,'Cmentarz','boss')")
        self.assertTrue(self.stage())
        self.assertFalse(self.conn.execute("SELECT name FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())
        self.assertEqual(1,self.conn.execute('SELECT count(*) FROM v115_fame_repeat_exp').fetchone()[0])
    def test_repeat_rollback_with_combat(self):
        self.conn.execute('SAVEPOINT combat')
        self.assertTrue(self.stage())
        self.assertTrue(self.stage())
        self.conn.execute('ROLLBACK TO SAVEPOINT combat')
        self.conn.execute('RELEASE SAVEPOINT combat')
        self.assertFalse(self.conn.execute("SELECT name FROM sqlite_master WHERE name='v115_fame_repeat_exp'").fetchone())
    def test_savepoint_duplicate_token_is_idempotent_but_conflict_fails(self):
        plan=RewardSnapshot(100,200,300,400,(('Mag',100),),999999,False,'Bohater',True)
        tok='a'*32
        self.assertEqual((tok,True),repeat.stage_repeat_exp(self.conn,88,'Cmentarz','boss','Boss',plan,now=1000,kill_token=tok))
        self.assertEqual((tok,False),repeat.stage_repeat_exp(self.conn,88,'Cmentarz','boss','Boss',plan,now=1000,kill_token=tok))
        altered=RewardSnapshot(110,200,300,400,(('Mag',100),),999999,False,'Bohater',True)
        with self.assertRaises(ValueError):
            repeat.stage_repeat_exp(self.conn,88,'Cmentarz','boss','Boss',altered,now=1000,kill_token=tok)
    def test_no_early_payment_wrong_character_or_audio(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES (88,'Cmentarz','boss')")
        self.stage()
        tok=self.conn.execute('SELECT kill_token FROM v115_fame_repeat_exp').fetchone()[0]
        db=SimpleNamespace(conn=self.conn)
        self.assertIsNone(repeat.settle_repeat_exp(db,self.char,88,tok,now=1000))
        wrong=SimpleNamespace(account_id=88,name='Inna postać')
        with self.assertRaises(ValueError):
            repeat.settle_repeat_exp(db,wrong,88,tok,now=1400)
        self.assertNotIn('sound_events',Path(repeat.__file__).read_text())
    def test_real_award_atomic_and_only_once(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES (88,'Cmentarz','boss')")
        self.stage()
        tok=self.conn.execute('SELECT kill_token FROM v115_fame_repeat_exp').fetchone()[0]
        db=SimpleNamespace(conn=self.conn)
        def award(_db,ch,aid,**kw):
            _db.conn.execute('CREATE TABLE IF NOT EXISTS exp_records (account_id INT, exp INT)')
            _db.conn.execute('INSERT INTO exp_records VALUES (?,?)',(aid,kw['character_xp']))
            ch.silver+=1
            return {'character':(kw['character_xp'],[])}
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',side_effect=award):
            paid=repeat.settle_repeat_exp(db,self.char,88,tok,now=1400)
            self.assertEqual(100,paid['character'][0])
            self.assertIsNone(repeat.settle_repeat_exp(db,self.char,88,tok,now=1500))
        self.assertEqual([(88,100)],self.conn.execute('SELECT * FROM exp_records').fetchall())
        self.assertEqual('DONE',self.conn.execute('SELECT status FROM v115_fame_repeat_exp').fetchone()[0])
    def test_failure_rollback_sql_and_character_then_retry(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES (88,'Cmentarz','boss')")
        self.stage()
        tok=self.conn.execute('SELECT kill_token FROM v115_fame_repeat_exp').fetchone()[0]
        db=SimpleNamespace(conn=self.conn)
        self.conn.execute('CREATE TABLE exp_records(x INTEGER)')
        self.conn.sql.commit()
        def broken(_db,ch,aid,**kw):
            ch.silver+=55
            _db.conn.execute('INSERT INTO exp_records VALUES (11)')
            raise RuntimeError('disk failure simulated')
        with patch('systems.combat_kill_settlement_v10400.settle_combat_full_progression_v10400',side_effect=broken):
            with self.assertRaises(RuntimeError):repeat.settle_repeat_exp(db,self.char,88,tok,now=1400)
        self.assertEqual(0,self.char.silver)
        self.assertEqual([],self.conn.execute('SELECT * FROM exp_records').fetchall())
        self.assertEqual('PENDING',self.conn.execute('SELECT status FROM v115_fame_repeat_exp').fetchone()[0])
    def test_restart_persists_delayed_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=str(Path(tmp)/'db.sqlite')
            a=ProxyConnection(file)
            plan=RewardSnapshot(100,200,300,400,(('Mag',100),),999999,False,'Bohater',True)
            repeat.stage_repeat_exp(a,88,'Cmentarz','boss','Boss',plan,now=1000)
            a.sql.commit();a.close()
            b=ProxyConnection(file)
            self.assertEqual(1,len(repeat.due_repeats(b,88,'Bohater',now=1400)))
            b.close()
    def test_scheduler_sees_repeat_without_first_queue(self):
        plan=RewardSnapshot(100,200,300,400,(('Mag',100),),999999,False,'Bohater',True)
        repeat.stage_repeat_exp(self.conn,88,'Cmentarz','boss','Boss',plan,now=1000)
        self.assertEqual({88},scheduler.pending_online_accounts(self.conn))

if __name__=='__main__':unittest.main()
