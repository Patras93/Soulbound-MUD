# -*- coding: utf-8 -*-
"""v106 staging: real SessionCraftingMixin+DB take ingredients from two sources."""
import os
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from player.session_mixins.crafting import SessionCraftingMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account
from systems.equipment_crafting_guard_v10600 import active, guard_recipe, take_one_kind

CAT={'ring':{'type':'armor'},'helm':{'type':'armor'},'ore':{'type':'material'},'gem':{'type':'material'}}
class DB(DatabaseInventoryMixin):
    def __init__(self,conn):
        self.conn=conn
        self._v106_shadow_slots_disposable_copy=True
        self._v106_shadow_item_catalog=CAT

class Session(SessionCraftingMixin):
    def __init__(self,db):
        self.server=SimpleNamespace(db=db)
        self.account_id=1
    def recipe_container_for_item(self,item):
        return 'craftbox' if str(item) in ('ore','gem') else None


def run():
    prev=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    raw=sqlite3.connect(':memory:');raw.row_factory=sqlite3.Row
    raw.executescript('''
      CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(account_id,item_id));
      CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
          PRIMARY KEY(account_id,slot));
      CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
          PRIMARY KEY(account_id,record_key));
      CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
          quantity INTEGER,PRIMARY KEY(account_id,container,item_id));
      CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
          paid_silver INTEGER,quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
      INSERT INTO inventory VALUES(1,'ore',2),(1,'gem',2),(1,'ring',2),(2,'ore',4);
      INSERT INTO profession_storage VALUES(1,'craftbox','ore',3),(1,'craftbox','gem',1);
      INSERT INTO equipment VALUES(1,'finger','ring');
      INSERT INTO shop_purchase_lots_v1175 VALUES(1,'ore',20,2),(1,'ring',90,1);
    ''')
    db=DB(_DeferredCommitConnection(raw));sess=Session(db)
    n=0
    def ok(flag,msg):
        nonlocal n
        if not flag:raise AssertionError(msg)
        n+=1
    def denied(func,error,msg):
        nonlocal n
        try:func()
        except error:n+=1
        else:raise AssertionError(msg)
    def snapshot():
        return {t:tuple(tuple(row) for row in raw.execute('SELECT * FROM '+t+' ORDER BY 1,2'))
                for t in ('inventory','profession_storage','shop_purchase_lots_v1175',
                          'v106_item_instances','v106_equipped_instances','v106_stored_instances')}
    try:
        prepare_on_disposable_copy(db.conn,CAT,confirm_disposable_copy=True)
        ok(active(db),'staging armed')
        ok(raw.execute("SELECT COUNT(*) FROM v106_item_instances WHERE item_id='ring'").fetchone()[0]==2,
           'two physical rings')
        before=snapshot()
        ok(sess.consume_recipe_item('ore',4) is True,'mixed sources atomic')
        ok(db.storage_qty(1,'craftbox','ore')==0 and db.item_qty(1,'ore')==1,
           'storage first, then one inventory unit')
        ok(db.item_qty(2,'ore')==4,'no other account affected')
        ok(raw.execute("SELECT quantity FROM shop_purchase_lots_v1175 WHERE account_id=1 AND item_id='ore'").fetchone()[0]==1,
           'cost basis adjusted in atomic inventory consume')
        raw.rollback() if raw.in_transaction else None
        # reset with explicit values, no direct SQL change to tracked gear.
        raw.execute("INSERT OR REPLACE INTO profession_storage(account_id,container,item_id,quantity) VALUES(1,'craftbox','ore',3)")
        raw.execute("UPDATE inventory SET quantity=2 WHERE account_id=1 AND item_id='ore'")
        raw.execute("UPDATE shop_purchase_lots_v1175 SET quantity=2 WHERE account_id=1 AND item_id='ore'")
        raw.commit()
        before=snapshot()
        ok(sess.consume_recipe_item('ore',6) is False,'insufficient across both sources')
        ok(snapshot()==before,'insufficient leaves both ledgers unchanged')
        # Failing inventory SQL must roll back previously removed storage.
        raw.execute('''CREATE TRIGGER fail_ore BEFORE UPDATE ON inventory
           WHEN NEW.item_id='ore' AND NEW.account_id=1
           BEGIN SELECT RAISE(ABORT,'blocked inventory'); END''');raw.commit()
        denied(lambda:sess.consume_recipe_item('ore',4),sqlite3.IntegrityError,
               'SQL error in second source raises')
        ok(snapshot()==before,'SQL failure rolls back storage and cost')
        raw.execute('DROP TRIGGER fail_ore');raw.commit()
        # Outer SAVEPOINT remains owned by the caller.
        raw.execute('SAVEPOINT outer_craft')
        ok(sess.consume_recipe_item('ore',4) is True,'nested SAVEPOINT removal')
        ok(raw.in_transaction,'deferred commit did not end outer transaction')
        raw.execute('ROLLBACK TO SAVEPOINT outer_craft')
        raw.execute('RELEASE SAVEPOINT outer_craft')
        ok(snapshot()==before,'outer rollback restores everything')
        # v106 physical equipment never enters ordinary crafting material path.
        denied(lambda:sess.consume_recipe_item('ring',1),RuntimeError,
               'physical item cannot be consumed as material')
        denied(lambda:db.consume_items_across_storage_and_inventory(1,('ore','ring'),1),
               RuntimeError,'direct DB pooled consumption must also be guarded')
        denied(lambda:guard_recipe(db,{'ingredients':{'ore':1,'ring':1}}),RuntimeError,
               'direct equipment ingredient blocks before craft wait')
        denied(lambda:guard_recipe(db,{'ingredients':{'ore':1},
                   'distinct_ingredient_pool':['ring']}),RuntimeError,
               'distinct pool protects equipment')
        denied(lambda:guard_recipe(db,{'pooled_ingredient_pool':['ring']}),RuntimeError,
               'pooled pool protects equipment')
        ok(snapshot()==before,'denied gear leaves DB unchanged')
        denied(lambda:sess.consume_recipe_item('ore',-1),ValueError,
               'negative requested qty rejected')
        ok(sess.consume_recipe_item('ore',0) is True,'zero amount no-op')
        ok(sess.consume_recipe_item('gem',2) is True,'other material from two sources')
        ok(db.storage_qty(1,'craftbox','gem')==0 and db.item_qty(1,'gem')==1,
           'second material consumed with no gear impact')
        # Low-level ingredients + output in one transaction. This deliberately
        # does NOT claim the complete high-level XP and quality crafting path.
        raw.execute("INSERT OR REPLACE INTO profession_storage VALUES(1,'craftbox','ore',3)")
        raw.execute("INSERT OR REPLACE INTO inventory VALUES(1,'ore',2)")
        raw.commit()
        ok(db.craft_item_atomic_v106(1,{'ore':4},'helm',2,
                  containers={'ore':'craftbox'}) is True,'atomic low-level craft')
        helms=[row[0] for row in raw.execute(
              "SELECT instance_id FROM v106_item_instances WHERE account_id=1 AND item_id='helm'")]
        ok(len(helms)==len(set(helms))==2,'crafted helms have distinct IDs')
        ok(db.item_qty(1,'helm')==2,'minted count matches inventory')
        ok(db.storage_qty(1,'craftbox','ore')==0 and db.item_qty(1,'ore')==1,
           'all recipe ingredients consumed atomically')
        ok(raw.execute('PRAGMA integrity_check').fetchone()[0]=='ok','atomic output SQLite integrity')
        # Force a failure after ingredients disappear, before output commits.
        raw.execute("INSERT OR REPLACE INTO profession_storage VALUES(1,'craftbox','ore',3)")
        raw.execute("INSERT OR REPLACE INTO inventory VALUES(1,'ore',2)")
        raw.commit()
        raw.execute('''CREATE TRIGGER block_helm BEFORE INSERT ON v106_item_instances
                 WHEN NEW.item_id='helm' BEGIN SELECT RAISE(ABORT,'blocked craft'); END''')
        raw.commit()
        pre=snapshot()
        denied(lambda:db.craft_item_atomic_v106(1,{'ore':4},'helm',1,
                   containers={'ore':'craftbox'}),sqlite3.IntegrityError,
               'failed physical output reverts every ingredient')
        ok(snapshot()==pre,'output failure rolled back inventory, storage and instances')
        raw.execute('DROP TRIGGER block_helm');raw.commit()
        ok(db.craft_item_atomic_v106(1,{'ore':6},'helm',1,
                   containers={'ore':'craftbox'}) is False,'missing ingredient prevents entire craft')
        ok(snapshot()==pre,'missing materials changed nothing')
        raw.execute('SAVEPOINT caller_craft')
        ok(db.craft_item_atomic_v106(1,{'ore':4},'helm',1,
                   containers={'ore':'craftbox'}) is True,'output nested in caller transaction')
        raw.execute('ROLLBACK TO SAVEPOINT caller_craft')
        raw.execute('RELEASE SAVEPOINT caller_craft')
        ok(snapshot()==pre,'outer rollback restores crafted instances')
        denied(lambda:db.craft_item_atomic_v106(1,{'ring':1},'helm',1),RuntimeError,
               'physical EQ cannot be consumed as a material')
        denied(lambda:db.craft_item_atomic_v106(1,{'ore':-1},'helm',1),ValueError,
               'negative ingredient blocked')
        denied(lambda:db.craft_item_atomic_v106(1,{'ore':1},'helm',0),ValueError,
               'zero output count blocked')
        _check_account(db.conn,1,CAT);ok(True,'physical ledger consistent')
        ok(raw.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # A test DB requiring staging must not silently fall back to v105.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        denied(lambda:sess.consume_recipe_item('ore',1),PermissionError,
               'staging environment switch required')
        os.environ['SOULBOUND_V106_STAGING']='1'
        db._v106_shadow_slots_disposable_copy=False
        ok(active(db) is False,'v105 non-staged mode unchanged')
        ok(guard_recipe(db,{'ingredients':{'ring':1}}) is None,
           'non-staged v105 recipe guard inert')
        return n
    finally:
        raw.close()
        if prev is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=prev

if __name__=='__main__':print('V106 CRAFT ATOMIC STAGING:',run(),'PASS',flush=True)
