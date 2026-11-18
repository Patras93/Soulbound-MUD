# -*- coding: utf-8 -*-
from pathlib import Path
import hashlib
import tempfile
import unittest
from release_readme_cleanup import V115_DISTRIBUTED_NOTES, cleanup_legacy_readmes
from unittest.mock import patch

class DocumentsCleanup(unittest.TestCase):
    def test_known_documents_backup_and_clean(self):
        self.assertEqual(len(V115_DISTRIBUTED_NOTES), 18)
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            root = work / 'Soulbound-MUD'
            root.mkdir()
            src = Path(__file__).resolve().parents[1]
            # Test with certified original bytes supplied inside this test's fixtures.
            # SHA mismatches must leave files untouched.
            (root / 'CHANGELOG_PL.txt').write_text('changelog', encoding='utf-8')
            (root / 'soulbound_world_seed.txt').write_text('TRWALY-SEED', encoding='utf-8')
            (root / 'CZYTAJ_V115_PL.txt').write_text('ZMODYFIKOWANY-PLIK',encoding='utf-8')
            retired, archived = cleanup_legacy_readmes(root, work/'backup')
            self.assertEqual(retired, [])
            self.assertIsNone(archived)
            self.assertEqual((root/'CZYTAJ_V115_PL.txt').read_text(), 'ZMODYFIKOWANY-PLIK')
            self.assertEqual((root/'soulbound_world_seed.txt').read_text(), 'TRWALY-SEED')
            self.assertEqual((root/'CHANGELOG_PL.txt').read_text(), 'changelog')
    def test_backup_then_delete_exact_known_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=base/'Soulbound-MUD';root.mkdir()
            sample=b'raport etapu 115\n'
            name='ETAP12_KOREKTA_STARYCH_EXPOWISK_PL.txt'
            (root/name).write_bytes(sample)
            (root/'CHANGELOG_PL.txt').write_text('historia',encoding='utf-8')
            (root/'soulbound_world_seed.txt').write_text('nie zmieniaj',encoding='utf-8')
            with patch.dict(V115_DISTRIBUTED_NOTES,{name:hashlib.sha256(sample).hexdigest()}):
                names,backup=cleanup_legacy_readmes(root,base/'backup')
            self.assertEqual(names,[name])
            self.assertFalse((root/name).exists())
            self.assertEqual((backup/name).read_bytes(),sample)
            self.assertTrue((root/'CHANGELOG_PL.txt').exists())
            self.assertEqual((root/'soulbound_world_seed.txt').read_text(),'nie zmieniaj')
    def test_release_docs_not_in_candidate_sources(self):
        root = Path(__file__).resolve().parents[1]
        actual = [p.name for p in root.iterdir() if p.is_file() and p.suffix.lower() in {'.txt','.md','.rst'}]
        # Tests may materialize the private runtime seed next to DB_PATH.
        # It is removed when constructing the distributable ZIP.
        self.assertEqual(sorted(set(actual)-{'soulbound_world_seed.txt'}), ['CHANGELOG_PL.txt'])

if __name__ == '__main__':
    unittest.main()
