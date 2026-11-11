# -*- coding: utf-8 -*-
"""Read-only v106 physical EQ cutover preflight with adversarial fixtures."""
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_instances_v10600 import (
    apply_to_explicit_test_copy,cutover_readiness,
)


def run():
    c=sqlite3.connect(':memory:')
    c.executescript('''
    CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
       PRIMARY KEY(account_id,item_id));
    CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
       PRIMARY KEY(account_id,slot));
    CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
       PRIMARY KEY(account_id,record_key));
    INSERT INTO inventory VALUES(1,'helm',1),(2,'helm',2),(3,'helm',1);
    INSERT INTO equipment VALUES(1,'head','helm'),(2,'head','helm'),(3,'head','helm');
    INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:helm',5),
       (2,'eq_evolution_v10500:helm',7),
       (9,'eq_evolution_v10500:helm',3);
    ''')
    catalog={'helm':{'type':'armor'}}
    count=0
    def ck(cond,msg):
        nonlocal count
        assert cond,msg;count+=1
    before_inv=list(c.execute('SELECT * FROM inventory'))
    report=cutover_readiness(c,catalog)
    ck(not report['data_consistent'] and not report['gameplay_ready'],
       'unmigrated data never marked ready')
    ck(any('wiele kopii' in x[2] for x in report['blocking_issues']),'duplicated gear reported')
    ck(any('historyczna' in x[2] for x in report['blocking_issues']),'orphan legacy stage reported')
    ck(any('migracja' in x[2] for x in report['blocking_issues']),'missing schema reported')
    apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    report=cutover_readiness(c,catalog)
    ck(report['instance_rows']==2,'unique copies migrated')
    ck(any('wiele kopii' in x[2] for x in report['blocking_issues']),
       'duplicate still blocks after partial migration')
    ck(any('historyczna' in x[2] for x in report['blocking_issues']),
       'orphan still blocks after partial migration')
    ck(list(c.execute('SELECT * FROM inventory'))==before_inv,'preflight read-only')
    c.execute("UPDATE inventory SET quantity=1 WHERE account_id=2")
    c.execute("DELETE FROM player_records_v03051 WHERE account_id=9")
    apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
    clear=cutover_readiness(c,catalog)
    ck(clear['data_consistent'] and not clear['blocking_issues'],
       'explicitly reconciled test data no blockers')
    ck(not clear['gameplay_ready'],'clean shadow ledger does not authorize cutover')
    c.execute("INSERT INTO equipment VALUES(1,'body','helm')")
    report=cutover_readiness(c,catalog)
    ck(any('więcej założonych' in x[2] for x in report['blocking_issues']),
       'two equipped slots for one physical copy blocked')
    c.execute("DELETE FROM equipment WHERE account_id=1 AND slot='body'")
    c.execute("UPDATE v106_item_instances SET account_id=999 WHERE account_id=1")
    report=cutover_readiness(c,catalog)
    ck(any('osierocona' in x[2] for x in report['blocking_issues']),
       'altered owner creates orphan')
    ck(any('brak fizycznej' in x[2] for x in report['blocking_issues']),
       'original owner missing migrated unit')
    c.execute("UPDATE v106_item_instances SET account_id=1 WHERE account_id=999")
    ck(cutover_readiness(c,catalog)['data_consistent'],'owner repair restores shadow consistency')
    c.execute("UPDATE inventory SET quantity=2 WHERE account_id=1")
    ck(not cutover_readiness(c,catalog)['data_consistent'],
       'newly duplicated quantity invalidates migration readiness')
    c.execute("UPDATE inventory SET quantity=1 WHERE account_id=1")
    ck(cutover_readiness(c,catalog)['data_consistent'],'quantity restored')
    ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite intact')
    c.close()
    return count

if __name__=='__main__':print('V106 EQ CUTOVER READINESS:',run(),'PASS',flush=True)
