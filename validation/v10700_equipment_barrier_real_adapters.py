# -*- coding: utf-8 -*-
"""Test physical copy adapter against real SQLite TEMP write barriers."""
from pathlib import Path
import os,sqlite3,sys
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy,_check_account
from systems.v10700_equipment_write_barrier import install_on_migrated_connection

CAT={'helm':{'type':'armor'},'glove':{'type':'armor'},'ore':{'type':'material'}}
class Db(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_slots_disposable_copy=True
        self._v106_shadow_item_catalog=CAT

def run():
    checks=0
    def ck(value,label):
        nonlocal checks
        assert value,label
        checks+=1
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    try:
        with TemporaryDirectory(prefix='v107-gear-route-') as directory:
            raw=sqlite3.connect(Path(directory)/'copy.db')
            raw.row_factory=sqlite3.Row
            conn=_DeferredCommitConnection(raw)
            conn.executescript('''
                CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
                    PRIMARY KEY(account_id,item_id));
                CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
                    PRIMARY KEY(account_id,slot));
                CREATE TABLE bank_items(account_id INTEGER,item_id TEXT,quantity INTEGER,
                    PRIMARY KEY(account_id,item_id));
                CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,
                    PRIMARY KEY(account_id,container,item_id));
                CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
                    PRIMARY KEY(account_id,record_key));
                CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
                    paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
                INSERT INTO inventory VALUES(1,'helm',2);
                INSERT INTO equipment VALUES(1,'head','helm');
            ''')
            conn.commit()
            db=Db(conn)
            prepare_on_disposable_copy(conn,CAT,confirm_disposable_copy=True)
            ck(install_on_migrated_connection(db,CAT,approved_test_copy=True)==2,
               'write barrier should recognize both armor templates')
            def fail(statement):
                try:conn.execute(statement)
                except sqlite3.DatabaseError:return True
                return False
            ck(fail('UPDATE inventory SET quantity=4 WHERE account_id=1'),
               'untracked SQL changed initial helm stack')
            db.add_item(1,'helm',1)
            ck(db.item_qty(1,'helm')==3,'atomic tracked drop should work')
            ck(db.remove_item(1,'helm',1) is True,'atomic tracked consume should work')
            ck(db.transfer_inventory_item(1,2,'helm',1) is True,
               'atomically moved one unbound helm')
            ck(db.item_qty(1,'helm')==1 and db.item_qty(2,'helm')==1,
               'transfer balances diverged')
            _check_account(conn,1,CAT);_check_account(conn,2,CAT)
            db.equip(2,'head','helm')
            ck(conn.execute('SELECT instance_id FROM v106_equipped_instances WHERE account_id=2').fetchone() is not None,
               'physical equip could not write under barrier')
            db.unequip(2,'head')
            ck(conn.execute('SELECT COUNT(*) FROM v106_equipped_instances WHERE account_id=2').fetchone()[0]==0,
               'physical unequip could not clear exact slot')
            ck(fail("DELETE FROM inventory WHERE account_id=2 AND item_id='helm'"),
               'raw delete bypassed physical ledger')
            ck(db.remove_item(2,'helm',1) is True,'tracked removal allowed')
            ck(db.item_qty(2,'helm')==0,'tracked removal reconciled')
            ck(not getattr(conn,'_v107_eq_write_depth',0),'adapter permission leaked')
            ck(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
            conn.close()
    finally:
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous
    return checks
if __name__=='__main__':print('V107 REAL EQ ADAPTERS WITH SQL BARRIER:',run(),'PASS')
