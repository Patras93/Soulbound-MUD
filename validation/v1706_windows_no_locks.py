# -*- coding: utf-8 -*-
"""Runtime fake-server and static safeguards; no real Windows processes killed."""
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import json

ROOT = Path(__file__).resolve().parents[1]


def run_regression():
    checks=0
    for name in ('START_Soulbound.bat','STOP_Soulbound.bat',
                 'Start-Soulbound-Windows.bat','START_Soulbound_UKRYTY.vbs',
                 'uruchom_w_tle.py','windows_launcher_state.py'):
        assert (ROOT/name).is_file(), name
        checks+=1
    assert 'cwd=str(ROOT)' in (ROOT/'uruchom_w_tle.py').read_text(encoding='utf-8')
    checks+=1
    assert 'wait_gone(launcher_pid' in (ROOT/'stop_soulbound_windows.py').read_text(encoding='utf-8')
    checks+=1
    assert 'wait_gone(pid' in (ROOT/'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    checks+=1
    # Isolated launch exercising the original host and its process marker.
    with tempfile.TemporaryDirectory(prefix='soulbound1706-') as folder:
        base=Path(folder)
        shutil.copy2(ROOT/'host_windows.py',base/'host_windows.py')
        (base/'server.py').write_text('print("TEST LAUNCH",flush=True)\n',encoding='utf-8')
        proc = subprocess.run([sys.executable,str(base/'host_windows.py')], cwd=base,
             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=25)
        assert proc.returncode==0,proc.stderr
        checks+=1
        assert not (base/'logs'/'soulbound_launcher.json').exists()
        checks+=1
        assert 'TEST LAUNCH' in (base/'logs'/'serwer.log').read_text(encoding='utf-8')
        checks+=1
    # Normal and error exit must still work without an attached console.
    from validation.v1705_windows_clean_stop import run_regression as old_regression
    assert old_regression()==8
    checks+=1
    return checks

if __name__=='__main__':
    print(f'WINDOWS NO FOLDER LOCK v1.70.6: {run_regression()} checks PASS')
