# -*- coding: utf-8 -*-
"""v108: user's cancellation of new EQ 2.0 is a permanent release contract."""
from __future__ import annotations
from pathlib import Path
from contextlib import closing
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch
import hashlib
import sqlite3
import sys

from validation.v10800_v107_equipment_compat_gate import audit_read_only

ROOT=Path(__file__).resolve().parents[1]


def run():
    checked=0
    def ck(yes,msg):
        nonlocal checked
        assert yes,msg
        checked+=1
    server=(ROOT/'server/mud_server.py').read_text('utf-8')
    ck('activate_v108_production_ledger' not in server,'v108 EQ2 activation revived')
    ck('activate_production_ledger' in server,'v107 equipment protection removed')
    ck(not (ROOT/'systems/v10800_live_equipment.py').exists(),'v108 EQ2 migration module shipped')
    ck(not (ROOT/'UZGODNIJ_EQ_V108.bat').exists(),'v108 EQ2 auto-repair shipped')
    ck(not (ROOT/'validation/v10800_windows_eq_release_gate.py').exists(),
       'old v108 EQ2 migration required again')
    with TemporaryDirectory(prefix='sb108_no_eq2_contract_') as folder:
        source=Path(folder)/'private_snapshot.sqlite'
        with closing(sqlite3.connect(source)) as db:
            db.executescript('''
                CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT);
                INSERT INTO v107_eq_production_cutover VALUES('107.00.0','old_backup.sqlite');
                CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY,account_id INTEGER,
                    item_id TEXT,evolution_stage INTEGER,origin TEXT);
                CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,instance_id TEXT);
                CREATE TABLE v106_stored_instances(instance_id TEXT,account_id INTEGER,
                    storage_kind TEXT,container TEXT);
                CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER);
                CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT);
                INSERT INTO inventory VALUES(1,'helm',1);
                INSERT INTO equipment VALUES(1,'head','helm');
                INSERT INTO v106_item_instances VALUES('original',1,'helm',3,'v107');
                INSERT INTO v106_equipped_instances VALUES(1,'head','original');
            ''')
        stub=ModuleType('world.dynamic_content')
        stub.ITEMS={'helm':{'type':'armor'}}
        with patch.dict(sys.modules,{'world.dynamic_content':stub}):
            original=hashlib.sha256(source.read_bytes()).digest()
            ck(audit_read_only(source)==1,'existing v107 physical copy rejected')
            ck(hashlib.sha256(source.read_bytes()).digest()==original,'readonly check modified snapshot')
            with closing(sqlite3.connect(source)) as db:
                db.execute("UPDATE inventory SET quantity=2 WHERE item_id='helm'");db.commit()
            try:audit_read_only(source)
            except RuntimeError:checked+=1
            else:raise AssertionError('preexisting v107 drift silently approved')
            with closing(sqlite3.connect(source)) as db:
                db.execute('CREATE TABLE v108_eq_production_cutover(version TEXT)');db.commit()
            try:audit_read_only(source)
            except RuntimeError:checked+=1
            else:raise AssertionError('cancelled v108 EQ2 cutover allowed')
    return checked

if __name__=='__main__':
    print('V108 BEZ EQ2, ZACHOWANE V107:',run(),'KONTROLI PASS',flush=True)
