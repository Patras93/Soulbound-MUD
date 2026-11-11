# -*- coding: utf-8 -*-
"""Adversarial compatibility checks: old audit findings may not be hidden."""
from __future__ import annotations
import unittest
from copy import deepcopy
from core.classes_skills import CLASS_SKILLS, CLASSES
from core.class_skills_v10400 import NAMES as SKILL_NAMES
from validation.v10400_legacy_audit_compat import accepted_legacy_reports, NAMES


def sample():
    skills = deepcopy(CLASS_SKILLS)
    selected=[]
    for idx, entry in enumerate(CLASSES, 1):
        name=entry[0]
        for j in (1,2,3):
            selected.append((name, next(r for r in skills[name] if r['id']==f'v10400_skill_{idx:02d}_{j}')))
    err={}
    err['FULL_GAME_AUDIT_V03014']=['skill unlock '+r['id'] for _,r in selected]
    err['V03014_SKILL_NAME_AUDIT']=[f'{c}/{r["name"]}: unlock poza zakresem: {r["unlock"]}' for c,r in selected]
    err['PROGRESSION_COMBAT_AUDIT_V03017']=[
        (f'{c}/{r["id"]}: ' + (f'nieprawidłowy próg {r["unlock"]}' if c in ('Mec','Inżynier')
                               else f'próg {r["unlock"]} poza siatką')) for c,r in selected]
    err['GENERATOR_NUMERIC_ONLY_AUDIT_V03018']=[
        ('skill unlock range changed: ' if c in ('Mec','Inżynier') else 'skill unlock grid changed: ')+c
        for c,*_ in CLASSES]
    first_ten=[]
    for c,*_ in CLASSES[:10]:
        unlocks=[r['unlock'] for r in skills[c]]
        first_ten.append(f'{c}:{len(unlocks)}:{min(unlocks)}-{max(unlocks)}')
    err['PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360']=[
        'soul_tiers_80: FAIL', 'skill_grid_243_per_class: '+str(first_ten)]
    err['FULL_RELEASE_INTEGRITY_AUDIT_V03022']=[
        f'{name}: {str(err[name][:3])}' for name in (
            'FULL_GAME_AUDIT_V03014','PROGRESSION_COMBAT_AUDIT_V03017',
            'GENERATOR_NUMERIC_ONLY_AUDIT_V03018')]
    err['FULL_RELEASE_INTEGRITY_AUDIT_V03025']=['v0.30.22 release gate regressed']
    ns={'CLASS_SKILLS':skills}
    ns.update((name,{'error_count':len(errors),'errors':errors}) for name,errors in err.items())
    return ns


class LegacyAuditCompatibilityTest(unittest.TestCase):
    def test_exact_canonical_findings_are_accepted(self):
        ns=sample()
        self.assertEqual(accepted_legacy_reports(ns),frozenset(NAMES))
    def test_one_extra_error_stays_blocking(self):
        ns=sample()
        ns['FULL_GAME_AUDIT_V03014']['errors'].append('Real security issue')
        ns['FULL_GAME_AUDIT_V03014']['error_count']+=1
        with self.assertRaises(AssertionError):accepted_legacy_reports(ns)
    def test_mismatched_report_count_stays_blocking(self):
        ns=sample();ns['PROGRESSION_COMBAT_AUDIT_V03017']['error_count']-=1
        with self.assertRaises(AssertionError):accepted_legacy_reports(ns)
    def test_missing_old_report_stays_blocking(self):
        ns=sample();del ns['FULL_RELEASE_INTEGRITY_AUDIT_V03025']
        with self.assertRaises(AssertionError):accepted_legacy_reports(ns)
    def test_rogue_high_skill_unlock_stays_blocking(self):
        ns=sample();ns['CLASS_SKILLS'][CLASSES[0][0]][0]['unlock']=9999
        with self.assertRaises(AssertionError):accepted_legacy_reports(ns)
    def test_corrupted_author_skill_cannot_be_accepted(self):
        ns=sample()
        name=CLASSES[0][0]
        next(r for r in ns['CLASS_SKILLS'][name] if r['id']=='v10400_skill_01_1')['unlock']=10000
        with self.assertRaises(AssertionError):accepted_legacy_reports(ns)

if __name__=='__main__':unittest.main()
