# -*- coding: utf-8 -*-
"""Follow-up Windows 60/60 failures: expanded professions and v105 sales guard."""
import json
import unittest
from validation.v10400_profession_quest_baseline import FIXTURE, check_baseline
from world.v10500_region_index import REGIONS


class ProfessionContractV105(unittest.TestCase):
    def _fixture(self):
        old = json.loads(FIXTURE.read_text(encoding='utf-8'))
        groups = {}
        for qid, row in old.items():
            quest = dict(name=row['name'], requires_quest=row['requ'],
                         reward_profession=row['reward_profession'],
                         required_profession=row['required_profession'], target=row['target'])
            groups.setdefault(row['prof'], []).append((qid, quest))
        for index in range(140):
            qid = f'v10400_contract_test_{index:03d}'
            groups.setdefault('Archeologia', []).append((qid, dict(name=qid,
                         required_profession='Archeologia', reward_profession='Archeologia',
                         target='Archeologia')))
        for slug, *_ in REGIONS:
            for index in range(1, 16):
                qid = f'v10500_{slug}_prof_{index:02d}'
                groups.setdefault('Archeologia', []).append((qid, dict(name=qid,
                         required_profession='Archeologia', reward_profession='Archeologia',
                         target='Archeologia')))
        registry = {qid: quest for entries in groups.values() for qid, quest in entries}
        return registry, groups

    def test_all_2815_profession_quests_preserved(self):
        registry, groups = self._fixture()
        result = check_baseline(registry, groups, version='105.00.0')
        self.assertEqual((result['historic_preserved'], result['new_v104'],
                          result['new_v105'], result['total']), (2375, 140, 300, 2815))

    def test_extra_quest_id_is_rejected(self):
        registry, groups = self._fixture()
        qid = 'v10500_unreviewed_prof_01'
        groups['Archeologia'].append((qid, dict(name=qid,
             required_profession='Archeologia', reward_profession='Archeologia',
             target='Archeologia')))
        registry[qid] = groups['Archeologia'][-1][1]
        with self.assertRaisesRegex(AssertionError, '300 questow'):
            check_baseline(registry, groups, version='105.00.0')

    def test_v104_does_not_accept_v105_quests(self):
        registry, groups = self._fixture()
        with self.assertRaises(AssertionError):
            check_baseline(registry, groups, version='104.00.3')

    def test_historical_v103_quest_mutation_is_rejected(self):
        registry, groups = self._fixture()
        registry['v0701_beginner_archaeology']['name'] = 'Zmieniony quest'
        with self.assertRaisesRegex(AssertionError, 'zmienione'):
            check_baseline(registry, groups, version='105.00.0')


class V105ClassEquipmentProfileTest(unittest.TestCase):
    def test_all_88_new_class_items_have_three_real_attributes(self):
        from world.v10500_equipment import install
        from core.classes_skills import CLASSES
        from world.v10500_region_index import REGIONS
        from world.v10400_equipment_5001 import SLOTS
        items = {'steel_ingot': {'type':'craft_material'}}
        for slug, *_ in REGIONS:
            items[f'v10500_{slug}_alloy'] = {'type':'craft_material'}
            items[f'v10500_{slug}_material_3'] = {'type':'craft_material'}
        recipes, bonuses = {}, {}
        result = install(items, recipes, bonuses)
        self.assertEqual(result['sets'], 34)
        self.assertEqual(result['items'], 136)
        for index,(klass,kind,*_) in enumerate(CLASSES,1):
            primary = 'intelligence' if kind=='magic' else (
                'dexterity' if klass in ('Łotrzyk','Łowca','Mnich','Mec','Inżynier')
                else 'strength')
            secondary = 'willpower' if kind=='magic' else 'strength' if primary=='dexterity' else 'dexterity'
            for slot,_ in SLOTS:
                item = items[f'v10500_class_{index:02d}_{slot}']
                present = {item['affix'], *item['stats']}
                self.assertTrue({primary, secondary, 'constitution'} <= present,
                                (klass, slot, present))
                self.assertGreater(item['stats'][secondary],0)
                self.assertGreater(item['stats']['constitution'],0)


class AstalTrialCompatTest(unittest.TestCase):
    def test_real_67_dynamic_astral_targets_and_strict_rejection(self):
        from validation.test_v10400_legacy_audit_compat import sample
        from validation.v10400_legacy_audit_compat import accepted_legacy_reports, NAMES
        from core.progression_600 import SOUL_TRIAL_QUEST_IDS
        from world.dynamic_content import QUESTS
        from systems.dungeons_regions import is_astral_boss_floor
        extras = []
        for tier in range(1010, 3001, 10):
            qid = SOUL_TRIAL_QUEST_IDS[tier]
            target = QUESTS[qid]['target']
            if target.startswith('astral_boss_'):
                self.assertTrue(is_astral_boss_floor(int(target.removeprefix('astral_boss_'))))
                extras.append(('quest_bad_kill_target', qid, target))
        self.assertEqual(len(extras), 67)
        namespace = sample()
        report = namespace['FULL_GAME_AUDIT_V03014']
        report['errors'].extend(f'quest mob target missing {qid}:{target}' for _, qid, target in extras)
        report['error_count'] = len(report['errors'])
        namespace['FULL_GAME_PREDEPLOY_AUDIT_V0336'] = {'errors': list(extras), 'error_count': len(extras)}
        self.assertEqual(accepted_legacy_reports(namespace, version='105.00.0'), frozenset((*NAMES, 'FULL_GAME_PREDEPLOY_AUDIT_V0336')))
        report['errors'][-1] = 'quest mob target missing '+extras[-1][1]+':astral_boss_999999'
        with self.assertRaisesRegex(AssertionError, 'unexpected legacy findings'):
            accepted_legacy_reports(namespace, version='105.00.0')
        with self.assertRaises(AssertionError):
            accepted_legacy_reports(namespace, version='104.00.3')


if __name__ == '__main__':
    unittest.main()
