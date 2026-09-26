# -*- coding: utf-8 -*-
"""Database facade for Soulbound v0.46.0.

Persistence is split by responsibility and assembled through normal mixins; Database keeps the public API unchanged.
"""

import os
import sqlite3

from storage.db_schema import DatabaseSchemaMixin
from storage.db_accounts import DatabaseAccountsMixin
from storage.db_world import DatabaseWorldMixin
from storage.db_inventory import DatabaseInventoryMixin
from storage.db_progression import DatabaseProgressionMixin
from storage.db_quests import DatabaseQuestMixin
from storage.db_guilds import DatabaseGuildMixin
from storage.db_crafting_extensions import DatabaseCraftingExtensionsMixin


class Database(
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
        self.conn = sqlite3.connect(path)
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
