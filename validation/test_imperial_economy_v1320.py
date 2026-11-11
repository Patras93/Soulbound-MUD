# -*- coding: utf-8 -*-
"""Functional v1.32.0 regression: durable escrow, offline seller and armies."""
import sqlite3
from systems import imperial_economy_v1320 as e


def run_tests_v1320():
    c=sqlite3.connect(':memory:')
    c.row_factory=sqlite3.Row
    c.executescript('''
        CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
        CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
        CREATE TABLE characters(account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER);
        CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
        CREATE TABLE player_clans(id INTEGER PRIMARY KEY,treasury INTEGER);
    ''')
    e.init(c);e.init(c)
    c.executemany('INSERT INTO characters VALUES(?,?,?,?)',[(1,500,0,0),(2,3000,0,0)])
    c.execute('INSERT INTO inventory VALUES(1,?,?)',('test_sword',3))
    c.execute('INSERT INTO shop_purchase_lots_v1175 VALUES(1,?,?,?)',('test_sword',300,3))
    c.execute('INSERT INTO profession_storage VALUES(1,?,?,?)',('craftbox','test_gem',4))
    c.commit()
    assert e.select_source(c,1,'test_gem',3)=='craftbox'
    assert 'cobalt_ingot' in e.SHIPS['fregata'][2]
    x=e.list_item(c,1,'test_sword',2,1000,'inventory')
    assert c.execute('SELECT quantity FROM inventory WHERE account_id=1').fetchone()[0]==1
    c.execute('UPDATE characters SET silver=999 WHERE account_id=2');c.commit()
    try:e.purchase(c,2,x,3000)
    except ValueError: caught=True
    else:raise AssertionError('buyer acquired without money')
    c.execute('UPDATE characters SET silver=3000 WHERE account_id=2');c.commit()
    assert c.execute("SELECT state FROM market_listings_v1320 WHERE id=?",(x,)).fetchone()[0]=='active'
    row,new=e.purchase(c,2,x,3000)
    assert row['quantity']==2 and new==2000
    assert c.execute('SELECT quantity FROM inventory WHERE account_id=2').fetchone()[0]==2
    assert c.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=2').fetchone()[0]==2
    try:e.purchase(c,2,x,3000)
    except ValueError: caught=True
    else:raise AssertionError('duplicate purchase')
    amount,new=e.take_payout(c,1,500)
    assert (amount,new)==(1000,1500)
    assert e.take_payout(c,1,1500)==(0,1500)
    y=e.list_item(c,1,'test_gem',3,550,'craftbox')
    e.cancel(c,1,y)
    assert e.select_source(c,1,'test_gem',4)=='craftbox'
    assert c.execute("SELECT state FROM market_listings_v1320 WHERE id=?",(y,)).fetchone()[0]=='cancelled'
    assert e.siege_result(300000,300000) and not e.siege_result(299999,300000)
    c.execute('INSERT INTO empire_armies_v1320 VALUES(1,?,?)',('mag',20));c.commit()
    assert e.troop_strength(c,1)==120000
    assert e.fort_strength(c,'bazalt')==300000
    c.execute('INSERT INTO empire_forts_v1320 VALUES(?,?,?,?)',('bazalt',1,4,0));c.commit()
    assert e.fort_strength(c,'bazalt')==480000
    # Confirm that a failed statement in escrow rolls back the entire transfer.
    try:
        with e.atomic(c):
            e.take(c,1,'test_sword',1,'inventory')
            raise ValueError('interrupt transfer')
    except ValueError: caught=True
    assert c.execute('SELECT quantity FROM inventory WHERE account_id=1').fetchone()[0]==1
    c.close()
    return True

if __name__=='__main__': print('v1.32.0 economic assertions:', 'PASS' if run_tests_v1320() else 'FAIL')
