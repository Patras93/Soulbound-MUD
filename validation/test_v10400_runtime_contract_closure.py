# -*- coding: utf-8 -*-
"""v104: strict checks for the audited endgame content; offline, no sockets/DB."""
from __future__ import annotations
import unittest
from core.class_skills_v10400 import install as install_skills, is_authored_endgame_unlock_v104
from core.catalog_validation import validate_catalog
from core.classes_skills import CLASSES
from world.v10400_equipment_5001 import install as install_eq, expected_ids
from world.v10400_krainy_5001_10000 import REGIONS


class EndgameSkillSafety(unittest.TestCase):
    def test_all_66_new_skills_class_bound_and_exact(self):
        catalog = {row[0]: [] for row in CLASSES}
        self.assertEqual(install_skills(catalog, CLASSES), 66)
        self.assertEqual(install_skills(catalog, CLASSES), 0)
        self.assertEqual(validate_catalog({'CLASS_SKILLS': catalog})['error_count'], 0)
        for klass, rows in catalog.items():
            self.assertEqual(len(rows), 3)
            for skill in rows:
                self.assertTrue(is_authored_endgame_unlock_v104(skill, klass))

    def test_rejects_rogue_high_level_and_class_swap(self):
        originals = {row[0]: [] for row in CLASSES}
        install_skills(originals, CLASSES)
        first = originals[CLASSES[0][0]][0]
        self.assertFalse(is_authored_endgame_unlock_v104(first, CLASSES[1][0]))
        for rogue in (
            {'id': 'old_legacy_skill', 'unlock': 5200},
            {'id': first['id'], 'unlock': 999999},
            {'id': 'v10400_skill_99_1', 'unlock': 5200},
            {'id': first['id'], 'unlock': 5200.0},
            {'id': first['id'], 'unlock': True},
        ):
            self.assertFalse(is_authored_endgame_unlock_v104(rogue, CLASSES[0][0]))
        originals[CLASSES[0][0]].append({'id':'bad_high_id', 'unlock':9200})
        report = validate_catalog({'CLASS_SKILLS': originals})
        self.assertTrue(any('bad_high_id' in error for error in report['errors']))


class EndgameEquipmentSafety(unittest.TestCase):
    def setUp(self):
        self.items = {'steel_ingot': {'name': 'Sztabka stali', 'type': 'craft_material'}}
        for slug, *_ in REGIONS:
            for suffix in ('alloy', 'material_3'):
                iid = f'v10400_{slug}_{suffix}'
                self.items[iid] = {'name': iid, 'type': 'craft_material'}
        self.recipes = {}
        self.bonuses = {}

    def test_128_items_authored_names_and_stats(self):
        result = install_eq(self.items, self.recipes, self.bonuses)
        self.assertEqual(result['items'], len(expected_ids()))
        self.assertEqual(result['recipes'], len(expected_ids()))
        names = []
        class_armor = 0
        for index, (class_name, klass_type, *_) in enumerate(CLASSES, 1):
            for slot in ('head', 'body', 'hands', 'feet'):
                item = self.items[f'v10400_class_{index:02d}_{slot}']
                names.append(item['name'].casefold())
                class_armor += 1
                self.assertEqual(item['required_class'], class_name)
                self.assertIn('Dziedzictwa:', item['name'])
                present = set(item['stats']) | {item['affix']}
                if klass_type == 'magic':
                    self.assertTrue({'intelligence','willpower','constitution'} <= present)
                else:
                    self.assertTrue({'strength','dexterity','constitution'} <= present)
        self.assertEqual(class_armor, 88)
        self.assertEqual(len(set(names)), len(names))
        self.assertEqual(install_eq(self.items, self.recipes, self.bonuses)['items'], 0)

    def test_missing_alloy_cannot_half_install(self):
        self.items.pop(f'v10400_{REGIONS[0][0]}_alloy')
        before = dict(self.items)
        with self.assertRaises(RuntimeError):
            install_eq(self.items, self.recipes, self.bonuses)
        self.assertEqual(self.items, before)
        self.assertFalse(self.recipes)
        self.assertFalse(self.bonuses)


if __name__ == '__main__':
    unittest.main()
