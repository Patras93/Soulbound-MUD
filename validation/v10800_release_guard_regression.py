# -*- coding: utf-8 -*-
"""v108 adversarial release gate, fully synthetic: NEVER touches a live game."""
from __future__ import annotations
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import hashlib
import json
from unittest.mock import patch
import zipfile

from validation.v10800_release_readiness import (release_at_least_108,
                                                   unmet_requirements)
import predeploy_nowej_wersji as predeploy
import testuj_soulbound_windows as windows
from aktualizuj_soulbound import UpdateError, require_v104_official_predeploy, run_update

ROOT = Path(__file__).resolve().parents[1]


def run():
    checks = 0
    def ok(value, message):
        nonlocal checks
        assert value, message
        checks += 1

    ok(not release_at_least_108('107.00.0'), 'v107 must retain its existing contract')
    ok(release_at_least_108('108.00.0'), '108 production gate missing')
    ok(release_at_least_108('108.00.1'), 'later hotfix must not bypass release gate')
    ok(release_at_least_108('109.00.0'), 'future version must not silently skip gate')
    for invalid in ('', '108', '108.a.0', '107.0.0.extra', '108.00.-1', None):
        try: release_at_least_108(invalid)
        except ValueError: checks += 1
        else: raise AssertionError('Malformed version accepted')

    # Code-completeness is not runtime authorization. The current checkout
    # has no external Windows PREDEPLOY PASS or installer-issued marker.
    missing = unmet_requirements(ROOT)
    ok(not missing, 'v108 candidate still lacks a required production module')
    from systems.v10800_activation import production_approved
    ok(not production_approved(), 'source checkout authorized production without marker')
    with tempfile.TemporaryDirectory(prefix='v108_incomplete_readiness_') as temp:
        fake = Path(temp)
        (fake/'VERSION').write_text('108.00.0',encoding='utf-8')
        unmet = unmet_requirements(fake)
        ok(bool(unmet), 'missing runtime, compatibility and PREDEPLOY were accepted')
        ok(any('autoryzac' in reason.lower() for reason in unmet), 'runtime authorization gate absent')
        ok(any('EQ' in reason for reason in unmet), 'v107 compatibility gate absent')
        ok(any('PREDEPLOY' in reason for reason in unmet), 'Windows PREDEPLOY gate absent')

    with tempfile.TemporaryDirectory(prefix='sb108_release_gate_fake_') as td:
        work = Path(td)
        staged = work/'staged'
        (staged/'logs').mkdir(parents=True)
        (staged/'VERSION').write_text('108.00.0\n', encoding='utf-8')
        local_log = staged/'logs'/'TESTY_Soulbound.log'
        output = StringIO()
        with patch.object(windows, 'ROOT', staged), patch.object(windows, 'LOG', local_log), \
                patch.object(windows, 'run_parallel_stages', side_effect=AssertionError(
                    'Historical tests started before v108 production gate')), \
                redirect_stdout(output):
            code = windows.main()
        ok(code == 3, 'v108 must refuse to use legacy 60/60 as deploy approval')
        ok('V108 PREDEPLOY: FAIL' in output.getvalue(), 'missing clear NVDA failure message')
        ok('WYNIK KONCOWY: FAIL' in output.getvalue(), 'test failed without final FAIL')
        ok(local_log.is_file(), 'early predeploy refusal must produce a log')
        ok('BLOKADA V108' in local_log.read_text(encoding='utf-8'),
           'specific release reason not included in log')

        source = ROOT/'core/bootstrap_economy_professions.py'
        core_text = source.read_text(encoding='utf-8')
        assert 'VERSION = "108.00.0"' in core_text
        def archive(version):
            path = work/f'Soulbound-MUD-v{version}-SYNTHETIC.zip'
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
                for name in predeploy.REQUIRED:
                    if name == 'core/bootstrap_economy_professions.py':
                        out.writestr(name, core_text.replace('VERSION = "108.00.0"',
                                                             f'VERSION = "{version}"'))
                    else:
                        out.write(ROOT/name, name)
                out.writestr('VERSION', version+'\n')
            return path
        v107 = archive('107.00.0')
        v108 = archive('108.00.0')
        old_version, _ = predeploy.inspect_zip(v107)
        ok(old_version == '107.00.0', 'v107 candidate accidentally rejected')
        try: predeploy.inspect_zip(v108)
        except ValueError as exc:
            ok('produkcyjnej bramki' in str(exc),
               'v108 candidate rejected for an unexpected unrelated reason')
        else: raise AssertionError('v108 renamed ZIP accepted without activation')

        fake_live = work/'live'
        fake_live.mkdir()
        (fake_live/'soulbound.db').write_bytes(b'FAKE_PLAYER_DATA_ONLY')
        before = (fake_live/'soulbound.db').read_bytes()
        (fake_live/'core').mkdir()
        (fake_live/'core/bootstrap_economy_professions.py').write_text(
            'VERSION = "107.00.0"\n', encoding='utf-8')
        approved_file = work/'Soulbound_PREDEPLOY'/'last_result_v108.json'
        approved_file.parent.mkdir()
        approved_file.write_text(json.dumps({
            'status':'PASS', 'quality_gate':'ULTIMATE-60-PLUS',
            'completed_stages':60, 'required_stages':60, 'returncode':0,
            'version':'108.00.0', 'installed_at_test':'107.00.0',
            'zip':str(v108), 'sha256':hashlib.sha256(v108.read_bytes()).hexdigest(),
        }), encoding='utf-8')
        try: require_v104_official_predeploy(fake_live, v108, '108.00.0')
        except UpdateError as exc:
            ok('v108:' in str(exc), 'installer refused without v108-specific message')
        else: raise AssertionError('v108 installer accepted a fake 60/60 result')
        with patch('aktualizuj_soulbound.stop_local_server',
                   side_effect=AssertionError('Server STOP before v108 release proof')):
            try: run_update(fake_live, v108, '108.00.0', restart=False)
            except UpdateError as exc:
                ok('v108:' in str(exc), 'direct updater did not block v108')
            else: raise AssertionError('run_update bypassed v108 release gate')
        ok((fake_live/'VERSION').exists() is False,
           'unapproved update wrote VERSION into the game')
        ok((fake_live/'soulbound.db').read_bytes() == before,
           'attempted release guard changed fake player file')
        ok(not any(work.glob('Soulbound_BACKUP*')), 'attempted release created backup')
    return checks


if __name__ == '__main__':
    print(f'V108 BRAMKA WYDANIA: {run()} KONTROLI PASS; NIE WDRAZAC', flush=True)
