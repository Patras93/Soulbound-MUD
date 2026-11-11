# -*- coding: utf-8 -*-
"""Unmodified copies can be allocated; evolved duplicates MUST remain blocked.
Only synthetic in-memory SQLite data, no production writes or gameplay cutover.
"""
from __future__ import annotations
import sqlite3
from systems.equipment_instances_v10600 import apply_to_explicit_test_copy, cutover_readiness


def run():
    c=sqlite3.connect(':memory:')
    try:
        c.executescript('''
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
                PRIMARY KEY(account_id,slot));
            CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
                PRIMARY KEY(account_id,record_key));
            INSERT INTO inventory VALUES(1,'helm',2),(1,'sword',1);
            INSERT INTO equipment VALUES(1,'head','helm'),(1,'weapon','sword');
            INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:sword',5);
        ''')
        catalog={'helm':{'type':'armor'},'sword':{'type':'weapon'}}
        n=0
        def ck(ok,label):
            nonlocal n
            assert ok,label
            n+=1
        before=(list(c.execute('SELECT * FROM inventory')),
                list(c.execute('SELECT * FROM equipment')),
                list(c.execute('SELECT * FROM player_records_v03051')))
        ck(not cutover_readiness(c,catalog)['data_consistent'],'no migration, no pass')
        result=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
        ck(result['new_instances']==3 and result['ambiguous']==0,'3 safely migrated copies')
        ready=cutover_readiness(c,catalog)
        ck(ready['data_consistent'] and not ready['blocking_issues'],'unmodified duplicate is safe')
        ck(not ready['gameplay_ready'],'even complete clone cannot enable gameplay')
        ck(ready['snapshot_items']==2 and ready['instance_rows']==3,'counts preserved')
        ck((list(c.execute('SELECT * FROM inventory')),
            list(c.execute('SELECT * FROM equipment')),
            list(c.execute('SELECT * FROM player_records_v03051')))==before,
            'old data untouched')
        again=apply_to_explicit_test_copy(c,catalog,confirm_disposable_copy=True)
        ck(again['new_instances']==0 and again['ambiguous']==0,'idempotent')
        # Portable SQLite: LIMIT in an UPDATE is an optional compile-time feature.
        # LIMIT inside the SELECT subquery is supported on Windows too.
        c.execute("UPDATE v106_item_instances SET evolution_stage=4 "
                  "WHERE instance_id=(SELECT instance_id FROM v106_item_instances "
                  "WHERE item_id='helm' ORDER BY instance_id LIMIT 1)")
        ck(not cutover_readiness(c,catalog)['data_consistent'],
           'modified duplicate must be blocked')
        c.execute("UPDATE v106_item_instances SET evolution_stage=0 WHERE item_id='helm'")
        ck(cutover_readiness(c,catalog)['data_consistent'],'corrected shadow works')
        c.execute("UPDATE v106_item_instances SET origin='unknown' "
                  "WHERE instance_id=(SELECT instance_id FROM v106_item_instances "
                  "WHERE item_id='helm' ORDER BY instance_id LIMIT 1)")
        ck(not cutover_readiness(c,catalog)['data_consistent'],'unknown copy origin blocked')
        c.execute("UPDATE v106_item_instances SET origin='legacy_unique' WHERE item_id='helm'")
        c.execute("INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:helm',7)")
        ck(not cutover_readiness(c,catalog)['data_consistent'],
           'duplicate with historical evolution never auto-cleared')
        ck(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # Reproduce the shape seen in the user's PREDEPLOY report without
        # copying any private player rows: 155 templates, 184 physical copies.
        # The extra 29 are ordinary, stage-zero duplicates and must NOT be
        # mistaken for 29 unresolved historical evolution decisions.
        replica=sqlite3.connect(':memory:')
        try:
            replica.executescript('''
                CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
                    PRIMARY KEY(account_id,item_id));
                CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
                    PRIMARY KEY(account_id,slot));
                CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
                    PRIMARY KEY(account_id,record_key));
            ''')
            catalog2={f'item_{i:03d}':{'type':'armor'} for i in range(155)}
            replica.executemany('INSERT INTO inventory VALUES(1,?,?)',
                ((item,2 if i<29 else 1) for i,item in enumerate(catalog2)))
            before=list(replica.execute('SELECT * FROM inventory ORDER BY item_id'))
            result=apply_to_explicit_test_copy(replica,catalog2,confirm_disposable_copy=True)
            ready=cutover_readiness(replica,catalog2)
            ck(result['inspected']==155 and result['new_instances']==184 and
                result['ambiguous']==0,'155 templates and 184 copies')
            ck(ready['data_consistent'] and ready['instance_rows']==184 and
                not ready['blocking_issues'],'29 zero-stage duplicate groups do not block')
            ck(not ready['gameplay_ready'] and
                before==list(replica.execute('SELECT * FROM inventory ORDER BY item_id')),
                'synthetic source inventory unchanged and runtime remains disabled')
            replica.execute("INSERT INTO player_records_v03051 VALUES(1, 'eq_evolution_v10500:item_000', 2)")
            ck(not cutover_readiness(replica,catalog2)['data_consistent'],
                'a single ambiguous evolved duplicate still blocks')
        finally:
            replica.close()
        return n
    finally:
        c.close()

if __name__=='__main__':
    print('V106 EQ ZWYKLE KOPIE I HISTORIA:',run(),'PASS',flush=True)
