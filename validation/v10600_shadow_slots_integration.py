# -*- coding: utf-8 -*-
"""Real DatabaseInventoryMixin equip/unequip on disposable SQLite only."""
import os,sys,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import (
    prepare_on_disposable_copy,equipped_copy,_check_account,
)

CAT={'plate':{'type':'armor'},'ring':{'type':'armor'},'helm':{'type':'armor'}}
class FakeDB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_item_catalog=CAT
        self._v106_shadow_slots_disposable_copy=True


def run():
    previous=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    c=sqlite3.connect(':memory:')
    c.row_factory=sqlite3.Row
    c.executescript('''
     CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
        PRIMARY KEY(account_id,item_id));
     CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
        PRIMARY KEY(account_id,slot));
     CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
        PRIMARY KEY(account_id,record_key));
     INSERT INTO inventory VALUES(1,'plate',1),(1,'ring',2),(2,'helm',1),(3,'ring',2);
     INSERT INTO equipment VALUES(1,'body','plate'),(1,'ring1','ring');
     INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:plate',6),
        (2,'eq_evolution_v10500:helm',2),(3,'eq_evolution_v10500:ring',7);
    ''')
    checks=0
    def ok(flag,label):
        nonlocal checks
        if not flag:raise AssertionError(label)
        checks+=1
    db=FakeDB(c)
    try:
        try:prepare_on_disposable_copy(c,CAT)
        except PermissionError:checks+=1
        else:raise AssertionError('shadow unauthorized')
        result=prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        ok(result['new_slot_bindings']==2,'bind existing slots')
        ok(result['migrated']['new_instances']==4, '1 plate + 2 rings + 1 helm, ambiguous untouched')
        ok(result['migrated']['ambiguous']==1,'stage7 identical rings remain ambiguous')
        old=equipped_copy(c,1,'ring1',CAT)
        ok(old is not None and old[1:] ==('ring',0),'original ring bound')
        db.equip(1,'ring2','ring')
        new=equipped_copy(c,1,'ring2',CAT)
        ok(new and new[0]!=old[0] and new[2]==0,'second physical ring distinct')
        ok(len({row[0] for row in c.execute('SELECT instance_id FROM v106_equipped_instances')})==3,'unique physical slots')
        try:db.equip(1,'ring3','ring')
        except RuntimeError:checks+=1
        else:raise AssertionError('third ring equipped')
        ok(c.execute('SELECT count(*) FROM equipment WHERE account_id=1').fetchone()[0]==3,'third ring rolled back')
        try:db.equip(1,'ring1','helm')
        except RuntimeError:checks+=1
        else:raise AssertionError('other owner helm stolen')
        ok(equipped_copy(c,1,'ring1',CAT)==old,'ownership fail left original')
        db.unequip(1,'ring1')
        ok(equipped_copy(c,1,'ring1',CAT) is None,'detach erased slot and shadow')
        db.unequip(1,'body')
        ok(equipped_copy(c,1,'body',CAT) is None,'old unique physical copy released')
        db.equip(1,'ring1','plate')
        ok(equipped_copy(c,1,'ring1',CAT)[1:] ==('plate',6),'unique evolved plate moved to ring1')
        # A copied item cannot be worn twice, but the second ring is already bound.
        try:db.equip(1,'extra','plate')
        except RuntimeError:checks+=1
        else:raise AssertionError('same physical copy double equipped')
        ok(equipped_copy(c,1,'ring1',CAT)[1]=='plate','ring1 slot did not change')
        _check_account(c,1,CAT);checks+=1
        again=prepare_on_disposable_copy(c,CAT,confirm_disposable_copy=True)
        ok(again['new_slot_bindings']==0,'idempotent binding')
        # Direct untracked old SQL is detected, not silently accepted.
        c.execute("UPDATE equipment SET item_id='ring' WHERE account_id=1 AND slot='ring1'")
        try:db.unequip(1,'ring2')
        except RuntimeError:checks+=1
        else:raise AssertionError('untracked mutation accepted')
        c.execute("UPDATE equipment SET item_id='plate' WHERE account_id=1 AND slot='ring1'")
        # caller-owned transaction is not committed
        c.execute('SAVEPOINT outer_v106')
        db.unequip(1,'ring2')
        ok(equipped_copy(c,1,'ring2',CAT) is None, 'outer deletion staged')
        c.execute('ROLLBACK TO SAVEPOINT outer_v106')
        c.execute('RELEASE SAVEPOINT outer_v106')
        ok(equipped_copy(c,1,'ring2',CAT) is not None,'outer rollback restored both tables')
        # Direct changes to inventory by any legacy route must fail closed.
        c.execute("UPDATE inventory SET quantity=1 WHERE account_id=1 AND item_id='ring'")
        try:db.unequip(1,'ring2')
        except RuntimeError:checks+=1
        else:raise AssertionError('untracked inventory reduction accepted')
        c.execute("UPDATE inventory SET quantity=2 WHERE account_id=1 AND item_id='ring'")
        ok(equipped_copy(c,1,'ring2',CAT) is not None,'untracked change did not drop instance')
        # Staging flag is required even if object has opt-in marker.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        try:db.unequip(1,'ring2')
        except PermissionError:checks+=1
        else:raise AssertionError('did not check staging env')
        ok(equipped_copy(c,1,'ring2',CAT) is not None,'production guard does not mutate')
        ok(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # A deliberate SQL failure after the legacy equipment change must
        # roll back BOTH legacy and new slot rows atomically.
        os.environ['SOULBOUND_V106_STAGING']='1'
        c.execute('CREATE TRIGGER block_shadow_extra BEFORE INSERT ON v106_equipped_instances '
                  "WHEN NEW.slot='blocked' BEGIN SELECT RAISE(ABORT,'blocked'); END")
        try:db.equip(1,'blocked','ring')
        except sqlite3.IntegrityError:checks+=1
        else:raise AssertionError('trigger failure did not abort transaction')
        ok(c.execute("SELECT COUNT(*) FROM equipment WHERE slot='blocked'").fetchone()[0]==0,
           'legacy side of failed atomic insert restored')
        ok(c.execute("SELECT COUNT(*) FROM v106_equipped_instances WHERE slot='blocked'").fetchone()[0]==0,
           'shadow side of failed insert restored')
        # Without the marker, original v105 equip/unequip functions operate
        # without requiring shadow schema and without changing shadow rows.
        db._v106_shadow_slots_disposable_copy=False
        old_shadow=c.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0]
        db.equip(4,'body','plain_old_item')
        ok(c.execute("SELECT item_id FROM equipment WHERE account_id=4 AND slot='body'").fetchone()[0]
           =='plain_old_item','legacy equip unchanged without marker')
        db.unequip(4,'body')
        ok(c.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0]
           ==old_shadow,'legacy operations did not touch shadow')
        db._v106_shadow_slots_disposable_copy=True
        db.unequip(1,'ring2')  # commits change, leaves ring physically free
        ok(not c.in_transaction,'fixture ready for commit=False test')
        db.equip(1,'ring2','ring',commit=False)
        ok(c.in_transaction,'commit=False leaves SQL pending')
        ok(equipped_copy(c,1,'ring2',CAT) is not None,'pending physical binding')
        c.rollback()
        ok(equipped_copy(c,1,'ring2',CAT) is None,'rollback pending legacy and shadow rows')
        return checks
    finally:
        c.close()
        if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous

if __name__=='__main__':print('V106 REAL DB SHADOW EQUIP:',run(),'PASS')
