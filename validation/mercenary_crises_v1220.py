# -*- coding: utf-8 -*-
"""Fast SQLite and progression regression for v1.22.0.

Runs against an in-memory test database; never opens player saves.
"""
import sqlite3
from storage.db_mercenaries import DatabaseMercenariesMixin
from storage.db_world_crises_v1220 import DatabaseWorldCrisesV1220Mixin
from systems.mercenary_growth_v1220 import *
from systems.world_crises_v1220 import *

class FakeDB(DatabaseMercenariesMixin,DatabaseWorldCrisesV1220Mixin):
 def __init__(self):
  self.conn=sqlite3.connect(':memory:');self.conn.row_factory=sqlite3.Row
  self.conn.executescript('CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, coins INTEGER);CREATE TABLE item_counts (character_account_id INTEGER,item_id TEXT,qty INTEGER,PRIMARY KEY(character_account_id,item_id));')
  self.conn.execute('INSERT INTO account_wallet VALUES(1,200000)');self.conn.commit()
  self.create_mercenary_schema();self.create_world_crises_schema_v1220()
 def master_account_for_character(self, ident):return ident
 def shared_wallet_for_master(self, master):return (self.conn.execute('SELECT coins FROM account_wallet WHERE master_account_id=?',(master,)).fetchone()[0],0,0)
 def set_shared_wallet_for_master(self, master,coins,gold,mithril,commit=True):
  self.conn.execute('UPDATE account_wallet SET coins=? WHERE master_account_id=?',(coins,master))
  if commit:self.conn.commit()
 def add_item(self, ident,item,qty,commit=True):
  self.conn.execute('INSERT INTO item_counts VALUES (?,?,?) ON CONFLICT(character_account_id,item_id) DO UPDATE SET qty=qty+excluded.qty',(ident,item,qty))
  if commit:self.conn.commit()


def validate_mercenary_crises_v1220():
    db=FakeDB();tests=0
    def check(what,value):
     nonlocal tests
     assert value,what
     tests+=1
    check('level1',mercenary_level(0)==1)
    check('level10',mercenary_level(mercenary_xp_for_level(10))==10)
    check('level25',mercenary_level(mercenary_xp_for_level(25))==25)
    check('level50',mercenary_level(mercenary_xp_for_level(50))==50)
    check('unbounded', mercenary_level(10**14)>1000)
    check('level xp',mercenary_action_xp(100,200)>mercenary_action_xp(100,40))
    check('attack unbounded',mercenary_attack_multiplier(1000,'szturm') > mercenary_attack_multiplier(100,'szturm'))
    check('no contract',db.mercenary_specialize_v1220(1,'mag','szturm')=='not_hired')
    db.conn.execute('INSERT INTO mercenary_contracts VALUES(1,?,0)',('mag',));db.conn.commit()
    check('tactic level1 freely set',db.mercenary_specialize_v1220(1,'mag','szturm',owner_level=1)=='ok')
    for _ in range(5):db.mercenary_gain_xp_v1220(1,'mag',3000)
    check('old xp retained for compatibility',db.mercenary_progress_v1220(1,'mag')['xp']==15000)
    check('tactic reselect anytime',db.mercenary_specialize_v1220(1,'mag','szturm',owner_level=9)=='ok')
    check('tactic switch support',db.mercenary_specialize_v1220(1,'mag','wsparcie',owner_level=10)=='ok')
    check('tactic switch back',db.mercenary_specialize_v1220(1,'mag','szturm',owner_level=100)=='ok')
    check('legacy progress unaffected',db.mercenary_progress_v1220(1,'mag')['xp']==15000)
    db.dismiss_mercenary(1,'mag')
    check('after dismiss progress',db.mercenary_progress_v1220(1,'mag')['xp']==15000)
    for region in CRISES:
     check('start '+region,db.crisis_start_v1220(1,region,23000))
     check('unique '+region,not db.crisis_start_v1220(1,region,23000))
     check('wrong boss '+region,db.crisis_kill_v1220(1,region,23000,boss=True) is None)
     for i in range(3):
      progress=db.crisis_kill_v1220(1,region,23000)
      check('stage1 kill '+region,progress is not None)
     check('stage2 '+region,progress==(2,0))
     check('early rescue '+region,not db.crisis_rescue_v1220(1,region,23000))
     for i in range(4):
      progress=db.crisis_kill_v1220(1,region,23000)
      check('stage2 kill '+region,progress is not None)
     check('stage2 limit '+region,db.crisis_kill_v1220(1,region,23000) is None)
     check('rescue '+region,db.crisis_rescue_v1220(1,region,23000))
     check('rescue twice '+region,not db.crisis_rescue_v1220(1,region,23000))
     check('boss '+region,db.crisis_kill_v1220(1,region,23000,boss=True)==(4,0))
     check('no repeat boss '+region,db.crisis_kill_v1220(1,region,23000,boss=True) is None)
     check('claim '+region,db.crisis_claim_v1220(1,region,23000,500,'ess_'+region,5))
     check('cannot repeat '+region,not db.crisis_claim_v1220(1,region,23000,500,'ess_'+region,5))
     check('proper claim '+region,db.crisis_status_v1220(1,region,23000)['stage']==5)
     check('fresh next day '+region,db.crisis_start_v1220(1,region,23001))
    check('wallet once',db.shared_wallet_for_master(1)[0]==202000)
    check('items once',db.conn.execute('SELECT SUM(qty) FROM item_counts').fetchone()[0]==20)
    check('other player no progress',db.crisis_status_v1220(2,'aurora',23000) is None)
    return tests


if __name__ == "__main__":
    print(f"V1.22.0 MERCENARY AND CRISES: {validate_mercenary_crises_v1220()} checks PASS")
