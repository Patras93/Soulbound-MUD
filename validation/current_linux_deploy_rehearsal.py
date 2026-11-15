# -*- coding: utf-8 -*-
"""Full Linux first-install with a *synthetic* approval and synthetic SQLite.

Does not grant real release permission; PREDEPLOY's 60 gates run separately.
"""
from __future__ import annotations
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import linux_release as L
from systems.universal_release_update import verify_stage


def main():
    archive=os.environ.get('SOULBOUND_LINUX_ARCHIVE','')
    if not archive:raise RuntimeError('Missing real candidate ZIP for Linux rehearsal')
    checks=0
    with tempfile.TemporaryDirectory(prefix='sb_current_linux_deploy_') as td:
        root=Path(td);db=root/'sample-windows-export.sqlite'
        with sqlite3.connect(db) as c:
            c.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY, login TEXT)')
            c.execute('CREATE TABLE characters(id INTEGER PRIMARY KEY,account_id INTEGER,eq BLOB)')
            c.execute('INSERT INTO accounts VALUES(1,?)',('synthetic-owner',))
            c.execute('INSERT INTO characters VALUES(1,1,?)',(b'\x00\xff\x12\x00',))
            c.commit()
        checks+=1
        approve=root/'synthetic-approval.json'
        state={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS','platform':'linux',
               'required_stages':60,'completed_stages':60,'returncode':0,
               'release_gates_pass':True,'linux_contract_pass':True,
               'version':L.VERSION,'installed_at_test':'LINUX_FIRST_OR_UPGRADE',
               'zip':str(Path(archive).resolve()),'sha256':L.digest(archive),
               'db_fingerprint':L.fingerprint_source(db),
               'SYNTHETIC_NOT_FOR_DEPLOYMENT':True}
        log=root/'synthetic-PREDEPLOY.log'
        log.write_text('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
            'SOULBOUND RELEASE GATES PASS\nPLUS CHECKS PASS\n'
            'UNIVERSAL RELEASE SAFETY: 20/20 PASS\nTCP 6 GRACZY: PASS\n'
            'PASS - FIZYCZNE EQ NA KOPII BAZY (kod 0)\n'
            'LINUX CONTRACT EXIT validation/current_linux_release_regression.py 0\n'
            'LINUX CONTRACT EXIT validation/current_linux_deploy_rehearsal.py 0\n',
            encoding='utf-8')
        state.update(log=str(log),log_sha256=L.digest(log))
        L.save_json(approve,state);checks+=1
        result=L.deploy(archive,db,approve,root/'workspace',no_start=True);checks+=1
        assert verify_stage(result);checks+=1
        assert (root/'workspace/current').is_symlink();checks+=1
        assert result.name=='v'+L.VERSION;checks+=1
        assert (result/'START_Soulbound.sh').stat().st_mode & 0o100;checks+=1
        assert L.fingerprint_source(result/'soulbound.db')==L.fingerprint_source(db);checks+=1
        assert list((root/'workspace/backups').glob('*.sqlite'));checks+=1
        with sqlite3.connect(result/'soulbound.db') as c:
            assert c.execute('SELECT eq FROM characters').fetchone()[0]==b'\x00\xff\x12\x00';checks+=1
        # Running the same release again may never overwrite the target.
        try:L.deploy(archive,db,approve,root/'workspace',no_start=True)
        except L.LinuxReleaseError:checks+=1
        else:raise AssertionError('Overwrote active version')
        with sqlite3.connect(db) as c:
            c.execute('INSERT INTO characters VALUES(2,1,?)',(b'delta',));c.commit()
        try:L.validate_approval(Path(archive),db,approve)
        except L.LinuxReleaseError:checks+=1
        else:raise AssertionError('Changed player data passed stale PREDEPLOY')
        assert L.fingerprint_source(result/'soulbound.db')==state['db_fingerprint'];checks+=1
        assert verify_stage(result);checks+=1
        log.write_text(log.read_text()+'tampered\n')
        try:L.validate_approval(Path(archive),result/'soulbound.db',approve)
        except L.LinuxReleaseError:checks+=1
        else:raise AssertionError('Tampered PREDEPLOY log accepted')
    print('LINUX FIRST INSTALL REAL PROCESS: '+str(checks)+'/'+str(checks)+' PASS '
          '(SYNTHETIC DATA AND APPROVAL; NOT a production PREDEPLOY)',flush=True)


if __name__=='__main__':main()
