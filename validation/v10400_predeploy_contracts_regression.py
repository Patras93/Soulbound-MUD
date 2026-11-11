# -*- coding: utf-8 -*-
"""Compatibility audit for v104 without disabling old gameplay safeguards.

This verifies the 800-level historical catalog, the specifically reviewed
v104 5000+ skills and the crypt generator baseline fingerprint. No DB or TCP.
"""
from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import unittest

from core.classes_skills import CLASS_SKILLS
from validation.v10400_skill_catalog_contract import old_and_new_skills
from validation.class_balance_v1172 import audit_class_skill_balance_v1172
from validation.v4100_large_modularization import SPLIT_SYMBOLS


class V104PredeployContracts(unittest.TestCase):
    def test_legacy_and_new_skill_unlocks(self):
        old, new = old_and_new_skills(CLASS_SKILLS)
        self.assertFalse(audit_class_skill_balance_v1172()['errors'])
        for name in old:
            self.assertTrue(all(1 <= int(r['unlock']) <= 800 for r in old[name]
                                if r.get('unlock') is not None), name)
            self.assertEqual(sorted(int(r['unlock']) for r in new[name]),
                             [5200, 7600, 9800], name)

    def test_crypt_baseline_is_pinned(self):
        root = Path(__file__).resolve().parents[1]
        symbol = 'create_infinite_crypt_floor_definition'
        old_path, new_path, pinned, _ = SPLIT_SYMBOLS[symbol]
        self.assertEqual(old_path, 'world/economy_quests.py')
        self.assertEqual(new_path, 'world/v410_infinite_floors.py')
        tree = ast.parse((root/new_path).read_text(encoding='utf-8'))
        matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name==symbol]
        self.assertEqual(len(matches), 1)
        digest = sha256(ast.dump(matches[0], include_attributes=False).encode()).hexdigest()
        self.assertEqual(digest, pinned)

    def test_exception_audit_no_unreviewed_silencing(self):
        from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571
        self.assertEqual(FAST_PREDEPLOY_AUDIT_V0571['swallowed_exception_count'], 0)


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(V104PredeployContracts)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Regresja kontraktow historycznych v104 nie przeszla.')
    return result.testsRun

if __name__ == '__main__':
    print('V104 HISTORICAL CONTRACTS:', run(), 'PASS')
