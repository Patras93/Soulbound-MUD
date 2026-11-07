# -*- coding: utf-8 -*-
"""Test real storage mixin, atomic per-copy relocation with cost-basis ledger."""
import os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy
CAT={'helm':{'type':'armor'},'plate':{'type':'armor'}}
class DB(DatabaseInventoryMixin):
    def __init__(self,c):
        self.conn=c
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True
        self._v106_storage_shadow_disposable_copy=True

def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
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
     CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
       quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
     INSERT INTO inventory VALUES(1,'helm',2),(1,'plate',1);
     INSERT INTO equipment VALUES(1,'head','helm');
     INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:plate',6);
     INSERT INTO shop_purchase_lots_v1175 VALUES(1,'helm',80,2);
    ''')
    checks=0
    def ck(b,msg):
        nonlocal checks
        assert b,msg;checks+=1
    def denied(fn,error):
        nonlocal checks
        try:fn()
        except error:checks+=1
        else:raise AssertionError('unexpected unsafe success')
    try:
        db=DB(c)
        prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        def snap():
            tables=('inventory','equipment','v106_item_instances',
                    'v106_stored_instances','shop_purchase_lots_v1175','profession_storage')
            return {t:[tuple(x) for x in c.execute('SELECT * FROM '+t+' ORDER BY 1,2')]
                    for t in tables}
        original=snap()
        ck(db.move_storage_equipment_v106(1,'craftbox','helm',1),'move one unworn helmet')
        ck(db.item_qty(1,'helm')==1 and db.storage_qty(1,'craftbox','helm')==1,
           'legacy stock split')
        ck(c.execute('SELECT COUNT(*) FROM v106_stored_instances WHERE storage_kind="storage"').fetchone()[0]==1,
           'one exact physical ID stored')
        ck(c.execute("SELECT paid_silver FROM shop_purchase_lots_v1175 WHERE item_id='__storage_v106__:craftbox:helm'").fetchone()[0]==80,
           'cost basis preserved')
        ck(db.move_storage_equipment_v106(1,'craftbox','helm',1) is False,
           'worn second copy cannot move')
        ck(db.move_storage_equipment_v106(1,'craftbox','helm',1,withdraw=True),'withdraw original')
        ck(snap()==original,'physical ID and cost ledger fully restored')
        ck(db.move_storage_equipment_v106(1,'craftbox','plate',1) is False,
           'legacy evolved armor not moved')
        ck(snap()==original,'old evolved item untouched')
        ck(db.move_storage_equipment_v106(1,'craftbox','helm',1,commit=False),
           'pending storage move')
        ck(c.in_transaction,'pending transaction not committed')
        c.rollback()
        ck(snap()==original,'rollback all 3 ledgers and purchase basis')
        c.execute("CREATE TRIGGER fail_box BEFORE INSERT ON profession_storage BEGIN SELECT RAISE(ABORT,'fail box'); END")
        denied(lambda:db.move_storage_equipment_v106(1,'craftbox','helm',1),sqlite3.IntegrityError)
        ck(snap()==original,'SQL trigger rolls back all changes')
        c.execute('DROP TRIGGER fail_box');c.commit()
        c.execute("INSERT INTO profession_storage VALUES(1,'craftbox','helm',1)");c.commit()
        denied(lambda:db.move_storage_equipment_v106(1,'craftbox','helm',1),RuntimeError)
        ck(db.storage_qty(1,'craftbox','helm')==1,'preexisting untracked box untouched')
        c.execute("DELETE FROM profession_storage WHERE item_id='helm'");c.commit()
        denied(lambda:db.move_storage_equipment_v106(1,'bad:name','helm',1),ValueError)
        db._v106_storage_shadow_disposable_copy=False
        denied(lambda:db.move_storage_equipment_v106(1,'craftbox','helm',1),PermissionError)
        ck(snap()==original,'disabled new feature does not mutate')
        denied(lambda:db.add_storage_item(1,'craftbox','helm',1),RuntimeError)
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        return checks
    finally:
        c.close()
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous
if __name__=='__main__':print('V106 STORAGE PHYSICAL EQ:',run(),'PASS')
