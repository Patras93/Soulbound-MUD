# -*- coding: utf-8 -*-
"""Focused SQLite schema: core."""


def create_core_schema(self):
    self.conn.executescript(
        r"""
        CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                        password_salt TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );

        CREATE TABLE IF NOT EXISTS account_characters (
                        master_account_id INTEGER NOT NULL,
                        character_account_id INTEGER NOT NULL UNIQUE,
                        slot INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(master_account_id, slot),
                        FOREIGN KEY(master_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                        FOREIGN KEY(character_account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS account_wallet (
                        master_account_id INTEGER PRIMARY KEY,
                        silver INTEGER NOT NULL DEFAULT 0,
                        gold INTEGER NOT NULL DEFAULT 0,
                        mithril INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(master_account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS characters (
                        account_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                        name_nom TEXT NOT NULL DEFAULT '',
                        name_gen TEXT NOT NULL DEFAULT '',
                        name_dat TEXT NOT NULL DEFAULT '',
                        name_acc TEXT NOT NULL DEFAULT '',
                        name_ins TEXT NOT NULL DEFAULT '',
                        name_loc TEXT NOT NULL DEFAULT '',
                        name_voc TEXT NOT NULL DEFAULT '',
                        race TEXT NOT NULL,
                        class_name TEXT NOT NULL,
                        class_type TEXT NOT NULL,
                        soul_weapon TEXT NOT NULL,
                        weapon_base INTEGER NOT NULL,
                        strength INTEGER NOT NULL,
                        dexterity INTEGER NOT NULL,
                        constitution INTEGER NOT NULL,
                        intelligence INTEGER NOT NULL,
                        willpower INTEGER NOT NULL,
                        stat_progress INTEGER NOT NULL DEFAULT 0,
                        strength_progress INTEGER NOT NULL DEFAULT 0,
                        dexterity_progress INTEGER NOT NULL DEFAULT 0,
                        constitution_progress INTEGER NOT NULL DEFAULT 0,
                        intelligence_progress INTEGER NOT NULL DEFAULT 0,
                        willpower_progress INTEGER NOT NULL DEFAULT 0,
                        charisma_progress INTEGER NOT NULL DEFAULT 0,
                        soul_level INTEGER NOT NULL DEFAULT 1,
                        soul_xp INTEGER NOT NULL DEFAULT 0,
                        soul_tier INTEGER NOT NULL DEFAULT 1,
                        soul_weapon_mastery_level INTEGER NOT NULL DEFAULT 1,
                        soul_weapon_mastery_xp INTEGER NOT NULL DEFAULT 0,
                        room_id TEXT NOT NULL DEFAULT 'square',
                        silver INTEGER NOT NULL DEFAULT 250,
                        gold INTEGER NOT NULL DEFAULT 2,
                        mithril INTEGER NOT NULL DEFAULT 0,
                        charisma INTEGER NOT NULL DEFAULT 10,
                        character_level INTEGER NOT NULL DEFAULT 1,
                        character_xp INTEGER NOT NULL DEFAULT 0,
                        deaths INTEGER NOT NULL DEFAULT 0,
                        crypt_checkpoint INTEGER NOT NULL DEFAULT 0,
                        guild_reputation_json TEXT NOT NULL DEFAULT '{}',
                        guild_exams_json TEXT NOT NULL DEFAULT '{}',
                        guild_class_quests_json TEXT NOT NULL DEFAULT '{}',
                        guild_bounty_json TEXT NOT NULL DEFAULT '{}',
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS inventory (
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS equipment (
                        account_id INTEGER NOT NULL,
                        slot TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        PRIMARY KEY(account_id, slot),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS equipment_gems (
                        account_id INTEGER NOT NULL,
                        slot TEXT NOT NULL,
                        socket_index INTEGER NOT NULL,
                        jewelry_item_id TEXT NOT NULL,
                        gem_id TEXT NOT NULL,
                        PRIMARY KEY(account_id, slot, socket_index),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS bank_balances (
                        account_id INTEGER PRIMARY KEY,
                        silver INTEGER NOT NULL DEFAULT 0,
                        gold INTEGER NOT NULL DEFAULT 0,
                        mithril INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS bank_items (
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id,item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS player_friends_v0928 (
                        account_id INTEGER NOT NULL,
                        friend_account_id INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, friend_account_id),
                        CHECK(account_id <> friend_account_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                        FOREIGN KEY(friend_account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS player_friend_requests_v0928 (
                        sender_account_id INTEGER NOT NULL,
                        target_account_id INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(sender_account_id, target_account_id),
                        CHECK(sender_account_id <> target_account_id),
                        FOREIGN KEY(sender_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                        FOREIGN KEY(target_account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );
        """
    )
