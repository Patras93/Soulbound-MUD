# -*- coding: utf-8 -*-
"""v9.00.0: 8 x 120 real class sagas, additive to the 14 historic paths."""
from systems.new_heroes_v900 import NEW_CLASSES
from systems.class_legend_paths_v800 import CHAPTERS,STAGE_TYPES,stage_level,_anchors,_attach,_insert

QUEST_IDS = {}
MENTOR_ROOMS = {}
ALL_IDS = []
# v11.00.12: named mentors retain separate rooms; their three short lessons
# complement rather than replace the 120-step class legend sagas.
TEACHER_NAMES = {
    'Paladyn': 'Mistrzyni Serafina',
    'Samuraj': 'Mistrz Hiroto',
    'Korsarz': 'Kapitan Roksana',
    'Gladiator': 'Mistrz Aureliusz',
    'Chronomanta': 'Mistrzyni Eona',
    'Iluzjonista': 'Mistrzyni Miraluna',
    'Bard': 'Mistrz Arion',
    'Szaman': 'Mistrzyni Nalara',
}
# Verified existing quest target categories (also used by hourly contracts).
# Entries are deliberately class-specific and require genuine kills.
TEACHER_TRIALS = {
    'Paladyn': ('skeleton', 'shadow_wolf', 'Ochrona Pielgrzymów', 'Sztandar Świtu'),
    'Samuraj': ('bandit', 'goblin', 'Porządek Ostrza', 'Próba Ostrza Honoru'),
    'Korsarz': ('goblin', 'bandit', 'Patrol Wybrzeża', 'Odbicie Łupów'),
    'Gladiator': ('goblin', 'skeleton', 'Pierwszy Pojedynek', 'Próba Areny'),
    'Chronomanta': ('shadow_wolf', 'skeleton', 'Zakłócenia Czasu', 'Pieczęć Eonów'),
    'Iluzjonista': ('bandit', 'shadow_wolf', 'Zmylenie Tropów', 'Próba Zwierciadeł'),
    'Bard': ('goblin', 'bandit', 'Ballada o Szlaku', 'Pieśń Odwagi'),
    'Szaman': ('skeleton', 'shadow_wolf', 'Niespokojni Przodkowie', 'Krąg Duchów'),
}
TEACHER_QUEST_IDS = frozenset(
    f'v1112_teacher_{entry[4]}_{stage:02d}'
    for entry in NEW_CLASSES for stage in range(1, 4)
)
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
        # Each named teacher offers a short, real three-step class training.
        # No NPC is duplicated; the teacher stays in their own reachable room.
        first_target, final_target, first_title, final_title = TEACHER_TRIALS[name]
        teacher_name = TEACHER_NAMES[name]
        training_ids=[]
        for step in (1, 2, 3):
            qid = f'v1112_teacher_{slug}_{step:02d}'
            predecessor = training_ids[-1] if training_ids else None
            if step == 1:
                kind, target, needed = 'kill', first_target, 5
                title = first_title
                objective = (f'Pokonaj 5 prawdziwych przeciwników z kategorii {first_target} '
                             'po przyjęciu zadania. Każde zabójstwo zapisuje postęp.')
            elif step == 2:
                kind, target, needed = 'collect', material, 3
                title = f'Przygotowania: {theme}'
                objective = (f'Pozyskaj 3 sztuki: {items[material]["name"]}, '
                             'po przyjęciu zadania. Surowiec przynieś nauczycielowi.')
            else:
                kind, target, needed = 'kill', final_target, 8
                title = final_title
                objective = (f'Pokonaj 8 prawdziwych przeciwników z kategorii {final_target} '
                             'po przyjęciu zadania i wróć po nagrodę.')
            lesson = {
                'name': f'{name}: {title}', 'giver': teacher_name,
                'kind': kind, 'target': target, 'needed': needed,
                'required_class': name, 'required_npc_id': teacher,
                'description': (f'Próba nauczyciela {name}, etap {step}/3. '
                                f'{objective} Nauczyciel: {teacher_name}. '
                                'Quest jest oddawany u nauczyciela.'),
                'generator_level': (1, 10, 25)[step-1],
                'reward_silver': (1600, 2900, 5200)[step-1],
                'reward_gold': 0, 'reward_mithril': 0, 'reward_items': {},
                'repeatable': False, 'v1112_teacher_training': True,
            }
            if predecessor:
                lesson['requires_quest'] = predecessor
            _insert(quests, 'QUESTS', qid, lesson)
            training_ids.append(qid)
        _insert(npcs,'NPCS',teacher,{
            'name':teacher_name,'room':teacher_room,'teacher_class':name,
            'dialogue':(f'Uczę technik klasy {name}. Mam też trzy próby szkoleniowe: '
                        'walka, materiał i próba mistrzowska. '
                        'Wpisz quest list i przyjmij 1; do nauki skilli wpisz learn.'),
            'quest_chain': tuple(training_ids),
            'v1112_teacher_quests': True})
        # Existing `help klasa_<nazwa>` pages are created before v9 NPCs.
        # Update the live help topic at installation so help paladyn, help
        # samuraj, etc. never print the incorrect teacher value "brak".
        topic_key = 'klasa_' + slug
        for i, line in enumerate(help_topics.get(topic_key, ())):
            if str(line).startswith('Nauczyciel: '):
                help_topics[topic_key][i] = (
                    f'Nauczyciel: {teacher_name}. '
                    f'Lokacja: {rooms[teacher_room]["name"]}. '
                    'Ma 3 questy; quest list i przyjmij 1; learn uczy umiejętności.'
                )
                break
        QUEST_IDS[name]=tuple(ids);MENTOR_ROOMS[name]=room_id
    assert len(ALL_IDS)==960 and len(QUEST_IDS)==8
    assert len(TEACHER_QUEST_IDS) == 24
    help_topics['nauczyciele klas'] = [
        'Każda z 22 klas ma nauczyciela skilli. Osiem nowych klas ma także trzy indywidualne zadania u swojego imiennego nauczyciela.',
        'U nauczyciela: quest list, przyjmij 1, questy postep, oddaj quest; nauka umiejętności: learn.',
        'Próby: prawdziwa walka, zdobycie materiału i walka finałowa. Nagrody i postęp zapisuje SQLite.',
        'Droga Legendy 120 etapów pozostaje u oddzielnego Mistrza Drogi Legendy.',
    ]
    help_topics['nowe klasy v9']=[
        'v9.00.0: 22 klasy i 22 rasy. Jedna klasa na postać; Mec jedyną hybrydą.',
        'Paladyn, Samuraj, Korsarz, Gladiator — klasy fizyczne.',
        'Chronomanta, Iluzjonista, Bard, Szaman — klasy magiczne.',
        'Każda nowa klasa ma własną Broń Duszy, nauczyciela, EQ i 120 prób Drogi Legendy.',
        'Nauczyciel i mentor mają osobne pomieszczenia, podłączone do świata.',
        'quest list; przyjmij 1; oddaj quest; learn; bron duszy.',
    ]
    return {'classes':8,'quests':960,'npcs':16,'rooms':16}
