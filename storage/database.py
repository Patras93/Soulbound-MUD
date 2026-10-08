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
