# -*- coding: utf-8 -*-
"""A test runner may not claim PASS when it did not select any tests."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from validation import v10400_suite_isolated as runner

class SuiteRangeSafety(unittest.TestCase):
    def test_no_index_zero(self):
        with self.assertRaisesRegex(ValueError, 'Zakres'):
            runner.run(start_index=0)

    def test_no_index_past_last(self):
        with self.assertRaisesRegex(ValueError, 'Zakres'):
            runner.run(start_index=len(runner.TESTS)+1)

    def test_end_before_start(self):
        with self.assertRaisesRegex(ValueError, 'Zakres'):
            runner.run(start_index=2, end_index=1)

    def test_no_end_past_last(self):
        with self.assertRaisesRegex(ValueError, 'Zakres'):
            runner.run(end_index=len(runner.TESTS)+1)

    def test_no_empty_suite(self):
        with patch.object(runner, 'TESTS', ()): 
            with self.assertRaisesRegex(ValueError, 'Lista'):
                runner.run()

    def test_no_duplicate_modules(self):
        with patch.object(runner, 'TESTS', ('one','one')): 
            with self.assertRaisesRegex(ValueError, 'Lista'):
                runner.run()

if __name__ == '__main__': unittest.main()
