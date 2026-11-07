# -*- coding: utf-8 -*-
"""Isolated migration prototype tests; no production DB."""
from pathlib import Path
import sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_instances_v10600 import snapshot,apply_to_explicit_test_copy


def run():
    c=sqlite3.connect(':memory:')
    c.executescript('''
       CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
          PRIMARY KEY(account_id,item_id));
       CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
          PRIMARY KEY(account_id,record_key));
       INSERT INTO inventory VALUES(1,'v105_armor',1),(2,'v105_armor',2),
          (3,'v105_armor',1),(4,'ore',999);
       INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:v105_armor',6),
          (2,'eq_evolution_v10500:v105_armor',7),
          (9,'eq_evolution_v10500:v105_armor',4);
    ''')
    catalog={'v105_armor':{'type':'armor'},'ore':{'type':'craft_material'}}
    original_inventory=list(c.execute('SELECT * FROM inventory'))
    original_evolutions=list(c.execute('SELECT * FROM player_records_v03051'))
    checks=0
    def ok(x,msg):
        nonlocal checks
        if not x:raise AssertionError(msg)
        checks+=1
    report=snapshot(c,catalog)
    ok(len(report)==4,'snapshot and orphaned legacy stage')
    try:apply_to_explicit_test_copy(c,catalog)
    except PermissionError:checks+=1
    else:raise AssertionError('missing copy permission accepted')
    out=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    ok(out['new_instances']==2 and out['ambiguous']==2,'stage counts')
    ok(list(c.execute('SELECT account_id,evolution_stage FROM v106_item_instances '
                      'ORDER BY account_id'))==[(1,6),(3,0)],'stage ownership')
    ok(list(c.execute('SELECT account_id,copies,legacy_stage FROM '
                      'v106_evolution_migration_issues'))==[(2,2,7),(9,0,4)],'duplicates and orphan preserved')
    ok(list(c.execute('SELECT * FROM inventory'))==original_inventory,'inventory was changed')
    ok(list(c.execute('SELECT * FROM player_records_v03051'))==original_evolutions,
       'historical evolution was changed')
    repeated=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    ok(repeated['new_instances']==0 and repeated['ambiguous']==2,'idempotence')
    c.execute('UPDATE player_records_v03051 SET value=8 WHERE account_id=1')
    try:apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    except RuntimeError:checks+=1
    else:raise AssertionError('changed evolution silently overwritten')
    ok(list(c.execute('SELECT account_id,evolution_stage FROM v106_item_instances '
                      'ORDER BY account_id'))==[(1,6),(3,0)],'rollback integrity')
    # Re-sync only the disposable test fixture for the next migration case.
    c.execute('UPDATE player_records_v03051 SET value=6 WHERE account_id=1')
    c.execute('UPDATE inventory SET quantity=2 WHERE account_id=1 AND item_id="v105_armor"')
    try:apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    except RuntimeError:checks+=1
    else:raise AssertionError('inventory count drift should block migration')
    ok(list(c.execute('SELECT evolution_stage FROM v106_item_instances '
                      'WHERE account_id=1'))==[(6,)], 'drift did not modify instance')
    c.execute('UPDATE inventory SET quantity=1 WHERE account_id=1 AND item_id="v105_armor"')
    c.execute('UPDATE v106_item_instances SET account_id=999 WHERE account_id=1')
    try:apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    except RuntimeError:checks+=1
    else:raise AssertionError('tampered instance owner accepted')
    c.execute('UPDATE v106_item_instances SET account_id=1 WHERE account_id=999')
    ok(apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)['new_instances']==0,
       'restored identity permits idempotent rerun')
    # Historical ambiguity is resolved ONLY after physical count becomes one;
    # never assign the prior stage arbitrarily while there are two copies.
    c.execute('UPDATE inventory SET quantity=1 WHERE account_id=2 AND item_id="v105_armor"')
    fixed=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    ok(fixed['new_instances']==1 and fixed['ambiguous']==1,'explicitly reduced count resolved')
    ok(list(c.execute('SELECT account_id,evolution_stage FROM v106_item_instances '
                      'ORDER BY account_id'))==[(1,6),(2,7),(3,0)],'correct stage after resolution')
    ok(list(c.execute('SELECT account_id FROM v106_evolution_migration_issues'))==[(9,)],
       'stale duplicate warning cleared, orphan remains')
    # A caller-owned transaction must NOT be committed by migration.
    c.execute('SAVEPOINT sb_v106_outer_fixture')
    c.execute('INSERT INTO inventory VALUES (5,"v105_armor",1)')
    c.execute('INSERT INTO player_records_v03051 VALUES '
              '(5,"eq_evolution_v10500:v105_armor",2)')
    out=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    ok(out['new_instances']==1,'new fixture copy created inside outer savepoint')
    c.execute('ROLLBACK TO SAVEPOINT sb_v106_outer_fixture')
    c.execute('RELEASE SAVEPOINT sb_v106_outer_fixture')
    ok(c.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=5').fetchone()[0]==0,
       'outer transaction controls rollback')
    ok(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','migration SQLite integrity')
    ok(list(c.execute('SELECT value FROM player_records_v03051 '
                      'WHERE account_id=9'))==[(4,)],'orphan stage never erased')
    c.close()
    return checks

if __name__=='__main__':print('V106 EQ MIGRATION STAGING:',run(),'PASS',flush=True)
