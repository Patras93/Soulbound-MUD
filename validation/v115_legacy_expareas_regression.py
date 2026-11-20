# -*- coding: utf-8 -*-
"""Focused regression for v115 old hunting-zone extension (no game service)."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from systems.v115.legacy_expareas import AREAS, WIDTH, HEIGHT, room_id, expand

class LegacyExpansionTest(unittest.TestCase):
    def setUp(self):
        self.rooms = {}
        self.templates = {}
        self.spawns = []
        for _, zone, anchor, enemies, _ in AREAS:
            self.rooms[anchor] = {'zone':zone, 'name':'stare wejście', 'exits':{'north':'stary_pokoj'}}
            for mob in enemies: self.templates[mob] = {'name':mob}
        self.old = deepcopy(self.rooms)

    def test_counts_and_idempotence(self):
        with patch('systems.v115.legacy_expareas.catalog_assign', side_effect=lambda v,_,d,path: d.__setitem__(path[0],v)), patch('systems.v115.legacy_expareas.catalog_set_path', side_effect=lambda _,d,path,v:d[path[0]]['exits'].__setitem__(path[-1],v)):
            a=expand(self.rooms,self.templates,self.spawns)
            self.assertEqual(a, {'new_rooms':len(AREAS)*WIDTH*HEIGHT,'new_spawns':len(AREAS)*WIDTH*HEIGHT//2,'areas':len(AREAS)})
            self.assertEqual(expand(self.rooms,self.templates,self.spawns), {'new_rooms':0,'new_spawns':0,'areas':5})
        for entry, old in self.old.items():
            self.assertEqual(self.rooms[entry]['exits']['north'],old['exits']['north'])

    def test_connectivity_and_ep(self):
        with patch('systems.v115.legacy_expareas.catalog_assign', side_effect=lambda v,_,d,path:d.__setitem__(path[0],v)), patch('systems.v115.legacy_expareas.catalog_set_path', side_effect=lambda _,d,path,v:d[path[0]]['exits'].__setitem__(path[-1],v)):
            expand(self.rooms,self.templates,self.spawns)
        for key,_,anchor,_,_ in AREAS:
            seen={anchor}; todo=[anchor]
            while todo:
                here=todo.pop()
                for dest in self.rooms[here]['exits'].values():
                    if dest in self.rooms and dest not in seen:
                        seen.add(dest);todo.append(dest)
            self.assertEqual(sum(room_id(key,x,y) in seen for x in range(WIDTH) for y in range(HEIGHT)),WIDTH*HEIGHT)
            self.assertEqual(sum(self.rooms[room_id(key,x,y)]['exploration_ep']>=5 for x in range(WIDTH) for y in range(HEIGHT)),WIDTH*HEIGHT//2)

    def test_no_overwrite_when_full(self):
        for _,_,anchor,_,_ in AREAS:
            self.rooms[anchor]['exits']={k:'occupied' for k in ('west','east','north','south','up','down')}
        with patch('systems.v115.legacy_expareas.catalog_assign', side_effect=lambda v,_,d,path:d.__setitem__(path[0],v)):
            with self.assertRaisesRegex(ValueError,'Brak wolnego wyjścia'):
                expand(self.rooms,self.templates,self.spawns)

if __name__=='__main__':unittest.main()
