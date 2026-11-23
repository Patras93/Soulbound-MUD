#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Current-release smoke audit; no historical dawny edytor editor tests.

This script runs inside the release runner's private workspace. It does NOT
replace any of the 60 PLUS stages, the universal 30-gate suite, real EQ clone,
or six-player TCP test. It fails immediately if a current gameplay contract
regresses. All source changes go through PREDEPLOY, not dawny edytor.
"""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CHECKS = (
    ("validation.v11400_soul_infinite_regression", "unittest"),
    ("validation.current_unbounded_progression_v114_regression", "module"),
    ("validation.current_soul_v113_pacing_v11403_regression", "module"),
    ("validation.current_soul_tier_lock_v11662_regression", "module"),
    ("validation.current_v11405_emergency_regression", "module"),
    ("validation.current_nopycache_v11406_regression", "module"),
    ("validation.v11400_xp_late_continuation_regression", "module"),
    ("validation.current_saved_content_compatibility_regression", "module"),
    ("validation.current_published_nonempty_startup_regression", "module"),
    ("validation.current_published_readonly_regression", "module"),
    ("validation.current_profession_unbounded_v114_regression", "module"),
    ("validation.current_tool_tier_after_800_regression", "module"),
    ("validation.current_v11325_bank_alias_regression", "module"),
    ("validation.current_v11329_sound_cap_regression", "module"),
    ("validation.current_v11333_mercenary_38_regression", "module"),
    ("validation.current_mercenary_arsenal_v11334_regression", "module"),
    ("validation.current_mercenary_tactics_v116_regression", "module"),
    ("validation.current_skill_exp_v11332_regression", "module"),
    ("validation.current_achievement_xp_v11331_regression", "module"),
)


def run():
    from validation.current_private_predeploy import isolated_predeploy_env
    import socket
    import tempfile
    if not (ROOT/'VERSION').is_file():
        raise AssertionError('Missing complete release identity')
    version=(ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()
    if tuple(int(n) for n in version.split('.')) < (113,0,0):
        raise AssertionError('Current-only gate cannot approve obsolete source')
    source=(ROOT/'player/session_mixins/admin_tools.py').read_text(encoding='utf-8')
    tree=ast.parse(source)
    admin=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='SessionAdminToolsMixin')
    methods={node.name for node in admin.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert {'admin_command','is_admin'} <= methods
    completed=0
    with tempfile.TemporaryDirectory(prefix='sbcurrent_fast_') as private:
        for module,mode in CHECKS:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0))
                port=sock.getsockname()[1]
            env=isolated_predeploy_env(dict(os.environ),private,port)
            env['SOULBOUND_V106_STAGING']='1'  # Historical Tier 6000 catalogue, not production
            command=[sys.executable,'-u','-m','unittest',module,'-q'] if mode=='unittest' else [sys.executable,'-u','-m',module]
            result=subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                  text=True, errors='replace', timeout=120, check=False)
            output=(result.stdout+'\n'+result.stderr).strip()
            if result.returncode:
                raise AssertionError(f'{module} FAIL: '+output[-2200:])
            completed+=1
            print(f'CURRENT {completed}/{len(CHECKS)} PASS {module} '+output[-150:],flush=True)
    assert completed==len(CHECKS)
    print(f'CURRENT FAST PREDEPLOY: {completed}/{len(CHECKS)} PASS',flush=True)
    return 0


if __name__=='__main__':
    try:result=run()
    except Exception as error:
        print('CURRENT FAST PREDEPLOY FAIL: '+type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        raise
    raise SystemExit(result)
