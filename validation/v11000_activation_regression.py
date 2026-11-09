# -*- coding: utf-8 -*-
"""Independent v110 activation evidence without any older installer files."""
from __future__ import annotations
import json, shutil, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.v11000_activation import CORE, MARKER, activation_manifest, verify, sha

def main():
    with tempfile.TemporaryDirectory(prefix='sb110_activation_') as folder:
        home=Path(folder); staged=home/'Soulbound-MUD'; staged.mkdir()
        for name in CORE:
            dest=staged/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        source=home/'approved.zip';source.write_bytes(b'private test-only release marker')
        state=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',version='110.00.0',
                   returncode=0,completed_stages=60,required_stages=60,
                   v110_release_gates_pass=True,sha256=sha(source))
        assert not verify(staged)
        marker=activation_manifest(state,source,staged,CORE)
        assert set(marker['files'])==set(CORE)
        dest=staged/MARKER;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(marker),encoding='utf-8')
        assert verify(staged),'Valid authenticated v110 manifest rejected'
        assert not any((staged/name).exists() for name in (
            'wdroz_v107_z_zewnatrz.py','wdroz_v108_z_zewnatrz.py',
            'wdroz_v109_z_zewnatrz.py'))
        critical=staged/'server.py';original=critical.read_bytes()
        try:
            critical.write_bytes(original+b'\n# unauthorized\n')
            assert not verify(staged),'Mutation did not revoke production approval'
        finally:critical.write_bytes(original)
        assert verify(staged)
        for key in ('sha256','v110_release_gates_pass','status'):
            bad=state.copy();bad[key]='0'*64 if key=='sha256' else False if key.endswith('pass') else 'FAIL'
            try:activation_manifest(bad,source,staged,CORE)
            except ValueError as exc:
                assert "v110" in str(exc),str(exc)
            else:raise AssertionError('False v110 approval accepted: '+key)
        print('V110 ACTIVATION: 8/8 PASS; independent current marker; stale installer not required',flush=True)

if __name__=='__main__':main()
