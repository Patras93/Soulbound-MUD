# -*- coding: utf-8 -*-
"""Synthetic v113 and v114 activation without historical version modules."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import hashlib

ROOT=Path(__file__).resolve().parents[1]

RUN='''import json,sys
from pathlib import Path
from systems.universal_activation import activation_manifest,verify
root=Path.cwd()
source=Path(sys.argv[1])
version=sys.argv[2]
state=json.loads(Path(sys.argv[3]).read_text())
mapping={Path(p.relative_to(root)):None for p in root.rglob('*') if p.is_file() and p.name!='state.json'}
manifest=activation_manifest(state,source,root,mapping)
marker=root/'LIVE_CONTENT'/'release_current.json';marker.parent.mkdir(exist_ok=True)
marker.write_text(json.dumps(manifest))
assert verify(root)
(root/'server.py').write_text('tampered')
assert not verify(root)
print('ACTIVATION PASS '+version)
'''

def run():
    checks=0
    for version in ('113.00.0','114.02.7'):
        with tempfile.TemporaryDirectory(prefix='sb_activation_candidate_') as temp:
            root=Path(temp)
            for name in ('VERSION','server.py','core/bootstrap_economy_professions.py',
                         'core/release_version.py',
                         'systems/runtime_activation.py','systems/universal_activation.py',
                         'systems/universal_release_update.py','systems/current_fresh_install.py',
                         'aktualizuj_soulbound.py','predeploy_nowej_wersji.py',
                         'wdroz_po_predeploy.py','PREDEPLOY_NOWEJ_WERSJI.bat',
                         'WDROZ_PO_PREDEPLOY.bat','START_Soulbound.bat','STOP_Soulbound.bat'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                if name.endswith('.py') and (ROOT/name).is_file():
                    p.write_bytes((ROOT/name).read_bytes())
                else:p.write_text(version if name=='VERSION' else 'fixture')
            archive=Path(temp).parent/(root.name+'.zip')
            try:
                with zipfile.ZipFile(archive,'w') as z:z.writestr('proof.txt','release')
                digest=hashlib.sha256(archive.read_bytes()).hexdigest()
                state={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
                       'returncode':0,'completed_stages':60,'required_stages':60,
                       'version':version,'installed_at_test':'112.00.0',
                       'release_gates_pass':True,'sha256':digest}
                (root/'state.json').write_text(json.dumps(state))
                proc=subprocess.run([sys.executable,'-c',RUN,str(archive),version,str(root/'state.json')],
                                    cwd=root,env=dict(os.environ,PYTHONPATH=str(root),
                                                      PYTHONDONTWRITEBYTECODE='1'),
                                    capture_output=True,text=True,timeout=30)
                assert proc.returncode==0,proc.stdout+'\n'+proc.stderr
                checks+=1
                # Fake/old approval cannot sign a new version.
                state['release_gates_pass']=False
                (root/'state.json').write_text(json.dumps(state))
                bad=subprocess.run([sys.executable,'-c',RUN,str(archive),version,str(root/'state.json')],
                                   cwd=root,env=dict(os.environ,PYTHONPATH=str(root),
                                                     PYTHONDONTWRITEBYTECODE='1'),
                                   capture_output=True,text=True,timeout=30)
                assert bad.returncode != 0
                checks+=1
            finally:archive.unlink(missing_ok=True)
    print('VERSION-NEUTRAL ACTIVATION: '+str(checks)+'/4 PASS')

if __name__=='__main__':run()
