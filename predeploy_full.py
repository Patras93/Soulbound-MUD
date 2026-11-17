#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Current gameplay audit, independent of the removed dawny edytor editor.

The 60 PLUS stages, the universal release suite, EQ backup compatibility,
and six-player TCP audit remain independently mandatory in the outer runner.
Historic dawny edytor test source is intentionally not loaded during this audit.
"""
from __future__ import annotations
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from validation.current_private_predeploy import isolated_predeploy_env

ROOT=Path(__file__).resolve().parent
# Different from the fast/current universal preflight: validate authored world,
# class/help catalogue, combat mechanics, SQLite, quests, and server bootstrap.
MODULES=(
    ('validation.v1110_unique_skill_names','run_regression'),
    ('validation.v1111_skill_help_dispatch','run_regression'),
    ('validation.v1112_teacher_quests','run_regression'),
    ('validation.v10205_readme_cleanup','run'),
    ('validation.v9604_release_tcp','run'),
)
SCRIPT_GATES=(
    'validation/current_universal_end_to_end_regression.py',
    'validation/current_crypt_overcap_party_regression.py',
    'validation/current_downed_channels_regression.py',
    'validation/current_jammer_auto_regression.py',
    'validation/current_jammer_cast_regression.py',
    'validation/current_party_follow_regression.py',
    'validation/current_unlimited_characters_regression.py',
    'validation/current_profession_unbounded_v114_regression.py',
    'validation/current_only_server_smoke.py',
)


def run():
    with tempfile.TemporaryDirectory(prefix='sbcurrent_fast_') as private:
        for module,func in MODULES:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0))
                port=sock.getsockname()[1]
            env=isolated_predeploy_env(dict(os.environ),private,port)
            code=('from '+module+' import '+func+' as f; result=f(); '
                  'print("PASS",result,flush=True)')
            process=subprocess.run([sys.executable,'-u','-c',code],cwd=ROOT,env=env,
                                   capture_output=True,text=True,errors='replace',timeout=180)
            output=(process.stdout+'\n'+process.stderr).strip()
            if process.returncode or 'PASS' not in output:
                raise AssertionError(module+' FAIL: '+output[-2800:])
            print('FULL WORLD PASS '+module+' '+output[-200:],flush=True)
        for file in SCRIPT_GATES:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0))
                port=sock.getsockname()[1]
            env=isolated_predeploy_env(dict(os.environ),private,port)
            process=subprocess.run([sys.executable,'-u',str(ROOT/file)],cwd=ROOT,env=env,
                                   capture_output=True,text=True,errors='replace',timeout=240)
            output=(process.stdout+'\n'+process.stderr).strip()
            if process.returncode:
                raise AssertionError(file+' FAIL: '+output[-2800:])
            print('FULL GAMEPLAY PASS '+file+' '+output[-200:],flush=True)
    print(f'CURRENT FULL AUDIT: {len(MODULES)+len(SCRIPT_GATES)} independent checks PASS',flush=True)
    return 0


if __name__=='__main__':
    try:result=run()
    except Exception as error:
        print('CURRENT FULL AUDIT FAIL: '+type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        raise
    raise SystemExit(result)
