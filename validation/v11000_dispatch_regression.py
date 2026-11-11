# -*- coding: utf-8 -*-
"""V110: a deployment must execute the *approved candidate's* updater.

Offline unit test: never stops the real server or changes player databases.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import wdroz_po_predeploy as dispatcher


def run_regression():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb110_deploy_dispatch_') as tmp:
        home = Path(tmp)
        live = home/'Soulbound-MUD'; live.mkdir()
        archive = home/'Soulbound-MUD-v110.00.0-CANDIDATE.zip'
        archive.write_bytes(b'unit-test candidate; no real installer launched')
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        statefile = home/'last_result.json'
        state = dict(status='PASS', quality_gate='ULTIMATE-60-PLUS',
                     completed_stages=60, required_stages=60, returncode=0,
                     version='110.00.0', installed_at_test='109.00.0',
                     v110_release_gates_pass=True, sha256=digest, zip=str(archive))
        statefile.write_text(json.dumps(state), encoding='utf-8')
        launches=[]
        def capture(cmd, *, cwd, env):
            launches.append((cmd, cwd, env))
            return 0
        with (patch.object(dispatcher, 'ROOT', live),
              patch.object(dispatcher, 'STATE', statefile),
              patch.object(dispatcher, 'installed_version', return_value='109.00.0'),
              patch.object(dispatcher, 'inspect_zip', return_value=('110.00.0', {})),
              patch('builtins.input', return_value='WDRAZAM') as prompt,
              patch.object(dispatcher.subprocess, 'call', side_effect=capture)):
            assert dispatcher.main() == 0; checks += 1
            assert len(launches)==1 and prompt.call_count==1; checks += 1
            cmd, cwd, env = launches[0]
            candidate_updater = ROOT/'aktualizuj_soulbound.py'
            assert Path(cmd[2]).resolve() == candidate_updater.resolve(); checks += 1
            assert not (live/'aktualizuj_soulbound.py').exists(); checks += 1
            assert cwd == live and env.get('SOULBOUND_LIVE_ROOT') == str(live); checks += 1
            assert cmd[-2:] == [str(archive), '--yes']; checks += 1
            # Missing approval blocks the handoff before user confirmation.
            launches.clear()
            state['status']='FAIL'; statefile.write_text(json.dumps(state), encoding='utf-8')
            assert dispatcher.main()==1 and not launches; checks += 1
            state['status']='PASS'; statefile.write_text(json.dumps(state), encoding='utf-8')
        # No real ZIP, production root, service or database ever touched.
        assert archive.read_bytes().startswith(b'unit-test candidate'); checks += 1
    return checks


if __name__ == '__main__':
    print('V110 UNIVERSAL DISPATCH:', run_regression(), 'PASS', flush=True)
