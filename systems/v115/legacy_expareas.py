# -*- coding: utf-8 -*-
"""v115: additional hunting grids for five verified legacy zones.

Never replace an old room, boss, quest or resource site; only attach new
branches after the older zone builder has registered the original rooms.
"""
from data.catalog_mutations import catalog_assign, catalog_set_path

WIDTH = 12
HEIGHT = 12
# Existing, stable entry rooms and enemies, never new mandatory templates.
AREAS = (
    ('kult', 'Ruiny Kultystów', 'cult_ruins_gate', ('cult_acolyte', 'cult_blade', 'cult_void_seer'), 75),
    ('bestie', 'Legowisko Bestii', 'beast_lair_mouth', ('beast_cave_stalker', 'beast_ironhide_boar', 'beast_root_bear'), 70),
    ('nekropolia', 'Nekropolia', 'necropolis_gate', ('necro_tomb_guard', 'necro_bone_knight', 'necro_mourning_spirit'), 115),
    ('kanaly', 'Kanały Pod Miastem', 'sewer_runoff', ('sewer_plague_rat', 'sewer_slime', 'sewer_smuggler'), 40),
    ('lod', 'Lodowe Jaskinie', 'ice_cave_mouth', ('ice_fang_wolf', 'ice_crystal_golem', 'ice_wraith'), 105),
)
NAMES = ('Zarośnięty trakt', 'Rozstaje śladów', 'Podziemne obejście', 'Przecięty szlak',
         'Kamienna galeria', 'Stary przesmyk', 'Pobojowisko', 'Boczna dolina',
         'Zwalony mur', 'Ciemna polana', 'Zapomniana ścieżka', 'Zniszczona brama')
DIRECTIONS = (('up', 'down'), ('down', 'up'), ('west', 'east'), ('south', 'north'))

def room_id(key, x, y):
    return f'v115_legacy_{key}_{x:02d}_{y:02d}'

def expand(rooms, templates, spawns):
    """Idempotent catalog registration, one physical route into each extension."""
    # First validate every target so a missing old entry cannot cause partial installation.
    for _key, _zone, _anchor, _enemies, _level in AREAS:
        if _anchor not in rooms:
            raise ValueError(f'Brak dotychczasowego wejścia do krainy: {_zone} ({_anchor})')
        if any(_mob not in templates for _mob in _enemies):
            raise ValueError(f'Brak starych potworów w {_zone}')
    # Preflight the FULL batch before modifying any catalog. A broken entry
    # cannot leave earlier regions partially installed.
    plans = []
    for key, zone, anchor, enemies, level in AREAS:
        entry = room_id(key, 0, 0)
        anchor_exits = rooms[anchor].get('exits', {})
        matching = [(a, b) for a, b in DIRECTIONS if anchor_exits.get(a) == entry]
        free = next(((a, b) for a, b in DIRECTIONS if a not in anchor_exits), None)
        if matching:
            outward, backward = matching[0]
        elif free:
            outward, backward = free
        else:
            raise ValueError(f'Brak wolnego wyjścia w {anchor} – bez nadpisywania istniejących dróg')
        # All existing rooms must belong to this exact extension. A partial
        # or foreign installation is not silently replaced.
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = room_id(key, x, y)
                if rid in rooms and rooms[rid].get('v115_legacy_expansion') != key:
                    raise ValueError(f'Obca lokacja o identyfikatorze: {rid}')
        plans.append((key, zone, anchor, enemies, level, outward, backward))
    created = []
    additions = []
    for key, zone, anchor, enemies, level, outward, backward in plans:
        entry = room_id(key, 0, 0)
        anchor_exits = rooms[anchor].setdefault('exits', {})
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = room_id(key, x, y)
                exits = {}
                if x: exits['west'] = room_id(key, x-1, y)
                if x+1 < WIDTH: exits['east'] = room_id(key, x+1, y)
                if y: exits['south'] = room_id(key, x, y-1)
                if y+1 < HEIGHT: exits['north'] = room_id(key, x, y+1)
                if (x, y) == (0, 0): exits[backward] = anchor
                payload = {
                    'zone': zone, 'name': NAMES[(x*3 + y*5) % len(NAMES)] + ' — ' + zone,
                    'desc': f'{zone}. Odcinek wyprawy {x+1} na {y+1}; różne obejścia prowadzą dalej przez rozległy teren.',
                    'exits': exits, 'generator_level': level,
                    'exploration_ep': (5 + min(13, level//15) + (x+y)//4) if (x+y)%2 == 0 else 2,
                    'v115_legacy_expansion': key,
                }
                if rid in rooms:
                    if rooms[rid] != payload:
                        raise ValueError(f'Kolizja ze zmienioną lokacją: {rid}')
                else:
                    catalog_assign(payload, 'ROOMS', rooms, (rid,))
                    created.append(rid)
                if (x+y)%2 == 0:
                    mob = enemies[(x+2*y) % len(enemies)]
                    if (rid, mob) not in spawns:
                        spawns.append((rid, mob))
                        additions.append((rid, mob))
        if anchor_exits.get(outward) != entry:
            catalog_set_path('ROOMS', rooms, (anchor, 'exits', outward), entry)
    return {'new_rooms': len(created), 'new_spawns': len(additions), 'areas': len(AREAS)}
