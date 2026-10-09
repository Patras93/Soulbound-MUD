# -*- coding: utf-8 -*-
"""SQLite transactional and persistence tests for Soulbound economy v1.36.0."""
import sqlite3
import unittest
import asyncio
from types import SimpleNamespace
from player.session_mixins.economy4_v1360 import SessionEconomy4V1360Mixin
from systems import economy4_v1360 as e
from systems import imperial_economy_v1321 as fleet
from systems import ocean4_v1350 as ocean

class Economy4V1360Tests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:')
        self.c.row_factory=sqlite3.Row
        self.c.executescript('''
        CREATE TABLE characters(account_id INTEGER PRIMARY KEY, silver INTEGER DEFAULT 0,
          gold INTEGER DEFAULT 0, mithril INTEGER DEFAULT 0);
        CREATE TABLE inventory(account_id INTEGER, item_id TEXT, quantity INTEGER,
          PRIMARY KEY(account_id,item_id));
        CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(account_id,container,item_id));
        CREATE TABLE player_clans(id INTEGER PRIMARY KEY, treasury INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE player_clan_bank(clan_id INTEGER,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(clan_id,item_id));
        CREATE TABLE ocean_ship_v1000(account_id INTEGER PRIMARY KEY,owned INTEGER NOT NULL DEFAULT 0,
          hull INTEGER DEFAULT 1,sails INTEGER DEFAULT 1,cargo INTEGER DEFAULT 1,navigation INTEGER DEFAULT 1);
        INSERT INTO characters VALUES(1,10000,0,0);
        INSERT INTO player_clans VALUES(100,5000000);
        INSERT INTO inventory VALUES(1,'iron_ore',10);
        INSERT INTO profession_storage VALUES(1,'bag','iron_ore',20);
        INSERT INTO profession_storage VALUES(1,'woodpile','oak_log',35);
        INSERT INTO inventory VALUES(1,'iron_ingot',20);
        INSERT INTO profession_storage VALUES(1,'craftbox','oak_plank',35);
        INSERT INTO profession_storage VALUES(1,'net','salmon',20);
        INSERT INTO profession_storage VALUES(1,'herbbag','moonflower',12);
        ''')
        fleet.init(self.c)
        ocean.init(self.c)
        e.init(self.c)

    def tearDown(self):self.c.close()

    def q(self,table,item,box=None):
        if box is None:return (self.c.execute('SELECT quantity FROM inventory WHERE account_id=1 AND item_id=?',(item,)).fetchone() or [0])[0]
        return (self.c.execute('SELECT quantity FROM profession_storage WHERE account_id=1 AND item_id=? AND container=?',(item,box)).fetchone() or [0])[0]

    def test_quote_stability_rotation(self):
        self.assertEqual(e.demand('zelazo',now=3600),e.demand('zelazo',now=7200))
        self.assertNotEqual(e.demand('zelazo',now=3600),e.demand('zelazo',now=21600))

    def test_two_storage_escrow_and_persistence(self):
        r=e.start_convoy(self.c,1,'zelazo',now=10000)
        self.assertEqual(self.q('inventory','iron_ore'),0)
        self.assertEqual(self.q('profession_storage','iron_ore','bag'),0)
        self.assertEqual(e.convoy(self.c,1)['arrival'],11800)
        self.assertGreater(r['reward'],0)
        with self.assertRaisesRegex(ValueError,'Masz już'):
            e.start_convoy(self.c,1,'drewno',now=10001)

    def test_early_and_double_collection(self):
        e.start_convoy(self.c,1,'zelazo',now=10000)
        with self.assertRaisesRegex(ValueError,'dotrze'):
            e.collect_convoy(self.c,1,now=11000)
        reward,balance=e.collect_convoy(self.c,1,now=12000)
        self.assertEqual(balance,10000+reward)
        self.assertEqual(e.records(self.c,1)['convoys'],1)
        with self.assertRaisesRegex(ValueError,'Nie masz'):
            e.collect_convoy(self.c,1,now=12000)

    def test_defense_changes_payout_once(self):
        e.start_convoy(self.c,1,'zelazo',now=10000)
        e.defend_convoy(self.c,1,now=10001)
        with self.assertRaises(ValueError):e.defend_convoy(self.c,1,now=10002)
        self.assertEqual(e.collect_convoy(self.c,1,now=12000)[0],e.caravan_quotes(now=10000)[0][4])

    def test_missing_goods_rollback(self):
        self.c.execute("UPDATE profession_storage SET quantity=5 WHERE item_id='moonflower'")
        with self.assertRaisesRegex(ValueError,'Brakuje'):
            e.start_convoy(self.c,1,'ziola',now=10000)
        self.assertEqual(self.q('profession_storage','moonflower','herbbag'),5)
        self.assertIsNone(e.convoy(self.c,1))

    def test_ship_requirement_and_capacity(self):
        with self.assertRaisesRegex(ValueError,'statku'):
            e.start_convoy(self.c,1,'deski',now=10000)
        self.c.execute("INSERT INTO ocean_ship_v1000 VALUES(1,1,1,1,1,1)")
        e.start_convoy(self.c,1,'deski',now=10000)
        self.assertEqual(self.q('profession_storage','oak_plank','craftbox'),23)

    def test_marine_command_initializes_ocean_before_first_use(self):
        self.c.execute("INSERT INTO ocean_ship_v1000 VALUES(1,1,1,1,1,1)")
        self.c.execute('DROP TABLE ocean4_ship_condition_v1350')
        class FakeSession(SessionEconomy4V1360Mixin):
            def __init__(self,conn):
                self.account_id=1
                self.server=SimpleNamespace(db=SimpleNamespace(conn=conn))
                self.character=SimpleNamespace(room_id='port',silver=10000,gold=0,mithril=0)
                self.messages=[]
            def _econ_v1321(self): return self.server.db.conn
            def _naval_v1350(self):
                ocean.init(self.server.db.conn)
                return self.server.db.conn
            def ocean_port_name_v1000(self,room):return 'port'
            async def send(self,msg):self.messages.append(msg)
        sess=FakeSession(self.c)
        asyncio.run(sess.economy4_command_v1360('wyslij deski potwierdz'))
        self.assertTrue(any('Wysłano' in msg for msg in sess.messages),sess.messages)
        self.assertEqual(e.convoy(self.c,1)['code'],'deski')

    def test_active_naval_battle_prevents_transport(self):
        self.c.execute("INSERT INTO ocean_ship_v1000 VALUES(1,1,1,1,1,1)")
        self.c.execute("INSERT INTO ocean4_battles_v1350(account_id,enemy,enemy_hp,enemy_max_hp,started_at) VALUES(1,'kraken',3000,3000,1)")
        with self.assertRaisesRegex(ValueError,'bitwy'):
            e.start_convoy(self.c,1,'deski',now=10000)
        self.assertEqual(self.q('profession_storage','oak_plank','craftbox'),35)

    def test_cooldown_survives_finished_trip(self):
        e.start_convoy(self.c,1,'zelazo',now=10000)
        e.collect_convoy(self.c,1,now=12000)
        with self.assertRaisesRegex(ValueError,'transport za'):
            e.start_convoy(self.c,1,'drewno',now=12001)

    def test_order_consumption_and_cooldown(self):
        _,price,balance=e.finish_order(self.c,1,'uzbrojenie',now=10000)
        self.assertGreater(price,0)
        self.assertEqual(balance,10000+price)
        self.assertEqual(self.q('inventory','iron_ingot'),5)
        self.assertEqual(self.q('profession_storage','oak_plank','craftbox'),27)
        with self.assertRaises(ValueError):e.finish_order(self.c,1,'okrety',now=15000)

    def test_order_rolls_back_every_ingredient(self):
        self.c.execute("DELETE FROM profession_storage WHERE item_id='moonflower'")
        before=self.q('profession_storage','salmon','net')
        with self.assertRaises(ValueError):e.finish_order(self.c,1,'uczta',now=10000)
        self.assertEqual(self.q('profession_storage','salmon','net'),before)
        self.assertEqual(e._coins(self.c,1),10000)

    def test_building_cost_and_no_double_collection(self):
        level,cost=e.upgrade_building(self.c,100,'kopalnia',now=10000)
        self.assertEqual((level,cost),(1,22000))
        self.assertEqual(e.collect_production(self.c,100,now=10000),[])
        out=e.collect_production(self.c,100,now=10000+21600)
        self.assertEqual(out[0][2],12)
        self.assertEqual(out[0][3],800)
        self.assertEqual(e.collect_production(self.c,100,now=10000+21600),[])
        self.assertEqual(self.c.execute('SELECT quantity FROM player_clan_bank WHERE clan_id=100 AND item_id="iron_ore"').fetchone()[0],12)
        self.assertEqual(self.c.execute('SELECT treasury FROM player_clans WHERE id=100').fetchone()[0],5000000-22000-800)

    def test_bounded_offline_and_upgrade_no_retroactive_gain(self):
        e.upgrade_building(self.c,100,'tartak',now=10000)
        with self.assertRaisesRegex(ValueError,'Najpierw odbierz'):
            e.upgrade_building(self.c,100,'tartak',now=10000+21600)
        result=e.collect_production(self.c,100,now=10000+10*21600)
        self.assertEqual(result[0][2],40)
        self.assertEqual(e.upgrade_building(self.c,100,'tartak',now=10000+10*21600)[0],2)

if __name__=='__main__':unittest.main(verbosity=1)
