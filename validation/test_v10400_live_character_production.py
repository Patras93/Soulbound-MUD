# -*- coding: utf-8 -*-
"""Production 14-axis character BigNumber, full game schema, never real data."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from core.big_numbers_v10400 import SQLITE_INT64_MAX
from core.classes_skills import CLASSES, RACES
from player.character import Character
from storage.database import Database


class CharacterProductionLiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_live_char_')
        self.path = Path(self.tmp.name) / 'sandbox.sqlite'
        self.db = Database(str(self.path))
        self.uid = self.db.create_account('Tester', 'testpassword123')
        cases = {key:'Tester' for key in ('nom','gen','dat','acc','ins','loc','voc')}
        self.db.create_character_for_master(self.uid, 'Tester', RACES[0], CLASSES[0], cases)
    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()
    def character(self):
        return Character.from_row(self.db.character_for_account(self.uid))

    def test_progress_14_axes_exact_after_reopen(self):
        c = self.character()
        c.character_xp = 10**200+21
        c.soul_xp = 10**201+22
        c.soul_tier = 10**160+23
        c.strength_progress = 10**155+24
        c.soul_weapon_mastery_xp = 10**175+25
        self.db.save_character(c)
        self.assertEqual(self.db.conn.execute('SELECT character_xp FROM characters WHERE account_id=?', (self.uid,)).fetchone()[0], SQLITE_INT64_MAX)
        self.db.conn.close(); self.db=Database(str(self.path))
        r=self.character()
        for name in ('character_xp','soul_xp','soul_tier','strength_progress','soul_weapon_mastery_xp'):
            self.assertEqual(getattr(r,name),getattr(c,name))
        self.assertEqual(self.db.characters_for_master(self.uid)[0]['character_xp'],c.character_xp)
        self.assertEqual(self.db.characters_for_master(self.uid)[0][self.db.characters_for_master(self.uid)[0].keys().index('character_xp')],c.character_xp)
        self.assertEqual(self.db.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_existing_char_without_shadows_works(self):
        c=self.character();c.character_xp=50;c.soul_xp=60
        self.db.save_character(c)
        self.assertEqual(self.character().character_xp,50)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_character_v10400').fetchone()[0],0)

    def test_corruption_missing_receipt_or_shadow_fails(self):
        c=self.character();c.character_xp=10**100
        self.db.save_character(c)
        self.db.conn.execute("DELETE FROM big_number_live_character_v10400 WHERE axis='character_xp'")
        with self.assertRaisesRegex(ValueError,'brak potwierdzenia lub dokladnej'):
            self.character()
        with self.assertRaises(ValueError):
            self.db.save_character(c)

    def test_direct_update_refused_on_migrated_field(self):
        c=self.character();c.soul_xp=10**100
        self.db.save_character(c)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.conn.execute('UPDATE characters SET soul_xp=? WHERE account_id=?',(777,self.uid))
        self.assertEqual(self.character().soul_xp,10**100)

    def test_outer_rollback_restores_exact_and_mirror(self):
        c=self.character();c.character_xp=10**100
        self.db.save_character(c)
        self.db.conn.execute('SAVEPOINT caller')
        c.character_xp=10**101
        self.db.save_character(c)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT caller')
        self.db.conn.execute('RELEASE SAVEPOINT caller')
        self.assertEqual(self.character().character_xp,10**100)

    def test_second_shadow_failure_rolls_back_wallet_and_character(self):
        c=self.character();prior=(c.character_xp,c.silver)
        self.db.conn.execute('''CREATE TRIGGER forced_shadow_failure BEFORE INSERT
          ON big_number_live_character_v10400
          WHEN NEW.axis='soul_xp' BEGIN SELECT RAISE(ABORT,'forced'); END''')
        c.character_xp=10**100;c.soul_xp=10**101;c.silver+=100
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(c)
        again=self.character()
        self.assertEqual((again.character_xp,again.silver),prior)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_character_v10400').fetchone()[0],0)

    def test_one_reward_transaction_rollback_across_all_big_number_routes(self):
        self.db.ensure_profession(self.uid, 'Zielarstwo')
        self.db.ensure_tool(self.uid, 'kilof')
        self.db.ensure_class_progress(self.uid, 'Wojownik')
        c=self.character()
        try:
            with self.db.conn.deferred_commits():
                c.character_xp=10**100
                c.soul_xp=10**101
                self.db.save_character(c)
                self.db.save_profession(self.uid, 'Zielarstwo', 800, 10**102, 1)
                self.db.save_tool(self.uid, 'kilof', 800, 10**103, 1)
                from storage.big_number_live_keyed_xp_v10400 import write_live_keyed_xp
                write_live_keyed_xp(self.db,self.uid,'class','Wojownik',level=800,xp=10**104)
                raise RuntimeError('Symulowana awaria rozliczenia walki')
        except RuntimeError:  # AUDIT_INTENTIONAL_PASS: wymuszona awaria, rollback sprawdzany ponizej
            pass
        self.assertEqual(self.character().character_xp, 0)
        self.assertEqual(self.character().soul_xp, 0)
        self.assertEqual(self.db.profession(self.uid,'Zielarstwo')['xp'],0)
        self.assertEqual(self.db.tool(self.uid,'kilof')['xp'],0)
        self.assertEqual(self.db.class_progress_row(self.uid,'Wojownik')['xp'],0)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_character_v10400').fetchone()[0],0)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_keyed_xp_v10400').fetchone()[0],0)

    def test_currency_int64_limit_still_in_place(self):
        c=self.character();prior=c.character_xp;c.character_xp=10**100;c.silver=10**100
        with self.assertRaises(OverflowError):
            self.db.save_character(c)
        self.assertEqual(self.character().character_xp,prior)

    def test_foreign_key_cascade_for_character_data(self):
        c=self.character();c.character_xp=10**100
        self.db.save_character(c)
        self.db.conn.execute('DELETE FROM accounts WHERE id=?',(self.uid,))
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_character_v10400').fetchone()[0],0)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_live_character_receipt_v10400').fetchone()[0],0)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CharacterProductionLiveTests)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Produkcyjny BigNumber CharacterProductionLiveTests: blad testow.')
    return result.testsRun


if __name__=='__main__':unittest.main()
