# -*- coding: utf-8 -*-
"""Jednoznaczne przejscia miedzy granicami obszarow.

Zachowujemy wszystkie ID lokacji, bossow i progi. Przenosimy tylko dwa
historyczne skroty ze srodka cmentarza na skraj siatki. Zmiany z v116.00.14.
"""
from __future__ import annotations

CEMETERY_CRYPT_EDGE = 'v115_graveyard_11_11'   # polnocno-wschodni skraj
CEMETERY_NECROPOLIS_EDGE = 'v115_graveyard_11_00'  # poludniowo-wschodni skraj


def install_static(rooms):
    """Krypta jest dostepna z dalekiego kranca Cmentarza, nie z jego srodka.

    To czesc katalogu wczesnego swiata, przed doinstalowaniem krain
    proceduralnych. Bez nowych pokojow, danych DB i migracji postaci.
    """
    graveyard = rooms['graveyard']['exits']
    crypt = rooms['crypt_entrance']['exits']
    cemetery = rooms[CEMETERY_CRYPT_EDGE]['exits']
    if (graveyard.get('down') != 'crypt_entrance'
            or crypt.get('up') != 'graveyard'
            or 'down' in cemetery):
        raise ValueError('Niespojna historyczna trasa Cmentarz-Krypta')
    del graveyard['down']
    cemetery['down'] = 'crypt_entrance'
    crypt['up'] = CEMETERY_CRYPT_EDGE
    rooms['graveyard']['desc'] = ('Początek Starego Cmentarza. Krypty szukaj na północno-wschodnim krańcu; tam są schody w dół.')
    rooms[CEMETERY_CRYPT_EDGE]['desc'] += ' Schody w dół prowadzą do Krypty.'


def install_runtime(rooms):
    """Polacz rozszerzona Nekropolie ze wschodnim KRAŃCEM Cmentarza.

    Nekropolia pojawia sie dopiero podczas rozbudowy runtime swiatow, wiec
    nie wolno wczesniej zgadywac ani nadpisywac jej istniejących wyjsc.
    """
    if 'necropolis_gate' not in rooms:
        return False  # katalog minimalny, bez opcjonalnej Nekropolii
    graveyard = rooms['graveyard']['exits']
    necropolis = rooms['necropolis_gate']['exits']
    cemetery = rooms[CEMETERY_NECROPOLIS_EDGE]['exits']
    if (graveyard.get('east') != 'necropolis_gate'
            or necropolis.get('west') != 'graveyard'
            or 'east' in cemetery):
        raise ValueError('Niespojna historyczna trasa Cmentarz-Nekropolia')
    del graveyard['east']
    cemetery['east'] = 'necropolis_gate'
    necropolis['west'] = CEMETERY_NECROPOLIS_EDGE
    rooms[CEMETERY_NECROPOLIS_EDGE]['desc'] += ' Na wschodzie zaczyna się Nekropolia.'
    return True


# v116.00.15: thirty long access trails from Horyzonty hub to the real border.
HORIZON_APPROACH_LENGTH = 12


def horizon_approach_id(region_index: int, step: int) -> str:
    return f'v116_horizon_border_{region_index:02d}_{step:02d}'


def install_horizon_border_trails(rooms):
    """Place the actual zone crossover at the END of each 12-room spur.

    The old crossroads and hub IDs, world region IDs, region grids and bosses
    are not moved.  Verify every original two-way gateway before mutation.
    No mobs, rewards, level gates, traps, database writes or auto-aggression.
    """
    from systems.v115.high_level_world import REGIONS
    from systems.v115.playable_regions import HUB, room_id
    plans = []
    generated = {}
    for index, region in enumerate(REGIONS, 1):
        node = HUB if index == 1 else f'v115_wezel_{index:02d}'
        entry = room_id(region.key, 0, 0)
        if node not in rooms or entry not in rooms:
            raise ValueError(f'Brak historycznej bramy Horyzontow: {index}')
        if rooms[node]['exits'].get('east') != entry:
            raise ValueError(f'Zmienione wyjscie Szlaku Horyzontow: {node}')
        if rooms[entry]['exits'].get('west') != node:
            raise ValueError(f'Zmieniony powrot z krainy Horyzontow: {entry}')
        if rooms[node]['zone'] != 'Szlak Horyzontów':
            raise ValueError(f'Zmieniona strefa Szlaku Horyzontow: {node}')
        if rooms[entry]['zone'] == rooms[node]['zone']:
            raise ValueError(f'Brak granicy stref Horyzontow: {entry}')
        plans.append((index, node, entry, region.name))
        for step in range(1, HORIZON_APPROACH_LENGTH + 1):
            rid = horizon_approach_id(index, step)
            if rid in rooms or rid in generated:
                raise ValueError(f'Kolizja drogi granicznej: {rid}')
            west = node if step == 1 else horizon_approach_id(index, step - 1)
            east = entry if step == HORIZON_APPROACH_LENGTH else horizon_approach_id(index, step + 1)
            generated[rid] = {
                'zone': 'Szlak Horyzontów',
                'name': f'Trakt graniczny {index} — odcinek {step}',
                'desc': (f'Droga na kraniec Szlaku Horyzontów, w stronę {region.name}. '
                         f'Odcinek {step} z {HORIZON_APPROACH_LENGTH}. '
                         'Na zachód powrót, na wschód dalsza droga.'),
                'exits': {'west': west, 'east': east},
            }
    if len(plans) != 30 or len(generated) != 30 * HORIZON_APPROACH_LENGTH:
        raise ValueError('Niekompletne drogi graniczne Horyzontow')
    rooms.update(generated)
    for index, node, entry, _ in plans:
        rooms[node]['exits']['east'] = horizon_approach_id(index, 1)
        rooms[entry]['exits']['west'] = horizon_approach_id(index, HORIZON_APPROACH_LENGTH)
    return len(generated)


# v116.00.16: peryferyjne sieci dla starej Dziczy, Gór i Bagien.
# Przejście między dwoma terenami leży na ZEWNĘTRZNEJ krawędzi obu sieci.
WILD_BORDER_SIZE = 12
_WILD_AREAS = (
    ('dzicz', 'Północne Rubieże Dziczy', 'Dzicz', 'forester_lodge', 'north', 'south', 12,
     ('Leśny przesmyk', 'Dziki jar', 'Zarośnięta ścieżka', 'Wysoka polana')),
    ('gory', 'Grzbiet Górski', 'Góry', 'lava_fissure', 'north', 'south', 30,
     ('Kamienny grzbiet', 'Wietrzna ścieżka', 'Górska dolina', 'Skalna grań')),
    ('bagna', 'Rubieże Czarnych Bagien', 'Bagna', 'swamp_hunter_post', 'east', 'west', 20,
     ('Bagienna grobla', 'Trzcinowy trakt', 'Mętne rozlewisko', 'Sucha kępa')),
)
_WILD_GATEWAYS = (
    ('hill', 'east', 'mountain_pass', 'west', ('dzicz', 11, 11, 'east'), ('gory', 0, 11, 'west')),
    ('deep_grove', 'south', 'swamp_boardwalk', 'north', ('dzicz', 11, 0, 'east'), ('bagna', 0, 11, 'west')),
)

def wild_border_id(key: str, x: int, y: int) -> str:
    return f'v116_wild_edge_{key}_{x:02d}_{y:02d}'

def install_wild_border_network(rooms):
    """Przesuń DWA stare przejścia ze środka tras na rzeczywiste brzegi.

    Musi działać PO dobudowaniu dawnych przejść przez world.dynamic_content.
    Sprawdza wszystkie stare kierunki, punkty zaczepienia i kolizje przed zmianą.
    Historyczne ID i pozostałe stare wyjścia, NPC, bossowie, zadania, EXP i DB
    pozostają nienaruszone. Brak automatycznego aggro, pułapek i blokad.
    """
    created = {}
    for key, zone, old_zone, anchor, departure, back, level, names in _WILD_AREAS:
        existing = rooms.get(anchor)
        if not isinstance(existing, dict) or existing.get('zone') != old_zone:
            raise ValueError(f'Nieprawidlowy kraniec dawnego terenu: {anchor}')
        if departure in existing.get('exits', {}):
            raise ValueError(f'Zajety kierunek na brzegu: {anchor}/{departure}')
        # Stara lokacja musi być końcową odnogą, nie węzłem pośrodku.
        same_zone = sum(rooms.get(dst, {}).get('zone') == old_zone
                        for dst in existing['exits'].values())
        if same_zone != 1:
            raise ValueError(f'Punkt zaczepienia nie jest końcem trasy: {anchor}')
        for y in range(WILD_BORDER_SIZE):
            for x in range(WILD_BORDER_SIZE):
                rid = wild_border_id(key, x, y)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja nowego pokoju: {rid}')
                exits = {}
                if x > 0: exits['west'] = wild_border_id(key, x-1, y)
                if x+1 < WILD_BORDER_SIZE: exits['east'] = wild_border_id(key, x+1, y)
                if y > 0: exits['south'] = wild_border_id(key, x, y-1)
                if y+1 < WILD_BORDER_SIZE: exits['north'] = wild_border_id(key, x, y+1)
                if (x, y) == (0, 0):
                    if back in exits: raise ValueError('Zle wejscie do siatki')
                    exits[back] = anchor
                created[rid] = {
                    'zone': zone,
                    'name': f'{names[(x + 3*y) % len(names)]} — {zone}',
                    'desc': f'{zone}. Odcinek {x+1}/12, pas {y+1}/12. Drogi łączą sektory.',
                    'exits': exits,
                    'generator_level': level,
                    'exploration_ep': 0,
                    'v116_wild_border': key,
                }
    # Obydwie historyczne pary muszą naprawdę istnieć i być dwukierunkowe.
    for old_a, dir_a, old_b, dir_b, dest_a, dest_b in _WILD_GATEWAYS:
        if (old_a not in rooms or old_b not in rooms or
                rooms[old_a]['exits'].get(dir_a) != old_b or
                rooms[old_b]['exits'].get(dir_b) != old_a):
            raise ValueError(f'Niepoprawna historyczna brama: {old_a} / {old_b}')
        a_key, ax, ay, adir = dest_a
        b_key, bx, by, bdir = dest_b
        arid = wild_border_id(a_key, ax, ay)
        brid = wild_border_id(b_key, bx, by)
        if (ax not in (0, 11) and ay not in (0, 11)) or (bx not in (0, 11) and by not in (0, 11)):
            raise ValueError('Przejscie nie lezy na krancach obu map')
        if adir in created[arid]['exits'] or bdir in created[brid]['exits']:
            raise ValueError('Przejscie nadpisywaloby stara droge')
        if created[arid]['zone'] == created[brid]['zone']:
            raise ValueError('Przejscie nie zmienia terenu')
        created[arid]['exits'][adir] = brid
        created[brid]['exits'][bdir] = arid
    if len(created) != 3 * WILD_BORDER_SIZE ** 2:
        raise ValueError('Niekompletna siec graniczna')
    # Dopiero teraz zmieniaj świat: jednorazowa, zweryfikowana operacja.
    rooms.update(created)
    for key, _zone, _old_zone, anchor, departure, _back, _level, _names in _WILD_AREAS:
        rooms[anchor]['exits'][departure] = wild_border_id(key, 0, 0)
    for old_a, dir_a, old_b, dir_b, _edge_a, _edge_b in _WILD_GATEWAYS:
        del rooms[old_a]['exits'][dir_a]
        del rooms[old_b]['exits'][dir_b]
    return len(created)


# v116.00.17: zamiast przejścia przez wnętrze Gaju Szeptów — połączenie
# na końcu dwóch tras granicznych. Nie zmieniaj żadnego dawnego room_id.
HISTORICAL_BORDER_LENGTH = 12

def historical_border_id(key: str, step: int) -> str:
    return f'v116_meadow_wild_border_{key}_{step:02d}'

def install_historical_meadow_wilderness_border(rooms):
    """Poprowadź Dzicz <-> Łąki przez dwie graniczne drogi, bez skrótów.

    Usuwamy też JEDNOSTRONNY środkowy skrót Rozdroże -> Ruiny Strażnicy.
    Normalna dwukierunkowa droga przez Kamienny Most zostaje, wraz z
    istniejącymi questami, NPC, szablonami, zapisami oraz komnatami bossów.
    Funkcja działa po rejestracji wszystkich dawnych terenów w runtime.
    """
    wild = rooms.get('whisper_grove')
    meadow = rooms.get('flower_meadow')
    crossroads = rooms.get('crossroads')
    watchtower = rooms.get('ruined_watchtower')
    bridge = rooms.get('stone_bridge')
    if any(not isinstance(room, dict) for room in (wild, meadow, crossroads, watchtower, bridge)):
        raise ValueError('Brak historycznych pomieszczen przejscia Dzicz-Laki-Straznica')
    if (wild.get('zone') != 'Dzicz' or meadow.get('zone') != 'Łąki'
            or wild['exits'].get('east') != 'flower_meadow'
            or meadow['exits'].get('west') != 'whisper_grove'):
        raise ValueError('Zmieniona brama Dzicz-Laki; nie nadpisuje wyjsc')
    if (crossroads.get('zone') != 'Dzicz'
            or watchtower.get('zone') != 'Ruiny Strażnicy'
            or crossroads['exits'].get('east') != 'ruined_watchtower'
            or watchtower['exits'].get('west') != 'stone_bridge'
            or bridge['exits'].get('east') != 'ruined_watchtower'):
        raise ValueError('Zmieniona historyczna droga Ruin Straznicy')
    # Przed modyfikacją upewniamy się, że Kamienny Most jest dostępny
    # z Łąk, a nie poprzez jednostronny skrót z Rozdroża.
    def can_reach(start, end, skip):
        from collections import deque
        queue = deque([start]); seen = {start}
        while queue:
            node = queue.popleft()
            if node == end: return True
            for direction, dest in rooms[node].get('exits', {}).items():
                if (node, direction) == skip or dest not in rooms or dest in seen:
                    continue
                seen.add(dest); queue.append(dest)
        return False
    if not can_reach('flower_meadow', 'ruined_watchtower', ('crossroads','east')):
        raise ValueError('Po skasowaniu skrotu Ruiny przestalyby byc dostepne')
    created = {}
    for key, zone, level, difficulty in (
        ('dzicz', 'Dzicz', 12, 'poczatkujace'),
        ('laki', 'Łąki', 5, 'poczatkujace'),
    ):
        for step in range(1, HISTORICAL_BORDER_LENGTH + 1):
            rid = historical_border_id(key, step)
            if rid in rooms or rid in created:
                raise ValueError(f'Kolizja ID drogi granicznej: {rid}')
            if key == 'dzicz':
                west = 'whisper_grove' if step == 1 else historical_border_id(key, step - 1)
                east = (historical_border_id('laki', 1) if step == HISTORICAL_BORDER_LENGTH
                        else historical_border_id(key, step + 1))
            else:
                west = (historical_border_id('dzicz', HISTORICAL_BORDER_LENGTH) if step == 1
                        else historical_border_id(key, step - 1))
                east = 'flower_meadow' if step == HISTORICAL_BORDER_LENGTH else historical_border_id(key, step + 1)
            created[rid] = {
                'zone': zone,
                'name': f'Graniczny Trakt {zone} — odcinek {step}',
                'desc': f'{zone}, trakt graniczny. Odcinek {step} z {HISTORICAL_BORDER_LENGTH}. Na wschód dalsza droga, na zachód powrót.',
                'exits': {'west': west, 'east': east},
                'generator_level': level,
                'region_difficulty_v2006': difficulty,
                'region_stage_v2006': level,
                'exploration_ep': 0,
                'v116_meadow_wild_border': key,
            }
    if len(created) != HISTORICAL_BORDER_LENGTH * 2:
        raise ValueError('Niekompletna droga graniczna')
    rooms.update(created)
    wild['exits']['east'] = historical_border_id('dzicz',1)
    meadow['exits']['west'] = historical_border_id('laki',HISTORICAL_BORDER_LENGTH)
    # Ten skrót nie miał drogi powrotnej: z Ruin prowadzi tylko mostem.
    # Zostawiamy wszystkie inne wyjścia z Rozdroża oraz Ruin.
    del crossroads['exits']['east']
    return len(created)


# v116.00.18: trzy kolejne historyczne trasy. Każda z dwóch stref posiada
# własne dojście, a granica przebiega między KOŃCAMI dróg obu obszarów.
LEGACY_BORDER_LENGTH = 12
_LEGACY_BORDER_ROUTES = (
    ('jezioro', 'lakeside_meadow', 'south', 'lake_shore', 'north'),
    ('rzeka', 'mint_meadow', 'east', 'riverbank', 'west'),
    ('las', 'deep_grove', 'west', 'forest_edge', 'east'),
)
_LEGACY_OPPOSITE = {'north':'south', 'south':'north', 'east':'west', 'west':'east'}


def legacy_border_id(key: str, side: str, step: int) -> str:
    return f'v116_old_border_{key}_{side}_{step:02d}'


def install_old_border_routes(rooms):
    """Zamień trzy skróty międzystrefowe na drogi kończące się na granicy.

    Każdy stary pokój zostaje i utrzymuje wszystkie atrybuty poza konkretnym
    przekierowywanym wyjściem. Questy, łowiska, profesje, spawny, bossowie
    i zapisy nie wymagają migracji. Walidacja poprzedza modyfikacje mapy.
    """
    created = {}
    verified = []
    for key, old_a, forward_a, old_b, forward_b in _LEGACY_BORDER_ROUTES:
        a, b = rooms.get(old_a), rooms.get(old_b)
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise ValueError(f'Brak historycznych wejsc granicznych: {key}')
        if a.get('zone') == b.get('zone'):
            raise ValueError(f'Trasa {key} nie prowadzi do osobnej strefy')
        if (_LEGACY_OPPOSITE[forward_a] != forward_b
                or a.get('exits', {}).get(forward_a) != old_b
                or b.get('exits', {}).get(forward_b) != old_a):
            raise ValueError(f'Nieprawidlowa dawna brama {old_a} - {old_b}')
        verified.append((key, old_a, forward_a, old_b, forward_b))
        for side, old, forward in (('a', old_a, forward_a), ('b', old_b, forward_b)):
            zone = rooms[old]['zone']
            back = _LEGACY_OPPOSITE[forward]
            opposite = 'b' if side == 'a' else 'a'
            for step in range(1, LEGACY_BORDER_LENGTH+1):
                rid = legacy_border_id(key, side, step)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja pokoju na granicy: {rid}')
                backwards = old if step == 1 else legacy_border_id(key, side, step-1)
                onwards = (legacy_border_id(key, opposite, LEGACY_BORDER_LENGTH)
                           if step == LEGACY_BORDER_LENGTH
                           else legacy_border_id(key, side, step+1))
                created[rid] = {
                    'zone': zone,
                    'name': f'Droga graniczna {zone} — odcinek {step}',
                    'desc': (f'{zone}. Droga graniczna, odcinek {step} z 12. '
                             f'Przejście do innej krainy jest na końcu tej drogi.'),
                    'exits': {back: backwards, forward: onwards},
                    'exploration_ep': 0,
                    'v116_old_border': key,
                }
    if len(verified) != 3 or len(created) != 3*2*LEGACY_BORDER_LENGTH:
        raise ValueError('Niekompletne historyczne przejscia brzegowe')
    rooms.update(created)
    for key, old_a, forward_a, old_b, forward_b in verified:
        rooms[old_a]['exits'][forward_a] = legacy_border_id(key, 'a', 1)
        rooms[old_b]['exits'][forward_b] = legacy_border_id(key, 'b', 1)
    return len(created)


# v116.00.19: Łąki i Łąki Zielarskie — dwie historyczne drogi graniczne.
# Przejście między strefami następuje WYŁĄCZNIE na krańcach OBU dróg.
HERBAL_BORDER_LENGTH = 12
_HERBAL_BORDER_ROUTES = (
    ('mieta', 'meadow', 'east', 'mint_meadow', 'west'),
    ('ziola', 'flower_meadow', 'north', 'herb_meadow_hub', 'south'),
)
_HERBAL_OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def herbal_border_id(key: str, side: str, step: int) -> str:
    return f'v116_herbal_border_{key}_{side}_{step:02d}'


def install_herbal_border_routes(rooms):
    """Przenieś dwa przejścia Łąki–Łąki Zielarskie na kraniec OBU terenów.

    Weryfikuj cały plan przed jakąkolwiek zmianą; nie dotykaj starych ID,
    innych wyjść, spawnów, punktów profesji, questów i zapisu graczy.
    """
    created, plans = {}, []
    for key, old_a, forward_a, old_b, forward_b in _HERBAL_BORDER_ROUTES:
        a, b = rooms.get(old_a), rooms.get(old_b)
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise ValueError(f'Brak historycznej bramy Łąk Zielarskich: {key}')
        if (a.get('zone') == b.get('zone')
                or _HERBAL_OPPOSITE.get(forward_a) != forward_b
                or a.get('exits', {}).get(forward_a) != old_b
                or b.get('exits', {}).get(forward_b) != old_a):
            raise ValueError(f'Zmienione historyczne przejście: {old_a} / {old_b}')
        plans.append((key, old_a, forward_a, old_b, forward_b))
        for side, old, forward in (('a',old_a,forward_a),('b',old_b,forward_b)):
            zone = rooms[old]['zone']
            back = _HERBAL_OPPOSITE[forward]
            other = 'b' if side == 'a' else 'a'
            for step in range(1, HERBAL_BORDER_LENGTH + 1):
                rid=herbal_border_id(key,side,step)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja ID drogi: {rid}')
                backwards=(old if step==1 else herbal_border_id(key,side,step-1))
                onwards=(herbal_border_id(key,other,HERBAL_BORDER_LENGTH)
                         if step==HERBAL_BORDER_LENGTH else herbal_border_id(key,side,step+1))
                created[rid]={
                    'zone':zone,
                    'name':f'Skraj Łąk Zielarskich — {key}, droga {side}, odcinek {step}',
                    'desc':f'{zone}. Graniczna ścieżka {step} z {HERBAL_BORDER_LENGTH}.',
                    'exits':{back:backwards,forward:onwards},
                    'exploration_ep':0,
                    'v116_herbal_border':key,
                }
    if len(plans)!=2 or len(created)!=2*2*HERBAL_BORDER_LENGTH:
        raise ValueError('Niekompletna sieć dróg zielarskich')
    rooms.update(created)
    for key,old_a,forward_a,old_b,forward_b in plans:
        rooms[old_a]['exits'][forward_a]=herbal_border_id(key,'a',1)
        rooms[old_b]['exits'][forward_b]=herbal_border_id(key,'b',1)
    return len(created)


# v116.00.20: pięć historycznych tras — góry, wioska i jaskinie.
# Przejście do innej strefy następuje dopiero na ostatnich odcinkach OBU dróg.
MOUNTAIN_BORDER_LENGTH = 12
_MOUNTAIN_BORDER_ROUTES = (
    ('wioska', 'mountain_pass', 'east', 'mountain_village', 'west', 'Górski trakt do wioski'),
    ('trolle', 'mountain_troll_trail', 'south', 'troll_cave_entrance', 'north', 'Ścieżka do jaskini trolli'),
    ('lod', 'ice_pass', 'east', 'ice_cave_mouth', 'west', 'Lodowy przesmyk'),
    ('gobliny', 'goblin_camp', 'east', 'goblin_cave_mouth', 'west', 'Droga ku jaskini goblinów'),
    ('bandyci', 'frontier_watchpost', 'east', 'bandit_camp', 'west', 'Trakt ku obozowisku bandytów'),
)
_MOUNTAIN_OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def mountain_border_id(key: str, side: str, step: int) -> str:
    return f'v116_mountain_border_{key}_{side}_{step:02d}'


def install_mountain_border_routes(rooms):
    """Przenieś pięć rzeczywistych granic na koniec drogi po KAŻDEJ stronie.

    Przed mutacją zweryfikuj stare kierunki i ich powroty, strefy oraz kolizje.
    Zachowaj pozostałe przejścia, komnaty bossów, spawny i ID postaci.
    """
    created, plans = {}, []
    for key, old_a, forward_a, old_b, forward_b, label in _MOUNTAIN_BORDER_ROUTES:
        a, b = rooms.get(old_a), rooms.get(old_b)
        if not isinstance(a, dict) or not isinstance(b, dict):
            raise ValueError(f'Brak historycznej trasy: {key}')
        if (_MOUNTAIN_OPPOSITE.get(forward_a) != forward_b
                or a.get('zone') == b.get('zone')
                or a.get('exits', {}).get(forward_a) != old_b
                or b.get('exits', {}).get(forward_b) != old_a):
            raise ValueError(f'Nieprawidłowa historyczna granica: {old_a} / {old_b}')
        plans.append((key, old_a, forward_a, old_b, forward_b))
        for side, old, forward in (('a',old_a,forward_a), ('b',old_b,forward_b)):
            zone = rooms[old]['zone']
            back = _MOUNTAIN_OPPOSITE[forward]
            other = 'b' if side=='a' else 'a'
            for step in range(1, MOUNTAIN_BORDER_LENGTH+1):
                rid = mountain_border_id(key,side,step)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja ID traktu: {rid}')
                backwards = old if step==1 else mountain_border_id(key,side,step-1)
                onwards = (mountain_border_id(key,other,MOUNTAIN_BORDER_LENGTH)
                           if step==MOUNTAIN_BORDER_LENGTH else mountain_border_id(key,side,step+1))
                created[rid] = {
                    'zone': zone,
                    'name': f'{label} — odcinek {step}',
                    'desc': f'{zone}. Droga graniczna {step} z {MOUNTAIN_BORDER_LENGTH}.',
                    'exits': {back: backwards, forward: onwards},
                    'exploration_ep': 0,
                    'v116_mountain_border': key,
                }
    if len(plans) != 5 or len(created) != 5*2*MOUNTAIN_BORDER_LENGTH:
        raise ValueError('Niekompletne drogi graniczne Gór i Jaskiń')
    rooms.update(created)
    for key,old_a,forward_a,old_b,forward_b in plans:
        rooms[old_a]['exits'][forward_a] = mountain_border_id(key,'a',1)
        rooms[old_b]['exits'][forward_b] = mountain_border_id(key,'b',1)
    return len(created)

# Dostępność sal treningowych po historycznym dodaniu Hangaru Meca.
# Dawne wyjście martial/east do Sali Dyscypliny zostało zajęte przez Meca.
# Nie usuwaj żadnych starych kierunków: dodaj dwustronne wewnętrzne schody.
def install_guild_training_access(rooms):
    """Przywróć dojście do Mnicha i Strażnika bez ruszania Hangaru Meca.

    Wszystkie warunki muszą być spełnione przed pierwszą zmianą świata.
    Pozostałe tereny, NPC, bossowie, nagrody i zapis postaci bez zmian.
    """
    martial = rooms.get('guild_martial_hall')
    body = rooms.get('guild_body_hall')
    mec = rooms.get('guild_mec_chamber')
    monk = rooms.get('guild_monk_chamber')
    guardian = rooms.get('guild_guardian_chamber')
    if any(not isinstance(room, dict) or room.get('zone') != 'Gildia Dusz'
           for room in (martial, body, mec, monk, guardian)):
        raise ValueError('Brak sal klasowych Gildii Dusz')
    martial_exits = martial.get('exits')
    body_exits = body.get('exits')
    mec_exits = mec.get('exits')
    if any(not isinstance(exits, dict)
           for exits in (martial_exits, body_exits, mec_exits)):
        raise ValueError('Nieprawidlowa mapa przejsc Gildii Dusz')
    if (martial_exits.get('east') != 'guild_mec_chamber'
            or mec_exits.get('south') != 'guild_martial_hall'
            or body_exits.get('west') != 'guild_martial_hall'
            or body_exits.get('north') != 'guild_monk_chamber'
            or body_exits.get('east') != 'guild_guardian_chamber'
            or monk.get('exits', {}).get('west') != 'guild_body_hall'
            or guardian.get('exits', {}).get('west') != 'guild_body_hall'):
        raise ValueError('Zmodyfikowane stare przejscia sal treningowych')
    if 'down' in martial_exits or 'up' in body_exits:
        raise ValueError('Zajety kierunek schodow sal treningowych')
    martial_exits['down'] = 'guild_body_hall'
    body_exits['up'] = 'guild_martial_hall'
    return 2



# Trzy historyczne, zwykłe szlaki w obrębie jednej strefy prowadziły
# tylko w jednym kierunku. Zachowujemy wszystkie dawne wyjścia;
# brakujące POWROTY dodajemy do wolnych kierunków docelowych.
# Floor 0 i arena Serpentariusa są wykluczone: to specjalne bramki.
_HISTORICAL_RETURN_PATHS = (
    ('crossroads', 'west', 'deep_grove', 'south', 'Dzicz'),
    ('cinder_ravine', 'north', 'ember_ruins', 'west', 'Popielne Pustkowia'),
    ('absolute_gallery', 'north', 'crown_stair', 'west', 'Korona Świata'),
)


def install_historical_return_paths(rooms):
    """Dodaj dokładnie trzy bezpieczne wyjścia powrotne, atomowo.

    Trasa powrotna nie musi mieć przeciwnego kierunku kompasu:
    nie wolno nadpisywać istniejących przejść z docelowego pokoju.
    Nie podłącza to nowych stref ani nie dotyka bramek bossów.
    """
    planned = []
    for source_id, direction, destination_id, return_direction, zone in _HISTORICAL_RETURN_PATHS:
        source = rooms.get(source_id)
        destination = rooms.get(destination_id)
        if (not isinstance(source, dict) or not isinstance(destination, dict)
                or source.get('zone') != zone or destination.get('zone') != zone):
            raise ValueError(f'Nieprawidlowa strefa trasy powrotnej: {source_id}')
        source_exits = source.get('exits')
        destination_exits = destination.get('exits')
        if (not isinstance(source_exits, dict) or not isinstance(destination_exits, dict)
                or source_exits.get(direction) != destination_id):
            raise ValueError(f'Zmieniona dawna droga: {source_id}/{direction}')
        if source_id in destination_exits.values():
            raise ValueError(f'Droga powrotna juz istnieje: {destination_id}')
        if return_direction in destination_exits:
            raise ValueError(f'Zajety kierunek powrotny: {destination_id}/{return_direction}')
        planned.append((destination_exits, return_direction, source_id))
    if len(planned) != len(_HISTORICAL_RETURN_PATHS):
        raise ValueError('Niekompletny zestaw drog powrotnych')
    # Zmiana rozpoczyna się dopiero po pełnym sprawdzeniu WSZYSTKICH par.
    for exits, direction, target in planned:
        exits[direction] = target
    return len(planned)
