# -*- coding: utf-8 -*-
"""v105: 12 distinct regional and 22 class four-piece equipment sets.
Native regional_set 2/4 and 4/4 bonuses; no custom equipment ledger.
"""
from core.classes_skills import CLASSES
from world.v10500_region_index import REGIONS
from world.v10400_equipment_5001 import SLOTS


def planned_ids():
    return frozenset([f'v10500_set_{slug}_{slot}' for slug,*_ in REGIONS[:12] for slot,_ in SLOTS] +
                     [f'v10500_class_{j:02d}_{slot}' for j in range(1,23) for slot,_ in SLOTS])


def install(items,recipes,bonuses):
    ids=planned_ids()
    if ids.issubset(items) and ids.issubset(recipes):
        return {'sets':0,'items':0,'recipes':0,'reason':'already installed'}
    if ids & (set(items)|set(recipes)):
        raise RuntimeError('v105: kolizja w katalogu zestawów')
    all_sets={f'v10500_{slug}' for slug,*_ in REGIONS[:12]} | {f'v10500_class_{j:02d}' for j in range(1,23)}
    if all_sets & set(bonuses): raise RuntimeError('v105: kolizja bonusów zestawu')
    local_i={};local_r={};local_b={}
    for i,(slug,region,low,*_) in enumerate(REGIONS[:12],1):
        sid=f'v10500_{slug}';local_b[sid]={'name':f'Regalia {region}',
                                             'hp':1.06+i*.002,'damage':1.10+i*.003,
                                             'defense':1.0,'v104_four_piece':True}
        for slot,label in SLOTS:
            iid=f'v10500_set_{slug}_{slot}'
            local_i[iid]={'name':f'{label} {region}', 'type':'armor','slot':slot,
                          'rarity':'legendary','price':None,'defense':low*5,
                          'affix':'constitution','affix_amount':low//7,'regional_set':sid,
                          'sockets':3,'desc':f'Set {region}: premie za 2/4 i 4/4. Trzy gniazda run.'}
            local_r[iid]={'name':f'Wykuj {label} {region}', 'stations':('forge',),
                          'ingredients':{f'v10500_{slug}_alloy':2,f'v10500_{slug}_material_3':3,'steel_ingot':1},
                          'output':iid,'quantity':1,'profession':'Kowalstwo',
                          'generator_level':800,'min_profession_level':low,
                          'profession_xp':low*5,'tool_xp':low*4,
                          'desc':f'Czteroczęściowy zestaw regionalny {region}.'}
    for j,(class_name,kind,*_) in enumerate(CLASSES,1):
        slug,region,low,*_=REGIONS[(j-1)%len(REGIONS)]
        sid=f'v10500_class_{j:02d}'
        local_b[sid]={'name':f'Dziedzictwo {class_name} v105',
                      'hp':1.11,'damage':1.14,'defense':1.,'v104_four_piece':True}
        main='intelligence' if kind=='magic' else 'dexterity' if class_name in ('Łotrzyk','Łowca','Mnich','Mec','Inżynier') else 'strength'
        secondary='willpower' if kind=='magic' else 'strength' if main=='dexterity' else 'dexterity'
        for slot,label in SLOTS:
            iid=f'v10500_class_{j:02d}_{slot}'
            local_i[iid]={'name':f'{label} Wiecznego Dziedzictwa: {class_name}',
                          'type':'armor','slot':slot,'rarity':'legendary','price':None,
                          'defense':low*6,'affix':main,'affix_amount':low//5,
                          'stats':{secondary:max(1,low//13),'constitution':low//12},'required_class':class_name,
                          'class_set_name':f'Wieczne Dziedzictwo: {class_name}',
                          'regional_set':sid,'sockets':3,
                          'desc':f'Zestaw klasy {class_name}, premie za 2/4 i 4/4; trzy gniazda run.'}
            local_r[iid]={'name':f'Wykuj {label}: {class_name} v105',
                          'stations':('forge',),'ingredients':{f'v10500_{slug}_alloy':3,
                          f'v10500_{slug}_material_3':4,'steel_ingot':1},
                          'output':iid,'quantity':1,'profession':'Kowalstwo',
                          'generator_level':800,'min_profession_level':low,
                          'profession_xp':low*5,'tool_xp':low*4,
                          'desc':f'Zestaw klasy {class_name}, etap v105.'}
    for recipe in local_r.values():
        if not set(recipe['ingredients']).issubset(items):
            raise RuntimeError('v105: brakuje materiału dla zestawu '+recipe['name'])
    items.update(local_i);recipes.update(local_r);bonuses.update(local_b)
    return {'sets':len(local_b),'items':len(local_i),'recipes':len(local_r)}
