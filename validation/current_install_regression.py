# -*- coding: utf-8 -*-
"""Standalone installer adversarial tests; temporary synthetic SQLite only."""
from __future__ import annotations
from contextlib import closing, redirect_stdout
import io
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
from systems.current_install_ledger import initialize_empty_ledger
from systems import current_install as installer


def base_schema(conn):
    for table in ('accounts', 'characters', 'inventory', 'equipment',
                  'bank_items', 'profession_storage'):
        conn.execute('CREATE TABLE ' + table + '(id INTEGER)')
    conn.commit()


def check():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb112_install_unit_') as folder:
        root = Path(folder)
        with closing(sqlite3.connect(root / 'new.sqlite')) as conn:
            base_schema(conn)
            result = initialize_empty_ledger(conn)
            assert result['origin'] == 'new_empty_database'
            for table in ('v106_item_instances', 'v106_equipped_instances',
                          'v106_stored_instances', 'v106_evolution_migration_issues'):
                assert conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] == 0
                checks += 1
            assert conn.execute('SELECT origin FROM current_install_origin').fetchone() == ('new_empty_database',)
            checks += 1
            try:
                initialize_empty_ledger(conn)
            except ValueError:
                checks += 1
            else:
                raise AssertionError('existing ledger reinitialized')
        for table in ('accounts', 'characters', 'inventory', 'equipment',
                      'bank_items', 'profession_storage'):
            with closing(sqlite3.connect(':memory:')) as conn:
                base_schema(conn)
                conn.execute('INSERT INTO ' + table + ' VALUES(1)')
                conn.commit()
                before = list(conn.iterdump())
                try:
                    initialize_empty_ledger(conn)
                except ValueError:
                    assert list(conn.iterdump()) == before, 'existing saves changed'
                    checks += 1
                else:
                    raise AssertionError('existing player data accepted: ' + table)
        with closing(sqlite3.connect(':memory:')) as conn:
            base_schema(conn)
            conn.execute('INSERT INTO accounts VALUES(1)')
            try:
                initialize_empty_ledger(conn)
            except ValueError:
                assert conn.in_transaction, 'caller transaction lost'
                checks += 1
            else:
                raise AssertionError('caller transaction accepted')
        existing = root / 'existing'
        existing.mkdir()
        sentinel = existing / 'player-save'
        sentinel.write_bytes(b'keep')
        with patch.object(installer, 'validate') as validate:
            try:
                installer.install(existing)
            except installer.InstallError:
                validate.assert_not_called()
                assert sentinel.read_bytes() == b'keep'
                checks += 1
            else:
                raise AssertionError('existing install overwritten')
        # Runtime assets are not limited to conventional source suffixes.
        asset_source = root / 'asset_source'
        (asset_source / 'systems').mkdir(parents=True)
        (asset_source / 'VERSION').write_text(installer.VERSION)
        (asset_source / 'server.py').write_text('# fixture')
        (asset_source / 'systems/current_install.py').write_text('# fixture')
        assets = {'data/catalogue_numeric_defaults_v1283.jsonl.gz': b'compressed catalog fixture',
                  'data/tzdb/Europe/Warsaw': b'extensionless timezone fixture'}
        for name, content in assets.items():
            file = asset_source / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(content)
        for name in ('soulbound.db', 'soulbound.db-wal', '.env', 'credentials.json', 'download.zip'):
            (asset_source / name).write_bytes(b'private or mutable')
        hashes = installer.source_files(asset_source)
        assert set(assets) <= hashes.keys()
        assert not {'soulbound.db', 'soulbound.db-wal', '.env', 'credentials.json', 'download.zip'} & hashes.keys()
        selected = installer.installed_sources(asset_source, hashes)
        assert set(assets) <= selected.keys()
        copied = root / 'copied_assets'
        copied.mkdir()
        installer.copy_sources(asset_source, copied, selected)
        for name, content in assets.items():
            assert (copied / name).read_bytes() == content
            assert installer.sha(copied / name) == hashes[name]
            checks += 1
        checks += 2
        # A failed mandatory subprocess never produces reusable PASS evidence.
        from subprocess import CompletedProcess
        with patch.object(installer.subprocess, 'run', return_value=CompletedProcess([], 9, b'FAIL')), redirect_stdout(io.StringIO()):
            try:
                installer._execute(installer.ROOT, installer.VALIDATORS[0])
            except installer.InstallError:
                checks += 1
            else:
                raise AssertionError('failed gate accepted')
        for data in ({}, {'schema': 2, 'version': installer.VERSION,
                          'status': 'PASS', 'quality_gate': installer.QUALITY_GATE,
                          'source_gate': 'CURRENT_STANDALONE_VALIDATED',
                          'checks': []}):
            assert not installer.verify_marker(root, data)
            checks += 1
    print(f'CURRENT INSTALL REGRESSION PASS: {checks} checks; new empty ledger, existing saves refused, failed gate refused')
    return checks

if __name__ == '__main__':
    check()
