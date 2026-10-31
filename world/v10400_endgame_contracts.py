# -*- coding: utf-8 -*-
"""Repeatable 5001+ contracts using the native quest ledger and NPC offers.

Repeat cooldown is measured from completion, not a calendar rollover. Not a new
bounty engine; no background timer or in-memory reward counter is introduced.
"""
from __future__ import annotations
from world.v10400_krainy_5001_10000 import REGIONS

DAY=86400
WEEK=7*DAY

def install(quests,npcs,mobs,items):
    ids={f'v10400_contract_{slug}_{freq}' for slug,*_ in REGIONS for freq in ('daily','weekly','invasion')}
    present=ids&set(quests)
    if present:
        if present!=ids:
            raise RuntimeError('Niekompletny katalog kontraktów v104')
        return {'contracts':0,'reason':'already installed'}
    for slug,*_ in REGIONS:
        if f'v10400_{slug}_npc_3' not in npcs:
            raise RuntimeError(f'Brak NPC kontraktowego {slug}')
        for suffix in ('mob_3','boss_2'):
            if f'v10400_{slug}_{suffix}' not in mobs:
                raise RuntimeError(f'Brak celu {slug} {suffix}')
    for i,(slug,region,low,high,*_) in enumerate(REGIONS,1):
        npc=npcs[f'v10400_{slug}_npc_3']
        offers=list(npc['specialist_quests'])
        for freq,needed,enemy,cooldown in (
            ('daily',8,'mob_3',DAY),('weekly',1,'boss_2',WEEK),
            ('invasion',3,'boss_2',WEEK)):
            qid=f'v10400_contract_{slug}_{freq}'
            mob=f'v10400_{slug}_{enemy}'
            quests[qid]={
                'name':f'{"Codzienny" if freq=="daily" else "Tygodniowy"} kontrakt: {region}' + (' — Inwazja' if freq=='invasion' else ''),
                'giver':npc['name'],'kind':'kill','target':mob,'needed':needed,
                'description':f'Pokonaj {needed} × {mobs[mob]["name"]}; wróć do {npc["name"]}. ',
                'generator_level':low, 'repeatable':True,
                'repeat_cooldown':cooldown,
                'repeat_calendar_v104':'day_utc' if freq=='daily' else 'week_utc',
                'reward_stat_progress':low*1000*(1 if freq=='daily' else 5),
                'olc_reward_xp':low*1600*(1 if freq=='daily' else 5),
                'olc_reward_class_xp':low*1400*(1 if freq=='daily' else 5),
                'olc_reward_soul_xp':low*1200*(1 if freq=='daily' else 5),
                'reward_gold':300+i*100 if freq=='daily' else 1800+i*300,
                'reward_mithril':i if freq=='daily' else 5*i,
                'reward_items':{f'v10400_{slug}_material_1':2 if freq=='daily' else 6},
                'v104_contract_kind':freq,
            }
            offers.append(qid)
        npc['specialist_quests']=tuple(offers)
    return {'contracts':len(ids),'daily':10,'weekly':10,'invasion_repeatable':10}
