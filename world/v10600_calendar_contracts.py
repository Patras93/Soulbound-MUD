# -*- coding: utf-8 -*-
"""60 dodatkowych kontraktów dziennych/tygodniowych w 30 krainach v106.

Kalendarz UTC współdzieli istniejący licznik SQLite poprzez
systems.quest_calendar_v10400; kod uruchamia się tylko w v106 STAGING.
"""
from world.v10600_region_index import REGIONS
DAY=86400
WEEK=7*DAY


def planned_ids():
    return {f'v10600_contract_{slug}_{cadence}' for slug,*_ in REGIONS
            for cadence in ('daily','weekly')}


def install(quests,npcs,mobs,items):
    ids=planned_ids()
    if ids.issubset(quests):
        for slug,*_ in REGIONS:
            npc=npcs[f'v10600_{slug}_npc_4']
            if not all(f'v10600_contract_{slug}_{frequency}' in npc['specialist_quests']
                       for frequency in ('daily','weekly')):
                raise RuntimeError('v106: niepełny ponowny import zleceń')
        return {'contracts':0,'reason':'already installed'}
    if ids.intersection(quests):
        raise RuntimeError('v106: częściowa kolizja kontraktów')
    for slug,*_ in REGIONS:
        if f'v10600_{slug}_npc_4' not in npcs:
            raise RuntimeError('v106: brak NPC do kontraktu')
        if f'v10600_{slug}_mob_3' not in mobs or f'v10600_{slug}_boss_2' not in mobs:
            raise RuntimeError('v106: brak przeciwnika do kontraktu')
        if f'v10600_{slug}_material_1' not in items:
            raise RuntimeError('v106: brak materiału nagrody')
    for i,(slug,region,low,*_) in enumerate(REGIONS,1):
        npc=npcs[f'v10600_{slug}_npc_4'];offers=list(npc['specialist_quests'])
        for frequency,needed,target,cooldown in (
                ('daily',8,f'v10600_{slug}_mob_3',DAY),
                ('weekly',1,f'v10600_{slug}_boss_2',WEEK)):
            qid=f'v10600_contract_{slug}_{frequency}'
            daily=frequency=='daily'
            quests[qid]={
              'name':f'{"Codzienny" if daily else "Tygodniowy"} kontrakt: {region}',
              'giver':npc['name'],'kind':'kill','target':target,'needed':needed,
              'description':f'Pokonaj {needed} × {mobs[target]["name"]} i wróć do {npc["name"]}.',
              'generator_level':low,'repeatable':True,
              'repeat_cooldown':cooldown,
              'repeat_calendar_v104':'day_utc' if daily else 'week_utc',
              'reward_stat_progress':low*1200*(1 if daily else 4),
              'olc_reward_xp':low*1700*(1 if daily else 4),
              'olc_reward_class_xp':low*1600*(1 if daily else 4),
              'olc_reward_soul_xp':low*1400*(1 if daily else 4),
              'reward_gold':650+i*200 if daily else 3200+i*500,
              'reward_mithril':i+1 if daily else 4*i,
              'reward_items':{f'v10600_{slug}_material_1':2 if daily else 6}}
            offers.append(qid)
        npc['specialist_quests']=tuple(offers)
    return {'contracts':60,'daily':30,'weekly':30}
