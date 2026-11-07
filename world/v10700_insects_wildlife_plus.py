# -*- coding: utf-8 -*-
"""v107 staging phase 7: a second additive insect expansion for Chitynowy Tron.

All extra rooms hang off the v107 phase-6 insect rooms, never raid sectors.
Keeps legacy and phase-6 IDs and rewards stable and never touches saved players.
"""
from __future__ import annotations

from data.catalog_mutations import catalog_assign, catalog_set_path
from world.legends_v3100 import OPPOSITE
from world.v10700_insects_expansion import PREFIX as PREV, ZONE

PREFIX = 'v10700_insects_plus'

# key, parent room phase6, name, Polish description
HABITATS = (
    ('royal_nest', 'hornets', 'Koronne Gniazdo Szerszeni',
     'Warstwowe gniazda z pergaminowych plastrów. Patrole strzegą królewskiej komory.'),
    ('wasp_forest', 'bees', 'Las Papierowych Os',
     'Wysoko pod koronami wiszą papierowe kokony. Osy wypatrują intruzów.'),
    ('amber_bark', 'beetles', 'Bursztynowy Zagajnik Żuków',
     'W pniach migocze żywica, a barwne chrząszcze drążą głębokie korytarze.'),
    ('grass_mimics', 'locusts', 'Gąszcz Patyczaków',
     'Gałęzie poruszają się niespodziewanie: owady ukrywają się jak liście.'),
    ('pond', 'marsh', 'Staw Wodnych Owadów',
     'Po tafli biegną nartniki, a pod powierzchnią czyhają drapieżne larwy.'),
    ('fossil_clay', 'ants', 'Gliniaste Kopce Mrówkolwów',
     'Lejki w piasku, gniazda turkuci i zapadnięte kopce skrywają drapieżników.'),
    ('night_bloom', 'moths', 'Ogród Nocnego Pyłku',
     'Nocą kwiaty świecą. Ćmy i chrząszcze zbierają drobiny nektaru.'),
    ('hunter_den', 'mantis', 'Przesmyk Drapieżnych Owadów',
     'W cieniu liści modliszki i osy pasożytnicze czekają na zdobycz.'),
)

# slug, name, habitat index, element, new material, level, tier. 21 ordinary and 3 elites.
INSECTS = (
    ('hornet_royal', 'Szerszeń Królewski', 0, 'poison', 'pheromone', 205, 'normal'),
    ('hornet_storm', 'Szerszeń Piorunowy', 0, 'lightning', 'pheromone', 217, 'normal'),
    ('hornet_tunnel', 'Szerszeń Tunelowy', 0, 'physical', 'resin', 188, 'normal'),
    ('wasp_paper', 'Osa Papierowa', 1, 'physical', 'resin', 180, 'normal'),
    ('wasp_parasite', 'Osa Gąsienicznik', 1, 'poison', 'pheromone', 202, 'normal'),
    ('wasp_red', 'Osa Czerwonoskrzydła', 1, 'fire', 'nectar', 207, 'normal'),
    ('beetle_jewel', 'Chrząszcz Klejnotnik', 2, 'arcane', 'resin', 193, 'normal'),
    ('beetle_longhorn', 'Chrząszcz Kózkowaty', 2, 'physical', 'bark', 184, 'normal'),
    ('beetle_click', 'Sprężyk Piorunowy', 2, 'lightning', 'bark', 198, 'normal'),
    ('stick_insect', 'Patyczak Leśny', 3, 'physical', 'bark', 171, 'normal'),
    ('leaf_insect', 'Liściec Szmaragdowy', 3, 'holy', 'nectar', 190, 'normal'),
    ('katydid', 'Pasikonik Zwiadowca', 3, 'physical', 'bark', 177, 'normal'),
    ('water_strider', 'Nartnik Wodny', 4, 'physical', 'nectar', 175, 'normal'),
    ('water_bug', 'Pluskolec Wodny', 4, 'poison', 'pheromone', 190, 'normal'),
    ('mayfly', 'Jętka Blasku', 4, 'holy', 'nectar', 185, 'normal'),
    ('antlion', 'Mrówkolew Piaskowy', 5, 'physical', 'bark', 204, 'normal'),
    ('mole_cricket', 'Turkuć Podjadek', 5, 'physical', 'resin', 189, 'normal'),
    ('earwig', 'Skorek Pancerzony', 5, 'physical', 'bark', 182, 'normal'),
    ('moth_silk', 'Ćma Jedwabista', 6, 'shadow', 'nectar', 198, 'normal'),
    ('beetle_glow', 'Świetlik Olbrzymi', 6, 'holy', 'nectar', 201, 'normal'),
    ('mantis_orchid', 'Modliszka Storczykowa', 7, 'arcane', 'pheromone', 214, 'normal'),
    ('hornet_empress', 'Cesarzowa Szerszeni', 0, 'poison', 'pheromone', 246, 'elite'),
    ('beetle_king', 'Król Żuków Bursztynowych', 2, 'physical', 'resin', 238, 'elite'),
    ('mantis_archon', 'Arcyłowczyni Modliszek', 7, 'shadow', 'bark', 244, 'elite'),
)

MATERIALS = (
    ('pheromone', 'Feromon Królewskiego Roju', 'Aromatyczna substancja z królewskich komór.'),
    ('resin', 'Bursztynowa Żywica', 'Twardniejąca żywica zbierana z owadzich gniazd.'),
    ('bark', 'Chitynowa Kora', 'Wytrzymały fragment pancerza przypominający drewno.'),
    ('nectar', 'Nektar Nocnych Kwiatów', 'Świetlisty nektar z ogrodów owadów.'),
)

# 13 ordinary hunts + all 3 elite hunts, all explicitly spawned and solo-capable.
HUNTS = (0, 1, 2, 3, 4, 6, 7, 9, 10, 12, 14, 15, 20, 21, 22, 23)


def planned_ids():
    return {
        'rooms': {f'{PREFIX}_{slug}' for slug, *_ in HABITATS},
        'mobs': {f'{PREFIX}_{slug}' for slug, *_ in INSECTS},
        'items': {f'{PREFIX}_{slug}' for slug, *_ in MATERIALS},
        'npcs': {f'{PREFIX}_entomologist', f'{PREFIX}_warden'},
        'quests': {f'{PREFIX}_hunt_{i:02d}' for i in range(1, 17)} |
                  {f'{PREFIX}_collect_{i:02d}' for i in range(1, 5)},
    }


def install(rooms, mobs, spawns, npcs, quests, items, help_topics, help_aliases):
    """Add eight rooms, 24 creatures, 4 materials and 20 solo quests.

    Preflight all identifiers and exits before making mutations. Idempotent when
    every phase-7 record is already present. No existing catalog entry deleted.
    """
    ids = planned_ids()
    catalogs = {'rooms': rooms, 'mobs': mobs, 'items': items,
                'npcs': npcs, 'quests': quests}
    existing = {key: required & catalogs[key].keys() for key, required in ids.items()}
    if any(existing.values()):
        if not all(existing[key] == ids[key] for key in ids):
            raise RuntimeError('v107 Owady PLUS: niepełny katalog; odmawiam nadpisywania')
        for slug, parent, *_ in HABITATS:
            target = f'{PREFIX}_{slug}'
            source = f'{PREV}_{parent}'
            if target not in rooms.get(source, {}).get('exits', {}).values() or source not in rooms[target].get('exits', {}).values():
                raise RuntimeError('v107 Owady PLUS: niepełne połączenie')
        return {'already_installed': True, 'rooms': 0, 'mobs': 0,
                'spawns': 0, 'items': 0, 'npcs': 0, 'quests': 0}
    if len(INSECTS) != 24 or len({r[0] for r in INSECTS}) != 24 or sum(r[-1]=='elite' for r in INSECTS) != 3:
        raise RuntimeError('v107 Owady PLUS: błędny katalog owadów')
    if f'{PREFIX}_region' in help_topics or any(key in help_aliases for key in ('owady_plus', 'szerszenie')):
        raise RuntimeError('v107 Owady PLUS: kolizja pomocy')
    if not all(rooms.get(f'{PREV}_{parent}', {}).get('zone') == ZONE for _, parent, *_ in HABITATS):
        raise RuntimeError('v107 Owady PLUS: najpierw zainstaluj etap 6 Krainy Owadów')
    if not all(f'{PREV}_{key}' in items for key in ('chitin','wing')):
        raise RuntimeError('v107 Owady PLUS: brak zachowanych surowców z etapu 6')
    if 'soul_shard' not in items:
        raise RuntimeError('v107 Owady PLUS: brak odłamka duszy')
    for slug, *_ in MATERIALS:
        if slug not in {record[4] for record in INSECTS}:
            raise RuntimeError(f'v107 Owady PLUS: brak potworów z surowcem {slug}')

    directions = ('up','down','northeast','southeast','northwest','southwest',
                  'north','east','south','west')
    links=[]
    reserved=set()
    for slug, parent, *_ in HABITATS:
        source = f'{PREV}_{parent}'
        exits = rooms[source].get('exits', {})
        direction = next((d for d in directions if d not in exits and (source,d) not in reserved),None)
        if direction is None:
            raise RuntimeError(f'v107 Owady PLUS: nie ma wolnego wyjścia z {source}')
        links.append((source,direction,f'{PREFIX}_{slug}'))
        reserved.add((source,direction))

    def add(catalog, code, key, record):
        catalog_assign(record, code, catalog, (key,))

    for slug, name, desc in MATERIALS:
        add(items,'ITEMS',f'{PREFIX}_{slug}', {
            'name':name,'type':'craft_material','price':None,'sell_gold':5,
            'desc':desc,'v107_insects_plus':True,
        })
    for index, ((slug, _, name, desc), (source,direction,dest)) in enumerate(zip(HABITATS,links)):
        add(rooms,'ROOMS',dest, {
            'name':name,'zone':ZONE,'desc':desc,
            'exits':{OPPOSITE[direction]:source},'generator_level':180+index*7,
            'recommended_mastery':120,'v107_insects_plus':True,
        })
        catalog_set_path('ROOMS',rooms,(source,'exits',direction),dest)

    for slug, name, habitat, element, material, stage, tier in INSECTS:
        elite = tier=='elite'
        mid = f'{PREFIX}_{slug}'
        drops={f'{PREV}_chitin': .65 if elite else .30,
               'soul_shard': .60 if elite else .17,
               f'{PREFIX}_{material}':1.0 if elite else .65}
        add(mobs,'MOB_TEMPLATES',mid,{
            'name':name,'generator_level':stage,
            'max_hp':stage*(420 if elite else 140),
            'damage':stage*(8 if elite else 5),
            'damage_type':'physical' if element=='physical' else 'magic',
            'attack_elements_v11339':() if element=='physical' else (element,),
            'stat_reward':stage*(180 if elite else 55),
            'class_xp_reward':stage*(9000 if elite else 2100),
            'soul_reward':stage*(3100 if elite else 750),
            'silver':stage*(2200 if elite else 450),
            'gold':0,'mithril':0,'rank':tier,'boss':elite,'world_boss':False,
            'quest_target':mid,'stationary_mob':True,'auto_aggro':False,
            'drops':drops,'v107_insects_plus':True,
        })
        spawns.append((f'{PREFIX}_{HABITATS[habitat][0]}',mid))
        if not elite:
            spawns.append((f'{PREV}_{HABITATS[habitat][1]}',mid))

    researcher='Entomolożka Wera'
    guardian='Strażnik Sadu Halik'
    quest_records=[]
    for index,insect_idx in enumerate(HUNTS,1):
        slug, name, _, _, material, stage, tier=INSECTS[insect_idx]
        giver=researcher if index<=9 else guardian
        required=1 if tier=='elite' else 4
        repeatable=tier!='elite'
        qid=f'{PREFIX}_hunt_{index:02d}'
        quest_records.append((qid,giver,'kill',f'{PREFIX}_{slug}',required,
                              f'Pokonaj {required} przeciwników: {name}. Wróć do {giver}.',
                              stage,repeatable,material))
    for index,(material,name,_) in enumerate(MATERIALS,1):
        qid=f'{PREFIX}_collect_{index:02d}'
        quest_records.append((qid,guardian,'collect',f'{PREFIX}_{material}',3,
                              f'Zdobądź 3 sztuki surowca: {name}. Wróć do {guardian}.',
                              190,True,material))
    for qid,giver,kind,target,needed,description,stage,repeatable,material in quest_records:
        add(quests,'QUESTS',qid,{
            'name':f'Kraina Owadów: {description.split(". ")[0]}',
            'giver':giver,'kind':kind,'target':target,'needed':needed,
            'description':description,'generator_level':stage,
            'character_xp_reward':stage*(3300 if repeatable else 9000),
            'reward_stat_progress':stage*900,
            'reward_silver':stage*(1700 if repeatable else 5000),
            'reward_gold':0,'reward_mithril':0,
            'reward_items':{f'{PREFIX}_{material}':2},
            'repeatable':repeatable,
            **({'repeat_cooldown':3600} if repeatable else {}),
            'v107_insects_plus':True,
        })
    add(npcs,'NPCS',f'{PREFIX}_entomologist',{
        'name':researcher,'room':f'{PREFIX}_royal_nest',
        'dialogue':'Badam szerszenie i inne gatunki. Wpisz quest list.',
        'specialist_quests':tuple(qid for qid,giver,*_ in quest_records if giver==researcher),
        'v107_insects_plus':True,
    })
    add(npcs,'NPCS',f'{PREFIX}_warden',{
        'name':guardian,'room':f'{PREFIX}_night_bloom',
        'dialogue':'Szanuj stare gniazda i zbieraj owadzie surowce. Wpisz quest list.',
        'specialist_quests':tuple(qid for qid,giver,*_ in quest_records if giver==guardian),
        'v107_insects_plus':True,
    })
    help_topics[f'{PREFIX}_region']=[
        'Kraina Owadów — Chitynowy Tron. Drugie rozszerzenie: szerszenie i owady leśne.',
        'Dodatkowe 8 lokacji odchodzących od istniejących bocznych ścieżek.',
        'Szerszeń Królewski, Szerszeń Piorunowy, Cesarzowa Szerszeni, osy, chrząszcze, patyczaki i owady wodne.',
        'Nowe zadania: Entomolożka Wera w Koronnym Gnieździe; Strażnik Sadu Halik w Ogrodzie Nocnego Pyłku.',
        'Brak rajdów i auto-agro. Każda walka oraz polowanie mogą być wykonane solo.',
    ]
    help_aliases['owady_plus']=f'{PREFIX}_region'
    help_aliases['szerszenie']=f'{PREFIX}_region'
    return {'already_installed':False,'rooms':len(HABITATS),
            'mobs':len(INSECTS),'spawns':len(INSECTS)*2-3,
            'items':len(MATERIALS),'npcs':2,'quests':len(quest_records),
            'elite_mobs':3,'raids':0}
