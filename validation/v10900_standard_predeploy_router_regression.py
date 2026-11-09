# -*- coding: utf-8 -*-
"""Zwykly PREDEPLOY_NOWEJ_WERSJI.bat: router v108->v109 bez zmiany chronionych plikow."""
from __future__ import annotations
from pathlib import Path
from contextlib import redirect_stderr,redirect_stdout
from io import StringIO
import tempfile
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

import predeploy_v109_standard_router as router


def run():
    count = 0
    def check(value, msg):
        nonlocal count
        assert value, msg
        count += 1

    with tempfile.TemporaryDirectory(prefix='v109_router_regression_') as t:
        base = Path(t)
        live = base/'Soulbound-MUD'
        inbox = live/'NOWE_WERSJE'
        inbox.mkdir(parents=True)
        (live/'VERSION').write_text('108.00.0\n', encoding='utf-8')
        protected = live/'predeploy_nowej_wersji.py'
        protected.write_bytes(b'# v108 pinned by manifest\n')
        old = protected.read_bytes()
        candidate = inbox/'Soulbound-MUD-v109.00.0-READY.zip'
        members = {
            'VERSION': '109.00.0\n',
            'predeploy_v109_z_zewnatrz.py': 'print("candidate only")\n',
            'predeploy_nowej_wersji.py': 'print("candidate only")\n',
            'systems/v10900_activation.py': 'REQUIRED=()\n',
        }
        with ZipFile(candidate,'w', ZIP_DEFLATED) as zipped:
            for rel, content in members.items():
                zipped.writestr('Soulbound-MUD/'+rel, content)
        check(router._candidate(live,None)==candidate,'one candidate found')
        check(router._candidate(live,str(candidate))==candidate,'explicit candidate found')
        with tempfile.TemporaryDirectory(prefix='v109_router_extract_') as u:
            stage=router._stage_archive(candidate,Path(u))
            check((stage/'VERSION').read_text()=='109.00.0\n','candidate extracted')
            check((stage/'systems/v10900_activation.py').is_file(),'subfolder staged')
        def fake_call(argv, **kwargs):
            check(Path(argv[2]).is_file(),'bridge exists while runner called')
            check(argv[3:] == ['--instalacja',str(live),'--zip',str(candidate)],
                  'external bridge sees exact live and ZIP')
            check(Path(kwargs['cwd']) != live,'bridge runs outside live')
            return 0
        with patch.object(router,'ROOT',live), patch.object(router.subprocess,'call',side_effect=fake_call) as run_call:
            check(router.main([])==0,'standard BAT routes to v109')
            check(run_call.call_count==1,'bridge called once')
        check(protected.read_bytes()==old,'v108 authenticated tool untouched')
        check(not (live/'systems/v10900_activation.py').exists(),'no v109 code copied into live')
        dup=inbox/'Soulbound-MUD-v109.00.0-DUPLICATE.zip'
        dup.write_bytes(candidate.read_bytes())
        try:router._candidate(live,None)
        except ValueError:check(True,'duplicate version refused')
        else:raise AssertionError('duplicate should be blocked')
        dup.unlink()
        malicious = base/'malicious.zip'
        with ZipFile(malicious,'w', ZIP_DEFLATED) as zipped:
            for rel,content in members.items():
                zipped.writestr('Soulbound-MUD/'+rel,content)
            zipped.writestr('Soulbound-MUD/../../escape.txt','malicious')
        with tempfile.TemporaryDirectory() as u:
            try: router._stage_archive(malicious,Path(u))
            except ValueError:check(True,'ZIP traversal refused')
            else:raise AssertionError('zip traversal accepted')
            check(not (Path(u)/'escape.txt').exists(),'no traversal file written')
        with ZipFile(malicious,'w', ZIP_DEFLATED) as zipped:
            for rel,content in members.items():
                zipped.writestr('Soulbound-MUD/'+rel,content)
            zipped.writestr('Soulbound-MUD/player.sqlite','not a real db')
        with tempfile.TemporaryDirectory() as u:
            try: router._stage_archive(malicious,Path(u))
            except ValueError:check(True,'candidate with DB refused')
            else:raise AssertionError('database archive accepted')
        bad=inbox/'Soulbound-MUD-v109.00.0-BAD.zip'
        bad.write_bytes(b'bad archive')
        candidate.unlink()
        with patch.object(router,'ROOT',live), redirect_stderr(StringIO()), redirect_stdout(StringIO()):
            check(router.main([])==3,'corrupted ZIP refused')
        check(protected.read_bytes()==old,'corrupted ZIP left v108 unchanged')
        bad.unlink()
        older=inbox/'Soulbound-MUD-v108.00.0-CANDIDATE.zip'
        older.write_bytes(b'legacy runner will inspect it')
        with patch.object(router,'ROOT',live), patch.object(router.subprocess,'call',return_value=0) as run_call:
            check(router.main([])==0,'previous-version PREDEPLOY still delegated')
            check(run_call.call_args.args[0][2] == str(protected),'old runner unchanged')
        check(protected.read_bytes()==old,'old source is still intact')
    print('V109 STANDARD PREDEPLOY ROUTER:',count,'kontroli PASS; tylko syntetyczne')
    return 0


if __name__=='__main__':
    raise SystemExit(run())
