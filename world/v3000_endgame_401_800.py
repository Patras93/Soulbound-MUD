# -*- coding: utf-8 -*-
"""v30: four physical, connected 401-800 world regions (not placeholder exp areas).

New data uses the same registries/room exits/spawner as the rest of Soulbound.
No changes to stored characters or the character progression formulas.
"""

REGIONS = (
    ('scarlet', 'Szkarłatne Pogranicze', 401, 500, 'world_crown_summit', 'up', 'down',
     ('Szkarłatna Brama', 'Dolina Czerwonego Pyłu', 'Kanion Płomiennych Kości', 'Wąwóz Rdzawych Szeptów', 'Prastara Rubież', 'Twierdza Szkarłatu'),
     ('Strażnik Rubieży', 'Żarłoczny Moloch', 'Czerwony Widmowy Mag', 'Pradawny Łowca'), 'Pan Szkarłatnej Rubieży', 'fire'),
    ('crystal', 'Kryształowe Bezmiary', 501, 600, 'v3000_scarlet_6', 'up', 'down',
     ('Przejście Kryształów', 'Błękitna Dolina', 'Komnaty Przełamanych Luster', 'Most Szeptających Kamieni', 'Świetlista Grań', 'Serce Bezmiarów'),
     ('Kryształowy Tytan', 'Widmowy Pryzmat', 'Kamienny Arcymag', 'Strażnik Światła'), 'Władczyni Kryształowych Bezmiarów', 'ice'),
    ('abyss', 'Otchłań Nieskończoności', 601, 700, 'v3000_crystal_6', 'up', 'down',
     ('Próg Otchłani Nieskończoności', 'Szlak Głębokich Ech', 'Czarne Filary', 'Rozpadlina Zapomnianych', 'Korytarz Zmierzchu', 'Komnata Nieskończoności'),
     ('Cień Nieskończoności', 'Pustkowy Olbrzym', 'Zabójca Otchłani', 'Adept Bezkresu'), 'Władca Nieskończoności', 'shadow'),
    ('eternal', 'Tron Wieczności', 701, 800, 'v3000_abyss_6', 'up', 'down',
     ('Brama Wieczności', 'Ogrody Zapomnianego Czasu', 'Droga Gwiazd', 'Sala Przysięgi', 'Schody Przeznaczenia', 'Tron Wieczności'),
     ('Wieczny Rycerz', 'Arcyserafin Losu', 'Strażnik Chronosfery', 'Widmo Gwiazd'), 'Awatar Wieczności', 'arcane'),
)


def install(rooms, mobs, spawns, exp_areas, zone_ids, categories, guides, target_power):
    """Install once in the original registries; safe on repeated import/tests."""
    areas = []
    for slug, zone, low, high, parent, parent_dir, return_dir, titles, enemies, boss_name, element in REGIONS:
        first = f'v3000_{slug}_1'
        if first in rooms:
            continue
        if parent not in rooms:
            raise RuntimeError(f'v30 missing gateway: {parent}')
        if parent_dir in rooms[parent].setdefault('exits', {}):
            raise RuntimeError(f'v30 gateway direction occupied: {parent}.{parent_dir}')
        for index, title in enumerate(titles, 1):
            rid = f'v3000_{slug}_{index}'
            stage = min(high, low + (index-1) * 19)
            exits = {}
            if index > 1:
                exits['south'] = f'v3000_{slug}_{index-1}'
            if index < len(titles):
                exits['north'] = f'v3000_{slug}_{index+1}'
            if index == 1:
                exits[return_dir] = parent
            rooms[rid] = {
                'zone': zone, 'name': title,
                'desc': f'{zone}. Droga dla bohaterow poziomow {low}-{high}; widoczne sa slady coraz silniejszych przeciwnikow. Nie ma pulapek.',
                'generator_level': stage, 'recommended_mastery': stage,
                'exits': exits,
            }
        rooms[parent]['exits'][parent_dir] = first
        for j, name in enumerate(enemies, 1):
            mid = f'v3000_{slug}_mob_{j}'
            stage = min(high, low + (j-1)*22)
            delta = stage-400
            hp = 18000 + delta*230 + j*1600
            dmg = 330 + delta*3 + j*14
            mobs[mid] = {
                'name': name, 'generator_level': stage, 'max_hp': hp, 'damage': dmg,
                'damage_type': 'magic' if j%2 == 0 else 'physical',
                'class_xp_reward': 50000 + delta*1100 + j*10000,
                'soul_reward': 12500 + delta*220 + j*1200,
                'stat_reward': 4500 + delta*45, 'silver': 1800 + delta*17,
                'gold': 20 + delta//10, 'mithril': 0,
                'drops': {'soul_shard': .35}, 'endgame_region_mastery': stage,
                'v3000_element': element,
            }
        final_mid = f'v3000_{slug}_boss'
        delta = high-400
        mobs[final_mid] = {
            'name': boss_name, 'generator_level': high,
            'max_hp': 650000 + delta*11000,
            'damage': 750 + delta*7, 'damage_type': 'magic',
            'class_xp_reward': 250000 + delta*6500,
            'soul_reward': 45000 + delta*1300,
            'stat_reward': 18000 + delta*200,
            'silver': 10000 + delta*95, 'gold': 120 + delta//2,
            'mithril': 1 + (delta//100),
            'drops': {'soul_shard': 1., 'soul_elixir': .45},
            'world_boss': True, 'boss_mechanic': 'endgame_region_boss',
            'boss_mechanic_text': 'Zagrozenie rosnie wraz z zakresem tego regionu.',
            'endgame_region_mastery': high, 'v3000_element': element,
            'leave_corpse': True,
        }
        for index in range(1, len(titles)):
            rid = f'v3000_{slug}_{index}'
            for j in (index%4 + 1, (index+1)%4 + 1):
                spawns.append((rid, f'v3000_{slug}_mob_{j}'))
        spawns.append((f'v3000_{slug}_6', final_mid))
        area_id = f'v3000_{slug}'
        guides[zone.lower()] = first
        zone_ids[zone] = area_id
        categories[area_id] = 'Endgame'
        target_power[area_id] = low
        areas.append({
            'id': area_id, 'name': zone,
            'aliases': (zone.casefold(),),
            'soul_min': low, 'soul_max': high,
            'mastery_min': low, 'mastery_max': high,
            'difficulty': f'endgame {low}-{high}', 'guide': zone.lower(),
            'enemies': ', '.join(enemies) + ' i ' + boss_name,
            'description': f'Otwarty region poziomow {low}-{high} z szescioma pokojami, czterema gatunkami potworow i bossem.',
            'note': f'Wejscie przez poprzednia kraine. Zalecany Level {low}+. Moby i nagrody sa rzeczywiste; nie wymaga Soul Level 100.',
        })
    return tuple(areas)
