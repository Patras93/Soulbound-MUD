# -*- coding: utf-8 -*-
"""Historyczny audyt bezpieczeństwa Windows bez archiwalnego BAT v104.

W v110 testujemy rzeczywistą, obsługiwaną ścieżkę odłączonej migawki,
nie przechowujemy nieczynnego skryptu uruchamiającego v104.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WindowsFinalDiagnostics(unittest.TestCase):
    def test_current_predeploy_keeps_live_database_detached(self):
        self.assertFalse((ROOT/'SPRAWDZ_V104_KONCOWO_WINDOWS_BEZ_WDROZENIA.bat').exists())
        source=(ROOT/'predeploy_nowej_wersji.py').read_text(encoding='utf-8')
        self.assertIn('create_detached_source_snapshot(', source)
        self.assertIn('with tempfile.TemporaryDirectory(prefix=prefix) as frozen_dir:', source)
        self.assertIn("env['SOULBOUND_ULTRA_SOURCE_DB'] = str(snapshot)", source)
        self.assertIn("env['SOULBOUND_DB'] = str(snapshot)", source)
        self.assertNotIn('call wdroz_po_predeploy.bat', source.lower())

    def test_current_standard_entrypoints_are_guarded(self):
        bat=(ROOT/'PREDEPLOY_NOWEJ_WERSJI.bat').read_text(encoding='utf-8')
        self.assertIn('### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP', bat)
        self.assertIn('predeploy_nowej_wersji.py', bat)
        deploy=(ROOT/'wdroz_po_predeploy.py').read_text(encoding='utf-8')
        self.assertIn("s.get('quality_gate')!='ULTIMATE-60-PLUS'", deploy)
        self.assertIn("sha256(z)!=s.get('sha256')", deploy)
        self.assertIn("input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ')", deploy)

    def test_copy_tool_uses_sqlite_read_only_backup(self):
        source = (ROOT/'validation'/'v10400_migration_rehearsal.py').read_text(encoding='utf-8')
        self.assertIn('open_read_only(db_path)', source)
        read_only_source=(ROOT/'validation'/'v10400_big_number_audit.py').read_text(encoding='utf-8')
        self.assertIn("path.as_uri()+'?mode=ro'", read_only_source)
        self.assertIn('source.backup(target)', source)

if __name__ == '__main__':
    unittest.main()
