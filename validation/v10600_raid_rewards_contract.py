# -*- coding: utf-8 -*-
"""Raid 26–35: all 30 stages, NPC turn-in routes and authored rewards.

Offline read-only audit; does not modify characters, SQLite or server files.
"""
from __future__ import annotations
import os


def run():
    assert os.environ.get('SOULBOUND_V106_STAGING')=='1', 'Tylko test v106 staging.'
    from world.dynamic_content import ROOMS,MOB_TEMPLATES,NPCS,QUESTS,ITEMS,CRAFT_RECIPES
    from world.v10600_raids_26_35 import RAID_ROWS
    checked=0
    def check(condition,message):
        nonlocal checked
        assert condition,'Nagrody rajdowe v106: '+message
        checked+=1
    ids=[]
    for no,region,name,mechanic,cycle in RAID_ROWS:
        root=f'v10600_raid_{no}'
        fragment=root+'_fragment';seal=root+'_seal';relic=root+'_relic'
        check(fragment in ITEMS and seal in ITEMS and relic in ITEMS,f'{no}: przedmioty nagród')
        recipe=CRAFT_RECIPES[relic]
        check(recipe['output']==relic and recipe['ingredients'][fragment]==3
              and recipe['ingredients'][seal]==1,f'{no}: poprawna receptura relikwii')
        for stage in (1,2,3):
            boss=f'{root}_boss_{stage}'
            quest_id=f'{root}_quest_{stage}'
            room_id=f'{root}_stage_{stage}'
            ids.append(quest_id)
            q=QUESTS[quest_id];m=MOB_TEMPLATES[boss]
            check(q['kind']=='kill' and q['target']==boss
                  and q['needed']==1,f'{no}/{stage}: cel zadania')
            check(q.get('requires_quest') == (f'{root}_quest_{stage-1}' if stage>1 else None),
                  f'{no}/{stage}: kolejność i odblokowanie')
            check(q['reward_items']=={fragment:1} and int(q['reward_gold'])>0
                  and int(q['reward_mithril'])>0,f'{no}/{stage}: nagrody zadania')
            check(m['drops'].get(fragment)==1.0 and
                  (m['drops'].get(seal)==1.0)==(stage==3),
                  f'{no}/{stage}: materiały z bossa')
            check(m['quest_target']==boss and len(m['olc_boss_phases'])==4,
                  f'{no}/{stage}: połączenie z walką/fazami')
            check(room_id in ROOMS and ROOMS[room_id]['generator_level']==m['generator_level'],
                  f'{no}/{stage}: właściwa sala')
            npcs=[(npcid,npc) for npcid,npc in NPCS.items()
                  if npc.get('name')==q['giver']]
            check(len(npcs)==1 and npcs[0][1].get('room') in ROOMS
                  and quest_id in npcs[0][1].get('specialist_quests',()),
                  f'{no}/{stage}: NPC i oddawanie')
            check(not q.get('repeatable') and not q.get('remote_turnin'),
                  f'{no}/{stage}: jednokrotne oddawanie u NPC')
    check(len(set(ids))==30,'unikalne identyfikatory 30 questów')
    print(f'V106 NAGRODY RAJDOW 26-35: {checked} PASS '
          f'(30 etapow, cele, NPC, drop, skladniki, odblokowania).',flush=True)
    return checked

if __name__=='__main__': run()
