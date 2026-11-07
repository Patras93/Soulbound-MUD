# -*- coding: utf-8 -*-
"""Synthetic read-only EQ-v107 diagnostics and conservative release refusal."""
from __future__ import annotations
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch
import hashlib
import os
import sqlite3
import sys

from validation.v10800_v107_drift_details_ro import classify_snapshot, safe_summary
from validation.v10800_v107_equipment_compat_gate import audit_read_only, main

CAT={'helm': {'type': 'armor'}, 'ore': {'type':'material'}}
SCHEMA = '''
CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT);
INSERT INTO v107_eq_production_cutover VALUES('107.00.0','v107_before.sqlite');
CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
    PRIMARY KEY(account_id,item_id));
CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
    PRIMARY KEY(account_id,slot));
CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY,account_id INTEGER,
    item_id TEXT,evolution_stage INTEGER,origin TEXT);
CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,instance_id TEXT);
CREATE TABLE v106_stored_instances(instance_id TEXT,account_id INTEGER,
    storage_kind TEXT,container TEXT);
INSERT INTO inventory VALUES (1,'helm',2),(1,'ore',400);
INSERT INTO equipment VALUES (1,'head','helm');
INSERT INTO v106_item_instances VALUES ('h1',1,'helm',4,'historical'),('h2',1,'helm',0,'drop');
INSERT INTO v106_equipped_instances VALUES (1,'head','h1');
'''

def run():
    checks=0
    def check(ok,msg):
        nonlocal checks
        assert ok,msg
        checks+=1
    with TemporaryDirectory(prefix='sb108-v107-ro-ledger-') as home:
        path=Path(home)/'private_snapshot.sqlite'
        with closing(sqlite3.connect(path)) as c:
            c.executescript(SCHEMA)
            c.commit()
        original_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c:
            c.execute('PRAGMA query_only=ON')
            baseline=classify_snapshot(c,CAT)
        check(baseline['deficit_groups']==0 and baseline['deficit_copies']==0,
              'sprawny stary EQ nie powinien miec niedoboru')
        check(baseline['worn_slot_mismatches']==0,'sprawne sloty odrzucono')
        check(baseline['physical_instances']==2,'ilosc kopii nie zgadza sie')
        check(baseline['unrecognized_physical_templates']==0,'zly katalog')
        check(hashlib.sha256(path.read_bytes()).hexdigest()==original_hash,
              'diag zmienila SQLite mimo query_only')
        stub=ModuleType('world.dynamic_content');stub.ITEMS=CAT
        with patch.dict(sys.modules,{'world.dynamic_content':stub}):
            check(audit_read_only(path)==2,'prawidlowy v107 nie przeszedl bramki')
            with closing(sqlite3.connect(path)) as c:
                c.execute("UPDATE inventory SET quantity=3 WHERE item_id='helm'")
                c.commit()
            proof=hashlib.sha256(path.read_bytes()).hexdigest()
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c:
                c.execute('PRAGMA query_only=ON')
                deficit=classify_snapshot(c,CAT)
            check(deficit['deficit_groups']==1 and deficit['deficit_copies']==1,
                  'brak kopii nie wykryty')
            check(deficit['worn_slot_mismatches']==0,'brak kopii nie powinien psuc slotu')
            check(deficit['deficit_groups_with_evolved_copies']==1,
                  'historia ulepszen musi zostac oznaczona jako ryzyko')
            check('h1' not in safe_summary(deficit) and 'helm' not in safe_summary(deficit),
                  'raport ujawnia prywatne identyfikatory')
            check(hashlib.sha256(path.read_bytes()).hexdigest()==proof,
                  'diag zmienila źrodlowa SQLite')
            try:audit_read_only(path)
            except RuntimeError:checks+=1
            else:raise AssertionError('niezgodne EQ mialo PASS')
            env={'SOULBOUND_ULTRA_SOURCE_DB':str(path)}
            output=StringIO()
            with patch.dict(os.environ,env),redirect_stdout(output):
                code=main()
            check(code==3,'diagnostyka powinna blokowac wydanie')
            report=output.getvalue()
            check('deficit_groups=1' in report and 'deficit_copies=1' in report,
                  'diag bramki nie podaje wynikow')
            check('NIE WDRAZAJ' in report,'mimo niedoboru brakuje blokady')
            check('helm' not in report and 'h1' not in report,
                  'diag bramki ujawnia dane jednostkowe')
            check(hashlib.sha256(path.read_bytes()).hexdigest()==proof,
                  'uruchomienie bramki zmienilo zrodlo')
        with closing(sqlite3.connect(path)) as c:
            c.execute('UPDATE inventory SET quantity=1 WHERE item_id="helm"')
            c.execute('DELETE FROM v106_equipped_instances')
            c.commit()
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c:
            c.execute('PRAGMA query_only=ON')
            mismatch=classify_snapshot(c,CAT)
        check(mismatch['surplus_groups']==1 and mismatch['surplus_copies']==1,
              'nadwyzka fizycznych kopii nie wykryta')
        check(mismatch['worn_slot_mismatches']==1,'brak powiazania zalozonego EQ')
        with closing(sqlite3.connect(path)) as c:
            c.execute("INSERT INTO v106_item_instances VALUES ('obsolete',1,'old_no_catalog',0,'history')")
            c.commit()
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as c:
            unknown=classify_snapshot(c,CAT)
        check(unknown['unrecognized_physical_templates']==1,
              'historyczne nieznane ID trzeba odnotowac bez zgadywania typu')
    return checks

if __name__=='__main__':
    print('V108 STARE EQ V107: DIAGNOSTYKA BEZ ZAPISOW:',run(),'PASS; NIE WDRAZAC',flush=True)
