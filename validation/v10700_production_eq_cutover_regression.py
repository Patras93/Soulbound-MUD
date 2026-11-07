# -*- coding: utf-8 -*-
"""Physical EQ v107: isolated, real on-disk SQLite production path rehearsal.

Authorization is mocked ONLY inside this test process. No live database is opened.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from systems.v10700_live_equipment import activate_production_ledger, production_copy_evolution
from systems.equipment_evolution_v10500 import required_materials
import systems.v10700_activation as act

CAT={'helm':{'type':'armor','name':'Hełm','defense':12,'affix_amount':3,'stats':{}},
     'cloth':{'type':'material'}}

class DB(DatabaseInventoryMixin):
    def __init__(self,path):
        self.path=str(path)
        raw=sqlite3.connect(path)
        raw.row_factory=sqlite3.Row
        self.conn=_DeferredCommitConnection(raw)
        self.conn.execute('PRAGMA foreign_keys=ON')

def seed(db):
    db.conn.executescript('''
        CREATE TABLE accounts(id INTEGER PRIMARY KEY);
        CREATE TABLE characters(id INTEGER PRIMARY KEY);
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
        CREATE TABLE equipment_reforges(account_id INTEGER,item_id TEXT,affix TEXT,
            PRIMARY KEY(account_id,item_id));
        CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
            paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
        INSERT INTO accounts VALUES(1),(2);
        INSERT INTO inventory VALUES(1,'helm',2);
        INSERT INTO equipment VALUES(1,'head','helm');
    ''')
    db.conn.commit()

def run():
    count=0
    def ck(ok,what):
        nonlocal count
        assert ok,what
        count+=1
    before=act.production_approved
    try:
        with TemporaryDirectory(prefix='sb107_live_gear_') as temp:
            db=DB(Path(temp)/'original.sqlite');seed(db)
            # A random call from an unapproved package must not create a ledger.
            act.production_approved=lambda:False
            try:activate_production_ledger(db,CAT)
            except PermissionError:ck(True,'unapproved live startup rejected')
            else:raise AssertionError('unapproved package started live EQ')
            ck(not db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v107_eq_production_cutover'").fetchone(),
               'unapproved package modified schema')
            # Test-only simulation of an installer-verified 60/60 candidate.
            act.production_approved=lambda:True
            ck(activate_production_ledger(db,CAT),'authorised live migration')
            ck(db.conn.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==2,
               'both copies migrated')
            uid=db.conn.execute("SELECT instance_id FROM v106_equipped_instances WHERE account_id=1 AND slot='head'").fetchone()[0]
            ck(bool(uid),'worn physical identity bound')
            copies_before={r[0] for r in db.conn.execute('SELECT instance_id FROM v106_item_instances')}
            ck(len(copies_before)==2,'individual IDs unique')
            backup_name=db.conn.execute('SELECT backup_name FROM v107_eq_production_cutover').fetchone()[0]
            backup=Path(temp)/'backups'/backup_name
            ck(backup.is_file(),'durable rollback backup exists')
            with closing(sqlite3.connect(backup)) as old:
                ck(old.execute("SELECT name FROM sqlite_master WHERE name='v106_item_instances'").fetchone() is None,
                    'rollback backup contains original legacy schema')
                ck(old.execute('SELECT quantity FROM inventory WHERE account_id=1').fetchone()[0]==2,
                    'original inventory preserved in backup')
            try:db.conn.execute("UPDATE inventory SET quantity=5 WHERE account_id=1 AND item_id='helm'")
            except sqlite3.DatabaseError:ck(True,'raw SQL cannot mint tracked gear')
            else:raise AssertionError('barrier bypass')
            try:db.conn.execute("UPDATE v106_item_instances SET account_id=999 WHERE instance_id=?",(uid,))
            except sqlite3.DatabaseError:ck(True,'raw SQL cannot steal physical identity')
            else:raise AssertionError('identity ledger bypass')
            try:db.conn.execute("INSERT INTO equipment_reforges VALUES (1,'helm','raw')")
            except sqlite3.DatabaseError:ck(True,'old template-scoped forge cannot corrupt copies')
            else:raise AssertionError('legacy forge bypass')
            db.add_item(1,'helm',1)
            ck(db.item_qty(1,'helm')==3,'approved physical add')
            ck(db.transfer_inventory_item(1,2,'helm',1),'safe trade')
            ck(db.item_qty(1,'helm')==2 and db.item_qty(2,'helm')==1,'trade exact balances')
            for mat,qty in required_materials(1).items():
                db.conn.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',(1,'craftbox',mat,qty))
            db.conn.commit()
            done,stage=production_copy_evolution(db,1,'head',str(uid))
            ck(done and stage==1,'one exact copy evolved in production path')
            ck(db.conn.execute('SELECT evolution_stage FROM v106_item_instances WHERE instance_id=?',(uid,)).fetchone()[0]==1,
                'correct physical ID evolved')
            ck(db.conn.execute('SELECT COUNT(*) FROM v106_item_instances WHERE evolution_stage=0').fetchone()[0]==2,
                'other copies not evolved')
            ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity after operations')
            db.conn.close()
            # An ordinary restart must NEVER rerun v106 migration and reset stage 1.
            reopened=DB(Path(temp)/'original.sqlite')
            ck(activate_production_ledger(reopened,CAT),'reopen existing ledger')
            ck(reopened.conn.execute('SELECT evolution_stage FROM v106_item_instances WHERE instance_id=?',(uid,)).fetchone()[0]==1,
                'no stage loss on restart')
            ck(reopened.conn.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==3,
                'no duplicate gear after restart')
            ck({r[0] for r in reopened.conn.execute('SELECT instance_id FROM v106_item_instances')}==copies_before | {
                r[0] for r in reopened.conn.execute('SELECT instance_id FROM v106_item_instances WHERE origin=\'v106_inventory\'')
            },'identity survives reboot')
            try:activate_production_ledger(reopened,CAT)
            except RuntimeError:ck(True,'second bootstrap on same connection rejected')
            else:raise AssertionError('double bootstrap silently allowed')
            reopened.conn.close()
        return count
    finally:
        act.production_approved=before

if __name__=='__main__': print('V107 PRODUKCYJNY EQ - PRÓBA NA KOPII:',run(),'PASS',flush=True)
