# -*- coding: utf-8 -*-
"""Offline v106->v107 updater rehearsal with synthetic files and approval.

No real server or player database is used; STOP is mocked only within this
rehearsal. The production bridge keeps authenticated STOP and real backups.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import aktualizuj_soulbound as updater
from systems.v10700_activation import REQUIRED,MARKER,verify_root_for_test


def run():
    checks=0
    def check(v,reason):
        nonlocal checks
        assert v,reason
        checks+=1
    with tempfile.TemporaryDirectory(prefix='v107-test-install-only-') as directory:
        root=Path(directory);live=root/'Soulbound-MUD';(live/'core').mkdir(parents=True)
        (live/'core/bootstrap_economy_professions.py').write_text("VERSION='106.00.0'\n",encoding='utf-8')
        (live/'VERSION').write_text('106.00.0\n',encoding='utf-8')
        (live/'soulbound.db').write_bytes(b'FAKE_PLAYER_SQLITE_NEVER_TOUCH')
        before=(live/'soulbound.db').read_bytes()
        archive=root/'Soulbound-MUD-v107.00.0-OFFLINE-TEST.zip'
        entries=set(REQUIRED)|{
            'CHANGELOG_PL.txt','VERSION','START_Soulbound.bat','STOP_Soulbound.bat',
            'predeploy_check.py','aktualizuj_soulbound.py',
            'validation/v10700_release_readiness.py'}
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as out:
            for rel in sorted(entries):
                if rel == 'VERSION':
                    out.writestr(rel,'107.00.0\n')
                elif rel == 'core/bootstrap_economy_professions.py':
                    body=(ROOT/rel).read_text(encoding='utf-8-sig').replace(
                        'VERSION = "108.00.0"','VERSION = "107.00.0"')
                    out.writestr(rel,body)
                else:
                    out.write(ROOT/rel,rel)
        sha=hashlib.sha256(archive.read_bytes()).hexdigest()
        proof=root/'Soulbound_PREDEPLOY'/'last_result.json';proof.parent.mkdir()
        data=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',
                  completed_stages=60,required_stages=60,returncode=0,
                  version='107.00.0',installed_at_test='106.00.0',
                  zip=str(archive),sha256=sha)
        proof.write_text(json.dumps(data),encoding='utf-8')
        check(not (live/MARKER).exists(),'Marker exists before approved installer')
        with patch.object(updater,'stop_local_server',return_value=False):
            backup=updater.run_update(live,archive,'107.00.0',restart=False)
        check((live/MARKER).is_file(),'Approved updater did not create activation marker')
        check(verify_root_for_test(live),'Installed sources and approved ZIP do not match')
        check((live/'VERSION').read_text().strip()=='107.00.0','Version not installed')
        check((live/'soulbound.db').read_bytes()==before,'Legacy player data was overwritten')
        check((backup/'soulbound.db').read_bytes()==before,'Backup omitted private data')
        check((backup/'VERSION').read_text().strip()=='106.00.0','Backup has wrong code version')
        data['completed_stages']=59
        proof.write_text(json.dumps(data),encoding='utf-8')
        check(not verify_root_for_test(live),'Stale 59/60 approval accepted after deployment')
    return checks

if __name__=='__main__':print('V107 TEST INSTALATORA I AKTYWACJI:',run(),'PASS',flush=True)
