# -*- coding: utf-8 -*-
"""v116.00.49: city pest quest kills, runtime clones, one credit per kill."""
from __future__ import annotations
import sqlite3
import unittest
from unittest.mock import patch

from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from data.quests import QUESTS
from storage.db_quests import DatabaseQuestMixin
from storage.database import _DeferredCommitConnection
from systems.atomic_kill_quest_progress_v10400 import settle_all_kill_quests_v10400
from world.dynamic_content import quest_kill_targets_v0389


class CityPestKillCredit(unittest.TestCase):
    def setUp(self):
        self.city = 'v0900_city_miasto_dusz'
        self.other = 'v0900_city_brzozowy_trakt'
        self.pest = self.city + '_threat'
        self.stray = self.other + '_threat'
        self.terrain = self.pest + '__terrain_v0362_070'
        self.world = self.terrain + '__world_v0384_070'
        self.elite = self.world + '__elite_v11338_armored'
        self.room = self.city + '_undercity'
        self.other_room = self.other + '_undercity'
        self.q2 = self.city + '_2'
        self.q3 = self.city + '_3'
        self.mobs = {
            self.pest: {'name': 'Podziemny Szkodnik', 'quest_target': self.pest, 'v0900_city2': True},
            self.stray: {'name': 'Podziemny Szkodnik Mirlor', 'quest_target': self.stray, 'v0900_city2': True},
            self.terrain: {'name': 'Podziemny Szkodnik', 'base_template': self.pest},
            self.world: {'name': 'Podziemny Szkodnik', 'base_template': self.terrain},
            self.elite: {'name': 'Opancerzony Podziemny Szkodnik', 'elite_base_template': self.world},
        }
        self.patches = (
            patch.dict(MOB_TEMPLATES, self.mobs),
            patch.dict(ROOMS, {self.room: {'v0900_city2': True}, self.other_room: {'v0900_city2': True}}),
            patch.dict(QUESTS, {
                self.q2: {'kind':'kill','name':'Zagrożenie pod fundamentami', 'needed':8,'target':self.pest},
                self.q3: {'kind':'kill','name':'Bezpieczne ulice','needed':16,'target':self.pest},
            }),
        )
        for p in self.patches:p.start()
        self.db = DatabaseQuestMixin()
        self.db.conn = _DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.db.conn.row_factory = sqlite3.Row
        self.db.conn.executescript('''
            CREATE TABLE quests(account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER,
                completed_at INTEGER DEFAULT 0, completion_count INTEGER DEFAULT 0,
                PRIMARY KEY(account_id,quest_id));
            CREATE TABLE quest_resource_progress_v0929(account_id INTEGER,quest_id TEXT,
                target_id TEXT,progress INTEGER, PRIMARY KEY(account_id,quest_id,target_id));
        ''')
        for qid in (self.q2,self.q3):
            self.db.conn.execute('INSERT INTO quests(account_id,quest_id,status,progress) VALUES(1,?,\'active\',0)',(qid,))
        self.db.conn.execute('INSERT INTO quests(account_id,quest_id,status,progress) VALUES(2,?,\'active\',0)',(self.q2,))
        self.db.conn.commit()

    def tearDown(self):
        self.db.conn.close()
        for p in reversed(self.patches):p.stop()

    def kill(self, template_id, room_id=None):
        aliases = quest_kill_targets_v0389(template_id, MOB_TEMPLATES[template_id], room_id=room_id)
        basic, multi, saga, party = settle_all_kill_quests_v10400(
            self.db,1,template_id,aliases=aliases,active_classes=(),party_categories=(),mob_level=70)
        self.assertFalse(multi or saga or party)
        return basic

    def progress(self, quest_id, account=1):
        row=self.db.conn.execute('SELECT progress FROM quests WHERE account_id=? AND quest_id=?',(account,quest_id)).fetchone()
        return int(row['progress'])

    def test_ordinary_city_pest_counts_once_for_each_active_stage(self):
        self.assertEqual(set(self.kill(self.pest,self.room)), {(self.q2,1),(self.q3,1)})
        self.assertEqual(self.progress(self.q2),1)
        self.assertEqual(self.progress(self.q3),1)
        self.assertEqual(self.progress(self.q2,2),0)

    def test_nested_terrain_world_elite_without_quest_tag_counts_city(self):
        self.assertIn(self.pest, quest_kill_targets_v0389(self.elite, self.mobs[self.elite]))
        self.assertEqual(set(self.kill(self.elite,self.room)), {(self.q2,1),(self.q3,1)})

    def test_pest_in_local_city_counts_its_local_hunt_not_foreign_quest(self):
        self.assertEqual(set(self.kill(self.stray,self.room)), {(self.q2,1),(self.q3,1)})
        self.assertIn(self.pest, quest_kill_targets_v0389(self.stray,self.mobs[self.stray],room_id=self.room))

    def test_pest_outside_city_cannot_credit_wrong_city_hunt(self):
        self.assertEqual(self.kill(self.stray,self.other_room),[])
        self.assertEqual(self.progress(self.q2),0)
        self.assertEqual(self.kill(self.stray,'temple_basement'),[])

    def test_correct_city_stages_cap_independently_without_double_count(self):
        for _ in range(20):self.kill(self.pest,self.room)
        self.assertEqual(self.progress(self.q2),8)
        self.assertEqual(self.progress(self.q3),16)
        self.assertEqual(self.progress(self.q2,2),0)
        self.assertEqual(self.kill(self.pest,self.room),[])

    def test_not_active_quest_does_not_advance(self):
        self.db.conn.execute('UPDATE quests SET status=\'completed\' WHERE account_id=1 AND quest_id=?',(self.q2,))
        self.assertEqual(self.kill(self.pest,self.room),[(self.q3,1)])
        self.assertEqual(self.progress(self.q2),0)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CityPestKillCredit)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise AssertionError('CITY PEST KILL QUEST regression')
    print(f'CITY PEST KILL QUEST v116.00.49: {result.testsRun}/6 PASS',flush=True)
    return result.testsRun

if __name__=='__main__':run()
