# -*- coding: utf-8 -*-
"""Additive ancient materials, equipment, and actual profession-action quests.

No new tools, changes to EXP requirements, or reduction of prior rewards.
Relics are earned in real battles in the v11 wilderness, crafts consume them.
"""
from systems.forgotten_horizons_v1000 import _insert
from systems.eternal_glory_world_v1100 import REGIONS

NEW_CHARM_IDS = frozenset(f'v1100_artifact_{key}' for key,*_ in REGIONS)

# All twenty-two profession-action names use the existing database event handlers.
PROFESSION_NAMES = (
    'Wędkarstwo','Górnictwo','Drwalstwo','Kowalstwo','Gotowanie','Zielarstwo',
    'Alchemia','Jubilerstwo','Krawiectwo','Garbarstwo','Stolarstwo',
    'Zaklinanie','Archeologia','Kartografia',
    'Łowiectwo','Rolnictwo','Hodowla zwierząt','Okrętownictwo',
    'Murarstwo','Inżynieria','Kupiectwo','Żeglarstwo',
)
PROFESSION_QUEST_IDS = frozenset(
    f'v1100_craft_quest_{idx:02d}' for idx in range(len(PROFESSION_NAMES))
)


def install(items, quests, npcs, recipes, help_topics):
    for idx,(key,zone,level,element,guide,elite,boss,places) in enumerate(REGIONS):
        charm_id = f'v1100_artifact_{key}'
        mat_id = f'v1100_eg_{key}_relic'
        if mat_id not in items or 'soul_shard' not in items:
            raise AssertionError('11.0 crafting: missing a battle-earned material')
        _insert(items,'ITEMS',charm_id,{
            'name':f'Talizman Wiecznej Chwały: {zone}',
            'type':'armor','slot':'charm',
            'defense': max(8, level//9),
            'price':None,'sell_silver': (level+80)*880,
            'generator_level':level,
            'desc': f'Talizman sporządzony z dwóch reliktów regionu {zone}.',
            'v1100_artifact':True,
        })
        _insert(recipes,'CRAFT_RECIPES',charm_id,{
            'name':f'Wykucie: Talizman Wiecznej Chwały — {zone}',
            'stations':('forge',),
            'ingredients':{mat_id:2,'soul_shard':5 + idx},
            'output':charm_id,'quantity':1,
            'min_profession_level':min(800,max(80,level//2)),
            'tool_xp':max(500,level*9),
            'profession_xp':max(800,level*14),
            'generator_level':level,
            'category':'smithing',
            'desc':f'Wykorzystaj relikty ze strażników regionu {zone}; wyrób do slotu talizmanu.',
        })
    for idx, prof in enumerate(PROFESSION_NAMES):
        key,zone,level,element,guide,elite,boss,places = REGIONS[idx%len(REGIONS)]
        qid=f'v1100_craft_quest_{idx:02d}'
        _insert(quests,'QUESTS',qid,{
            'name': f'Mistrzostwo Wiecznej Chwały: {prof}',
            'giver':guide,'kind':'profession_action','target':prof,
            'needed':max(5,5+idx//2),
            'description':f'Wykonaj czynności profesji {prof} podczas przygotowań do wyprawy w {zone}.',
            'generator_level': min(800, max(50,level//2)),
            'reward_silver':(level+20)*5300,
            'reward_gold':0,'reward_mithril':0,'reward_items':{},
            'repeatable':False,'v1100_profession_quest':True,
        })
        npc = npcs[f'v1100_eg_{key}_guide']
        npc['specialist_quests'] = tuple(npc['specialist_quests'])+(qid,)
    help_topics['rzemioslo11'] = [
        'Rzemiosło Wiecznej Chwały: 12 talizmanów z nowych reliktów, w Kuźni.',
        'Każdy wyrób potrzebuje dwa regionalne relikty zdobywane w prawdziwej walce i Odłamki Duszy.',
        'U przewodników znajdziesz 22 jednorazowe zlecenia oparte na prawdziwych czynnościach profesji.',
        'Nie dodano nowych narzędzi; nagrody i wcześniejsze receptury pozostają bez zmian.',
    ]
    return {'talismans':len(NEW_CHARM_IDS),'profession_quests':len(PROFESSION_QUEST_IDS)}
