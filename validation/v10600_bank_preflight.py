# -*- coding: utf-8 -*-
"""Verify real bank commands reject v106 gear BEFORE first mutation."""
import asyncio,sqlite3,os,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import player.session_mixins.banking_charisma as bank
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy

class DB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_item_catalog={'ring':{'type':'armor'}}
        self._v106_shadow_slots_disposable_copy=True

class Session(bank.SessionBankingCharismaMixin):
    def __init__(self,db):
        self.server=SimpleNamespace(db=db)
        self.account_id=1
        self.sent=[]
    async def send(self,msg):self.sent.append(str(msg))

def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    orig_items=bank.ITEMS
    orig_bound=bank.is_character_bound_item
    bank.ITEMS={'ring':{'type':'armor','name':'Ring'}}
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
     INSERT INTO inventory VALUES(1,'ring',2);
     INSERT INTO bank_items VALUES(1,'ring',1);
     INSERT INTO shop_purchase_lots_v1175 VALUES(1,'ring',50,2);
    ''')
    n=0
    def ck(ok,msg):
        nonlocal n
        assert ok,msg;n+=1
    try:
        db=DB(c)
        prepare_on_disposable_copy(c,db._v106_shadow_item_catalog,
                                   confirm_disposable_copy=True)
        session=Session(db)
        def snapshot():
            return (list(map(tuple,c.execute('SELECT * FROM inventory'))),
                    list(map(tuple,c.execute('SELECT * FROM bank_items'))),
                    list(map(tuple,c.execute('SELECT * FROM shop_purchase_lots_v1175'))),
                    list(map(tuple,c.execute('SELECT * FROM v106_item_instances'))))
        before=snapshot()
        ck(asyncio.run(session.bank_deposit_item('ring 1')) is False,'deposit denied')
        ck(len(session.sent)>0 and 'v106' in session.sent[-1],'screen reader deposit explains')
        ck(snapshot()==before,'deposit no SQL changes (including shop lots)')
        ck(asyncio.run(session.bank_withdraw_item('ring 1')) is False,'withdraw denied')
        ck('v106' in session.sent[-1],'screen reader withdraw explains')
        ck(snapshot()==before,'withdraw no SQL changes')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        return n
    finally:
        c.close()
        bank.ITEMS=orig_items
        bank.is_character_bound_item=orig_bound
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 REAL BANK PRE-FLIGHT:',run(),'PASS',flush=True)
