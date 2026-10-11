# -*- coding: utf-8 -*-
"""Unit checks of the QUALITY GATE itself. No Soulbound server is started."""
from __future__ import annotations
import os
import sys
from pathlib import Path
import tempfile
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_regression():
    import testuj_soulbound_windows as gate
    from validation.v2102_tcp_six_players import run_contract
    checks = run_contract()
    # Railway image contains only explicitly COPY-ed sources. Without this
    # module, importing the Windows gate in this self-test fails even though
    # running from the complete Windows source tree succeeds.
    docker_source = (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    copy_gate = 'COPY testuj_soulbound_windows.py /app/testuj_soulbound_windows.py'
    build_gate = 'RUN python /app/predeploy_check.py'
    assert copy_gate in docker_source.splitlines(), 'Dockerfile does not COPY the quality gate into Railway'
    checks += 1
    assert docker_source.index(copy_gate) < docker_source.index(build_gate), 'The quality gate must exist before predeploy starts'
    checks += 1
    assert '/app/testuj_soulbound_windows.py' in docker_source[docker_source.index(build_gate):], 'Remove the build-only gate after tests'
    checks += 1
    with tempfile.TemporaryDirectory(prefix='sb-gate-selftest-') as directory:
        temp = Path(directory)
        saved_env = {k: os.environ.get(k) for k in ('RAILWAY_VOLUME_MOUNT_PATH', 'SOULBOUND_ADMIN_ACCOUNTS')}
        os.environ['RAILWAY_VOLUME_MOUNT_PATH'] = '/not-a-production-volume'
        os.environ['SOULBOUND_ADMIN_ACCOUNTS'] = 'do_not_inherit'
        try:
            env = gate.stage_env(temp)
        finally:
            for k, old in saved_env.items():
                if old is None: os.environ.pop(k, None)
                else: os.environ[k] = old
        for ok in (
            env['SOULBOUND_DB'] == str(temp / 'audit.sqlite'),
            env['SOULBOUND_WORLD_SEED_FILE'] == str(temp / 'audit_seed.txt'),
            env['SOULBOUND_HOST'] == '127.0.0.1',
            0 < int(env['SOULBOUND_PORT']) < 65536,
            'RAILWAY_VOLUME_MOUNT_PATH' not in env,
            'SOULBOUND_ADMIN_ACCOUNTS' not in env,
            len(gate.STAGES) == 9,
            [step[1] for step in gate.STAGES] == [
                'predeploy_check.py', 'predeploy_full.py',
                'validation/v2200_master_depths_ai.py',
                'validation/v2201_fleet_mastery.py',
                'validation/v2300_world_professions_ocean.py',
                'validation/v2302_coverage_contract.py',
                'validation/v2310_event_contract.py',
                'validation/v2320_autonomous_routes.py',
                'validation/v2102_tcp_six_players.py',
            ],
            gate.STAGES[-1][1] == 'validation/v2102_tcp_six_players.py',
            all(step[2] >= 120 for step in gate.STAGES),
        ):
            assert ok, 'Gate safety or completeness assertion failed'
            checks += 1
        original_root = gate.ROOT
        try:
            gate.ROOT = temp
            (temp / 'ok.py').write_text('print("OK")\n', encoding='utf-8')
            (temp / 'fail.py').write_text('print("FAILED")\nraise SystemExit(7)\n', encoding='utf-8')
            (temp / 'hang.py').write_text('import time\ntime.sleep(10)\n', encoding='utf-8')
            messages = []
            assert gate.run_stage('ok.py', env, 8, messages.append) == 0
            checks += 1
            assert 'OK' in messages
            checks += 1
            assert gate.run_stage('fail.py', env, 8, messages.append) == 7
            checks += 1
            assert 'FAILED' in messages
            checks += 1
            assert gate.run_stage('hang.py', env, .3, messages.append) == 124
            checks += 1
            assert any('Przekroczony limit czasu' in m for m in messages)
            checks += 1
            assert not (temp / 'audit.sqlite').exists(), 'Self-test must not create actual game db'
            checks += 1
        finally:
            gate.ROOT = original_root
    return checks


if __name__ == '__main__':
    print('QUALITY GATE CONTRACT:', run_regression(), 'PASS')
