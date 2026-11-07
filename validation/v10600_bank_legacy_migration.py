# -*- coding: utf-8 -*-
"""Controlled bank reconciliation on SQLite test copy, without server startup."""
import os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy,_check_account
from systems.equipment_inventory_flow_v10600 import reconcile_legacy_bank_on_disposable_copy

CAT={'ring':{'type':'armor'},'helm':{'type':'armor'}}
class DB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True
        self._v106_bank_shadow_disposable_copy=True

def run():
    original=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.executescript('''
     CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
         PRIMARY KEY(account_id,item_id));
     CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
         PRIMARY KEY(account_id,slot));
     CREATE TABLE bank_items(account_id INTEGER,item_id TEXT,quantity INTEGER,
         PRIMARY KEY(account_id,item_id));
     CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
         PRIMARY KEY(account_id,record_key));
     CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
         paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
     INSERT INTO inventory VALUES(1,'ring',1);
     INSERT INTO bank_items VALUES(1,'ring',2),(2,'helm',1);
     INSERT INTO shop_purchase_lots_v1175 VALUES(1,'__bank_v1175__:ring',120,1);
    ''')
    n=0
    def ck(v,t):
        nonlocal n
        assert v,t;n+=1
    def fail(fn,error):
        nonlocal n
        try:fn()
        except error:n+=1
        else:raise AssertionError('dangerous migration accepted')
    try:
        db=DB(c)
        prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        fail(lambda:reconcile_legacy_bank_on_disposable_copy(db),PermissionError)
        pre=c.execute('SELECT count(*) FROM v106_item_instances').fetchone()[0]
        ck(pre==1,'inventory untouched before bank reconciliation')
        result=reconcile_legacy_bank_on_disposable_copy(db,confirm_disposable_copy=True)
        ck(result['inspected']==2 and result['new_instances']==3,'old bank copies assigned')
        ck(db.bank_item_qty(1,'ring')==2,'historical bank count intact')
        ids=[r[0] for r in c.execute('''SELECT st.instance_id FROM v106_stored_instances st
            WHERE account_id=1 ORDER BY instance_id''')]
        ck(len(ids)==len(set(ids))==2,'bank duplicates have unique IDs')
        ck(db.item_qty(1,'ring')==1,'inventory quantity unchanged')
        _check_account(c,1,CAT);ck(True,'banked copies excluded from inventory')
        ck(reconcile_legacy_bank_on_disposable_copy(db,confirm_disposable_copy=True)['new_instances']==0,
           'idempotent migration')
        ck(db.move_bank_equipment_v106(1,'ring',1,withdraw=True),'old bank gear withdraws')
        ck(db.item_qty(1,'ring')==2 and db.bank_item_qty(1,'ring')==1,
           'withdraw transfers quantity conservatively')
        ck(c.execute('SELECT quantity FROM shop_purchase_lots_v1175 '
                     "WHERE account_id=1 AND item_id='ring'").fetchone()[0]==1,
           'old bank purchase price restored')
        ck(len(set(r[0] for r in c.execute('SELECT instance_id FROM v106_item_instances')))==4,
           'no phantom or duplicate ID')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
        # Evolved legacy copies are explicitly ambiguous: entire batch must roll back.
        c.execute("INSERT OR REPLACE INTO player_records_v03051 VALUES(2,'eq_evolution_v10500:helm',2)")
        c.commit()
        fail(lambda:reconcile_legacy_bank_on_disposable_copy(db,confirm_disposable_copy=True),RuntimeError)
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==4,
           'failed reconciliation never invents IDs')
        c.execute("DELETE FROM player_records_v03051 WHERE account_id=2");c.commit()
        # Drift in bank qty is caught even after a valid initial reconciliation.
        c.execute("UPDATE bank_items SET quantity=4 WHERE account_id=1 AND item_id='ring'")
        c.commit()
        fail(lambda:reconcile_legacy_bank_on_disposable_copy(db,confirm_disposable_copy=True),RuntimeError)
        ck(db.bank_item_qty(1,'ring')==4,'no silent repair of externally changed bank stock')
        return n
    finally:
        c.close()
        if original is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=original
if __name__=='__main__':print('V106 BANK LEGACY RECONCILIATION:',run(),'PASS')
