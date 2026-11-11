# -*- coding: utf-8 -*-
"""Regression: release integrity checks must never parse .bat as Python."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from validation import v10400_release_safety_check as gate

class ReleaseFilesGate(unittest.TestCase):
    def test_real_packed_file_types_pass(self):
        self.assertEqual(gate.inspect(),len(gate.MUST_EXIST))

    def test_windows_bat_must_call_copy_rehearsal(self):
        with tempfile.TemporaryDirectory(prefix='sb104_manifest_') as tmp:
            base=Path(tmp)
            for rel in gate.MUST_EXIST:
                file=base/rel
                file.parent.mkdir(parents=True,exist_ok=True)
                file.write_text('x=1\n' if rel.endswith('.py') else '@echo off\nexit /b 0\n',encoding='utf-8')
            (base/'VERSION').write_text('104.00.0',encoding='utf-8')
            with patch.object(gate,'ROOT',base):
                with self.assertRaisesRegex(AssertionError,'BAT'):
                    gate.inspect()
                (base/'SPRAWDZ_V104_MIGRACJE_NA_KOPII_BAZY.bat').write_text(
                    '@echo off\npy -3 -m validation.v10400_migration_rehearsal --db "%~1"\nexit /b 0\n',encoding='utf-8')
                self.assertEqual(gate.inspect(),len(gate.MUST_EXIST))

if __name__=='__main__':unittest.main()
