"""Strictly synthetic: reproduce 11 physical EQ deficits, rehearse on detached copy.
No user DB, no server, no production modification, no deployment.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4
from contextlib import closing
import hashlib,sqlite3
from validation.v10700_production_eq_cutover_regression import DB,seed,CAT
from systems.v10700_live_equipment import activate_production_ledger,_check_all_accounts
from validation.v10800_v107_drift_details_ro import classify_snapshot

checks=0
with TemporaryDirectory(prefix='sb107_11_drift_rehearsal_') as tmp:
    root=Path(tmp); source=root/'synthetic.sqlite'; cloned=root/'repair_preview.sqlite'
    db=DB(source); seed(db)
    for aid in range(3,14):
        db.conn.execute('INSERT INTO accounts(id) VALUES(?)',(aid,))
        db.conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)',(aid,'helm',1))
    db.conn.commit()
    with patch('systems.v10700_activation.production_approved',return_value=True):
        assert activate_production_ledger(db,CAT)
    original_ids={r[0] for r in db.conn.execute('SELECT instance_id FROM v106_item_instances')}
    slots_before=[tuple(r) for r in db.conn.execute('SELECT * FROM v106_equipped_instances ORDER BY account_id,slot')]
    assert len(original_ids)==13
    checks+=1
    db.conn.close()
    restarted=DB(source)
    with patch('systems.v10700_activation.production_approved',return_value=False):
        for aid in range(3,14):
            restarted.add_item(aid,'helm',1)
    report=classify_snapshot(restarted.conn,CAT)
    assert report['deficit_groups']==11 and report['deficit_copies']==11
    assert report['worn_slot_mismatches']==0 and report['surplus_copies']==0
    checks+=1
    restarted.conn.close()
    original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    # SQLite binary image cloned by API, not copied from a live WAL file.
    with closing(sqlite3.connect(source)) as old, closing(sqlite3.connect(cloned)) as trial:
        old.backup(trial)
        assert trial.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        checks+=1
        row_count=trial.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]
        for aid in range(3,14):
            assert trial.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(aid,'helm')).fetchone()[0]==2
            assert trial.execute('SELECT COUNT(*) FROM v106_item_instances WHERE account_id=? AND item_id=?',(aid,'helm')).fetchone()[0]==1
            trial.execute('INSERT INTO v106_item_instances(instance_id,account_id,item_id,evolution_stage,origin) VALUES(?,?,?,0,?)',(
                str(uuid4()),aid,'helm','v107_gate_loss_rehearsal_only'))
        trial.commit()
        _check_all_accounts(trial,CAT)
        assert trial.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert trial.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==row_count+11
        assert {r[0] for r in trial.execute('SELECT instance_id FROM v106_item_instances')} >= original_ids
        assert list(trial.execute('SELECT * FROM v106_equipped_instances ORDER BY account_id,slot'))==slots_before
        after=classify_snapshot(trial,CAT)
        assert after['deficit_groups']==0 and after['deficit_copies']==0 and after['surplus_copies']==0
        checks+=1
    assert hashlib.sha256(source.read_bytes()).hexdigest()==original_sha
    checks+=1
print(f'SYNTHETIC LEGACY 11 COPIES: {checks}/5 PASS; original unchanged; cloned rehearsal consistent; real DB not tested')
