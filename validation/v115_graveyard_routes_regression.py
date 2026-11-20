import unittest
from data.rooms import ROOMS
from systems.v115.graveyard_expansion import room_id, WIDTH, HEIGHT
class GraveRoutes(unittest.TestCase):
    def test_independent_up_route(self):
        grave=ROOMS['graveyard']['exits']
        self.assertEqual(grave['up'],room_id(0,0))
        self.assertEqual(ROOMS[room_id(0,0)]['exits']['down'],'graveyard')
        self.assertNotEqual(grave.get('north'),room_id(0,0))
    def test_all_rooms_reachable(self):
        seen={'graveyard'}; stack=['graveyard']
        while stack:
            u=stack.pop()
            for v in ROOMS[u].get('exits',{}).values():
                if v in ROOMS and v not in seen:seen.add(v);stack.append(v)
        self.assertTrue(all(room_id(x,y) in seen for x in range(WIDTH) for y in range(HEIGHT)))
if __name__=='__main__': unittest.main()
