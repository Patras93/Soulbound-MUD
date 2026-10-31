# -*- coding: utf-8 -*-
"""Era Bez Granic: 11 trzyetapowych rajdów w osobnych komnatach.

Wszystkie bossy korzystają z istniejącego AI faz (4 progi HP).
Nie tworzy nowych tabel bazy ani nie odblokowuje progresji graczom.
"""
from __future__ import annotations

from world.v10300_era_bez_granic import ERAS
from systems.live_olc4_boss_phases import validate_boss_phases


def raid_phases(slug):
    names = ('Przebudzenie pieczęci', 'Kontratak żywiołów',
             'Rozdarcie horyzontu', 'Ostatnia przysięga')
    return [dict(hp_percent=p, attack_multiplier=m, duration_seconds=duration,
                 message=f'{name} — {slug}.')
            for p, m, duration, name in zip((80, 60, 40, 20),
                (1.2, 1.45, 1.7, 2.0), (18, 22, 26, 30), names)]


def install(rooms, mobs, spawns, npcs, quests, items, recipes):
    """Wprowadza rajdy atomowo przy pierwszym uruchomieniu katalogu.

    Kolejność komnat to 1->2->3, questy 1->2->3. Ścieżka nie
    wymaga poziomu, ale questy wymagają poprzedniej części serii.
    """
    if 'v10300_swit_raid_1' in rooms:
        return {'raids': 0, 'reason':'already installed'}
    for slug, *_ in ERAS:
        prefix=f'v10300_{slug}'
        if f'{prefix}_09' not in rooms or f'{prefix}_npc_2' not in npcs:
            raise RuntimeError(f'Rajdy v103: brak regionu {slug}')
        if 'east' in rooms[f'{prefix}_09'].get('exits',{}):
            raise RuntimeError(f'Rajdy v103: zajęte przejście {prefix}_09')
    planned_rooms={f'v10300_{slug}_raid_{j}' for slug,*_ in ERAS for j in (1,2,3)}
    planned_mobs={f'v10300_{slug}_raid_boss_{j}' for slug,*_ in ERAS for j in (1,2,3)}
    planned_quests={f'v10300_{slug}_raid_quest_{j}' for slug,*_ in ERAS for j in (1,2,3)}
    planned_items={f'v10300_{slug}_raid_relic' for slug,*_ in ERAS}
    planned_items |= {f'v10300_{slug}_raid_fragment' for slug,*_ in ERAS}
    planned_recipes={f'v10300_{slug}_raid_relic' for slug,*_ in ERAS}
    for kind,registry,ids in (('rooms',rooms,planned_rooms),('mobs',mobs,planned_mobs),
                              ('quests',quests,planned_quests),('items',items,planned_items),
                              ('recipes',recipes,planned_recipes)):
        collision=ids.intersection(registry)
        if collision:raise RuntimeError(f'Rajdy v103: kolizja {kind}: {sorted(collision)[0]}')
    for stage,(slug,zone,low,high,theme,*_) in enumerate(ERAS,1):
        prefix=f'v10300_{slug}'
        entry=f'{prefix}_09'
        rooms[entry]['exits']['east']=f'{prefix}_raid_1'
        fragments=f'{prefix}_raid_fragment';relic=f'{prefix}_raid_relic'
        items[fragments]={'name':f'Fragment Rajdu {zone}', 'type':'craft_material',
                          'price':None,'sell_gold':30*stage,'desc':'Odłamek z trzech etapów rajdu.'}
        items[relic]={'name':f'Relikwia Rajdu {zone}', 'type':'armor', 'slot':'charm',
                      'defense':round(low*3.25),'price':None,
                      'desc':f'Relikwia obronna zdobyta w rajdzie {zone}.'}
        recipes[relic]={'name':f'Relikwia Rajdu {zone}', 'stations':('forge',),'category':'raid_relic',
                        'ingredients':{fragments:3,f'{prefix}_material_3':1,'steel_ingot':1},
                        'output':relic,'quantity':1,'profession':'Kowalstwo',
                        'generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                        'desc':f'Połącz fragmenty trzech bossów z regionalną pieczęcią.'}
        npc=npcs[f'{prefix}_npc_2']
        existing=list(npc['specialist_quests'])
        for j in (1,2,3):
            room_id=f'{prefix}_raid_{j}'
            monster_id=f'{prefix}_raid_boss_{j}'
            qid=f'{prefix}_raid_quest_{j}'
            req=low+round((high-low)*(j-1)/2)
            rooms[room_id]={
                'zone':zone, 'name':f'Rajd {zone}: etap {j} z 3',
                'desc':f'{theme}. Komnata {j} rajdu. Boss posiada cztery fazy HP. '
                       'Można wrócić; odblokowanie kolejnego questa wymaga wcześniejszego.',
                'generator_level':req,'recommended_mastery':req,
                'exits':{'west':entry} if j==1 else {'south':f'{prefix}_raid_{j-1}'}
            }
            if j<3:rooms[room_id]['exits']['north']=f'{prefix}_raid_{j+1}'
            # Reverse exits constructed only after all stage rooms are created.
            mobs[monster_id]={
                'name':f'{zone}: Władca Rajdu, etap {j}', 'boss':True,
                'world_boss':True,
                'boss_mechanic_text':'Fazy HP 80%, 60%, 40%, 20%; zmienne ataki i strażnicy.',
                'olc_boss_phases':raid_phases(slug),
                'olc_boss_guardian_interval':max(2,5-j),
                'generator_level':req,'max_hp':(1_800_000+req*14_000)*(j+1),
                'damage':(2_000+req*11)*(j+1),
                'damage_type':'magic' if j!=2 else 'physical',
                'class_xp_reward':max(200000,req*3500*j),
                'soul_reward':max(200000,req*1700*j),
                'stat_reward':max(200000,req*1500*j),
                'gold':400+stage*350+j*150,'silver':10000+stage*1300,
                'mithril':stage+j,'drops':{fragments:1.0, f'{prefix}_material_3':0.4},
                'endgame_region_mastery':req,'quest_target':monster_id,
                'leave_corpse':True,
            }
            validate_boss_phases(mobs[monster_id],mobs[monster_id]['olc_boss_phases'])
            spawns.append((room_id,monster_id))
            quests[qid]={
                'name':f'{zone}: rajd, etap {j} z 3',
                'giver':npc['name'],'kind':'kill','target':monster_id,'needed':1,
                'description':f'Pokonaj {mobs[monster_id]["name"]} w komnacie rajdu. '
                              f'Wracaj do {npc["name"]} po nagrodę i kolejną próbę.',
                'generator_level':req,
                'reward_stat_progress':max(200000,req*2000*j),
                'reward_gold':700+stage*500+j*100,'reward_mithril':stage+j,
                'reward_items':{fragments:1},
                **({'requires_quest':f'{prefix}_raid_quest_{j-1}'} if j>1 else {})
            }
            existing.append(qid)
        npc['specialist_quests']=tuple(existing)
        # Keep original quest chain stable: raid quests are independently selectable
        # from NPC's specialist_quests; never insert into old story chains.
    return {'raids':len(ERAS), 'rooms':len(planned_rooms), 'bosses':len(planned_mobs),
            'quests':len(planned_quests), 'items':len(planned_items),
            'recipes':len(planned_recipes)}
