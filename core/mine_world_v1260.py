# -*- coding: utf-8 -*-
"""Deterministic infinite geology and screen-reader-friendly mine routes.

No session state, random rolls, or mutable procedural generation: rebuilding a
room after a restart always produces the same feature and richness.
"""
from collections import deque
import hashlib
import math
from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS, MINE_DIRECTION_LABELS

FEATURES = {
    'ore_vein': ('Bogata żyła rudy', 'Pod skałą biegnie rozległa żyła cennej rudy.'),
    'lake': ('Podziemne jezioro', 'Słyszysz spokojną wodę głęboko pod ziemią.'),
    'cave': ('Naturalna jaskinia', 'Tunel otwiera się na rozległą naturalną jaskinię.'),
    'ruins': ('Zapomniane ruiny', 'Kamienne kolumny świadczą o dawnej cywilizacji.'),
    'chamber': ('Ukryta komnata', 'Wykopujesz zapieczętowaną komnatę dawnych górników.'),
    'vault': ('Strzeżony skarbiec', 'Odkrywasz skarbiec, którego pilnuje podziemny strażnik.'),
    'rare_ore': ('Legendarna żyła minerałów', 'Kryształy nieznanego pochodzenia połyskują w ścianie.'),
    'rock': ('Kamienny chodnik', 'Zwykła skała. Mogą tu jednak przebiegać nowe żyły.'),
    'lost_city': ('Opuszczone podziemne miasto', 'Słyszysz echo dawnych ulic i sal wykutych w skale.'),
    'underground_river': ('Rzeka Bezgwiezdna', 'Podziemny nurt omija naturalne filary skalne.'),
    'ancient_kingdom': ('Królestwo Głębin', 'Kamienne inskrypcje przypominają o nieznanej cywilizacji.'),
    'giant_cavern': ('Jaskinia Tysiąca Ech', 'Przed tobą ogromna pieczara o własnym mikroklimacie.'),
}

def geology_v1260(floor, x, y):
    floor, x, y = int(floor), int(x), int(y)
    if floor < 1:
        raise ValueError('Mine floor must be positive')
    distance = max(abs(x), abs(y))
    key = f'soulbound:mine:geology:1:{floor}:{x}:{y}'.encode('utf-8')
    digest = hashlib.blake2b(key, digest_size=12).digest()
    choice = int.from_bytes(digest[:4], 'big') % 10000
    # Root remains the familiar, safe central mine room.
    if x == y == 0:
        kind = 'rock'
    elif choice < 85 and floor >= 15 and distance >= 3:
        kind = 'vault'
    elif floor >= 55 and distance >= 5 and 8500 <= choice < 8575:
        kind = 'ancient_kingdom'
    elif floor >= 35 and distance >= 4 and 8575 <= choice < 8700:
        kind = 'lost_city'
    elif floor >= 25 and distance >= 3 and 8700 <= choice < 8900:
        kind = 'underground_river'
    elif floor >= 20 and distance >= 3 and 8900 <= choice < 9130:
        kind = 'giant_cavern'
    elif choice < 200 and floor >= 12:
        kind = 'rare_ore'
    elif choice < 540:
        kind = 'chamber'
    elif choice < 1000:
        kind = 'ruins'
    elif choice < 1650:
        kind = 'lake'
    elif choice < 2600:
        kind = 'cave'
    elif choice < 5900:
        kind = 'ore_vein'
    else:
        kind = 'rock'
    # Monotone, unbounded exploration richness; no 200/600 floor cap.
    richness = 1.0 + math.log1p(floor)/8.0 + math.log1p(distance)/5.0
    richness *= 1.0 + digest[4] / 255.0 * 0.22
    resource_bonus = {'rock':0, 'lake':0, 'cave':1, 'ore_vein':2,
                      'ruins':2, 'chamber':3, 'vault':4, 'rare_ore':5, 'lost_city':4, 'underground_river':2, 'ancient_kingdom':6, 'giant_cavern':3}[kind]
    reward = max(1, int((floor + distance + 10) * richness *
                        {'rock':.5,'lake':.5,'cave':1,'ore_vein':1.3,
                         'ruins':2.2,'chamber':3,'vault':8,'rare_ore':4.5,'lost_city':5,'underground_river':2,'ancient_kingdom':9,'giant_cavern':3}[kind]))
    return {'kind':kind, 'name':FEATURES[kind][0], 'description':FEATURES[kind][1],
            'floor':floor, 'x':x, 'y':y, 'distance':distance,
            'richness':richness, 'bonus_quantity':resource_bonus,
            'reward_gold':reward, 'has_guardian':kind == 'vault'}


def mine_route_v1260(cells, start, target=(0,0)):
    """Shortest walk over actually mined rooms (including diagonal corridors)."""
    discovered = {(int(x),int(y)) for x,y in cells} | {(0,0)}
    start = tuple(map(int, start)); target = tuple(map(int, target))
    if start not in discovered or target not in discovered:
        return None
    queue = deque([start]); paths = {start: ()}
    while queue:
        cell = queue.popleft()
        if cell == target:
            return paths[cell]
        for direction, (dx,dy) in HORIZONTAL_MINE_DIRECTIONS.items():
            nxt = (cell[0]+dx,cell[1]+dy)
            if nxt in discovered and nxt not in paths:
                paths[nxt] = paths[cell] + (direction,)
                queue.append(nxt)
    return None


def mine_map_lines_v1260(cells, floor, start, max_rooms=40):
    cells = {(int(x), int(y)) for x,y in cells} | {(0,0)}
    x, y = int(start[0]), int(start[1])
    lines = [f'MAPA KOPALNI: poziom {floor}. Twoje położenie X={x}, Y={y}. '
             f'Odkryto {len(cells)} komnat na tym piętrze.']
    for cx,cy in sorted(cells, key=lambda c:(max(abs(c[0]-x),abs(c[1]-y)),c[1],c[0]))[:max_rooms]:
        dirs = [MINE_DIRECTION_LABELS[k] for k,(dx,dy) in HORIZONTAL_MINE_DIRECTIONS.items()
                if (cx+dx,cy+dy) in cells]
        feature = geology_v1260(floor,cx,cy)
        label = 'TU JESTEŚ' if (cx,cy)==(x,y) else 'centralny szyb' if (cx,cy)==(0,0) else ''
        lines.append(f'X={cx}, Y={cy}. {feature["name"]}. '
                     f'Przejścia: {", ".join(dirs) if dirs else "brak"}. {label}'.strip())
    if len(cells)>max_rooms:
        lines.append(f'Pokazano najbliższe {max_rooms} odkryć z {len(cells)}. Użyj kopalnia droga.')
    return lines


def discovery_mineral_reward_v1260(geo):
    """Award a real, authored ore (usable/sellable in existing professions)."""
    if geo['kind'] not in ('vault','rare_ore','chamber','ruins','lost_city','ancient_kingdom','giant_cavern'):
        return None
    floor=int(geo['floor']); distance=int(geo['distance'])
    grade=floor + distance // 4
    ore='copper_ore'
    for minimum, item_id in (
        (3,'iron_ore'),(8,'silver_ore'),(15,'gold_ore'),
        (100,'cobalt_ore'),(120,'runestone_ore'),(140,'dragonsteel_ore'),
        (160,'astral_ore'),(180,'void_ore'),(200,'eternium_ore')):
        if grade>=minimum:
            ore=item_id
    amount=max(1,int(geo['richness'] * (1 + (3 if geo['kind']=='vault' else 1))))
    return ore,amount
