# -*- coding: utf-8 -*-
"""Offline: atomic multi-axis quest reward dry run, no network / production DB."""
import sqlite3
import tempfile
from pathlib import Path
import unittest

from storage.big_number_reward_bundle_v10400 import (
    apply_reward_bundle_copy, preview_quest_xp_bundle_copy,
    RewardBundleConflictV104, RewardBundleCorruptV104,
)
from storage.big_number_events_v10400 import verify_events_copy
from storage.big_number_ledger_v10400 import get_exact_copy, StaleLegacyValueV104


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.executescript('''
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,
                character_xp INTEGER,soul_xp INTEGER,silver INTEGER,gold INTEGER,mithril INTEGER);
            CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,xp INTEGER,
                PRIMARY KEY(account_id,class_name));
            INSERT INTO characters VALUES(1,100,50,100,0,0);
            INSERT INTO characters VALUES(2,200,80,100,0,0);
            INSERT INTO class_progress VALUES(1,'Mag',7);
            INSERT INTO class_progress VALUES(2,'Mag',17);
        ''')
        self.payload={('characters.character_xp',''):10**100,
                      ('characters.soul_xp',''):10**90,
                      ('class_progress.xp','Mag'):10**80,
                      ('characters.silver',''):5}
    def tearDown(self):self.conn.close()

    def test_all_four_axes_100_digits(self):
        result=apply_reward_bundle_copy(self.conn,1,'quest:era:55',self.payload)
        self.assertEqual(result[('characters.character_xp','')],10**100+100)
        self.assertEqual(result[('characters.soul_xp','')],10**90+50)
        self.assertEqual(result[('class_progress.xp','Mag')],10**80+7)
        self.assertEqual(result[('characters.silver','')],105)
        self.assertEqual(verify_events_copy(self.conn),4)
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters WHERE account_id=1').fetchone()[0],100)

    def test_idempotent_after_second_quest(self):
        once=apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        apply_reward_bundle_copy(self.conn,1,'quest:2',{('characters.character_xp',''):50})
        repeat=apply_reward_bundle_copy(self.conn,1,'quest:1',dict(reversed(list(self.payload.items()))))
        self.assertEqual(repeat[('characters.character_xp','')],once[('characters.character_xp','')]+50)
        self.assertEqual(verify_events_copy(self.conn),5)

    def test_no_reuse_id_with_different_payload(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        with self.assertRaises(RewardBundleConflictV104):
            apply_reward_bundle_copy(self.conn,1,'quest:1',{('characters.character_xp',''):11})
        self.assertEqual(verify_events_copy(self.conn),4)

    def test_failed_axis_reverts_all(self):
        payload=dict(self.payload)
        payload[('characters.soul_xp','')]=-10000
        with self.assertRaises(ValueError): apply_reward_bundle_copy(self.conn,1,'quest:fail',payload)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 'big_number_%'").fetchone()[0],0)

    def test_trigger_failure_reverts_all(self):
        apply_reward_bundle_copy(self.conn,1,'quest:first',{('characters.character_xp',''):50})
        self.conn.execute("""CREATE TRIGGER break_soul BEFORE INSERT ON big_number_events_v10400
            WHEN NEW.axis='characters.soul_xp' BEGIN SELECT RAISE(ABORT,'error'); END""")
        with self.assertRaises(sqlite3.IntegrityError):apply_reward_bundle_copy(self.conn,1,'quest:fail',self.payload)
        self.assertEqual(get_exact_copy(self.conn,1,'characters.character_xp'),150)
        self.assertEqual(verify_events_copy(self.conn),1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM big_number_reward_bundles_v10400').fetchone()[0],1)

    def test_receipt_deleted_blocks_orphan_replay(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        self.conn.execute('DELETE FROM big_number_reward_bundles_v10400')
        with self.assertRaises(RewardBundleCorruptV104):apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)

    def test_sub_event_deleted_detected(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        self.conn.execute("DELETE FROM big_number_events_v10400 WHERE axis='characters.soul_xp'")
        with self.assertRaises(RewardBundleCorruptV104):apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)

    def test_extra_event_with_same_id_detected(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        from storage.big_number_events_v10400 import apply_event_copy
        apply_event_copy(self.conn,1,'characters.gold',99,'quest:1')
        with self.assertRaises(RewardBundleCorruptV104):
            apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)

    def test_legacy_change_fails_closed(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        self.conn.execute('UPDATE characters SET soul_xp=51 WHERE account_id=1')
        with self.assertRaises(StaleLegacyValueV104):apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)

    def test_two_characters_do_not_mix(self):
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        out=apply_reward_bundle_copy(self.conn,2,'quest:1',self.payload)
        self.assertEqual(out[('characters.character_xp','')],10**100+200)
        self.assertEqual(verify_events_copy(self.conn),8)

    def test_rollback_with_parent(self):
        self.conn.execute('SAVEPOINT parent')
        apply_reward_bundle_copy(self.conn,1,'quest:1',self.payload)
        self.conn.execute('ROLLBACK TO parent')
        self.conn.execute('RELEASE parent')
        self.assertEqual(self.conn.execute('SELECT count(*) FROM sqlite_master WHERE name LIKE "big_number_%"').fetchone()[0],0)

    def test_restart_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/'test.db'
            backup=sqlite3.connect(dest)
            self.conn.backup(backup)
            try:
                apply_reward_bundle_copy(backup,1,'quest:1',self.payload)
                backup.commit();backup.close()
                again=sqlite3.connect(dest)
                self.assertEqual(apply_reward_bundle_copy(again,1,'quest:1',self.payload)[('characters.character_xp','')],10**100+100)
                again.close()
            finally:
                try:backup.close()
                except Exception:pass  # AUDIT_INTENTIONAL_PASS: cleanup may already have closed connection

    def test_reject_float_bool_key_duplicate_and_unknown_axis(self):
        for payload in ({('characters.character_xp',''):True},
                        {('characters.character_xp',''):1.5},
                        {('unknown.axis',''):1},
                        {('class_progress.xp',''):50},
                        {}):
            with self.subTest(payload=payload),self.assertRaises((ValueError,TypeError)):
                apply_reward_bundle_copy(self.conn,1,'quest:bad',payload)

    def test_real_quest_calculator_adapter(self):
        from world import dynamic_content as world
        qid='v10400_raid_12_raid_quest_1'
        deltas=preview_quest_xp_bundle_copy(qid,world.QUESTS[qid],class_name='Mag')
        self.assertGreaterEqual(deltas[('characters.character_xp','')],200000)
        self.assertTrue(set(key[0] for key in deltas).issubset({'characters.character_xp','characters.soul_xp','class_progress.xp'}))
        out=apply_reward_bundle_copy(self.conn,1,'quest:calc',deltas)
        self.assertGreater(out[('characters.character_xp','')],100)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(BundleTest)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():raise AssertionError('Etap 13 FAIL')
    return result.testsRun

if __name__=='__main__':print('V104 ETAP 13:',run(),'PASS',flush=True)
