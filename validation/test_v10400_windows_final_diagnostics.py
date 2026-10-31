# -*- coding: utf-8 -*-
"""Static, platform-independent safety checks of Windows-only diagnostics.

This test DOES NOT claim that Windows PREDEPLOY has run on this host.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BAT = ROOT / 'SPRAWDZ_V104_KONCOWO_WINDOWS_BEZ_WDROZENIA.bat'


class WindowsFinalDiagnostics(unittest.TestCase):
    def test_starts_from_archive_directory_and_not_live_server(self):
        body = BAT.read_text(encoding='utf-8').lower()
        self.assertIn('cd /d "%~dp0"', body)
        self.assertIn('set "soulbound_db="', body)
        self.assertIn('set "database_url="', body)
        self.assertNotIn('call wdroz_po_predeploy.bat', body)
        self.assertNotIn('python zainstaluj_predeploy.py', body)

    def test_uses_only_diagnostic_entrypoints(self):
        body = BAT.read_text(encoding='utf-8').lower()
        self.assertIn('validation.v10400_one_archive_verify --pelny', body)
        self.assertIn('validation.v10400_migration_rehearsal --db', body)
        self.assertIn('soULbound_v104_kontrola_windows_pl.txt'.lower(), body)
        self.assertIn('nie jest zgoda na wdrozenie', body)

    def test_copy_tool_uses_sqlite_read_only_backup(self):
        source = (ROOT / 'validation' / 'v10400_migration_rehearsal.py').read_text(encoding='utf-8')
        self.assertIn('open_read_only(db_path)', source)
        read_only_source = (ROOT / 'validation' / 'v10400_big_number_audit.py').read_text(encoding='utf-8')
        self.assertIn("path.as_uri()+'?mode=ro'", read_only_source)
        self.assertIn('source.backup(target)', source)


if __name__ == '__main__':
    unittest.main()
