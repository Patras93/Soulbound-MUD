# -*- coding: utf-8 -*-
"""v104: 10 regional + 22 class four-piece sets via existing equipment system.

This module adds catalog data only. It does not alter player records or older
sets. It deliberately uses existing regional_set counting and equip class checks.
"""
from __future__ import annotations
from core.classes_skills import CLASSES
from world.v10400_krainy_5001_10000 import REGIONS

SLOTS=(('head','Korona'),('body','Pancerz'),('hands','Rękawice'),('feet','Buty'))


def expected_ids():
    names=[f'v10400_set_{slug}_{slot}' for slug,*_ in REGIONS for slot,_ in SLOTS]
    names += [f'v10400_class_{index:02d}_{slot}' for index,_ in enumerate(CLASSES,1) for slot,_ in SLOTS]
    return frozenset(names)


def install(items,recipes,bonuses):
    planned=expected_ids()
    if all(i in items and i in recipes for i in planned):
        if not all(('v10400_'+slug) in bonuses for slug,*_ in REGIONS):
            raise RuntimeError('Niekompletne bonusy zestawów v104')
        return {'sets':0,'items':0,'recipes':0,'reason':'already installed'}
    collisions=planned & (set(items) | set(recipes))
    if collisions:
        raise RuntimeError(f'Kolizja elementu zestawu v104: {sorted(collisions)[0]}')
    if len({c[0] for c in CLASSES})!=len(CLASSES):
        raise RuntimeError('Powtórzone nazwy klas')
    set_ids={f'v10400_{slug}' for slug,*_ in REGIONS} | {f'v10400_class_{n:02d}' for n in range(1,len(CLASSES)+1)}
    if set_ids & set(bonuses):
        raise RuntimeError('Kolizja ID zestawu w tabeli bonusów')
    local_items={};local_recipes={};local_bonuses={}
    for n,(slug,region,low,high,*_) in enumerate(REGIONS,1):
        setid=f'v10400_{slug}'
        local_bonuses[setid]={'name':f'Regalia {region}', 'hp':1.02+n*.002,
                              'damage':1.035+n*.002,'defense':1.0,'v104_four_piece':True}
        mat=f'v10400_{slug}_alloy';seal=f'v10400_{slug}_material_3'
        for slot,label in SLOTS:
            iid=f'v10400_set_{slug}_{slot}'
            local_items[iid]={'name':f'{label} {region}', 'type':'armor','slot':slot,
                              'rarity':'legendary','price':None,'defense':low*4,
                              'affix':'constitution','affix_amount':low//8,
                              'regional_set':setid,'sockets':2,
                              'desc':f'Regalia {region}: 2/4 HP, 4/4 obrażenia. Zalecany poziom {low}+.'}
            local_recipes[iid]={'name':f'Wykuj: {label} {region}', 'stations':('forge',),
                                'ingredients':{mat:2,seal:3,'steel_ingot':1},'output':iid,'quantity':1,
                                'profession':'Kowalstwo','generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                                'desc':f'Zestaw regionalny {region}, próg 2/4 i 4/4.'}
    for index,(class_name,klass_type,*_) in enumerate(CLASSES,1):
        slug=REGIONS[(index-1)%len(REGIONS)][0]
        low=REGIONS[(index-1)%len(REGIONS)][2]
        setid=f'v10400_class_{index:02d}'
        local_bonuses[setid]={'name':f'Regalia klasy {class_name}', 'hp':1.04,
                              'damage':1.07, 'defense':1.0,'v104_four_piece':True}
        for slot,label in SLOTS:
            iid=f'v10400_class_{index:02d}_{slot}'
            # Two offensive attributes and CON on class gear. The old
            # catalogue's equipment contract checks both, not only an affix.
            dominant = ('intelligence' if klass_type=='magic' else
                        'dexterity' if class_name in ('Łotrzyk','Łowca','Mnich','Mec','Inżynier')
                        else 'strength')
            secondary = ('willpower' if klass_type=='magic' else
                         'strength' if dominant=='dexterity' else 'dexterity')
            local_items[iid]={'name':f'{label} Dziedzictwa: {class_name}',
                              'type':'armor','slot':slot,'rarity':'legendary',
                              'price':None,'defense':low*5,
                              'affix':dominant,'affix_amount':low//7,
                              'stats':{secondary:max(1,low//13),
                                       'constitution':max(1,low//19)},
                              'required_class':class_name,
                              'class_set_name':f'Dziedzictwa: {class_name}',
                              'regional_set':setid,'sockets':2,
                              'desc':f'Zestaw tylko dla klasy {class_name}: 2/4 HP, 4/4 obrażenia.'}
            local_recipes[iid]={'name':f'Wykuj {label} Dziedzictwa {class_name}',
                                'stations':('forge',),
                                'ingredients':{f'v10400_{slug}_alloy':3,
                                               f'v10400_{slug}_material_3':4,'steel_ingot':1},
                                'output':iid,'quantity':1,
                                'profession':'Kowalstwo', 'generator_level':800, 'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                                'desc':f'Regalia klasy {class_name}; specjalizacja endgame.'}
    # Validate prerequisites *before* changing shared registries.
    for recipe in local_recipes.values():
        if not all(i in items for i in recipe['ingredients']):
            raise RuntimeError(f'Brak materiału: {recipe["name"]}')
    items.update(local_items);recipes.update(local_recipes);bonuses.update(local_bonuses)
    return {'sets':len(local_bonuses),'items':len(local_items),'recipes':len(local_recipes)}
