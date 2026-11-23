# -*- coding: utf-8 -*-
"""v116.64: 38 class schools, teachers, practical training and safe city portal."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.classes_skills import CLASSES,RACES
from core.archetypes.chaos import CLASS_SPECS as CHAOS
from core.archetypes.expansion import CLASS_SPECS as EXPANSION
from systems.current_class_schools_v11664 import (
    WIDTH,HEIGHT,build_class_schools,install_class_schools,school_room,school_teacher)
from player.session_mixins.no_hires_minion_spells_v11664 import SessionNoHiresMinionSpellsV11664Mixin


def all_classes():
    # 22 authored + Magitek + 7 chaos + 8 successors, as installed in server.py.
    return [row[0] for row in CLASSES[:22]]+['Magitek']+[r[0] for r in CHAOS]+[r[0] for r in EXPANSION]


class AcademyTests(unittest.TestCase):
    def setUp(self):
        self.names=all_classes()
        self.rooms,self.teachers,self.spawns=build_class_schools(self.names)

    def test_all_38_classes_have_unique_teacher_and_25_rooms(self):
        self.assertEqual(len(self.names),38)
        self.assertEqual(len(set(self.names)),38)
        self.assertEqual((len(self.rooms),len(self.teachers)),(38*25,38))
        for name in self.names:
            tid=school_teacher(name)
            self.assertEqual(self.teachers[tid]['teacher_class'],name)
            self.assertEqual(self.teachers[tid]['room'],school_room(name))
            self.assertEqual(self.rooms[school_room(name)]['generator_level'],1)

    def test_traversable_halls_and_portal_at_far_boundary(self):
        for name in self.names:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    here=self.rooms[school_room(name,x,y)]
                    for direction,dst in here['exits'].items():
                        self.assertTrue(dst in self.rooms or (x,y)==(4,4) and direction=='up' and dst=='square')
                    self.assertEqual(here['v11664_school_city_portal'],(x,y)==(4,4))
            portal=self.rooms[school_room(name,4,4)]
            self.assertEqual(portal['exits']['up'],'square')
            self.assertNotIn('up',self.rooms[school_room(name)]['exits'])

    def test_real_beginner_combat_in_multiple_halls(self):
        from data.mobs import MOB_TEMPLATES
        allowed={'training_dummy','temple_rat','goblin'}
        self.assertGreaterEqual(len(self.spawns),len(self.names)*8)
        self.assertTrue(all(template in MOB_TEMPLATES and template in allowed for _,template in self.spawns))
        for name in self.names:
            slug=school_teacher(name).split('v11664_school_teacher_')[-1]
            local=[r for r,mid in self.spawns if r.startswith('v11664_class_school_'+slug+'_')]
            self.assertGreaterEqual(len(set(local)),8)
            self.assertTrue(all(self.rooms[r]['generator_level']<=10 for r in local))

    def test_install_checks_collisions_and_does_not_mutate_history(self):
        from data.mobs import MOB_TEMPLATES
        rooms={'square':{'zone':'Miasto Dusz','exits':{}}}
        npcs={'teacher_warrior':{'teacher_class':'Wojownik','room':'guild_martial_hall'}}
        spawns=[]
        result=install_class_schools(rooms,npcs,spawns,MOB_TEMPLATES,[(c,) for c in self.names])
        self.assertEqual(result['schools'],38)
        self.assertEqual(result['teachers'],38)
        self.assertEqual(len(spawns),len(self.spawns))
        self.assertIn('teacher_warrior',npcs)
        self.assertEqual(rooms['square']['exits'],{})
        with self.assertRaises(RuntimeError):
            install_class_schools(rooms,npcs,spawns,MOB_TEMPLATES,[(c,) for c in self.names])

    def test_character_create_new_room_only_when_runtime_flag_enabled(self):
        from storage.database import Database
        for is_live in (False,True):
            with tempfile.TemporaryDirectory(prefix='sb-v11664-schools-') as tmp:
                db=Database(str(Path(tmp)/'test.sqlite'))
                db._class_schools_v11664=is_live
                aid=db.create_account('SchoolHero','test-password-super-long')
                forms={k:'SchoolHero' for k in ('nom','gen','dat','acc','ins','loc','voc')}
                db.create_character(aid,'SchoolHero',RACES[0],CLASSES[0],forms)
                row=db.character_for_account(aid)
                self.assertEqual(row['room_id'],school_room(CLASSES[0][0]) if is_live else 'square')
                db.conn.close()

    def test_portal_warns_once_and_next_same_direction_confirms(self):
        from data.rooms import ROOMS
        class Underlying:
            async def move(self,direction,preserve_auto_mining=False):
                self.moves.append(direction)
        class Tester(SessionNoHiresMinionSpellsV11664Mixin,Underlying):
            def __init__(self):
                self.character=SimpleNamespace(room_id=school_room('Mec',4,4),character_level=1)
                self.moves=[];self.messages=[]
            async def send(self,value):self.messages.append(value)
        actor=Tester()
        with patch.dict(ROOMS,{actor.character.room_id:self.rooms[actor.character.room_id]}):
            asyncio.run(actor.move('up'))
            self.assertEqual(actor.moves,[])
            self.assertIn('poziom 10',actor.messages[-1].lower())
            asyncio.run(actor.move('west'))
            self.assertEqual(actor.moves,['west'])
            asyncio.run(actor.move('up'))
            self.assertEqual(actor.moves,['west'])
            asyncio.run(actor.move('up'))
            self.assertEqual(actor.moves,['west','up'])

    def test_teacher_method_prefers_school_only_when_there(self):
        from data.npcs import NPCS
        class Underlying:
            def class_teacher(self,cls=None):return ('guild_teacher',{'room':'guild_martial_hall'})
        class Tester(SessionNoHiresMinionSpellsV11664Mixin,Underlying):
            def __init__(self,room):self.character=SimpleNamespace(room_id=room,class_name='Mec')
        new=self.teachers[school_teacher('Mec')]
        with patch.dict(NPCS,{school_teacher('Mec'):new}):
            obj=Tester(school_room('Mec'))
            self.assertEqual(obj.class_teacher()[0],school_teacher('Mec'))
            obj.character.room_id='square'
            self.assertEqual(obj.class_teacher()[0],'guild_teacher')


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AcademyTests)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():raise AssertionError('Szkoły klasowe v11664: FAIL')
    return result.testsRun

if __name__=='__main__':
    print('38 CLASS SCHOOLS TEACHERS: %s/7 PASS'%run())
