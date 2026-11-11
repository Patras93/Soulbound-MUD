# -*- coding: utf-8 -*-
"""Detached Windows PREDEPLOY SQLite snapshot, WAL and temporary proof test.

Uses synthetic accounts only. Never reads the user's database or starts a server.
"""
from __future__ import annotations

from contextlib import closing, redirect_stdout
from io import StringIO
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

import predeploy_nowej_wersji as predeploy


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def run():
    checks = 0
    def ok(condition, message):
        nonlocal checks
        assert condition, message
        checks += 1

    with tempfile.TemporaryDirectory(prefix='v108_predeploy_snapshot_fixture_') as directory:
        home = Path(directory)
        source = home/'fake_live.sqlite'
        with closing(sqlite3.connect(source)) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('CREATE TABLE accounts(id INTEGER PRIMARY KEY); '
                             'CREATE TABLE characters(account_id INTEGER); '
                             'INSERT INTO accounts VALUES(1); '
                             'INSERT INTO characters VALUES(1);')
            db.commit()
            db.execute('INSERT INTO accounts VALUES(2)')
            db.commit()
            db.execute('BEGIN')
            db.execute('INSERT INTO accounts VALUES(3)')  # uncommitted
            source_sha = digest(source)
            wal = Path(str(source)+'-wal')
            wal_sha = digest(wal)
            frozen = predeploy.create_detached_source_snapshot(
                source, home/'frozen.sqlite')
            ok(frozen.exists(), 'no frozen SQLite image')
            ok(frozen != source, 'source overwritten')
            with closing(sqlite3.connect(frozen)) as check:
                ok(check.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
                   'backup failed SQLite integrity')
                ok(check.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] == 2,
                   'WAL committed pages were not captured or uncommitted rows included')
                ok(check.execute('SELECT COUNT(*) FROM characters').fetchone()[0] == 1,
                   'characters missing from frozen SQLite')
            ok(digest(source)==source_sha,'production source .sqlite was modified')
            ok(digest(wal)==wal_sha,'production source WAL was modified')
            db.rollback()
            db.execute('INSERT INTO accounts VALUES(4)')
            db.commit()
            with closing(sqlite3.connect(frozen)) as check:
                ok(check.execute('SELECT COUNT(*) FROM accounts').fetchone()[0] == 2,
                   'frozen snapshot tracked later live edits')

            for invalid in (home/'missing.sqlite', home/'frozen.sqlite'):
                try:
                    predeploy.create_detached_source_snapshot(invalid,
                                                             home/'frozen.sqlite')
                except RuntimeError: checks += 1
                else: raise AssertionError('invalid snapshot input accepted')
            ok(frozen.exists(), 'existing image was overwritten by failed request')

            test_stage = home/'stage'
            test_stage.mkdir()
            # The synthetic harness models pre-v108 behavior without an EQ
            # rebuild. Explicit VERSION prevents accidental v108 auto-branch.
            (test_stage/'VERSION').write_text('107.00.0\n',encoding='utf-8')
            program = test_stage/'testuj_soulbound_windows.py'
            # The *real* runner invokes a child. It must only be able to find
            # the detached snapshot through the environment, never source.
            program.write_text('''import json,os,sqlite3
from pathlib import Path
source=Path(os.environ['SOULBOUND_ULTRA_SOURCE_DB'])
assert source.exists(), 'missing source clone'
with sqlite3.connect(source) as conn:
    count=conn.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]
Path('test_result.json').write_text(json.dumps({
    'source':str(source), 'test_db':os.environ.get('SOULBOUND_DB'),
    'host':os.environ.get('SOULBOUND_HOST'),
    'secret':os.environ.get('SOULBOUND_CONTROL_TOKEN'),
    'dburl':os.environ.get('DATABASE_URL'),
    'count':count,
}),encoding='utf-8')
print('synthetic frozen test PASS',flush=True)
''', encoding='utf-8')
            with patch.dict(os.environ, {
                'SOULBOUND_DB':str(source),
                'SOULBOUND_CONTROL_TOKEN':'synthetic_secret',
                'DATABASE_URL':'postgres://synthetic_private',
            }):
                result = predeploy.run_tests(test_stage, home/'fake_predeploy.log',
                                              timeout_seconds=30)
            ok(result==0, 'detached predeploy child did not finish')
            record=json.loads((test_stage/'test_result.json').read_text(encoding='utf-8'))
            ok(record['source']!=str(source), 'child inherited live source filename')
            ok(record['source']==record['test_db'], 'test source path differs from detached path')
            ok(record['host']=='127.0.0.1', 'candidate network host not isolated')
            ok(record['secret'] is None and record['dburl'] is None,
               'live secrets leaked into candidate process')
            ok(record['count']==3, 'child did not see latest committed source rows')
            ok(not Path(record['source']).exists(), 'detached file left after test')
            ok('baza odlaczona' in (home/'fake_predeploy.log').read_text(encoding='utf-8'),
               'log does not report detached snapshot')

            missing = home/'fake_predeploy_missing.log'
            try:
                predeploy.run_tests(test_stage, missing, source_db=home/'does_not_exist.sqlite',
                                    timeout_seconds=5)
            except RuntimeError: checks += 1
            else: raise AssertionError('predeploy ran without source data')
            ok(not missing.exists(), 'bad DB launched candidate before refusing')

            proof = home/'stage_results.txt'
            proof.write_text('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
                             'PLUS CHECKS PASS\n',encoding='utf-8')
            ok(predeploy.verified_staged_pass(0,proof,'107.00.0'),
               'historical v107 PASS rejected')
            ok(not predeploy.verified_staged_pass(0,proof,'108.00.0'),
               'v107-only PASS wrongly approved v108')
            with proof.open('a',encoding='utf-8') as out:
                out.write('V108 RELEASE GATES PASS\n')
            ok(predeploy.verified_staged_pass(0,proof,'108.00.0'),
               'real staged v108 PASS not recognized')
            ok(not predeploy.verified_staged_pass(1,proof,'108.00.0'),
               'nonzero process exit accepted')
            proof.unlink()
            ok(not predeploy.verified_staged_pass(0,proof,'108.00.0'),
               'missing staged log accepted')

            # Test the REAL predeploy.main ordering with a deliberately mocked
            # archive inspector and mocked 60-stage runner. This proves the
            # staged log is examined while the TemporaryDirectory still exists,
            # without ever authorizing a real v108 ZIP or using any player DB.
            candidate = home/'Soulbound-MUD-v108.00.0-SYNTHETIC.zip'
            candidate.write_bytes(b'only synthetic test content; not a release')
            audit_home = home/'fake_predeploy_state'
            audit_state = audit_home/'last_result_v108.json'
            old_v107_state = audit_home/'last_result.json'
            audit_home.mkdir(parents=True,exist_ok=True)
            old_v107_state.write_text('v107 ORIGINAL APPROVAL - DO NOT TOUCH',encoding='utf-8')
            for v108_proof in (True, False):
                def stage_synthetic(_archive, stage_dir, _mapping):
                    (stage_dir/'logs').mkdir(exist_ok=True)
                    body = ('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
                            'PLUS CHECKS PASS\n')
                    if v108_proof:
                        body += 'V108 RELEASE GATES PASS\n'
                    (stage_dir/'logs/TESTY_Soulbound.log').write_text(
                        body, encoding='utf-8')
                def mock_trial(_stage_dir, logpath, **_kw):
                    with Path(logpath).open('a',encoding='utf-8') as writer:
                        writer.write('V108 PREDEPLOY REBUILD SNAPSHOT PASS: MOCKED_FIXTURE_ONLY\n')
                    return 0
                with patch.object(predeploy, 'WORK', audit_home), \
                     patch.object(predeploy, 'STATE', audit_state), \
                     patch.object(predeploy, 'inspect_zip', return_value=('108.00.0', {})), \
                     patch.object(predeploy, 'installed_version', return_value='107.00.0'), \
                     patch.object(predeploy, 'stage', side_effect=stage_synthetic), \
                     patch.object(predeploy, 'source_review', return_value=[]), \
                     patch.object(predeploy, 'run_tests', side_effect=mock_trial), \
                     redirect_stdout(StringIO()):
                    outcome = predeploy.main([str(candidate)])
                record = json.loads(audit_state.read_text(encoding='utf-8'))
                ok(outcome == (0 if v108_proof else 1),
                   'stage log lifetime caused incorrect PREDEPLOY return code')
                ok(record['status'] == ('PASS' if v108_proof else 'FAIL'),
                   'staged proof did not survive temporary directory cleanup')
                ok(record['sha256'] == digest(candidate),
                   'approved predeploy referred to a different archive')
                ok(old_v107_state.read_text(encoding='utf-8') == 'v107 ORIGINAL APPROVAL - DO NOT TOUCH',
                   'v108 PREDEPLOY overwrote live v107 approval')
            # The PASS above belongs to a deliberately mocked runner with a
            # synthetic invalid ZIP; it is NEVER a real deployment approval.

        not_game = home/'invalid.sqlite'
        with closing(sqlite3.connect(not_game)) as bad:
            bad.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
            bad.commit()
        try:
            predeploy.create_detached_source_snapshot(not_game,
                                                     home/'invalid_output.sqlite')
        except RuntimeError: checks += 1
        else: raise AssertionError('SQLite lacking characters accepted as real game')
        ok(not (home/'invalid_output.sqlite').exists(),
           'failed predeploy left a reusable invalid snapshot')
    return checks

if __name__=='__main__':
    print('V108 PREDEPLOY MIGAWKA WAL I DOWOD: '+str(run())+' PASS; NIE WDRAZAC',flush=True)
