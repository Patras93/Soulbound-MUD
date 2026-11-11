# -*- coding: utf-8 -*-
"""Regression for rejected untracked SQLite writes on a disposable ledger."""
from contextlib import closing
from pathlib import Path
import sqlite3, sys
from tempfile import TemporaryDirectory
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from systems.v10700_equipment_write_barrier import install_on_migrated_connection,approved_instance_operation

class Db:
    def __init__(self, conn):
        self.conn=conn
        self._v106_shadow_slots_disposable_copy=True


def run():
    checks=0
    def ck(condition,description):
        nonlocal checks
        assert condition, description
        checks+=1
    with TemporaryDirectory(prefix='v107-eq-barrier-') as directory:
        path=Path(directory)/'copy.db'
        raw=sqlite3.connect(path)
        conn=_DeferredCommitConnection(raw)
        for t in ('inventory','equipment','bank_items','profession_storage'):
            conn.execute(f'CREATE TABLE {t} (account_id INTEGER, item_id TEXT, quantity INTEGER)')
        conn.execute('CREATE TABLE v106_item_instances (instance_id TEXT PRIMARY KEY)')
        conn.execute('CREATE TABLE v106_equipped_instances (instance_id TEXT PRIMARY KEY)')
        conn.execute('CREATE TABLE v106_stored_instances (instance_id TEXT PRIMARY KEY)')
        conn.commit()
        db=Db(conn)
        catalog={'helm':{'type':'armor'},'wood':{'type':'material'}}
        ck(install_on_migrated_connection(db,catalog,approved_test_copy=True)==1,
            'gear registry should contain armor only')
        conn.execute("INSERT INTO inventory VALUES (1,'wood',7)")
        conn.commit()
        ck(conn.execute("SELECT quantity FROM inventory WHERE item_id='wood'").fetchone()[0]==7,
           'barrier blocked ordinary materials')
        def rejected(stmt):
            try:conn.execute(stmt)
            except sqlite3.DatabaseError: return True
            return False
        ck(rejected("INSERT INTO inventory VALUES (1,'helm',1)"),'legacy loot minted tracked armor')
        ck(rejected("INSERT INTO bank_items VALUES (1,'helm',1)"),'legacy bank minted tracked armor')
        ck(rejected("INSERT INTO profession_storage VALUES (1,'helm',1)"),'legacy storage minted tracked armor')
        ck(rejected("INSERT INTO equipment VALUES (1,'helm',1)"),'legacy equip bypassed slot ledger')
        ck(rejected("INSERT INTO inventory VALUES (1,'craftq_unknown',1)"),
           'unregistered dynamically generated gear was not guarded')
        catalog['craftq_generated_helmet']={'type':'armor'}
        ck(rejected("INSERT INTO inventory VALUES (1,'craftq_generated_helmet',1)"),
           'dynamic template added AFTER startup escaped the barrier')
        with approved_instance_operation(conn):
            conn.execute("INSERT INTO inventory VALUES (1,'helm',1)")
            conn.execute("INSERT INTO equipment VALUES (1,'helm',1)")
        conn.commit()
        ck(conn.execute("SELECT COUNT(*) FROM inventory WHERE item_id='helm'").fetchone()[0]==1,
           'approved adapter could not write')
        ck(rejected("UPDATE inventory SET quantity=100 WHERE item_id='helm'"),
           'legacy direct UPDATE changed owned copies')
        ck(rejected("DELETE FROM equipment WHERE item_id='helm'"),
           'legacy direct DELETE removed a physical slot')
        ck(rejected("UPDATE inventory SET item_id='wood' WHERE item_id='helm'"),
           'legacy UPDATE concealed a protected item via new type')
        ck(not getattr(conn,'_v107_eq_write_depth',0),'write privilege leaked across actions')
        try:
            with approved_instance_operation(conn):
                raise RuntimeError('rollback route')
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: test exception-safe write depth
        ck(not getattr(conn,'_v107_eq_write_depth',0),'exception leaked write privilege')
        conn.commit()
        conn.close()
        with closing(sqlite3.connect(path)) as check:
            ck(check.execute("SELECT quantity FROM inventory WHERE item_id='helm'").fetchone()[0]==1,
               'unsafe changes persisted to disk')
    # A real live path must be exercised with source unchanged and an
    # immutable recovery backup; a removed TODO or a renamed flag is not PASS.
    from validation.v10700_release_readiness import unmet_requirements
    blockers=unmet_requirements()
    ck(not any('produkcyjnego ledgeru' in reason for reason in blockers),
       'production physical ledger failed verified clone')
    ck(not any('ewolucja fizycznych kopii' in reason for reason in blockers),
       'production per-copy evolution failed verified clone')
    return checks

if __name__=='__main__':print('V107 SQLITE PHYSICAL EQ WRITE BARRIER:',run(),'PASS')
