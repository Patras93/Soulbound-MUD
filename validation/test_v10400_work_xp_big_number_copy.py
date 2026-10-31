# -*- coding: utf-8 -*-
"""BigNumber professions/tools, real DB methods on disposable copies only."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from storage.db_inventory import DatabaseInventoryMixin
from validation.test_v10400_real_character_big_number_rehearsal import CopyDB
from core.big_numbers_v10400 import SQLITE_INT64_MAX
from storage.big_number_shadow_v10400 import check_shadow,install_shadow_schema

class WorkCopyDB(DatabaseInventoryMixin, CopyDB):
    def __init__(self,folder):
        super().__init__(folder)
        self.conn.execute('CREATE TABLE professions(account_id INTEGER, profession TEXT, level INTEGER, xp INTEGER, actions INTEGER, PRIMARY KEY(account_id,profession))')
        self.conn.execute('CREATE TABLE tools(account_id INTEGER, tool_type TEXT, level INTEGER, xp INTEGER, uses INTEGER, PRIMARY KEY(account_id,tool_type))')
        self.conn.commit()

class WorkBigNumberCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='sb104_work_copy_')
        self.folder=Path(self.tmp.name)
        (self.folder/'.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TYLKO KOPIA',encoding='utf-8')
        self.db=WorkCopyDB(self.folder)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_professions_and_tools_independent_values_after_reopen(self):
        self.db.ensure_profession(1,'Zielarstwo')
        self.db.ensure_profession(1,'Kowalstwo')
        self.db.ensure_tool(1,'młot')
        self.db.save_profession(1,'Zielarstwo',1000,10**200+41,55)
        self.db.save_profession(1,'Kowalstwo',1001,10**201+42,77)
        self.db.save_tool(1,'młot',9999,10**202+43,88)
        self.db.conn.close()
        self.db.conn=sqlite3.connect(self.db.path)
        self.db.conn.row_factory=sqlite3.Row
        self.assertEqual(self.db.profession(1,'Zielarstwo')['xp'],10**200+41)
        self.assertEqual(self.db.profession(1,'Kowalstwo')['xp'],10**201+42)
        self.assertEqual(self.db.tool(1,'młot')['xp'],10**202+43)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM tools').fetchone()[0],SQLITE_INT64_MAX)
        self.assertEqual(check_shadow(self.db.conn),3)

    def test_legacy_path_refuses_overflow_and_preserves_rows(self):
        self.db._v104_big_number_copy_rehearsal=False
        self.db.ensure_profession(1,'Kowalstwo')
        self.db.ensure_tool(1,'kilof')
        for f,args in [(self.db.save_profession,(1,'Kowalstwo',1000,10**100,1)),
                       (self.db.save_tool,(1,'kilof',1000,10**100,1))]:
            with self.assertRaises(OverflowError):f(*args)
        self.assertEqual(self.db.profession(1,'Kowalstwo')['xp'],0)
        self.assertEqual(self.db.tool(1,'kilof')['xp'],0)

    def test_missing_marker_prevents_write_and_lazy_insert(self):
        (self.folder/'.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError): self.db.profession(1,'Nowa')
        with self.assertRaises(PermissionError): self.db.tool(1,'Nowe')
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM tools').fetchone()[0],0)

    def test_external_legacy_mutation_is_rejected(self):
        self.db.ensure_tool(1,'kilof')
        self.db.save_tool(1,'kilof',1000,10**150,3)
        self.db.conn.execute('UPDATE tools SET xp=3 WHERE tool_type=?',('kilof',))
        with self.assertRaisesRegex(ValueError,'poza migracj'):self.db.tool(1,'kilof')
        with self.assertRaisesRegex(ValueError,'poza migracj'):self.db.save_tool(1,'kilof',1000,10**151,3)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM tools').fetchone()[0],3)

    def test_failed_shadow_insert_rolls_back(self):
        self.db.ensure_profession(1,'Kowalstwo')
        install_shadow_schema(self.db.conn)
        self.db.conn.execute('''CREATE TRIGGER block_prof BEFORE INSERT ON big_number_shadow_v10400
          WHEN NEW.axis='professions.xp' BEGIN SELECT RAISE(ABORT,'failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError): self.db.save_profession(1,'Kowalstwo',2000,10**300,100)
        row=self.db.conn.execute('SELECT level,xp,actions FROM professions').fetchone()
        self.assertEqual(tuple(row),(1,0,0))

if __name__=='__main__':unittest.main()
