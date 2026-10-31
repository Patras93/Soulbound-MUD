# -*- coding: utf-8 -*-
"""Regression: a release must contain only one documentation TXT."""
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from validation.v10400_clean_archive import file_list, pack


class CleanArchive(unittest.TestCase):
    def fixture(self, root):
        for name in ('VERSION', 'server.py', 'predeploy_check.py',
                     'core/bootstrap_economy_professions.py', 'CHANGELOG_PL.txt',
                     'world/some_quests.py', 'data/quests.json',
                     'RAPORT_WCZORAJSZY.txt', 'SUMY_SHA256.txt',
                     'CHANGELOG_ETAP_3.txt', 'soulbound_world_seed.txt',
                     'README_ETAP.md', 'logs/server.log'):
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(name, encoding='utf-8')

    def test_only_changelog_but_keep_game_code_and_json(self):
        with tempfile.TemporaryDirectory(prefix='sb104_clean_zip_') as td:
            root=Path(td)/'src'; root.mkdir(); self.fixture(root)
            names={name for name,_ in file_list(root)}
            self.assertIn('CHANGELOG_PL.txt',names)
            self.assertIn('world/some_quests.py',names)
            self.assertIn('data/quests.json',names)
            self.assertNotIn('soulbound_world_seed.txt',names)
            self.assertFalse(any(x.endswith(('.md','.log','.csv','.txt')) and x!='CHANGELOG_PL.txt' for x in names))
            zpath=Path(td)/'game.zip'
            count,sha=pack(root,zpath)
            self.assertEqual(count,len(names))
            self.assertEqual(len(sha),64)
            with ZipFile(zpath) as z:
                self.assertEqual(set(z.namelist()),names)
                self.assertEqual(z.read('CHANGELOG_PL.txt'),b'CHANGELOG_PL.txt')
            # Packaging must never erase the original seed or user files.
            self.assertTrue((root/'soulbound_world_seed.txt').exists())
            self.assertTrue((root/'RAPORT_WCZORAJSZY.txt').exists())

    def test_refuse_secret_even_when_not_txt(self):
        with tempfile.TemporaryDirectory(prefix='sb104_clean_secret_') as td:
            root=Path(td)/'src';root.mkdir();self.fixture(root)
            secret=root/'admin'/'private.pem'
            secret.parent.mkdir(parents=True)
            secret.write_text('secret',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Niebezpieczne pliki'):
                file_list(root)

    def test_refuse_sqlite_and_symlinks(self):
        with tempfile.TemporaryDirectory(prefix='sb104_clean_security_') as td:
            root=Path(td)/'src';root.mkdir();self.fixture(root)
            (root/'soulbound.db').write_bytes(b'private')
            with self.assertRaisesRegex(ValueError, 'baz/cache'):
                file_list(root)
            (root/'soulbound.db').unlink()
            if hasattr(Path,'symlink_to'):
                link=root/'world'/'link.py'
                try: link.symlink_to(root/'server.py')
                except (OSError, NotImplementedError): return
                with self.assertRaisesRegex(ValueError,'link'):
                    file_list(root)

if __name__ == '__main__':
    unittest.main()
