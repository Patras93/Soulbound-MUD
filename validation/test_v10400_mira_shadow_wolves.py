# -*- coding: utf-8 -*-
"""Regresja: Zielarka Mira podaje taka sama liczbe wilkow co postep questa."""
from __future__ import annotations
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MiraShadowWolvesQuestTest(unittest.TestCase):
    def test_base_quest_requires_twelve_and_says_twelve(self):
        from data.quests import QUESTS
        q = QUESTS['shadow_wolves']
        self.assertEqual(q['giver'], 'Zielarka Mira')
        self.assertEqual(q['target'], 'shadow_wolf')
        self.assertEqual(q['needed'], 12)
        self.assertIn('12 Wilków Cienia', q['description'])
        self.assertNotIn('2 Wilki Cienia', q['description'])

    def _check_installed_description(self, needed):
        # Wlasny proces: rozbudowa swiata zmienia katalogi globalne.
        code = '''
from systems.dungeons_regions import QUESTS
from world.expansion_frontier_forest_v407 import build_forest_wolves_and_quest_balance
QUESTS['shadow_wolves']['needed'] = int(__import__('sys').argv[1])
build_forest_wolves_and_quest_balance()
q = QUESTS['shadow_wolves']
assert q['needed'] == int(__import__('sys').argv[1])
assert f"{q['needed']} Wilków Cienia" in q['description'], q
assert 'Po ukończeniu' in q['description']
'''
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        proc = subprocess.run([sys.executable, '-B', '-c', code, str(needed)],
                              cwd=ROOT, env=env, capture_output=True, text=True,
                              timeout=20, encoding='utf-8', errors='replace')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_forest_expansion_says_twelve(self):
        self._check_installed_description(12)

    def test_forest_expansion_description_tracks_custom_requirement(self):
        # Chroni przed powrotem stalej liczby w opisie przy edycji celu.
        self._check_installed_description(16)


if __name__ == '__main__':
    unittest.main()
