# -*- coding: utf-8 -*-
"""Zgodnosc premii Soul/klas/gildii w realnej sciezce walki."""
import ast
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import random
import unittest
from core.exact_reward_math_v10400 import scale_bonus_percent_v10400 as bonus


class CombatPrecisionV104Tests(unittest.TestCase):
    def test_small_exact_legacy(self):
        rng=random.Random(104104)
        for _ in range(3000):
            amount=rng.randrange(0,10**7)
            percent=rng.randrange(0,3001)/10
            self.assertEqual(bonus(amount,percent), max(0, int(round(amount*(1.0+percent/100.0)))))

    def test_high_exact_integer(self):
        x=10**100+1
        self.assertEqual(bonus(x,25), (x*5+2)//4)
        self.assertEqual(bonus(x,100), x*2)
        self.assertEqual(bonus(x,0),x)

    def test_high_fractional_percent(self):
        x=10**100+17
        p=12.5
        f=1+Fraction(Decimal(str(p)))/100
        n,r=divmod(x*f.numerator,f.denominator)
        self.assertEqual(bonus(x,p),n+(2*r>f.denominator or (2*r==f.denominator and n%2==1)))

    def test_no_float_overflow(self):
        self.assertEqual(bonus(10**350,100),2*10**350)

    def test_invalid(self):
        for percent in [float('nan'),float('inf'),float('-inf'),-1,-0.1,True,'25']:
            with self.assertRaises((ValueError,TypeError)):
                bonus(100,percent)
        for amount in [-1,True,1.5]:
            with self.assertRaises((ValueError,TypeError)):
                bonus(amount,10)

    def test_active_kill_path(self):
        s=(Path(__file__).resolve().parents[1]/'player/session_mixins/combat_rewards.py').read_text(encoding='utf-8')
        t=ast.parse(s)
        calls=[node.func.id for node in ast.walk(t) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name)]
        self.assertGreaterEqual(calls.count('scale_bonus_percent_v10400'),3)
        self.assertIn('_soul_payout_v104 = scale_bonus_percent_v10400',s)
        self.assertIn('_class_payout_v104 = scale_bonus_percent_v10400',s)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CombatPrecisionV104Tests)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful(): raise AssertionError('LIVE COMBAT PRECISION FAIL')
    return result.testsRun

if __name__=='__main__':
    print('LIVE COMBAT PRECISION',run(),'PASS')
