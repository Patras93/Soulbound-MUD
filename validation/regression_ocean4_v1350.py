# -*- coding: utf-8 -*-
"""Durable real SQLite Ocean 4.0 tests, executed by Railway predeploy."""
import os
import sqlite3
import tempfile
import unittest

from systems import ocean4_v1350 as navy
from systems import imperial_economy_v1321 as fleet


class Ocean4V1350Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='sb-ocean4-')
        self.path=os.path.join(self.tmp.name,'navy.db')
        self.conn=self._connect()
        self.conn.executescript('''
          CREATE TABLE characters(account_id INTEGER PRIMARY KEY,silver INTEGER NOT NULL,gold INTEGER NOT NULL,mithril INTEGER NOT NULL);
          INSERT INTO characters VALUES(1,2000000,0,0);
          CREATE TABLE ocean_ship_v1000(account_id INTEGER PRIMARY KEY,owned INTEGER,hull INTEGER,sails INTEGER,cargo INTEGER,navigation INTEGER);
          INSERT INTO ocean_ship_v1000 VALUES(1,1,5,4,4,4);
          CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
        ''')
        fleet.init(self.conn)
        navy.init(self.conn)
        self.conn.execute("INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,hull,sails,cargo,navigation,active,built_at) VALUES(1,3,'Sztandar',5,4,4,4,1,100)")
        self.conn.execute("INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,hull,sails,cargo,navigation,active,built_at) VALUES(1,2,'Eskorta 1',4,3,3,4,0,100)")
        self.conn.execute("INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,hull,sails,cargo,navigation,active,built_at) VALUES(1,2,'Eskorta 2',4,3,3,4,0,100)")
        self.conn.execute("INSERT INTO shipyard_ships_v1321(account_id,ship_class,name,hull,sails,cargo,navigation,active,built_at) VALUES(1,1,'Nadmiar',2,2,2,2,0,100)")
        self.conn.commit()
    def _connect(self):
        c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row
        return c
    def tearDown(self):
        self.conn.close();self.tmp.cleanup()
    def test_escort_capacity_ownership_and_flagship(self):
        navy.escort(self.conn,1,2);navy.escort(self.conn,1,3)
        self.assertEqual(len([r for r in navy.fleet_status(self.conn,1) if r['escort']]),2)
        for bad in (1,4,999):
            with self.assertRaises(ValueError):navy.escort(self.conn,1,bad)
        navy.escort(self.conn,1,2,enable=False)
        self.assertEqual(len([r for r in navy.fleet_status(self.conn,1) if r['escort']]),1)
    def test_persisted_fight_and_no_double_reward(self):
        navy.escort(self.conn,1,2)
        navy.escort(self.conn,1,3)
        navy.begin(self.conn,1,'korsarze',now=5000)
        with self.assertRaises(ValueError):navy.begin(self.conn,1,'smok',now=5001)
        with self.assertRaises(ValueError):navy.escort(self.conn,1,4)
        with self.assertRaises(ValueError):navy.action(self.conn,1,'abordaz',now=5001)
        navy.action(self.conn,1,'salwa',now=5002)
        turn=navy.battle_state(self.conn,1)['turn'];self.assertEqual(turn,1)
        self.conn.close();self.conn=self._connect()
        self.assertEqual(navy.battle_state(self.conn,1)['turn'],1)
        result=None
        for i in range(2,30):
            result=navy.action(self.conn,1,'salwa',now=5000+i)
            if result['outcome']!='trwa':break
        self.assertEqual(result['outcome'],'zwyciestwo')
        self.assertEqual(result['reward'],navy.ENEMIES['korsarze'][3])
        self.assertEqual(self.conn.execute("SELECT quantity FROM inventory WHERE item_id='iron_ingot'").fetchone()[0],1)
        with self.assertRaises(ValueError):navy.action(self.conn,1,'salwa',now=6000)
        self.assertEqual(navy.records(self.conn,1),[('korsarze',1)])
        with self.assertRaises(ValueError):navy.begin(self.conn,1,'kraken',now=5000+navy.COOLDOWN-1)
        navy.begin(self.conn,1,'kraken',now=15000)
        with self.assertRaises(ValueError):navy.action(self.conn,1,'abordaz',now=15001)
    def test_repair_cost_is_atomic_and_legacy_modules_unchanged(self):
        before=self.conn.execute('SELECT * FROM ocean_ship_v1000').fetchone()
        navy._set_hp(self.conn,1,1,100)
        self.conn.commit()
        cost,remaining=navy.repair(self.conn,1,1)
        self.assertGreater(cost,0)
        self.assertEqual(remaining,2000000-cost)
        self.assertEqual(navy.fleet_status(self.conn,1)[0]['hp'],navy.fleet_status(self.conn,1)[0]['max_hp'])
        after=self.conn.execute('SELECT * FROM ocean_ship_v1000').fetchone()
        self.assertEqual(tuple(before),tuple(after))
        self.conn.execute('UPDATE characters SET silver=0')
        navy._set_hp(self.conn,1,1,20)
        self.conn.commit()
        with self.assertRaises(ValueError):navy.repair(self.conn,1,1)
        self.assertEqual(navy.fleet_status(self.conn,1)[0]['hp'],20)
    def test_no_repair_or_escort_during_combat(self):
        navy.begin(self.conn,1,'blokada',now=100)
        with self.assertRaises(ValueError):navy.repair(self.conn,1,1)
        with self.assertRaises(ValueError):navy.escort(self.conn,1,3)
    def test_retreat_cooldown_and_no_reward(self):
        navy.begin(self.conn,1,'korsarze',now=100)
        navy.retreat(self.conn,1,now=110)
        self.assertEqual(navy.battle_state(self.conn,1)['outcome'],'odwrot')
        with self.assertRaises(ValueError):navy.begin(self.conn,1,'korsarze',now=120)
        self.assertEqual(self.conn.execute('SELECT silver FROM characters').fetchone()[0],2000000)
        self.assertEqual(navy.records(self.conn,1),[])
    def test_defeat_does_not_remove_ship(self):
        navy._set_hp(self.conn,1,1,1000);self.conn.commit()
        navy.begin(self.conn,1,'smok',now=100)
        result=navy.action(self.conn,1,'salwa',now=101)
        self.assertEqual(result['outcome'],'porazka')
        self.assertEqual(len(navy.fleet_status(self.conn,1)),4)
        self.assertEqual(self.conn.execute('SELECT silver FROM characters').fetchone()[0],2000000)


if __name__=='__main__':unittest.main()
