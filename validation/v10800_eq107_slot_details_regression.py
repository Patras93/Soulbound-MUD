# -*- coding: utf-8 -*-
"""Synthetic, non-production test for anonymous v107 slot-mismatch diagnostics."""
from __future__ import annotations
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sqlite3

from validation.v10700_production_eq_cutover_regression import DB, seed, CAT
from systems.v10700_live_equipment import activate_production_ledger
from validation.v10800_eq107_readonly_reconcile import run, SlotAuditBlocked
from validation.v10800_eq107_slot_details_ro import summarize

checks = 0
with TemporaryDirectory(prefix='sb108_slot_ro_test_') as tmp:
    root = Path(tmp) / 'game'
    root.mkdir()
    path = root / 'soulbound.db'
    db = DB(path)
    seed(db)
    with patch('systems.v10700_activation.production_approved', return_value=True):
        assert activate_production_ledger(db, CAT)
    db.conn.close()
    with closing(sqlite3.connect(path)) as db:
        # baseline is consistent
        before = summarize(db, {'helm'})
        assert before['SLOTY_EQUIPMENT'] == 1 and before['SLOTY_CIENIA'] == 1
        assert before['EQUIPMENT_BEZ_CIENIA'] == before['CIEN_BEZ_EQUIPMENT'] == 0
        checks += 1
        # delete the old shadow row: the specific observed code must be returned.
        db.execute('DELETE FROM v106_equipped_instances WHERE account_id=1')
        db.commit()
    original = sha256(path.read_bytes()).hexdigest()
    backup_name = None
    with closing(sqlite3.connect(path)) as db:
        backup_name = db.execute('SELECT backup_name FROM v107_eq_production_cutover').fetchone()[0]
    backup_path = root / 'backups' / backup_name
    backup_hash = sha256(backup_path.read_bytes()).hexdigest()
    try:
        run(root, CAT, {'helm'})
        raise AssertionError('missing shadow was accepted')
    except SlotAuditBlocked as error:
        assert error.counts['EQUIPMENT_BEZ_CIENIA'] == 1
        assert error.counts['CIEN_BEZ_EQUIPMENT'] == 0
        assert error.counts['POROWNANIE_Z_BACKUPEM_DOSTEPNE'] == 1
        assert error.counts['SLOTY_ROZNE_SZABLONY'] == 0
        assert 'helm' not in str(error.counts) and 'head' not in str(error.counts)
        checks += 1
    assert original == sha256(path.read_bytes()).hexdigest()
    assert backup_hash == sha256(backup_path.read_bytes()).hexdigest()
    checks += 1
    with closing(sqlite3.connect(path)) as db:
        uid = db.execute('SELECT instance_id FROM v106_item_instances LIMIT 1').fetchone()[0]
        db.execute('DELETE FROM equipment WHERE account_id=1')
        db.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',(1,'head',uid))
        db.commit()
        d = summarize(db, {'helm'})
        assert d['CIEN_BEZ_EQUIPMENT'] == 1 and d['EQUIPMENT_BEZ_CIENIA'] == 0
        checks += 1
        db.execute('UPDATE equipment SET item_id=? WHERE 1=0',('material',))
        db.execute('INSERT INTO equipment VALUES(1,?,?)',('head','helm'))
        db.execute('UPDATE v106_item_instances SET account_id=2 WHERE instance_id=?',(uid,))
        db.commit()
        d = summarize(db, {'helm'})
        assert d['CIEN_INNY_WLASCICIEL'] == 1
        checks += 1
        db.execute('UPDATE v106_item_instances SET account_id=1 WHERE instance_id=?',(uid,))
        db.execute('INSERT INTO v106_stored_instances VALUES(?,?,?,?)',(uid,1,'bank',''))
        db.commit()
        d = summarize(db, {'helm'})
        assert d['CIEN_W_MAGAZYNIE'] == 1
        checks += 1
        db.execute('DELETE FROM v106_stored_instances')
        db.execute('DELETE FROM v106_item_instances WHERE instance_id=?',(uid,))
        db.commit()
        d = summarize(db, {'helm'})
        assert d['CIEN_BRAK_FIZYCZNEJ_KOPII'] == 1
        checks += 1
        # A deleted physical ID must never be reconstructed as part of diagnosis.
        assert db.execute('SELECT COUNT(*) FROM v106_item_instances WHERE instance_id=?',(uid,)).fetchone()[0] == 0
        checks += 1
print(f'V108 EQ107 SLOTY ANONIMOWY ODCZYT: {checks}/8 PASS', flush=True)
