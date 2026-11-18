# -*- coding: utf-8 -*-
"""Regression v115: guarded Cyborg creation and atomic failure rollback.
Only disposable SQLite fixtures; no production DB access.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from storage.database import Database
from core.classes_skills import RACES, CLASSES


class TestCharacterCreationAtomicV115(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix='sb11410_cyborg_')
        self.db = Database(str(Path(self.tmp.name) / 'game.sqlite'))
        self.account = self.db.create_account('TestCharacter11410', 'StrongPassword11410Test!')
        self.cases = {c: 'Test' for c in ('nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc')}
        self.race = next(r for r in RACES if r[0] == 'Cyborg')
        self.cls = next(c for c in CLASSES if c[0] == 'Wojownik')

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def count(self, table):
        assert table in ('accounts', 'characters', 'account_characters', 'inventory', 'class_progress')
        return self.db.conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]

    def test_cyborg_has_no_board_under_equipment_guard(self):
        self.db.conn.execute("CREATE TEMP TRIGGER guard_example BEFORE INSERT ON main.inventory "
            "WHEN NEW.item_id='moogle_board' BEGIN SELECT RAISE(ABORT, "
            "'v107 EQ: nieśledzony zapis fizycznego przedmiotu'); END")
        char, slot = self.db.create_character_for_master(
            self.account, 'NewCyborg', self.race, self.cls, self.cases)
        self.assertEqual((char,slot), (self.account,1))
        self.assertEqual(self.db.item_qty(char,'moogle_board'), 0)
        self.assertEqual(self.db.item_qty(char,'healing_potion'), 2)
        self.assertEqual(self.count('account_characters'), 1)
        self.assertEqual(self.db.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_old_orphan_not_relinked_on_database_restart(self):
        # Reproduce an old interrupted character creation on an existing
        # master account.  The hidden account still owns a character, but its
        # roster link was never committed.  Startup may not silently adopt it.
        self.db.create_character_for_master(
            self.account, 'OwnedBefore', self.race, self.cls, self.cases)
        ghost_id = self.db.create_account('HiddenOrphan114', 'StrongPassword11410Test!')
        self.db.create_character(ghost_id, 'OrphanBefore', self.race, self.cls, self.cases)
        before = list(self.db.conn.execute(
            'SELECT master_account_id,character_account_id,slot FROM account_characters ORDER BY master_account_id,slot'))
        self.assertIsNone(self.db.conn.execute(
            'SELECT 1 FROM account_characters WHERE character_account_id=?',(ghost_id,)).fetchone())
        path = self.db.path
        self.db.conn.close()
        self.db = Database(path)
        after = list(self.db.conn.execute(
            'SELECT master_account_id,character_account_id,slot FROM account_characters ORDER BY master_account_id,slot'))
        self.assertEqual([tuple(x) for x in after], [tuple(x) for x in before])
        self.assertIsNone(self.db.conn.execute(
            'SELECT 1 FROM account_characters WHERE character_account_id=?',(ghost_id,)).fetchone())
        self.assertIsNotNone(self.db.conn.execute(
            'SELECT name FROM characters WHERE account_id=?',(ghost_id,)).fetchone())
        self.assertEqual(self.db.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_failed_first_character_leaves_no_ghost(self):
        self.db.conn.execute("CREATE TEMP TRIGGER failing_inventory BEFORE INSERT ON main.inventory "
            "WHEN NEW.item_id='healing_potion' BEGIN SELECT RAISE(ABORT, 'test rollback'); END")
        with self.assertRaisesRegex(Exception,'test rollback'):
            self.db.create_character_for_master(self.account,'BadFirst',self.race,self.cls,self.cases)
        for tbl in ('characters', 'account_characters', 'inventory','class_progress'):
            self.assertEqual(self.count(tbl),0,tbl)
        self.assertEqual(self.count('accounts'),1)
        self.db.conn.execute('DROP TRIGGER failing_inventory')
        _,slot=self.db.create_character_for_master(self.account,'GoodFirst',self.race,self.cls,self.cases)
        self.assertEqual(slot,1)

    def test_failed_later_character_leaves_no_hidden_account(self):
        self.db.create_character_for_master(self.account,'GoodFirst',self.race,self.cls,self.cases)
        counts={tbl:self.count(tbl) for tbl in ('accounts','characters','account_characters','inventory','class_progress')}
        self.db.conn.execute("CREATE TEMP TRIGGER failing_inventory BEFORE INSERT ON main.inventory "
            "WHEN NEW.item_id='healing_potion' BEGIN SELECT RAISE(ABORT, 'test rollback'); END")
        for i in range(2):
            with self.assertRaisesRegex(Exception,'test rollback'):
                self.db.create_character_for_master(self.account,f'BadSecond{i}',self.race,self.cls,self.cases)
            self.assertEqual({tbl:self.count(tbl) for tbl in counts},counts)
        self.db.conn.execute('DROP TRIGGER failing_inventory')
        _,slot=self.db.create_character_for_master(self.account,'GoodSecond',self.race,self.cls,self.cases)
        self.assertEqual(slot,2)
        self.assertEqual(self.db.conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        self.assertEqual(list(self.db.conn.execute('PRAGMA foreign_key_check')),[])


if __name__ == '__main__':
    unittest.main()
