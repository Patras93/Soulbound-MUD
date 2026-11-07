# -*- coding: utf-8 -*-
"""300 fizycznych nowych Prób Soul Tier 3010–6000; KOD ROBOCZY.

Ważne: samo wygenerowanie definicji nie podnosi SOUL_MAX_TIER silnika.
Starych prób 1–3000 nie modyfikować. Integracja później wymaga aktualizacji
core/progression_600.py i realnych testów unlock oraz ofert Elora.
"""
from world.v10600_region_index import REGIONS

FIRST=3010
LAST=6000
STEP=10


def trial_ids():
    return {tier:f'soul_tier_{tier:02d}_trial' for tier in range(FIRST,LAST+1,STEP)}


def quest_definitions():
    result={}
    for tier,qid in trial_ids().items():
        region_index=min((tier-3001)//100, len(REGIONS)-1)
        slug,region,low,high,_,_=REGIONS[region_index]
        boss_number=1 if tier%100<=50 and tier%100!=0 else 2
        mob=f'v10600_{slug}_boss_{boss_number}'
        needed_level=tier*10
        result[qid]={
            'name':f'Próba Broni Duszy: Tier {tier}',
            'giver':'Kapłan Elor','kind':'kill','target':mob,'needed':1,
            'description':f'Pokonaj strażnika krainy {region}, wróć do Kapłana Elora. '
                          f'Wymaga Soul Level {needed_level} i Tieru {tier-1}.',
            'required_soul_level':needed_level,'required_soul_tier':tier-1,
            'unlocks_soul_tier':tier,
            'reward_gold':max(1,500+(tier-3000)*120),
            'reward_silver':needed_level*120,'reward_mithril':0,'reward_items':{},
            'olc_reward_xp':2_000_000+(tier-500)*40_000,
            'olc_reward_class_xp':1_500_000+(tier-500)*30_000,
            'olc_reward_soul_xp':2_000_000+(tier-500)*35_000,
            'olc_reward_stat_xp':1_000_000+(tier-500)*20_000,
        }
    return result


def register(quests,mobs):
    definitions=quest_definitions()
    if set(definitions).issubset(quests):
        # world.equipment_help dodaje do istniejących wpisów metadane
        # trial_band/soul_trial_tier; nie wolno ich kasować ani nadpisywać.
        # Silnik dawnych questów normalizuje walutę z reward_gold do
        # reward_silver. Tę starą operację zostawiamy nienaruszoną; inne
        # pola, zwłaszcza cel, próg Tieru i EXP, muszą być dokładne.
        if any(any(quests[q].get(k) != value for k,value in definition.items()
                   if k not in ('reward_gold','reward_silver'))
               for q,definition in definitions.items()):
            raise RuntimeError('v106: niespójny ponowny import Prób Duszy')
        missing={q['target'] for q in definitions.values()}-set(mobs)
        if missing:raise RuntimeError('v106: brak bossów Prób: '+str(sorted(missing)[:3]))
        return 0
    if set(definitions)&set(quests):
        raise RuntimeError('v106: częściowa kolizja Prób Duszy')
    missing={q['target'] for q in definitions.values()}-set(mobs)
    if missing:raise RuntimeError('v106: brakuje bossów Prób: '+str(sorted(missing)[:3]))
    quests.update(definitions)
    return len(definitions)
