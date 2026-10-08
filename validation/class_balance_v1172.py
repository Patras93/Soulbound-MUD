"""v1.17.2: regression checks for all playable classes and materialized class EQ.

Read-only catalog checks; no changes to live player state, combat damage or loot.
"""

from __future__ import annotations

from collections import Counter

from core.classes_skills import CLASSES, CLASS_SKILLS, effective_skill_mana_cost

OFFENSIVE = frozenset({'damage', 'aoe_damage', 'execute', 'drain'})
STAT_KEYS = frozenset({'strength', 'dexterity', 'constitution', 'intelligence', 'willpower'})
STAGES = (1, 100, 200, 400, 600)


def audit_class_skill_balance_v1172():
    errors, report, checks = [], {}, 0
    roster = {row[0] for row in CLASSES}
    if len(roster) != 14 or set(CLASS_SKILLS) != roster:
        errors.append('class roster mismatch')
    for class_name in sorted(roster):
        rows = CLASS_SKILLS.get(class_name, ())
        counter = Counter(str(s.get('kind') or '') for s in rows)
        offensive = [s for s in rows if s.get('kind') in OFFENSIVE]
        late = [s for s in offensive if int(s.get('unlock', 0) or 0) >= 400]
        ids = [str(s.get('id') or '') for s in rows]
        checks += 4
        if not rows or not offensive or not late:
            errors.append(f'{class_name}: incomplete active/endgame skills')
        if len(ids) != len(set(ids)):
            errors.append(f'{class_name}: duplicate skill IDs')
        if any(int(s.get('unlock', 0) or 0) > 600 for s in rows):
            errors.append(f'{class_name}: skill unlock exceeds mastery 600')
        if any(int(effective_skill_mana_cost(s, class_name)) < 0 for s in rows):
            errors.append(f'{class_name}: negative mana cost')
        report[class_name] = {
            'total': len(rows), 'offensive': len(offensive),
            'endgame_400_plus': len(late), 'heals': counter['heal'] + counter['group_heal'],
            'buffs': counter['boost'] + counter['guard'],
        }
    return {'version': '1.17.2', 'checks': checks, 'skills': sum(len(v) for v in CLASS_SKILLS.values()),
            'classes': len(roster), 'per_class': report,
            'errors': errors, 'error_count': len(errors)}


def audit_class_equipment_balance_v1172(items, catalog, tech_set_ids):
    """Inspect post-Generator ITEMS, rather than early recipe templates."""
    errors, checks, report = [], 0, {}
    roster = {row[0] for row in CLASSES}
    for class_name in sorted(roster):
        class_report = {}
        previous = -1
        for stage in STAGES:
            ids = catalog.get(class_name, {}).get(stage, ())
            # Compare all three styles of the same slot. Their distributions
            # differ intentionally, but every one must have the proper axes.
            hand_items = [items[iid] for iid in ids if iid in items and items[iid].get('slot') == 'hands']
            checks += 1
            if len(hand_items) < 3:
                errors.append(f'{class_name} {stage}: missing shop style(s)')
                continue
            style_signatures = set()
            stage_budgets = []
            for item in hand_items:
                checks += 1
                stats = {key: int(val) for key, val in (item.get('stats') or {}).items()}
                affix = str(item.get('affix') or '')
                stats[affix] = stats.get(affix, 0) + int(item.get('affix_amount', 0) or 0)
                expected = STAT_KEYS if class_name == 'Mec' else (
                    frozenset({'intelligence', 'willpower', 'constitution'})
                    if next(r for r in CLASSES if r[0] == class_name)[1] == 'magic'
                    else frozenset({'strength', 'dexterity', 'constitution'})
                )
                if any(stats.get(key, 0) <= 0 for key in expected):
                    errors.append(f'{class_name} {stage}: missing/zero class stat on {item.get("name")}')
                if int(item.get('required_mastery', -1)) != stage:
                    errors.append(f'{class_name} {stage}: incorrect mastery requirement')
                if item.get('required_class') != class_name:
                    errors.append(f'{class_name} {stage}: incorrect required class')
                if class_name == 'Mec' and (
                    int(item.get('attack', 0) or 0) <= 0 or int(item.get('magic_attack', 0) or 0) <= 0
                ):
                    errors.append(f'Mec {stage}: missing physical/magic channel')
                # Compare only the shared three-stat base. Mec's extra axes
                # should not make its basic scaling compare falsely unequal.
                primary_keys = (
                    ('strength','dexterity','constitution') if class_name != 'Mec' and
                    next(r for r in CLASSES if r[0] == class_name)[1] == 'physical'
                    else ('intelligence','willpower','constitution') if class_name != 'Mec'
                    else ('strength','dexterity','constitution')
                )
                budget = sum(stats.get(key, 0) for key in primary_keys)
                stage_budgets.append(budget)
                style_signatures.add((
                    int(item.get('defense', 0) or 0),
                    int(item.get('attack', 0) or 0),
                    int(item.get('magic_attack', 0) or 0),
                    tuple(sorted(stats.items())),
                ))
            checks += 2
            if len(style_signatures) < 3:
                errors.append(f'{class_name} {stage}: shop styles collapsed to same power')
            if min(stage_budgets) <= previous:
                errors.append(f'{class_name} {stage}: class EQ stat power did not grow')
            previous = min(stage_budgets)
            class_report[stage] = {'base_min': min(stage_budgets), 'base_max': max(stage_budgets)}
        report[class_name] = class_report
    # The special Mec Tech Set is not shop class equipment and must keep 5 stats.
    for iid in tech_set_ids.get('tech_mec', ()):
        checks += 1
        item = items.get(iid) or {}
        if any(int((item.get('stats') or {}).get(stat, 0) or 0) <= 0 for stat in STAT_KEYS):
            errors.append(f'Tech Mec missing five-stat profile: {iid}')
    return {'version': '1.17.2', 'checks': checks, 'classes': len(roster),
            'per_class': report, 'errors': errors, 'error_count': len(errors)}
