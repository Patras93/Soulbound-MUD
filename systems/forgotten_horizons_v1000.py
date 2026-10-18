# -*- coding: utf-8 -*-
"""Soulbound 10: six connected authored regions, one-time cartographic landmarks.

No new currencies, profession/tool tracks or changes to EXP/Fame rewards.
No historic catalog key or SQLite progress is removed. Survey milestones use
existing per-character collections and the pre-existing 'mapuj' work action.
"""
from collections import deque

REGIONS = (
    ('przedwit', 'Dolina Przedświtu', 25, 'holy', 'Zwiadowczyni Armina', 'Strażnik Szklanych Łąk', 'Król Zapomnianego Świtu',
     ('Łąki Białych Śladów', 'Wrota Rosa', 'Stary Obelisk')),
    ('torfowiska', 'Torfowiska Zaginionych Królów', 110, 'poison', 'Kronikarz Veldran', 'Władca Torfowych Korzeni', 'Serce Topielnych Koron',
     ('Głazy Mokrego Tronu', 'Latarnia Błędnych Świateł', 'Grota Korzeni')),
    ('sztormy', 'Wybrzeże Zaklętych Sztormów', 210, 'water', 'Nawigatorka Iskra', 'Sługa Błękitnego Wiru', 'Lewiatan Zapomnianego Brzegu',
     ('Latarnia Zaginionych Statków', 'Zatoka Pękniętych Żagli', 'Tron Przypływu')),
    ('krysztaly', 'Kryształowe Urwiska Eteru', 340, 'arcane', 'Mistrzyni Kryształów Lira', 'Sędzia Rozbitych Pryzmatów', 'Arcykryształ Otchłani',
     ('Most Kryształowego Nieba', 'Wieża Głosu', 'Pryzmat Przodków')),
    ('popioly', 'Popioły Zapomnianych Bogów', 530, 'fire', 'Pielgrzymka Astra', 'Strażnik Spopielonego Przymierza', 'Bóg Pustego Paleniska',
     ('Schody Wiecznego Żaru', 'Ołtarz Ostatniej Iskry', 'Kamienne Słońce')),
    ('bezkres', 'Bezkresna Granica Gwiazd', 720, 'dark', 'Kartograf Gwiazd Onaris', 'Posłaniec Milczącej Pustki', 'Strażnik Bramy Bez Końca',
     ('Brama Dalekich Świateł', 'Łuk Zaginionego Czasu', 'Oko Nieskończoności')),
)
MATERIAL_NAMES = (
    'Kryształ Pierwszej Rosy', 'Korzeń Błędnych Koron',
    'Perła Zaklętego Sztormu', 'Odłamek Eterowego Pryzmatu',
    'Żar Pradawnego Paleniska', 'Gwiezdny Pył Bezkresu',
)
PATH_NAMES = (
    'Przejście Żurawich Kręgów','Szlak Starej Mapy','Gęstwina Zapomnianych Tropów',
    'Kamień Północnego Wiatru','Rozdroże Pękniętych Bram','Most Szeptów',
    'Ścieżka Bursztynowych Cieni','Oko Dawnej Gwiazdy','Krawędź Milczącej Doliny',
    'Wrota Ostatniej Wyprawy','Sala Niegasnącego Światła','Przedpole Ostatecznej Pieczęci',
)
ROOMS_PER_REGION = 12
LANDMARK_POSITIONS = (3, 7, 10)
LANDMARK_IDS = {
    f'v1000_horizon_{key}_{position:02d}'
    for key, *_ in REGIONS for position in LANDMARK_POSITIONS
}
NEW_ROOM_IDS = {f'v1000_horizon_{key}_{i:02d}' for key, *_ in REGIONS for i in range(ROOMS_PER_REGION)}
QUEST_IDS = {f'v1000_{key}_quest_{stage}' for key, *_ in REGIONS for stage in (1, 2)}
REVERSE = {'north':'south', 'south':'north', 'east':'west','west':'east',
           'up':'down','down':'up','northeast':'southwest','southwest':'northeast',
           'northwest':'southeast','southeast':'northwest'}
DIRECTIONS = ('north', 'east', 'south', 'west', 'northeast','northwest','southeast','southwest','up','down')


def _insert(catalog, kind, key, row):
    if key in catalog:
        raise AssertionError('v10 ID collision: '+key)
    from data import catalog_mutations as mutation
    mutation.catalog_assign(row, kind, catalog, (key,))


def _link(rooms, first, second):
    if first not in rooms or second not in rooms:
        raise AssertionError('v10 missing location for passage')
    for direction in DIRECTIONS:
        reverse = REVERSE[direction]
        if direction not in rooms[first]['exits'] and reverse not in rooms[second]['exits']:
            rooms[first]['exits'][direction] = second
            rooms[second]['exits'][reverse] = first
            return
    raise AssertionError('v10 no free passage from '+first)


def _accessible(rooms):
    roots = ('square',) if 'square' in rooms else tuple(root for root in ('temple','temple_square','town_square') if root in rooms)[:1]
    if not roots:
        raise AssertionError('v10 cannot find original world entrance')
    known = set(roots)
    q = deque(roots)
    while q:
        rid = q.popleft()
        for target in rooms[rid].get('exits',{}).values():
            if target in rooms and target not in known:
                known.add(target)
                q.append(target)
    return known


def _anchor_candidates(rooms, npcs):
    reachable = _accessible(rooms)
    occupied = {npc.get('room') for npc in npcs.values()}
    blocked = {'square','temple','temple_square','town_square', 'market',
               'library','sea_pier','guild_hall','forge','north_gate','south_gate'}
    rows = []
    for rid in reachable:
        room = rooms[rid]
        if (rid in occupied or rid in blocked or rid.startswith(('v800_', 'v900_', 'v1000_')) or any(token in rid.lower() for token in ('arena','gauntlet','boss','portal','checkpoint','final','trial','dungeon','crypt','tower'))
            or any(room.get(key) for key in ('v800_class_mentor_room','v900_mentor_room',
                                             'v900_teacher_room','procedural_surface',
                                             'procedural_gateway','exploration_boss_room'))):
            continue
        exits = room.get('exits',{})
        if not exits or len(exits)>3 or not any(d not in exits for d in DIRECTIONS):
            continue
        if not any(x in str(room.get('zone','')).casefold() for x in (
                'miasto','rubież','las','góry','wybrzeż','królestw','świat','pustyni','łąk',
                'zapomnian','strefa','szlak')):
            continue
        rows.append((abs(int(room.get('recommended_mastery') or room.get('level') or 1)-175),
                     str(room.get('zone')),rid))
    # Select six distinct safe old routes, rather than overwrite a main-city exit.
    return [x[-1] for x in sorted(rows)]


def _enemy(name, level, element, boss=False):
    return {'name':name, 'generator_level':level, 'max_hp':level*(2400 if boss else 70),
            'damage':level*(23 if boss else 4), 'damage_type':'magic' if element!='physical' else 'physical',
            'attack_elements_v11339':(element,), 'rank':'world_boss' if boss else 'elite',
            'boss':boss,'world_boss':boss,'v017_boss_phases':boss,
            'boss_mechanic':'ancient' if boss else None,
            'stat_reward':level*(300 if boss else 45),
            'class_xp_reward':level*(10500 if boss else 1500),
            'soul_reward':level*(4000 if boss else 600),
            'silver':level*(1600 if boss else 220),
            'gold':0,'mithril':0,'drops':{'soul_shard':1.0},
            'stationary_mob':True,'auto_aggro':False,'v1000_horizon':True}


def install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases):
    anchors = _anchor_candidates(rooms,npcs)
    if len(anchors)<6:raise AssertionError('v10 requires six safe world entrances')
    used_zones = set()
    picked = []
    for _, _, stage, *_ in REGIONS:
        choice = next((rid for rid in anchors if rid not in picked and
                       rooms[rid].get('zone') not in used_zones),None)
        if choice is None:
            choice = next((rid for rid in anchors if rid not in picked),None)
        if choice is None:raise AssertionError('v10 not enough safe anchors')
        picked.append(choice);used_zones.add(rooms[choice].get('zone'))
    for number,(key,zone,level,element,npc_name,elite_name,boss_name,landmarks) in enumerate(REGIONS):
        prefix=f'v1000_horizon_{key}'
        for idx in range(ROOMS_PER_REGION):
            rid=f'{prefix}_{idx:02d}'
            landmark_index = LANDMARK_POSITIONS.index(idx) if idx in LANDMARK_POSITIONS else None
            name=(landmarks[landmark_index] if landmark_index is not None else
                  f'{zone}: {PATH_NAMES[idx]}')
            desc=(f'{zone}. Pradawne ślady prowadzą dalej w nieznany świat. '
                  'Wyjątkowe miejsce kartograficzne — wykonaj mapuj, aby je udokumentować.'
                  if landmark_index is not None else
                  f'{zone}. Tutejsze szlaki wymagają uważnej eksploracji i pomiarów Kartografii.')
            _insert(rooms,'ROOMS',rid,{
                'name':name,'zone':zone,'desc':desc,'exits':{},
                'generator_level':level,'recommended_mastery':level,
                'exploration_ep': 5 if landmark_index is not None else 2 + min(6, level//110),
                'v1000_landmark':landmark_index is not None, 'v1000_horizon':key,
                'v1000_horizon_final':idx==ROOMS_PER_REGION-1,
            })
            if idx>0:_link(rooms,f'{prefix}_{idx-1:02d}',rid)
        _link(rooms,picked[number],f'{prefix}_00')
        material_id=f'v1000_{key}_material'
        _insert(items,'ITEMS',material_id,{
            'name':MATERIAL_NAMES[number],'type':'resource','price':None,
            'sell_silver':level*120,'desc':f'Rzadki surowiec z regionu {zone}, pozyskiwany z naturalnych przeciwników.',
            'v1000_horizon_resource':True})
        elite=f'v1000_{key}_elite';boss=f'v1000_{key}_boss'
        elite_template=_enemy(elite_name,level,element)
        elite_template['drops'][material_id]=0.28
        boss_template=_enemy(boss_name,level,element,boss=True)
        boss_template['drops'][material_id]=1.0
        _insert(mobs,'MOB_TEMPLATES',elite,elite_template)
        _insert(mobs,'MOB_TEMPLATES',boss,boss_template)
        for room_idx in (2,5,8):
            spawns.append((f'{prefix}_{room_idx:02d}',elite))
        spawns.append((f'{prefix}_11',boss))
        q1=f'v1000_{key}_quest_1';q2=f'v1000_{key}_quest_2'
        _insert(quests,'QUESTS',q1,{
            'name':f'{zone}: Ślady Zagrożenia','giver':npc_name,'kind':'kill',
            'target':elite,'needed':3,'description':f'Pokonaj trzy strażnicze istoty w regionie {zone}.',
            'generator_level':level,'reward_silver':level*4500,'reward_gold':0,
            'reward_mithril':0,'reward_items':{},'repeatable':False,
        })
        _insert(quests,'QUESTS',q2,{
            'name':f'{zone}: Finał Wyprawy','giver':npc_name,'kind':'kill',
            'target':boss,'needed':1,'requires_quest':q1,
            'description':f'Pokonaj głównego strażnika regionu {zone}, po ukończeniu poprzedniego zadania.',
            'generator_level':level,'reward_silver':level*9000,'reward_gold':0,
            'reward_mithril':0,'reward_items':{},'repeatable':False,
        })
        _insert(npcs,'NPCS',f'v1000_{key}_guide',{
            'name':npc_name,'room':f'{prefix}_00',
            'dialogue':f'Witaj w regionie {zone}. Odkrywaj szlaki i mapuj charakterystyczne miejsca. '
                       f'Zadania: quest list; przyjmij 1; oddaj quest.',
            'specialist_quests':(q1,q2), 'v1000_horizon_guide':True,
        })
    help_topics['horyzonty10']=[
        'Zapomniane Horyzonty v10: sześć nowych regionów i sześciu odrębnych przewodników.',
        'Regiony: Dolina Przedświtu, Torfowiska Zaginionych Królów, Wybrzeże Zaklętych Sztormów, Kryształowe Urwiska Eteru, Popioły Zapomnianych Bogów, Bezkresna Granica Gwiazd.',
        'W regionach zdobywasz standardowe EP za pierwszą wizytę. Nie ma bonusowego EXP za EP.',
        'W 18 punktach charakterystycznych wykonaj prawdziwe mapuj z Kompasem Mierniczym; sam spacer ich nie zaliczy.',
        'Komendy: ep, ep region, ep all, kartografia, kartografia region, gdzie ep, exp, experience cap, fame.',
        'Dwanaście zadań: po dwa u przewodnika każdej nowej krainy; bez blokowania gry solo.',
    ]
    help_aliases['horyzonty']='horyzonty10'
    return {'regions':6,'rooms':72,'landmarks':18,'guides':6,'quests':12,'materials':6,'spawns':24,'entrances':tuple(picked)}


def documented_landmarks(conn, account_id, collection_lookup):
    """Computed from the *existing* cartography_v1100 per-character ledger."""
    return frozenset(collection_lookup(account_id,'cartography_v1100')).intersection(LANDMARK_IDS)
