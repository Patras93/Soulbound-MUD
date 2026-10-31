# -*- coding: utf-8 -*-
"""Era Bez Granic, etap zawartosci: 11 fizycznych szlakow 801-5000.

Additive install. Nie ingeruje w zapis postaci, limity, ustawienia admina
ani poziom przeciwnikow zależny od graczy. Statystyki sa stale dla regionu.
"""
from __future__ import annotations

from core.classes_skills import CLASSES
# Mirrors the published v0.70 profession roster, but without importing its
# installer at module import (it requires NPCs from a later bootstrap phase).
PROFESSION_SPECS = (
    ('Wędkarstwo','fishing','wykonuj połowy'),
    ('Górnictwo','mining','wydobywaj surowce'),
    ('Drwalstwo','woodcutting','pozyskuj drewno'),
    ('Kowalstwo','crafting','pracuj przy kuźni'),
    ('Gotowanie','cooking','przygotowuj potrawy'),
    ('Zielarstwo','herbalism','zbieraj zioła'),
    ('Alchemia','alchemy','warz mikstury'),
    ('Jubilerstwo','jewelcrafting','twórz biżuterię'),
    ('Krawiectwo','tailoring','wykonuj prace krawieckie'),
    ('Garbarstwo','leatherworking','obrabiaj skóry'),
    ('Stolarstwo','carpentry','wykonuj prace stolarskie'),
    ('Zaklinanie','enchanting','wykonuj zaklęcia rzemieślnicze'),
    ('Archeologia','archaeology','prowadź wykopaliska'),
    ('Kartografia','cartography_profession','wykonuj pomiary'),
)

# (slug, name, low, high, theme, first boss, final boss)
ERAS = (
    ('swit', 'Bramy Nowego Świtu', 801, 1200, 'Przebudzone pieczęcie', 'Strażnik Zarania', 'Władca Złotych Bram'),
    ('kuznie', 'Wulkany Wiecznych Kuźni', 1201, 1600, 'Żywy żar', 'Tytan Płynnego Żelaza', 'Królowa Ognistej Kuźni'),
    ('gwiazdy', 'Morze Zerwanych Gwiazd', 1601, 2000, 'Rozbita konstelacja', 'Władczyni Rozbitych Gwiazd', 'Lewiatan Pustych Niebios'),
    ('echa', 'Pustkowie Tysiąca Ech', 2001, 2400, 'Głosy zapomnianych', 'Herold Echa', 'Sędzia Utraconych Imion'),
    ('runy', 'Cesarstwo Run i Stali', 2401, 2800, 'Pradawne runy', 'Imperator Run', 'Strażnik Żelaznego Tronu'),
    ('smoki', 'Korony Upadłych Smoków', 2801, 3200, 'Dziedzictwo smoczych rodów', 'Pierwszy Smoczy Regent', 'Serce Smoczego Gromu'),
    ('materia', 'Labirynt Żywej Materii', 3201, 3600, 'Zmieniający się świat', 'Serce Przemiany', 'Mistrz Żywego Kryształu'),
    ('dusza', 'Dziedzictwo Pierwotnej Duszy', 3601, 4000, 'Pierwotne imiona', 'Strażnik Pierwotnego Imienia', 'Władca Dwóch Dusz'),
    ('ogrody', 'Ogrody Niebiańskiej Otchłani', 4001, 4400, 'Rozdzielone żywioły', 'Królowa Dwóch Żywiołów', 'Ogrodnik Wiecznej Pustki'),
    ('czas', 'Cytadela Złamanego Czasu', 4401, 4800, 'Pęknięta chronologia', 'Mistrz Pętli Epok', 'Cień Ostatniej Godziny'),
    ('tron', 'Tron Tysiąca Epok', 4801, 5000, 'Ostateczne przekroczenie', 'Awatar Wiecznego Przekroczenia', 'Władca Tysiąca Epok'),
)

ROOM_PARTS = (
    'Brama', 'Przedmurze', 'Szlak Wędrowców', 'Ostoja Kronikarzy',
    'Rozdroże', 'Spękana Galeria', 'Pracownia Mistrzów', 'Taras Światła',
    'Próg Wyzwania', 'Arena Strażnika', 'Schody Przeznaczenia', 'Tron Finału',
)
ENEMY_PARTS = ('Zwiadowca', 'Żołnierz', 'Łowca', 'Widmo', 'Mściciel', 'Czarownik', 'Tytan', 'Strażnik')
MATERIAL_PARTS = ('Odłamek', 'Rdzeń', 'Pieczęć')


def install(rooms, mobs, spawns, npcs, quests, items, recipes, areas, zone_ids, categories, guides, target_power):
    """Instaluj 11 regionow addytywnie i deterministycznie; ponowny import no-op.

    All NPC rooms are distinct; quests never require an unspawned target.
    Use normal QUESTS / MOB_SPAWNS / ITEMS / CRAFT_RECIPES, no custom save tables.
    """
    first = 'v10300_swit_01'
    if first in rooms:
        return {'regions': 0, 'reason': 'already installed'}
    parent = 'v3000_eternal_6'
    if parent not in rooms:
        raise RuntimeError('Era Bez Granic: brak lacza do Tronu Wiecznosci')
    if 'east' in rooms[parent].get('exits', {}):
        raise RuntimeError('Era Bez Granic: zajete przejscie z Tronu Wiecznosci')
    # Before modifying registries check all generated IDs, so a collision
    # cannot leave a half-installed world.
    planned_rooms = {f'v10300_{slug}_{i:02d}' for slug, *_ in ERAS for i in range(1, 13)}
    planned_mobs = {f'v10300_{slug}_mob_{i}' for slug, *_ in ERAS for i in range(1, 9)}
    planned_mobs |= {f'v10300_{slug}_boss_{i}' for slug, *_ in ERAS for i in (1, 2)}
    planned_npcs = {f'v10300_{slug}_npc_{i}' for slug, *_ in ERAS for i in (1, 2, 3)}
    planned_items = {f'v10300_{slug}_{i}' for slug, *_ in ERAS for i in ('material_1','material_2','material_3','alloy','charm')}
    planned_recipes = {f'v10300_{slug}_{i}' for slug, *_ in ERAS for i in ('alloy','charm')}
    for label, registry, proposed in (('room',rooms,planned_rooms),('mob',mobs,planned_mobs),
        ('npc',npcs,planned_npcs),('item',items,planned_items),('recipe',recipes,planned_recipes)):
        duplicated = proposed.intersection(registry)
        if duplicated:
            raise RuntimeError(f'Era Bez Granic: kolizja {label}: {sorted(duplicated)[0]}')
    created_quests = []
    new_areas = []
    previous = parent
    region_ids = []
    classes = tuple(row[0] for row in CLASSES)
    profession_specs = PROFESSION_SPECS
    # Distribute 3 class quests to every currently authored class, without
    # silently pretending custom admin-created classes already exist.
    class_for_region = {index: [] for index in range(len(ERAS))}
    for n, class_name in enumerate(classes):
        class_for_region[n % len(ERAS)].append((n, class_name))
    for idx, (slug, zone, low, high, theme, first_boss, final_boss) in enumerate(ERAS):
        prefix = f'v10300_{slug}'
        entrance = f'{prefix}_01'
        # One mutually reversible gateway between consecutive authored eras.
        rooms[previous].setdefault('exits', {})['east'] = entrance
        for i, part in enumerate(ROOM_PARTS, 1):
            rid = f'{prefix}_{i:02d}'
            level = low + ((high-low)*(i-1))//11
            exits = {}
            if i == 1:
                exits['west'] = previous
            else:
                exits['south'] = f'{prefix}_{i-1:02d}'
            if i < 12:
                exits['north'] = f'{prefix}_{i+1:02d}'
            rooms[rid] = {
                'zone': zone,
                'name': f'{part} — {zone}',
                'desc': f'{theme}. {zone}, zalecane poziomy {low}–{high}. '
                        f'Sciezka {i} z 12. Brak blokady poziomu; powrot dostepny.',
                'generator_level': level,
                'recommended_mastery': level,
                'exits': exits,
            }
        previous = f'{prefix}_12'
        if idx == len(ERAS)-1:
            # Closing arena remains accessible, and its north path stays unused;
            # procedural 5001+ is NOT faked by linking to an imaginary room.
            pass
        stage = idx+1
        m1, m2, m3 = (f'{prefix}_material_{i}' for i in (1,2,3))
        alloy, charm = f'{prefix}_alloy', f'{prefix}_charm'
        for item_id, title, desc in (
            (m1, f'{MATERIAL_PARTS[0]} {zone}', 'Wydobywany z miejscowych potworow.'),
            (m2, f'{MATERIAL_PARTS[1]} {zone}', 'Pozyskiwany z silniejszych przeciwnikow.'),
            (m3, f'{MATERIAL_PARTS[2]} {zone}', 'Zdobywany u regionalnych bossow.'),
            (alloy, f'Stop {zone}', 'Skladnik regionalnego talizmanu.'),
        ):
            items[item_id] = {'name': title, 'type':'craft_material','price':None,
                              'sell_gold': max(1, stage*20),'desc':desc}
        items[charm] = {'name':f'Talizman {zone}', 'type':'armor','slot':'charm',
                        'defense':int(low*2.0),'price':None,
                        'desc':f'Regionalny talizman ochronny {zone}, etap {low}–{high}.'}
        recipes[alloy] = {'name':f'Stop {zone}','stations':('forge',),
                          'ingredients':{m1:2,m2:2},'output':alloy,'quantity':1,
                          'profession':'Kowalstwo','generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                          'desc':f'Wytop 2 odlamki i 2 rdzenie w Stop {zone}.'}
        recipes[charm] = {'name':f'Talizman {zone}','stations':('forge',),
                          'ingredients':{alloy:2,m3:1,'steel_ingot':1},'output':charm,'quantity':1,
                          'profession':'Kowalstwo','generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                          'desc':f'Wytworz talizman z 2 stopow i 1 pieczeci bossa.'}
        for i, part in enumerate(ENEMY_PARTS,1):
            mid=f'{prefix}_mob_{i}'
            level = low + ((high-low)*i)//10
            hp = int((75_000+level*680)*(1+stage/5))
            damage = int((500+level*4)*(1+stage/12))
            mobs[mid]={'name':f'{part} {zone}', 'generator_level':level,
                       'max_hp':hp,'damage':damage,'damage_type':'magic' if i%2==0 else 'physical',
                       'class_xp_reward':max(200000, 300_000+stage*650_000+i*140_000),
                       'soul_reward':max(200000, 200_000+stage*180_000+i*55000),
                       'stat_reward':max(200000,200_000+stage*160_000),
                       'gold':150+stage*90+i*20,'silver':1000+stage*500,
                       'mithril':stage*2, 'drops':{m1:0.8,m2:0.55,'soul_shard':0.15},
                       'endgame_region_mastery':level,'quest_target':mid}
            for room_number in (2+(i-1)%8,3+(i-1)%8):
                spawns.append((f'{prefix}_{room_number:02d}',mid))
        for i,name in enumerate((first_boss,final_boss),1):
            mid=f'{prefix}_boss_{i}'
            lvl=low if i==1 else high
            mobs[mid]={'name':name,'generator_level':lvl,'max_hp':(3_000_000+lvl*12_000)*i,
                       'damage':int((1_800+lvl*12)*i),'damage_type':'magic',
                       'class_xp_reward':1_000_000+stage*1_200_000*i,
                       'soul_reward':800_000+stage*320_000*i,
                       'stat_reward':max(200000,250000+stage*140000*i),
                       'gold':500+stage*550,'silver':20000+stage*1000,
                       'mithril':3+stage*3,'drops':{m3:1.0,'soul_shard':1.0},
                       'world_boss':True,'boss_mechanic':'endgame_region_boss',
                       'boss_mechanic_text':f'{name}. Uwaga na obrazenia obszarowe.',
                       'endgame_region_mastery':lvl,'quest_target':mid,'leave_corpse':True}
            spawns.append((f'{prefix}_{10 if i==1 else 12:02d}',mid))
        # Main story: eight physical combats, two material collections and
        # two existing regional bosses. No invented quest targets.
        targets=[('kill',f'{prefix}_mob_{j}',2+(j%3)) for j in range(1,9)] + [
            ('collect',m1,3),('collect',m2,3),
            ('kill',f'{prefix}_boss_1',1),('kill',f'{prefix}_boss_2',1),
        ]
        story_ids=[]
        for j,(kind,target,needed) in enumerate(targets,1):
            qid=f'{prefix}_story_{j:02d}'
            giver=f'Kronikarz {zone}' if j <= 4 else (f'Mistrz {zone}' if j<=8 else f'Strażniczka {zone}')
            desc = ('Pokonaj przeciwnika' if kind=='kill' else 'Zdobadz przedmiot')
            quests[qid]={
                'name':f'{zone}: kronika {j} z 12', 'giver':giver,
                'kind':kind, 'target':target,'needed':needed,
                'description':f'{desc} {needed} razy: {mobs[target]["name"] if kind=="kill" else items[target]["name"]}. '
                              f'Cel w {zone}. Wroc do NPC: {giver}.',
                'generator_level':low+((high-low)*(j-1))//11,
                'reward_stat_progress':max(200000,250000+stage*700000+j*50000),
                'reward_gold':250+stage*400+j*80,
                'reward_mithril':stage if j>=11 else 0,
                'reward_items':{m1:1 if j<11 else 2},
                **({'requires_quest':f'{prefix}_story_{j-1:02d}'} if j>1 else {}),
            }
            story_ids.append(qid)
        # 3 profession-action contracts per currently configured profession?
        # Exactly one per profession per era; action credit is handled by the
        # already deployed profession_action event path.
        prof_ids=[]
        for p,(profession,tool_type,activity) in enumerate(profession_specs,1):
            qid=f'{prefix}_prof_{p:02d}'
            quests[qid]={
                'name':f'{zone}: kontrakt {profession}',
                'giver':f'Strażniczka {zone}','kind':'profession_action',
                'target':profession,'needed':8+stage*2,
                'description':f'Wykonaj {8+stage*2} czynnosci profesji {profession} po przyjeciu zadania: {activity}. '
                              f'Nastepnie wroc do Strazniczki {zone}.',
                'required_profession':profession,'min_profession_level':low,
                'generator_level':low,'specialist_tool_type':tool_type,
                'reward_profession':profession,'reward_profession_xp':max(200000,low*2000),
                'reward_tool_type':tool_type,'reward_tool_xp':max(200000,low*2000),
                'reward_silver':stage*10000, 'reward_gold':stage*250,
                'reward_mithril':stage, 'reward_items':{},
            }
            prof_ids.append(qid)
        class_ids=[]
        for number,klass in class_for_region[idx]:
            for j in (1,2,3):
                qid=f'{prefix}_class_{number+1:02d}_{j}'
                target=f'{prefix}_mob_{(j+number)%8+1}' if j<3 else f'{prefix}_boss_1'
                quests[qid]={
                    'name':f'{klass}: proba {j} — {zone}',
                    'giver':f'Mistrz {zone}','kind':'kill','target':target,
                    'needed':j if j<3 else 1,'required_class':klass,
                    'description':f'Klasa {klass}: pokonaj {j if j<3 else 1} x {mobs[target]["name"]} w {zone}.',
                    'generator_level':low, 'reward_stat_progress':max(200000,low*1600+j*250000),
                    'reward_gold':stage*400+j*120,'reward_mithril':stage,
                    'reward_items':{m1:1},
                    **({'requires_quest':f'{prefix}_class_{number+1:02d}_{j-1}'} if j>1 else {}),
                }
                class_ids.append(qid)
        # NPCs must be in three *different* rooms.
        for i,room,person,ids in (
            (1,1,f'Kronikarz {zone}',story_ids[:4]),
            (2,4,f'Mistrz {zone}',tuple(story_ids[4:8])+tuple(class_ids)),
            (3,7,f'Strażniczka {zone}',tuple(story_ids[8:])+tuple(prof_ids))):
            npc_id=f'{prefix}_npc_{i}'
            npcs[npc_id]={
                'name':person, 'room':f'{prefix}_{room:02d}',
                'dialogue':f'{person}: {theme}. Prowadze zadania tej epoki. Quest list, przyjmij 1.',
                'specialist_quests':tuple(ids), 'quest_chain':tuple(ids),
                'quest':ids[0], 'v700_story_npc':True, 'v10300_era_npc':True,
            }
        area_id=prefix
        zone_ids[zone]=area_id
        categories[area_id]='Endgame'
        guides[zone.casefold()]=entrance
        # Store the fixed authored zone difficulty, never the player's level.
        target_power[area_id]=low
        new_areas.append({
            'id':area_id,'name':zone,'aliases':(zone.casefold(),slug),
            'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
            'difficulty':f'era {low}-{high}','guide':zone.casefold(),
            'enemies':', '.join(mobs[f'{prefix}_mob_{j}']['name'] for j in range(1,9)),
            'description':f'{zone}: 12 pokojow, 3 NPC, 8 wrogow, 2 bossow i seria zadan. {theme}.',
            'note':f'Wejscie od poprzedniej epoki, poziomy {low}-{high} zalecane, nie wymagane.',
        })
        region_ids.append(area_id)
        created_quests.extend(story_ids+prof_ids+class_ids)
    return {
        'regions':len(region_ids), 'rooms':len(planned_rooms), 'npcs':len(planned_npcs),
        'mobs':len(planned_mobs), 'quests':len(created_quests),
        'story_quests':12*len(ERAS),'profession_quests':len(profession_specs)*len(ERAS),
        'class_quests':3*len(classes), 'items':len(planned_items),
        'recipes':len(planned_recipes), 'region_ids':tuple(region_ids),
        'areas':tuple(new_areas),
    }
