

class Database:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_schema()
        self.migrate_schema()

    def create_schema(self):
        self.conn.executescript(
            """
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

            CREATE TABLE IF NOT EXISTS bounty_boards (
                account_id INTEGER PRIMARY KEY,
                offers_json TEXT NOT NULL DEFAULT '[]',
                active_json TEXT NOT NULL DEFAULT '{}',
                completed_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
        self.conn.commit()

    def migrate_schema(self):
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
        """)
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
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(characters)")}
        _v027_character_level_new = "character_level" not in cols
        additions = {
            "silver": "INTEGER NOT NULL DEFAULT 30",
            "gold": "INTEGER NOT NULL DEFAULT 2",
            "mithril": "INTEGER NOT NULL DEFAULT 0",
            "charisma": "INTEGER NOT NULL DEFAULT 10",
            "character_level": "INTEGER NOT NULL DEFAULT 1",
            "character_xp": "INTEGER NOT NULL DEFAULT 0",
            "deaths": "INTEGER NOT NULL DEFAULT 0",
            "crypt_checkpoint": "INTEGER NOT NULL DEFAULT 0",
            "name_nom": "TEXT NOT NULL DEFAULT ''",
            "name_gen": "TEXT NOT NULL DEFAULT ''",
            "name_dat": "TEXT NOT NULL DEFAULT ''",
            "name_acc": "TEXT NOT NULL DEFAULT ''",
            "name_ins": "TEXT NOT NULL DEFAULT ''",
            "name_loc": "TEXT NOT NULL DEFAULT ''",
            "name_voc": "TEXT NOT NULL DEFAULT ''",
            "guild_reputation_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_exams_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_class_quests_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_bounty_json": "TEXT NOT NULL DEFAULT '{}'",
            "loot_filter": "TEXT NOT NULL DEFAULT 'all'",
            "active_title": "TEXT NOT NULL DEFAULT ''",
            "strength_progress": "INTEGER NOT NULL DEFAULT 0",
            "dexterity_progress": "INTEGER NOT NULL DEFAULT 0",
            "constitution_progress": "INTEGER NOT NULL DEFAULT 0",
            "intelligence_progress": "INTEGER NOT NULL DEFAULT 0",
            "willpower_progress": "INTEGER NOT NULL DEFAULT 0",
            "charisma_progress": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in additions.items():
            if name not in cols:
                self.conn.execute(f"ALTER TABLE characters ADD COLUMN {name} {decl}")

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

        # Zgodność ze starymi postaciami: jeśli nie mają jeszcze odmiany,
        # dotychczasowe imię staje się bezpieczną formą we wszystkich przypadkach.
        for column in (
            "name_nom", "name_gen", "name_dat", "name_acc",
            "name_ins", "name_loc", "name_voc",
        ):
            self.conn.execute(
                f"UPDATE characters SET {column}=name "
                f"WHERE {column} IS NULL OR TRIM({column})=''"
            )
        # v0.8.38: Charyzma jest szóstą normalną statystyką.
        # Stare postacie zachowują wypracowaną Charyzmę; wartości 0/brakujące
        # otrzymują bezpieczną wartość startową 10.
        self.conn.execute(
            "UPDATE characters SET charisma=10 "
            "WHERE charisma IS NULL OR charisma < 1"
        )

        # v0.8.6: dwa sloty pierścieni. Stary slot ring jest
        # bezpiecznie migrowany do ring1 bez kasowania przedmiotów.
        old_ring = self.conn.execute(
            "SELECT item_id FROM equipment WHERE slot='ring' LIMIT 1"
        ).fetchone()
        ring1 = self.conn.execute(
            "SELECT item_id FROM equipment WHERE slot='ring1' LIMIT 1"
        ).fetchone()
        if old_ring and not ring1:
            self.conn.execute(
                "UPDATE equipment SET slot='ring1' WHERE slot='ring'"
            )
            self.conn.execute(
                "UPDATE equipment_gems SET slot='ring1' WHERE slot='ring'"
            )
        elif old_ring and ring1:
            # Nie niszczymy nietypowych danych; pozostawiony stary wpis
            # zostanie zignorowany do ręcznej korekty zamiast nadpisania ring1.
            pass

        # v0.8.52: dwa sloty talizmanów. Stary slot charm zostaje
        # niedestrukcyjnie przeniesiony do charm1.
        self.conn.execute(
            "UPDATE equipment SET slot='charm1' "
            "WHERE slot='charm' AND NOT EXISTS ("
            "SELECT 1 FROM equipment e2 "
            "WHERE e2.account_id=equipment.account_id AND e2.slot='charm1'"
            ")"
        )

        quest_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(quests)")
        }
        quest_additions = {
            "completed_at": "INTEGER NOT NULL DEFAULT 0",
            "completion_count": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in quest_additions.items():
            if name not in quest_cols:
                self.conn.execute(
                    f"ALTER TABLE quests ADD COLUMN {name} {decl}"
                )

        # v0.8.24: każda ściana Kopalni Głębinowej ma własny,
        # losowy i trwały próg uderzeń. Kolumna jest dodawana
        # niedestrukcyjnie do zapisów z wcześniejszych wersji.
        mine_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(mine_progress)")
        }
        if "wall_required_hits" not in mine_cols:
            self.conn.execute(
                "ALTER TABLE mine_progress ADD COLUMN "
                "wall_required_hits INTEGER NOT NULL DEFAULT 0"
            )

        # v0.8.5: jednorazowa, niedestrukcyjna migracja starego systemu
        # Soul Tier 1-5 do nowego 1-20. Zachowuje zdobyte Próby.
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS migration_flags("
            "flag TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )

        # v0.27.0: stare postacie nie startują nagle od Levelu 1. Przy pierwszym
        # dodaniu osi Character Level wyprowadzamy go z najwyższej istniejącej osi
        # progresji (Soul/Biegłość/profesja/narzędzie), bez kasowania żadnego postępu.
        if _v027_character_level_new:
            self.conn.execute("""
                UPDATE characters SET character_level = MIN(400, MAX(1,
                    soul_level,
                    COALESCE((SELECT MAX(level) FROM class_progress cp WHERE cp.account_id=characters.account_id),1),
                    COALESCE((SELECT MAX(level) FROM professions p WHERE p.account_id=characters.account_id),1),
                    COALESCE((SELECT MAX(level) FROM tools t WHERE t.account_id=characters.account_id),1)
                )), character_xp=0
            """)
            self.conn.execute("INSERT OR IGNORE INTO migration_flags(flag) VALUES(?)",("character_level_v0270",))

        # v0.8.66: sześć niezależnych liczników EXP statystyk.
        # Stary wspólny Postęp Rozwoju jest kopiowany 1:1 do każdej statystyki,
        # dzięki czemu żadna postać nie traci wypracowanego postępu.
        stat_xp_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("separate_stat_progress_v0866",),
        ).fetchone()
        if not stat_xp_migrated:
            self.conn.execute(
                "UPDATE characters SET "
                "strength_progress=stat_progress, dexterity_progress=stat_progress, "
                "constitution_progress=stat_progress, intelligence_progress=stat_progress, "
                "willpower_progress=stat_progress, charisma_progress=stat_progress"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("separate_stat_progress_v0866",),
            )
        migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("soul_tier_20_v085",),
        ).fetchone()
        if not migrated:
            self.conn.execute(
                "UPDATE characters SET soul_tier = CASE soul_tier "
                "WHEN 1 THEN 1 WHEN 2 THEN 4 WHEN 3 THEN 7 "
                "WHEN 4 THEN 13 WHEN 5 THEN 19 ELSE soul_tier END "
                "WHERE soul_tier BETWEEN 1 AND 5"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("soul_tier_20_v085",),
            )

        # v0.8.8: narzędzia profesji są Character-Bound.
        # Jeżeli stara wersja pozwoliła schować je do Banku Dusz albo
        # zgromadzić kilka kopii, zostaje dokładnie jedna sztuka przy postaci.
        bound_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("character_bound_tools_v088",),
        ).fetchone()
        if not bound_migrated:
            for item_id in CHARACTER_BOUND_TOOL_IDS:
                bank_rows = self.conn.execute(
                    "SELECT account_id,quantity FROM bank_items "
                    "WHERE item_id=? AND quantity>0",
                    (item_id,),
                ).fetchall()
                for bank_row in bank_rows:
                    account_id = int(bank_row["account_id"])
                    owned = self.conn.execute(
                        "SELECT quantity FROM inventory "
                        "WHERE account_id=? AND item_id=?",
                        (account_id, item_id),
                    ).fetchone()
                    if not owned or int(owned["quantity"]) <= 0:
                        self.conn.execute(
                            "INSERT INTO inventory(account_id,item_id,quantity) "
                            "VALUES(?,?,1) "
                            "ON CONFLICT(account_id,item_id) "
                            "DO UPDATE SET quantity=1",
                            (account_id, item_id),
                        )
                self.conn.execute(
                    "DELETE FROM bank_items WHERE item_id=?",
                    (item_id,),
                )
                self.conn.execute(
                    "UPDATE inventory SET quantity=1 "
                    "WHERE item_id=? AND quantity>1",
                    (item_id,),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("character_bound_tools_v088",),
            )

        # v0.31.8: ponowna, pełna normalizacja narzędzi po dodaniu
        # Krawiectwa, Garbarstwa, Stolarstwa i Zaklinania. Stara flaga v0.8.8
        # mogła już istnieć na kontach utworzonych przed dodaniem tych profesji.
        # Progres narzędzi (level/xp/uses) jest w tabeli tools i nie jest tu
        # modyfikowany — normalizujemy wyłącznie fizyczną liczbę przedmiotów.
        tools_0318_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("character_bound_tools_all_v0318",),
        ).fetchone()
        if not tools_0318_migrated:
            for item_id in CHARACTER_BOUND_TOOL_IDS:
                # Jeśli stara kopia leży w Banku Dusz, przenieś jedną sztukę
                # do inventory właściciela tylko wtedy, gdy nie ma jej już tam.
                bank_rows = self.conn.execute(
                    "SELECT account_id,quantity FROM bank_items "
                    "WHERE item_id=? AND quantity>0",
                    (item_id,),
                ).fetchall()
                for bank_row in bank_rows:
                    account_id = int(bank_row["account_id"])
                    owned = self.conn.execute(
                        "SELECT quantity FROM inventory "
                        "WHERE account_id=? AND item_id=?",
                        (account_id, item_id),
                    ).fetchone()
                    if not owned or int(owned["quantity"] or 0) <= 0:
                        self.conn.execute(
                            "INSERT INTO inventory(account_id,item_id,quantity) "
                            "VALUES(?,?,1) "
                            "ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=1",
                            (account_id, item_id),
                        )
                # Bank nie może przechowywać character-bound tools.
                self.conn.execute("DELETE FROM bank_items WHERE item_id=?", (item_id,))
                # Na każdej postaci zostaje najwyżej jedna fizyczna sztuka.
                self.conn.execute(
                    "UPDATE inventory SET quantity=1 "
                    "WHERE item_id=? AND quantity>1",
                    (item_id,),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("character_bound_tools_all_v0318",),
            )

        # v0.8.20: stare konto z jedną postacią staje się kontem głównym
        # ze slotem 1. Dalsze postacie są przechowywane w osobnych, ukrytych
        # profilach danych, dzięki czemu wszystkie dotychczasowe tabele
        # pozostają w 100% odseparowane między postaciami.
        self.conn.execute(
            """
            INSERT OR IGNORE INTO account_characters(
                master_account_id, character_account_id, slot
            )
            SELECT c.account_id, c.account_id, 1
            FROM characters c
            WHERE NOT EXISTS(
                SELECT 1 FROM account_characters ac
                WHERE ac.character_account_id=c.account_id
            )
            """
        )

        # v0.8.32: jeden wspólny portfel dla wszystkich postaci na koncie.
        # Pierwsza migracja SUMUJE walutę wszystkich istniejących slotów,
        # dzięki czemu aktualizacja nie kasuje pieniędzy żadnej postaci.
        wallet_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("shared_account_wallet_v0832",),
        ).fetchone()
        if not wallet_migrated:
            masters = self.conn.execute(
                "SELECT DISTINCT master_account_id FROM account_characters "
                "ORDER BY master_account_id"
            ).fetchall()
            for master_row in masters:
                master_id = int(master_row["master_account_id"])
                sums = self.conn.execute(
                    """
                    SELECT COALESCE(SUM(c.silver),0) AS silver,
                           COALESCE(SUM(c.gold),0) AS gold,
                           COALESCE(SUM(c.mithril),0) AS mithril
                    FROM account_characters ac
                    JOIN characters c ON c.account_id=ac.character_account_id
                    WHERE ac.master_account_id=?
                    """,
                    (master_id,),
                ).fetchone()
                silver, gold, mithril = normalize_currency_values(
                    int(sums["silver"] or 0),
                    int(sums["gold"] or 0),
                    int(sums["mithril"] or 0),
                )
                self.conn.execute(
                    "INSERT OR REPLACE INTO account_wallet("
                    "master_account_id,silver,gold,mithril,updated_at"
                    ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
                    (master_id, silver, gold, mithril),
                )
                self.conn.execute(
                    """
                    UPDATE characters SET silver=?,gold=?,mithril=?
                    WHERE account_id IN (
                        SELECT character_account_id FROM account_characters
                        WHERE master_account_id=?
                    )
                    """,
                    (silver, gold, mithril, master_id),
                )

                # Waluta zdeponowana w Banku Dusz również jest wspólna.
                bank_sums = self.conn.execute(
                    """
                    SELECT COALESCE(SUM(b.silver),0) AS silver,
                           COALESCE(SUM(b.gold),0) AS gold,
                           COALESCE(SUM(b.mithril),0) AS mithril
                    FROM account_characters ac
                    LEFT JOIN bank_balances b ON b.account_id=ac.character_account_id
                    WHERE ac.master_account_id=?
                    """,
                    (master_id,),
                ).fetchone()
                bank_silver, bank_gold, bank_mithril = normalize_currency_values(
                    int(bank_sums["silver"] or 0),
                    int(bank_sums["gold"] or 0),
                    int(bank_sums["mithril"] or 0),
                )
                self.conn.execute(
                    "INSERT INTO bank_balances(account_id,silver,gold,mithril) "
                    "VALUES(?,?,?,?) "
                    "ON CONFLICT(account_id) DO UPDATE SET "
                    "silver=excluded.silver,gold=excluded.gold,mithril=excluded.mithril",
                    (master_id, bank_silver, bank_gold, bank_mithril),
                )
                self.conn.execute(
                    """
                    DELETE FROM bank_balances
                    WHERE account_id<>? AND account_id IN (
                        SELECT character_account_id FROM account_characters
                        WHERE master_account_id=?
                    )
                    """,
                    (master_id, master_id),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("shared_account_wallet_v0832",),
            )

        # v0.8.51: nadaj istniejącym postaciom taki sam bazowy profil klasy,
        # jaki od tej wersji dostają nowe postacie. Jednorazowa flaga zapobiega
        # ponownemu dodawaniu bonusów po restarcie/deployu.
        class_stats_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("class_starting_stats_v0851",),
        ).fetchone()
        if not class_stats_migrated:
            rows = self.conn.execute(
                "SELECT account_id,class_name FROM characters"
            ).fetchall()
            for row in rows:
                bonuses = V0876_CLASS_STARTING_STAT_BONUSES.get(row["class_name"], {})
                self.conn.execute(
                    "UPDATE characters SET strength=strength+?, dexterity=dexterity+?, "
                    "constitution=constitution+?, intelligence=intelligence+?, "
                    "willpower=willpower+?, charisma=charisma+? WHERE account_id=?",
                    (
                        int(bonuses.get("strength", 0)),
                        int(bonuses.get("dexterity", 0)),
                        int(bonuses.get("constitution", 0)),
                        int(bonuses.get("intelligence", 0)),
                        int(bonuses.get("willpower", 0)),
                        int(bonuses.get("charisma", 0)),
                        int(row["account_id"]),
                    ),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("class_starting_stats_v0851",),
            )

        # v0.9.0: pełny balans startu rasa + klasa + weapon_base.
        # Zachowujemy CAŁY zdobyty później rozwój: do aktualnej wartości
        # dodajemy wyłącznie różnicę między starym a nowym profilem startowym.
        # Flaga sprawia, że migracja jest idempotentna.
        character_balance_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("character_start_balance_v0900",),
        ).fetchone()
        if not character_balance_migrated:
            new_race_stats = {
                race[0]: {
                    "strength": int(race[2]),
                    "dexterity": int(race[3]),
                    "constitution": int(race[4]),
                    "intelligence": int(race[5]),
                    "willpower": int(race[6]),
                }
                for race in RACES
            }
            new_weapon_bases = {entry[0]: int(entry[3]) for entry in CLASSES}
            rows = self.conn.execute(
                "SELECT account_id,race,class_name FROM characters"
            ).fetchall()
            stat_names = (
                "strength", "dexterity", "constitution",
                "intelligence", "willpower", "charisma",
            )
            for row in rows:
                race_name = row["race"]
                class_name = row["class_name"]
                old_race = V0876_RACE_BASE_STATS.get(race_name, {})
                new_race = new_race_stats.get(race_name, old_race)
                old_class = V0876_CLASS_STARTING_STAT_BONUSES.get(class_name, {})
                new_class = CLASS_STARTING_STAT_BONUSES.get(class_name, old_class)
                deltas = {}
                for stat_name in stat_names:
                    race_delta = 0
                    if stat_name != "charisma":
                        race_delta = int(new_race.get(stat_name, 0)) - int(old_race.get(stat_name, 0))
                    class_delta = int(new_class.get(stat_name, 0)) - int(old_class.get(stat_name, 0))
                    deltas[stat_name] = race_delta + class_delta
                self.conn.execute(
                    "UPDATE characters SET "
                    "strength=MAX(1,strength+?), dexterity=MAX(1,dexterity+?), "
                    "constitution=MAX(1,constitution+?), intelligence=MAX(1,intelligence+?), "
                    "willpower=MAX(1,willpower+?), charisma=MAX(1,charisma+?), "
                    "weapon_base=? WHERE account_id=?",
                    (
                        deltas["strength"], deltas["dexterity"],
                        deltas["constitution"], deltas["intelligence"],
                        deltas["willpower"], deltas["charisma"],
                        int(new_weapon_bases.get(class_name, 7)),
                        int(row["account_id"]),
                    ),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("character_start_balance_v0900",),
            )

        # v0.8.60: jedno wspólne saldo, trzy nominały.
        # Konwersja jest wykonywana dokładnie raz i zachowuje pełną wartość:
        # silver 1:1, gold 1:1000, mithril 1:1_000_000 srebra.
        unified_currency_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("unified_currency_v0859",),
        ).fetchone()
        if not unified_currency_migrated:
            wallet_rows = self.conn.execute(
                "SELECT master_account_id,silver,gold,mithril FROM account_wallet"
            ).fetchall()
            for row in wallet_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                master_id = int(row["master_account_id"])
                self.conn.execute(
                    "UPDATE account_wallet SET silver=?,gold=0,mithril=0,"
                    "updated_at=CURRENT_TIMESTAMP WHERE master_account_id=?",
                    (coins, master_id),
                )
                self.conn.execute(
                    "UPDATE characters SET silver=?,gold=0,mithril=0 "
                    "WHERE account_id IN (SELECT character_account_id "
                    "FROM account_characters WHERE master_account_id=?)",
                    (coins, master_id),
                )

            # Nietypowe stare save'y bez account_wallet też nie tracą środków.
            orphan_rows = self.conn.execute(
                "SELECT account_id,silver,gold,mithril FROM characters "
                "WHERE account_id NOT IN (SELECT character_account_id FROM account_characters)"
            ).fetchall()
            for row in orphan_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                self.conn.execute(
                    "UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?",
                    (coins, int(row["account_id"])),
                )

            bank_rows = self.conn.execute(
                "SELECT account_id,silver,gold,mithril FROM bank_balances"
            ).fetchall()
            for row in bank_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                self.conn.execute(
                    "UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?",
                    (coins, int(row["account_id"])),
                )

            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("unified_currency_v0859",),
            )

        # v0.9.4: Historia postaci / Lifetime Statistics.
        # Odtwarzamy wyłącznie dane, które starsze wersje faktycznie zapisywały.
        # Dokładne ilości ryb/rud/drewna/ziół oraz crafted_items zaczynają się
        # od v0.9.4, ponieważ starsze save'y nie przechowywały pełnej historii sztuk.
        lifetime_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("lifetime_statistics_v094",),
        ).fetchone()
        if not lifetime_migrated:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            production_professions = {"Kowalstwo", "Gotowanie", "Alchemia", "Jubilerstwo"}
            for account_id in character_ids:
                def set_max(key, value):
                    value = max(0, int(value or 0))
                    self.conn.execute(
                        "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
                        "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
                        "value=MAX(lifetime_statistics.value,excluded.value), "
                        "updated_at=CURRENT_TIMESTAMP",
                        (account_id, key, value),
                    )

                bestiary_rows = self.conn.execute(
                    "SELECT mob_template_id,kills FROM bestiary_stats WHERE account_id=?",
                    (account_id,),
                ).fetchall()
                total_kills = sum(max(0, int(row["kills"] or 0)) for row in bestiary_rows)
                boss_kills = 0
                rare_kills = 0
                for row in bestiary_rows:
                    mob_id = str(row["mob_template_id"])
                    kills = max(0, int(row["kills"] or 0))
                    template = MOB_TEMPLATES.get(mob_id, {})
                    if mob_id in BOSS_COLLECTION_CATALOG:
                        boss_kills += kills
                    if template.get("rare_mob"):
                        rare_kills += kills

                metrics = {
                    str(row["metric"]): max(0, int(row["value"] or 0))
                    for row in self.conn.execute(
                        "SELECT metric,value FROM achievement_progress WHERE account_id=?",
                        (account_id,),
                    ).fetchall()
                }
                set_max("kills_total", total_kills)
                set_max("combat_victories", total_kills)
                set_max("boss_kills", max(boss_kills, metrics.get("boss_kills", 0)))
                set_max("rare_kills", max(rare_kills, metrics.get("rare_kills", 0)))
                set_max("rare_fish_caught", metrics.get("rare_fish_caught", 0))
                set_max("gems_found", metrics.get("gems_found", 0))

                char_row = self.conn.execute(
                    "SELECT deaths FROM characters WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("deaths", int(char_row["deaths"] or 0) if char_row else 0)

                quest_row = self.conn.execute(
                    "SELECT COALESCE(SUM(completion_count),0) AS total FROM quests WHERE account_id=?",
                    (account_id,),
                ).fetchone()
                set_max("quests_completed", int(quest_row["total"] or 0) if quest_row else 0)

                bounty_row = self.conn.execute(
                    "SELECT completed_count FROM bounty_boards WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("bounties_completed", int(bounty_row["completed_count"] or 0) if bounty_row else 0)

                profession_rows = self.conn.execute(
                    "SELECT profession,actions FROM professions WHERE account_id=?", (account_id,)
                ).fetchall()
                profession_actions = sum(max(0, int(row["actions"] or 0)) for row in profession_rows)
                craft_actions = sum(
                    max(0, int(row["actions"] or 0))
                    for row in profession_rows if str(row["profession"]) in production_professions
                )
                set_max("profession_actions", profession_actions)
                set_max("craft_actions", craft_actions)

                explored = self.conn.execute(
                    "SELECT COUNT(*) AS total FROM exploration_rooms WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("rooms_discovered", int(explored["total"] or 0) if explored else 0)
                unique_bestiary = len({str(row["mob_template_id"]) for row in bestiary_rows})
                set_max("bestiary_unique", unique_bestiary)

            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("lifetime_statistics_v094",),
            )

        # v0.9.5: Dziennik ryb. Starszy zapis potrafi pewnie potwierdzić tylko
        # gatunki nadal obecne w Siatce. Seedujemy je raz; rekordy rozmiaru i
        # pełny licznik połowów są dokładne od v0.9.5.
        fish_journal_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("fish_journal_v095",),
        ).fetchone()
        if not fish_journal_migrated:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            for account_id in character_ids:
                rows = self.conn.execute(
                    "SELECT item_id,quantity FROM profession_storage "
                    "WHERE account_id=? AND container='net' AND quantity>0",
                    (account_id,),
                ).fetchall()
                seeded_counts = {}
                for row in rows:
                    item_id = str(row["item_id"])
                    base_id = base_fish_species_id(item_id)
                    if base_id not in FISH_RESOURCE_IDS:
                        continue
                    qty = max(1, int(row["quantity"] or 0))
                    seeded_counts[base_id] = seeded_counts.get(base_id, 0) + qty
                for base_id, qty in seeded_counts.items():
                    self.conn.execute(
                        "INSERT OR IGNORE INTO fish_journal("
                        "account_id,fish_id,caught_count,best_length_mm,best_weight_g,first_room_id,last_room_id"
                        ") VALUES(?,?,?,0,0,'','')",
                        (account_id, base_id, qty),
                    )
                self.conn.execute(
                    "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
                    "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
                    "value=MAX(lifetime_statistics.value,excluded.value),updated_at=CURRENT_TIMESTAMP",
                    (account_id, "fish_species_discovered", len(seeded_counts)),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("fish_journal_v095",),
            )

        # v0.9.6: rozszerzony Collection Codex. Seedujemy tylko dane, które
        # poprzednie wersje potrafią pewnie potwierdzić: Dziennik ryb,
        # bossów z Bestiariusza, istniejący Rare Codex oraz przedmioty nadal
        # posiadane w inventory/storage.
        collection_v096 = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("collections_v096",),
        ).fetchone()
        if not collection_v096:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            for account_id in character_ids:
                for row in self.conn.execute(
                    "SELECT fish_id FROM fish_journal WHERE account_id=?", (account_id,)
                ).fetchall():
                    fish_id = str(row["fish_id"])
                    if fish_id in FISH_COLLECTION_CATALOG:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, "fish", fish_id),
                        )

                for row in self.conn.execute(
                    "SELECT mob_template_id FROM bestiary_stats WHERE account_id=? AND kills>0",
                    (account_id,),
                ).fetchall():
                    mob_id = canonical_bestiary_template_id(row["mob_template_id"])
                    if mob_id in BOSS_COLLECTION_CATALOG:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, "bosses", mob_id),
                        )

                owned_ids = set()
                for row in self.conn.execute(
                    "SELECT item_id FROM inventory WHERE account_id=? AND quantity>0", (account_id,)
                ).fetchall():
                    owned_ids.add(str(row["item_id"]))
                for row in self.conn.execute(
                    "SELECT item_id FROM profession_storage WHERE account_id=? AND quantity>0", (account_id,)
                ).fetchall():
                    owned_ids.add(str(row["item_id"]))
                for item_id in owned_ids:
                    base_id = canonical_profession_resource_id(item_id)
                    categories = []
                    if base_id in MINERAL_COLLECTION_CATALOG: categories.append(("minerals", base_id))
                    if base_id in HERB_COLLECTION_CATALOG: categories.append(("herbs", base_id))
                    if base_id in MATERIAL_COLLECTION_CATALOG: categories.append(("materials", base_id))
                    if item_id in GEM_COLLECTION_CATALOG: categories.append(("gems", item_id))
                    if item_id in UNIQUE_ITEM_COLLECTION_CATALOG: categories.append(("unique", item_id))
                    for category, entry_id in categories:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, category, entry_id),
                        )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("collections_v096",),
            )

        # v0.9.11: v0.9.10 przez krótki czas dawało darmowe klasowe EQ
        # przy tworzeniu postaci. Nowa zasada usuwa te wyłącznie startowe
        # przedmioty również ze starych zapisów, bez dotykania kupionego/zdobytego EQ.
        starter_eq_removed = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("remove_class_starter_equipment_v0911",),
        ).fetchone()
        if not starter_eq_removed:
            self.conn.execute(
                "DELETE FROM equipment_gems WHERE EXISTS ("
                "SELECT 1 FROM equipment e "
                "WHERE e.account_id=equipment_gems.account_id "
                "AND e.slot=equipment_gems.slot "
                "AND e.item_id LIKE 'starter_%'"
                ")"
            )
            self.conn.execute(
                "DELETE FROM equipment WHERE item_id LIKE 'starter_%'"
            )
            self.conn.execute(
                "DELETE FROM inventory WHERE item_id LIKE 'starter_%'"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("remove_class_starter_equipment_v0911",),
            )

        self.conn.commit()

    def account_name(self, account_id):
        row = self.conn.execute(
            "SELECT username FROM accounts WHERE id=?", (int(account_id),)
        ).fetchone()
        return str(row["username"]) if row else ""

    def wipe_characters_for_master(self, master_account_id):
        """Usuń postacie/progres konta, ale zachowaj login i hasło konta."""
        master_account_id = int(master_account_id)
        rows = self.conn.execute(
            "SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot",
            (master_account_id,),
        ).fetchall()
        char_ids = [int(row["character_account_id"]) for row in rows]

        # Ukryte konta profili można bezpiecznie usunąć — FK CASCADE czyści ich dane.
        for char_id in char_ids:
            if char_id != master_account_id:
                self.conn.execute("DELETE FROM accounts WHERE id=?", (char_id,))

        # Pierwsza postać może używać ID konta głównego, więc kasujemy jej dane,
        # ale nigdy rekordu logowania w accounts.
        if master_account_id in char_ids:
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )

        self.conn.execute(
            "DELETE FROM account_characters WHERE master_account_id=?",
            (master_account_id,),
        )
        # Portfel jest częścią postępu gry, nie danych logowania. Nowa pierwsza
        # postać ponownie dostanie normalny pakiet startowy.
        self.conn.execute(
            "DELETE FROM account_wallet WHERE master_account_id=?",
            (master_account_id,),
        )
        self.conn.commit()
        return len(char_ids)

    def delete_character_for_master(self, master_account_id, character_account_id):
        """v0.9.1: usuń dokładnie jedną postać bez kasowania konta ani wspólnego portfela.

        Pierwsza postać może używać ID konta głównego, dlatego nie wolno wtedy
        usuwać rekordu z accounts. Dodatkowe postacie mają ukryte konta techniczne
        i ich usunięcie przez FK CASCADE czyści cały własny progres postaci.
        """
        master_account_id = int(master_account_id)
        character_account_id = int(character_account_id)
        row = self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.name
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? AND ac.character_account_id=?
            """,
            (master_account_id, character_account_id),
        ).fetchone()
        if not row:
            return None

        slot = int(row["slot"])
        name = str(row["name"])

        if character_account_id != master_account_id:
            # Ukryty profil postaci. Usunięcie konta technicznego uruchamia
            # ON DELETE CASCADE dla całego progresu i samego powiązania slotu.
            self.conn.execute(
                "DELETE FROM accounts WHERE id=?", (character_account_id,)
            )
        else:
            # Slot oparty na koncie głównym: zachowujemy login, hasło i
            # account_wallet, a czyścimy wyłącznie dane tej postaci.
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND character_account_id=?",
                (master_account_id, character_account_id),
            )

        self.conn.commit()
        return {"slot": slot, "name": name}

    def wipe_all_characters_preserve_accounts(self):
        masters = [
            int(row["id"])
            for row in self.conn.execute(
                "SELECT id FROM accounts WHERE id NOT IN ("
                "SELECT character_account_id FROM account_characters "
                "WHERE character_account_id<>master_account_id) ORDER BY id"
            ).fetchall()
        ]
        removed = 0
        for master_id in masters:
            removed += self.wipe_characters_for_master(master_id)
        return removed, masters

    def master_accounts(self):
        """v0.30.1: lista prawdziwych kont logowania, bez ukrytych profili postaci."""
        return self.conn.execute(
            """
            SELECT a.id,a.username,COUNT(ac.character_account_id) AS character_count
            FROM accounts a
            LEFT JOIN account_characters ac ON ac.master_account_id=a.id
            WHERE a.id NOT IN (
                SELECT character_account_id FROM account_characters
                WHERE character_account_id<>master_account_id
            )
            GROUP BY a.id,a.username
            ORDER BY a.username COLLATE NOCASE,a.id
            """
        ).fetchall()

    def master_account_by_name(self, username):
        """v0.30.1: znajdź tylko konto główne; profil techniczny postaci nie jest celem admina."""
        return self.conn.execute(
            """
            SELECT a.* FROM accounts a
            WHERE a.username=? COLLATE NOCASE
              AND a.id NOT IN (
                  SELECT character_account_id FROM account_characters
                  WHERE character_account_id<>master_account_id
              )
            """,
            (username,),
        ).fetchone()

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def is_character_profile(self, account_id):
        row = self.conn.execute(
            "SELECT 1 FROM account_characters "
            "WHERE character_account_id=? AND master_account_id<>character_account_id",
            (account_id,),
        ).fetchone()
        return row is not None

    def master_account_for_character(self, character_account_id):
        row = self.conn.execute(
            "SELECT master_account_id FROM account_characters "
            "WHERE character_account_id=?",
            (character_account_id,),
        ).fetchone()
        if row:
            return int(row["master_account_id"])
        return int(character_account_id)

    def shared_wallet_for_master(self, master_account_id):
        master_account_id = int(master_account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM account_wallet "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        if row:
            silver, gold, mithril = normalize_currency_values(
                row["silver"], row["gold"], row["mithril"]
            )
            if gold or mithril or silver != int(row["silver"]):
                self.set_shared_wallet_for_master(
                    master_account_id, silver, gold, mithril
                )
            return (silver, gold, mithril)

        # Bezpieczny fallback dla świeżego konta albo nietypowego starego save'a.
        sums = self.conn.execute(
            """
            SELECT COALESCE(SUM(c.silver),0) AS silver,
                   COALESCE(SUM(c.gold),0) AS gold,
                   COALESCE(SUM(c.mithril),0) AS mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            """,
            (master_account_id,),
        ).fetchone()
        silver, gold, mithril = normalize_currency_values(
            int(sums["silver"] or 0), int(sums["gold"] or 0), int(sums["mithril"] or 0)
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO account_wallet("
            "master_account_id,silver,gold,mithril,updated_at"
            ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (master_account_id, silver, gold, mithril),
        )
        self.conn.commit()
        return silver, gold, mithril

    def shared_wallet_for_character(self, character_account_id):
        return self.shared_wallet_for_master(
            self.master_account_for_character(character_account_id)
        )

    def set_shared_wallet_for_master(self, master_account_id, silver, gold, mithril, *, commit=True):
        master_account_id = int(master_account_id)
        silver, gold, mithril = normalize_currency_values(silver, gold, mithril)
        self.conn.execute(
            """
            INSERT INTO account_wallet(master_account_id,silver,gold,mithril,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(master_account_id) DO UPDATE SET
                silver=excluded.silver,
                gold=excluded.gold,
                mithril=excluded.mithril,
                updated_at=CURRENT_TIMESTAMP
            """,
            (master_account_id, silver, gold, mithril),
        )
        # Trzymamy kolumny legacy zsynchronizowane, żeby wszystkie starsze
        # fragmenty gry i narzędzia administracyjne widziały to samo saldo.
        self.conn.execute(
            """
            UPDATE characters SET silver=?,gold=?,mithril=?
            WHERE account_id IN (
                SELECT character_account_id FROM account_characters
                WHERE master_account_id=?
            )
            """,
            (silver, gold, mithril, master_account_id),
        )
        if commit:
            self.conn.commit()
        return silver, gold, mithril

    def set_shared_wallet_for_character(self, character_account_id, silver, gold, mithril, *, commit=True):
        return self.set_shared_wallet_for_master(
            self.master_account_for_character(character_account_id),
            silver, gold, mithril, commit=commit,
        )

    def apply_shared_wallet_to_character(self, character):
        silver, gold, mithril = self.shared_wallet_for_character(character.account_id)
        character.silver = silver
        character.gold = gold
        character.mithril = mithril
        return character

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def characters_for_master(self, master_account_id):
        return self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.*
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot
            """,
            (master_account_id,),
        ).fetchall()

    def character_count_for_master(self, master_account_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM account_characters "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        return int(row["n"] or 0) if row else 0

    def _next_character_slot(self, master_account_id):
        used = {
            int(r["slot"]) for r in self.conn.execute(
                "SELECT slot FROM account_characters WHERE master_account_id=?",
                (master_account_id,),
            ).fetchall()
        }
        for slot in range(1, MAX_CHARACTERS_PER_ACCOUNT + 1):
            if slot not in used:
                return slot
        return None

    def _create_hidden_character_account(self, master_account_id, slot):
        # Profil jest wyłącznie technicznym kluczem danych postaci. Nie można
        # zalogować się do niego z ekranu logowania.
        while True:
            username = f"__char_{master_account_id}_{slot}_{secrets.token_hex(6)}"
            if not self.account_by_name(username):
                break
        salt, digest = hash_password(secrets.token_urlsafe(32))
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        return int(cur.lastrowid)

    def create_character_for_master(self, master_account_id, name, race, cls, name_cases):
        if self.character_count_for_master(master_account_id) >= MAX_CHARACTERS_PER_ACCOUNT:
            raise ValueError("character_limit")

        slot = self._next_character_slot(master_account_id)
        if slot is None:
            raise ValueError("character_limit")

        existing_master_character = self.character_for_account(master_account_id)
        master_link = self.conn.execute(
            "SELECT 1 FROM account_characters WHERE character_account_id=?",
            (master_account_id,),
        ).fetchone()

        if slot == 1 and not existing_master_character and not master_link:
            character_account_id = int(master_account_id)
        else:
            character_account_id = self._create_hidden_character_account(
                master_account_id, slot
            )

        self.conn.execute(
            "INSERT INTO account_characters(master_account_id,character_account_id,slot) "
            "VALUES(?,?,?)",
            (master_account_id, character_account_id, slot),
        )
        try:
            self.create_character(
                character_account_id, name, race, cls, name_cases
            )
            wallet_row = self.conn.execute(
                "SELECT silver,gold,mithril FROM account_wallet "
                "WHERE master_account_id=?",
                (master_account_id,),
            ).fetchone()
            if wallet_row is None:
                # Pierwsza postać zakłada wspólny portfel z pakietem startowym.
                created = self.character_for_account(character_account_id)
                self.set_shared_wallet_for_master(
                    master_account_id,
                    created["silver"], created["gold"], created["mithril"],
                )
            else:
                # Każda następna postać dostaje dokładnie saldo konta,
                # bez ponownego przyznawania startowych monet.
                self.set_shared_wallet_for_master(
                    master_account_id,
                    wallet_row["silver"], wallet_row["gold"], wallet_row["mithril"],
                )
        except Exception:
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND slot=?",
                (master_account_id, slot),
            )
            if character_account_id != master_account_id:
                self.conn.execute(
                    "DELETE FROM accounts WHERE id=?", (character_account_id,)
                )
            self.conn.commit()
            raise
        return character_account_id, slot

    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def character_account_id_by_name_v0928(self, name):
        row = self.conn.execute(
            "SELECT account_id FROM characters WHERE name=? COLLATE NOCASE",
            (str(name or "").strip(),),
        ).fetchone()
        return int(row["account_id"]) if row else None

    def character_name_by_account_v0928(self, account_id):
        row = self.conn.execute(
            "SELECT name FROM characters WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        return str(row["name"]) if row else None

    def are_friends_v0928(self, account_id, friend_account_id):
        return self.conn.execute(
            "SELECT 1 FROM player_friends_v0928 WHERE account_id=? AND friend_account_id=?",
            (int(account_id), int(friend_account_id)),
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases):
        rname, _, _race_strength, _race_dexterity, _race_constitution, _race_intelligence, _race_willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        starting_stats = class_starting_stats_for(race, cls)
        strength = starting_stats["strength"]
        dexterity = starting_stats["dexterity"]
        constitution = starting_stats["constitution"]
        intelligence = starting_stats["intelligence"]
        willpower = starting_stats["willpower"]
        charisma = starting_stats["charisma"]
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,charisma,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',?,?,?,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower, charisma,
                STARTING_SILVER, STARTING_GOLD, STARTING_MITHRIL,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        if rname == "Cyborg":
            self.conn.execute(
                "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
                (account_id, "moogle_board", 1),
            )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()

    def save_character(self, c):
        (
            c.silver,
            c.gold,
            c.mithril,
        ) = normalize_currency_values(
            c.silver,
            c.gold,
            c.mithril,
        )

        # v0.8.32: waluta należy do konta głównego, nie do slotu postaci.
        self.set_shared_wallet_for_character(
            c.account_id, c.silver, c.gold, c.mithril, commit=False
        )

        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, strength_progress=?, dexterity_progress=?,
                constitution_progress=?, intelligence_progress=?, willpower_progress=?,
                charisma_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?,
                silver=?, gold=?, mithril=?, charisma=?, character_level=?, character_xp=?, deaths=?,
                guild_reputation_json=?, guild_exams_json=?,
                guild_class_quests_json=?, guild_bounty_json=?,
                loot_filter=?, active_title=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                min(c.strength_progress, c.dexterity_progress, c.constitution_progress,
                    c.intelligence_progress, c.willpower_progress, c.charisma_progress),
                c.strength_progress, c.dexterity_progress, c.constitution_progress,
                c.intelligence_progress, c.willpower_progress, c.charisma_progress,
                c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.character_level, c.character_xp, c.deaths,
                c.guild_reputation_json, c.guild_exams_json,
                c.guild_class_quests_json, c.guild_bounty_json,
                c.loot_filter, c.active_title,
                c.account_id,
            ),
        )
        self.conn.commit()

    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_crypt_boss_floor(floor):
            return self.crypt_checkpoint(account_id)

        current = self.crypt_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                "UPDATE characters SET crypt_checkpoint=? "
                "WHERE account_id=?",
                (new_value, account_id),
            )
            self.conn.commit()
        return new_value

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = crypt_floor_number(room_id)
        if floor is None:
            return self.crypt_checkpoint(account_id)

        # Stara postać stojąca na piętrze N musiała wcześniej przejść
        # wszystkie bossy poniżej N. Nie zaliczamy bossa bieżącego piętra.
        safe_floor = ((max(1, floor) - 1) // 10) * 10
        if safe_floor >= 10:
            return self.unlock_crypt_checkpoint(account_id, safe_floor)
        return self.crypt_checkpoint(account_id)

    def crypt_portal(self, account_id):
        return self.crypt_checkpoint(account_id)

    def unlock_crypt_portal(self, account_id, floor):
        return self.unlock_crypt_checkpoint(account_id, floor)

    def astral_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT checkpoint FROM astral_progress WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["checkpoint"] or 0) if row else 0

    def unlock_astral_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_astral_boss_floor(floor):
            return self.astral_checkpoint(account_id)

        current = self.astral_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                """
                INSERT INTO astral_progress(account_id,checkpoint)
                VALUES(?,?)
                ON CONFLICT(account_id)
                DO UPDATE SET checkpoint=excluded.checkpoint
                """,
                (account_id, new_value),
            )
            self.conn.commit()
        return new_value

    def astral_portal(self, account_id):
        return self.astral_checkpoint(account_id)

    def unlock_astral_portal(self, account_id, floor):
        return self.unlock_astral_checkpoint(account_id, floor)

    def boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        # Zgodność starych save'ów: checkpoint Krypty/Wieży oznacza, że wszystkie
        # wcześniejsze bossy co 10 zostały już kiedyś pokonane.
        if dungeon_kind == "crypt" and floor <= self.crypt_checkpoint(account_id):
            return True
        if dungeon_kind == "astral" and floor <= self.astral_checkpoint(account_id):
            return True
        row = self.conn.execute(
            "SELECT 1 FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=? AND floor=?",
            (account_id, dungeon_kind, floor),
        ).fetchone()
        return bool(row)

    def mark_boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_floor_clears(account_id,dungeon_kind,floor) VALUES(?,?,?)",
            (account_id, dungeon_kind, floor),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def ensure_mine_progress(self, account_id):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO mine_progress(
                account_id,max_floor_unlocked,wall_hits,wall_required_hits
            ) VALUES(?,1,0,0)
            """,
            (account_id,),
        )
        self.conn.commit()

    def mine_progress(self, account_id):
        self.ensure_mine_progress(account_id)
        row = self.conn.execute(
            """
            SELECT max_floor_unlocked,wall_hits,wall_required_hits
            FROM mine_progress
            WHERE account_id=?
            """,
            (account_id,),
        ).fetchone()
        highest = max(
            MINE_MIN_FLOOR,
            int(row["max_floor_unlocked"]),
        )
        hits = max(0, int(row["wall_hits"]))
        required_hits = max(0, int(row["wall_required_hits"]))

        # Stare zapisy nie miały losowego progu. Losujemy go raz
        # dla aktualnej ściany i zapisujemy, aby restart niczego nie zmieniał.
        if required_hits <= hits:
            required_hits = roll_mine_wall_hits_required(highest, hits)
            self.conn.execute(
                "UPDATE mine_progress SET wall_required_hits=? WHERE account_id=?",
                (required_hits, account_id),
            )
            self.conn.commit()

        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
        }

    def add_mine_wall_hit(self, account_id, floor):
        floor = int(floor)
        progress = self.mine_progress(account_id)
        highest = progress["max_floor_unlocked"]
        hits = progress["wall_hits"]
        required_hits = progress["wall_required_hits"]

        if floor != highest:
            return {
                "max_floor_unlocked": highest,
                "wall_hits": hits,
                "wall_required_hits": required_hits,
                "unlocked_floor": None,
            }

        hits += 1
        unlocked_floor = None
        if hits >= required_hits:
            highest = highest + 1
            hits = 0
            unlocked_floor = highest
            required_hits = roll_mine_wall_hits_required(highest, 0)

        self.conn.execute(
            """
            UPDATE mine_progress
            SET max_floor_unlocked=?, wall_hits=?, wall_required_hits=?
            WHERE account_id=?
            """,
            (highest, hits, required_hits, account_id),
        )
        self.conn.commit()
        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
            "unlocked_floor": unlocked_floor,
        }

    def reset_mine_for_server_start(self):
        """v0.30.35: reset Kopalni Głębinowej przy każdym starcie procesu/deployu.

        Reset dotyczy wyłącznie wspólnego stanu przejścia Kopalni: odblokowanej
        głębokości oraz postępu bieżącej ściany. Nie dotyka Górnictwa, Kilofa,
        surowców, EQ, questów ani żadnej progresji postaci. Postacie zapisane
        wewnątrz dynamicznych pięter są przenoszone do wejścia, żeby po resecie
        nie pozostawały poniżej ponownie zamkniętej ściany.
        """
        progress_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM mine_progress"
        ).fetchone()["n"] or 0)
        moved_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM characters WHERE room_id LIKE 'mine_floor_%'"
        ).fetchone()["n"] or 0)
        self.conn.execute(
            "UPDATE mine_progress SET max_floor_unlocked=?, wall_hits=0, wall_required_hits=0",
            (MINE_MIN_FLOOR,),
        )
        self.conn.execute(
            "UPDATE characters SET room_id='crystal_chamber' WHERE room_id LIKE 'mine_floor_%'"
        )
        self.conn.commit()
        return {
            "progress_rows_reset": progress_rows,
            "characters_moved_to_entrance": moved_rows,
            "max_floor_unlocked": MINE_MIN_FLOOR,
            "wall_hits": 0,
        }

    def ensure_bank(self, account_id):
        # v0.8.32: waluta Banku Dusz jest również wspólna dla całego konta.
        currency_account_id = self.master_account_for_character(account_id)
        self.conn.execute(
            "INSERT OR IGNORE INTO bank_balances("
            "account_id,silver,gold,mithril"
            ") VALUES(?,0,0,0)",
            (currency_account_id,),
        )
        self.conn.commit()
        return currency_account_id

    def bank_balance(self, account_id):
        currency_account_id = self.ensure_bank(account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM bank_balances "
            "WHERE account_id=?",
            (currency_account_id,),
        ).fetchone()

        silver, gold, mithril = normalize_currency_values(
            row["silver"],
            row["gold"],
            row["mithril"],
        )

        if (
            silver != int(row["silver"])
            or gold != int(row["gold"])
            or mithril != int(row["mithril"])
        ):
            self.conn.execute(
                "UPDATE bank_balances "
                "SET silver=?, gold=?, mithril=? "
                "WHERE account_id=?",
                (silver, gold, mithril, currency_account_id),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT silver,gold,mithril FROM bank_balances "
                "WHERE account_id=?",
                (currency_account_id,),
            ).fetchone()

        return row

    def change_bank_currency(self, account_id, currency, amount):
        if currency not in ("silver", "gold", "mithril"):
            raise ValueError("Nieznana waluta bankowa.")

        currency_account_id = self.master_account_for_character(account_id)
        row = self.bank_balance(account_id)
        values = {
            "silver": int(row["silver"]),
            "gold": int(row["gold"]),
            "mithril": int(row["mithril"]),
        }
        values[currency] += int(amount)

        if values[currency] < 0:
            return False

        silver, gold, mithril = normalize_currency_values(
            values["silver"],
            values["gold"],
            values["mithril"],
        )

        self.conn.execute(
            "UPDATE bank_balances "
            "SET silver=?, gold=?, mithril=? "
            "WHERE account_id=?",
            (silver, gold, mithril, currency_account_id),
        )
        self.conn.commit()
        return True

    def bank_items(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM bank_items "
            "WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def bank_item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM bank_items "
            "WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        self.conn.execute(
            """
            INSERT INTO bank_items(account_id,item_id,quantity)
            VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        current = self.bank_item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM bank_items "
                "WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE bank_items SET quantity=? "
                "WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def persisted_crafting_quality_item_ids_v0332(self):
        found=set()
        tables=self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table_row in tables:
            table=str(table_row[0])
            if not table.replace("_","").isalnum():
                continue
            try:
                cols=[str(row[1]) for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
            except Exception:
                continue
            for col in cols:
                if col not in ("item_id","jewelry_item_id"):
                    continue
                try:
                    rows=self.conn.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} LIKE 'craftq_%'").fetchall()
                    found.update(str(row[0]) for row in rows if row[0])
                except Exception:
                    pass
        return sorted(found)

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        # v0.9.15: materiały rzemieślnicze nigdy nie zapychają zwykłego
        # inventory. Każde źródło używające add_item automatycznie kieruje
        # je do Szkatułki Rzemieślniczej.
        if item_id in CRAFT_MATERIAL_STORAGE_IDS:
            self.add_storage_item(account_id, "craftbox", item_id, qty)
            return
        self.conn.execute(
            """
            INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def mark_room_discovered(self, account_id, room_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)",
            (account_id, room_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def discovered_room_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT room_id FROM exploration_rooms WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["room_id"]) for row in rows}

    def claim_exploration_reward(self, account_id, zone):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rewards(account_id,zone) VALUES(?,?)",
            (account_id, zone),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def exploration_reward_claimed(self, account_id, zone):
        row = self.conn.execute(
            "SELECT 1 FROM exploration_rewards WHERE account_id=? AND zone=?",
            (account_id, zone),
        ).fetchone()
        return bool(row)

    def record_bestiary_kill(self, account_id, mob_template_id, kill_ms=None):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
        previous = self.conn.execute(
            "SELECT kills,fastest_kill_ms FROM bestiary_stats "
            "WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()
        is_new = previous is None
        old_fastest = int(previous["fastest_kill_ms"]) if previous and previous["fastest_kill_ms"] is not None else None
        clean_ms = None
        if kill_ms is not None:
            try:
                clean_ms = max(1, int(kill_ms))
            except (TypeError, ValueError):
                clean_ms = None
        self.conn.execute(
            """
            INSERT INTO bestiary_stats(
                account_id,mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at
            ) VALUES(?,?,1,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,mob_template_id) DO UPDATE SET
                kills=bestiary_stats.kills+1,
                fastest_kill_ms=CASE
                    WHEN excluded.fastest_kill_ms IS NULL THEN bestiary_stats.fastest_kill_ms
                    WHEN bestiary_stats.fastest_kill_ms IS NULL THEN excluded.fastest_kill_ms
                    WHEN excluded.fastest_kill_ms < bestiary_stats.fastest_kill_ms THEN excluded.fastest_kill_ms
                    ELSE bestiary_stats.fastest_kill_ms
                END,
                last_killed_at=CURRENT_TIMESTAMP
            """,
            (account_id, mob_template_id, clean_ms),
        )
        self.conn.commit()
        row = self.bestiary_entry(account_id, mob_template_id)
        new_fastest = row["fastest_kill_ms"] if row else None
        is_record = (
            clean_ms is not None
            and new_fastest == clean_ms
            and (old_fastest is None or clean_ms < old_fastest)
        )
        return row, is_new, is_record

    def bestiary_entry(self, account_id, mob_template_id):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()

    def bestiary_rows(self, account_id):
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? ORDER BY kills DESC,mob_template_id",
            (account_id,),
        ).fetchall()

    def record_boss_codex_kill(self, account_id, boss_id, grouped=False):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG:
            return None
        solo_inc = 0 if grouped else 1
        group_inc = 1 if grouped else 0
        self.conn.execute(
            "INSERT INTO boss_codex_stats(account_id,boss_id,solo_kills,group_kills) VALUES(?,?,?,?) "
            "ON CONFLICT(account_id,boss_id) DO UPDATE SET "
            "solo_kills=boss_codex_stats.solo_kills+excluded.solo_kills, "
            "group_kills=boss_codex_stats.group_kills+excluded.group_kills",
            (account_id, boss_id, solo_inc, group_inc),
        )
        self.conn.commit()
        return self.boss_codex_stats(account_id, boss_id)

    def boss_codex_stats(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        return self.conn.execute(
            "SELECT boss_id,solo_kills,group_kills FROM boss_codex_stats "
            "WHERE account_id=? AND boss_id=?",
            (account_id, boss_id),
        ).fetchone()

    def add_boss_codex_drop(self, account_id, boss_id, item_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG or item_id not in ITEMS:
            return False
        if not boss_codex_drop_is_unique(item_id):
            return False
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_codex_drops(account_id,boss_id,item_id) VALUES(?,?,?)",
            (account_id, boss_id, item_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def boss_codex_drops(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        rows = self.conn.execute(
            "SELECT item_id,discovered_at FROM boss_codex_drops "
            "WHERE account_id=? AND boss_id=? ORDER BY discovered_at,item_id",
            (account_id, boss_id),
        ).fetchall()
        return rows

    def add_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def collection_entry_ids(self, account_id, category):
        rows = self.conn.execute(
            "SELECT entry_id FROM collection_codex WHERE account_id=? AND category=?",
            (account_id, category),
        ).fetchall()
        return {str(row["entry_id"]) for row in rows}

    def remove_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "DELETE FROM collection_codex WHERE account_id=? AND category=? AND entry_id=?",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # v0.29.0: jeden aktywny Nemesis na konto. Rekord jest trwały i
    # bezpiecznie przechodzi przez restarty serwera.
    def nemesis_row_v029(self, account_id):
        return self.conn.execute(
            "SELECT * FROM nemesis_v029 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

    def promote_nemesis_v029(self, account_id, base_template_id, base_name, player_name, level, room_id):
        account_id = int(account_id)
        previous = self.nemesis_row_v029(account_id)
        same = bool(previous and int(previous["active"] or 0) and str(previous["base_template_id"]) == str(base_template_id))
        rank = min(10, (int(previous["rank"] or 1) + 1) if same else 1)
        kills = (int(previous["kills_player"] or 0) + 1) if same else 1
        defeats = int(previous["defeats"] or 0) if previous else 0
        stage = max(1, min(400, int(level or 1) + (rank - 1) * 8))
        name = dynamic_world_v029.nemesis_name(str(base_name), account_id, str(player_name), rank)
        self.conn.execute(
            "INSERT INTO nemesis_v029(account_id,base_template_id,nemesis_name,rank,level,room_id,kills_player,defeats,active,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP) "
            "ON CONFLICT(account_id) DO UPDATE SET base_template_id=excluded.base_template_id,nemesis_name=excluded.nemesis_name,"
            "rank=excluded.rank,level=excluded.level,room_id=excluded.room_id,kills_player=excluded.kills_player,defeats=excluded.defeats,"
            "active=1,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(base_template_id), name, rank, stage, str(room_id), kills, defeats),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)

    def defeat_nemesis_v029(self, account_id):
        row = self.nemesis_row_v029(account_id)
        if not row:
            return None
        self.conn.execute(
            "UPDATE nemesis_v029 SET active=0,defeats=defeats+1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
            (int(account_id),),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)


    # v0.21.0: trwała progresja po capie 400, World Tier i Endless Gauntlet.
    def ascension_row_v021(self, account_id, track):
        track=str(track or "")
        self.conn.execute(
            "INSERT OR IGNORE INTO ascension_progress_v021(account_id,track,rank,xp) VALUES(?,?,0,0)",
            (account_id,track),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? AND track=?",
            (account_id,track),
        ).fetchone()

    def add_ascension_xp_v021(self, account_id, track, amount):
        row=self.ascension_row_v021(account_id,track)
        rank=max(0,int(row["rank"] or 0)); xp=max(0,int(row["xp"] or 0)); gain=max(0,int(amount or 0))
        xp=min(V019_SAFE_INT,xp+gain); ups=0
        while rank < V021_ASCENSION_MAX_RANK:
            needed=v0210_ascension_xp_to_next(rank)
            if needed<=0 or xp<needed: break
            xp-=needed; rank+=1; ups+=1
        if rank>=V021_ASCENSION_MAX_RANK:
            rank=V021_ASCENSION_MAX_RANK; xp=0
        self.conn.execute(
            "UPDATE ascension_progress_v021 SET rank=?,xp=? WHERE account_id=? AND track=?",
            (rank,xp,account_id,str(track)),
        ); self.conn.commit()
        return {"track":str(track),"rank":rank,"xp":xp,"rank_ups":ups,"gain":gain,"next_xp":v0210_ascension_xp_to_next(rank)}

    def ascension_rows_v021(self, account_id):
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? ORDER BY rank DESC,track",
            (account_id,),
        ).fetchall()

    def world_tier_v021(self, account_id):
        self.conn.execute("INSERT OR IGNORE INTO world_tier_settings_v021(account_id,tier) VALUES(?,1)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT tier FROM world_tier_settings_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(1,min(V021_WORLD_TIER_MAX,int(row["tier"] if row else 1)))

    def set_world_tier_v021(self, account_id, tier):
        tier=max(1,min(V021_WORLD_TIER_MAX,int(tier)))
        self.conn.execute(
            "INSERT INTO world_tier_settings_v021(account_id,tier) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET tier=excluded.tier",
            (account_id,tier),
        ); self.conn.commit(); return tier

    def endless_gauntlet_best_v021(self, account_id):
        self.conn.execute("INSERT OR IGNORE INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,0)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT best_round FROM endless_gauntlet_progress_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(0,int(row["best_round"] if row else 0))

    def mark_endless_gauntlet_round_v021(self, account_id, round_no):
        round_no=max(0,int(round_no))
        self.conn.execute(
            "INSERT INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET best_round=MAX(best_round,excluded.best_round)",
            (account_id,round_no),
        ); self.conn.commit(); return self.endless_gauntlet_best_v021(account_id)

    # v0.9.21: trwała mapa instancji, sekrety i checkpointy.
    def mark_instance_floor_visited(self, account_id, instance_kind, floor):
        instance_kind = str(instance_kind or "")
        floor = max(1, int(floor))
        previous = self.conn.execute(
            "SELECT 1 FROM instance_map_progress WHERE account_id=? AND instance_kind=? AND floor=?",
            (account_id, instance_kind, floor),
        ).fetchone()
        self.conn.execute(
            "INSERT INTO instance_map_progress(account_id,instance_kind,floor) VALUES(?,?,?) "
            "ON CONFLICT(account_id,instance_kind,floor) DO UPDATE SET last_visited_at=CURRENT_TIMESTAMP",
            (account_id, instance_kind, floor),
        )
        self.conn.commit()
        return previous is None

    def instance_visited_floors(self, account_id, instance_kind):
        rows = self.conn.execute(
            "SELECT floor FROM instance_map_progress WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()
        return {int(row["floor"]) for row in rows}

    def instance_highest_floor(self, account_id, instance_kind):
        row = self.conn.execute(
            "SELECT MAX(floor) AS floor FROM instance_map_progress WHERE account_id=? AND instance_kind=?",
            (account_id, str(instance_kind or "")),
        ).fetchone()
        return int(row["floor"] or 0) if row else 0

    def mark_instance_secret(self, account_id, instance_kind, floor, secret_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_secrets(account_id,instance_kind,floor,secret_name) VALUES(?,?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor)), str(secret_name or "Sekret")),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_secret_rows(self, account_id, instance_kind):
        return self.conn.execute(
            "SELECT floor,secret_name,discovered_at FROM instance_map_secrets "
            "WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()

    def mark_instance_checkpoint(self, account_id, instance_kind, floor):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_checkpoints(account_id,instance_kind,floor) VALUES(?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor))),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_checkpoint_floors(self, account_id, instance_kind):
        kind = str(instance_kind or "")
        result = {
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM instance_map_checkpoints WHERE account_id=? AND instance_kind=?",
                (account_id, kind),
            ).fetchall()
        }
        # Jednorazowo zaliczone bramki bossów są również checkpointami mapy.
        result.update(
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=?",
                (account_id, kind),
            ).fetchall()
        )
        # Zgodność starych save'ów, które miały tylko najwyższy portal.
        if kind == "crypt":
            highest = self.crypt_checkpoint(account_id)
            result.update(range(10, highest + 1, 10))
        elif kind == "astral":
            highest = self.astral_checkpoint(account_id)
            start = int(ASTRAL_MIN_FLOOR)
            if highest >= start:
                result.update(range(start, highest + 1, 10))
        return result

    def highest_boss_floor_cleared(self, account_id, instance_kind):
        floors = self.instance_checkpoint_floors(account_id, instance_kind)
        return max(floors) if floors else 0

    def treasure_chest_opened_at(self, account_id, room_id):
        row = self.conn.execute(
            "SELECT opened_at FROM treasure_chest_cooldowns WHERE account_id=? AND room_id=?",
            (account_id, room_id),
        ).fetchone()
        return int(row["opened_at"]) if row else 0

    def mark_treasure_chest_opened(self, account_id, room_id, opened_at=None):
        stamp = int(time.time() if opened_at is None else opened_at)
        self.conn.execute(
            "INSERT INTO treasure_chest_cooldowns(account_id,room_id,opened_at) VALUES(?,?,?) "
            "ON CONFLICT(account_id,room_id) DO UPDATE SET opened_at=excluded.opened_at",
            (account_id, room_id, stamp),
        )
        self.conn.commit()
        return stamp

    def achievement_metric(self, account_id, metric):
        row = self.conn.execute(
            "SELECT value FROM achievement_progress WHERE account_id=? AND metric=?",
            (account_id, metric),
        ).fetchone()
        return int(row["value"]) if row else 0

    def add_achievement_metric(self, account_id, metric, amount=1):
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric)
            DO UPDATE SET value=value+excluded.value
            """,
            (account_id, metric, int(amount)),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def set_achievement_metric_max(self, account_id, metric, value):
        value = max(0, int(value))
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric) DO UPDATE SET
                value=MAX(achievement_progress.value, excluded.value)
            """,
            (account_id, metric, value),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def unlock_achievement(self, account_id, achievement_id, name, tier):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO achievements(account_id,achievement_id,name,tier) VALUES(?,?,?,?)",
            (account_id, achievement_id, name, tier),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def achievement_rows(self, account_id):
        return self.conn.execute(
            "SELECT achievement_id,name,tier,unlocked_at FROM achievements "
            "WHERE account_id=? ORDER BY unlocked_at, achievement_id",
            (account_id,),
        ).fetchall()

    def unlock_title(self, account_id, title_id, title_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO unlocked_titles(account_id,title_id,title_name) VALUES(?,?,?)",
            (account_id, title_id, title_name),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def title_rows(self, account_id):
        return self.conn.execute(
            "SELECT title_id,title_name,unlocked_at FROM unlocked_titles "
            "WHERE account_id=? ORDER BY title_name COLLATE NOCASE",
            (account_id,),
        ).fetchall()

    def bounty_board_state(self, account_id):
        row = self.conn.execute(
            "SELECT offers_json,active_json,completed_count FROM bounty_boards WHERE account_id=?",
            (account_id,),
        ).fetchone()
        if not row:
            return {"offers": [], "active": {}, "completed_count": 0}
        try:
            offers = json.loads(row["offers_json"] or "[]")
        except Exception:
            offers = []
        try:
            active = json.loads(row["active_json"] or "{}")
        except Exception:
            active = {}
        if not isinstance(offers, list):
            offers = []
        if not isinstance(active, dict):
            active = {}
        return {
            "offers": offers,
            "active": active,
            "completed_count": max(0, int(row["completed_count"] or 0)),
        }

    def save_bounty_board_state(self, account_id, offers=None, active=None, completed_count=None):
        current = self.bounty_board_state(account_id)
        if offers is None:
            offers = current["offers"]
        if active is None:
            active = current["active"]
        if completed_count is None:
            completed_count = current["completed_count"]
        self.conn.execute(
            """
            INSERT INTO bounty_boards(account_id,offers_json,active_json,completed_count,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                offers_json=excluded.offers_json,
                active_json=excluded.active_json,
                completed_count=excluded.completed_count,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                account_id,
                json.dumps(list(offers or []), ensure_ascii=False, separators=(",", ":")),
                json.dumps(dict(active or {}), ensure_ascii=False, separators=(",", ":")),
                max(0, int(completed_count or 0)),
            ),
        )
        self.conn.commit()

    def dynamic_world_quest_v015(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,)
        ).fetchone()
        return row

    def save_dynamic_world_quest_v015(self, account_id, quest):
        quest = dict(quest or {})
        self.conn.execute(
            """
            INSERT INTO dynamic_world_quests_v015(
                account_id,quest_key,quest_type,target,label,needed,progress,
                reward_soul_xp,reward_gold,accepted_slot,completed,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                quest_key=excluded.quest_key, quest_type=excluded.quest_type,
                target=excluded.target, label=excluded.label, needed=excluded.needed,
                progress=excluded.progress, reward_soul_xp=excluded.reward_soul_xp,
                reward_gold=excluded.reward_gold, accepted_slot=excluded.accepted_slot,
                completed=excluded.completed, updated_at=CURRENT_TIMESTAMP
            """,
            (account_id, str(quest.get("quest_key", "")), str(quest.get("quest_type", "")),
             str(quest.get("target", "any")), str(quest.get("label", "")),
             max(0,int(quest.get("needed",0))), max(0,int(quest.get("progress",0))),
             max(0,int(quest.get("reward_soul_xp",0))), max(0,int(quest.get("reward_gold",0))),
             int(quest.get("accepted_slot",0)), 1 if quest.get("completed") else 0)
        )
        self.conn.commit()

    def clear_dynamic_world_quest_v015(self, account_id):
        self.conn.execute("DELETE FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,))
        self.conn.commit()

    def faction_reputation_v016(self, account_id, faction_id):
        row = self.conn.execute(
            "SELECT reputation FROM faction_reputation_v016 WHERE account_id=? AND faction_id=?",
            (account_id, str(faction_id)),
        ).fetchone()
        return max(0, int(row["reputation"] or 0)) if row else 0

    def faction_reputations_v016(self, account_id):
        rows = self.conn.execute(
            "SELECT faction_id,reputation FROM faction_reputation_v016 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["faction_id"]): max(0,int(row["reputation"] or 0)) for row in rows}

    def add_faction_reputation_v016(self, account_id, faction_id, amount=1):
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return self.faction_reputation_v016(account_id, faction_id)
        self.conn.execute(
            "INSERT INTO faction_reputation_v016(account_id,faction_id,reputation) VALUES(?,?,?) "
            "ON CONFLICT(account_id,faction_id) DO UPDATE SET "
            "reputation=faction_reputation_v016.reputation+excluded.reputation,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(faction_id), amount),
        )
        self.conn.commit()
        return self.faction_reputation_v016(account_id, faction_id)

    def lifetime_stat(self, account_id, stat_key):
        row = self.conn.execute(
            "SELECT value FROM lifetime_statistics WHERE account_id=? AND stat_key=?",
            (account_id, str(stat_key)),
        ).fetchone()
        return max(0, int(row["value"] or 0)) if row else 0

    def add_lifetime_stat(self, account_id, stat_key, amount=1):
        amount = int(amount or 0)
        if amount <= 0:
            return self.lifetime_stat(account_id, stat_key)
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=lifetime_statistics.value+excluded.value,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), amount),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def set_lifetime_stat_max(self, account_id, stat_key, value):
        value = max(0, int(value or 0))
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=MAX(lifetime_statistics.value,excluded.value),updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), value),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def lifetime_stats(self, account_id):
        rows = self.conn.execute(
            "SELECT stat_key,value FROM lifetime_statistics WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["stat_key"]): max(0, int(row["value"] or 0)) for row in rows}

    def fish_journal_entry(self, account_id, fish_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? AND fish_id=?",
            (account_id, base_fish_species_id(fish_id)),
        ).fetchone()

    def fish_journal_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? ORDER BY caught_count DESC, fish_id",
            (account_id,),
        ).fetchall()

    def fish_journal_ids(self, account_id):
        return {str(row["fish_id"]) for row in self.fish_journal_rows(account_id)}

    def record_fish_catch(self, account_id, fish_id, quantity, length_mm, weight_g, room_id):
        fish_id = base_fish_species_id(fish_id)
        quantity = max(1, int(quantity or 1))
        length_mm = max(0, int(length_mm or 0))
        weight_g = max(0, int(weight_g or 0))
        room_id = str(room_id or "")
        old = self.fish_journal_entry(account_id, fish_id)
        old_length = int(old["best_length_mm"] or 0) if old else 0
        old_weight = int(old["best_weight_g"] or 0) if old else 0
        result = {
            "new_species": old is None,
            "new_length_record": length_mm > old_length,
            "new_weight_record": weight_g > old_weight,
        }
        self.conn.execute(
            """
            INSERT INTO fish_journal(
                account_id,fish_id,caught_count,best_length_mm,best_weight_g,
                first_room_id,last_room_id,first_caught_at,last_caught_at
            ) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,fish_id) DO UPDATE SET
                caught_count=fish_journal.caught_count+excluded.caught_count,
                best_length_mm=MAX(fish_journal.best_length_mm,excluded.best_length_mm),
                best_weight_g=MAX(fish_journal.best_weight_g,excluded.best_weight_g),
                last_room_id=excluded.last_room_id,
                last_caught_at=CURRENT_TIMESTAMP
            """,
            (account_id, fish_id, quantity, length_mm, weight_g, room_id, room_id),
        )
        self.conn.commit()
        row = self.fish_journal_entry(account_id, fish_id)
        result.update({
            "caught_count": int(row["caught_count"] or 0),
            "best_length_mm": int(row["best_length_mm"] or 0),
            "best_weight_g": int(row["best_weight_g"] or 0),
        })
        return result

    # ---------------- v0.22.0 persistent systems ----------------
    def record_fishing_global_v022(self, fish_id, item_id, holder_name, length_mm, weight_g, account_id=None):
        fish_id=base_fish_species_id(fish_id); item_id=str(item_id or fish_id); holder_name=str(holder_name or "Nieznany")
        length_mm=max(0,int(length_mm or 0)); weight_g=max(0,int(weight_g or 0))
        row=self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(fish_id,)).fetchone()
        old_l=int(row["best_length_mm"] or 0) if row else 0; old_w=int(row["best_weight_g"] or 0) if row else 0
        new_l=length_mm>old_l; new_w=weight_g>old_w
        best_l=max(old_l,length_mm); best_w=max(old_w,weight_g)
        lholder=holder_name if new_l else (str(row["length_holder"] or "") if row else "")
        wholder=holder_name if new_w else (str(row["weight_holder"] or "") if row else "")
        self.conn.execute("""INSERT INTO fish_global_records_v022(fish_id,best_length_mm,length_holder,best_weight_g,weight_holder,updated_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(fish_id) DO UPDATE SET best_length_mm=excluded.best_length_mm,length_holder=excluded.length_holder,best_weight_g=excluded.best_weight_g,weight_holder=excluded.weight_holder,updated_at=CURRENT_TIMESTAMP""",
            (fish_id,best_l,lholder,best_w,wholder))
        score=v022_fish_rarity_score(item_id); rare=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()
        old_score=int(rare["rarity_score"] or 0) if rare else 0; old_rare_weight=int(rare["weight_g"] or 0) if rare else 0
        new_rare=score>old_score or (score==old_score and weight_g>old_rare_weight)
        if new_rare:
            self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES('global',?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                (score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        new_personal_rare=False
        if account_id is not None:
            pkey=f"account:{int(account_id)}"; personal=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(pkey,)).fetchone()
            pscore=int(personal["rarity_score"] or 0) if personal else 0; pweight=int(personal["weight_g"] or 0) if personal else 0
            new_personal_rare=score>pscore or (score==pscore and weight_g>pweight)
            if new_personal_rare:
                self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                    (pkey,score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        self.conn.commit(); return {"new_global_length":new_l,"new_global_weight":new_w,"new_global_rarest":new_rare,"new_personal_rarest":new_personal_rare}

    def fish_global_record_v022(self, fish_id):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(base_fish_species_id(fish_id),)).fetchone()

    def fish_global_top_v022(self, limit=5):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 ORDER BY best_weight_g DESC,best_length_mm DESC LIMIT ?",(max(1,min(20,int(limit))),)).fetchall()

    def fish_rarest_global_v022(self):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()

    def fish_rarest_personal_v022(self, account_id):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(f"account:{int(account_id)}",)).fetchone()

    def world_project_state_v022(self, project_id):
        project_id=str(project_id); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        if not row:
            self.conn.execute("INSERT INTO world_projects_v022(project_id,progress_json,completed) VALUES(?,'{}',0)",(project_id,)); self.conn.commit(); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        try: progress=json.loads(row["progress_json"] or "{}")
        except Exception: progress={}
        return {"project_id":project_id,"progress":progress if isinstance(progress,dict) else {},"completed":bool(row["completed"]),"completed_at":row["completed_at"]}

    def world_project_contribution_v022(self, project_id, account_id):
        row=self.conn.execute("SELECT * FROM world_project_contributions_v022 WHERE project_id=? AND account_id=?",(project_id,account_id)).fetchone()
        if not row: return {"points":0,"coins":0,"resources":{},"reward_claimed":False}
        try: resources=json.loads(row["resources_json"] or "{}")
        except Exception: resources={}
        return {"points":int(row["points"] or 0),"coins":int(row["coins"] or 0),"resources":resources if isinstance(resources,dict) else {},"reward_claimed":bool(row["reward_claimed"])}

    def add_world_project_contribution_v022(self, project_id, account_id, category, amount, points):
        spec=V022_WORLD_PROJECTS[project_id]; state=self.world_project_state_v022(project_id); progress=dict(state["progress"]); category=str(category); amount=max(0,int(amount)); points=max(0,int(points))
        need=int(spec["requirements"].get(category,0)); old=int(progress.get(category,0) or 0); accepted=min(amount,max(0,need-old))
        if accepted<=0: return {"accepted":0,"completed":state["completed"],"newly_completed":False,"progress":progress}
        progress[category]=old+accepted
        completed=all(int(progress.get(k,0) or 0)>=int(v) for k,v in spec["requirements"].items())
        newly=completed and not state["completed"]
        self.conn.execute("UPDATE world_projects_v022 SET progress_json=?,completed=?,completed_at=CASE WHEN ?=1 AND completed=0 THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE project_id=?",(json.dumps(progress,ensure_ascii=False,separators=(",",":")),1 if completed else 0,1 if completed else 0,project_id))
        cur=self.world_project_contribution_v022(project_id,account_id); resources=dict(cur["resources"]); coins=int(cur["coins"]);
        if category=="coins": coins+=accepted
        else: resources[category]=int(resources.get(category,0) or 0)+accepted
        self.conn.execute("""INSERT INTO world_project_contributions_v022(project_id,account_id,points,resources_json,coins,reward_claimed,updated_at) VALUES(?,?,?,?,?,0,CURRENT_TIMESTAMP)
            ON CONFLICT(project_id,account_id) DO UPDATE SET points=world_project_contributions_v022.points+excluded.points,resources_json=excluded.resources_json,coins=excluded.coins,updated_at=CURRENT_TIMESTAMP""",
            (project_id,account_id,points,json.dumps(resources,ensure_ascii=False,separators=(",",":")),coins))
        self.conn.commit(); return {"accepted":accepted,"completed":completed,"newly_completed":newly,"progress":progress}

    def mark_world_project_reward_claimed_v022(self, project_id, account_id):
        cur=self.conn.execute("UPDATE world_project_contributions_v022 SET reward_claimed=1,updated_at=CURRENT_TIMESTAMP WHERE project_id=? AND account_id=? AND reward_claimed=0",(project_id,account_id)); self.conn.commit(); return cur.rowcount>0

    def legendary_contract_state_v022(self, account_id):
        row=self.conn.execute("SELECT * FROM legendary_contracts_v022 WHERE account_id=?",(account_id,)).fetchone()
        if not row: return {"offers":[],"active":{},"completed_count":0}
        try: offers=json.loads(row["offers_json"] or "[]")
        except Exception: offers=[]
        try: active=json.loads(row["active_json"] or "{}")
        except Exception: active={}
        return {"offers":offers if isinstance(offers,list) else [],"active":active if isinstance(active,dict) else {},"completed_count":int(row["completed_count"] or 0)}

    def save_legendary_contract_state_v022(self, account_id, offers=None, active=None, completed_count=None):
        cur=self.legendary_contract_state_v022(account_id); offers=cur["offers"] if offers is None else offers; active=cur["active"] if active is None else active; completed_count=cur["completed_count"] if completed_count is None else completed_count
        self.conn.execute("""INSERT INTO legendary_contracts_v022(account_id,offers_json,active_json,completed_count,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET offers_json=excluded.offers_json,active_json=excluded.active_json,completed_count=excluded.completed_count,updated_at=CURRENT_TIMESTAMP""",
            (account_id,json.dumps(list(offers or []),ensure_ascii=False,separators=(",",":")),json.dumps(dict(active or {}),ensure_ascii=False,separators=(",",":")),max(0,int(completed_count or 0))))
        self.conn.commit()

    def add_drop_history(self, account_id, item_id, item_name, rarity, source, zone):
        self.conn.execute(
            "INSERT INTO drop_history(account_id,item_id,item_name,rarity,source,zone) "
            "VALUES(?,?,?,?,?,?)",
            (account_id, item_id, item_name, rarity, source, zone),
        )
        self.conn.execute(
            "DELETE FROM drop_history WHERE account_id=? AND id NOT IN ("
            "SELECT id FROM drop_history WHERE account_id=? ORDER BY id DESC LIMIT ?)",
            (account_id, account_id, DROP_HISTORY_LIMIT),
        )
        self.conn.commit()

    def drop_history_rows(self, account_id, limit=20):
        return self.conn.execute(
            "SELECT item_name,rarity,source,zone,created_at FROM drop_history "
            "WHERE account_id=? ORDER BY id DESC LIMIT ?",
            (account_id, max(1, min(DROP_HISTORY_LIMIT, int(limit)))),
        ).fetchall()

    def remove_item(self, account_id, item_id, qty=1):
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def transfer_inventory_item(self, from_account_id, to_account_id, item_id, qty=1):
        """Atomowo przenosi zwykły item inventory między dwiema postaciami."""
        qty = max(1, int(qty))
        if from_account_id == to_account_id:
            return False
        current = self.item_qty(from_account_id, item_id)
        if current < qty:
            return False
        try:
            self.conn.execute("BEGIN")
            new_qty = current - qty
            if new_qty <= 0:
                self.conn.execute(
                    "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                    (from_account_id, item_id),
                )
            else:
                self.conn.execute(
                    "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                    (new_qty, from_account_id, item_id),
                )
            self.conn.execute(
                """
                INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
                ON CONFLICT(account_id,item_id)
                DO UPDATE SET quantity=quantity+excluded.quantity
                """,
                (to_account_id, item_id, qty),
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def transfer_shared_currency(self, from_character_account_id, to_character_account_id, amount_silver):
        """Atomowy transfer wspólnego salda konta między dwoma różnymi kontami."""
        amount_silver = int(amount_silver or 0)
        if amount_silver <= 0:
            return False
        from_master = self.master_account_for_character(from_character_account_id)
        to_master = self.master_account_for_character(to_character_account_id)
        if from_master == to_master:
            return False
        from_total = int(self.shared_wallet_for_master(from_master)[0])
        to_total = int(self.shared_wallet_for_master(to_master)[0])
        if from_total < amount_silver:
            return False
        if to_total + amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
            return False
        try:
            self.conn.execute("BEGIN")
            self.set_shared_wallet_for_master(
                from_master, from_total - amount_silver, 0, 0, commit=False
            )
            self.set_shared_wallet_for_master(
                to_master, to_total + amount_silver, 0, 0, commit=False
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def ensure_class_progress(self, account_id, class_name):
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,NULL)",
            (account_id, class_name),
        )
        self.conn.commit()

    def ensure_primary_class(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND active_slot=1 AND class_name<>?",
            (account_id, class_name),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()

    def class_progress_row(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()

    def active_class_rows(self, account_id, primary_class):
        self.ensure_primary_class(account_id, primary_class)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND active_slot IS NOT NULL "
            "ORDER BY active_slot",
            (account_id,),
        ).fetchall()

    def active_class_names(self, account_id, primary_class):
        return [
            row["class_name"]
            for row in self.active_class_rows(account_id, primary_class)
        ]

    def activate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        rows = self.active_class_rows(account_id, primary_class)
        active_names = [row["class_name"] for row in rows]

        if class_name in active_names:
            return False, "Ta klasa jest już aktywna."
        if len(active_names) >= MULTICLASS_MAX_ACTIVE:
            return False, "Masz już maksymalnie 3 aktywne klasy."

        used_slots = {
            int(row["active_slot"])
            for row in rows
            if row["active_slot"] is not None
        }
        slot = next(
            number for number in range(2, MULTICLASS_MAX_ACTIVE + 1)
            if number not in used_slots
        )

        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=? "
            "WHERE account_id=? AND class_name=?",
            (slot, account_id, class_name),
        )
        self.conn.commit()
        return True, slot

    def deactivate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        if class_name == primary_class:
            return False, "Nie można wyłączyć klasy głównej."

        row = self.conn.execute(
            "SELECT active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()
        if not row or row["active_slot"] is None:
            return False, "Ta klasa nie jest aktywna."

        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()
        return True, None

    def add_class_mastery_xp(self, account_id, class_name, amount):
        self.ensure_class_progress(account_id, class_name)
        row = self.class_progress_row(account_id, class_name)
        level = int(row["level"])
        xp = int(row["xp"])
        gain = max(0, int(amount))
        xp += gain
        level_ups = 0

        while level < CLASS_MASTERY_MAX_LEVEL:
            needed = class_mastery_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        overflow_xp = 0
        if level >= CLASS_MASTERY_MAX_LEVEL:
            level = CLASS_MASTERY_MAX_LEVEL
            overflow_xp = max(0, int(xp))
            xp = 0

        self.conn.execute(
            "UPDATE class_progress SET level=?,xp=? "
            "WHERE account_id=? AND class_name=?",
            (level, xp, account_id, class_name),
        )
        self.conn.commit()
        return {
            "class_name": class_name,
            "level": level,
            "xp": xp,
            "level_ups": level_ups,
            "next_xp": class_mastery_xp_to_next(level),
            "gain": gain,
            "overflow_xp": overflow_xp,
        }

    def skill_queue_rows(self, account_id, queue_type=None):
        if queue_type is None:
            return self.conn.execute(
                "SELECT queue_type,position,skill_id FROM skill_queue "
                "WHERE account_id=? ORDER BY CASE queue_type WHEN 'physical' THEN 0 ELSE 1 END, position",
                (account_id,),
            ).fetchall()
        return self.conn.execute(
            "SELECT queue_type,position,skill_id FROM skill_queue "
            "WHERE account_id=? AND queue_type=? ORDER BY position",
            (account_id, queue_type),
        ).fetchall()

    def skill_queue_enabled(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_queue_settings(account_id,enabled) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT enabled FROM skill_queue_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return bool(row and int(row["enabled"]))

    def set_skill_queue_enabled(self, account_id, enabled):
        self.conn.execute(
            "INSERT INTO skill_queue_settings(account_id,enabled) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled",
            (account_id, 1 if enabled else 0),
        )
        self.conn.commit()

    def combat_log_mode(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO combat_log_settings(account_id,mode) VALUES(?, 'normal')",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT mode FROM combat_log_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        mode = str(row["mode"] if row else "normal").lower()
        return mode if mode in ("concise", "normal", "full") else "normal"

    def set_combat_log_mode(self, account_id, mode):
        mode = str(mode or "normal").lower()
        if mode not in ("concise", "normal", "full"):
            mode = "normal"
        self.conn.execute(
            "INSERT INTO combat_log_settings(account_id,mode) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET mode=excluded.mode",
            (account_id, mode),
        )
        self.conn.commit()
        return mode

    def wimpy_percent(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO wimpy_settings(account_id,percent) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT percent FROM wimpy_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        value = int(row["percent"] if row else 0)
        return max(0, min(99, value))

    def set_wimpy_percent(self, account_id, percent):
        percent = max(0, min(99, int(percent or 0)))
        self.conn.execute(
            "INSERT INTO wimpy_settings(account_id,percent) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET percent=excluded.percent",
            (account_id, percent),
        )
        self.conn.commit()
        return percent

    def replace_skill_queue(self, account_id, queue_type, skill_ids):
        queue_type = str(queue_type)
        skill_ids = list(skill_ids)
        self.conn.execute(
            "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        )
        for index, skill_id in enumerate(skill_ids, 1):
            self.conn.execute(
                "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
                (account_id, queue_type, index, skill_id),
            )
        self.conn.commit()

    def add_skill_queue_entry(self, account_id, queue_type, skill_id):
        exists = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if exists:
            return False, f"Umiejętność jest już w kolejce {exists['queue_type']} na pozycji {exists['position']}."
        row = self.conn.execute(
            "SELECT COALESCE(MAX(position),0) AS max_position FROM skill_queue "
            "WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        ).fetchone()
        position = int(row["max_position"]) + 1
        self.conn.execute(
            "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
            (account_id, queue_type, position, skill_id),
        )
        self.conn.commit()
        return True, position

    def remove_skill_queue_entry(self, account_id, queue_type, position):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        if index < 0 or index >= len(skill_ids):
            return None
        removed = skill_ids.pop(index)
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return removed

    def remove_skill_queue_skill(self, account_id, skill_id):
        row = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if not row:
            return None
        return self.remove_skill_queue_entry(
            account_id, row["queue_type"], int(row["position"])
        )

    def clear_skill_queue(self, account_id, queue_type=None):
        if queue_type is None:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=?",
                (account_id,),
            )
        else:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
                (account_id, queue_type),
            )
        self.conn.commit()

    def move_skill_queue_entry(self, account_id, queue_type, position, delta):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        target = index + int(delta)
        if index < 0 or index >= len(skill_ids) or target < 0 or target >= len(skill_ids):
            return False
        skill_ids[index], skill_ids[target] = skill_ids[target], skill_ids[index]
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return True

    def learned_skill_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT skill_id FROM learned_skills WHERE account_id=? ORDER BY learned_at, skill_id",
            (account_id,),
        ).fetchall()
        return {row["skill_id"] for row in rows}

    def knows_skill(self, account_id, skill_id):
        return self.conn.execute(
            "SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone() is not None

    def learn_skill(self, account_id, skill_id):
        before = self.conn.total_changes
        self.conn.execute(
            "INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)",
            (account_id, skill_id),
        )
        self.conn.commit()
        learned_now = self.conn.total_changes > before
        self.ensure_skill_progress(account_id, skill_id)
        return learned_now

    def ensure_skill_progress(self, account_id, skill_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_progress(account_id,skill_id,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, skill_id),
        )
        self.conn.commit()

    def skill_progress(self, account_id, skill_id):
        self.ensure_skill_progress(account_id, skill_id)
        return self.conn.execute(
            "SELECT level,xp,uses FROM skill_progress WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()

    def add_skill_xp(self, account_id, skill_id, amount):
        self.ensure_skill_progress(account_id, skill_id)
        row = self.skill_progress(account_id, skill_id)
        level = int(row["level"])
        xp = int(row["xp"]) + max(0, int(amount))
        uses = int(row["uses"]) + 1
        level_ups = 0

        while level < SKILL_MAX_LEVEL:
            needed = skill_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= SKILL_MAX_LEVEL:
            level = SKILL_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE skill_progress SET level=?,xp=?,uses=? WHERE account_id=? AND skill_id=?",
            (level, xp, uses, account_id, skill_id),
        )
        self.conn.commit()
        return {
            "level": level,
            "xp": xp,
            "uses": uses,
            "level_ups": level_ups,
            "next_xp": skill_xp_to_next(level),
        }

    def equipment(self, account_id):
        return self.conn.execute(
            "SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot",
            (account_id,),
        ).fetchall()

    def equipped_item(self, account_id, slot):
        row = self.conn.execute(
            "SELECT item_id FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        ).fetchone()
        return row["item_id"] if row else None

    def equip(self, account_id, slot, item_id):
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        self.conn.commit()

    def unequip(self, account_id, slot):
        self.conn.execute(
            "DELETE FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()

    def socketed_gems(self, account_id, slot, jewelry_item_id=None):
        if jewelry_item_id is None:
            return self.conn.execute(
                "SELECT socket_index,jewelry_item_id,gem_id "
                "FROM equipment_gems "
                "WHERE account_id=? AND slot=? "
                "ORDER BY socket_index",
                (account_id, slot),
            ).fetchall()
        return self.conn.execute(
            "SELECT socket_index,jewelry_item_id,gem_id "
            "FROM equipment_gems "
            "WHERE account_id=? AND slot=? AND jewelry_item_id=? "
            "ORDER BY socket_index",
            (account_id, slot, jewelry_item_id),
        ).fetchall()

    def add_socketed_gem(
        self, account_id, slot, jewelry_item_id,
        socket_index, gem_id,
    ):
        self.conn.execute(
            """
            INSERT INTO equipment_gems(
                account_id,slot,socket_index,jewelry_item_id,gem_id
            ) VALUES(?,?,?,?,?)
            ON CONFLICT(account_id,slot,socket_index)
            DO UPDATE SET
                jewelry_item_id=excluded.jewelry_item_id,
                gem_id=excluded.gem_id
            """,
            (
                account_id, slot, int(socket_index),
                jewelry_item_id, gem_id,
            ),
        )
        self.conn.commit()

    def clear_socketed_gems(self, account_id, slot):
        rows = self.socketed_gems(account_id, slot)
        self.conn.execute(
            "DELETE FROM equipment_gems "
            "WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()
        return rows

    def ensure_profession(self, account_id, profession):
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        self.conn.commit()

    def profession(self, account_id, profession):
        self.ensure_profession(account_id, profession)
        return self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()

    def save_profession(self, account_id, profession, level, xp, actions):
        self.conn.execute(
            "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
            (level, xp, actions, account_id, profession),
        )
        self.conn.commit()


    def equipment_enchant_v03053(self, account_id, slot):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? AND slot=?",(account_id,slot)).fetchone()

    def set_equipment_enchant_v03053(self, account_id, slot, enchant_key, stat, amount):
        self.conn.execute("INSERT INTO equipment_enchants_v03053(account_id,slot,enchant_key,stat,amount) VALUES(?,?,?,?,?) ON CONFLICT(account_id,slot) DO UPDATE SET enchant_key=excluded.enchant_key,stat=excluded.stat,amount=excluded.amount,updated_at=CURRENT_TIMESTAMP",(account_id,slot,enchant_key,stat,int(amount)))
        self.conn.commit()

    def equipment_enchants_v03053(self, account_id):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? ORDER BY slot",(account_id,)).fetchall()

    def ensure_tool(self, account_id, tool_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        self.conn.commit()

    def tool(self, account_id, tool_type):
        self.ensure_tool(account_id, tool_type)
        return self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()

    def save_tool(self, account_id, tool_type, level, xp, uses):
        self.conn.execute(
            "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
            (level, xp, uses, account_id, tool_type),
        )
        self.conn.commit()

    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_storage_item(self, account_id, container, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1):
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        self.conn.commit()
        return True

    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        total = 0
        for item_id in item_ids:
            total += self.item_qty(account_id, item_id)
            if container:
                total += self.storage_qty(account_id, container, item_id)
        return total

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None):
        remaining = needed

        if container:
            for item_id in sorted(item_ids):
                if remaining <= 0:
                    break
                qty = self.storage_qty(account_id, container, item_id)
                take = min(qty, remaining)
                if take > 0:
                    self.remove_storage_item(account_id, container, item_id, take)
                    remaining -= take

        for item_id in sorted(item_ids):
            if remaining <= 0:
                break
            qty = self.item_qty(account_id, item_id)
            take = min(qty, remaining)
            if take > 0:
                self.remove_item(account_id, item_id, take)
                remaining -= take

        return remaining == 0

    def quest(self, account_id, quest_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        ).fetchone()

    def start_quest(self, account_id, quest_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO quests("
            "account_id,quest_id,status,progress,completed_at,completion_count"
            ") VALUES(?,?, 'active',0,0,0)",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def restart_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='active',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def set_quest_progress(self, account_id, quest_id, progress):
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (max(0, int(progress)), account_id, quest_id),
        )
        self.conn.commit()

    def abandon_quest(self, account_id, quest_id):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "active":
            return False
        # Nie kasujemy completion_count ani completed_at: historia wcześniejszych
        # ukończeń ma pozostać. Porzucenie kasuje tylko bieżące podejście/postęp.
        self.conn.execute(
            "UPDATE quests SET status='abandoned',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()
        return True

    def repeat_quest_seconds_remaining(self, account_id, quest_id, cooldown):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "completed":
            return 0
        completed_at = int(row["completed_at"] or 0)
        if completed_at <= 0:
            return 0
        elapsed = max(0, int(time.time()) - completed_at)
        return max(0, int(cooldown) - elapsed)

    def quest_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? ORDER BY status,quest_id",
            (account_id,),
        ).fetchall()

    def increment_quest(self, account_id, target):
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q or q["kind"] != "kill" or q["target"] != target:
                continue
            new_progress = min(q["needed"], row["progress"] + 1)
            # v0.30.7: gotowy quest nie ogłasza ponownie tego samego
            # stanu po każdym kolejnym zabiciu tego samego celu.
            if int(new_progress) == int(row["progress"]):
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress))
        self.conn.commit()
        return changed

    def increment_item_collect_quest(self, account_id, item_id, amount=1):
        """v0.8.66: zwykłe collect liczy wyłącznie nowe zdobycze po przyjęciu."""
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if (
                not quest
                or quest.get("kind") != "collect"
                or quest.get("track_craft_progress")
                or quest.get("target") != item_id
            ):
                continue
            needed = max(1, int(quest.get("needed", 1)))
            old_progress = max(0, int(row["progress"]))
            new_progress = min(needed, old_progress + amount)
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress, needed))
        self.conn.commit()
        return changed

    def increment_craft_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or not quest.get(
                "track_craft_progress"
            ):
                continue

            if quest.get("kind") == "collect":
                if quest.get("target") != item_id:
                    continue
                needed = max(
                    1, int(quest.get("needed", 1))
                )
                old_progress = int(row["progress"])
                new_progress = min(
                    needed,
                    old_progress + amount,
                )
                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_progress,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        new_progress,
                        needed,
                    )
                )
                continue

            if quest.get("kind") == "craft_set":
                targets = tuple(
                    quest.get("targets") or ()
                )
                if item_id not in targets:
                    continue

                index = targets.index(item_id)
                old_mask = int(row["progress"])
                new_mask = old_mask | (1 << index)
                if new_mask == old_mask:
                    continue

                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_mask,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        int(new_mask).bit_count(),
                        len(targets),
                    )
                )

        self.conn.commit()
        return changed

    def increment_resource_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        progress_item_id = canonical_profession_resource_id(item_id)
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            quest_target = canonical_profession_resource_id(
                quest.get("target") if quest else ""
            )
            if (
                not quest
                or quest.get("kind") != "collect_resource"
                or not quest.get("track_resource_progress")
                or quest_target != progress_item_id
            ):
                continue

            needed = max(
                1, int(quest.get("needed", 1))
            )
            old_progress = int(row["progress"])
            new_progress = min(
                needed,
                old_progress + amount,
            )
            # v0.30.7: po osiągnięciu celu nie zwracamy sztucznej
            # "zmiany" 30->30. Dzięki temu komunikat o gotowości questa
            # nie powtarza się przy każdym następnym zbiorze.
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? "
                "WHERE account_id=? AND quest_id=?",
                (
                    new_progress,
                    account_id,
                    row["quest_id"],
                ),
            )
            changed.append(
                (
                    row["quest_id"],
                    new_progress,
                    needed,
                )
            )

        self.conn.commit()
        return changed

    def resource_set_progress_v0929(self, account_id, quest_id, targets):
        result = {}
        for target_id in targets:
            row = self.conn.execute(
                "SELECT progress FROM quest_resource_progress_v0929 "
                "WHERE account_id=? AND quest_id=? AND target_id=?",
                (account_id, quest_id, canonical_profession_resource_id(target_id)),
            ).fetchone()
            result[target_id] = max(0, int(row["progress"])) if row else 0
        return result

    def distinct_category_items_v023(self, account_id, quest_id):
        rows = self.conn.execute(
            "SELECT target_id FROM quest_resource_progress_v0929 "
            "WHERE account_id=? AND quest_id=? AND progress>0 ORDER BY target_id",
            (account_id, quest_id),
        ).fetchall()
        return [str(row["target_id"]) for row in rows]

    def mark_distinct_category_item_v023(self, account_id, quest_id, item_id, needed):
        """Zapisz jeden NOWY gatunek/typ dla questa wymagającego różnych zasobów."""
        needed = max(1, int(needed))
        existing = self.distinct_category_items_v023(account_id, quest_id)
        if item_id in existing or len(existing) >= needed:
            return len(existing), False
        self.conn.execute(
            "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
            "VALUES(?,?,?,1) ON CONFLICT(account_id,quest_id,target_id) DO NOTHING",
            (account_id, quest_id, str(item_id)),
        )
        count = len(self.distinct_category_items_v023(account_id, quest_id))
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (min(needed, count), account_id, quest_id),
        )
        self.conn.commit()
        return min(needed, count), True

    def increment_resource_set_quest_v0929(self, account_id, item_id, amount=1):
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        item_base = canonical_profession_resource_id(item_id)
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or quest.get("kind") != "collect_resource_set":
                continue
            requirements = dict(quest.get("resource_targets") or {})
            matched_target = None
            target_needed = 0
            for target_id, needed in requirements.items():
                if canonical_profession_resource_id(target_id) == item_base:
                    matched_target = target_id
                    target_needed = max(1, int(needed))
                    break
            if matched_target is None:
                continue
            current = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            ).get(matched_target, 0)
            updated = min(target_needed, current + amount)
            # v0.30.7: brak ponownego komunikatu po osiągnięciu limitu.
            if updated == current:
                continue
            self.conn.execute(
                "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
                "VALUES(?,?,?,?) ON CONFLICT(account_id,quest_id,target_id) "
                "DO UPDATE SET progress=excluded.progress",
                (account_id, row["quest_id"], canonical_profession_resource_id(matched_target), updated),
            )
            counts = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            )
            counts[matched_target] = updated
            total = sum(min(max(1, int(requirements[t])), int(counts.get(t, 0))) for t in requirements)
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (total, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], total, int(quest.get("needed", total)), matched_target, updated, target_needed))
        self.conn.commit()
        return changed

    def complete_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='completed',completed_at=?,"
            "completion_count=completion_count+1 "
            "WHERE account_id=? AND quest_id=?",
            (int(time.time()), account_id, quest_id),
        )
        self.conn.commit()


    # ---- v0.9.25 equipment crafting / clan persistence ----
    def equipment_reforge(self, account_id, item_id):
        return self.conn.execute(
            "SELECT affix,affix_amount,rerolls FROM equipment_reforges WHERE account_id=? AND item_id=?",
            (account_id,item_id),
        ).fetchone()

    def save_equipment_reforge(self, account_id, item_id, affix, amount):
        self.conn.execute(
            "INSERT INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,1) "
            "ON CONFLICT(account_id,item_id) DO UPDATE SET affix=excluded.affix,affix_amount=excluded.affix_amount,rerolls=equipment_reforges.rerolls+1",
            (account_id,item_id,affix,int(amount)),
        )
        self.conn.commit()

    def equipment_runes_v0925(self, account_id, item_id):
        return self.conn.execute(
            "SELECT socket_index,rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? ORDER BY socket_index",
            (account_id,item_id),
        ).fetchall()

    def add_equipment_rune_v0925(self, account_id, item_id, socket_index, rune_id):
        self.conn.execute(
            "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
            (account_id,item_id,int(socket_index),rune_id),
        )
        self.conn.commit()

    def remove_equipment_rune_v0925(self, account_id, item_id, socket_index):
        row=self.conn.execute(
            "SELECT rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        ).fetchone()
        if not row: return None
        self.conn.execute(
            "DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        )
        self.conn.commit()
        return str(row["rune_id"])

    def equipment_upgrade_level_v03042(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT upgrade_level FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return max(0, int(row["upgrade_level"])) if row else 0

    def set_equipment_upgrade_level_v03042(self, account_id, item_id, level):
        level = max(0, min(V03042_EQ_UPGRADE_MAX, int(level)))
        if level <= 0:
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "INSERT INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?) "
                "ON CONFLICT(account_id,item_id) DO UPDATE SET upgrade_level=excluded.upgrade_level",
                (account_id, item_id, level),
            )
        self.conn.commit()

    def clear_equipment_crafting_v0925(self, account_id, item_id):
        self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.commit()

    def transfer_equipment_crafting_v0925(self, from_account_id, to_account_id, item_id):
        ref=self.equipment_reforge(from_account_id,item_id)
        runes=list(self.equipment_runes_v0925(from_account_id,item_id))
        upgrade=self.equipment_upgrade_level_v03042(from_account_id,item_id)
        if ref:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,?)",
                (to_account_id,item_id,ref["affix"],int(ref["affix_amount"]),int(ref["rerolls"])),
            )
            self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        for rr in runes:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
                (to_account_id,item_id,int(rr["socket_index"]),rr["rune_id"]),
            )
        if runes:
            self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        if upgrade > 0:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?)",
                (to_account_id,item_id,int(upgrade)),
            )
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (from_account_id,item_id),
            )
        self.conn.commit()

    def clan_membership(self, account_id):
        # Wewnętrzna nazwa pozostaje dla zgodności z v0.9.25; UI mówi Gildia.
        return self.conn.execute(
            "SELECT c.id clan_id,c.name,c.level,c.treasury,m.rank,c.owner_account_id "
            "FROM player_clan_members m JOIN player_clans c ON c.id=m.clan_id WHERE m.account_id=?",
            (account_id,),
        ).fetchone()

    def guild_bonus_percent_v0926(self, account_id):
        row=self.clan_membership(account_id)
        return v0926_guild_bonus_percent(int(row["level"])) if row else 0

    def ensure_guild_default_roles_v0926(self, clan_id):
        clan_id=int(clan_id)
        for key,data in V0926_GUILD_DEFAULT_ROLES.items():
            self.conn.execute(
                "INSERT OR IGNORE INTO player_clan_roles(clan_id,role_key,name,priority,withdraw_money,withdraw_items,invite,kick) VALUES(?,?,?,?,?,?,?,?)",
                (clan_id,key,data["name"],data["priority"],data["withdraw_money"],data["withdraw_items"],data["invite"],data["kick"]),
            )
        self.conn.commit()

    def guild_role_v0926(self, clan_id, role_key):
        if str(role_key)=="leader":
            return {"role_key":"leader","name":"Lider","priority":1000,"withdraw_money":1,"withdraw_items":1,"invite":1,"kick":1}
        self.ensure_guild_default_roles_v0926(clan_id)
        return self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=? AND role_key=?",
            (int(clan_id),str(role_key)),
        ).fetchone()

    def guild_role_by_name_v0926(self, clan_id, query):
        self.ensure_guild_default_roles_v0926(clan_id)
        norm=normalize_lookup_text(query)
        rows=self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=?",
            (int(clan_id),),
        ).fetchall()
        exact=[r for r in rows if normalize_lookup_text(r["name"])==norm or normalize_lookup_text(r["role_key"])==norm]
        if exact: return exact[0]
        partial=[r for r in rows if norm and (norm in normalize_lookup_text(r["name"]) or norm in normalize_lookup_text(r["role_key"]))]
        return partial[0] if len(partial)==1 else None

    def clan_log(self, clan_id, actor_account_id, message):
        self.conn.execute("INSERT INTO player_clan_log(clan_id,actor_account_id,message) VALUES(?,?,?)", (clan_id,actor_account_id,str(message)))
        self.conn.commit()

    def clan_metric_add(self, clan_id, metric, amount=1):
        self.conn.execute(
            "INSERT INTO player_clan_metrics(clan_id,metric,value) VALUES(?,?,?) ON CONFLICT(clan_id,metric) DO UPDATE SET value=value+excluded.value",
            (clan_id,metric,int(amount)),
        )
        self.conn.commit()

    def guild_hall_v0927(self, clan_id):
        clan_id=int(clan_id)
        self.conn.execute("INSERT OR IGNORE INTO player_guild_halls_v0927(clan_id) VALUES(?)",(clan_id,))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_halls_v0927 WHERE clan_id=?",(clan_id,)).fetchone()

    def guild_contract_row_v0927(self, clan_id, contract_id):
        self.conn.execute("INSERT OR IGNORE INTO player_guild_contracts_v0927(clan_id,contract_id) VALUES(?,?)",(int(clan_id),str(contract_id)))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_contracts_v0927 WHERE clan_id=? AND contract_id=?",(int(clan_id),str(contract_id))).fetchone()

    def guild_contract_add_v0927(self, clan_id, kind, amount=1):
        clan_id=int(clan_id); now=int(time.time()); changed=[]
        for contract_id,definition in V0927_GUILD_CONTRACTS.items():
            if definition["kind"]!=kind: continue
            row=self.guild_contract_row_v0927(clan_id,contract_id)
            if int(row["ready_at"] or 0)>now: continue
            need=int(definition["need"]); new=min(need,int(row["progress"] or 0)+int(amount))
            self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=? WHERE clan_id=? AND contract_id=?",(new,clan_id,contract_id))
            changed.append((contract_id,new,need))
        self.conn.commit(); return changed

    def guild_contract_complete_v0927(self, clan_id, contract_id):
        clan_id=int(clan_id); definition=V0927_GUILD_CONTRACTS[str(contract_id)]
        row=self.guild_contract_row_v0927(clan_id,contract_id)
        if int(row["progress"] or 0)<int(definition["need"]): return False
        ready=int(time.time())+int(definition["cooldown"]); reward=int(definition["reward"])
        self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=0,completed_count=completed_count+1,ready_at=? WHERE clan_id=? AND contract_id=?",(ready,clan_id,contract_id))
        self.conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(reward,clan_id))
        self.conn.commit(); return True


    # v0.30.54 Crafting Mastery -------------------------------------------------
    def crafting_mastery_v03054(self, account_id, profession, category):
        profession=str(profession); category=str(category)
        self.conn.execute(
            "INSERT OR IGNORE INTO crafting_mastery_v03054(account_id,profession,category) VALUES(?,?,?)",
            (int(account_id),profession,category),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT * FROM crafting_mastery_v03054 WHERE account_id=? AND profession=? AND category=?",
            (int(account_id),profession,category),
        ).fetchone()

    def add_crafting_mastery_action_v03054(self, account_id, profession, category, critical=False, legendary=False):
        self.crafting_mastery_v03054(account_id,profession,category)
        self.conn.execute(
            "UPDATE crafting_mastery_v03054 SET actions=actions+1, criticals=criticals+?, legendary_count=legendary_count+? "
            "WHERE account_id=? AND profession=? AND category=?",
            (1 if critical else 0,1 if legendary else 0,int(account_id),str(profession),str(category)),
        )
        self.conn.commit()
        return self.crafting_mastery_v03054(account_id,profession,category)

    def crafting_masteries_v03054(self, account_id):
        return self.conn.execute(
            "SELECT * FROM crafting_mastery_v03054 WHERE account_id=? ORDER BY profession,category",
            (int(account_id),),
        ).fetchall()
