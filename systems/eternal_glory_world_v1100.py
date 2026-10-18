# -*- coding: utf-8 -*-
"""Twelve authored wilderness expeditions for Soulbound 11.

Catalog mutation-only: no destructive updates to existing world, professions or DB.
No town rooms grant EP. Each distant expedition has a landmark, a unique
single-room guide, a story pair, one elite type and one superboss template.
"""
from systems.forgotten_horizons_v1000 import _insert, _link, _anchor_candidates, _enemy

REGIONS = (
    ('bogowie', 'Pustkowia Zapomnianych Bogów', 160, 'dark',
     'Kronikarka Wira', 'Widmowy Herold Bogów', 'Tytan Zapomnianej Przysięgi',
     ('Złamana Brama Królów','Kamień Zapomnianego Przymierza','Ruiny Ostatniej Kaplicy')),
    ('bialylas', 'Białe Lasy Wieczności', 290, 'ice',
     'Kartografka Elwa', 'Strażnik Białego Boru', 'Władca Wiecznej Zamieci',
     ('Pradawne Korzenie Lodu','Zasypany Krąg Elfów','Serce Lodowego Lasu')),
    ('wulkan', 'Płonący Kontynent Wygnańców', 470, 'fire',
     'Wędrowiec Urgan', 'Popielny Egzekutor', 'Bóg Spękanego Wulkanu',
     ('Ścieżka Czarnego Popiołu','Zatopiony Ołtarz Ognia','Pęknięte Serce Góry')),
    ('otchlan', 'Wody Bezdennej Otchłani', 660, 'water',
     'Badaczka Mira', 'Zwiadowca Głębin', 'Lewiatan Wiecznego Wiru',
     ('Rafa Bezgłosu','Wrota Zaginionych Marynarzy','Tron Oceanicznej Otchłani')),
    ('klepsydra', 'Pustynia Złamanego Czasu', 390, 'arcane',
     'Mistrz Chronik Arven', 'Łowca Piaskowych Godzin', 'Kolos Wiecznych Klepsydr',
     ('Próg Utraconych Minut','Oaza Bez Czasu','Tron Ostatniej Sekundy')),
    ('ciernie', 'Królestwo Cierniowych Puszcz', 220, 'poison',
     'Druidka Aralia', 'Cierniowy Łowca', 'Matka Tysiąca Cierni',
     ('Brama Zapomnianych Korzeni','Mokradła Ostatniego Liścia','Serce Czarnego Drzewa')),
    ('meteory', 'Góry Gwiezdnych Odłamków', 590, 'lightning',
     'Astronom Kaelen', 'Strażnik Spadających Gwiazd', 'Smok Gwiezdnego Deszczu',
     ('Siodło Błękitnego Meteoru','Krater Zaginionych Przysiąg','Ołtarz Niebiańskiego Grzmotu')),
    ('szept', 'Archipelag Milczących Głębin', 750, 'water',
     'Żeglarka Orina', 'Upiór Głębinowych Żagli', 'Królowa Bezgłośnego Oceanu',
     ('Latarnia Ostatnich Żagli','Rafa Głębinowych Szeptów','Pałac Utopionych Koron')),
    ('popiol', 'Wrota Popielnego Nieba', 680, 'fire',
     'Wieszczka Selene', 'Płomienny Łowca Gwiazd', 'Serafin Płomiennego Sądu',
     ('Most Rozpalonych Gwiazd','Zwęglony Ogród Niebios','Pieczęć Ognistego Serafina')),
    ('otchlan_lodu', 'Korona Wiecznej Zimy', 530, 'ice',
     'Strażniczka Vela', 'Lodowy Egzekutor', 'Cesarz Nieskończonego Mrozu',
     ('Zamarznięty Przesmyk','Cmentarz Srebrnych Sosen','Pałac Ostatniej Zimy')),
    ('burza', 'Wyspy Rozszalałych Burz', 610, 'lightning',
     'Żeglarz Theron', 'Upiorny Gromowładny', 'Leviatan Stu Błyskawic',
     ('Przesmyk Grzmotów','Wrak Piorunowego Okrętu','Oko Nieskończonego Sztormu')),
    ('mrok', 'Pustkowia Utraconych Dusz', 790, 'dark',
     'Duszoznawczyni Nyra', 'Cień Wiecznej Rozpaczy', 'Pan Ostatniego Zapomnienia',
     ('Ślad Zaginionych Dusz','Ogród Martwych Wspomnień','Ołtarz Ostatniego Imienia')),


)
ROOMS_PER_REGION=12
LANDMARK_POSITIONS=(3, 7, 10)
LANDMARK_IDS={f'v1100_eg_{key}_{i:02d}' for key,*_ in REGIONS for i in LANDMARK_POSITIONS}
ROOM_IDS={f'v1100_eg_{key}_{i:02d}' for key,*_ in REGIONS for i in range(ROOMS_PER_REGION)}
QUEST_IDS={f'v1100_eg_{key}_quest_{i}' for key,*_ in REGIONS for i in (1,2)}
PATH_NAMES=(
 'Złamane Kamienie','Stary Szlak','Rozdroże Wiatrów', 'Święta Granica',
 'Ukryte Rozlewisko', 'Próg Przodków','Wąwóz Echa', 'Zapomniany Znak',
 'Ścieżka Strażników','Niebezpieczne Urwisko', 'Wieczny Pomnik', 'Komnata Władcy',
)

def install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases):
    candidates=[x for x in _anchor_candidates(rooms,npcs) if not x.startswith('v1000_') and not x.startswith('v1100_')]
    if len(candidates)<len(REGIONS):
        raise AssertionError('Soulbound 11: insufficient external wilderness entrances')
    chosen=[]
    previous_zones=set()
    for key,zone,level,element,guide,elite,boss,places in REGIONS:
        anchor=next((r for r in candidates if r not in chosen and rooms[r].get('zone') not in previous_zones),None)
        if anchor is None:anchor=next((r for r in candidates if r not in chosen),None)
        if anchor is None:raise AssertionError('Not enough anchors for 11.0')
        chosen.append(anchor)
        previous_zones.add(rooms[anchor].get('zone'))
        prefix=f'v1100_eg_{key}'
        for idx in range(ROOMS_PER_REGION):
            rid=f'{prefix}_{idx:02d}'
            landmark=idx in LANDMARK_POSITIONS
            title=places[LANDMARK_POSITIONS.index(idx)] if landmark else f'{zone}: {PATH_NAMES[idx]}'
            _insert(rooms,'ROOMS',rid,{
                'name':title,'zone':zone,
                'desc': f'{zone}. Rozległy teren dawnych wypraw. '
                        + ('Znajdujesz wyjątkowy punkt eksploracyjny.' if landmark else 'Zwykły szlak nie przyznaje EP.'),
                'exits':{},'generator_level':level,'recommended_mastery':level,
                'exploration_ep':5 if landmark else 0,
                'v1000_landmark':landmark,'v1100_expedition':key,
                'v1100_eternal_glory':True,
            })
            if idx:_link(rooms,f'{prefix}_{idx-1:02d}',rid)
        _link(rooms,anchor,f'{prefix}_00')
        material=f'v1100_eg_{key}_relic'
        _insert(items,'ITEMS',material,{'name':f'Relikt: {zone}', 'type':'resource',
                'price':None,'sell_silver':level*135,
                'desc':'Pozostałość po pradawnej ekspedycji, znajdowana przy potężnych strażnikach.'})
        elite_id=f'{prefix}_elite';boss_id=f'{prefix}_boss'
        elite_entry=_enemy(elite,level,element);elite_entry['drops'][material]=0.35
        boss_entry=_enemy(boss,level,element,True);boss_entry['drops'][material]=1.0
        boss_entry['v1100_eternal_glory_boss']=True
        _insert(mobs,'MOB_TEMPLATES',elite_id,elite_entry)
        _insert(mobs,'MOB_TEMPLATES',boss_id,boss_entry)
        for idx in (2,5,8):spawns.append((f'{prefix}_{idx:02d}',elite_id))
        spawns.append((f'{prefix}_11',boss_id))
        qa=f'{prefix}_quest_1';qb=f'{prefix}_quest_2'
        _insert(quests,'QUESTS',qa,{'name':f'{zone}: Zagrożenie na Szlaku',
                'giver':guide,'kind':'kill','target':elite_id,'needed':3,
                'description':f'Pokonaj trzech strażników: {zone}.',
                'generator_level':level,'reward_silver':level*4600,
                'reward_gold':0,'reward_mithril':0,'reward_items':{},'repeatable':False})
        _insert(quests,'QUESTS',qb,{'name':f'{zone}: Ostatni Strażnik',
                'giver':guide,'kind':'kill','target':boss_id,'needed':1,'requires_quest':qa,
                'description':f'Zakończ wyprawę i pokonaj strażnika krainy {zone}.',
                'generator_level':level,'reward_silver':level*9200,
                'reward_gold':0,'reward_mithril':0,'reward_items':{},'repeatable':False})
        _insert(npcs,'NPCS',f'{prefix}_guide',{'name':guide,'room':f'{prefix}_00',
                'dialogue':f'{zone}. Witaj, podróżniku. Mam dla ciebie wyprawę. Zobacz quest list.',
                'specialist_quests':(qa,qb),'v1100_expedition_guide':True})
    help_topics['chwale11']=[
        'Era Wiecznej Chwały: dwanaście nowych dzikich krain i dwadzieścia cztery zadania ekspedycyjnych.',
        'EP wpada automatycznie wyłącznie w ważnych punktach; miasta i zwykłe szlaki nie przyznają EP.',
        'Komendy: ep, ep region, ep all, fame. Ważne odkrycia to 36 punktów w nowych krainach.',
    ]
    help_aliases['chwala11']='chwale11'
    return {'regions':len(REGIONS),'rooms':len(ROOM_IDS),'landmarks':len(LANDMARK_IDS),'guides':len(REGIONS),
            'quests':len(QUEST_IDS),'materials':len(REGIONS),'spawns':4*len(REGIONS),'entrances':tuple(chosen)}
