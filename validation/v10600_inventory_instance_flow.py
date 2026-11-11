# -*- coding: utf-8 -*-
"""v106: real storage mixin methods, physical EQ + fail-closed routes, test DB only."""
import os, sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import (
    prepare_on_disposable_copy, equipped_copy, _check_account)

CAT={'plate':{'type':'armor'}, 'helm':{'type':'armor'}, 'ring':{'type':'armor'},
     'ore':{'type':'material'}}
class DB(DatabaseInventoryMixin):
    def __init__(self,c):
        self.conn=c
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True


def run():
    prev=os.environ.get('SOULBOUND_V106_STAGING')
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
      CREATE TABLE bank_items(account_id INTEGER,item_id TEXT,quantity INTEGER,
                             PRIMARY KEY(account_id,item_id));
      CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
                quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
      CREATE TABLE player_mail_v03051(id INTEGER PRIMARY KEY,
                recipient_account_id INTEGER,attachment_kind TEXT,
                attachment_item_id TEXT, attachment_claimed INTEGER DEFAULT 0);
      INSERT INTO inventory VALUES (1,'ring',2),(1,'plate',1),(1,'ore',5);
      INSERT INTO equipment VALUES(1,'ring1','ring'),(1,'body','plate');
      INSERT INTO player_records_v03051 VALUES
            (1,'eq_evolution_v10500:plate',7);
      INSERT INTO shop_purchase_lots_v1175 VALUES(1,'ring',30,1);
      INSERT INTO player_mail_v03051 VALUES(1,2,'item','ring',0);
    ''')
    checks=0
    def ck(v,msg):
        nonlocal checks
        if not v:raise AssertionError(msg)
        checks+=1
    def fails(func,exc,label):
        nonlocal checks
        try:func()
        except exc:checks+=1
        else:raise AssertionError(label)
    db=DB(c)
    try:
        data=prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        ck(data['new_slot_bindings']==2,'slots prepared')
        orig_ring=equipped_copy(c,1,'ring1',CAT)[0]
        orig_plate=equipped_copy(c,1,'body',CAT)[0]
        ck(equipped_copy(c,1,'body',CAT)[2]==7,'legacy evolved preserved')
        ck(db.remove_item(1,'plate',1) is False,'evolved cannot remove')
        ck(db.transfer_inventory_item(1,2,'plate',1) is False,'evolved cannot transfer')
        ck(db.remove_item(1,'ring',2) is False,'worn copy cannot be consumed')
        ck(db.transfer_inventory_item(1,2,'ring',1) is True,'free copy transfer')
        ck(db.item_qty(1,'ring')==1 and db.item_qty(2,'ring')==1,'transfer conserved quantities')
        ck(equipped_copy(c,1,'ring1',CAT)[0]==orig_ring,'worn instance unchanged')
        moved=c.execute('SELECT instance_id FROM v106_item_instances WHERE account_id=2 AND item_id="ring"').fetchone()[0]
        ck(moved!=orig_ring,'transferred the free copy, not worn')
        ck(db.transfer_inventory_item(1,2,'ring',1) is False,'worn instance cannot transfer')
        ck(db.remove_item(1,'ring',1) is False,'worn instance cannot remove')
        ck(c.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=2 AND item_id="ring"').fetchone()[0]==1,
           'cost lot followed the transferred copy')
        db.equip(2,'ring2','ring')
        ck(equipped_copy(c,2,'ring2',CAT)[0]==moved,'receiver equips same physical copy')
        db.unequip(2,'ring2')
        ck(db.remove_item(2,'ring',1) is True,'remove unbound stage0 copy')
        ck(db.item_qty(2,'ring')==0,'removed inventory row')
        ck(c.execute('SELECT 1 FROM v106_item_instances WHERE instance_id=?',(moved,)).fetchone() is None,
           'removed the exact physical copy')
        db.add_item(2,'helm',2)
        helms=[row[0] for row in c.execute('SELECT instance_id FROM v106_item_instances WHERE account_id=2 AND item_id="helm"')]
        ck(len(helms)==len(set(helms))==2,'each gained copy has new distinct identity')
        ck(db.item_qty(2,'helm')==2,'gained count matches ledger')
        ck(db.remove_item(2,'helm',1) is True,'consume one unbound stage0 copy')
        ck(db.item_qty(2,'helm')==1,'one copy remains')
        ck(len(list(c.execute('SELECT instance_id FROM v106_item_instances WHERE account_id=2 AND item_id="helm"')))==1,
           'physical quantity agrees after consume')
        db.equip(2,'head','helm')
        ck(db.remove_item(2,'helm',1) is False,'cannot consume worn helm')
        ck(db.transfer_inventory_item(2,3,'helm',1) is False,'cannot send worn helm')
        db.unequip(2,'head')
        ck(db.transfer_inventory_item(2,3,'helm',1) is True,'can send unworn helm')
        ck(db.item_qty(3,'helm')==1,'recipient gains helm')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=3 AND item_id="helm"').fetchone()[0]==1,
           'recipient holds same physical helm')
        for label,fn in [
            ('bank.deposit',lambda:db.add_bank_item(1,'ring',1)),
            ('bank.withdraw',lambda:db.remove_bank_item(1,'ring',1)),
            ('storage.deposit',lambda:db.add_storage_item(1,'box','ring',1)),
            ('storage.withdraw',lambda:db.remove_storage_item(1,'box','ring',1)),
            ('mail.send',lambda:db.send_mail_attachment_v0614(1,2,'Tester',kind='item',item_id='ring')),
            ('mail.claim',lambda:db.claim_mail_attachment_v0614(2,1)),
        ]:
            fails(fn,RuntimeError,label+' should be unavailable')
        ck(c.execute('SELECT attachment_claimed FROM player_mail_v03051 WHERE id=1').fetchone()[0]==0,
           'mail not marked received')
        ck(db.item_qty(1,'ring')==1,'blocked routes left inventory unchanged')
        db.add_item(2,'ring',2,commit=False)
        ck(c.in_transaction,'add(commit=False) stays pending')
        ck(db.item_qty(2,'ring')==2,'pending acquisition exists')
        c.rollback()
        ck(db.item_qty(2,'ring')==0,'rollback acquisition restores inventory')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=2 AND item_id="ring"').fetchone()[0]==0,
           'rollback acquisition restores ledger')
        # Second test: consumption also respects caller-owned transaction.
        db.add_item(2,'helm',1)
        before=db.item_qty(2,'helm')
        ck(db.remove_item(2,'helm',1,commit=False) is True,'pending consumption')
        ck(c.in_transaction and db.item_qty(2,'helm')==before-1,'pending removal not auto-committed')
        c.rollback()
        ck(db.item_qty(2,'helm')==before,'rollback restores removed equipment')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=2 AND item_id="helm"').fetchone()[0]==before,
           'rollback restores physical IDs')
        # Legacy per-template rune/forge/upgrade data must NEVER be mixed
        # into an unmodified physical copy until the final per-copy migration.
        c.execute('CREATE TABLE equipment_runes_v0925(account_id INTEGER,item_id TEXT, '
                  'socket_index INTEGER,rune_id TEXT)')
        c.execute("INSERT INTO equipment_runes_v0925 VALUES(2,'helm',0,'fire')")
        ck(db.remove_item(2,'helm',1) is False,'legacy rune blocks removal')
        ck(db.transfer_inventory_item(2,4,'helm',1) is False,'legacy rune blocks transfer')
        fails(lambda:db.add_item(2,'helm',1),RuntimeError,
              'legacy rune blocks another identical item')
        c.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=2 AND item_id='helm'")
        c.commit()
        c.execute('CREATE TRIGGER fail_destination BEFORE INSERT ON inventory '
                 'WHEN NEW.account_id=4 AND NEW.item_id="helm" BEGIN SELECT RAISE(ABORT,"blocked"); END')
        fails(lambda:db.transfer_inventory_item(2,4,'helm',1),sqlite3.IntegrityError,
              'transfer SQL failure rolls back both ledgers')
        ck(db.item_qty(2,'helm')==before and db.item_qty(4,'helm')==0,
           'failed transfer preserves inventories')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=4').fetchone()[0]==0,
           'failed transfer preserves ownership')
        # Direct SQL bypass is still detected; this overlay does not pretend
        # to protect ALL other direct-SQL routes yet.
        c.execute('UPDATE inventory SET quantity=4 WHERE account_id=2 AND item_id="helm"')
        fails(lambda:db.add_item(2,'helm',1),RuntimeError,'direct SQL drift detected')
        c.rollback()
        ck(db.item_qty(2,'helm')==before,'no corrupted direct-SQL commit accepted')
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        fails(lambda:db.add_item(2,'helm',1),PermissionError,'staging flag required')
        os.environ['SOULBOUND_V106_STAGING']='1'
        # Original v105 path for non-gear and when not armed remains unchanged.
        db.add_item(3,'ore',2)
        ck(db.item_qty(3,'ore')==2,'non-gear v105 operation unchanged')
        db._v106_shadow_slots_disposable_copy=False
        db.add_item(4,'ring',1)
        ck(db.item_qty(4,'ring')==1,'legacy without marker is unchanged')
        ck(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=4').fetchone()[0]==0,
           'unarmed legacy route never creates shadow rows')
        ck(equipped_copy(c,1,'body',CAT)[0]==orig_plate,'evolved physical identity remained')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        return checks
    finally:
        c.close()
        if prev is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=prev

if __name__=='__main__':print('V106 REAL DB INVENTORY INSTANCE FLOW:',run(),'PASS',flush=True)
