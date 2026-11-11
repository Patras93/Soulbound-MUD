# -*- coding: utf-8 -*-
"""Fail-closed historical quest ID protection, without starting the game."""
import json
import unittest

from validation.v10400_profession_quest_baseline import FIXTURE, check_baseline


class LegacyProfessionQuestIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def _catalog(self):
        # The lightweight negative controls exercise the contract itself.
        groups = {}
        for qid, r in self.source.items():
            q = {key: r[key] for key in ('name', 'requires_quest', 'reward_profession',
                                        'required_profession', 'target') if key in r and key != 'name'}
            q['name'] = r['name']
            q['requires_quest'] = r['requ']
            groups.setdefault(r['prof'], []).append((qid, q))
        for index in range(140):
            qid = f'v10400_contract_test_{index:03d}'
            groups.setdefault('Archeologia', []).append((qid, {
                'name': qid, 'required_profession': 'Archeologia',
                'reward_profession': 'Archeologia', 'target': 'Archeologia'}))
        registry = {qid: quest for group in groups.values() for qid, quest in group}
        return registry, groups

    def test_frozen_real_v103_has_six_starter_ids(self):
        self.assertEqual(len(self.source), 2375)
        for name in ('archaeology','carpentry','cartography_profession',
                     'enchanting','leatherworking','tailoring'):
            self.assertIn('v0701_beginner_' + name, self.source)

    def test_full_historical_catalog_is_accepted(self):
        quests, groups = self._catalog()
        self.assertEqual(check_baseline(quests, groups)['total'], 2515)

    def test_silent_drop_of_any_one_starter_is_blocked(self):
        quests, groups = self._catalog()
        groups['Archeologia'] = [(k, q) for k, q in groups['Archeologia']
                                if k != 'v0701_beginner_archaeology']
        with self.assertRaisesRegex(AssertionError, 'brak'):
            check_baseline(quests, groups)

    def test_silent_rename_of_historical_quest_is_blocked(self):
        quests, groups = self._catalog()
        quests['v0701_beginner_tailoring']['name'] = 'Zamiana nazwy'
        with self.assertRaisesRegex(AssertionError, 'zmienione'):
            check_baseline(quests, groups)

    def test_unreviewed_new_id_is_blocked(self):
        quests, groups = self._catalog()
        qid, q = groups['Archeologia'][-1]
        self.assertTrue(qid.startswith('v10400_'))
        groups['Archeologia'][-1] = ('unexpected_mod_001', q)
        with self.assertRaisesRegex(AssertionError, 'nowe questy'):
            check_baseline(quests, groups)


if __name__ == '__main__':
    unittest.main()
