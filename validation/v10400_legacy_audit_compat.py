# -*- coding: utf-8 -*-
"""Reconcile ONLY exact known v104 endgame differences in old 800-cap reports.

Never alters legacy audit results, their code/AST, or runtime catalogues.
Unexpected/partial findings remain fatal to PREDEPLOY.  Used exclusively by
predeploy_full.py after all original reports were executed.
"""
from __future__ import annotations
from collections import Counter


NAMES = (
    'FULL_GAME_AUDIT_V03014',
    'PROGRESSION_COMBAT_AUDIT_V03017',
    'V03014_SKILL_NAME_AUDIT',
    'GENERATOR_NUMERIC_ONLY_AUDIT_V03018',
    'PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360',
    'FULL_RELEASE_INTEGRITY_AUDIT_V03022',
    'FULL_RELEASE_INTEGRITY_AUDIT_V03025',
)


def accepted_legacy_reports(ns, *, version="104.00.3"):
    """Return narrow eligible advisories or raise on even one mismatch."""
    from core.classes_skills import CLASSES
    from core.class_skills_v10400 import NAMES as authored_names, is_authored_endgame_unlock_v104
    from core.progression_600 import SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS

    class_names = [entry[0] for entry in CLASSES]
    if len(class_names) != 22 or len(set(class_names)) != 22 or set(class_names) != set(authored_names):
        raise AssertionError('v104 audit: invalid 22-class identity')
    # v105 extends the catalogue. Keep auditing the immutable v104 prefix
    # rather than rejecting newer, fully backward-compatible Tier entries.
    if (SOUL_MAX_TIER not in (1000, 3000) or
        len(SOUL_TIER_THRESHOLDS) != SOUL_MAX_TIER or
        (SOUL_TIER_THRESHOLDS[499], SOUL_TIER_THRESHOLDS[500], SOUL_TIER_THRESHOLDS[999])
        != (5000, 5010, 10000) or
        (SOUL_MAX_TIER == 3000 and SOUL_TIER_THRESHOLDS[-1] != 30000)):
        raise AssertionError('v104 audit: historical 501-1000 tiers changed or v105 invalid')
    all_skills = ns['CLASS_SKILLS']
    if set(all_skills) != set(class_names):
        raise AssertionError('v104 audit: missing or added class')
    high = []
    for idx, name in enumerate(class_names, 1):
        rows = all_skills[name]
        ids = [row.get('id') for row in rows]
        if len(ids) != len(set(ids)) or len(rows) < 243:
            raise AssertionError('v104 audit: duplicate or missing old class skills: '+name)
        selected = [row for row in rows if str(row.get('id', '')).startswith('v10400_skill_')]
        expected_ids = {f'v10400_skill_{idx:02d}_{j}' for j in (1, 2, 3)}
        if len(selected) != 3 or {s['id'] for s in selected} != expected_ids:
            raise AssertionError('v104 audit: skill IDs differ: '+name)
        for j in (1, 2, 3):
            row = next(x for x in selected if x['id'] == f'v10400_skill_{idx:02d}_{j}')
            if not is_authored_endgame_unlock_v104(row, name) or row['name'] != authored_names[name][j-1] or (
                row.get('kind') != ('damage', 'aoe_damage', 'boost')[j-1]
            ):
                raise AssertionError('v104 audit: altered endgame skill: '+name)
            high.append((name, row))
        # The 800-level legacy catalogue remains bound to its historical cap.
        if any(not (type(x.get('unlock')) is int and 1 <= x['unlock'] <= 800)
               for x in rows if x not in selected):
            raise AssertionError('v104 audit: older skill was unlocked above 800: '+name)
    if len(high) != 66:
        raise AssertionError('v104 audit: expected exactly 66 high skills')

    expected = {}
    expected['FULL_GAME_AUDIT_V03014'] = ['skill unlock '+r['id'] for _, r in high]
    # The frozen v0.30.14 validator only sees static MOB_TEMPLATES, while
    # the v105 Astral Tower creates 10k+ bosses lazily on first floor entry.
    # Admit precisely the real milestone/target pairs, not arbitrary unknown
    # quest targets; validate them against the genuine infinite-floor rule.
    from validation.release_contracts import parse_version
    if parse_version(version) >= (105, 0, 0):
        from core.progression_600 import SOUL_TRIAL_QUEST_IDS, SOUL_TIER_THRESHOLDS
        from world.dynamic_content import QUESTS
        from systems.dungeons_regions import is_astral_boss_floor
        astral_advisories = []
        for tier in range(1010, 3001, 10):
            qid = SOUL_TRIAL_QUEST_IDS[tier]
            quest = QUESTS.get(qid)
            if not isinstance(quest, dict):
                raise AssertionError('v105 trial missing: '+str(qid))
            target = str(quest.get('target') or '')
            if target.startswith('astral_boss_'):
                floor = SOUL_TIER_THRESHOLDS[tier - 1]
                if (target != f'astral_boss_{floor}' or
                    not is_astral_boss_floor(floor) or
                    quest.get('kind') != 'kill' or
                    quest.get('unlocks_soul_tier') != tier or
                    quest.get('required_soul_level') != floor):
                    raise AssertionError('v105 invalid dynamic Astral Trial '+qid)
                astral_advisories.append(('quest_bad_kill_target', qid, target))
        if len(astral_advisories) != 67:
            raise AssertionError('v105 Astral Trials changed: '+str(len(astral_advisories)))
        expected['FULL_GAME_AUDIT_V03014'].extend(
            f'quest mob target missing {qid}:{target}' for _, qid, target in astral_advisories
        )
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'] = astral_advisories
    expected['V03014_SKILL_NAME_AUDIT'] = [
        f'{c}/{r["name"]}: unlock poza zakresem: {r["unlock"]}' for c,r in high
    ]
    expected['PROGRESSION_COMBAT_AUDIT_V03017'] = [
        (f'{c}/{r["id"]}: '+
         (f'nieprawidłowy próg {r["unlock"]}' if c in ('Mec','Inżynier')
          else f'próg {r["unlock"]} poza siatką')) for c,r in high
    ]
    expected['GENERATOR_NUMERIC_ONLY_AUDIT_V03018'] = [
        ('skill unlock range changed: ' if name in ('Mec','Inżynier')
         else 'skill unlock grid changed: ') + name for name in class_names
    ]
    # Original v0.36.0 gate printed only the first ten classes. We demand
    # exactly those expected, not a generic old-grid exemption.
    grid_summary = [
        f'{name}:{len(all_skills[name])}:{min(x["unlock"] for x in all_skills[name])}'
        f'-{max(x["unlock"] for x in all_skills[name])}' for name in class_names
    ]
    expected['PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360'] = [
        'soul_tiers_80: FAIL', 'skill_grid_243_per_class: '+str(grid_summary[:10])
    ]
    expected['FULL_RELEASE_INTEGRITY_AUDIT_V03022'] = [
        f'{name}: {str(expected[name][:3])}' for name in (
            'FULL_GAME_AUDIT_V03014', 'PROGRESSION_COMBAT_AUDIT_V03017',
            'GENERATOR_NUMERIC_ONLY_AUDIT_V03018')
    ]
    expected['FULL_RELEASE_INTEGRITY_AUDIT_V03025'] = ['v0.30.22 release gate regressed']
    allowed = set()
    required_names = NAMES + (('FULL_GAME_PREDEPLOY_AUDIT_V0336',) if parse_version(version) >= (105, 0, 0) else ())
    for name in required_names:
        report = ns.get(name)
        if not isinstance(report,dict):
            raise AssertionError(f'v104 audit: missing historical report {name}')
        errors = report.get('errors')
        expected_errors = expected[name]
        if (not isinstance(errors,(list,tuple)) or
            int(report.get('error_count', -1)) != len(errors) or
            Counter(errors) != Counter(expected_errors)):
            raise AssertionError(f'v104 audit: unexpected legacy findings in {name}: '
                                 f'{repr(errors)[:400]}')
        allowed.add(name)
    return frozenset(allowed)
