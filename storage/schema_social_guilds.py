# -*- coding: utf-8 -*-
"""Focused SQLite schema: social guilds."""


def create_social_guilds_schema(self):
    self.conn.executescript(
        r"""
        CREATE TABLE IF NOT EXISTS player_clans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                        owner_account_id INTEGER NOT NULL,
                        level INTEGER NOT NULL DEFAULT 1,
                        treasury INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS player_clan_roles (
                        clan_id INTEGER NOT NULL,
                        role_key TEXT NOT NULL,
                        name TEXT NOT NULL,
                        priority INTEGER NOT NULL DEFAULT 20,
                        withdraw_money INTEGER NOT NULL DEFAULT 0,
                        withdraw_items INTEGER NOT NULL DEFAULT 0,
                        invite INTEGER NOT NULL DEFAULT 0,
                        kick INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(clan_id,role_key),
                        UNIQUE(clan_id,name)
                    );

        CREATE TABLE IF NOT EXISTS player_clan_members (
                        clan_id INTEGER NOT NULL,
                        account_id INTEGER NOT NULL UNIQUE,
                        rank TEXT NOT NULL DEFAULT 'member',
                        joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(clan_id,account_id)
                    );

        CREATE TABLE IF NOT EXISTS player_clan_invites (
                        clan_id INTEGER NOT NULL,
                        target_account_id INTEGER NOT NULL,
                        inviter_account_id INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(clan_id,target_account_id)
                    );

        CREATE TABLE IF NOT EXISTS player_clan_bank (
                        clan_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(clan_id,item_id)
                    );

        CREATE TABLE IF NOT EXISTS player_clan_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clan_id INTEGER NOT NULL,
                        actor_account_id INTEGER NOT NULL DEFAULT 0,
                        message TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS player_clan_metrics (
                        clan_id INTEGER NOT NULL,
                        metric TEXT NOT NULL,
                        value INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(clan_id,metric)
                    );

        CREATE TABLE IF NOT EXISTS player_clan_achievements (
                        clan_id INTEGER NOT NULL,
                        achievement_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(clan_id,achievement_id)
                    );

        CREATE TABLE IF NOT EXISTS player_guild_halls_v0927 (
                        clan_id INTEGER PRIMARY KEY,
                        hall_level INTEGER NOT NULL DEFAULT 1,
                        forge_level INTEGER NOT NULL DEFAULT 0,
                        treasury_level INTEGER NOT NULL DEFAULT 0,
                        library_level INTEGER NOT NULL DEFAULT 0,
                        training_level INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS player_guild_contracts_v0927 (
                        clan_id INTEGER NOT NULL,
                        contract_id TEXT NOT NULL,
                        progress INTEGER NOT NULL DEFAULT 0,
                        completed_count INTEGER NOT NULL DEFAULT 0,
                        ready_at INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(clan_id,contract_id)
                    );

        CREATE TABLE IF NOT EXISTS player_guild_boss_records_v0927 (
                        clan_id INTEGER PRIMARY KEY,
                        kills INTEGER NOT NULL DEFAULT 0,
                        fastest_kill_ms INTEGER,
                        last_boss_name TEXT NOT NULL DEFAULT '',
                        last_killed_at TEXT,
                        last_summoned_at INTEGER NOT NULL DEFAULT 0
                    );

        CREATE TABLE IF NOT EXISTS player_guild_trophies_v0927 (
                        clan_id INTEGER NOT NULL,
                        trophy_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        count INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(clan_id,trophy_id)
                    );

        CREATE TABLE IF NOT EXISTS lifetime_statistics (
                        account_id INTEGER NOT NULL,
                        stat_key TEXT NOT NULL,
                        value INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, stat_key),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS fish_journal (
                        account_id INTEGER NOT NULL,
                        fish_id TEXT NOT NULL,
                        caught_count INTEGER NOT NULL DEFAULT 0,
                        best_length_mm INTEGER NOT NULL DEFAULT 0,
                        best_weight_g INTEGER NOT NULL DEFAULT 0,
                        first_room_id TEXT NOT NULL DEFAULT '',
                        last_room_id TEXT NOT NULL DEFAULT '',
                        first_caught_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_caught_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, fish_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS fish_global_records_v022 (
                        fish_id TEXT PRIMARY KEY,
                        best_length_mm INTEGER NOT NULL DEFAULT 0,
                        length_holder TEXT NOT NULL DEFAULT '',
                        best_weight_g INTEGER NOT NULL DEFAULT 0,
                        weight_holder TEXT NOT NULL DEFAULT '',
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS fish_rarest_record_v022 (
                        record_key TEXT PRIMARY KEY,
                        rarity_score INTEGER NOT NULL DEFAULT 0,
                        fish_id TEXT NOT NULL DEFAULT '',
                        item_id TEXT NOT NULL DEFAULT '',
                        holder_name TEXT NOT NULL DEFAULT '',
                        length_mm INTEGER NOT NULL DEFAULT 0,
                        weight_g INTEGER NOT NULL DEFAULT 0,
                        rarity_label TEXT NOT NULL DEFAULT '',
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS world_projects_v022 (
                        project_id TEXT PRIMARY KEY,
                        progress_json TEXT NOT NULL DEFAULT '{}',
                        completed INTEGER NOT NULL DEFAULT 0,
                        completed_at TEXT
                    );

        CREATE TABLE IF NOT EXISTS world_project_contributions_v022 (
                        project_id TEXT NOT NULL,
                        account_id INTEGER NOT NULL,
                        points INTEGER NOT NULL DEFAULT 0,
                        resources_json TEXT NOT NULL DEFAULT '{}',
                        coins INTEGER NOT NULL DEFAULT 0,
                        reward_claimed INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(project_id,account_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS legendary_contracts_v022 (
                        account_id INTEGER PRIMARY KEY,
                        offers_json TEXT NOT NULL DEFAULT '[]',
                        active_json TEXT NOT NULL DEFAULT '{}',
                        completed_count INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );
        """
    )
