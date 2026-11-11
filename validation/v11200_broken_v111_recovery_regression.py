# -*- coding: utf-8 -*-
"""Adversarial tests: recover non-booting v111 without a historical v106 backup.

Run only in system TEMP. No live database or Windows service is accessed.
"""
from __future__ import annotations

import hashlib
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))

from aktualizuj_soulbound import (
    UpdateError, v112_base_preflight, require_v104_official_predeploy,
    v112_confirm_backup,
)
from systems import v10700_activation
from systems import v10700_live_equipment
from systems import v11200_activation


def creates_fixture(root: Path):
    root.mkdir(parents=True)
    (root/'core').mkdir()
    (root/'VERSION').write_text('111.00.0\n',encoding='utf-8')
    (root/'core/bootstrap_economy_professions.py').write_text(
        "VERSION = '111.00.0'\n",encoding='utf-8')
    with closing(sqlite3.connect(root/'soulbound.db')) as conn, conn:
        for table in ('equipment','inventory','v106_item_instances',
                      'v106_stored_instances','v106_equipped_instances'):
            conn.execute(f'CREATE TABLE {table} (account_id INTEGER)')
        conn.execute('''CREATE TABLE v107_eq_production_cutover
                        (cutover_version TEXT,backup_name TEXT,cutover_utc TEXT)''')
        conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?,?)',(
            '107.00.0','soulbound_v106_before_eq107_MISSING.sqlite',
            '2026-11-05T00:00:00+00:00'))
        conn.commit()


def must_block(action, reason):
    try:
        action()
    except UpdateError:
        return
    raise AssertionError('v112 should block: '+reason)


def main():
    checks=0
    with tempfile.TemporaryDirectory(prefix='sb112_recovery_') as folder:
        base=Path(folder)
        live=base/'game'
        creates_fixture(live)
        before=(live/'soulbound.db').read_bytes()
        # No v111 manifest, no historical snapshot: precisely the user's error.
        assert not (live/'LIVE_CONTENT/release_current.json').exists()
        assert v112_base_preflight(live)=='validated-ledger'
        checks+=1
        # The historical snapshot may be gone forever after a committed cutover.
        from systems.equipment_mail_v10600 import _schema
        assert callable(_schema)
        with closing(sqlite3.connect(live/'soulbound.db')) as conn, conn:
            instance=SimpleNamespace(conn=conn,path=str(live/'soulbound.db'))
            with patch.object(v10700_live_equipment,'_require_approved'), \
                 patch('systems.equipment_mail_v10600._schema'), \
                 patch.object(v10700_live_equipment,'install_on_migrated_connection') as barrier:
                assert v10700_live_equipment.activate_production_ledger(instance,{1:{'slot':'hands'}})
                assert instance._v107_eq_live_active
                barrier.assert_called_once()
        assert not list(live.glob('backups/*.sqlite'))
        checks+=1
        # v112 EQ production approval must not traverse v108/v110/v111 modules.
        (live/'VERSION').write_text('112.00.0\n')
        with patch.object(v10700_activation,'ROOT',live), \
             patch.object(v11200_activation,'production_approved',return_value=True), \
             patch.dict(sys.modules,{'systems.v10800_activation':None,
                                     'systems.v11000_activation':None,
                                     'systems.v11100_holiday_activation':None}):
            assert v10700_activation.production_approved()
        (live/'VERSION').write_text('111.00.0\n')
        checks+=1
        archive=base/'Soulbound-MUD-v112.00.0-RELEASE.zip'
        archive.write_bytes(b'isolated mock archive, never a live ZIP')
        state={
            'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
            'completed_stages':60,'required_stages':60,'returncode':0,
            'version':'112.00.0','installed_at_test':'111.00.0',
            'v112_release_gates_pass':True,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'zip':str(archive),
        }
        working=base/'Soulbound_PREDEPLOY'
        working.mkdir()
        result=working/'last_result.json'
        result.write_text(json.dumps(state),encoding='utf-8')
        # The exact candidate and explicit 60/60 approval is still mandatory.
        require_v104_official_predeploy(live,archive,'112.00.0')
        checks+=1
        for broken in (
            dict(state,completed_stages=59),
            dict(state,installed_at_test='110.00.0'),
            dict(state,v112_release_gates_pass=False),
            dict(state,sha256='0'*64),
        ):
            result.write_text(json.dumps(broken))
            must_block(lambda:require_v104_official_predeploy(live,archive,'112.00.0'),
                       'old/failed/unrelated PREDEPLOY')
            checks+=1
        result.write_text(json.dumps(state))
        # Any corrupted current ledger blocks the repair, regardless of PASS.
        with closing(sqlite3.connect(live/'soulbound.db')) as conn, conn:
            conn.execute('DELETE FROM v107_eq_production_cutover')
        must_block(lambda:v112_base_preflight(live),'no committed cutover')
        checks+=1
        with closing(sqlite3.connect(live/'soulbound.db')) as conn, conn:
            conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?,?)',
                         ('107.00.0','snapshot_not_present.sqlite','2026-11-05'))
            conn.execute('DROP TABLE v106_equipped_instances')
        must_block(lambda:v112_base_preflight(live),'missing physical EQ')
        checks+=1
        with closing(sqlite3.connect(live/'soulbound.db')) as conn, conn:
            conn.execute('CREATE TABLE v106_equipped_instances(account_id INTEGER)')
        assert v112_base_preflight(live)=='validated-ledger'
        checks+=1
        (live/'VERSION').write_text('110.00.0\n',encoding='utf-8')
        must_block(lambda:v112_base_preflight(live),'mismatched VERSION')
        checks+=1
        (live/'VERSION').write_text('111.00.0\n',encoding='utf-8')
        # Backup must be an exact byte-for-byte copy, including possible WAL.
        backup=base/'backup';backup.mkdir()
        (backup/'soulbound.db').write_bytes((live/'soulbound.db').read_bytes())
        v112_confirm_backup(live,backup)
        checks+=1
        (backup/'soulbound.db').write_bytes(b'corrupt')
        must_block(lambda:v112_confirm_backup(live,backup),'incomplete/changed rollback backup')
        checks+=1
        assert (live/'soulbound.db').read_bytes()!=b'corrupt'
        print('V112 RECOVERY PASS:',checks,
              'adversarial checks, absent old snapshot, signed 60/60 gate, ledger and backup')

if __name__=='__main__':main()
