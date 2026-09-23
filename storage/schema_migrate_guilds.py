# -*- coding: utf-8 -*-
"""Guild schema migrations."""

def migrate_guild_schema(self, V0926_GUILD_DEFAULT_ROLES, V0927_GUILD_CONTRACTS):
    # v0.9.26: rozwój Gildii graczy jest niedestrukcyjnym rozszerzeniem
    # tabel v0.9.25. Wewnętrzne nazwy player_clan pozostają dla zgodności save'ów.
    _guild_cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(player_clans)")}
    if "level" not in _guild_cols:
        self.conn.execute("ALTER TABLE player_clans ADD COLUMN level INTEGER NOT NULL DEFAULT 1")
    if "treasury" not in _guild_cols:
        self.conn.execute("ALTER TABLE player_clans ADD COLUMN treasury INTEGER NOT NULL DEFAULT 0")
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS player_clan_roles (
            clan_id INTEGER NOT NULL, role_key TEXT NOT NULL, name TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 20,
            withdraw_money INTEGER NOT NULL DEFAULT 0,
            withdraw_items INTEGER NOT NULL DEFAULT 0,
            invite INTEGER NOT NULL DEFAULT 0, kick INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(clan_id,role_key), UNIQUE(clan_id,name)
        )
    """)
    for _grow in self.conn.execute("SELECT id FROM player_clans").fetchall():
        _gid=int(_grow["id"])
        for _key,_data in V0926_GUILD_DEFAULT_ROLES.items():
            self.conn.execute(
                "INSERT OR IGNORE INTO player_clan_roles(clan_id,role_key,name,priority,withdraw_money,withdraw_items,invite,kick) VALUES(?,?,?,?,?,?,?,?)",
                (_gid,_key,_data["name"],_data["priority"],_data["withdraw_money"],_data["withdraw_items"],_data["invite"],_data["kick"]),
            )

    # v0.9.27: osobna Siedziba Gildii, budynki, kontrakty i bossy.
    self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS player_guild_halls_v0927 (
            clan_id INTEGER PRIMARY KEY, hall_level INTEGER NOT NULL DEFAULT 1,
            forge_level INTEGER NOT NULL DEFAULT 0, treasury_level INTEGER NOT NULL DEFAULT 0,
            library_level INTEGER NOT NULL DEFAULT 0, training_level INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS player_guild_contracts_v0927 (
            clan_id INTEGER NOT NULL, contract_id TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
            completed_count INTEGER NOT NULL DEFAULT 0, ready_at INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(clan_id,contract_id)
        );
        CREATE TABLE IF NOT EXISTS player_guild_boss_records_v0927 (
            clan_id INTEGER PRIMARY KEY, kills INTEGER NOT NULL DEFAULT 0, fastest_kill_ms INTEGER,
            last_boss_name TEXT NOT NULL DEFAULT '', last_killed_at TEXT, last_summoned_at INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS player_guild_trophies_v0927 (
            clan_id INTEGER NOT NULL, trophy_id TEXT NOT NULL, name TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(clan_id,trophy_id)
        );
    """)
    for _grow in self.conn.execute("SELECT id FROM player_clans").fetchall():
        _gid=int(_grow["id"])
        self.conn.execute("INSERT OR IGNORE INTO player_guild_halls_v0927(clan_id) VALUES(?)",(_gid,))
        for _cid in V0927_GUILD_CONTRACTS:
            self.conn.execute("INSERT OR IGNORE INTO player_guild_contracts_v0927(clan_id,contract_id) VALUES(?,?)",(_gid,_cid))


