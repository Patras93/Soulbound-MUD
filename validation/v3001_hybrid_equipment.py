# -*- coding: utf-8 -*-
"""v7.10.1: physical and magic class EQ are separate; Mec is hybrid."""
from systems.equipment_multiclass_v3001 import crossover_bonus_v3001, crossover_text_v3001


def run_regression():
    checks = 0
    def check(ok, message):
        nonlocal checks
        assert ok, message
        checks += 1

    physical = {'type':'armor','slot':'body','required_class':'Wojownik',
                'stats':{'strength':100,'dexterity':50},'attack':60,'defense':20}
    magical = {'type':'armor','slot':'body','required_class':'Mag',
               'stats':{'intelligence':90,'willpower':60},'magic_attack':50,'defense':20}
    mec = {'type':'armor','slot':'body','required_class':'Mec',
           'stats':{'strength':80,'dexterity':80,'constitution':80,'intelligence':40,'willpower':40},
           'attack':50,'magic_attack':50}
    for item in (physical, magical, mec, {'type':'tool'}, {}):
        check(crossover_bonus_v3001(item) == ({}, {}), 'no extra cross-class bonuses')
        check(crossover_text_v3001(item) == '', 'no obsolete NVDA crossover text')
    check(physical['stats'] == {'strength':100,'dexterity':50}, 'original physical stats preserved')
    check(magical['stats'] == {'intelligence':90,'willpower':60}, 'original magic stats preserved')
    check(all(mec['stats'].get(s,0) > 0 for s in
              ('strength','dexterity','constitution','intelligence','willpower')), 'Mec 5 stats')
    check(mec['attack'] > 0 and mec['magic_attack'] > 0, 'Mec both power channels')
    from systems.equipment_crafting import (
        class_equipment_base_stat_triplet, class_equipment_flat_power_channels,
        mec_hybrid_extra_stats,
    )
    from core.classes_skills import CLASSES
    for class_name, klass_type, *_ in CLASSES:
        stat_triplet = class_equipment_base_stat_triplet(class_name)
        power = class_equipment_flat_power_channels(class_name, 100, 'hands')
        if class_name == 'Mec':
            check(set(stat_triplet) == {'strength','dexterity','constitution'}, 'Mec physical base')
            extra = mec_hybrid_extra_stats(100)
            check(extra.get('intelligence',0)>0 and extra.get('willpower',0)>0, 'Mec magic extra')
            check(power['attack'] > 0 and power['magic_attack'] > 0, 'Mec dual power')
        elif klass_type == 'magic':
            check(set(stat_triplet) == {'intelligence','willpower','constitution'}, f'{class_name} magic triplet')
            check(power['attack'] == 0 and power['magic_attack'] > 0, f'{class_name} magic-only attack')
        else:
            check(set(stat_triplet) == {'strength','dexterity','constitution'}, f'{class_name} physical triplet')
            check(power['magic_attack'] == 0 and power['attack'] > 0, f'{class_name} physical-only attack')

    # The actual class-shop item table is created by server startup; assert
    # authored gear keeps the original stat split when available.
    import sys
    server = sys.modules.get('server')
    items = getattr(server, 'ITEMS', {}) if server else {}
    for class_name in ('Wojownik','Mag','Mec'):
        item = next((it for it in items.values() if it.get('class_shop_item')
                     and it.get('required_class') == class_name), None)
        if item is None:
            continue
        stats = dict(item.get('stats') or {})
        # Shop items store the primary stat in 'affix', not in 'stats'.
        if item.get('affix'):
            stats[str(item['affix'])] = int(item.get('affix_amount',0) or 0)
        channels = (int(item.get('attack',0) or 0), int(item.get('magic_attack',0) or 0))
        if class_name == 'Wojownik':
            check('intelligence' not in stats and 'willpower' not in stats,
                  'real physical shop EQ no forced magic')
            check(channels[1] == 0, 'real warrior no magic power')
        elif class_name == 'Mag':
            check('strength' not in stats and 'dexterity' not in stats,
                  'real magic shop EQ no forced physical')
            check(channels[0] == 0, 'real mage no physical power')
        else:
            check(all(stat in stats for stat in ('strength','dexterity','constitution','intelligence','willpower')),
                  'real Mec full hybrid stats')
            check(all(channel > 0 for channel in channels), 'real Mec two attacks')
    return checks

if __name__ == '__main__':
    print(f'EQ FIZYCZNE / MAGICZNE / MEC v7.10.1: {run_regression()} checks PASS')
