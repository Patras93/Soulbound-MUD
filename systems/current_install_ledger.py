# -*- coding: utf-8 -*-
"""Initialize the physical-item schema for a NEW, empty current installation.

The v106/v107 table identifiers are persistent data-format identifiers. They
are created directly here; no prior release, migration, backup or activator
is imported or executed. Existing accounts/items or ledgers are never converted.
"""
from __future__ import annotations
from datetime import datetime, timezone
import sqlite3
from pathlib import Path

SCHEMA = (
    """CREATE TABLE v106_item_instances (
        instance_id TEXT PRIMARY KEY, account_id INTEGER NOT NULL,
        item_id TEXT NOT NULL, evolution_stage INTEGER NOT NULL
            CHECK(evolution_stage BETWEEN 0 AND 10),
        origin TEXT NOT NULL DEFAULT 'legacy_unique')""",
    """CREATE TABLE v106_evolution_migration_issues (
        account_id INTEGER NOT NULL, item_id TEXT NOT NULL,
        copies INTEGER NOT NULL, legacy_stage INTEGER NOT NULL,
        reason TEXT NOT NULL, PRIMARY KEY(account_id,item_id))""",
    """CREATE TABLE v106_equipped_instances (
        account_id INTEGER NOT NULL, slot TEXT NOT NULL,
        instance_id TEXT NOT NULL UNIQUE,
        PRIMARY KEY(account_id,slot),
        FOREIGN KEY(instance_id) REFERENCES v106_item_instances(instance_id))""",
    """CREATE TABLE v106_stored_instances (
        instance_id TEXT PRIMARY KEY, account_id INTEGER NOT NULL,
        storage_kind TEXT NOT NULL, container TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(instance_id) REFERENCES v106_item_instances(instance_id))""",
    """CREATE TABLE v107_eq_production_cutover (
        cutover_version TEXT NOT NULL PRIMARY KEY,
        backup_name TEXT NOT NULL, cutover_utc TEXT NOT NULL)""",
    """CREATE TABLE current_install_origin (
        version TEXT NOT NULL PRIMARY KEY, initialized_utc TEXT NOT NULL,
        origin TEXT NOT NULL CHECK(origin='new_empty_database'))""",
)


def initialize_empty_ledger(conn):
    """Create current physical schema once; fail before writes for any saves."""
    if conn.in_transaction:
        raise ValueError('Fresh initialization requires an idle connection')
    tables = {str(r[0]) for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    required = {'accounts', 'characters', 'inventory', 'equipment'}
    if not required <= tables:
        raise ValueError('Current base schema must be created first')
    ledgers = {'v106_item_instances', 'v106_equipped_instances',
               'v106_stored_instances', 'v107_eq_production_cutover',
               'current_install_origin'}
    if ledgers & tables:
        raise ValueError('Refusing to reinitialize an existing physical ledger')
    for table in ('accounts', 'characters', 'inventory', 'equipment',
                  'bank_items', 'profession_storage'):
        if table in tables and conn.execute(
                'SELECT 1 FROM "' + table + '" LIMIT 1').fetchone():
            raise ValueError('Refusing existing player data in ' + table)
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Current empty database failed integrity_check')
    from systems.universal_activation import current_version
    version = current_version(Path(__file__).resolve().parents[1])
    stamp = datetime.now(timezone.utc).isoformat()
    conn.execute('SAVEPOINT current_new_install')
    try:
        for statement in SCHEMA:
            conn.execute(statement)
        # Data-format checkpoint consumed by the existing per-copy adapter.
        # There was no old database and therefore no historical backup.
        conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?,?)',
                     ('107.00.0', 'current_empty_install', stamp))
        conn.execute('INSERT INTO current_install_origin VALUES(?,?,?)',
                     (version, stamp, 'new_empty_database'))
        conn.execute('RELEASE SAVEPOINT current_new_install')
        conn.commit()
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT current_new_install')
        conn.execute('RELEASE SAVEPOINT current_new_install')
        conn.rollback()
        raise
    return {'version': version, 'origin': 'new_empty_database',
            'physical_tables': 4}
