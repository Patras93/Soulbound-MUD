"""Soulbound 1.17.7: no-save race balance/identity regression audit.

Fast mode checks all authored race/class combinations without assembling the world.
Runtime mode also probes Character's real passive methods after server bootstrap.
This is a consistency audit, not a claim of equal DPS in live long fights.
"""
from __future__ import annotations

from core.classes_skills import (
    RACES, CLASSES, RACE_CLASS_RECOMMENDATIONS,
    class_starting_stats_for, starting_hp_mana_for,
)
from core.character_resources import (
    AUTHORED_RACE_PASSIVE_PROFILES, race_passive_profile,
    race_passive_text_pl, character_hp_base, character_mana_base,
)

# Anchored values from existing designed race descriptions (no balance nerfs).
EXPECTED = {
    "Człowiek": ("stat_xp", .10), "Ogr": ("physical_damage", .12),
    "Elf": ("dodge", .05), "Krasnolud": ("damage_reduction", .10),
    "Ork": ("max_hp", .10), "Niziołek": ("profession_bonus", .03),
    "Mroczny Elf": ("magic_damage", .10), "Gnom": ("max_mana", .15),
    "Smok": ("all_damage", .08), "Troll": ("physical_reduction", .12),
    "Diablę": ("soul_xp", .10), "Aasimar": ("magic_defense", .12),
    "Driada": ("healing", .15), "Cyborg": ("damage_reduction", .10),
}
from systems.new_heroes_v900 import NEW_RACES
EXPECTED.update({name:(kind,value) for name,desc,s,d,c,i,w,kind,value in NEW_RACES})
PASSIVE_METHODS = {
    "stat_xp": ("racial_stat_progress_multiplier", 1),
    "physical_damage": ("racial_physical_damage_multiplier", 1),
    "dodge": ("racial_dodge_bonus", 0),
    "damage_reduction": ("racial_damage_reduction_percent", 100),
    "max_hp": ("racial_max_hp_multiplier", 1),
    "profession_bonus": ("racial_profession_bonus_chance", 0),
    "magic_damage": ("racial_magic_damage_multiplier", 1),
    "max_mana": ("racial_max_mana_multiplier", 1),
    "all_damage": ("racial_all_damage_multiplier", 1),
    "physical_reduction": ("racial_physical_damage_reduction_percent", 100),
    "soul_xp": ("racial_soul_xp_multiplier", 1),
    "magic_defense": ("racial_magic_defense_multiplier", 1),
    "healing": ("racial_healing_multiplier", 1),
}


def audit_race_balance_v1177(*, runtime=False):
    # Fast predeploy imports historical 22-class audits *before* the server
    # extends the catalogue. Resolve canonical live lists at invocation time,
    # not the pre-bootstrap snapshots captured by this module's import.
    from core.classes_skills import (RACES as RACES, CLASSES as CLASSES,
                                     RACE_CLASS_RECOMMENDATIONS as RACE_CLASS_RECOMMENDATIONS)
    checks, errors = 0, []
    def check(ok, description):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(description)

    race_names = [r[0] for r in RACES]
    from systems.admin_live_races_v7600 import current as custom_races
    from core.archetypes.chaos import (RACE_SPECS as V107_RACES,
                                            CLASS_SPECS as V107_CLASSES)
    from core.archetypes.expansion import (RACE_SPECS as V110_RACES,
                                       CLASS_SPECS as V110_CLASSES)
    custom=custom_races()
    class_names = [c[0] for c in CLASSES]
    # Anchored v1.17 races are immutable. v107/v110 add strictly independent
    # full packs, each with 8 races and 8 classes; partial installs FAIL.
    v107_race_names={r[0] for r in V107_RACES}
    v110_race_names={r[0] for r in V110_RACES}
    v107_class_names={c[0] for c in V107_CLASSES}
    v110_class_names={c[0] for c in V110_CLASSES}
    active_v107 = bool(v107_race_names & set(race_names))
    active_v110 = bool(v110_race_names & set(race_names))
    profile_expected=dict(EXPECTED)
    if active_v107:
        profile_expected.update({n:(kind,val) for n,kind,val,*_ in V107_RACES})
    if active_v110:
        profile_expected.update({n:(kind,val) for n,kind,val,*_ in V110_RACES})
    expected_names=set(profile_expected)|set(custom)
    check(len(RACES) == 22+len(custom)+8*active_v107+8*active_v110
          and len(set(race_names)) == len(RACES), 'races: 22 historical plus complete 8-race packs')
    check(len(CLASSES) == 22+8*active_v107+8*active_v110
          and len(set(class_names)) == len(CLASSES), 'classes: 22 historical plus complete 8-class packs')
    check(not active_v107 or v107_class_names <= set(class_names), 'incomplete v107 classes')
    check(not active_v110 or v110_class_names <= set(class_names), 'incomplete v110 classes')
    check(set(race_names) == expected_names, 'race names differ from anchored baseline plus registered packs')
    check(set(AUTHORED_RACE_PASSIVE_PROFILES) == expected_names | {'Smoczy'}, 'race passive profile roster drift')
    check(race_passive_profile('Smoczy') == race_passive_profile('Smok'), 'legacy Smoczy no longer matches Smok')
    check(set(RACE_CLASS_RECOMMENDATIONS) == set(race_names), 'race recommendations are incomplete')

    for race in RACES:
        name = race[0]
        check(sum(race[2:]) == 50, f'{name}: race stat budget no longer 50')
        kind, value = EXPECTED[custom[name]['parent']] if name in custom else profile_expected[name]
        row = race_passive_profile(name)
        check(row == {'kind': kind, 'value': value}, f'{name}: race passive diverges from described profile')
        check('brak' not in race_passive_text_pl(name).lower(), f'{name}: missing passive text')
        for recommended in RACE_CLASS_RECOMMENDATIONS.get(name, {}).get('classes', []):
            check(recommended in class_names, f'{name}: nonexistent recommended class {recommended}')
        for clazz in CLASSES:
            stats = class_starting_stats_for(race, clazz)
            # Seven v107 Chaos classes had an authored 8-point bonus.
            # Preserve that historical live balance; new v110 classes use 9.
            budget = 68 if clazz[0] in v107_class_names else 69
            check(sum(stats.values()) == budget,
                  f'{name}/{clazz[0]}: starting budget {sum(stats.values())} != {budget}')
            check(all(v > 0 for v in stats.values()), f'{name}/{clazz[0]}: non-positive starting stat')
            hp, mana = starting_hp_mana_for(race, clazz)
            base_hp = character_hp_base(1, stats['constitution'])
            base_mana = character_mana_base(1, stats['intelligence'], stats['willpower'])
            check(hp == round(base_hp * (1.0 + (value if kind == 'max_hp' else 0))),
                  f'{name}/{clazz[0]}: initial HP passive incorrect')
            check(mana == round(base_mana * (1.0 + (value if kind == 'max_mana' else 0))),
                  f'{name}/{clazz[0]}: initial Mana passive incorrect')

    if runtime:
        from player.character import Character
        for name in race_names + ['Smoczy']:
            kind, val = EXPECTED[custom[name]['parent']] if name in custom else profile_expected['Smok' if name == 'Smoczy' else name]
            ch = object.__new__(Character)
            ch.race = name
            check(ch._generated_race_passive() == race_passive_profile(name), f'{name}: runtime passive profile mismatch')
            check(ch.racial_passive_text() == race_passive_text_pl(name), f'{name}: runtime passive description mismatch')
            for passive, (method, bias) in PASSIVE_METHODS.items():
                expected_value = val if passive == kind else 0
                if bias == 100:
                    expected_value = int(round(100 * expected_value))
                elif bias == 1:
                    expected_value += 1.0
                observed = getattr(ch, method)()
                check(abs(observed - expected_value) < 1e-9,
                      f'{name}: {method} expected {expected_value}, got {observed}')
            for raw in (1, 500, 10000, 10000000):
                result, prevented = ch.apply_racial_damage_reduction(raw)
                reduction = ch.racial_damage_reduction_percent()
                expected_result = max(1, round(raw * (1 - reduction / 100)))
                check(result == expected_result and result + prevented == raw,
                      f'{name}: actual damage reduction mismatch for {raw}')

    return {'races': len(RACES), 'classes': len(CLASSES), 'combos': len(RACES)*len(CLASSES),
            'checks': checks, 'errors': errors, 'error_count': len(errors), 'runtime': runtime}
