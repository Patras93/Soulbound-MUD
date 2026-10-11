# -*- coding: utf-8 -*-
"""Fast standalone quality gate for exhaustive v2.30.2 coverage instrumentation."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from validation import v2302_exhaustive_game_coverage as coverage
import testuj_soulbound_windows as gate


def run_contract():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='soulbound-coverage-') as directory:
        env = gate.stage_env(directory)
        save_db = os.environ.get('SOULBOUND_DB')
        save_host = os.environ.get('SOULBOUND_HOST')
        try:
            os.environ.update(SOULBOUND_DB=env['SOULBOUND_DB'], SOULBOUND_HOST='127.0.0.1')
            assert coverage.check_sandbox_environment().name == 'audit.sqlite'; checks += 1
            for val in ('/root/production/players.sqlite', 'players.sqlite', ''):
                os.environ['SOULBOUND_DB'] = val
                try:
                    coverage.check_sandbox_environment()
                except RuntimeError:
                    checks += 1
                else:
                    raise AssertionError('Niebezpieczny DB zostal dopuszczony: '+val)
            os.environ['SOULBOUND_DB'] = env['SOULBOUND_DB']
            os.environ['SOULBOUND_HOST'] = '0.0.0.0'
            try:
                coverage.check_sandbox_environment()
            except RuntimeError:
                checks += 1
            else:
                raise AssertionError('Niepubliczny test TCP musi uzywac localhost')
        finally:
            if save_db is None: os.environ.pop('SOULBOUND_DB', None)
            else: os.environ['SOULBOUND_DB'] = save_db
            if save_host is None: os.environ.pop('SOULBOUND_HOST', None)
            else: os.environ['SOULBOUND_HOST'] = save_host
    assert len(gate.STAGES) == 8; checks += 1
    assert gate.STAGES[-1][1] == 'validation/v2102_tcp_six_players.py'; checks += 1
    assert gate.STAGES[-3][1] == 'validation/v2302_coverage_contract.py'; checks += 1
    assert len(coverage.READ_TCP_CASES) == len(set(coverage.READ_TCP_CASES)); checks += 1
    assert len(coverage.ADDITIONAL_TCP_CASES) == len(set(coverage.ADDITIONAL_TCP_CASES)); checks += 1
    assert set(coverage.NEGATIVE_TCP_CASES) <= set(coverage.ADDITIONAL_TCP_CASES); checks += 1
    assert 'kill' in coverage.SUPPORTED_QUEST_KINDS; checks += 1
    assert 'profession_action' in coverage.SUPPORTED_QUEST_KINDS; checks += 1
    errors, tested = coverage.check_quest_isolation({
        'fixture_collect': {'needed': 5},
        'fixture_kill': {'needed': 12},
        'fixture_profession': {'needed': 3},
    })
    assert not errors and tested == 18; checks += tested
    return checks


if __name__ == '__main__':
    print('AUDYT POKRYCIA v2.30.2: ', run_contract(), 'kontroli PASS', flush=True)
    print('Pelna gra: komendy i questy w predeploy_full, rzeczywiste scenariusze TCP w ostatniej bramce.', flush=True)
