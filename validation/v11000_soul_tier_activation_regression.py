# -*- coding: utf-8 -*-
"""v110 retains v106 Soul Tiers 3001-6000 only in an authorized runtime.

Tests in child interpreters so module-level constants cannot be reused from
another legacy staging pass. Uses a disposable path, never a player DB.
"""
from __future__ import annotations
import os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_CODE = ('from core.progression_600 import SOUL_MAX_TIER, SOUL_TRIAL_QUEST_IDS; '
         'print(SOUL_MAX_TIER, len(SOUL_TRIAL_QUEST_IDS))')


def run_regression():
    with tempfile.TemporaryDirectory(prefix='sb110_soul_tier_') as scratch:
        test_db = str(Path(scratch) / 'isolated.sqlite')
        cases = (
            ('unapproved no flags', {}, 3000),
            ('test flag but unauthorized DB', {
                'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
                'SOULBOUND_V110_STAGING':'1','SOULBOUND_DB':str(ROOT/'soulbound.db')},3000),
            ('approved isolated v110', {
                'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
                'SOULBOUND_V110_STAGING':'1','SOULBOUND_DB':test_db},6000),
            ('wrong TCP port', {
                'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
                'SOULBOUND_V110_STAGING':'1','SOULBOUND_DB':test_db,
                'SOULBOUND_PORT':'4000'},3000),
            ('wrong TCP host', {
                'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
                'SOULBOUND_V110_STAGING':'1','SOULBOUND_DB':test_db,
                'SOULBOUND_HOST':'0.0.0.0'},3000),
            ('original v106 opt in', {'SOULBOUND_V106_STAGING':'1'},6000),
        )
        for label, additions, expected in cases:
            env = os.environ.copy()
            for key in ('SOULBOUND_V106_STAGING','SOULBOUND_V107_STAGING',
                        'SOULBOUND_V109_STAGING','SOULBOUND_V110_STAGING','SOULBOUND_DB',
                        'SOULBOUND_HOST','SOULBOUND_PORT'):
                env.pop(key,None)
            # The approved v110 sandbox always requires localhost and an
            # explicitly non-production port.  Earlier tests used flags only.
            env.update(SOULBOUND_HOST='127.0.0.1', SOULBOUND_PORT='45889')
            env.update(additions)
            result=subprocess.run([sys.executable,'-c',_CODE], cwd=ROOT,env=env,
                                  stdin=subprocess.DEVNULL, capture_output=True,
                                  text=True,encoding='utf-8',errors='replace',timeout=25)
            expected_line=f'{expected} {expected-1}'
            assert result.returncode == 0 and result.stdout.strip() == expected_line, (
                label, expected_line, result.stdout, result.stderr)
        assert not Path(test_db).exists(), 'no SQLite should be created during authorization check'
    return len(cases)

if __name__ == '__main__':
    print(f'V110 SOUL TIER SUCCESSOR ACTIVATION: {run_regression()}/6 PASS',flush=True)
