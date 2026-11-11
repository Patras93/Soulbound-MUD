# -*- coding: utf-8 -*-
"""Safety checks for live DB snapshot EQ rehearsal, using synthetic accounts."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10700_eq_ledger_live_clone import analyze_copy,audit_live_db

SCHEMA='''
CREATE TABLE accounts(id INTEGER PRIMARY KEY);
CREATE TABLE characters(account_id INTEGER);
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
INSERT INTO accounts VALUES(1),(2);
INSERT INTO characters VALUES(1),(2);
INSERT INTO inventory VALUES(1,'helm',1),(2,'helm',2);
INSERT INTO equipment VALUES(1,'head','helm'),(2,'head','helm');
INSERT INTO bank_items VALUES(2,'helm',3);
INSERT INTO profession_storage VALUES(2,'chest','helm',2);
INSERT INTO player_records_v03051 VALUES(2,'eq_evolution_v10500:helm',4);
'''


def run():
    ck=0
    def check(b,msg):
        nonlocal ck
        assert b,msg;ck+=1
    catalog={'helm':{'type':'armor'}}
    with tempfile.TemporaryDirectory(prefix='v107eqtest-') as directory:
        src=Path(directory)/'real.db'
        with closing(sqlite3.connect(src)) as db, db:db.executescript(SCHEMA)
        before=src.read_bytes()
        report=audit_live_db(src,catalog)
        check(report['bank_units']==3,'bank held gear missed')
        check(report['profession_storage_units']==2,'profession storage gear missed')
        check(report['legacy_ambiguous']>=1,'evolved duplicates not detected')
        check(report['blocking_count']>=6,'clone incorrectly marked ready')
        check(report['live_per_copy_enabled'] is False,'prohibited runtime approval')
        check(src.read_bytes()==before,'production SQLite file touched by clone')
        with closing(sqlite3.connect(src)) as db, db:
            db.execute('DELETE FROM bank_items')
            db.execute('DELETE FROM profession_storage')
            db.execute('DELETE FROM player_records_v03051')
            db.execute('UPDATE inventory SET quantity=1 WHERE account_id=2')
            db.commit()
        clean=audit_live_db(src,catalog)
        check(clean['bank_units']==0 and clean['profession_storage_units']==0,
              'bank or storage audit residue')
        check(clean['legacy_ambiguous']==0,'phantom evolution ambiguity')
        check(clean['live_per_copy_enabled'] is False,
              'zero issues erroneously enables live EQ')
    return ck

if __name__=='__main__':print('V107 KOPIA LIVE EQ:',run(),'PASS',flush=True)
