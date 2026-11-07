# -*- coding: utf-8 -*-
"""v106: dziesięć nowych rajdów 26–35, po trzy etapy. Etap rozwoju.

Podłączono do testowego bootstrapu v106, ale NIE do produkcji. Docelowo
1–6 realnych graczy; naturalne walki i atomowość nagród nadal do audytu.
"""
from world.v10600_region_index import REGIONS
from world.v10400_raids_12_25 import _boss_phases, _phase_strategy
from systems.live_olc4_boss_phases import validate_boss_phases

RAID_ROWS=(
 (26,4,'Brama Rozdartego Firmamentu','osłony i rozdarcia',('lightning','holy','shadow')),
 (27,9,'Tron Błękitnego Wiru','przypływy i cisza',('ice','lightning','dark')),
 (28,11,'Archiwum Żywych Run','przełamywanie run',('holy','fire','shadow')),
 (29,14,'Sanktuarium Pamięci','odbicia wspomnień',('dark','holy','ice')),
 (30,16,'Sąd Dwunastu Cieni','zmienne wyroki',('shadow','dark','holy')),
 (31,19,'Pałac Nienazwanych','brak imienia i złudzenia',('dark','poison','holy')),
 (32,22,'Kuźnia Dusz','przegrzanie i odsiecz',('fire','lightning','ice')),
 (33,24,'Krąg Prób','węzły duszy i rytuał',('holy','shadow','fire')),
 (34,28,'Żywa Cytadela','sieci osłon i kontry',('ice','fire','lightning')),
 (35,29,'Serce Astralnego Przebudzenia','pełnia pierwotnej mocy',('holy','dark','lightning')),
)
STAGES=('Strażnik Progu','Herold Przemiany','Władca Ostateczny')


def planned_ids():
    return {'rooms':{f'v10600_raid_{no}_stage_{s}' for no,*_ in RAID_ROWS for s in (1,2,3)},
            'mobs':{f'v10600_raid_{no}_boss_{s}' for no,*_ in RAID_ROWS for s in (1,2,3)},
            'quests':{f'v10600_raid_{no}_quest_{s}' for no,*_ in RAID_ROWS for s in (1,2,3)},
            'items':{f'v10600_raid_{no}_{part}' for no,*_ in RAID_ROWS for part in ('fragment','seal','relic')},
            'recipes':{f'v10600_raid_{no}_relic' for no,*_ in RAID_ROWS}}


def install(rooms,mobs,spawns,npcs,quests,items,recipes):
    ids=planned_ids()
    regs={'rooms':rooms,'mobs':mobs,'quests':quests,'items':items,'recipes':recipes}
    first='v10600_raid_26_stage_1'
    if first in rooms:
        for label,required in ids.items():
            if not required.issubset(regs[label]):raise RuntimeError('v106: częściowy import rajdu '+label)
        for no,idx,*_ in RAID_ROWS:
            parent=f'v10600_{REGIONS[idx][0]}_23'
            if rooms[parent]['exits'].get('east')!=f'v10600_raid_{no}_stage_1':
                raise RuntimeError('v106: utracone wejście rajdu '+str(no))
        return {'raids':0,'rooms':0,'bosses':0,'quests':0,'reason':'already installed'}
    for label,required in ids.items():
        if required.intersection(regs[label]):raise RuntimeError('v106: kolizja rajd '+label)
    for no,idx,*_ in RAID_ROWS:
        slug=REGIONS[idx][0]; parent=f'v10600_{slug}_23'
        npc=f'v10600_{slug}_npc_4'
        if parent not in rooms or 'east' in rooms[parent].get('exits',{}):
            raise RuntimeError('v106: brak wejścia do rajdu '+str(no))
        if npc not in npcs:raise RuntimeError('v106: brak gospodarza rajdu '+str(no))
    for no,idx,name,mechanic,cycle in RAID_ROWS:
        slug,region,low,high,*_=REGIONS[idx]
        root=f'v10600_raid_{no}';entry=f'v10600_{slug}_23'
        npc=npcs[f'v10600_{slug}_npc_4'];offers=list(npc['specialist_quests'])
        fragment=f'{root}_fragment';seal=f'{root}_seal';relic=f'{root}_relic'
        for iid,label in ((fragment,'Odłamek'),(seal,'Pieczęć'),(relic,'Relikwia')):
            items[iid]={'name':f'{label} rajdu {name}', 'type':'craft_material',
                       'price':None,'desc':f'Nagroda z rajdu {no}: {name}.'}
        recipes[relic]={'name':f'Złóż relikwię {name}','stations':('forge',),
            'ingredients':{fragment:3,seal:1,f'v10600_{slug}_alloy':2},
            'output':relic,'quantity':1,'profession':'Kowalstwo',
            'min_profession_level':low,'generator_level':800,
            'profession_xp':low*6,'tool_xp':low*5,'desc':f'Relikwia rajdu {no}.'}
        rooms[entry]['exits']['east']=f'{root}_stage_1'
        for s,label in enumerate(STAGES,1):
            rid=f'{root}_stage_{s}';mid=f'{root}_boss_{s}';qid=f'{root}_quest_{s}'
            prev=entry if s==1 else f'{root}_stage_{s-1}'
            exits={'west':entry} if s==1 else {'south':prev}
            if s<3:exits['north']=f'{root}_stage_{s+1}'
            rooms[rid]={'zone':region,'name':f'Rajd {no}: {name} — {label}',
             'desc':f'{mechanic}; fazy 80, 60, 40, 20 procent HP. '
                    f'Etap {s}/3. Dostępny odwrót.',
             'generator_level':low+(high-low)*(s-1)//2,
             'recommended_mastery':low,'exits':exits}
            lvl=low+(high-low)*(s-1)//2
            phases=_boss_phases(name,s);strategy=_phase_strategy(cycle,s)
            mobs[mid]={'name':f'{name}: {label}','boss':True,'world_boss':True,
                'boss_mechanic_text':mechanic,'olc_boss_phases':phases,
                'olc_boss_guardian_interval':max(2,6-s),
                'olc_boss_tactic_interval':max(2,6-s),
                'olc_boss_support_interval':max(2,6-s),
                'olc_boss_element_cycle':list(cycle),**strategy,
                'generator_level':lvl,'v106_authored_boss_stage':lvl,
                'max_hp':(7_000_000+lvl*24000)*(s+1),
                'damage':(5000+lvl*18)*(s+1),
                'damage_type':'magic' if s!=2 else 'physical',
                'class_xp_reward':lvl*6500*s,'soul_reward':lvl*5000*s,
                'stat_reward':lvl*3900*s,'gold':1800+no*220+s*350,
                'silver':20000+no*1300,'mithril':no+s,
                'drops':{fragment:1.,f'v10600_{slug}_material_3':0.5,
                         **({seal:1.} if s==3 else {})},
                'quest_target':mid,'leave_corpse':True}
            validate_boss_phases(mobs[mid],phases)
            spawns.append((rid,mid))
            quest={'name':f'Rajd {no}: {name}, etap {s}/3',
                  'giver':npc['name'],'kind':'kill','target':mid,'needed':1,
                  'description':f'Pokonaj {name}: {label}; wróć do {npc["name"]}.',
                  'generator_level':lvl,'reward_stat_progress':lvl*3000*s,
                  'reward_gold':2000+no*350+s*450,'reward_mithril':no+s,
                  'reward_items':{fragment:1}}
            if s>1:quest['requires_quest']=f'{root}_quest_{s-1}'
            quests[qid]=quest;offers.append(qid)
        npc['specialist_quests']=tuple(offers)
    return {'raids':10,'rooms':30,'bosses':30,'quests':30}
