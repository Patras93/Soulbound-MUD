# -*- coding: utf-8 -*-
"""Version-neutral regression gate for separately packaged feature modules.

A feature package systems/vNNN is not release-ready if its matching tests
cannot be found or executed. New feature versions need no new deploy BAT/SH.
"""
from __future__ import annotations
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / 'validation'


def run():
    feature_dirs = sorted(p for p in (ROOT/'systems').iterdir()
                          if p.is_dir() and (p/'__init__.py').is_file()
                          and re.fullmatch(r'v[0-9]+', p.name))
    completed = 0
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
               SOULBOUND_SOUND_EVENTS='0')
    for feature in feature_dirs:
        prefix=feature.name
        cases=sorted(VALIDATION.glob(f'test_{prefix}_*.py'))
        regressions=sorted(VALIDATION.glob(f'{prefix}_*regression.py'))
        if not cases or not regressions:
            raise AssertionError(f'{prefix}: feature tests or regressions missing')
        # Run the real unittest loader for all matching tests; a successful
        # import alone is not a PASS. No exclusions or skipped-case allowlist.
        command=[sys.executable,'-B','-m','unittest','discover',
                 '-s','validation','-p',f'test_{prefix}_*.py']
        process=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,
                               text=True,errors='replace',timeout=105)
        output=(process.stdout+'\n'+process.stderr)
        if process.returncode or 'OK' not in output or 'Ran ' not in output:
            raise AssertionError(f'{prefix} unit tests failed: '+output[-1300:])
        completed+=1
        print(f'CURRENT FEATURE {prefix}: {len(cases)} files, unittest PASS',flush=True)
        for path in regressions:
            process=subprocess.run([sys.executable,'-B','-m',f'validation.{path.stem}'],cwd=ROOT,
                                   env=env,capture_output=True,text=True,
                                   errors='replace',timeout=25)
            output=(process.stdout+'\n'+process.stderr)
            verified=('PASS' in output or ('Ran ' in output and '\nOK' in output))
            if process.returncode or not verified:
                raise AssertionError(f'{path.name} failed: '+output[-1300:])
            completed+=1
            print(f'CURRENT FEATURE {prefix}: {path.name} PASS',flush=True)
        print(f'CURRENT FEATURE {prefix}: {len(regressions)} independent regressions PASS',flush=True)
    print(f'CURRENT FEATURE RELEASE: {completed} test groups PASS',flush=True)
    return completed


if __name__ == '__main__':run()
