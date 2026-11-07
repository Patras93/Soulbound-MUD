# -*- coding: utf-8 -*-
"""v107 staging: living, solo-friendly diversity in existing Chitynowy Tron.

Pure additive registries; no database writes, legacy IDs, raid mechanics or
mandatory party requirements. Installed only after v3.10 authored realms.
"""
from __future__ import annotations

from data.catalog_mutations import catalog_assign, catalog_set_path
from world.legends_v3100 import OPPOSITE, REALMS

PREFIX = 'v10700_insects'
LEGACY = 'v3100_insects'
ZONE = next(spec[1] for spec in REALMS if spec[0] == 'insects')

# Old room numbers are stable: 0 gate, 1 market, 3 archive, 5 hornet nest,
# 6 mantis track, 7 chitin mine, 8 mushroom garden, 9 larvae sanctuary.
HABITATS = (
    ('hornets', 5, 'Zewnętrzne Gniazdo Szerszeni',
     'Gęsty rój patroluje tunele. Ze ścian wystają chitynowe komory.'),
    ('marsh', 8, 'Bagna Komarów',
     'Płytka woda i toksyczne opary. Nad wodą krążą komary i ważki.'),
    ('mantis', 6, 'Ukryty Matecznik Modliszek',
     'Przemykające modliszki strzegą młodych. Wyjście prowadzi z powrotem na szlak.'),
    ('ants', 7, 'Tunele Mrówczych Wojowników',
     'Pod ziemią rozciągają się suche korytarze mrówek i termitów.'),
    ('beetles', 10, 'Skalny Trakt Chrząszczy',
     'Rogate żuki i skarabeusze toczą ciężkie pancerze po skalnych stopniach.'),
    ('bees', 2, 'Kwiecista Pasieka Ula',
     'Dziki rój zbiera pyłek. W pobliżu krążą bojowe pszczoły i osy.'),
    ('moths', 9, 'Grota Świetlików i Ciem',
     'Migoczące światło odsłania skryte motyle i larwy.'),
    ('locusts', 4, 'Łąka Szarańczy i Cykad',
     'Pośród suchej trawy rozbrzmiewa cykanie; stada szarańczy skaczą z liścia na liść.'),
)

# Key, Polish display name, habitat index, native elemental affinity, loot family,
# stage offset from 120, tier (only last two are elite; no raid/boss gate).
INSECTS = (
    ('hornet_scout', 'Szerszeń Zwiadowca', 0, 'physical', 'chitin', 12, 'normal'),
    ('hornet_venom', 'Jadowity Szerszeń', 0, 'poison', 'venom', 20, 'normal'),
    ('hornet_guard', 'Szerszeń Strażnik Gniazda', 0, 'physical', 'chitin', 30, 'normal'),
    ('hornet_giant', 'Olbrzymi Szerszeń', 0, 'poison', 'venom', 39, 'normal'),
    ('wasp_hunter', 'Osa Łowczyni', 5, 'physical', 'wing', 15, 'normal'),
    ('wasp_amber', 'Osa Bursztynowa', 5, 'poison', 'wax', 25, 'normal'),
    ('bee_warrior', 'Pszczoła Bojowa', 5, 'physical', 'wax', 15, 'normal'),
    ('bumblebee', 'Trzmiel Strażnik', 5, 'physical', 'pollen', 22, 'normal'),
    ('ant_warrior', 'Mrówka Wojowniczka', 3, 'physical', 'chitin', 13, 'normal'),
    ('fire_ant', 'Mrówka Ognista', 3, 'fire', 'venom', 28, 'normal'),
    ('termite', 'Termit Żołnierz', 3, 'physical', 'chitin', 22, 'normal'),
    ('mantis_hunter', 'Modliszka Łowczyni', 2, 'physical', 'chitin', 24, 'normal'),
    ('mantis_shadow', 'Modliszka Cienia', 2, 'shadow', 'wing', 35, 'normal'),
    ('bombardier_beetle', 'Chrząszcz Bombardier', 4, 'fire', 'chitin', 30, 'normal'),
    ('stag_beetle', 'Żuk Rogacz', 4, 'physical', 'chitin', 26, 'normal'),
    ('scarab', 'Opancerzony Skarabeusz', 4, 'physical', 'chitin', 33, 'normal'),
    ('mosquito', 'Komar Bagienny', 1, 'poison', 'venom', 13, 'normal'),
    ('dragonfly', 'Ważka Burzowa', 1, 'lightning', 'wing', 25, 'normal'),
    ('night_moth', 'Ćma Nocna', 6, 'shadow', 'wing', 20, 'normal'),
    ('poison_butterfly', 'Motyl Jadowity', 6, 'poison', 'pollen', 28, 'normal'),
    ('locust', 'Szarańcza Żarłoczna', 7, 'physical', 'chitin', 18, 'normal'),
    ('grasshopper', 'Konik Polny Ostronogi', 7, 'physical', 'wing', 18, 'normal'),
    ('firefly', 'Świetlik Kryształowy', 6, 'holy', 'pollen', 27, 'normal'),
    ('cicada', 'Cykada Echa', 7, 'arcane', 'wing', 35, 'normal'),
    ('hornet_matriarch', 'Matriarcha Szerszeni', 0, 'poison', 'venom', 67, 'elite'),
    ('mantis_matriarch', 'Pradawna Modliszka', 2, 'shadow', 'chitin', 65, 'elite'),
)

MATERIALS = (
    ('chitin', 'Twarda Chityna', 'Pancerz owada odzyskany po walce.'),
    ('venom', 'Jad Szerszenia', 'Silna toksyna pozyskana z jadowitych owadów.'),
    ('wax', 'Wosk Wielkiego Ula', 'Wosk używany przez dzikie kolonie.'),
    ('pollen', 'Pyłek Królowej', 'Rzadki pyłek ze skrzydeł i kwiatów krainy.'),
    ('wing', 'Skrzydło Owadzie', 'Delikatne, lecz wytrzymałe skrzydło.'),
)

# The first twelve hunts are repeatable; two elite hunts are unique.
HUNT_TARGETS = (0, 1, 2, 3, 4, 6, 8, 9, 11, 13, 16, 17, 23)


def planned_ids():
    return {
        'rooms': {f'{PREFIX}_{slug}' for slug, *_ in HABITATS},
        'mobs': {f'{PREFIX}_{slug}' for slug, *_ in INSECTS},
        'items': {f'{PREFIX}_{slug}' for slug, *_ in MATERIALS},
        'npcs': {f'{PREFIX}_researcher', f'{PREFIX}_beekeeper'},
        'quests': {f'{PREFIX}_hunt_{i:02d}' for i in range(1, 16)} |
                  {f'{PREFIX}_collect_{i:02d}' for i in range(1, 6)},
    }


def install(rooms, mobs, spawns, npcs, quests, items, help_topics, help_aliases):
    """Install 8 linked rooms, 26 mobs, 5 items and 20 solo quests.

    Preflight checks every planned ID and source corridor before mutation; if an
    external mod takes an exit, installation refuses without damaging routes.
    """
    ids = planned_ids()
    catalogs = {'rooms': rooms, 'mobs': mobs, 'items': items,
                'npcs': npcs, 'quests': quests}
    present = {key: expected & catalogs[key].keys() for key, expected in ids.items()}
    if any(present.values()):
        if not all(present[key] == ids[key] for key in ids):
            raise RuntimeError('v107 Owady: częściowy katalog, nie nadpisuję')
        if any(f'{PREFIX}_{slug}' not in rooms.get(f'{LEGACY}_room_{source:02d}', {}).get('exits', {}).values()
               for slug, source, *_ in HABITATS):
            raise RuntimeError('v107 Owady: uszkodzone połączenie boczne')
        return {'already_installed': True, 'rooms': 0, 'mobs': 0, 'spawns': 0,
                'items': 0, 'npcs': 0, 'quests': 0}
    if (f'{PREFIX}_region' in help_topics or
            any(alias in help_aliases for alias in ('owady', 'kraina_owadow'))):
        raise RuntimeError('v107 Owady: kolizja pomocy')
    if len(INSECTS) != 26 or len({v[0] for v in INSECTS}) != 26:
        raise RuntimeError('v107 Owady: błąd katalogu gatunków')
    if not all(rooms.get(f'{LEGACY}_room_{i:02d}', {}).get('zone') == ZONE
               for i in range(12)):
        raise RuntimeError('v107 Owady: brakuje istniejącej Krainy Owadów')
    if not all(item_id in items for item_id in ('soul_shard',)):
        raise RuntimeError('v107 Owady: brak istniejącej nagrody duszy')
    for slug, *_ in MATERIALS:
        if slug not in {record[4] for record in INSECTS}:
            raise RuntimeError(f'v107 Owady: brak źródła surowca {slug}')

    directions = ('up', 'down', 'northeast', 'southeast', 'northwest',
                  'southwest', 'north', 'east', 'south', 'west')
    links = []
    reserved = set()
    for slug, source, *_ in HABITATS:
        src = f'{LEGACY}_room_{source:02d}'
        candidate = next((d for d in directions
                          if d not in rooms[src].get('exits', {}) and (src, d) not in reserved), None)
        if candidate is None:
            raise RuntimeError(f'v107 Owady: brak wolnego wyjścia w {src}')
        links.append((src, candidate, f'{PREFIX}_{slug}'))
        reserved.add((src, candidate))
    npc_positions = (f'{LEGACY}_room_03', f'{LEGACY}_room_09')
    if any(any(npc.get('room') == rid for npc in npcs.values()) for rid in npc_positions):
        raise RuntimeError('v107 Owady: wybrana sala NPC jest już zajęta')

    def add(catalog, code, key, record):
        catalog_assign(record, code, catalog, (key,))

    # All validations above; no existing ID is replaced.
    for slug, name, desc in MATERIALS:
        add(items, 'ITEMS', f'{PREFIX}_{slug}', {
            'name': name, 'type': 'craft_material', 'price': None,
            'sell_gold': 4, 'desc': desc, 'v107_insects': True,
        })
    for index, ((slug, _, name, desc), (src, direction, dst)) in enumerate(zip(HABITATS, links)):
        level = 130 + index * 6
        add(rooms, 'ROOMS', dst, {
            'name': name, 'zone': ZONE, 'desc': desc,
            'exits': {OPPOSITE[direction]: src},
            'generator_level': level, 'recommended_mastery': 120,
            'v107_insects': True,
        })
        catalog_set_path('ROOMS', rooms, (src, 'exits', direction), dst)
    for index, (slug, name, habitat, element, material, offset, rank) in enumerate(INSECTS):
        stage = 120 + offset
        boss = rank == 'elite'
        mid = f'{PREFIX}_{slug}'
        hp = stage * (420 if boss else 140)
        damage = stage * (8 if boss else 5)
        loot = {f'{PREFIX}_chitin': .65 if boss else .30,
                'soul_shard': .60 if boss else .18}
        loot[f'{PREFIX}_{material}'] = max(loot.get(f'{PREFIX}_{material}', 0.0),
                                           1.0 if boss else .65)
        add(mobs, 'MOB_TEMPLATES', mid, {
            'name': name, 'generator_level': stage,
            'max_hp': hp, 'damage': damage,
            'damage_type': 'magic' if element not in ('physical',) else 'physical',
            'attack_elements_v11339': (element,) if element != 'physical' else (),
            'stat_reward': stage * (180 if boss else 55),
            'class_xp_reward': stage * (9000 if boss else 2100),
            'soul_reward': stage * (3100 if boss else 750),
            'silver': stage * (2200 if boss else 450),
            'gold': 0, 'mithril': 0,
            'rank': rank, 'boss': boss, 'world_boss': False,
            'quest_target': mid, 'stationary_mob': True, 'auto_aggro': False,
            'drops': loot, 'v107_insects': True,
        })
        home = f'{PREFIX}_{HABITATS[habitat][0]}'
        # One location guaranteed for elites; two for normal recurring hunts.
        spawns.append((home, mid))
        if not boss:
            other = f'{LEGACY}_room_{HABITATS[habitat][1]:02d}'
            spawns.append((other, mid))

    researcher_id = f'{PREFIX}_researcher'
    beekeeper_id = f'{PREFIX}_beekeeper'
    researcher = 'Badacz Owadów Arlen'
    beekeeper = 'Strażniczka Ula Merya'
    quest_records = []
    for i, insect_idx in enumerate(HUNT_TARGETS, 1):
        slug, name, _, _, material, offset, _ = INSECTS[insect_idx]
        stage = 120 + offset
        qid = f'{PREFIX}_hunt_{i:02d}'
        giver = researcher if i <= 8 else beekeeper
        quest_records.append((qid, giver, 'kill', f'{PREFIX}_{slug}', 4,
                              f'Pokonaj cztery owady: {name}. Wróć do {giver}.',
                              stage, True, material))
    for i, (material, name, _) in enumerate(MATERIALS, 1):
        qid = f'{PREFIX}_collect_{i:02d}'
        quest_records.append((qid, beekeeper, 'collect', f'{PREFIX}_{material}', 3,
                              f'Po przyjęciu zadania zdobądź trzy sztuki: {name}. '
                              f'Wróć do {beekeeper}.', 150, True, material))
    for i, record in enumerate(INSECTS[-2:], 14):
        slug, name, _, _, material, offset, _ = record
        qid = f'{PREFIX}_hunt_{i:02d}'
        quest_records.append((qid, researcher, 'kill', f'{PREFIX}_{slug}', 1,
                              f'Pokonaj elitarnego przeciwnika: {name}. '
                              f'Wróć do {researcher}.', 120 + offset, False, material))
    for qid, giver, kind, target, needed, description, stage, repeatable, material in quest_records:
        add(quests, 'QUESTS', qid, {
            'name': f'Kraina Owadów: {description.split(". ")[0]}',
            'giver': giver, 'kind': kind, 'target': target,
            'needed': needed, 'description': description,
            'generator_level': stage,
            'character_xp_reward': stage * (3300 if repeatable else 9000),
            'reward_stat_progress': stage * 900,
            'reward_silver': stage * (1700 if repeatable else 5000),
            'reward_gold': 0, 'reward_mithril': 0,
            'reward_items': {f'{PREFIX}_{material}': 2},
            'repeatable': repeatable,
            **({'repeat_cooldown': 3600} if repeatable else {}),
            'v107_insects': True,
        })
    researcher_qids = tuple(qid for qid, giver, *_ in quest_records if giver == researcher)
    beekeeper_qids = tuple(qid for qid, giver, *_ in quest_records if giver == beekeeper)
    add(npcs, 'NPCS', researcher_id, {
        'name': researcher, 'room': npc_positions[0],
        'dialogue': 'Badam szerszenie, modliszki i inne owady. Wpisz quest list.',
        'specialist_quests': researcher_qids, 'v107_insects': True,
    })
    add(npcs, 'NPCS', beekeeper_id, {
        'name': beekeeper, 'room': npc_positions[1],
        'dialogue': 'Kolonie potrzebują pyłku, wosku i chityny. Wpisz quest list.',
        'specialist_quests': beekeeper_qids, 'v107_insects': True,
    })
    help_topics[f'{PREFIX}_region'] = [
        'Kraina Owadów — Chitynowy Tron: wejście przez Galerię Ośmiu Bram.',
        'Szerszenie, osy, pszczoły, mrówki, modliszki, chrząszcze, komary, ważki, ćmy i inne gatunki.',
        'Osiem nowych bocznych lokacji; kierunki sprawdź przez ex. Brak automatycznej agresji.',
        'Zadania: Badacz Owadów Arlen w Księdze Feromonów; Strażniczka Ula Merya w Świątyni Larw.',
        'Zadania można wykonać samodzielnie; nowe elity nie są rajdami.',
    ]
    help_aliases['owady'] = f'{PREFIX}_region'
    help_aliases['kraina_owadow'] = f'{PREFIX}_region'
    return {
        'already_installed': False, 'rooms': len(HABITATS),
        'mobs': len(INSECTS), 'spawns': len(INSECTS) * 2 - 2,
        'items': len(MATERIALS), 'npcs': 2, 'quests': len(quest_records),
        'elite_mobs': 2, 'raids': 0,
    }
