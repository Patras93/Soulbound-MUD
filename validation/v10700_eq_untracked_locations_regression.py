# -*- coding: utf-8 -*-
"""Regresja pomijanych lokalizacji fizycznego EQ: test tylko na sztucznym SQLite."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10700_eq_untracked_locations import audit_untracked
from validation.v10700_eq_ledger_live_clone import audit_live_db
from validation.v10700_eq_ledger_live_clone_regression import SCHEMA

CAT={'helm':{'type':'armor'},'sword':{'type':'weapon'}}

def run():
    count=0
    def ck(ok,msg):
        nonlocal count
        assert ok,msg
        count+=1
    with tempfile.TemporaryDirectory(prefix='v107-locations-') as directory:
        db_path=Path(directory)/'fake.db'
        with closing(sqlite3.connect(db_path)) as conn, conn:
            conn.executescript(SCHEMA)
            conn.execute('DELETE FROM bank_items')
            conn.execute('DELETE FROM profession_storage')
            conn.execute('DELETE FROM player_records_v03051')
            conn.execute('UPDATE inventory SET quantity=1 WHERE account_id=2')
            conn.executescript('''
                CREATE TABLE player_mail_v03051(id INTEGER PRIMARY KEY,
                    attachment_kind TEXT,attachment_item_id TEXT,
                    attachment_item_qty INTEGER,attachment_claimed INTEGER);
                CREATE TABLE player_housing_v03051(account_id INTEGER,storage_json TEXT);
                CREATE TABLE housing_rooms_v03052(account_id INTEGER,chest_json TEXT);
                CREATE TABLE equipment_reforges(account_id INTEGER,item_id TEXT,affix TEXT);
                CREATE TABLE equipment_runes_v0925(account_id INTEGER,item_id TEXT,rune TEXT);
            ''')
            ck(audit_untracked(conn,CAT)['pending_mail_gear_units']==0,'initial pending mail')
            conn.execute("INSERT INTO player_mail_v03051 VALUES(1,'item','helm',2,0)")
            ck(audit_untracked(conn,CAT)['pending_mail_gear_units']==2,'pending mail')
            conn.execute('UPDATE player_mail_v03051 SET attachment_claimed=1')
            ck(audit_untracked(conn,CAT)['pending_mail_gear_units']==0,'claimed mail ignored')
            conn.execute("INSERT INTO player_housing_v03051 VALUES(1,'{\"sword\":3}')")
            ck(audit_untracked(conn,CAT)['housing_gear_units']==3,'housing chest')
            conn.execute("INSERT INTO housing_rooms_v03052 VALUES(2,'{\"helm\":2}')")
            ck(audit_untracked(conn,CAT)['housing_gear_units']==5,'housing room')
            conn.execute("INSERT INTO equipment_reforges VALUES(2,'helm','fire')")
            ck(audit_untracked(conn,CAT)['ambiguous_modifiers']==0,'single-copy modifier allowed')
            conn.execute("UPDATE inventory SET quantity=2 WHERE account_id=2")
            ck(audit_untracked(conn,CAT)['ambiguous_modifiers']==1,'duplicated modified equipment')
            conn.execute("INSERT INTO equipment_runes_v0925 VALUES(1,'sword','power')")
            ck(audit_untracked(conn,CAT)['orphaned_modifier_rows']==1,'orphan modified equipment')
            conn.execute("INSERT INTO inventory VALUES(1,'deepq_fake_helm',3)")
            ck(audit_untracked(conn,CAT)['unresolved_dynamic_units']==3,'uncatalogued physical template')
            conn.execute("INSERT INTO player_housing_v03051 VALUES(2,'not json')")
            ck(audit_untracked(conn,CAT)['housing_json_errors']==1,'invalid housing json')
            conn.commit()
        before=db_path.read_bytes()
        report=audit_live_db(db_path,CAT)
        ck(report['pending_mail_gear_units']==0,'claimed mail not counted on clone')
        ck(report['housing_gear_units']==5,'housing gear in main report')
        ck(report['ambiguous_modifiers']==1,'modifier ambiguity in main report')
        ck(report['orphaned_modifier_rows']==1,'orphan modifier in main report')
        ck(report['unresolved_dynamic_units']==3,'dynamic IDs in main report')
        ck(report['housing_json_errors']==1,'broken JSON in main report')
        ck(report['blocking_count']>=11,'new blockers prevent success')
        ck(report['live_per_copy_enabled'] is False,'zero data blockers never approves release')
        ck(db_path.read_bytes()==before,'original file changed by clone')
    return count

if __name__=='__main__':
    print('V107 LOKALIZACJE EQ:',run(),'PASS',flush=True)
