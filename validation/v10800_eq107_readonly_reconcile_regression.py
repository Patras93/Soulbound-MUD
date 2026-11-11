# -*- coding: utf-8 -*-
"""Test read-only v107 11-instance forensic gate using fake on-disk SQLite only."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hashlib import sha256
import sqlite3

from validation.v10700_production_eq_cutover_regression import DB, seed, CAT
from validation.v10800_eq107_readonly_reconcile import run, AuditBlocked
from systems.v10700_live_equipment import activate_production_ledger

checks = 0
with TemporaryDirectory(prefix='sb108_eq107_readonly_regression_') as temp:
    base = Path(temp)
    game = base / 'game'
    game.mkdir()
    database = game / 'soulbound.db'
    db = DB(database)
    seed(db)
    for account in range(3, 14):
        db.conn.execute('INSERT INTO accounts(id) VALUES(?)', (account,))
        db.conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)',
                        (account, 'helm', 1))
    db.conn.commit()
    with patch('systems.v10700_activation.production_approved', return_value=True):
        assert activate_production_ledger(db, CAT)
    backup_name = db.conn.execute('SELECT backup_name FROM v107_eq_production_cutover').fetchone()[0]
    backup = game / 'backups' / backup_name
    db.conn.close()
    # Simulated startup with missing PREDEPLOY, legacy inventory path modifies only inventory.
    with closing(sqlite3.connect(database)) as raw:
        for account in range(3, 14):
            raw.execute('UPDATE inventory SET quantity=2 WHERE account_id=? AND item_id=?',
                        (account, 'helm'))
        raw.commit()
    source_before = sha256(database.read_bytes()).hexdigest()
    backup_before = sha256(backup.read_bytes()).hexdigest()
    counts, ok = run(game, CAT, {'helm'})
    assert ok and counts['TEST_KOPII_PASS'] == 1
    assert counts['BRAKUJACE_KOPIE'] == 11 and counts['KOPIE_DODANE_TYLKO_DO_PROBY'] == 11
    checks += 1
    assert sha256(database.read_bytes()).hexdigest() == source_before
    assert sha256(backup.read_bytes()).hexdigest() == backup_before
    checks += 1
    with closing(sqlite3.connect(database)) as raw:
        assert raw.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0] == 13
        assert raw.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0] == 1
        raw.execute('UPDATE inventory SET quantity=3 WHERE account_id=3 AND item_id="helm"')
        raw.commit()
    counts, ok = run(game, CAT, {'helm'})
    assert not ok and counts['BRAKUJACE_KOPIE'] == 12
    checks += 1
    with closing(sqlite3.connect(database)) as raw:
        raw.execute('UPDATE inventory SET quantity=2 WHERE account_id=3 AND item_id="helm"')
        raw.execute("INSERT INTO player_records_v03051 VALUES (3,'eq_evolution_v10500:helm',1)")
        raw.commit()
    counts, ok = run(game, CAT, {'helm'})
    assert not ok and counts['NIEPEWNE_GRUPY'] == 1
    checks += 1
    backup.unlink()
    try:
        run(game, CAT, {'helm'})
    except AuditBlocked as exc:
        assert str(exc) == 'BRAK_BEZPIECZNEGO_BACKUPU_V107'
        checks += 1
    else:
        raise AssertionError('missing backup must reject rehearsal')

print(f'V108 EQ107 ANONIMOWA PROBA BEZ ZMIAN: {checks}/5 PASS', flush=True)
