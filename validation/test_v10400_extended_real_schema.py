# -*- coding: utf-8 -*-
"""Real Soulbound SQLite schema, one synthetic player, copy-only BigNumber test."""
import tempfile
import unittest
from pathlib import Path
from storage.database import Database
from validation.v10400_migration_rehearsal import rehearse


class FullSchemaCopy(unittest.TestCase):
    def test_real_game_schema_and_synthetic_character(self):
        with tempfile.TemporaryDirectory(prefix='sb104_real_schema_gate_') as tmp:
            path = Path(tmp) / 'source.sqlite'
            db = Database(str(path))
            conn = db.conn
            try:
                conn.execute("INSERT INTO accounts(id,username,password_salt,password_hash) VALUES(1,'Pilot','sample','sample')")
                mandatory = {}
                for column in conn.execute('PRAGMA table_info(characters)').fetchall():
                    _, name, dtype, nonnull, default, _pk = column
                    if name == 'account_id': mandatory[name] = 1
                    elif name == 'name': mandatory[name] = 'Pilot'
                    elif name in ('race', 'class_name', 'class_type', 'soul_weapon'):
                        mandatory[name] = 'Test'
                    elif nonnull and default is None:
                        mandatory[name] = 1 if 'INT' in dtype.upper() else 'Test'
                cols = ','.join('"'+key+'"' for key in mandatory)
                binds = ','.join('?' for _ in mandatory)
                conn.execute(f'INSERT INTO characters ({cols}) VALUES ({binds})',tuple(mandatory.values()))
                conn.execute('INSERT INTO account_wallet(master_account_id,silver,gold,mithril) VALUES(1,2,3,4)')
                conn.execute('INSERT INTO bank_balances(account_id,silver,gold,mithril) VALUES(1,5,6,7)')
                conn.execute("INSERT INTO class_progress(account_id,class_name,xp) VALUES(1,'Mag',8)")
                conn.execute("INSERT INTO professions(account_id,profession,xp) VALUES(1,'Kowalstwo',9)")
                conn.execute("INSERT INTO tools(account_id,tool_type,xp) VALUES(1,'kilof',10)")
                conn.commit()
            finally:
                conn.close()
            result = rehearse(path)
            self.assertEqual(result['preflight']['total_cells'], 12)
            self.assertEqual(result['extended_preflight']['cells'], 14)
            self.assertEqual(result['extended_mirrored'], 14)
            self.assertEqual(result['shadow_checks'], 26)
            self.assertEqual(result['production_modified'], 'NIE')

if __name__=='__main__': unittest.main()
