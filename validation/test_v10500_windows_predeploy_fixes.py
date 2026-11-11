# -*- coding: utf-8 -*-
"""Regresja trzech rzeczywistych blokad Windows PREDEPLOY v105 (2026-11-02)."""
import ast
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from validation.v4200_modularization import (
    LEDGER, V104_UNLOCK_AST_SHA256, V105_UNLOCK_AST_SHA256,
    expected_moved_ast_digest_v4200,
)
from validation.v4200_virtual_source import read_actual_refactored_source_v4200

ROOT = Path(__file__).resolve().parents[1]
SYMBOL = 'SessionSkillLearningMixin.unlock'


class WindowsPredeployFixes(unittest.TestCase):
    def test_legacy_ledger_and_current_unlock_ast_remain_strict(self):
        oldrel, newrel, original, _ = LEDGER[SYMBOL]
        self.assertEqual(original, V104_UNLOCK_AST_SHA256)
        src = ast.parse((ROOT / newrel).read_text(encoding='utf-8'))
        nodes = [n for n in src.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'unlock']
        self.assertEqual(len(nodes), 1)
        body = nodes[0]
        self.assertEqual(expected_moved_ast_digest_v4200(ROOT, SYMBOL, original, body), V105_UNLOCK_AST_SHA256)
        self.assertEqual(sha256(ast.dump(body, include_attributes=False).encode()).hexdigest(), V105_UNLOCK_AST_SHA256)
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            (folder / 'VERSION').write_text('104.00.3', encoding='utf-8')
            self.assertEqual(expected_moved_ast_digest_v4200(folder, SYMBOL, original, body), original)
            (folder / 'VERSION').write_text('105.00.0', encoding='utf-8')
            self.assertEqual(expected_moved_ast_digest_v4200(folder, SYMBOL, original, body), V105_UNLOCK_AST_SHA256)
            with self.assertRaises(AssertionError):
                expected_moved_ast_digest_v4200(folder, SYMBOL, '0' * 64, body)

    def test_fast_and_full_predeploy_reconstruct_v105_unlock(self):
        code = read_actual_refactored_source_v4200(ROOT / 'player/session_mixins/skill_learning.py')
        tree = ast.parse(code)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionSkillLearningMixin')
        fn = next(n for n in klass.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'unlock')
        self.assertIn('% 10 == 0', ast.unparse(fn))
        self.assertIn('SOUL_TRIAL_QUEST_IDS', ast.unparse(fn))
        self.assertNotIn('Unbound Soulbound method unlock', ast.unparse(fn))


if __name__ == '__main__':
    unittest.main()
