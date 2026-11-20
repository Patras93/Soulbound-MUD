# -*- coding: utf-8 -*-
"""v116: preserve old 8x8 IDs while expanding six legacy areas to 12x12."""
import unittest
from collections import deque
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from systems.v115.legacy_expareas import AREAS, WIDTH, HEIGHT, room_id
from systems.v115.graveyard_expansion import (
    WIDTH as G_WIDTH, HEIGHT as G_HEIGHT, room_id as grave_room_id,
)

class LegacyBorderRegions(unittest.TestCase):
    def test_larger_regions_keep_original_rooms_and_spawns(self):
        self.assertEqual((WIDTH, HEIGHT), (12, 12))
        self.assertEqual((G_WIDTH, G_HEIGHT), (12, 12))
        for key, zone, anchor, enemies, level in AREAS:
            all_rooms = {room_id(key,x,y) for x in range(WIDTH) for y in range(HEIGHT)}
            self.assertEqual(len(all_rooms),144)
            self.assertTrue(all(r in ROOMS for r in all_rooms),zone)
            self.assertTrue(all(ROOMS[r]['v115_legacy_expansion']==key for r in all_rooms),zone)
            # The previous 8x8 positions, including player last-room IDs, remain.
            original = {room_id(key,x,y) for x in range(8) for y in range(8)}
            self.assertEqual(len(original),64)
            spawns={(r,m) for r,m in MOB_SPAWNS if r in all_rooms}
            self.assertGreaterEqual(len(spawns),72)  # runtime may add scaled clones
            self.assertEqual(sum(mid in enemies for _,mid in spawns),72)
            for y in range(8):
                for x in range(8):
                    r=room_id(key,x,y)
                    self.assertEqual(ROOMS[r]['generator_level'],level)
                    if (x+y)%2==0:
                        self.assertIn((r,enemies[(x+2*y)%len(enemies)]),spawns)
            for _,mid in spawns: self.assertIn(mid,MOB_TEMPLATES)

    def test_all_routes_return_and_cross_only_at_start(self):
        zones=[(key, anchor, lambda x,y,key=key:room_id(key,x,y),WIDTH,HEIGHT)
               for key,_,anchor,_,_ in AREAS]
        zones.append(('graveyard','graveyard',grave_room_id,G_WIDTH,G_HEIGHT))
        for key,anchor,loc,width,height in zones:
            inside={loc(x,y) for y in range(height) for x in range(width)}
            self.assertEqual(len(inside),144,key)
            entry=loc(0,0)
            self.assertIn(entry,ROOMS[anchor]['exits'].values(),key)
            # Every interior link must have the matching return link.
            opposites={'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up'}
            for y in range(height):
                for x in range(width):
                    rid=loc(x,y);exits=ROOMS[rid]['exits']
                    self.assertNotIn('trap',ROOMS[rid],key)
                    self.assertNotIn('min_level',ROOMS[rid],key)
                    for direction,dest in exits.items():
                        if dest in inside:
                            self.assertEqual(ROOMS[dest]['exits'][opposites[direction]],rid,(key,rid))
                        else:
                            # Nowe wejścia są na przeciwległych krańcach Starego Cmentarza.
                            # Nie osłabiamy reguły oryginalnych przejść 6 innych obszarów.
                            if key == 'graveyard' and (x,y) in ((11,0),(11,11)):
                                expected = ('necropolis_gate' if (x,y)==(11,0)
                                            else 'crypt_entrance')
                                self.assertEqual(dest,expected,(key,rid))
                                self.assertEqual(ROOMS[dest]['exits'][opposites[direction]],rid,(key,rid))
                            else:
                                self.assertEqual((x,y),(0,0),(key,rid,dest))
                                self.assertEqual(dest,anchor,(key,rid))
                                self.assertEqual(ROOMS[anchor]['exits'][opposites[direction]],rid,(key,rid))
            reachable={entry}; todo=deque([entry])
            while todo:
                for dst in ROOMS[todo.popleft()]['exits'].values():
                    if dst in inside and dst not in reachable:
                        reachable.add(dst);todo.append(dst)
            self.assertEqual(reachable,inside,key)
            # Bidirectional links mean every new sector can also go home.
            self.assertTrue(any(anchor in ROOMS[r]['exits'].values() for r in inside),key)

    def test_graveyard_old_ids_and_old_spawns(self):
        inside={grave_room_id(x,y) for y in range(G_HEIGHT) for x in range(G_WIDTH)}
        spawns={(r,m) for r,m in MOB_SPAWNS if r in inside}
        self.assertEqual(len(spawns),72)
        for y in range(8):
            for x in range(8):
                room=grave_room_id(x,y)
                self.assertIn(room,ROOMS)
                self.assertEqual(ROOMS[room]['v115_legacy_expansion'],'graveyard')
                if (x+y)%2==0: self.assertIn((room,'skeleton'),spawns)

if __name__=='__main__': unittest.main()
