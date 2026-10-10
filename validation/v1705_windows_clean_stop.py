# -*- coding: utf-8 -*-
"""Verify Windows host returns 0 for graceful stop and non-zero for failures.

Uses disposable fake server processes, never starts the real MUD or opens port 4000.
"""
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run_regression():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='soulbound-stop-check-') as folder:
        root = Path(folder)
        shutil.copy2(ROOT / 'host_windows.py', root / 'host_windows.py')
        for code in (0, 7):
            (root / 'server.py').write_text(f'import sys\nprint("FAKE SERVER: exit {code}", flush=True)\nsys.exit({code})\n', encoding='utf-8')
            outcome = subprocess.run(
                [sys.executable, '-u', str(root / 'host_windows.py')],
                cwd=root,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=20,
            )
            assert outcome.returncode == code, f'exit {code} became {outcome.returncode}: {outcome.stderr}'
            checks += 1
            log = (root / 'logs' / 'serwer.log').read_text(encoding='utf-8')
            assert f'STOP | Kod zakonczenia serwera: {code}' in log
            checks += 1
            errors = (root / 'logs' / 'bledy.log').read_text(encoding='utf-8')
            assert 'BLAD LAUNCHERA' not in errors and 'SystemExit: 0' not in errors
            checks += 1
            if code:
                assert f'STOP | Kod zakonczenia serwera: {code}' in errors
                checks += 1
            else:
                assert not errors.strip(), errors
                checks += 1
    return checks

if __name__ == '__main__':
    print(f'WINDOWS CLEAN STOP v1.70.5: {run_regression()} checks PASS')
