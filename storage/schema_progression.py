# -*- coding: utf-8 -*-
"""Focused SQLite schema: progression."""


def create_progression_schema(self):
    self.conn.executescript(
        r"""
        CREATE TABLE IF NOT EXISTS professions (
                        account_id INTEGER NOT NULL,
                        profession TEXT NOT NULL,
                        level INTEGER NOT NULL DEFAULT 1,
                        xp INTEGER NOT NULL DEFAULT 0,
                        actions INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, profession),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS crafting_mastery_v03054 (
                        account_id INTEGER NOT NULL,
                        profession TEXT NOT NULL,
                        category TEXT NOT NULL,
                        actions INTEGER NOT NULL DEFAULT 0,
                        criticals INTEGER NOT NULL DEFAULT 0,
                        legendary_count INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, profession, category),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS tools (
                        account_id INTEGER NOT NULL,
                        tool_type TEXT NOT NULL,
                        level INTEGER NOT NULL DEFAULT 1,
                        xp INTEGER NOT NULL DEFAULT 0,
                        uses INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, tool_type),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS profession_storage (
                        account_id INTEGER NOT NULL,
                        container TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, container,item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS astral_progress (
                        account_id INTEGER PRIMARY KEY,
                        checkpoint INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS mine_progress (
                        account_id INTEGER PRIMARY KEY,
                        max_floor_unlocked INTEGER NOT NULL DEFAULT 1,
                        wall_hits INTEGER NOT NULL DEFAULT 0,
                        wall_required_hits INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS class_progress (
                        account_id INTEGER NOT NULL,
                        class_name TEXT NOT NULL,
                        level INTEGER NOT NULL DEFAULT 1,
                        xp INTEGER NOT NULL DEFAULT 0,
                        active_slot INTEGER,
                        PRIMARY KEY(account_id, class_name),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS learned_skills (
                        account_id INTEGER NOT NULL,
                        skill_id TEXT NOT NULL,
                        learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, skill_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS skill_progress (
                        account_id INTEGER NOT NULL,
                        skill_id TEXT NOT NULL,
                        level INTEGER NOT NULL DEFAULT 1,
                        xp INTEGER NOT NULL DEFAULT 0,
                        uses INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, skill_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS skill_queue (
                        account_id INTEGER NOT NULL,
                        queue_type TEXT NOT NULL,
                        position INTEGER NOT NULL,
                        skill_id TEXT NOT NULL,
                        PRIMARY KEY(account_id, queue_type, position),
                        UNIQUE(account_id, skill_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS skill_queue_settings (
                        account_id INTEGER PRIMARY KEY,
                        enabled INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS combat_log_settings (
                        account_id INTEGER PRIMARY KEY,
                        mode TEXT NOT NULL DEFAULT 'normal',
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS wimpy_settings (
                        account_id INTEGER PRIMARY KEY,
                        percent INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS ascension_progress_v021 (
                        account_id INTEGER NOT NULL,
                        track TEXT NOT NULL,
                        rank INTEGER NOT NULL DEFAULT 0,
                        xp INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, track),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS world_tier_settings_v021 (
                        account_id INTEGER PRIMARY KEY,
                        tier INTEGER NOT NULL DEFAULT 1,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS endless_gauntlet_progress_v021 (
                        account_id INTEGER PRIMARY KEY,
                        best_round INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS unlocked_titles (
                        account_id INTEGER NOT NULL,
                        title_id TEXT NOT NULL,
                        title_name TEXT NOT NULL,
                        unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, title_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS equipment_reforges (
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        affix TEXT NOT NULL,
                        affix_amount INTEGER NOT NULL DEFAULT 0,
                        rerolls INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id,item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS equipment_upgrades_v03042 (
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        upgrade_level INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id,item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS equipment_runes_v0925 (
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        socket_index INTEGER NOT NULL,
                        rune_id TEXT NOT NULL,
                        PRIMARY KEY(account_id,item_id,socket_index),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );
        """
    )
