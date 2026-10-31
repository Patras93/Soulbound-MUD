# -*- coding: utf-8 -*-
"""Soulbound v104 etap 4: rajdy 12–25, bez migracji kont i bez bramek poziomu.

Integracja z dotychczasowymi rejestrami świata, questów, NPC, łupów i OLC AI.
Nie nadpisuje rajdów v103 ani systemu nagród; każdy boss ma unikatowe ID.
"""
from __future__ import annotations

from world.v10400_krainy_5001_10000 import REGIONS
from systems.live_olc4_boss_phases import validate_boss_phases
from systems.live_olc20_phase_tactics import validate_stage_map, ELEMENTS, ROLES
from systems.live_olc21_phase_strategy import validate_phase_strategy

# RAID_ID, region slug, entrance room number, NPC number, name, mechanic, elemental cycle
# Two different quest-givers host the paired raids in four first regions.
RAIDS = (
    (12, 'sztorm', 11, 2, 'Tron Piorunów', 'piorunowe kontrataki i szybkie fazy', ('lightning', 'ice', 'holy')),
    (13, 'sztorm', 13, 3, 'Oko Wiecznego Cyklonu', 'rotacja burzy i osłony strażników', ('ice', 'lightning', 'shadow')),
    (14, 'zelazo', 11, 2, 'Twierdza Żywego Metalu', 'obrońcy i przemiany pancerza', ('fire', 'lightning', 'poison')),
    (15, 'zelazo', 13, 3, 'Serce Tytanicznej Kuźni', 'przegrzanie i odsiecz konstruktorów', ('fire', 'holy', 'lightning')),
    (16, 'cienie', 11, 2, 'Flota Bez Powrotu', 'mroczne zasadzki i kontratak załogi', ('shadow', 'dark', 'ice')),
    (17, 'cienie', 13, 3, 'Korona Ciszy', 'osłony cieni i przebudzenie upiorów', ('dark', 'poison', 'shadow')),
    (18, 'runy', 11, 2, 'Pieczęć Pierwszej Runy', 'rytuały i zmiana żywiołów', ('holy', 'fire', 'dark')),
    (19, 'runy', 13, 3, 'Archiwum Zakazanej Magii', 'runiczne wsparcie i obrona', ('lightning', 'holy', 'poison')),
    (20, 'ogrody', 13, 3, 'Korzenie Początku', 'leczenie strażników i furia natury', ('poison', 'holy', 'shadow')),
    (21, 'pustynia', 13, 3, 'Ołtarz Zapomnienia', 'burze piasku i gniew bóstwa', ('fire', 'dark', 'holy')),
    (22, 'wrota', 13, 3, 'Rozdarcie Wieloświata', 'zmienne żywioły między wymiarami', ('lightning', 'shadow', 'holy')),
    (23, 'smok', 13, 3, 'Oddech Pierwotnego Smoka', 'ogień i ochrona smoczych strażników', ('fire', 'fire', 'holy')),
    (24, 'labirynt', 13, 3, 'Serce Nieskończonych Dróg', 'przebiegłe kontry i wzmocnienia', ('shadow', 'ice', 'dark')),
    (25, 'tron', 13, 3, 'Wojna Ostatniego Świtu', 'pełna furia czterech faz', ('holy', 'fire', 'lightning')),
)

STAGE_NAMES = ('Strażnik Progu', 'Władca Przemiany', 'Suweren Ostateczny')
PHASE_NAMES = ('Budzi pieczęcie', 'Wzywa obrońców', 'Rozrywa osłony', 'Ostatnia furia')
PHASE_THRESHOLDS = (80, 60, 40, 20)
PHASE_ATTACK = (1.22, 1.48, 1.82, 2.25)


def _ids():
    return {
        'rooms': {f'v10400_raid_{n:02d}_stage_{s}' for n, *_ in RAIDS for s in (1, 2, 3)},
        'mobs': {f'v10400_raid_{n:02d}_boss_{s}' for n, *_ in RAIDS for s in (1, 2, 3)},
        'quests': {f'v10400_raid_{n:02d}_raid_quest_{s}' for n, *_ in RAIDS for s in (1, 2, 3)},
        'items': {f'v10400_raid_{n:02d}_{kind}' for n, *_ in RAIDS
                  for kind in ('fragment', 'seal', 'relic')},
        'recipes': {f'v10400_raid_{n:02d}_relic' for n, *_ in RAIDS},
    }


def _boss_phases(raid_name, stage):
    return [dict(hp_percent=hp, attack_multiplier=min(3.0, mult+stage*.06),
                 duration_seconds=18+3*index+stage,
                 message=f'{PHASE_NAMES[index-1]} — {raid_name}, etap {stage}.')
            for index, (hp, mult) in enumerate(zip(PHASE_THRESHOLDS, PHASE_ATTACK), 1)]


def _phase_strategy(cycle, stage):
    # 0 and all 4 active phases are mapped explicitly to current OLC combat AI.
    phases = ('0', '1', '2', '3', '4')
    elements = {p: [cycle[(i+int(p)) % len(cycle)], cycle[(i+int(p)+1) % len(cycle)]]
                for i, p in enumerate(phases)}
    roles = {p: [['obronca', 'zbrojny'], ['arkaniczny', 'obronca'],
                 ['uzdrowiciel', 'arkaniczny'], ['furia', 'zbrojny'],
                 ['furia', 'obronca']][int(p)] for p in phases}
    tactics = {p: max(2, 6-int(p)-(stage//2)) for p in phases}
    guardians = {p: max(2, 6-int(p)-(stage//2)) for p in phases}
    support = {p: max(2, 7-int(p)) for p in phases}
    validate_stage_map(elements, ELEMENTS, 'żywioły')
    validate_stage_map(roles, ROLES, 'role')
    for field, value in (('olc_boss_phase_tactic_intervals', tactics),
                         ('olc_boss_phase_guardian_intervals', guardians),
                         ('olc_boss_phase_support_intervals', support)):
        validate_phase_strategy(field, value)
    return {
        'olc_boss_phase_element_cycles':elements,
        'olc_boss_guardian_phase_roles':roles,
        'olc_boss_phase_tactic_intervals':tactics,
        'olc_boss_phase_guardian_intervals':guardians,
        'olc_boss_phase_support_intervals':support,
    }


def install(rooms, mobs, spawns, npcs, quests, items, recipes):
    """Rejestracja z prekontrolą kolizji, bez dotykania zapisów postaci.

    Zmienia tylko dwa istniejące pola dla każdego rajdu: exits[east] sali
    wejściowej i specialist_quests jego NPC. Pozostałe dane są nowe.
    """
    planned=_ids()
    first='v10400_raid_12_stage_1'
    if first in rooms:
        for kind, registry in (('rooms',rooms),('mobs',mobs),('quests',quests),
                               ('items',items),('recipes',recipes)):
            if not planned[kind].issubset(registry):
                raise RuntimeError(f'Rajdy v104: niekompletny ponowny import {kind}')
        for number,slug,room_no,npc_no,*_ in RAIDS:
            base=f'v10400_raid_{number:02d}'
            if rooms[f'v10400_{slug}_{room_no:02d}']['exits'].get('east') != f'{base}_stage_1':
                raise RuntimeError(f'Rajdy v104: utracone wejście {number}')
            for stage in (1,2,3):
                if f'{base}_raid_quest_{stage}' not in npcs[f'v10400_{slug}_npc_{npc_no}']['specialist_quests']:
                    raise RuntimeError(f'Rajdy v104: brak oferty NPC {number}')
        return {'raids':0,'rooms':0,'bosses':0,'quests':0,'items':0,'recipes':0,
                'reason':'already installed'}

    if len(RAIDS)!=14 or {row[0] for row in RAIDS}!=set(range(12,26)):
        raise RuntimeError('Rajdy v104: niepełny katalog 12–25')
    for kind, registry in (('rooms',rooms),('mobs',mobs),('quests',quests),
                           ('items',items),('recipes',recipes)):
        overlap=planned[kind].intersection(registry)
        if overlap:
            raise RuntimeError(f'Rajdy v104: kolizja {kind}: {sorted(overlap)[0]}')
    for number,slug,room_no,npc_no,*_ in RAIDS:
        rid=f'v10400_{slug}_{room_no:02d}'
        nid=f'v10400_{slug}_npc_{npc_no}'
        if rid not in rooms or nid not in npcs:
            raise RuntimeError(f'Rajdy v104: brak krainy lub NPC {number}')
        if rooms[rid].get('exits',{}).get('east') is not None:
            raise RuntimeError(f'Rajdy v104: zajęte wejście na rajd {number}')
        if not isinstance(npcs[nid].get('specialist_quests'),(list,tuple)):
            raise RuntimeError(f'Rajdy v104: niewłaściwa lista NPC {number}')
    if len({(slug,room_no) for _,slug,room_no,*_ in RAIDS}) != len(RAIDS):
        raise RuntimeError('Rajdy v104: powtórzony pokój wejściowy')
    if len({(slug,npc_no) for _,slug,_,npc_no,*_ in RAIDS}) != len(RAIDS):
        raise RuntimeError('Rajdy v104: NPC może oferować tylko jedną serię rajdową')

    by_region={region[0]:region for region in REGIONS}
    for number,slug,room_no,npc_no,raid_name,mechanic,cycle in RAIDS:
        prefix=f'v10400_raid_{number:02d}'
        _,region_name,low,high,*_=by_region[slug]
        entry=f'v10400_{slug}_{room_no:02d}'
        nid=f'v10400_{slug}_npc_{npc_no}'
        npc=npcs[nid]
        rooms[entry]['exits']['east']=f'{prefix}_stage_1'
        fragment=f'{prefix}_fragment'
        seal=f'{prefix}_seal'
        relic=f'{prefix}_relic'
        items[fragment]={'name':f'Fragment: {raid_name}', 'type':'craft_material',
                         'price':None,'sell_gold':200+(number-11)*80,
                         'desc':f'Odłamek z rajdu {number}. Potrzebny do relikwii.'}
        items[seal]={'name':f'Pieczęć: {raid_name}', 'type':'craft_material',
                     'price':None,'sell_gold':450+(number-11)*100,
                     'desc':f'Pieczęć suwerena rajdu {number}.'}
        items[relic]={'name':f'Relikwia {raid_name}', 'type':'armor','slot':'charm',
                      'rarity':'legendary','defense':low*4+number*150,
                      'price':None,'desc':f'Unikalna relikwia z rajdu {number}: {mechanic}.'}
        recipes[relic]={'name':f'Relikwia {raid_name}', 'stations':('forge',),'category':'raid_relic',
                        'ingredients':{fragment:3,seal:1,f'v10400_{slug}_material_3':2,'steel_ingot':1},
                        'output':relic,'quantity':1,'profession':'Kowalstwo',
                        'generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                        'desc':f'Wykorzystaj fragmenty i pieczęć rajdu {number}.'}
        offers=list(npc['specialist_quests'])
        for stage,stage_name in enumerate(STAGE_NAMES,1):
            rid=f'{prefix}_stage_{stage}'
            mid=f'{prefix}_boss_{stage}'
            qid=f'{prefix}_raid_quest_{stage}'
            level=low+((high-low)*(stage-1))//2
            exits={'west':entry} if stage==1 else {'south':f'{prefix}_stage_{stage-1}'}
            if stage<3:
                exits['north']=f'{prefix}_stage_{stage+1}'
            rooms[rid]={
                'zone':region_name,'name':f'Rajd {number}: {raid_name} — etap {stage}/3',
                'desc':f'{mechanic.capitalize()}. {stage_name}. Boss ma 4 fazy HP: '
                       '80%, 60%, 40%, 20%. Wyjście powrotne jest zawsze dostępne. '
                       'Dalsze questy wymagają ukończenia poprzedniego.',
                'generator_level':level,'recommended_mastery':level,'exits':exits,
            }
            phases=_boss_phases(raid_name,stage)
            strategy=_phase_strategy(cycle,stage)
            hp=(6_000_000+level*22_000)*(stage+1)
            damage=(4_000+level*16)*(stage+1)
            mobs[mid]={
                'name':f'{raid_name}: {stage_name}',
                'boss':True,'world_boss':True,
                'boss_mechanic_text':f'{mechanic}; fazy HP 80/60/40/20.',
                'olc_boss_phases':phases,
                'olc_boss_guardian_interval':max(2,6-stage),
                'olc_boss_tactic_interval':max(2,6-stage),
                'olc_boss_support_interval':max(2,6-stage),
                'olc_boss_element_cycle':list(cycle),
                **strategy,
                'generator_level':level,'max_hp':hp,'damage':damage,
                'damage_type':'magic' if stage!=2 else 'physical',
                'class_xp_reward':max(1_000_000,level*6000*stage),
                'soul_reward':max(1_000_000,level*4700*stage),
                'stat_reward':max(1_000_000,level*3600*stage),
                'gold':1000+number*200+stage*300,
                'silver':15000+number*1100,
                'mithril':number+stage,
                'drops':{fragment:1.0, f'v10400_{slug}_material_3':0.50,
                         **({seal:1.0} if stage==3 else {})},
                'endgame_region_mastery':level,'quest_target':mid,
                'leave_corpse':True,
            }
            validate_boss_phases(mobs[mid],phases)
            spawns.append((rid,mid))
            quests[qid]={
                'name':f'Rajd {number}: {raid_name} — etap {stage}/3',
                'giver':npc['name'],'kind':'kill','target':mid,'needed':1,
                'description':f'Pokonaj {mobs[mid]["name"]}; wróć do {npc["name"]}. '
                              'W drużynie postęp jest przypisywany osobno każdemu uczestnikowi.',
                'generator_level':level,
                'reward_stat_progress':max(1_000_000,level*2900*stage),
                'reward_gold':1000+number*300+stage*400,
                'reward_mithril':number+stage,
                'reward_items':{fragment:1},
                **({'requires_quest':f'{prefix}_raid_quest_{stage-1}'} if stage>1 else {}),
            }
            offers.append(qid)
        npc['specialist_quests']=tuple(offers)
        # Nie zmieniamy quest_chain ani domyślnej oferty NPC z etapu 2.
    return {'raids':14,'rooms':len(planned['rooms']),'bosses':len(planned['mobs']),
            'quests':len(planned['quests']),'items':len(planned['items']),
            'recipes':len(planned['recipes'])}
