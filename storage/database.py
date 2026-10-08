# -*- coding: utf-8 -*-
"""Database facade for Soulbound v0.46.0.

Persistence is split by responsibility and assembled through normal mixins; Database keeps the public API unchanged.
"""

import os
import sqlite3
from contextlib import contextmanager

from storage.db_schema import DatabaseSchemaMixin
from storage.db_accounts import DatabaseAccountsMixin
from storage.db_world import DatabaseWorldMixin
from storage.db_inventory import DatabaseInventoryMixin
from storage.db_progression import DatabaseProgressionMixin
from storage.db_quests import DatabaseQuestMixin
from storage.db_guilds import DatabaseGuildMixin
from storage.db_crafting_extensions import DatabaseCraftingExtensionsMixin
from storage.db_mercenaries import DatabaseMercenariesMixin
from storage.db_world_crises_v1220 import DatabaseWorldCrisesV1220Mixin



class _DeferredCommitConnection:
    """Transparent sqlite3 proxy with nestable deferred commits."""
    def __init__(self, connection):
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_defer_depth", 0)
        object.__setattr__(self, "_commit_pending", False)

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._connection, name, value)

    def commit(self):
        if self._defer_depth > 0:
            self._commit_pending = True
            return
        self._connection.commit()

    def flush_deferred_commit(self):
        if self._commit_pending:
            self._commit_pending = False
            self._connection.commit()

    @contextmanager
    def deferred_commits(self):
        self._defer_depth += 1
        try:
            yield self
        finally:
            self._defer_depth -= 1
            if self._defer_depth <= 0:
                self._defer_depth = 0
                self.flush_deferred_commit()


class Database(
    DatabaseWorldCrisesV1220Mixin,
    DatabaseMercenariesMixin,
    DatabaseCraftingExtensionsMixin,
    DatabaseSchemaMixin,
    DatabaseAccountsMixin,
    DatabaseWorldMixin,
    DatabaseInventoryMixin,
    DatabaseProgressionMixin,
    DatabaseQuestMixin,
    DatabaseGuildMixin
):
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = _DeferredCommitConnection(sqlite3.connect(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        # v0.71.5: NORMAL is the recommended WAL durability/performance balance.
        # It keeps commits durable across normal process crashes while avoiding
        # an fsync-heavy FULL commit for every tiny character/progression write.
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.execute("PRAGMA wal_autocheckpoint=1000")
        self.create_schema()
        self.migrate_schema()
        self.install_crafting_extensions_schema()
        self.create_mercenary_schema()
        self.create_world_crises_schema_v1220()
        # v1.22.4: persistent but minimal admin diagnostics; no passwords or tokens.
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS admin_actions_v1224 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                admin_login TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS admin_errors_v1224 (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                exception TEXT NOT NULL, file TEXT NOT NULL, line INTEGER NOT NULL,
                subsystem TEXT NOT NULL, handler TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS admin_slow_commands_v1224 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                command TEXT NOT NULL, duration_ms INTEGER NOT NULL
            );
        """)
        self.conn.commit()

    def record_admin_action_v1224(self, admin_login, action, target=""):
        self.conn.execute(
            "INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES (?,?,?)",
            (str(admin_login)[:64], str(action)[:64], str(target)[:96]),
        )
        self.conn.execute("DELETE FROM admin_actions_v1224 WHERE id NOT IN "
                          "(SELECT id FROM admin_actions_v1224 ORDER BY id DESC LIMIT 2000)")
        self.conn.commit()

    def record_admin_error_v1224(self, report):
        # Deliberately omit command, traceback and exception message: may contain secrets.
        self.conn.execute("INSERT OR REPLACE INTO admin_errors_v1224 "
                          "(id,exception,file,line,subsystem,handler) VALUES (?,?,?,?,?,?)",
                          (report['error_id'], str(report.get('exception',''))[:80],
                           str(report.get('file',''))[:240], int(report.get('line',0)),
                           str(report.get('subsystem',''))[:80], str(report.get('handler',''))[:80]))
        self.conn.execute("DELETE FROM admin_errors_v1224 WHERE id NOT IN "
                          "(SELECT id FROM admin_errors_v1224 ORDER BY created_at DESC, rowid DESC LIMIT 500)")
        self.conn.commit()

    def record_slow_command_v1224(self, command, duration):
        self.conn.execute("INSERT INTO admin_slow_commands_v1224(command,duration_ms) VALUES (?,?)",
                          (str(command)[:50], int(duration * 1000)))
        self.conn.execute("DELETE FROM admin_slow_commands_v1224 WHERE id NOT IN "
                          "(SELECT id FROM admin_slow_commands_v1224 ORDER BY id DESC LIMIT 100)")
        self.conn.commit()

