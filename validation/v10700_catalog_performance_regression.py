# -*- coding: utf-8 -*-
"""Verify that cached guide text and NPC patrol indexes preserve results."""
from __future__ import annotations
from unittest.mock import patch
from types import SimpleNamespace


def run() -> int:
    import world.living_npcs as living
    from player.session_mixins.guide_navigation import (
        SessionGuideNavigationMixin, _normalized_room_search_text_v107,
    )
    checks = 0
    fn = SessionGuideNavigationMixin.normalize_room_query
    obj = SessionGuideNavigationMixin()
    examples = {
        '  Góry-ŁĄKI   ': 'gory laki',
        'Mityczna_Wieża': 'mityczna wieza',
        'Miasto Dusz': 'miasto dusz',
        '': '',
        None: '',
        'A...  B': 'a b',
    }
    _normalized_room_search_text_v107.cache_clear()
    for value, expected in examples.items():
        assert fn(obj, value) == expected, (value, fn(obj, value))
        checks += 1
    fn(obj, 'Miasto Dusz')
    assert _normalized_room_search_text_v107.cache_info().hits >= 1
    checks += 1
    assert fn(obj, 'Miasto Dusz NOVA') != fn(obj, 'Miasto Dusz')
    checks += 1
    rooms = {
        'r0': {'zone': 'Miasto', 'exits': {'n': 'r1'}},
        'r1': {'zone': 'Miasto', 'exits': {'s': 'r0', 'e': 'r2'}},
        'r2': {'zone': 'Szlak', 'exits': {'w': 'r1'}},
    }
    mobs = {
        'normal': {'name': 'Wilk', 'rank': 'normal'},
        'boss': {'name': 'Król', 'rank': 'boss'},
        'dummy': {'name': 'Manekin', 'rank': 'normal'},
    }
    registry = SimpleNamespace(MOB_SPAWNS=(('r0','boss'),('r1','normal'),('r2','dummy')))
    quest_catalog = {'q': {'giver': 'Strażnik'}}
    npcs = {'a': {'name': 'Strażnik'}, 'b': {'name': 'Zwiadowca'}}
    with patch.object(living,'ROOMS',rooms), patch.object(living,'MOB_TEMPLATES',mobs), \
         patch.object(living,'content_registry',registry), \
         patch.object(living,'QUESTS',quest_catalog), patch.object(living,'NPCS',npcs):
        idx = living._hourly_mob_spawn_index_v107()
        assert idx == {'r1': {'normal'}}, idx
        checks += 1
        for room in ('r0','r1','r2','missing'):
            src={'room':room}
            assert living._choose_hourly_kill_target_v0712('a',src,idx) == \
                   living._choose_hourly_kill_target_v0712('a',src)
            checks += 1
        names=living._quest_giver_names_v107()
        assert living._npc_has_any_quest(npcs['a'],names)
        assert not living._npc_has_any_quest(npcs['b'],names)
        assert living._npc_has_any_quest(npcs['a'])
        checks += 3
        registry.MOB_SPAWNS = (('r0','boss'),('r2','normal'))
        new_index = living._hourly_mob_spawn_index_v107()
        assert new_index != idx
        checks += 1
    return checks


if __name__ == '__main__':
    print(f'V107 INDEXY KRAIN/NPC: {run()} checks PASS', flush=True)
