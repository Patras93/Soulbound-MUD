# -*- coding: utf-8 -*-
"""Test real backup rehearsal interface on a disposable synthetic SQLite source."""
from contextlib import closing
from pathlib import Path
import sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10700_eq_routes_on_real_backup import audit_readonly

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
CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value TEXT,
 PRIMARY KEY(account_id,record_key));
CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
 paid_silver INTEGER,quantity INTEGER,
 PRIMARY KEY(account_id,item_id,paid_silver));
INSERT INTO accounts VALUES(1),(2);
INSERT INTO characters VALUES(1),(2);
INSERT INTO inventory VALUES(1,'helmet_old',1),(1,'ore',3);
INSERT INTO equipment VALUES(1,'head','helmet_old');
'''

def run():
    with tempfile.TemporaryDirectory(prefix='v107-real-backup-qa-') as directory:
        path=Path(directory)/'live_simulation.sqlite'
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.executescript(SCHEMA)
        before=path.read_bytes()
        catalog={'helmet_old':{'type':'armor','name':'Stary hełm'},
                 'helmet_new':{'type':'armor','name':'Nowy hełm'},
                 'ore':{'type':'material','name':'Ruda'}}
        import os
        previous=os.environ.get('SOULBOUND_V106_STAGING')
        os.environ['SOULBOUND_V106_STAGING']='1'
        try:checked=audit_readonly(path,catalog)
        finally:
            if previous is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
            else:os.environ['SOULBOUND_V106_STAGING']=previous
        assert checked==21, 'Nie zaliczono kompletu testów wymiany EQ'
        assert path.read_bytes()==before, 'AUDYT ZMIENIŁ PLIK ŹRÓDŁOWEJ BAZY'
        with closing(sqlite3.connect(path)) as conn:
            assert conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]==2
            assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        return 3

if __name__=='__main__':print('V107 PRAWDZIWA KOPIA EQ – REHEARSAL:',run(),'PASS')
