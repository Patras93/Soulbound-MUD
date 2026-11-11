# -*- coding: utf-8 -*-
"""Kontrola 66 nowych skilli v104 bez utraty mechanik starszych 5461."""
import unittest
from copy import deepcopy
from core.classes_skills import CLASS_SKILLS
from validation.v10400_skill_catalog_contract import (
    old_and_new_skills, LEGACY_SKILLS, NEW_SKILLS, TOTAL_SKILLS,
)

class SkillCatalogV104(unittest.TestCase):
    def test_all_22_classes_and_three_new_skills_each(self):
        old, new = old_and_new_skills(CLASS_SKILLS)
        self.assertEqual(sum(map(len, old.values())), LEGACY_SKILLS)
        self.assertEqual(sum(map(len, new.values())), NEW_SKILLS)
        self.assertEqual(sum(map(len, CLASS_SKILLS.values())), TOTAL_SKILLS)

    def test_missing_new_skill_rejected(self):
        copy = {key: list(items) for key, items in CLASS_SKILLS.items()}
        key = next(iter(copy))
        copy[key] = copy[key][:-1]
        with self.assertRaises(AssertionError): old_and_new_skills(copy)

    def test_duplicate_new_skill_id_rejected(self):
        copy = {key: [dict(item) for item in items] for key, items in CLASS_SKILLS.items()}
        key = next(iter(copy))
        new = [item for item in copy[key] if str(item['id']).startswith('v10400_skill_')]
        new[1]['id'] = new[0]['id']
        with self.assertRaises(AssertionError): old_and_new_skills(copy)

    def test_legacy_skill_deleted_rejected(self):
        copy = {key: list(items) for key, items in CLASS_SKILLS.items()}
        key = next(iter(copy))
        copy[key] = [s for s in copy[key] if s['id'] != 'warrior_power_slash']
        with self.assertRaises(AssertionError): old_and_new_skills(copy)

if __name__ == '__main__': unittest.main()
