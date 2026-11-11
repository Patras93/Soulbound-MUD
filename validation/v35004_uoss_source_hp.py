# -*- coding: utf-8 -*-
"""Regression: world-wide x2 HP must never override authentic UOSS boss HP."""
from copy import deepcopy


def run():
    from core.bootstrap_economy_professions import GLOBAL_MOB_HP_MULTIPLIER
    from world.economy_quests import apply_global_mob_hp_multiplier
    from world.uoss_superboss_world import SOURCE_SCANNER_V11156
    from data.mobs import MOB_TEMPLATES
    checks = 0
    assert GLOBAL_MOB_HP_MULTIPLIER == 2.0
    checks += 1
    for key, source in SOURCE_SCANNER_V11156.items():
        hp = source.get('max_hp')
        if hp is None:
            continue
        tid = f'uoss_superboss_{key}_v11136'
        boss = MOB_TEMPLATES[tid]
        assert boss['uoss_unique_superboss_key'] == key and boss['uoss_source_hp_exact']
        assert boss['max_hp'] == hp, (key, boss['max_hp'], hp)
        assert boss['base_max_hp'] == hp
        if source.get('xp') is not None:
            assert boss['source_xp'] == source['xp']
            checks += 1
        checks += 3
    sample = {
        'normal': {'max_hp':100, 'name':'Test zwykłego moba'},
        'uoss': {'max_hp':333, 'name':'Test UOSS', 'uoss_unique_superboss_key':'test', 'uoss_source_hp_exact':True},
        'uoss_no_exact_hp': {'max_hp':444, 'name':'UOSS bez podanego HP', 'uoss_unique_superboss_key':'test2', 'uoss_source_hp_exact':False},
    }
    first = deepcopy(sample)
    apply_global_mob_hp_multiplier(sample)
    assert sample['normal']['max_hp'] == first['normal']['max_hp'] * 2
    assert sample['normal']['base_max_hp'] == first['normal']['max_hp']
    assert sample['uoss']['max_hp'] == first['uoss']['max_hp']
    assert sample['uoss']['base_max_hp'] == first['uoss']['max_hp']
    assert sample['uoss_no_exact_hp']['max_hp'] == first['uoss_no_exact_hp']['max_hp'] * 2
    checks += 5
    return checks


if __name__ == '__main__':
    print('UOSS SOURCE HP 35.00.4:',run(),'PASS')
