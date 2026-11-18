# -*- coding: utf-8 -*-
"""Real character+wallet test of v115 quest/achievement silver payout.

No live player data, sockets, audio or historical migrations are modified.
"""
import sqlite3
import unittest
from types import SimpleNamespace
from validation.test_v10400_atomic_live_character_xp import fixture
from systems.v115.objective_rewards import settle_kill_objectives
from systems.v115.combat_objective_bridge import record_v115_victory
from systems.v115.objective_progress import record_event,total
from systems.v115.high_level_world import REGIONS

REGION=REGIONS[0].key

class ObjectivePayoutRealSQLite(unittest.TestCase):
    def setUp(self):
        self.db, self.c = fixture()
        self.c.room_id='arena'
        self.player=SimpleNamespace(account_id=1,character=self.c)
        self.server=SimpleNamespace(db=self.db,party_sessions=lambda *a,**k:[self.player])
        self.player.server=self.server
        self.mob=SimpleNamespace(alive=False)
    def tearDown(self):
        self.db.conn.close()
    def wallet(self):
        return int(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0])
    def claims(self):
        if not self.db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_objective_claims'").fetchone():
            return 0
        return self.db.conn.execute('SELECT COUNT(*) FROM v115_objective_claims').fetchone()[0]
    def win(self,eid,boss=True):
        return record_v115_victory(self.player,self.mob,{'v115_region_key':REGION,'boss':boss},event_id=eid)
    def test_boss_rewards_real_wallet(self):
        with self.db.conn.deferred_commits():
            self.assertEqual(self.win('boss-one'),2)
        # First regional boss completes two first-tier goals (quest+achievement).
        self.assertEqual(self.claims(),2)
        self.assertEqual(self.wallet(),460)
        self.assertEqual(self.c.silver,460)
        self.assertEqual(len(self.mob._v115_objective_notices),1)
    def test_retry_idempotent(self):
        with self.db.conn.deferred_commits():
            self.win('boss-one')
            self.assertEqual(self.win('boss-one'),0)
        self.assertEqual(self.wallet(),460)
        self.assertEqual(self.claims(),2)
    def test_old_content_never_creates_payout_schema(self):
        self.assertEqual(record_v115_victory(self.player,self.mob,{},event_id='old'),0)
        self.assertEqual(self.wallet(),100)
        self.assertEqual(self.db.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='v115_objective_claims'").fetchone()[0],0)
    def test_failed_wallet_write_rolls_back_claims_and_memory(self):
        self.db.conn.execute("CREATE TRIGGER fail_v115_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'payout failed'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.conn.deferred_commits():
                self.win('boss-fail')
        self.assertEqual(self.wallet(),100)
        self.assertEqual(self.c.silver,100)
        self.assertEqual(self.claims(),0)
        self.db.conn.execute('DROP TRIGGER fail_v115_wallet')
        with self.db.conn.deferred_commits():
            self.win('boss-fail')
        self.assertEqual(self.claims(),2)
        self.assertEqual(self.wallet(),460)
    def test_coordinator_failure_rollback_sql(self):
        with self.assertRaises(RuntimeError):
            with self.db.conn.deferred_commits():
                self.win('later')
                raise RuntimeError('later failure in kill')
        self.assertEqual(self.wallet(),100)
        self.assertEqual(self.claims(),0)
        # The full combat decorator (tested separately) restores in-memory
        # balances when its enclosing kill transaction fails.
    def test_payout_requires_account_matching_character(self):
        self.c.account_id=2
        with self.assertRaises(ValueError):
            settle_kill_objectives(self.db,self.c,1,REGION,('defeat_boss',))
        self.assertEqual(self.wallet(),100)
    def test_repeated_kills_no_duplicate_quest_claim(self):
        with self.db.conn.deferred_commits():
            self.win('one')
            self.win('two')
        # Second kill can unlock second repeatable achievement cycle,
        # but fixed quests cannot be claimed twice.
        rows=self.db.conn.execute("SELECT claim_key,cycle FROM v115_objective_claims WHERE claim_key LIKE 'v115_quest_%'").fetchall()
        self.assertEqual(len(rows),2)
        self.assertEqual(len({row[0] for row in rows}),2)
        self.assertTrue(all(row[1] == 0 for row in rows))
        self.assertGreater(self.wallet(),460)
    def test_full_kill_coordinator_restores_wallet_on_rollback(self):
        import asyncio
        from unittest.mock import patch
        # Extract the exact real decorator from source. Importing the entire
        # combat module without full world bootstrap triggers the legacy
        # static catalog's fail-closed initialization (977 missing IDs).
        import ast
        from pathlib import Path
        file=Path(__file__).resolve().parents[1] / 'player/session_mixins/combat_rewards.py'
        tree=ast.parse(file.read_text(encoding='utf8'))
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)
                      and x.name=='deferred_kill_commits_v11125')
        namespace={}
        exec(compile(ast.Module(body=[function], type_ignores=[]),str(file),'exec'),namespace)
        deferred_kill_commits_v11125=namespace['deferred_kill_commits_v11125']
        self.mob.alive=True
        self.db.conn.commit()
        async def fake_settle(_session, _callback, mob):
            mob._v115_objective_wallet_checkpoints = [(self.player,(100,0,0))]
            self.c.silver=460
            raise RuntimeError('transaction failed')
        async def run():
            @deferred_kill_commits_v11125
            async def kill(session,mob): return 'ok'
            with patch.dict(namespace, {'_run_with_deferred_kill_commits_v11125':fake_settle}):
                with self.assertRaisesRegex(RuntimeError,'transaction failed'):
                    await kill(self.player,self.mob)
        asyncio.run(run())
        self.assertEqual(self.c.silver,100)
        self.assertFalse(self.mob.v1400_kill_in_progress)
        self.assertFalse(hasattr(self.mob,'_v115_objective_wallet_checkpoints'))
    def test_postcommit_send_error_does_not_undo_saved_rewards(self):
        import asyncio
        from unittest.mock import patch
        # Extract the exact real decorator from source. Importing the entire
        # combat module without full world bootstrap triggers the legacy
        # static catalog's fail-closed initialization (977 missing IDs).
        import ast
        from pathlib import Path
        file=Path(__file__).resolve().parents[1] / 'player/session_mixins/combat_rewards.py'
        tree=ast.parse(file.read_text(encoding='utf8'))
        function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)
                      and x.name=='deferred_kill_commits_v11125')
        namespace={}
        exec(compile(ast.Module(body=[function], type_ignores=[]),str(file),'exec'),namespace)
        deferred_kill_commits_v11125=namespace['deferred_kill_commits_v11125']
        self.mob.alive=True
        self.db.conn.commit()
        async def fake_settle(_session,_callback,mob):
            self.c.silver=460
            mob._v115_objective_wallet_checkpoints=[(self.player,(100,0,0))]
            mob._v115_objective_notices=[(self.player,'Nagroda v115')]
            return 'saved'
        async def broken_send(message):
            raise ConnectionError('network send failed after commit')
        self.player.send=broken_send
        async def run():
            @deferred_kill_commits_v11125
            async def kill(session,mob):return 'ok'
            with patch.dict(namespace, {'_run_with_deferred_kill_commits_v11125':fake_settle}):
                with self.assertRaises(ConnectionError):
                    await kill(self.player,self.mob)
        asyncio.run(run())
        self.assertEqual(self.c.silver,460)
        self.assertFalse(hasattr(self.mob,'_v115_objective_notices'))
        self.assertFalse(self.mob.v1400_kill_in_progress)
    def test_no_audio_dependency(self):
        import inspect
        from systems.v115 import objective_rewards
        self.assertNotIn('sound_events',inspect.getsource(objective_rewards))
if __name__=='__main__':unittest.main()
