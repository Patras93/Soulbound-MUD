# -*- coding: utf-8 -*-
"""Regression: real installed-root launch and nonfatal bridge cleanup.

All files, ZIPs and state are synthetic and under TemporaryDirectory;
NEVER calls the user's server, registry, PREDEPLOY or SQLite.
"""
from __future__ import annotations
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    from systems.universal_release_update import restart_windows_without_console
    checks=0
    with TemporaryDirectory(prefix='sb_bridge_cleanup_regression_') as tmp:
        home=Path(tmp)
        installed=home/'Installed game'
        installed.mkdir()
        launcher=installed/'uruchom_w_tle.py'
        launcher.write_text('print("SYNTHETIC_INSTALLED_START")\n',encoding='utf-8')
        stage=home/'Temp stage'
        stage.mkdir()
        (stage/'uruchom_w_tle.py').write_text('raise AssertionError("BAD_TEMP_START")\n',encoding='utf-8')
        # The real subprocess runs the installed launcher, not the stage copy.
        from unittest.mock import Mock
        with patch('systems.universal_release_update.subprocess.run', return_value=Mock(returncode=0)) as proc:
            assert restart_windows_without_console(installed_root=installed)==0
            args,kwargs=proc.call_args
            assert args[0][-1]==str(launcher)
            assert kwargs['cwd']==str(installed)
            assert str(stage) not in str(args)
            assert 'cmd.exe' not in ' '.join(args[0]).lower()
            assert kwargs['env']['SOULBOUND_LIVE_ROOT']==str(installed)
            assert kwargs['stdin'] is not None
            checks+=7
        with patch('systems.universal_release_update.subprocess.run', return_value=Mock(returncode=7)):
            assert restart_windows_without_console(installed_root=installed)==7
            checks+=1
        launcher.unlink()
        with patch('systems.universal_release_update.subprocess.run') as proc:
            try:restart_windows_without_console(installed_root=installed)
            except RuntimeError:checks+=1
            else:raise AssertionError('Missing installed launcher was accepted')
            proc.assert_not_called()
            checks+=1
        # The permanent BAT must preserve the subprocess status even when
        # deleting temporary files is denied by Windows (WinError 32).
        import tempfile
        import subprocess
        import shutil
        from unittest.mock import Mock
        for filename in ('PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat'):
            bat=ROOT/filename
            if not bat.exists():continue  # Linux ZIP does not ship BAT
            source=bat.read_bytes().rsplit(b'### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###',1)[1]
            script=compile(source,str(bat),'exec')
            root=home/(filename+'-Installed')
            inbox=root/'NOWE_WERSJE';inbox.mkdir(parents=True)
            (root/'core').mkdir()
            (root/'core/bootstrap_economy_professions.py').write_text('VERSION = "113.00.22"\n',encoding='utf-8')
            z=inbox/'Soulbound-MUD-v113.00.24-TEST.zip'
            entries=['predeploy_nowej_wersji.py','wdroz_po_predeploy.py',
                     'aktualizuj_soulbound.py','VERSION',
                     'systems/runtime_activation.py','systems/universal_release_update.py',
                     'systems/current_fresh_install.py']
            with ZipFile(z,'w',ZIP_DEFLATED) as archive:
                for name in entries:
                    archive.writestr('Soulbound-MUD/'+name,
                                     '113.00.24\n' if name=='VERSION' else '# TEST\n')
            import hashlib
            state=root.parent/'Soulbound_PREDEPLOY'/'last_result.json'
            state.parent.mkdir(parents=True,exist_ok=True)
            state.write_text(json.dumps({'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
              'completed_stages':60,'required_stages':60,'returncode':0,
              'zip':str(z),'sha256':hashlib.sha256(z.read_bytes()).hexdigest()}),encoding='utf-8')
            action='deploy' if filename.startswith('WDROZ') else 'predeploy'
            stream=StringIO()
            def fake_remove(p):
                # Simulate Windows holding staged cwd; our fake is scoped
                # only to the bridge code's final cleanup.
                raise PermissionError(32,'Process cannot access file',str(p))
            with patch.object(sys,'argv',['<synthetic-bridge>',str(bat),str(root),action]), \
                 patch.object(subprocess,'call',return_value=0), \
                 patch.object(shutil,'rmtree',side_effect=fake_remove), \
                 redirect_stderr(stream),redirect_stdout(StringIO()):
                try:exec(script,{'__name__':'__main__'})
                except SystemExit as result:assert result.code==0, result.code
                else:raise AssertionError('bridge did not exit')
            assert 'tylko sprzatanie' in stream.getvalue()
            checks+=3
    return checks


if __name__=='__main__':
    n=run();print(f'BRIDGE ROOT / CLEANUP: {n}/{n} PASS',flush=True)
