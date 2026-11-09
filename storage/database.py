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
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
from storage.db_titans_v2100 import DatabaseTitansV2100Mixin



class _DeferredCommitConnection:
    """SQLite proxy: defer COMMIT and isolate failed scopes with SAVEPOINTs.

    A deferred operation must not commit a partial kill, nor may it roll back
    unrelated writes already staged by another component on the connection.
    This is still *not* an async concurrency lock: whole-kill isolation needs
    its own later validation when other asyncio tasks use the same connection.
    """
    def __init__(self, connection):
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_defer_depth", 0)
        object.__setattr__(self, "_commit_pending", False)
        object.__setattr__(self, "_savepoint_counter", 0)
        object.__setattr__(self, "_context_savepoints", [])

    def _new_savepoint(self):
        self._savepoint_counter += 1
        # Generated locally from a counter, never from SQL/user input.
        name = f"sb104_deferred_{self._savepoint_counter}"
        self._connection.execute("SAVEPOINT " + name)
        return name

    def __enter__(self):
        # sqlite3.Connection.__exit__ COMMITs the entire connection.  A nested
        # `with conn` must not silently commit the caller's existing SAVEPOINT.
        if self._defer_depth or self._connection.in_transaction:
            self._context_savepoints.append((self._new_savepoint(), self._commit_pending))
        else:
            self._context_savepoints.append(None)
            self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        marker = self._context_savepoints.pop()
        if marker is not None:
            name, pending_before = marker
            if exc_type is not None:
                try:
                    self._connection.execute("ROLLBACK TO SAVEPOINT " + name)
                finally:
                    self._connection.execute("RELEASE SAVEPOINT " + name)
                    self._commit_pending = pending_before
            else:
                self._connection.execute("RELEASE SAVEPOINT " + name)
                # Inside deferred_commits the surrounding owner may commit
                # later.  With an external transaction, leave commit to caller.
                self._commit_pending = True if self._defer_depth else pending_before
            return False
        return self._connection.__exit__(exc_type, exc, tb)

    def executescript(self, script):
        # Python sqlite3.executescript silently COMMITs any open transaction.
        # Run complete SQL statements with execute instead, preserving caller
        # transactions and SAVEPOINTs across schema migrations and combat.
        statement = ''
        for char in script:
            statement += char
            if char == ';' and sqlite3.complete_statement(statement):
                if statement.strip():
                    self._connection.execute(statement)
                statement = ''
        if statement.strip():
            self._connection.execute(statement)
        return None

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
        if self._defer_depth:
            return
        if self._commit_pending:
            self._connection.commit()
            self._commit_pending = False

    @contextmanager
    def deferred_commits(self):
        # Each nested scope owns its changes. A caught inner exception must
        # not leave a partial payout behind or erase unrelated prior SQL.
        # A SAVEPOINT can be nested in a transaction owned by a caller.
        # Never flush COMMIT across that ownership boundary: doing so removes
        # the caller's savepoint and makes its rollback impossible.
        outermost = self._defer_depth == 0
        caller_owns_transaction = outermost and self._connection.in_transaction
        marker = self._new_savepoint()
        prior_pending = self._commit_pending
        self._defer_depth += 1
        try:
            yield self
        except BaseException:
            try:
                self._connection.execute("ROLLBACK TO SAVEPOINT " + marker)
            finally:
                self._connection.execute("RELEASE SAVEPOINT " + marker)
                self._commit_pending = prior_pending
                self._defer_depth -= 1
            raise
        else:
            self._connection.execute("RELEASE SAVEPOINT " + marker)
            self._defer_depth -= 1
            if self._defer_depth == 0:
                if caller_owns_transaction:
                    # All changes stay inside the still-open caller transaction.
                    # A legacy method's commit request cannot escape it.
                    self._commit_pending = prior_pending
                else:
                    self.flush_deferred_commit()


def ensure_admin_error_status_v1371(conn):
    """Add manual resolution metadata to old SB error records without dropping them."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(admin_errors_v1224)")}
    if "resolved_at" not in columns:
        conn.execute("ALTER TABLE admin_errors_v1224 ADD COLUMN resolved_at TEXT NOT NULL DEFAULT ''")
    if "resolved_by" not in columns:
        conn.execute("ALTER TABLE admin_errors_v1224 ADD COLUMN resolved_by TEXT NOT NULL DEFAULT ''")


class Database(
    DatabaseTitansV2100Mixin,
    DatabaseExperienceBankV2011Mixin,
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
        self.migrate_friend_accounts_v12213()
        self.install_crafting_extensions_schema()
        self.create_mercenary_schema()
        self.create_world_crises_schema_v1220()
        self.create_experience_bank_schema_v2011()
        self.create_titans_schema_v2100()
        self.create_city_services_schema_v1225()
        # New, isolated v104 world-event tables; never touches player balances.
        from systems.world_invasions_v10400 import create_schema as _v104_invasions_schema
        _v104_invasions_schema(self.conn)
        from core.bootstrap_economy_professions import VERSION as _release_version
        if _release_version == '110.00.0':
            from systems.events_v110.storage import create_schema as _v110_event_schema
            _v110_event_schema(self.conn)
            # v110: created once at startup; no DDL in player work commands.
            self.conn.execute('CREATE TABLE IF NOT EXISTS v110_profession_cooldowns ('
                'account_id INTEGER NOT NULL,tool_type TEXT NOT NULL,ready_at INTEGER NOT NULL,'
                'PRIMARY KEY(account_id,tool_type))')
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
        # v1.37.1: non-destructive migration of the historical admin error register.
        # Old records remain unresolved until an administrator marks them fixed.
        ensure_admin_error_status_v1371(self.conn)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS protected_inventory_v1280 (
                account_id INTEGER NOT NULL, item_id TEXT NOT NULL,
                PRIMARY KEY (account_id, item_id)
            )
        """)
        # v104: all normal SQLite writers (also raw SQL outside mixins) must
        # refuse precision-losing REAL/TEXT values on progression/currencies.
        # No BigNumber live migration is activated here.
        from storage.sqlite_numeric_integrity_v10400 import install_numeric_write_barriers
        install_numeric_write_barriers(self.conn)
        # v104: production TEXT authority for keyed XP only. All other axes
        # retain int64 guards until their full gameplay routes are migrated.
        from storage.big_number_live_keyed_xp_v10400 import install_live_keyed_xp
        install_live_keyed_xp(self.conn)
        from storage.big_number_live_character_v10400 import install_live_character_progress
        install_live_character_progress(self.conn)
        # v107 physical ledger must be verified and explicitly installed later,
        # after live dynamic item templates are registered by MudServer.
        self._v107_eq_live_active = False
        self._v107_eq_migration_committed = False
        self._v104_live_exact_character = True
        self._v104_live_exact_keyed_xp = True
        self.conn.commit()

    def create_city_services_schema_v1225(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS bank_transfers_v1225 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL, receiver_id INTEGER NOT NULL,
                kind TEXT NOT NULL, item_id TEXT NOT NULL DEFAULT '',
                quantity INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id) REFERENCES accounts(id),
                FOREIGN KEY(receiver_id) REFERENCES accounts(id)
            );
            CREATE TABLE IF NOT EXISTS hunter_contracts_v1225 (
                account_id INTEGER NOT NULL, tier TEXT NOT NULL,
                target_id TEXT NOT NULL, needed INTEGER NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0, reward_silver INTEGER NOT NULL,
                state TEXT NOT NULL DEFAULT 'active', ready_after INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,tier),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
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

    def set_admin_error_resolved_v1371(self, error_id, admin_login, resolved=True):
        """Manual resolution label; an error is not assumed fixed automatically."""
        error_id = str(error_id).strip().upper()
        if not __import__("re").fullmatch(r"SB-[0-9A-F]{8}", error_id):
            return False
        with self.conn as conn:
            result = conn.execute(
                "UPDATE admin_errors_v1224 SET resolved_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE '' END, "
                "resolved_by=CASE WHEN ? THEN ? ELSE '' END WHERE id=?",
                (int(resolved), int(resolved), str(admin_login)[:64], error_id),
            )
            if not result.rowcount:
                return False
            conn.execute(
                "INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES (?,?,?)",
                (str(admin_login)[:64], "error_fixed" if resolved else "error_reopened", error_id),
            )
        return True

    def purge_resolved_admin_errors_v1371(self, admin_login):
        """Remove only explicitly resolved records; audit and purge share one SQLite transaction."""
        with self.conn as conn:
            result = conn.execute("DELETE FROM admin_errors_v1224 WHERE resolved_at != ''")
            removed = int(result.rowcount)
            conn.execute(
                "INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES (?,?,?)",
                (str(admin_login)[:64], "errors_purge_fixed", f"count={removed}"),
            )
        return removed

    def record_slow_command_v1224(self, command, duration):
        self.conn.execute("INSERT INTO admin_slow_commands_v1224(command,duration_ms) VALUES (?,?)",
                          (str(command)[:50], int(duration * 1000)))
        self.conn.execute("DELETE FROM admin_slow_commands_v1224 WHERE id NOT IN "
                          "(SELECT id FROM admin_slow_commands_v1224 ORDER BY id DESC LIMIT 100)")
        self.conn.commit()

