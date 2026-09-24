# -*- coding: utf-8 -*-
"""Focused SQLite schema: world quests."""


def create_world_quests_schema(self):
    self.conn.executescript(
        r"""
        CREATE TABLE IF NOT EXISTS quests (
                        account_id INTEGER NOT NULL,
                        quest_id TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        progress INTEGER NOT NULL DEFAULT 0,
                        completed_at INTEGER NOT NULL DEFAULT 0,
                        completion_count INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, quest_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS quest_resource_progress_v0929 (
                        account_id INTEGER NOT NULL,
                        quest_id TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        progress INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, quest_id, target_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS exploration_rooms (
                        account_id INTEGER NOT NULL,
                        room_id TEXT NOT NULL,
                        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, room_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS exploration_rewards (
                        account_id INTEGER NOT NULL,
                        zone TEXT NOT NULL,
                        claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, zone),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS collection_codex (
                        account_id INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        entry_id TEXT NOT NULL,
                        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, category, entry_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS nemesis_v029 (
                        account_id INTEGER PRIMARY KEY,
                        base_template_id TEXT NOT NULL,
                        nemesis_name TEXT NOT NULL,
                        rank INTEGER NOT NULL DEFAULT 1,
                        level INTEGER NOT NULL DEFAULT 1,
                        room_id TEXT NOT NULL,
                        kills_player INTEGER NOT NULL DEFAULT 1,
                        defeats INTEGER NOT NULL DEFAULT 0,
                        active INTEGER NOT NULL DEFAULT 1,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS bestiary_stats (
                        account_id INTEGER NOT NULL,
                        mob_template_id TEXT NOT NULL,
                        kills INTEGER NOT NULL DEFAULT 0,
                        fastest_kill_ms INTEGER,
                        first_killed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_killed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, mob_template_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS boss_codex_stats (
                        account_id INTEGER NOT NULL,
                        boss_id TEXT NOT NULL,
                        solo_kills INTEGER NOT NULL DEFAULT 0,
                        group_kills INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, boss_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS boss_codex_drops (
                        account_id INTEGER NOT NULL,
                        boss_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, boss_id, item_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS boss_floor_clears (
                        account_id INTEGER NOT NULL,
                        dungeon_kind TEXT NOT NULL,
                        floor INTEGER NOT NULL,
                        cleared_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, dungeon_kind, floor),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS achievement_progress (
                        account_id INTEGER NOT NULL,
                        metric TEXT NOT NULL,
                        value INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, metric),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS achievements (
                        account_id INTEGER NOT NULL,
                        achievement_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        tier TEXT NOT NULL,
                        unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, achievement_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS bounty_boards (
                        account_id INTEGER PRIMARY KEY,
                        offers_json TEXT NOT NULL DEFAULT '[]',
                        active_json TEXT NOT NULL DEFAULT '{}',
                        completed_count INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS crafting_orders_v0600 (
                        account_id INTEGER PRIMARY KEY,
                        cycle_slot INTEGER NOT NULL DEFAULT 0,
                        npc_id TEXT NOT NULL DEFAULT '',
                        profession TEXT NOT NULL DEFAULT '',
                        item_id TEXT NOT NULL DEFAULT '',
                        item_name TEXT NOT NULL DEFAULT '',
                        needed INTEGER NOT NULL DEFAULT 0,
                        progress INTEGER NOT NULL DEFAULT 0,
                        reward_coins INTEGER NOT NULL DEFAULT 0,
                        reward_profession_xp INTEGER NOT NULL DEFAULT 0,
                        reward_tool_type TEXT NOT NULL DEFAULT '',
                        reward_tool_xp INTEGER NOT NULL DEFAULT 0,
                        accepted_at INTEGER NOT NULL DEFAULT 0,
                        completed_cycle_slot INTEGER NOT NULL DEFAULT -1,
                        completed_count INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS crafting_order_stats_v0614 (
                        account_id INTEGER NOT NULL,
                        profession TEXT NOT NULL,
                        completed_count INTEGER NOT NULL DEFAULT 0,
                        total_coins INTEGER NOT NULL DEFAULT 0,
                        profession_xp INTEGER NOT NULL DEFAULT 0,
                        tool_xp INTEGER NOT NULL DEFAULT 0,
                        best_reward_coins INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, profession),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS dynamic_world_quests_v015 (
                        account_id INTEGER PRIMARY KEY,
                        quest_key TEXT NOT NULL DEFAULT '',
                        quest_type TEXT NOT NULL DEFAULT '',
                        target TEXT NOT NULL DEFAULT 'any',
                        label TEXT NOT NULL DEFAULT '',
                        needed INTEGER NOT NULL DEFAULT 0,
                        progress INTEGER NOT NULL DEFAULT 0,
                        reward_soul_xp INTEGER NOT NULL DEFAULT 0,
                        reward_gold INTEGER NOT NULL DEFAULT 0,
                        accepted_slot INTEGER NOT NULL DEFAULT 0,
                        completed INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS faction_reputation_v016 (
                        account_id INTEGER NOT NULL,
                        faction_id TEXT NOT NULL,
                        reputation INTEGER NOT NULL DEFAULT 0,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, faction_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS drop_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        rarity TEXT NOT NULL,
                        source TEXT NOT NULL DEFAULT '',
                        zone TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS treasure_chest_cooldowns (
                        account_id INTEGER NOT NULL,
                        room_id TEXT NOT NULL,
                        opened_at INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY(account_id, room_id),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS instance_map_progress (
                        account_id INTEGER NOT NULL,
                        instance_kind TEXT NOT NULL,
                        floor INTEGER NOT NULL,
                        first_visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, instance_kind, floor),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS instance_map_secrets (
                        account_id INTEGER NOT NULL,
                        instance_kind TEXT NOT NULL,
                        floor INTEGER NOT NULL,
                        secret_name TEXT NOT NULL,
                        discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, instance_kind, floor),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );

        CREATE TABLE IF NOT EXISTS instance_map_checkpoints (
                        account_id INTEGER NOT NULL,
                        instance_kind TEXT NOT NULL,
                        floor INTEGER NOT NULL,
                        unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(account_id, instance_kind, floor),
                        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
                    );
        """
    )
    # v0.61.4: zachowaj wcześniejszy łączny licznik zamówień bez zmyślania
    # historycznych zarobków/profesji. Szczegółowe statystyki liczymy od tej wersji.
    self.conn.execute(
        "INSERT OR IGNORE INTO crafting_order_stats_v0614(account_id,profession,completed_count) "
        "SELECT account_id,'__legacy__',completed_count FROM crafting_orders_v0600 WHERE completed_count>0"
    )
    self.conn.commit()
