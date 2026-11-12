# -*- coding: utf-8 -*-
"""Current-only activation regression. No server, sockets or player database."""
from __future__ import annotations
import ast
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HISTORICAL = {
    'systems.v10700_activation', 'systems.v10800_activation',
    'systems.v10900_activation', 'systems.v10900_staging_guard',
    'systems.v11000_activation', 'systems.v11100_holiday_activation',
    'systems.v11200_activation',
}


def check():
    from systems import runtime_activation as current
    from systems import universal_activation as implementation
    checks = 0
    # Every nonhistorical gameplay module must authorize through the current
    # release; offline historical fixtures remain outside this assertion.
    files = [ROOT / 'server.py']
    for folder in ('core', 'data', 'events', 'network', 'player', 'server',
                   'server_parts_v109', 'storage', 'systems', 'world'):
        files.extend((ROOT / folder).rglob('*.py'))
    for path in files:
        module = path.relative_to(ROOT).as_posix()[:-3].replace('/', '.')
        if module in HISTORICAL:
            continue
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in HISTORICAL, (path, node.lineno, node.module)
            elif isinstance(node, ast.Import):
                assert not HISTORICAL.intersection(a.name for a in node.names), path
    checks += 1
    assert not HISTORICAL.intersection(sys.modules), 'importing current API imported old activators'
    checks += 1
    required = set(current.REQUIRED)
    assert 'systems/runtime_activation.py' in required
    assert 'systems/universal_activation.py' in required
    assert not {m.replace('.', '/') + '.py' for m in HISTORICAL}.intersection(required)
    checks += 3
    from aktualizuj_soulbound import (
        V112_HISTORICAL_ACTIVATION_FILES, production_release_mapping,
    )
    from validation.v11200_closed_runtime_gate import inspect_files, source_files
    all_files = source_files(ROOT)
    installed = {p.as_posix() for p in production_release_mapping(
        {Path(p): None for p in all_files})}
    assert not V112_HISTORICAL_ACTIVATION_FILES.intersection(installed)
    closure = inspect_files(all_files, installed, required_files={
        'server.py', 'systems/runtime_activation.py', 'systems/universal_activation.py'})
    assert closure['missing_import_count'] == 0, closure['missing_imports'][:10]
    checks += 2
    source = (ROOT / 'server/mud_server.py').read_text(encoding='utf-8-sig')
    assert '_runtime_mode = authorized_mode(DB_PATH)' in source
    assert 'authorized_predeploy_test' not in source
    assert '_ver108' not in source and '_ver109' not in source and '_ver110' not in source
    assert 'v107_eq_production_cutover' in source, 'player ledger safety guard was lost'
    checks += 4
    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-stage-') as folder:
        database = Path(folder) / 'isolated.sqlite'
        clean = {'SOULBOUND_UNIVERSAL_STAGING': '1', 'SOULBOUND_HOST': '127.0.0.1',
                 'SOULBOUND_PORT': '49123', 'SOULBOUND_DB': str(database)}
        with patch.object(implementation, 'production_approved', return_value=False):
            with patch.dict(os.environ, clean, clear=True):
                assert current.enabled()
                assert current.authorized_mode(database) == 'test'
                checks += 2
                for change in ({'SOULBOUND_HOST': '0.0.0.0'},
                               {'SOULBOUND_PORT': '4000'},
                               {'SOULBOUND_UNIVERSAL_STAGING': '0'},
                               {'SOULBOUND_DB': str(ROOT / 'soulbound.db')}):
                    with patch.dict(os.environ, change):
                        assert not current.enabled(), change
                        try:
                            current.authorized_mode(os.environ['SOULBOUND_DB'])
                        except PermissionError:
                            checks += 1
                        else:
                            raise AssertionError(('unsafe staging authorized', change))
            old_flags = dict(clean)
            old_flags.pop('SOULBOUND_UNIVERSAL_STAGING')
            old_flags.update({f'SOULBOUND_V{v}_STAGING': '1'
                              for v in (106, 107, 108, 109, 110, 111)})
            with patch.dict(os.environ, old_flags, clear=True):
                assert not current.enabled(), 'old flags authorized current release'
                checks += 1
        # A staging flag never substitutes for a production signature.
        with patch.dict(os.environ, clean, clear=True):
            assert not implementation.verify(Path(folder))
            checks += 1
        assert not database.exists(), 'regression touched a SQLite database'
        checks += 1
    # End-to-end authorization contract for the nested private TCP arena.
    # No database is created; the sandbox disappears after the test.
    from arena_real_izolowana import _private_env
    with tempfile.TemporaryDirectory(prefix='Soulbound_UOSS_REAL_') as sandbox:
        clone = Path(sandbox) / 'gra'
        clone.mkdir()
        own_db = clone / 'soulbound.db'
        parent = {'SOULBOUND_UNIVERSAL_STAGING':'1',
                  'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'49129'}
        with patch.object(implementation, 'ROOT', clone), patch.object(implementation, 'production_approved', return_value=False):
            with patch.dict(os.environ, parent, clear=True):
                child = _private_env(clone, 49131)
                assert child.get('SOULBOUND_UNIVERSAL_STAGING')=='1'
                checks += 1
                with patch.dict(os.environ, child, clear=True):
                    assert current.authorized_mode(own_db)=='test'
                    checks += 1
                    for bad_db in (clone/'other.db',Path(sandbox)/'soulbound.db', ROOT/'soulbound.db'):
                        assert not implementation._test_database(bad_db), bad_db
                        checks += 1
                    for bad_env in ({'SOULBOUND_UNIVERSAL_STAGING':'0'},
                                    {'SOULBOUND_HOST':'0.0.0.0'},
                                    {'SOULBOUND_PORT':'4000'}):
                        with patch.dict(os.environ, bad_env):
                            assert not implementation._test_database(own_db), bad_env
                            checks += 1
            with patch.dict(os.environ, {'SOULBOUND_UNIVERSAL_STAGING':'0'}, clear=True):
                child = _private_env(clone, 49131)
                assert 'SOULBOUND_UNIVERSAL_STAGING' not in child
                checks += 1
            # Even with staging permission, a clone in any other fixture
            # directory cannot masquerade as the production database.
            with patch.dict(os.environ, parent, clear=True):
                assert 'SOULBOUND_UNIVERSAL_STAGING' not in _private_env(Path(sandbox), 49131)
                checks += 1
        assert not own_db.exists()
        checks += 1
    print(f'CURRENT ACTIVATION INDEPENDENCE: {checks} checks PASS')
    return checks

if __name__ == '__main__':
    check()
