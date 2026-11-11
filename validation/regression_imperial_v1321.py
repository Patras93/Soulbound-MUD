# -*- coding: utf-8 -*-
"""Isolated transaction/regression tests for the six-era v1.32.1 extension.
Run: python -m unittest validation.regression_imperial_v1321 -v
"""
import sqlite3
import unittest
from systems import imperial_economy_v1320 as old
from systems import imperial_economy_v1321 as new


class Imperial1321Tests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE characters(account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER DEFAULT 0, mithril INTEGER DEFAULT 0);
        CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
        CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
        CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
        CREATE TABLE player_clans(id INTEGER PRIMARY KEY,treasury INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE ocean_ship_v1000(account_id INTEGER PRIMARY KEY,owned INTEGER DEFAULT 0,hull INTEGER DEFAULT 1,sails INTEGER DEFAULT 1,cargo INTEGER DEFAULT 1,navigation INTEGER DEFAULT 1);
        INSERT INTO characters(account_id,silver,gold,mithril) VALUES(1,5000000,0,0),(2,5000000,0,0),(3,5000000,0,0);
        INSERT INTO inventory(account_id,item_id,quantity) VALUES(1,'oak_plank',100),(1,'iron_ingot',60),(1,'test_item',6);
        INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) VALUES(1,'test_item',200,6);
        INSERT INTO player_clans(id,treasury) VALUES(1,10000000);
        INSERT INTO ocean_ship_v1000(account_id,owned,hull,sails,cargo,navigation) VALUES(1,1,4,3,2,5);
        ''')
        new.init(self.conn)
        self.conn.commit()

    def tearDown(self):self.conn.close()
    def coins(self,account):return self.conn.execute('SELECT silver FROM characters WHERE account_id=?',(account,)).fetchone()[0]
    def inv(self,account,item):
        row=self.conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(account,item)).fetchone()
        return row[0] if row else 0

    def test_bids_atomic_and_refund_previous_bid(self):
        n=new.offer_auction(self.conn,1,'test_item',2,1000,6,'inventory')
        self.assertEqual(self.inv(1,'test_item'),4)
        with self.assertRaisesRegex(ValueError,'licytacja'):
            old.purchase(self.conn,2,n,5000000)
        with self.assertRaisesRegex(ValueError,'Licytację'):
            old.cancel(self.conn,1,n)
        bal,_=new.bid(self.conn,2,n,1500)
        self.assertEqual(bal,4998500)
        with self.assertRaises(ValueError):new.bid(self.conn,3,n,1000)
        self.assertEqual(self.coins(3),5000000)
        with self.assertRaisesRegex(ValueError,'Już prowadzisz'):
            new.bid(self.conn,2,n,2000)
        bal,_=new.bid(self.conn,3,n,1600)
        self.assertEqual(bal,4998400)
        refund=self.conn.execute('SELECT coins FROM market_payouts_v1320 WHERE account_id=2').fetchone()[0]
        self.assertEqual(refund,1500)
        with self.assertRaisesRegex(ValueError,'Nie można anulować'):
            new.cancel_auction(self.conn,1,n)
        with self.assertRaisesRegex(ValueError,'zostało'):
            new.settle(self.conn,n)
        state,row=new.settle(self.conn,n,now=2**32)
        self.assertEqual(state,'sold')
        self.assertEqual(self.inv(3,'test_item'),2)
        self.assertEqual(self.inv(1,'test_item'),4)
        self.assertEqual(self.conn.execute('SELECT coins FROM market_payouts_v1320 WHERE account_id=1').fetchone()[0],1600)
        self.assertEqual(self.conn.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=3 AND item_id="test_item"').fetchone()[0],2)
        with self.assertRaises(ValueError):new.settle(self.conn,n,now=2**32)

    def test_expired_no_bids_returns_item_and_basis(self):
        n=new.offer_auction(self.conn,1,'test_item',3,400,1,'inventory')
        state,_=new.settle(self.conn,n,now=2**32)
        self.assertEqual(state,'unsold')
        self.assertEqual(self.inv(1,'test_item'),6)
        self.assertEqual(self.conn.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=1 AND item_id="test_item"').fetchone()[0],6)

    def test_bid_cannot_overdraw_and_remains_open(self):
        n=new.offer_auction(self.conn,1,'test_item',2,1000,1,'inventory')
        with self.assertRaisesRegex(ValueError,'Brakuje'):
            new.bid(self.conn,2,n,6000000)
        self.assertEqual(self.conn.execute('SELECT highest_bid FROM market_auctions_v1321 WHERE listing_id=?',(n,)).fetchone()[0],0)
        self.assertEqual(self.coins(2),5000000)

    def test_cancellation_before_bids_restores_escrow(self):
        n=new.offer_auction(self.conn,1,'test_item',2,2000,6,'inventory')
        new.cancel_auction(self.conn,1,n)
        self.assertEqual(self.inv(1,'test_item'),6)
        self.assertEqual(self.conn.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=1 AND item_id="test_item"').fetchone()[0],6)

    def test_siege_has_three_phases_and_persists(self):
        self.conn.execute("INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(1,'mag',100)")
        self.assertGreater(new.start_siege(self.conn,1,'bazalt'),0)
        with self.assertRaisesRegex(ValueError,'już trwa'):
            new.start_siege(self.conn,1,'bazalt')
        self.conn.execute("INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(2,'wojownik',10)")
        with self.assertRaisesRegex(ValueError,'Inna gildia'):
            new.start_siege(self.conn,2,'bazalt')
        self.assertEqual(self.conn.execute("SELECT phase FROM siege_battles_v1321 WHERE fort='bazalt'").fetchone()[0],1)
        first=new.siege_order(self.conn,1,'bazalt','natarcie')
        self.assertEqual(first['phase'],2)
        self.assertGreater(first['casualties']['mag'],0)
        second=new.siege_order(self.conn,1,'bazalt','ostrzal')
        self.assertEqual(second['phase'],3)
        last=new.siege_order(self.conn,1,'bazalt','magia')
        self.assertEqual(last['outcome'],'victory')
        self.assertEqual(self.conn.execute("SELECT clan_id FROM empire_forts_v1320 WHERE fort='bazalt'").fetchone()[0],1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM siege_battles_v1321").fetchone()[0],0)
        self.assertGreater(self.conn.execute("SELECT ready_at FROM empire_sieges_v1320 WHERE fort='bazalt' AND clan_id=1").fetchone()[0],0)

    def test_siege_retreat_and_cooldown(self):
        self.conn.execute("INSERT INTO empire_armies_v1320(clan_id,troop,quantity) VALUES(1,'wojownik',20)")
        new.start_siege(self.conn,1,'chmury')
        new.retreat(self.conn,1,'chmury')
        with self.assertRaisesRegex(ValueError,'Przegrupowanie'):
            new.start_siege(self.conn,1,'chmury')

    def test_legacy_ship_migrates_and_switch_keeps_modules(self):
        self.conn.execute('INSERT INTO shipyard_fleet_v1320(account_id,ship_class,last_build) VALUES(1,2,0)')
        a=new.fleet_rows(self.conn,1)
        self.assertEqual(len(a),1)
        self.assertEqual(a[0]['ship_class'],2)
        self.assertEqual(a[0]['navigation'],5)
        sources={'oak_plank':'inventory','iron_ingot':'inventory'}
        ship_id,remaining=new.build_ship(self.conn,1,'bryg',sources)
        self.assertEqual(remaining,4840000)
        self.assertEqual(len(new.fleet_rows(self.conn,1)),2)
        self.assertEqual(self.conn.execute('SELECT hull FROM ocean_ship_v1000 WHERE account_id=1').fetchone()[0],1)
        self.conn.execute('UPDATE ocean_ship_v1000 SET hull=5, navigation=3 WHERE account_id=1')
        new.choose_ship(self.conn,1,a[0]['id'])
        legacy=self.conn.execute('SELECT hull,navigation FROM ocean_ship_v1000 WHERE account_id=1').fetchone()
        self.assertEqual((legacy['hull'],legacy['navigation']),(4,5))
        self.assertEqual(self.conn.execute('SELECT ship_class FROM shipyard_fleet_v1320 WHERE account_id=1').fetchone()[0],2)
        new.choose_ship(self.conn,1,ship_id)
        self.assertEqual(self.conn.execute('SELECT hull FROM ocean_ship_v1000 WHERE account_id=1').fetchone()[0],5)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM shipyard_ships_v1321 WHERE account_id=1 AND active=1').fetchone()[0],1)

    def test_fleet_build_failure_rollback(self):
        bal=self.coins(1)
        with self.assertRaises(ValueError):new.build_ship(self.conn,1,'fregata',{})
        self.assertEqual(self.coins(1),bal)
        self.assertEqual(self.inv(1,'oak_plank'),100)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM shipyard_ships_v1321 WHERE account_id=1').fetchone()[0],0)

    def test_ship_names_must_be_safe(self):
        sid=new.fleet_rows(self.conn,1)[0]['id']
        with self.assertRaisesRegex(ValueError,'Nazwa'):
            new.rename_ship(self.conn,1,sid,'<script>')
        new.rename_ship(self.conn,1,sid,'Biala Fregata')
        self.assertEqual(new.fleet_rows(self.conn,1)[0]['name'],'Biala Fregata')

if __name__=='__main__':unittest.main()
