# -*- coding: utf-8 -*-
"""Rozległe zwykłe expowiska historycznych stref 30–48 pokoi.

Wejścia na krańcach historycznych tras i siatek; bez zmian EXP, bossów czy SQLite.
"""
from __future__ import annotations
WIDTH = HEIGHT = 12
OPPOSITE={'west':'east','east':'west','north':'south','south':'north'}
SPECS = (('podziemia', 'v0100_podziemia_023', 'Podziemia', ('crypt_wraith', 'skeleton', 'crystal_guardian')), ('straznica', 'v0100_ruiny_straznicy_006', 'Ruiny Strażnicy', ('ruin_goblin_looter', 'ruin_shieldbearer', 'ruin_watchman', 'ruin_runekeeper')), ('wybrzeze', 'v0100_wybrzeze_028', 'Wybrzeże', ('coast_rock_crab', 'coast_sea_raider')), ('bagna', 'v0100_bagna_008', 'Bagna', ('swamp_crawler', 'swamp_serpent', 'swamp_mire_witch')), ('pustynia', 'v0100_pustynia_008', 'Pustynia', ('desert_raider', 'dune_scorpion', 'sand_wraith')), ('korona', 'v0100_korona_swiata_010', 'Korona Świata', ('timeless_magister', 'crown_sentinel', 'worldcrown_echo', 'absolute_guardian')), ('popiol', 'v0100_popielne_pustkowia_010', 'Popielne Pustkowia', ('cinder_wraith', 'ash_revenant', 'charred_colossus', 'ash_seer')), ('niebo', 'v0100_rozbite_niebo_010', 'Rozbite Niebo', ('skybreaker', 'storm_seraph', 'thunder_harrier', 'cloud_titan')), ('pustka', 'v0100_wybrzeze_pustki_010', 'Wybrzeże Pustki', ('black_tide_oracle', 'void_mariner', 'starless_knight', 'abyssal_manta')), ('gobliny', 'v0100_jaskinie_goblinow_006', 'Jaskinie Goblinów', ('goblin_spearman', 'goblin_cave_guard', 'goblin_shaman')), ('las', 'v0100_las_szeptow_006', 'Las Szeptów', ('shadow_wolf', 'shadow_wolf_stalker', 'shadow_wolf_howler')), ('bandyci', 'v0100_obozowiska_bandytow_006', 'Obozowiska Bandytów', ('bandit_scout', 'bandit', 'bandit_crossbowman')), ('trolle', 'v0100_jaskinia_trolli_020', 'Jaskinia Trolli', ('deep_troll_warrior', 'deep_troll_shaman', 'mountain_troll')))


def sector_id(slug,x,y):
    return f'v11623_exp_{slug}_{x:02d}_{y:02d}'


def install_remaining_grindfields(rooms, mob_spawns, mob_templates):
    # Preflight nie zapisuje ani jednego pokoju, zanim nie sprawdzi całości.
    if not isinstance(mob_spawns,list):
        raise ValueError('Niepoprawny katalog spawnów')
    new, spawns, anchors={},[],[]
    for slug,anchor,zone,mobs in SPECS:
        old=rooms.get(anchor)
        if not isinstance(old,dict) or old.get('zone')!=zone:
            raise ValueError(f'Brak historycznego krańca {anchor}')
        exits=old.get('exits')
        if not isinstance(exits,dict) or 'east' in exits:
            raise ValueError(f'Wschód zajęty przy {anchor}')
        if any(m not in mob_templates for m in mobs):
            raise ValueError(f'Brak oryginalnego potwora: {zone}')
        anchors.append((anchor,slug))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid=sector_id(slug,x,y)
                if rid in rooms or rid in new:
                    raise ValueError(f'Kolizja identyfikatora {rid}')
                ways={}
                if x: ways['west']=sector_id(slug,x-1,y)
                if x+1<WIDTH: ways['east']=sector_id(slug,x+1,y)
                if y: ways['south']=sector_id(slug,x,y-1)
                if y+1<HEIGHT: ways['north']=sector_id(slug,x,y+1)
                if (x,y)==(0,HEIGHT//2):ways['west']=anchor
                new[rid]={
                    'zone':zone,
                    'name':f'Rozległe rubieże — {zone}',
                    'desc':f'{zone}. Pas {y+1} z 12, sektor {x+1} z 12.',
                    'exits':ways,
                    'exploration_ep':0,
                    'v11623_grindfield':slug,
                }
                if (x+y)%2==0:
                    spawns.append((rid,mobs[(x+3*y)%len(mobs)]))
    if (len(anchors),len(new),len(spawns))!=(13,1872,936):
        raise ValueError('Niekompletne expowiska')
    for rid,room in new.items():
        for direction,target in room['exits'].items():
            if target in new:
                other=new[target]
            else:
                other=rooms.get(target)
            if not other or (target not in {a for a, _ in anchors} and other['exits'].get(OPPOSITE[direction])!=rid):
                raise ValueError(f'Brak poprawnej drogi powrotnej: {rid} -> {target}')
    rooms.update(new)
    for anchor,slug in anchors:
        rooms[anchor]['exits']['east']=sector_id(slug,0,HEIGHT//2)
    mob_spawns.extend(spawns)
    return len(anchors),len(new),len(spawns)


# v116.00.24: cztery podstawowe expowiska, wcześniej 66–108 pokoi.
# Dodatkowe sektory są jedną krainą z istniejącą strefą, nie osobnym portalem.
CORE_GRIND_SPECS = (('zielarskie', 'v0100_laki_zielarskie_019', 'Łąki Zielarskie', ('meadow_field_wolf', 'meadow_giant_wasp', 'meadow_wild_boar')), ('gory', 'v0100_gory_005', 'Góry', ('mountain_ice_wolf', 'mountain_stone_ram', 'mountain_harpy', 'mountain_troll')), ('laki', 'v0100_laki_027', 'Łąki', ('meadow_giant_wasp', 'meadow_field_wolf', 'meadow_wild_boar')), ('dzicz', 'v0100_dzicz_009', 'Dzicz', ('shadow_wolf', 'wild_ash_boar', 'wild_thorn_wolf', 'bandit')))


def core_sector_id(slug, x, y):
    return f'v11624_core_{slug}_{x:02d}_{y:02d}'


def install_core_region_grindfields(rooms, mob_spawns, mob_templates):
    # Walidacja całego rozszerzenia przed dotknięciem mapy: po błędzie brak częściowej instalacji.
    if not isinstance(mob_spawns, list):
        raise ValueError('Katalog spawnów podstawowych expowisk musi być listą')
    new_rooms, new_spawns, anchors = {}, [], []
    for slug, anchor, zone, mobs in CORE_GRIND_SPECS:
        original = rooms.get(anchor)
        if not isinstance(original, dict) or original.get('zone') != zone:
            raise ValueError(f'Brak historycznego krańca: {anchor}')
        exits = original.get('exits')
        if not isinstance(exits, dict) or 'east' in exits:
            raise ValueError(f'Zajęty wschód końcowej trasy: {anchor}')
        own_neighbors = sum(rooms.get(target, {}).get('zone') == zone for target in exits.values())
        if own_neighbors != 1 or any(rooms.get(target, {}).get('zone') != zone for target in exits.values()):
            raise ValueError(f'Wejście nie jest końcem zwykłej trasy: {anchor}')
        if any(mob not in mob_templates for mob in mobs):
            raise ValueError(f'Brak oryginalnego przeciwnika: {zone}')
        anchors.append((anchor, slug))
        for y in range(12):
            for x in range(12):
                rid = core_sector_id(slug, x, y)
                if rid in rooms or rid in new_rooms:
                    raise ValueError(f'Powtórzony identyfikator sektora: {rid}')
                exits_new = {}
                if x > 0: exits_new['west'] = core_sector_id(slug, x-1, y)
                if x < 11: exits_new['east'] = core_sector_id(slug, x+1, y)
                if y > 0: exits_new['south'] = core_sector_id(slug, x, y-1)
                if y < 11: exits_new['north'] = core_sector_id(slug, x, y+1)
                if (x, y) == (0, 6): exits_new['west'] = anchor
                new_rooms[rid] = {
                    'zone': zone,
                    'name': f'{zone} — rozległy sektor {x+1}/{y+1}',
                    'desc': f'{zone}. Rozległe expowisko, kolumna {x+1} i rząd {y+1} z 12.',
                    'exits': exits_new,
                    'exploration_ep': 0,
                    'v11624_core_grindfield': slug,
                }
                if (x+y) % 2 == 0:
                    new_spawns.append((rid, mobs[(x+3*y) % len(mobs)]))
    if (len(anchors), len(new_rooms), len(new_spawns)) != (4, 576, 288):
        raise ValueError('Niekompletne cztery expowiska')
    opposite = {'north':'south','south':'north','east':'west','west':'east'}
    anchor_set = {anchor for anchor, _ in anchors}
    for rid, room in new_rooms.items():
        for direction, target in room['exits'].items():
            if target in anchor_set: continue  # Dopinamy powrót po pomyślnym preflight.
            other = new_rooms.get(target)
            if not other or other['exits'].get(opposite[direction]) != rid:
                raise ValueError(f'Niespójna siatka: {rid} -> {target}')
    rooms.update(new_rooms)
    for anchor, slug in anchors:
        rooms[anchor]['exits']['east'] = core_sector_id(slug, 0, 6)
    mob_spawns.extend(new_spawns)
    return len(anchors), len(new_rooms), len(new_spawns)
