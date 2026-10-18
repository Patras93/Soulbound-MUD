# -*- coding: utf-8 -*-
"""v11: twelve authored dungeon chapters and a cross-region story.

Purely additive catalog registration. No room reuse, no traps, no destructive
SQLite changes. Dungeon rooms are walked in the ordinary world, not teleports.
Original infinite-dungeon portals/checkpoints are left unchanged.
"""
from systems.eternal_glory_world_v1100 import REGIONS
from systems.forgotten_horizons_v1000 import _insert, _link, _enemy

FLOORS_PER_DUNGEON = 10
SIGNIFICANT_FLOOR = 9
DUNGEON_ROOM_IDS = frozenset(
    f'v1100_vault_{key}_{i:02d}' for key,*_ in REGIONS
    for i in range(FLOORS_PER_DUNGEON)
)
DUNGEON_EP_IDS = frozenset(
    f'v1100_vault_{key}_{SIGNIFICANT_FLOOR:02d}' for key,*_ in REGIONS
)
DUNGEON_QUEST_IDS = frozenset(
    f'v1100_vault_{key}_quest_{i}' for key,*_ in REGIONS for i in (1, 2)
)


def install(rooms, npcs, mobs, spawns, quests, items, help_topics, help_aliases):
    count = 0
    for index, (key, zone, level, element, guide, elite, boss, places) in enumerate(REGIONS):
        prefix = f'v1100_vault_{key}'
        dungeon_zone = f'{zone} — Podziemia Pradawnych'
        for floor in range(FLOORS_PER_DUNGEON):
            room_id = f'{prefix}_{floor:02d}'
            is_final = floor == SIGNIFICANT_FLOOR
            # A fixed authored dungeon must never pretend to be another
            # infinite-dungeon floor or a previously unlocked checkpoint.
            room = {
                'name': f'{dungeon_zone}: ' + (
                    'Pieczęć Zapomnianego Strażnika' if is_final
                    else f'Komnata {("Wejścia", "Echa", "Korzeni", "Wspomnień", "Znaków", "Przysiąg", "Cieni", "Wiatru", "Płomieni")[floor]}'
                ),
                'zone': dungeon_zone,
                'desc': (
                    f'Podziemia pod krainą {zone}. ' +
                    ('Odkrywasz unikalną pieczęć. EP jest przyznawane tylko raz.'
                     if is_final else 'Zwykły korytarz nie przyznaje EP. Bez pułapek.')
                ),
                'exits': {},
                'generator_level': min(800, level + 25 + 3*floor),
                'recommended_mastery': min(800, level + 25 + 3*floor),
                'exploration_ep': 5 if is_final else 0,
                'v1000_landmark': is_final,
                'v1100_vault': key,
                'v1100_eternal_glory': True,
                'v1100_no_traps': True,
            }
            _insert(rooms, 'ROOMS', room_id, room)
            if floor:
                _link(rooms, f'{prefix}_{floor-1:02d}', room_id)
        _link(rooms, f'v1100_eg_{key}_06', f'{prefix}_00')

        sentinel_id = f'{prefix}_sentinel'
        guardian_id = f'{prefix}_guardian'
        sentinel = _enemy(f'Widmo Podziemi: {zone}', min(800, level+30), element)
        guardian = _enemy(f'Strażnik Pieczęci: {zone}', min(800, level+85), element, boss=True)
        guardian['v1100_vault_boss'] = True
        guardian['fame_target'] = True
        guardian['v017_boss_phases'] = True
        _insert(mobs, 'MOB_TEMPLATES', sentinel_id, sentinel)
        _insert(mobs, 'MOB_TEMPLATES', guardian_id, guardian)
        for floor in (1, 4, 7):
            spawns.append((f'{prefix}_{floor:02d}', sentinel_id))
        spawns.append((f'{prefix}_09', guardian_id))

        story_item = f'{prefix}_seal'
        _insert(items, 'ITEMS', story_item, {
            'name': f'Pieczęć Zapomnianych: {zone}', 'type': 'resource',
            'price': None, 'sell_silver': (level+85)*400,
            'desc': f'Unikatowa relikwia z podziemi regionu {zone}.',
            'v1100_vault_reward': True,
        })
        guardian['drops'][story_item] = 1.0
        quest_1 = f'{prefix}_quest_1'
        quest_2 = f'{prefix}_quest_2'
        prior = f'v1100_eg_{key}_quest_2'
        _insert(quests, 'QUESTS', quest_1, {
            'name': f'{zone}: Oczyszczenie Podziemi', 'giver': guide,
            'kind': 'kill', 'target': sentinel_id, 'needed': 3,
            'requires_quest': prior,
            'description': f'Po pokonaniu strażnika krainy oczyść podziemia {zone}.',
            'generator_level': min(800,level+25), 'repeatable': False,
            'reward_silver': (level+25)*12500,
            'reward_gold': 0, 'reward_mithril': 0, 'reward_items': {},
        })
        _insert(quests, 'QUESTS', quest_2, {
            'name': f'{zone}: Pieczęć Wieczności', 'giver': guide,
            'kind': 'kill', 'target': guardian_id, 'needed': 1,
            'requires_quest': quest_1,
            'description': f'Odnajdź finał podziemi i pokonaj Strażnika Pieczęci: {zone}.',
            'generator_level': min(800,level+85), 'repeatable': False,
            'reward_silver': (level+85)*21000,
            'reward_gold': 0, 'reward_mithril': 0, 'reward_items': {},
        })
        npcs[f'v1100_eg_{key}_guide']['specialist_quests'] += (quest_1, quest_2)
        count += 1
    help_topics['podziemia11'] = [
        'Podziemia Pradawnych 11.0: dwanaście niezależnych wypraw po dziesięć komnat każda.',
        'Wejścia są na trasach nowych krain. W głębi czekają strażnicy pieczęci oraz dodatkowe zadania u miejscowych przewodników.',
        'Finałowa pieczęć każdego podziemia daje jednorazowo 5 EP. Zwykłe korytarze i miasta: 0 EP. Bez pułapek.',
        'To dodatkowe lochy fabularne; dotychczasowe nieskończone lochy i portale co dziesięć pięter pozostają bez zmian.',
    ]
    help_aliases['podziemia11'] = 'podziemia11'
    return {'dungeons':count,'rooms':len(DUNGEON_ROOM_IDS),
            'ep_landmarks':len(DUNGEON_EP_IDS),'quests':len(DUNGEON_QUEST_IDS)}
