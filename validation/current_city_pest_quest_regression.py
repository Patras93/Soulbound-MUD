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

def run_quest_receiver_regression():
    """Real turn-in handlers: no item removal or payout before locality."""
    import asyncio
    from types import SimpleNamespace
    from data.npcs import NPCS
    from player.session_mixins.quest_turnin import SessionQuestTurninMixin
    herb = 'herbalist_30_herbs'
    seifer = 'v0560_hourly_npc_uoss_helper_seifer'
    delivery = '__test_delivery_receiver'
    teacher = '__test_required_teacher'
    board = '__test_virtual_board'
    unbound = '__test_unknown_receiver'
    fake_quests = {
        seifer: dict(QUESTS[herb], name='Godzinne zlecenie: Zaopatrzenie dla Seifer', giver='Seifer', needed=5, v0560_source_npc='uoss_helper_seifer'),
        delivery: dict(QUESTS[herb], name='Dostawa', giver='Seifer', kind='deliver_npc', target_npc='__receiver'),
        teacher: dict(QUESTS[herb], name='Próba nauczyciela', giver='Seifer', required_npc_id='__receiver', remote_turnin=True),
        board: dict(QUESTS[herb], name='Zlecenie wirtualne', giver='Tablica Godzinnych Zleceń', remote_turnin=True),
        unbound: dict(QUESTS[herb], name='Brak odbiorcy', giver='Nieistniejący NPC', remote_turnin=True),
    }
    fake_npcs = {
        'uoss_helper_seifer': {'name':'Seifer', 'room':'__seifer_room', 'quest':seifer},
        '__same_name': {'name':'Seifer', 'room':'__wrong_room'},
        '__receiver': {'name':'Odbiorca', 'room':'__receiver_room'},
    }
    checks = 0
    def check(ok, label):
        nonlocal checks
        assert ok, label
        checks += 1
    class DB:
        def __init__(self, qid):
            self.row = {'quest_id':qid, 'status':'active', 'progress':QUESTS[qid]['needed']}
            self.stock = QUESTS[qid]['needed']
        def quest(self, aid, qid): return self.row if qid == self.row['quest_id'] else None
        def quest_rows(self, aid): return [self.row]
        def total_items_across_storage_and_inventory(self, *args): return self.stock
    class Actor(SessionQuestTurninMixin):
        def __init__(self,qid,room):
            self.character = SimpleNamespace(room_id=room, class_name='Mag')
            self.account_id = 1
            self.combat_mob_key = None
            self.server = SimpleNamespace(db=DB(qid))
            self.quest_list_context = {'source':'active','quest_ids':[qid]}
            self.messages = []
            self.payouts = []
        def normalize_description_query(self, value):
            return value.strip().lower().translate(str.maketrans('ąćęłńóśźż','acelnoszz'))
        def quest_progress_for_turnin(self,qid): return QUESTS[qid]['needed'],True
        def quest_collect_category_info(self,target): return ('herb',), 'herb_storage', 'ziół'
        def consume_quest_items_batch_v10800(self,requirements):
            self.server.db.stock -= sum(r[1] for r in requirements)
            return True
        async def complete_quest(self,qid):
            self.payouts.append(qid)
            self.server.db.row['status']='completed'
        async def send(self,msg): self.messages.append(msg)
    async def exercise():
        for qid, wrong, right in ((herb,'__wrong_room',NPCS['herbalist_liora']['room']),
                                  (seifer,'__wrong_room','__seifer_room')):
            for route in ('number','name','plain','direct'):
                actor = Actor(qid,wrong)
                if route=='number':
                    resolved,error=actor.quest_id_for_turnin_number('1')
                    check(resolved==qid and error is None,'numeric context')
                    await actor.turn_in_quest_id(resolved)
                elif route=='name': await actor.turn_in_quest(QUESTS[qid]['name'])
                elif route=='plain': await actor.turn_in_quest('')
                else: await actor.handle_quest_interaction(qid)
                check(actor.server.db.stock==QUESTS[qid]['needed'] and not actor.payouts and actor.server.db.row['status']=='active', 'wrong location retains all state')
                check(bool(actor.messages),'wrong location explains refusal')
            for route in ('number','name','plain','direct'):
                actor=Actor(qid,right)
                if route=='number': await actor.turn_in_quest_id(qid)
                elif route=='name': await actor.turn_in_quest(QUESTS[qid]['name'])
                elif route=='plain': await actor.turn_in_quest('')
                else: await actor.handle_quest_interaction(qid)
                check(actor.server.db.stock==0 and actor.payouts==[qid] and actor.server.db.row['status']=='completed', 'right NPC consumes once and pays once')
        actor=Actor(seifer,'__wrong_room')
        with patch.dict(QUESTS[seifer],{'remote_turnin':True}):
            await actor.turn_in_quest_id(seifer)
            check(not actor.payouts and actor.server.db.stock==5,'generated NPC cannot be remote even if flag is set')
        # Exercise the source-ID rule even if localized giver name or offer changes.
        with patch.dict(QUESTS[seifer],{'giver':'Inny NPC'}), patch.dict(NPCS['uoss_helper_seifer'],{'quest':None}):
            check(not actor.quest_turnin_location(seifer)[0],'generated ID wins over stale name')
            actor.character.room_id='__seifer_room'
            check(actor.quest_turnin_location(seifer)[0],'generated source remains valid')
        for qid in (delivery,teacher):
            actor=Actor(qid,'__seifer_room')
            check(not actor.quest_turnin_location(qid)[0],'explicit receiver blocks original giver')
            actor.character.room_id='__receiver_room'
            check(actor.quest_turnin_location(qid)[0],'explicit receiver accepts')
        actor=Actor(board,'__wrong_room')
        await actor.turn_in_quest_id(board)
        check(actor.payouts==[board],'virtual board remains remote')
        actor=Actor(unbound,'__wrong_room')
        await actor.turn_in_quest_id(unbound)
        check(not actor.payouts and actor.server.db.stock==30,'unknown receiver fails closed')
        actor=Actor(board,'__wrong_room')
        with patch.dict(NPCS,{'__board_owner':{'name':'Seifer','room':'__seifer_room','quest':board}}):
            await actor.turn_in_quest_id(board)
            check(not actor.payouts and actor.server.db.stock==30,'NPC-linked board quest cannot be remotely redeemed')
    with patch.dict(QUESTS,fake_quests), patch.dict(NPCS,fake_npcs):
        asyncio.run(exercise())
    print(f'QUEST RECEIVER / HERBS v11676: {checks}/{checks} PASS',flush=True)
    return checks


if __name__=='__main__':run()
