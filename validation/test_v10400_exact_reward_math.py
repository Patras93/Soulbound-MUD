# -*- coding: utf-8 -*-
"""Testy zaokraglen wielkich nagrod bez utraty precyzji i regresji malych."""
import ast
import random
import unittest
from pathlib import Path
from core.exact_reward_math_v10400 import (
    scale_multiplier_xp_v10400 as mult, scale_percent_xp_v10400 as pct,
)

class ExactRewardMathTests(unittest.TestCase):
    def test_small_legacy_percentage(self):
        rng=random.Random(10400)
        for _ in range(500):
            amount=rng.randrange(0, 1000000)
            bonus=rng.randrange(0, 400)
            self.assertEqual(pct(amount, bonus), int(round(amount*(1+bonus/100))))
    def test_small_legacy_multiplier(self):
        rng=random.Random(10401)
        for _ in range(500):
            amount=rng.randrange(0, 1000000)
            factor=rng.randrange(0, 401)/100
            self.assertEqual(mult(amount, factor), int(round(amount*factor)))
    def test_high_precision_percentage(self):
        amount=(1<<53)+1
        self.assertEqual(pct(amount, 25), (amount*5+2)//4)
        self.assertEqual(pct(10**100+1,100), 2*(10**100+1))
    def test_high_precision_multiplier(self):
        amount=(1<<53)+1
        self.assertEqual(mult(amount, 1.25), (amount*5+2)//4)
        self.assertEqual(mult(10**100, 2), 2*10**100)
    def test_nearest_even(self):
        self.assertEqual(pct((1<<54)+2,25),((1<<54)+2)*5//4)
        self.assertEqual(pct(10**100+2,25), (10**100+2)*5//4)  # .5 zaokraglone do parzystej
    def test_reject_invalid(self):
        for args in ((True,1.0),(-1,1.0),(1,float('nan')),(1,float('inf')),(1,-2.0)):
            with self.assertRaises(ValueError): mult(*args)
        for args in ((True,5),(1,True),(1,-5),(-1,5)):
            with self.assertRaises(ValueError): pct(*args)
    def test_active_call_sites(self):
        root=Path(__file__).resolve().parents[1]
        for relative in ('player/character.py','player/session_mixins/class_progression.py'):
            tree=ast.parse((root/relative).read_text('utf-8'))
            names=[node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
            self.assertIn('scale_percent_xp_v10400',names)
        content=(root/'player/character.py').read_text('utf-8')
        self.assertIn('scale_multiplier_xp_v10400(base_amount, self.racial_soul_xp_multiplier())',content)

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ExactRewardMathTests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful(): raise AssertionError('EXACT REWARD MATH FAIL')
    return result.testsRun

if __name__=='__main__':
    print('V104 PRECISION:',run(),'PASS')
