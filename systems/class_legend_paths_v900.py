# -*- coding: utf-8 -*-
"""v9.00.0: 8 x 120 real class sagas, additive to the 14 historic paths."""
from systems.new_heroes_v900 import NEW_CLASSES
from systems.class_legend_paths_v800 import CHAPTERS,STAGE_TYPES,stage_level,_anchors,_attach,_insert

QUEST_IDS = {}
MENTOR_ROOMS = {}
ALL_IDS = []
MATERIALS = ('iron_ore','oak_plank','navigation_chart','stone_chunk','mint','mint','oak_plank','mint')

def install(rooms,npcs,quests,items,help_topics):
    if ALL_IDS:raise RuntimeError('v9 paths already installed')
    from core.classes_skills import CLASSES
    assert len(CLASSES)==22
    # Leave city hubs and NPC/shop infrastructure untouched: historical NPC
    # relocation later needs spare directions in the market and other hubs.
    # A small, otherwise empty connected road is the safe entry anchor.
    occupied={str(row.get('room')) for row in npcs.values()}
    forbidden={'temple','market','forge','meadow','mint_meadow','harbor',
               'lakeside_meadow','sea_pier','town_square','guild_hall','forest_path'}
    roads=[rid for rid in _anchors(rooms,130)
           if rid not in forbidden and rid not in occupied
           and not rooms[rid].get('v800_class_mentor_room')
           and not rooms[rid].get('v900_mentor_room')
           and not rooms[rid].get('v900_teacher_room')
           and not rooms[rid].get('v601_profession_mentor')
           and not rooms[rid].get('v700_story_room')
           and len(rooms[rid].get('exits',{}))<=3]
    anchors=roads[:len(NEW_CLASSES)]
    if len(anchors)!=len(NEW_CLASSES):raise RuntimeError('v9 inaccessible mentors')
    for n,(name,kind,weapon,power,slug,theme,scale,passive,value,element,titles) in enumerate(NEW_CLASSES):
        material=MATERIALS[n]
        if material not in items:raise RuntimeError('v9 missing material '+material)
        anchor=anchors[n]
        room_id='v900_legend_room_'+slug
        mentor='v900_legend_mentor_'+slug
        teacher_room='v900_teacher_room_'+slug
        teacher='teacher_v900_'+slug
        mentor_name='Mistrz Drogi Legendy '+name
        _insert(rooms,'ROOMS',room_id,{
            'zone':rooms[anchor].get('zone','Miasto Dusz'),
            'name':'Izba Legendy '+name,
            'desc':f'Droga Legendy klasy {name}, 120 prób. quest list; przyjmij 1; oddaj quest.',
            'exits':{},'v900_mentor_room':True})
        _attach(rooms,anchor,room_id)
        _insert(rooms,'ROOMS',teacher_room,{
            'zone':rooms[anchor].get('zone','Miasto Dusz'),
            'name':'Sala Nauczyciela '+name,
            'desc':f'Nauczyciel umiejętności klasy {name}. learn pokazuje dostępne umiejętności.',
            'exits':{},'v900_teacher_room':True})
        _attach(rooms,room_id,teacher_room)
        ids=[];previous=None
        for index in range(120):
            stage=index+1;chapter=index//10;within=index%10;level=stage_level(index)
            qkind=STAGE_TYPES[within]
            needed=(2+index//15) if qkind=='collect' else (3+index//12) if qkind=='kill' else (2+index//35)
            rank=('boss' if qkind=='kill' and within==9 else 'elite' if qkind=='kill' and within==4 else 'any')
            minimum=min(600,max(1,level//2)) if qkind=='kill' else 0
            if qkind=='explore_frontier':
                target='any';objective=f'Odkryj {needed} nowych fragmentów terenów proceduralnych.'
            elif qkind=='collect':
                target=material;objective=f'Pozyskaj {needed} sztuk surowca {items[material]["name"]} po przyjęciu zadania.'
            else:
                target='*';objective=f'Pokonaj {needed} rzeczywistych przeciwników rangi {rank} od poziomu {minimum}.'
            qid=f'v900_legend_{slug}_{stage:03d}'
            quest={
                'name':f'{name}: {CHAPTERS[chapter]} — Próba {within+1}',
                'giver':mentor_name,'kind':qkind,'target':target,'needed':needed,
                'description':f'Droga Legendy {name}, etap {stage}/120. {theme}. {objective} '
                              f'Poziom orientacyjny {level}. Nagroda u mistrza.',
                'required_class':name,'generator_level':level,
                'reward_silver':2400+level*155+index*200,
                'reward_gold':0,'reward_mithril':0,
                'reward_items':({'silver_ingot':1+chapter//4} if within==9 else {}),
                'repeatable':False,'v800_class_saga':True,
                'v800_stage':stage,'v800_min_enemy_level':minimum,'v800_enemy_rank':rank,
                'v900_class_saga':True}
            if previous:quest['requires_quest']=previous
            _insert(quests,'QUESTS',qid,quest)
            ids.append(qid);ALL_IDS.append(qid);previous=qid
        _insert(npcs,'NPCS',mentor,{
            'name':mentor_name,'room':room_id,
            'dialogue':f'Droga Legendy {name}: 120 etapów od 1 do 800. quest list; przyjmij 1.',
            'specialist_quests':tuple(ids),
            'v800_class_mentor':True,'v800_required_class':name})
        _insert(npcs,'NPCS',teacher,{
            'name':'Nauczyciel '+name,'room':teacher_room,'teacher_class':name,
            'dialogue':f'Prawdziwa nauka umiejętności klasy {name}; wpisz learn.'})
        QUEST_IDS[name]=tuple(ids);MENTOR_ROOMS[name]=room_id
    assert len(ALL_IDS)==960 and len(QUEST_IDS)==8
    help_topics['nowe klasy v9']=[
        'v9.00.0: 22 klasy i 22 rasy. Jedna klasa na postać; Mec jedyną hybrydą.',
        'Paladyn, Samuraj, Korsarz, Gladiator — klasy fizyczne.',
        'Chronomanta, Iluzjonista, Bard, Szaman — klasy magiczne.',
        'Każda nowa klasa ma własną Broń Duszy, nauczyciela, EQ i 120 prób Drogi Legendy.',
        'Nauczyciel i mentor mają osobne pomieszczenia, podłączone do świata.',
        'quest list; przyjmij 1; oddaj quest; learn; bron duszy.',
    ]
    return {'classes':8,'quests':960,'npcs':16,'rooms':16}
