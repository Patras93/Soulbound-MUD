# -*- coding: utf-8 -*-
"""Offline proof: permanent BAT bootstrap accepts future release-owned tools.

All data is synthetic in TemporaryDirectory; it never reads/writes the player's
server, SQLite, PREDEPLOY or GitHub.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
MARKER = '### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###'
NEEDS = ('predeploy_nowej_wersji.py', 'wdroz_po_predeploy.py',
         'aktualizuj_soulbound.py', 'VERSION', 'systems/runtime_activation.py',
         'systems/universal_release_update.py', 'systems/current_fresh_install.py')


def run():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb112_future_candidate_') as folder:
        temp=Path(folder)
        root=temp/'Installed'
        inbox=root/'NOWE_WERSJE'
        inbox.mkdir(parents=True)
        (root/'core').mkdir()
        (root/'core/bootstrap_economy_professions.py').write_text('VERSION = "112.00.0"\n',encoding='utf-8')
        file=inbox/'Soulbound-MUD-v113.00.0-SYNTHETIC-TEST.zip'
        entries={name: b'\n' for name in NEEDS}
        entries['VERSION']=b'113.00.0\n'
        entries['predeploy_nowej_wersji.py']=b'print("CANDIDATE_113_PREDEPLOY_ONLY")\n'
        entries['wdroz_po_predeploy.py']=b'print("CANDIDATE_113_DEPLOY_ONLY")\n'
        entries['aktualizuj_soulbound.py']=b'# FUTURE RELEASE OWNED\n'
        entries['systems/runtime_activation.py']=b'# V113 CURRENT\n'
        # The candidate does NOT contain the previous v112 release activator.
        assert not any('v11200_activation' in path for path in entries)
        checks+=1
        with ZipFile(file,'w',ZIP_DEFLATED) as zipout:
            for name,contents in entries.items():
                zipout.writestr('Soulbound-MUD/'+name,contents)
        with ZipFile(file) as archive:
            assert archive.testzip() is None
            checks+=1
        original_code=[]
        for bat in ('PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat'):
            body=(ROOT/bat).read_bytes().rsplit(MARKER.encode('ascii'),1)[1]
            compile(body,bat,'exec')
            original_code.append(body)
            checks+=1

        def bridge(code,action):
            args=[sys.executable,'-c',
                  'import sys;exec(compile(sys.stdin.buffer.read(),"bridge.py","exec"))',
                  str(ROOT/'PREDEPLOY_NOWEJ_WERSJI.bat'),str(root),action]
            # code is the embedded part of the BAT, with expected argv = script, root, action
            r=subprocess.run(args,input=code,capture_output=True,timeout=35,
                             env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            return r

        pre=bridge(original_code[0],'predeploy')
        assert pre.returncode==0,(pre.stdout,pre.stderr)
        assert b'CANDIDATE_113_PREDEPLOY_ONLY' in pre.stdout
        checks+=2
        approval=root.parent/'Soulbound_PREDEPLOY'/'last_result.json'
        approval.parent.mkdir()
        approval.write_text(json.dumps({
            'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
            'completed_stages':60,'required_stages':60,'returncode':0,
            'zip':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
        }),encoding='utf-8')
        deploy=bridge(original_code[1],'deploy')
        assert deploy.returncode==0,(deploy.stdout,deploy.stderr)
        assert b'CANDIDATE_113_DEPLOY_ONLY' in deploy.stdout
        checks+=2
        # Modified archive must fail before it can run candidate deploy script.
        file.write_bytes(file.read_bytes()+b'changed')
        reject=bridge(original_code[1],'deploy')
        assert reject.returncode!=0
        assert b'CANDIDATE_113_DEPLOY_ONLY' not in reject.stdout
        checks+=2
        # Important: intentionally no actual update, database or runtime execution.
    return checks

if __name__=='__main__':
    print(f'V112 FUTURE-CANDIDATE BRIDGE: {run()}/10 PASS')
