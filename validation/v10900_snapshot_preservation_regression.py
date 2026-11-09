# -*- coding: utf-8 -*-
"""Test v109 full data snapshot without using production data or a live server."""
from __future__ import annotations
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
from validation.v10900_snapshot_preservation import audit_snapshot, fingerprint, main


def run():
    checks = 0
    def ck(value, label):
        nonlocal checks
        assert value, label
        checks += 1
    with tempfile.TemporaryDirectory(prefix='Soulbound_PREDEPLOY_SQLITE_FROZEN_') as folder:
        src = Path(folder) / 'SOURCE_COMMITTED_SNAPSHOT.sqlite'
        with closing(sqlite3.connect(src)) as db:
            db.executescript('''
                CREATE TABLE accounts(id INTEGER PRIMARY KEY, name TEXT);
                CREATE TABLE characters(id INTEGER PRIMARY KEY, account_id INTEGER, exp INTEGER);
                CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver TEXT, gold INTEGER, mithril INTEGER);
                CREATE TABLE inventory(account_id INTEGER, item_id TEXT, quantity INTEGER);
                CREATE TABLE equipment(account_id INTEGER, slot TEXT, item_id TEXT);
                CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY, metadata BLOB);
                CREATE TABLE v106_equipped_instances(account_id INTEGER, slot TEXT, instance_id TEXT);
                CREATE TABLE v106_stored_instances(account_id INTEGER, instance_id TEXT);
                CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT);
                CREATE TABLE v109_trial_data(x BLOB, y TEXT, z REAL);
                INSERT INTO accounts VALUES(1,'ONE'),(2,'TWO');
                INSERT INTO characters VALUES(11,1,999999999999),(12,2,123);
                INSERT INTO account_wallet VALUES(1,'999999999999999999999999',55,3);
                INSERT INTO inventory VALUES(11,'soul_sword',2);
                INSERT INTO equipment VALUES(12,'weapon','staff');
                INSERT INTO v106_item_instances VALUES('instance-X',X'000102FF');
                INSERT INTO v106_equipped_instances VALUES(11,'weapon','instance-X');
                INSERT INTO v106_stored_instances VALUES(12,'instance-X');
                INSERT INTO v107_eq_production_cutover VALUES('107.00.0','rollback.sqlite');
                INSERT INTO v109_trial_data VALUES(X'00FF01',NULL,1.125);
            ''')
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA wal_autocheckpoint=0')
            db.execute('INSERT INTO inventory VALUES(12,?,?)',('gem',777))
            db.commit()
            original, counts = fingerprint(db)
            ck(counts['accounts']==2 and counts['characters']==2,'accounts & characters')
            ck(counts['v106_item_instances']==1,'physical eq rows')
            before = audit_snapshot(src)
            ck(before['sha256']==original,'full logical fingerprint including WAL')
            ck(before['tables']==len(counts) and before['instances']==1,'all tables restored')
            ck(before['accounts']==2 and before['characters']==2,'no loss of characters')
            with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB':str(src)}):
                ck(main()==0,'PREDEPLOY entry accepts only disposable snapshot')
            with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB':str(Path(folder)/'soulbound.db')}):
                ck(main()==3,'live-named database rejected')
            db.execute("PRAGMA query_only=OFF")
            db.execute("UPDATE account_wallet SET mithril=999 WHERE master_account_id=1")
            db.commit()
            changed, _ = fingerprint(db)
            ck(changed!=original,'changed wallet detected')
            db.execute("PRAGMA query_only=OFF")
            db.execute("DELETE FROM v106_item_instances")
            db.commit()
            again, _ = fingerprint(db)
            ck(again!=changed,'lost physical EQ detected')
            db.close()
        empty=Path(folder)/'EMPTY.sqlite'
        with closing(sqlite3.connect(empty)) as db:
            db.execute('CREATE TABLE accounts(id INTEGER)')
        try: audit_snapshot(empty)
        except RuntimeError:ck(True,'non-snapshot source refused')
        else:raise AssertionError('unsafe source passed')
        src.unlink()
        with closing(sqlite3.connect(src)) as db:
            db.execute('CREATE TABLE accounts(id INTEGER)')
        try:audit_snapshot(src)
        except RuntimeError:ck(True,'missing character/eq tables refused')
        else:raise AssertionError('incomplete copy passed')
    print('V109 DANE I KOPIA SQLITE:', checks, 'PASS; syntetyczny WAL, konta, postacie, pieniądze, EQ, BLOB')
    return checks

if __name__ == '__main__':
    run()
