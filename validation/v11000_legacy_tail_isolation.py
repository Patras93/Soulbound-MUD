# -*- coding: utf-8 -*-
"""Fail-closed isolation of legacy v103 tail audits from the shared FAST registry.

The original historical assertions execute unchanged in dedicated interpreters.
This keeps the synthetic retired-raid fixture out of the active v110 server.
"""
from __future__ import annotations

import subprocess
import sys
import os
import socket
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITS = {
    'party': ('validation.v10300_era_raid_party_sqlite',
              'ERA 103 PARTY RAID TWO-ACCOUNT SQLITE: 618 checks PASS', 618),
    'tcp': ('validation.v10300_era_tcp_fixture_gate',
            'ERA 103 TCP FIXTURE: 27 checks PASS', 27),
    'nvda': ('validation.v10300_era_raid_nvda_audit',
             'ERA 103 RAID NVDA STATUS: 61 checks PASS', 61),
    'release': ('validation.v10300_final_release',
                'V103 FINAL RELEASE GATE: 40 checks PASS', 40),
    'hp': ('validation.v10300_era_authored_hp',
           'ERA v103 AUTHORED HP: 77 checks PASS', 77),
}


def verify_result(key: str, returncode: int, stdout: str, stderr: str) -> int:
    """Reject errors, partial passes, wrong counts and spoofed stderr markers."""
    module, expected, count = AUDITS[key]
    lines = [line.strip() for line in stdout.splitlines()]
    if returncode != 0 or lines.count(expected) != 1 or 'Traceback' in stderr:
        details = (stdout + '\n' + stderr)[-4000:]
        raise AssertionError(f'v110 isolated legacy audit FAILED: {module}: {details}')
    return count


def _unused_loopback_port() -> int:
    """Give each historic interpreter its own non-production TCP port.

    The parent FAST runner may already hold its own bootstrap port.  The
    historical HP audit imports server.py and therefore binds a socket even
    though the audit itself only inspects a synthetic world catalogue.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.bind(('127.0.0.1', 0))
        port = int(candidate.getsockname()[1])
    if not 1025 <= port <= 65535 or port == 4000:
        raise RuntimeError('legacy v103 audit received unsafe TCP port')
    return port


def run(key: str) -> int:
    module, _, _ = AUDITS[key]
    # Isolate database path even from the already-private parent PREDEPLOY.
    # The staging authorization flags MUST come from the caller: this helper
    # cannot enable a non-approved v110 server by itself.
    with tempfile.TemporaryDirectory(prefix='sb110_legacy_v103_') as td:
        env = os.environ.copy()
        env['SOULBOUND_DB'] = str(Path(td)/'legacy_audit.sqlite')
        # server.py binds on import in the HP audit. Never share the parent's
        # active socket or inherit higher-priority Railway/PORT overrides.
        env.update(SOULBOUND_HOST='127.0.0.1',
                   SOULBOUND_PORT=str(_unused_loopback_port()),
                   PORT='', RAILWAY_TCP_APPLICATION_PORT='')
        result = subprocess.run(
            [sys.executable, '-u', '-m', module], cwd=str(ROOT),
            env=env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=180,
        )
    return verify_result(key, result.returncode, result.stdout, result.stderr)


def regression() -> int:
    checks = 0
    for key, (_, expected, count) in AUDITS.items():
        assert verify_result(key, 0, expected+'\n', '') == count
        checks += 1
        for rc, stdout, stderr in ((1, expected+'\n', 'Traceback: failure'),
                                   (0, 'OTHER: 1 checks PASS', ''),
                                   (0, expected+'\n'+expected+'\n', ''),
                                   (0, '', expected+'\n')):
            try:
                verify_result(key, rc, stdout, stderr)
            except AssertionError:
                checks += 1
            else:
                raise AssertionError(f'isolation allowed a false pass: {key}, {rc}')
    assert checks == 25
    # Both FAST and FULL must retain the exact same historic gates.
    for filename in ('predeploy_check.py', 'predeploy_full.py'):
        script = (ROOT/filename).read_text(encoding='utf-8')
        for key in AUDITS:
            assert f"_v110_legacy_tail('{key}')" in script, (filename, key)
            checks += 1
        for required in ('validation.v10300_era_raid_party_sqlite',
                         'validation.v10300_era_tcp_fixture_gate',
                         'validation.v10300_final_release'):
            assert required in script, (filename, required)
            checks += 1
    # Reproduce the v110 FAST failure: a parent binds its own bootstrap TCP
    # port, while a child HP audit imports server.py.  Every child must get a
    # different loopback port and ignore inherited higher-priority overrides.
    # Mock only process execution here: the real HP auditor runs separately.
    from types import SimpleNamespace
    from unittest.mock import patch
    observed = []

    def fake_child(argv, **kwargs):
        assert argv[:3] == [sys.executable, '-u', '-m']
        key = next(k for k, spec in AUDITS.items() if spec[0] == argv[3])
        env = kwargs['env']
        assert env['SOULBOUND_HOST'] == '127.0.0.1'
        assert env['PORT'] == env['RAILWAY_TCP_APPLICATION_PORT'] == ''
        port = int(env['SOULBOUND_PORT'])
        assert 1025 <= port <= 65535 and port not in (4000, 45892)
        assert Path(env['SOULBOUND_DB']).name == 'legacy_audit.sqlite'
        assert Path(env['SOULBOUND_DB']).parent.is_dir()
        assert env['SOULBOUND_V110_STAGING'] == '1'  # inherited, never fabricated
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', port))  # available for child server import
        observed.append(key)
        return SimpleNamespace(returncode=0, stdout=AUDITS[key][1]+'\n', stderr='')

    with patch.dict(os.environ, {
        'SOULBOUND_HOST': '0.0.0.0', 'SOULBOUND_PORT': '45892',
        'PORT': '4000', 'RAILWAY_TCP_APPLICATION_PORT': '4000',
        'SOULBOUND_V110_STAGING': '1',
    }), patch.object(subprocess, 'run', side_effect=fake_child):
        for key in AUDITS:
            assert run(key) == AUDITS[key][2]
            checks += 1
    assert observed == list(AUDITS)

    # A helper must never forge a production/staging authorization flag.
    def unauthorized_child(argv, **kwargs):
        env = kwargs['env']
        assert env.get('SOULBOUND_V110_STAGING') == '0'
        assert env['SOULBOUND_HOST'] == '127.0.0.1'
        assert env['PORT'] == env['RAILWAY_TCP_APPLICATION_PORT'] == ''
        assert Path(env['SOULBOUND_DB']).name == 'legacy_audit.sqlite'
        return SimpleNamespace(returncode=0, stdout=AUDITS['hp'][1]+'\n', stderr='')

    with patch.dict(os.environ, {'SOULBOUND_V110_STAGING': '0'}), \
         patch.object(subprocess, 'run', side_effect=unauthorized_child):
        assert run('hp') == AUDITS['hp'][2]
        checks += 1
    return checks


if __name__ == '__main__':
    print(f'V110 LEGACY V103 ISOLATION CONTRACT: {regression()} checks PASS', flush=True)
