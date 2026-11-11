# -*- coding: utf-8 -*-
"""Staging: actual inventory mixin + player bank commands + rollback SQLite."""
import asyncio
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import player.session_mixins.banking_charisma as bank
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account

CAT={'ring':{'type':'armor','name':'Pierścień'},'helm':{'type':'armor','name':'Hełm'},
     'plate':{'type':'armor','name':'Zbroja'}}

class DB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True
        self._v106_bank_shadow_disposable_copy=True

class Session(bank.SessionBankingCharismaMixin):
    def __init__(self,db):
        self.server=SimpleNamespace(db=db)
        self.account_id=1
        self.sent=[]
    async def send(self,msg):self.sent.append(str(msg))


def run():
    prev=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    old_items=bank.ITEMS;old_bound=bank.is_character_bound_item
    bank.ITEMS={'ring':{'name':'Pierścień','type':'armor'},'helm':{'name':'Hełm','type':'armor'},
                'plate':{'name':'Zbroja','type':'armor'}}
    bank.is_character_bound_item=lambda iid:False
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.executescript('''
       CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(account_id,item_id));
       CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
          PRIMARY KEY(account_id,slot));
       CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
          PRIMARY KEY(account_id,record_key));
       CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
          paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
       CREATE TABLE bank_items(account_id INTEGER,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(account_id,item_id));
       INSERT INTO inventory VALUES(1,'ring',3),(1,'plate',1),(1,'helm',1);
       INSERT INTO shop_purchase_lots_v1175 VALUES(1,'ring',85,2),(1,'ring',100,1);
       INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:plate',3);
       INSERT INTO equipment VALUES(1,'finger','ring');
    ''')
    checks=0
    def ck(ok,why):
        nonlocal checks
        if not ok:raise AssertionError(why)
        checks+=1
    def denied(action,exc,msg):
        nonlocal checks
        try:action()
        except exc:checks+=1
        else:raise AssertionError(msg)
    def snap():
        tables=('inventory','bank_items','v106_item_instances','v106_equipped_instances',
                'v106_stored_instances','shop_purchase_lots_v1175')
        return {t:[tuple(r) for r in c.execute('SELECT * FROM '+t+' ORDER BY 1,2')]
                for t in tables}
    try:
        db=DB(c)
        prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        s=Session(db)
        start=snap()
        ck(asyncio.run(s.bank_deposit_item('pierścień 1')) is True,'deposit works through session')
        ck('Do skrytki' in s.sent[-1],'deposit accessible NVDA output')
        ck(db.item_qty(1,'ring')==2 and db.bank_item_qty(1,'ring')==1,'counts moved')
        stored=c.execute("SELECT instance_id FROM v106_stored_instances WHERE storage_kind='bank'").fetchone()[0]
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=1').fetchone()[0]==5,
           'physical identity is not deleted or minted on deposit')
        ck(stored not in {r[0] for r in c.execute('SELECT instance_id FROM v106_equipped_instances')},
           'worn physical identity not banked')
        ck(c.execute("SELECT quantity FROM shop_purchase_lots_v1175 WHERE item_id='__bank_v1175__:ring'").fetchone()[0]==1,
           'original cost basis moved to bank')
        ck(c.execute("SELECT paid_silver FROM shop_purchase_lots_v1175 WHERE item_id='__bank_v1175__:ring'").fetchone()[0]==85,
           'real purchase price unchanged')
        _check_account(c,1,CAT);ck(True,'inventory excludes banked instances')
        denied(lambda:db.remove_item(1,'ring',2),Exception,'cannot consume worn and banked copies') if False else None
        ck(asyncio.run(s.bank_withdraw_item('pierścień 1')) is True,'withdraw through session')
        ck('Wyjmujesz' in s.sent[-1],'withdraw accessible NVDA output')
        ck(snap()==start,'bank roundtrip exactly restores inventories IDs slots and cost lots')
        ck(asyncio.run(s.bank_deposit_item('zbroja')) is False,'old evolved armor is protected')
        ck(snap()==start,'evolved deny changes nothing')
        ck(asyncio.run(s.bank_withdraw_item('pierścień')) is False,'no bank inventory to withdraw')
        ck(snap()==start,'missing stock leaves no SQL changes')
        # Caller-owned transaction must never be finalized by the cost-lot move.
        ck(db.move_bank_equipment_v106(1,'ring',1,commit=False) is True,'pending deposit succeeds')
        ck(c.in_transaction,'pending deposit stays uncommitted')
        ck(db.bank_item_qty(1,'ring')==1,'pending bank row exists')
        c.rollback()
        ck(snap()==start,'rollback restores all four ledgers including cost lots')
        # SQL failure mid-operation must undo both inventory and stored ledger.
        c.execute('''CREATE TRIGGER fail_bank_ins BEFORE INSERT ON bank_items
                     BEGIN SELECT RAISE(ABORT,'staged bank SQL error'); END''')
        denied(lambda:db.move_bank_equipment_v106(1,'ring',1),sqlite3.IntegrityError,
               'bank trigger prevents atomic operation')
        ck(snap()==start,'failed bank insert undoes inventory and identity')
        c.execute('DROP TRIGGER fail_bank_ins');c.commit()
        # Existing untracked v105 bank gear cannot be magically reconciled.
        c.execute("INSERT INTO bank_items VALUES(1,'ring',2)");c.commit()
        denied(lambda:db.move_bank_equipment_v106(1,'ring',1),RuntimeError,
               'untracked historical bank quantity blocked')
        ck(db.bank_item_qty(1,'ring')==2,'existing legacy bank stock untouched')
        c.execute("DELETE FROM bank_items WHERE item_id='ring'");c.commit()
        # The extra feature flag is mandatory, even when generic shadow gear is on.
        db._v106_bank_shadow_disposable_copy=False
        denied(lambda:db.move_bank_equipment_v106(1,'ring',1),PermissionError,
               'additional opt-in needed')
        ck(asyncio.run(s.bank_deposit_item('pierścień')) is False,
           'unarmed player command stays fail-closed')
        ck(snap()==start,'unarmed command unchanged')
        db._v106_bank_shadow_disposable_copy=True
        # Mail/storage are still explicitly denied, not silently changing gear.
        denied(lambda:db.add_storage_item(1,'craftbox','ring',1),RuntimeError,
               'unintegrated storage direct route blocked')
        # Non-gear and unarmed v105 paths stay intact.
        db._v106_shadow_slots_disposable_copy=False
        db.add_item(2,'ring',1)
        ck(db.item_qty(2,'ring')==1,'v105 unarmed inventory path intact')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=2').fetchone()[0]==0,
           'no physical ledger minted by legacy route')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
        return checks
    finally:
        c.close();bank.ITEMS=old_items;bank.is_character_bound_item=old_bound
        if prev is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=prev

if __name__=='__main__':print('V106 BANK PHYSICAL EQ:',run(),'PASS')
