# -*- coding: utf-8 -*-
"""v8.00.0: 14 distinct native class quest paths, 120 stages each.

No new playable classes, skills, shops or destructive migrations.
Uses persistent original quests table; each path has a private reachable mentor.
"""
from __future__ import annotations
from collections import defaultdict
from systems.npc_single_room_v3101 import OPPOSITE
from data.catalog_mutations import catalog_assign

CLASSES = (
    ('Wojownik','wojownik','Bohater Żelaznej Przysięgi','żelazne starcia i obrona przymierza','iron_ore'),
    ('Berserker','berserker','Dziedzic Gniewu','wytrwałość w najgroźniejszych bitwach','stone_chunk'),
    ('Łotrzyk','lotrzyk','Cień Bez Imienia','polowania na nieuchwytnych łupieżców','mint'),
    ('Łowca','lowca','Strażnik Dziewięciu Tropów','wyprawy na dzikie rubieże','oak_plank'),
    ('Mnich','mnich','Pielgrzym Wewnętrznej Siły','próby ducha i wytrzymałości','mint'),
    ('Strażnik','straznik','Bastion Żyjących','ochrona granic świata','iron_ore'),
    ('Mag','mag','Arcymistrz Runicznych Gwiazd','badanie żywiołów i starożytnej magii','mint'),
    ('Nekromanta','nekromanta','Władca Zapomnianych Dusz','tajemnice zaświatów i cieni','stone_chunk'),
    ('Kapłan','kaplan','Niosący Ostatni Świt','oczyszczenie przeklętych ziem','mint'),
    ('Czarownik','czarownik','Tkacz Szczelin Chaosu','zgłębianie sił chaosu','iron_ore'),
    ('Druid','druid','Serce Pierwszego Lasu','ochrona dzikich ostępów','oak_plank'),
    ('Psionik','psionik','Wędrowiec Przez Umysły','poznawanie tajemnic pamięci','mint'),
    ('Mec','mec','Obrońca Dwóch Energii','mechanika, magia i siła w jednym','iron_ore'),
    ('Inżynier','inzynier','Architekt Runicznej Obrony','starożytne mechanizmy i wyprawy','stone_chunk'),
)
CHAPTERS = (
    'Pierwsza Przysięga', 'Szlak Początkującego', 'Żywe Rubieże',
    'Duch Dawnych Wojen', 'Brama Wyzwań', 'Pieśń Bohaterów',
    'Ziemie Pradawnych', 'Wrota Półmroku', 'Czempion Krain',
    'Pamięć Nieśmiertelnych', 'Próba Wielkiej Legendy', 'Dziedzictwo Bez Kresu',
)
# Each ten-stage chapter has real fights, frontier discovery, supply collection,
# and its concluding elite/boss challenge. No automatic completion on accept.
STAGE_TYPES = ('kill','kill','explore_frontier','collect','kill',
               'explore_frontier','kill','collect','kill','kill')
QUEST_IDS = {}
MENTOR_ROOMS = {}
ALL_IDS = []

def stage_level(index):
    if not 0 <= index < 120: raise ValueError(index)
    return 1 + (799 * index) // 119

def _insert(catalog, name, key, value):
    if key in catalog:
        raise RuntimeError('v8.00.0 collision '+name+': '+key)
    catalog_assign(value,name,catalog,(key,))

def _attach(rooms, anchor, target):
    for way in ('north','south','east','west','northeast','northwest','southeast','southwest','up','down'):
        back=OPPOSITE[way]
        if way not in rooms[anchor]['exits'] and back not in rooms[target]['exits']:
            catalog_assign(target,'ROOMS',rooms,(anchor,'exits',way))
            catalog_assign(anchor,'ROOMS',rooms,(target,'exits',back))
            return way
    raise RuntimeError('v8: no safe mentor exit at '+anchor)

def _anchors(rooms, count):
    # Prefer known, connected legacy settlements/roads; never break existing exits.
    preferred=('temple','market','forge','meadow','mint_meadow','harbor',
               'lakeside_meadow','sea_pier','town_square','guild_hall','forest_path')
    seen=set()
    candidates=[]
    for rid in preferred:
        if rid in rooms and rid not in seen:
            seen.add(rid)
            candidates.append(rid)
    # Extend only along existing paths from temple; deterministic and walkable.
    queue=['temple'] if 'temple' in rooms else list(candidates[:1])
    visited=set(queue)
    for rid in queue:
        if len(queue)>250:break
        for nxt in rooms[rid].get('exits',{}).values():
            if nxt in rooms and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
                if nxt not in seen:
                    seen.add(nxt)
                    candidates.append(nxt)
    open_rooms=[rid for rid in candidates if isinstance(rooms[rid].get('exits'),dict) and
                len(rooms[rid]['exits']) < len(OPPOSITE) and not rooms[rid].get('v601_profession_mentor')
                and not rooms[rid].get('v700_story_room')]
    if len(open_rooms)<count: raise RuntimeError('v8: not enough reachable mentor anchors')
    return open_rooms[:count]

def install(rooms,npcs,quests,items,help_topics):
    if ALL_IDS:raise RuntimeError('v8: double install')
    from core.classes_skills import CLASSES as EXISTING_CLASSES
    existing={row[0] for row in EXISTING_CLASSES}
    if existing != {c[0] for c in CLASSES}:raise RuntimeError('v8: 14 playable classes mismatch')
    for _name,_key,_title,_topic,material in CLASSES:
        if material not in items: raise RuntimeError('v8: missing accessible supply '+material)
    anchors=_anchors(rooms,len(CLASSES))
    for n,(class_name,slug,epithet,subject,material) in enumerate(CLASSES):
        anchor=anchors[n]
        rid='v800_class_mentor_room_'+slug
        npc_id='v800_class_mentor_'+slug
        npc_name='Mistrz Drogi Legendy '+class_name
        _insert(rooms,'ROOMS',rid,{
            'zone':rooms[anchor].get('zone','Miasto Dusz'),
            'name':'Izba Drogi Legendy — '+class_name,
            'desc':f'{npc_name} opowiada o drodze klasy {class_name}. '
                   '120 zadań w 12 rozdziałach. Lista pokazuje tylko bieżący etap. '
                   'Komendy: quest list, przyjmij 1, quest info 1, oddaj quest.',
            'exits':{},'generator_level':1,'v800_class_mentor_room':True,
        })
        _attach(rooms,anchor,rid)
        quest_ids=[]
        previous=None
        for index in range(120):
            number=index+1
            chapter=index//10
            within=index%10
            level=stage_level(index)
            kind=STAGE_TYPES[within]
            needed = (2+index//15) if kind=='collect' else (3+index//12) if kind=='kill' else (2+index//35)
            boss = kind=='kill' and within==9
            elite = kind=='kill' and within==4
            # Intentionally do not demand a level above the generated world's
            # reliably accessible high areas. High stages still need bosses and
            # many genuine victories; no synthetic combat progress is allowed.
            minimum_enemy = min(600,max(1,level//2))
            if kind=='explore_frontier':
                objective=f'Odkryj {needed} nowych fragmentów terenów proceduralnych podczas eksploracji.'
                target='any'
            elif kind=='collect':
                target=material
                objective=f'Pozyskaj po przyjęciu zadania {needed} sztuk surowca: {items[material]["name"]}. Zachowaj je do oddania.'
            else:
                target='*'
                rank='bossa' if boss else 'elitarnego przeciwnika' if elite else 'przeciwnika'
                objective=f'Pokonaj {needed} razy {rank} na rzeczywistym świecie lub w lochach; poziom wroga co najmniej {minimum_enemy}.'
            quest_id=f'v800_legend_{slug}_{number:03d}'
            title=f'{class_name} — {CHAPTERS[chapter]}, próba {within+1}: {epithet}'
            quest={
                'name':title,'giver':npc_name,'kind':kind,'target':target,'needed':needed,
                'description':f'Droga Legendy {number}/120. {subject.capitalize()}. '
                              f'{objective} Etap na poziom orientacyjny {level}. '
                              'Wróć do swojego mistrza, aby odebrać nagrodę.',
                'required_class':class_name,'generator_level':level,
                'reward_silver':2400+level*155+index*200,
                'reward_gold':0,'reward_mithril':0,
                'reward_items':{'silver_ingot':1+chapter//4} if within==9 else {},
                'repeatable':False,
                'v800_class_saga':True,'v800_stage':number,
                'v800_min_enemy_level':minimum_enemy if kind=='kill' else 0,
                'v800_enemy_rank':'boss' if boss else 'elite' if elite else 'any',
            }
            if previous:quest['requires_quest']=previous
            _insert(quests,'QUESTS',quest_id,quest)
            quest_ids.append(quest_id)
            ALL_IDS.append(quest_id)
            previous=quest_id
        _insert(npcs,'NPCS',npc_id,{
            'name':npc_name,'room':rid,'dialogue':f'{npc_name}: {epithet}. '
                      f'Przed Tobą 120 prób klasy {class_name}, od poziomu 1 do 800. '
                      'Wpisz quest list i przyjmij 1. Nie możesz wykonywać prób innych klas.',
            'specialist_quests':tuple(quest_ids),
            'v800_class_mentor':True,'v800_required_class':class_name,
        })
        QUEST_IDS[class_name]=tuple(quest_ids)
        MENTOR_ROOMS[class_name]=rid
    if len(ALL_IDS)!=1680 or any(len(v)!=120 for v in QUEST_IDS.values()):
        raise RuntimeError('v8: unfinished class journeys')
    help_topics['droga legendy']=[
        'Droga Legendy: 120 niepowtarzalnych zadań dla każdej z 14 klas. Jedna klasa na postać.',
        'Znajdź swojego Mistrza Drogi Legendy w izbie połączonej z istniejącym światem.',
        'U mistrza: quest list; przyjmij 1; quest info 1; po wykonaniu: oddaj quest.',
        'Cele: realne zwycięstwa, elity i bossowie, odkrywanie terenów i pozyskiwanie zasobów.',
        'Postęp zapisuje się automatycznie w SQLite, tylko właściwa klasa może przyjąć etap.',
        'Lista pokazuje wyłącznie aktualną próbę; ukończone etapy nie zalewają czytnika NVDA.',
    ]
    return {'classes':14,'quests':len(ALL_IDS),'per_class':120,'npcs':14,'rooms':14}
