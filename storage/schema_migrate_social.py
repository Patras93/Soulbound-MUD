# -*- coding: utf-8 -*-
"""Social, postal and activity journal schema migrations."""


def migrate_social_courier_schema(self):
    # v0.30.51: Social Suite 2.0, mail, LFG, housing, records, mentor 2.0.
    self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS social_ignores_v03051(account_id INTEGER NOT NULL, ignored_account_id INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(account_id,ignored_account_id));
        CREATE TABLE IF NOT EXISTS social_channel_settings_v03051(account_id INTEGER NOT NULL, channel TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(account_id,channel));
        CREATE TABLE IF NOT EXISTS social_channel_history_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT, channel TEXT NOT NULL, sender_account_id INTEGER NOT NULL, sender_name TEXT NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS social_afk_v03051(account_id INTEGER PRIMARY KEY, message TEXT NOT NULL DEFAULT '', since_ts INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS player_mail_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT, recipient_account_id INTEGER NOT NULL, sender_account_id INTEGER, sender_name TEXT NOT NULL, subject TEXT NOT NULL DEFAULT '', body TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS bulletin_posts_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT, author_account_id INTEGER NOT NULL, author_name TEXT NOT NULL, category TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS lfg_entries_v03051(account_id INTEGER PRIMARY KEY, character_name TEXT NOT NULL, category TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_ts INTEGER NOT NULL, expires_ts INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS mentor_progress_v03051(mentor_account_id INTEGER NOT NULL, student_account_id INTEGER NOT NULL, activity_points INTEGER NOT NULL DEFAULT 0, rewards_claimed INTEGER NOT NULL DEFAULT 0, last_point_ts INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(mentor_account_id,student_account_id));
        CREATE TABLE IF NOT EXISTS newbie_protection_v03051(account_id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS daily_login_v03051(account_id INTEGER PRIMARY KEY, last_day TEXT NOT NULL DEFAULT '', streak INTEGER NOT NULL DEFAULT 0, best_streak INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS player_housing_v03051(account_id INTEGER PRIMARY KEY, level INTEGER NOT NULL DEFAULT 1, name TEXT NOT NULL DEFAULT 'Dom', decor TEXT NOT NULL DEFAULT '', storage_json TEXT NOT NULL DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS player_profile_privacy_v03051(account_id INTEGER PRIMARY KEY, inspect_enabled INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS player_presence_v0363(
            account_id INTEGER PRIMARY KEY,
            last_login_ts INTEGER NOT NULL DEFAULT 0,
            last_logout_ts INTEGER NOT NULL DEFAULT 0,
            last_seen_ts INTEGER NOT NULL DEFAULT 0,
            login_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS player_records_v03051(account_id INTEGER NOT NULL, record_key TEXT NOT NULL, value INTEGER NOT NULL DEFAULT 0, text_value TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(account_id,record_key));
        CREATE TABLE IF NOT EXISTS player_completion_v03052(account_id INTEGER PRIMARY KEY, secrets_found INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS mentor_graduation_v03052(mentor_account_id INTEGER NOT NULL, student_account_id INTEGER NOT NULL, graduated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, activity_points INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(mentor_account_id,student_account_id));
        CREATE TABLE IF NOT EXISTS housing_rooms_v03052(account_id INTEGER NOT NULL, room_key TEXT NOT NULL, room_name TEXT NOT NULL, decor TEXT NOT NULL DEFAULT '', station TEXT NOT NULL DEFAULT '', chest_json TEXT NOT NULL DEFAULT '{}', PRIMARY KEY(account_id,room_key));
        CREATE TABLE IF NOT EXISTS housing_trophies_v03052(account_id INTEGER NOT NULL, trophy_key TEXT NOT NULL, display_name TEXT NOT NULL, PRIMARY KEY(account_id,trophy_key));
        CREATE TABLE IF NOT EXISTS accessibility_presets_v03052(account_id INTEGER PRIMARY KEY, combat TEXT NOT NULL DEFAULT 'normal', social TEXT NOT NULL DEFAULT 'normal', system TEXT NOT NULL DEFAULT 'normal');
        CREATE TABLE IF NOT EXISTS combat_recaps_v03052(id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, opponent TEXT NOT NULL DEFAULT '', duration_ms INTEGER NOT NULL DEFAULT 0, damage_dealt INTEGER NOT NULL DEFAULT 0, damage_taken INTEGER NOT NULL DEFAULT 0, healing INTEGER NOT NULL DEFAULT 0, crits INTEGER NOT NULL DEFAULT 0, skills_used INTEGER NOT NULL DEFAULT 0, result TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS death_recaps_v03052(id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER NOT NULL, killer TEXT NOT NULL DEFAULT '', room_id TEXT NOT NULL DEFAULT '', damage_taken INTEGER NOT NULL DEFAULT 0, duration_ms INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS equipment_enchants_v03053(account_id INTEGER NOT NULL, slot TEXT NOT NULL, enchant_key TEXT NOT NULL, stat TEXT NOT NULL, amount INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(account_id,slot));
        CREATE TABLE IF NOT EXISTS engineer_tool_upgrades_v0317(account_id INTEGER NOT NULL, skill_id TEXT NOT NULL, upgraded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(account_id,skill_id));
        CREATE TABLE IF NOT EXISTS postal_delivery_state_v0522(
            account_id INTEGER PRIMARY KEY,
            active_json TEXT NOT NULL DEFAULT '{}',
            completed_count INTEGER NOT NULL DEFAULT 0,
            abandoned_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS courier_guild_state_v0530(
            account_id INTEGER PRIMARY KEY,
            reputation INTEGER NOT NULL DEFAULT 1,
            total_earnings INTEGER NOT NULL DEFAULT 0,
            longest_route INTEGER NOT NULL DEFAULT 0,
            visited_cities_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS city_reputation_v0710(
            account_id INTEGER NOT NULL,
            city_name TEXT NOT NULL,
            reputation INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(account_id, city_name),
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_city_reputation_v0710_account
            ON city_reputation_v0710(account_id, reputation DESC, city_name);
        CREATE TABLE IF NOT EXISTS activity_journal_v0560(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_activity_journal_v0560_account_time
            ON activity_journal_v0560(account_id,created_at DESC,id DESC);
    """)
    # v0.61.4: bezpieczne załączniki do poczty graczy. ALTER-y są addytywne
    # i działają na istniejącej bazie bez wipe.
    _mail_cols = {str(r[1]) for r in self.conn.execute("PRAGMA table_info(player_mail_v03051)")}
    for _name, _decl in (
        ("attachment_kind", "TEXT NOT NULL DEFAULT ''"),
        ("attachment_item_id", "TEXT NOT NULL DEFAULT ''"),
        ("attachment_item_name", "TEXT NOT NULL DEFAULT ''"),
        ("attachment_item_qty", "INTEGER NOT NULL DEFAULT 0"),
        ("attachment_coins", "INTEGER NOT NULL DEFAULT 0"),
        ("attachment_meta_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("attachment_claimed", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if _name not in _mail_cols:
            self.conn.execute(f"ALTER TABLE player_mail_v03051 ADD COLUMN {_name} {_decl}")
    self.conn.commit()
    # v0.30.51: Mentor System. Jedna aktywna para mentor-uczeń na konto.
    self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS mentor_requests_v03050 (
            mentor_account_id INTEGER NOT NULL,
            student_account_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(mentor_account_id, student_account_id)
        );
        CREATE TABLE IF NOT EXISTS mentor_links_v03050 (
            mentor_account_id INTEGER NOT NULL UNIQUE,
            student_account_id INTEGER NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(mentor_account_id, student_account_id)
        );
    """)

