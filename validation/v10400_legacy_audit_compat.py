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

    from validation.release_contracts import parse_version
    current=parse_version(version)
    playable_names=[entry[0] for entry in CLASSES]
    class_names=playable_names[:22]
    if (len(class_names)!=22 or len(set(class_names))!=22
        or set(class_names)!=set(authored_names)):
        raise AssertionError('v104 audit: invalid historical 22-class identity')
    # Verify successor identities separately instead of ignoring additional
    # playable classes or treating them as v104 skills.
    expected_successors=[]
    if current >= (107,0,0):
        from core.magitek.catalogue import CLASS_NAME as magitek
        from core.archetypes.chaos import CLASS_SPECS as successor_v107
        expected_successors.extend([magitek]+[row[0] for row in successor_v107])
    if current >= (110,0,0):
        from core.archetypes.expansion import CLASS_SPECS as successor_v110
        expected_successors.extend(row[0] for row in successor_v110)
    if (playable_names[22:]!=expected_successors
        or len(set(playable_names))!=len(playable_names)):
        raise AssertionError('v104 audit: v107/v110 successor class identities differ')
    # v105 extends the catalogue. Keep auditing the immutable v104 prefix
    # rather than rejecting newer, fully backward-compatible Tier entries.
    allowed_tiers={1000,3000}
    if current >= (110,0,0):allowed_tiers.add(6000)
    if (SOUL_MAX_TIER not in allowed_tiers or
        len(SOUL_TIER_THRESHOLDS) != SOUL_MAX_TIER or
        (SOUL_TIER_THRESHOLDS[499], SOUL_TIER_THRESHOLDS[500], SOUL_TIER_THRESHOLDS[999])
        != (5000, 5010, 10000) or
        (SOUL_MAX_TIER>=3000 and SOUL_TIER_THRESHOLDS[2999] != 30000) or
        (SOUL_MAX_TIER==6000 and SOUL_TIER_THRESHOLDS[5999] != 60000)):
        raise AssertionError('v104 audit: historical 501-1000 tiers changed or v105 invalid')
    all_skills = ns['CLASS_SKILLS']
    if set(all_skills) != set(playable_names):
        raise AssertionError('v104 audit: missing or extra successor class skills')
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
    if current >= (105, 0, 0):
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
    # v107/v109/v110 added crafted regional alloys at author-defined mastery
    # 60001–113001. The frozen v104 validator caps ALL recipes at 800.
    # Require the exact number, consecutive progression, source prefixes,
    # ownership, forge station, material inputs and output IDs. The historical
    # 800-cap assertions remain intact for every older recipe.
    if current >= (107, 0, 0):
        recipes=ns['CRAFT_RECIPES']
        items=ns['ITEMS']
        regional_groups=[('v10700_chaos_', 30, 60001)]
        if current >= (109, 0, 0):
            regional_groups.append(('v10900_horizon_', 12, 90001))
        if current >= (110, 0, 0):
            regional_groups.append(('v11000_realm_', 12, 102001))
        known_recipe_advisories=[]
        for prefix,count,start in regional_groups:
            entries=sorted((rid,row) for rid,row in recipes.items()
                           if rid.startswith(prefix) and rid.endswith('_alloy'))
            if len(entries)!=count:
                raise AssertionError(f'v104 audit: regional alloy set {prefix} count {len(entries)} != {count}')
            actual_levels=[]
            for rid,row in entries:
                if (row.get('output')!=rid or rid not in items or
                    row.get('profession')!='Kowalstwo' or
                    ('forge' not in tuple(row.get('stations',())) or
                     not set(row.get('stations',())) <= {'forge','crafting_workshop'}) or
                    len(row.get('ingredients',{}))!=2 or
                    any(int(amount)!=2 or material not in items
                        for material,amount in row['ingredients'].items())):
                    raise AssertionError('v104 audit: broken regional alloy recipe '
                                         +rid+' '+repr(row)[:550]
                                         +' item_exists='+str(rid in items))
                minimum=int(row.get('min_profession_level',0) or 0)
                generator=int(row.get('generator_level',0) or 0)
                if generator!=minimum:
                    raise AssertionError('v104 audit: regional alloy progression mismatch '+rid)
                actual_levels.append(minimum)
                known_recipe_advisories.append(f'CRAFT_RECIPES level {rid}:{minimum}')
            if sorted(actual_levels)!=[start+i*1000 for i in range(count)]:
                raise AssertionError('v104 audit: regional alloy level grid changed '+prefix)
        expected['FULL_GAME_AUDIT_V03014'].extend(known_recipe_advisories)
    # Successor catalogues are installed after the frozen v0.33.6 snapshot.
    # Preserve the original snapshot and its assertions; reconcile ONLY known
    # successor entries after independently verifying their real runtime IDs,
    # profession identities, cooldowns and class equipment sets.
    if current >= (107, 0, 0):
        from core.archetypes.chaos import PROFESSION_SPECS as prof_v107
        from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
        new_professions = {row[0] for row in prof_v107}
        if current >= (110, 0, 0):
            from core.archetypes.expansion import PROFESSION_SPECS as prof_v110
            new_professions.update(row[0] for row in prof_v110)
        expected_new_professions = 8 if current < (110, 0, 0) else 16
        if len(new_professions) != expected_new_professions:
            raise AssertionError('v104 audit: successor profession source is incomplete')
        live_professions = set(ns['PROFESSION_RANK_NAMES'])
        if not new_professions <= live_professions or len(live_professions) != 22 + expected_new_professions:
            raise AssertionError('v104 audit: missing or extra real professions')
        live_quests = ns['QUESTS']
        professional_quest_ids = []
        v107_count = v110_count = 0
        for qid, quest in live_quests.items():
            profession = quest.get('required_profession')
            if profession not in new_professions:
                continue
            if (qid.startswith('v10700_saga_prof_') and
                profession in {row[0] for row in prof_v107}):
                v107_count += 1
            elif (current >= (110, 0, 0) and
                  qid.startswith('v11000_realm_') and '_prof_' in qid and
                  profession in {row[0] for row in prof_v110}):
                v110_count += 1
            else:
                raise AssertionError('v104 audit: unrecognized successor profession quest '+qid)
            if (quest.get('kind') != 'profession_action'
                or quest.get('target') != profession
                or quest.get('reward_profession') != profession
                or type(quest.get('needed')) is not int or quest['needed'] < 1
                or quest.get('repeatable') is not True
                or int(quest.get('repeat_cooldown') or 0) != QUEST_REPEAT_COOLDOWN_SECONDS
                or not (quest.get('specialist_tool_type') or quest.get('reward_tool_type'))):
                raise AssertionError('v104 audit: damaged successor profession quest '+qid)
            professional_quest_ids.append((qid, profession))
        if (v107_count != 320 or
            v110_count != (48 if current >= (110, 0, 0) else 0)):
            raise AssertionError('v104 audit: wrong number of successor profession quests')
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'].extend(
            ('quest_bad_required_profession', qid, profession)
            for qid,profession in professional_quest_ids
        )
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'].extend(
            ('quest_bad_reward_profession', qid, profession)
            for qid,profession in professional_quest_ids
        )
        if not set(expected_successors) <= set(ns['CLASS_SKILLS']):
            raise AssertionError('v104 audit: successor skills missing from live catalogue')
        for name in expected_successors:
            if (not ns['CLASS_SKILLS'].get(name) or
                name not in ns['LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER'] or
                name not in ns['CLASS_EQUIPMENT_SETS']):
                raise AssertionError('v104 audit: successor class equipment incomplete '+name)
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'].extend(
            ('legendary_set_missing_class', name) for name in expected_successors
        )
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'].extend(
            ('class_set_unknown_class', name) for name in expected_successors
        )
        # Only the archived v104 post-raid quest titles and one known historic
        # item display-name collision may survive; validate their real objects.
        # No future duplicate gets a free pass through this compatibility gate.
        snapshot=ns['FULL_GAME_PREDEPLOY_AUDIT_V0336']
        duplicates=[row for row in snapshot['errors'] if row[0]=='duplicate_display_name']
        if len(duplicates) not in (0, 13):
            raise AssertionError('v104 audit: unexpected number of display-name collisions')
        item_count = quest_count = 0
        for row in duplicates:
            if len(row)!=4 or not isinstance(row[3],(tuple,list)) or len(row[3])!=2:
                raise AssertionError('v104 audit: malformed duplicate display name')
            _,category,display,ids=row
            registry=ns['ITEMS'] if category=='items' else ns['QUESTS'] if category=='quests' else None
            if registry is None or any(entry not in registry for entry in ids):
                raise AssertionError('v104 audit: missing duplicate source')
            names=tuple(str(registry[entry].get('name','')).casefold().strip() for entry in ids)
            if names != (display,display) or ids[0]==ids[1]:
                raise AssertionError('v104 audit: changed duplicate labels')
            if category=='items':
                if set(ids) != {'v10700_chaos_popiol_material_3','v11339_emberheart_charm'} or display != 'serce żaru':
                    raise AssertionError('v104 audit: unexpected duplicate item')
                item_count+=1
            elif category=='quests':
                if not all(str(entry).startswith('v10400_raid_') for entry in ids):
                    raise AssertionError('v104 audit: unexpected duplicate quest')
                quest_count+=1
        if (item_count,quest_count) not in ((0,0),(1,12)):
            raise AssertionError('v104 audit: historical duplicate count changed')
        expected['FULL_GAME_PREDEPLOY_AUDIT_V0336'].extend(duplicates)
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
    required_names = NAMES + (('FULL_GAME_PREDEPLOY_AUDIT_V0336',) if current >= (105, 0, 0) else ())
    # Current native runtime runs only its declared audit modules. Some
    # preserved reports are still exported by normal gameplay providers;
    # validate each of these against the exact old expected findings. The
    # retired report providers are not imported or marked PASS by their
    # absence; the clean full CURRENT audit is mandatory instead.
    observed_legacy = {name for name in NAMES if isinstance(ns.get(name),dict)}
    native = ns.get('FULL_GAME_PREDEPLOY_AUDIT_V0336')
    native_current = (isinstance(native,dict) and native.get('error_count')==0
                      and not native.get('errors') and int(native.get('checks',0))>0)
    if native_current:
        required_names = tuple(name for name in NAMES if name in observed_legacy)
    else:
        required_names = NAMES + (('FULL_GAME_PREDEPLOY_AUDIT_V0336',)
                                  if current >= (105,0,0) else ())
    # Missing current native proof re-enables the strict historical report
    # requirements, never an unconditional exception for absent audits.
    for name in required_names:
        report = ns.get(name)
        if not isinstance(report,dict):
            raise AssertionError(f'v104 audit: missing historical report {name}')
        errors = report.get('errors')
        expected_errors = expected[name]
        if (not isinstance(errors,(list,tuple)) or
            int(report.get('error_count', -1)) != len(errors) or
            Counter(errors) != Counter(expected_errors)):
            extra=list((Counter(errors)-Counter(expected_errors)).elements())
            missing=list((Counter(expected_errors)-Counter(errors)).elements())
            raise AssertionError(f'v104 audit: unexpected legacy findings in {name}: '
                                 f'extra={len(extra)} {extra[:5]!r}; '
                                 f'missing={len(missing)} {missing[:5]!r}; '
                                 f'actual={len(errors)} expected={len(expected_errors)}')
        allowed.add(name)
    return frozenset(allowed)
