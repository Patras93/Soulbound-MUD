# -*- coding: utf-8 -*-
"""Database schema and migrations."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.bootstrap_economy_professions import legacy_currency_to_coins, normalize_currency_values
from core.classes_skills import (
    CLASSES,
    CLASS_STARTING_STAT_BONUSES,
    RACES,
    V0876_CLASS_STARTING_STAT_BONUSES,
    V0876_RACE_BASE_STATS,
)
from core.mines_threat import CHARACTER_BOUND_TOOL_IDS
from core.progression_resources import FISH_RESOURCE_IDS
from network.protocol_gameplay_utils import V0926_GUILD_DEFAULT_ROLES, V0927_GUILD_CONTRACTS, canonical_profession_resource_id
from systems.content_registry import MOB_TEMPLATES
from systems.items_resources import base_fish_species_id
from world.dynamic_content import (
    BOSS_COLLECTION_CATALOG,
    FISH_COLLECTION_CATALOG,
    GEM_COLLECTION_CATALOG,
    HERB_COLLECTION_CATALOG,
    MATERIAL_COLLECTION_CATALOG,
    MINERAL_COLLECTION_CATALOG,
    UNIQUE_ITEM_COLLECTION_CATALOG,
    canonical_bestiary_template_id,
)


class DatabaseSchemaMixin:
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
            "soul_weapon_mastery_level": "INTEGER NOT NULL DEFAULT 1",
            "soul_weapon_mastery_xp": "INTEGER NOT NULL DEFAULT 0",
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
        # silver 1:1, gold 1:100, mithril 1:100_000 srebra.
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

        # v0.34.4: krótkotrwała v0.34.3 błędnie wprowadziła mithril_ore jako
        # zwykłą rudę. Mithril w Soulbound jest walutą. Stare sztuki nie mogą
        # zostać osierocone w Sakwie: jednorazowo zamieniamy je na ich dawną
        # wartość sprzedaży (500 srebra za sztukę), bez tworzenia dodatkowego
        # zysku ani 1:1 z wysokim nominałem mithrilu.
        legacy_mithril_ore_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("legacy_mithril_ore_v0344",),
        ).fetchone()
        if not legacy_mithril_ore_migrated:
            _legacy_by_master = {}
            _legacy_rows = self.conn.execute(
                "SELECT account_id,quantity FROM inventory WHERE item_id='mithril_ore' AND quantity>0 "
                "UNION ALL "
                "SELECT account_id,quantity FROM profession_storage WHERE item_id='mithril_ore' AND quantity>0"
            ).fetchall()
            for _row in _legacy_rows:
                _aid = int(_row["account_id"])
                _qty = max(0, int(_row["quantity"] or 0))
                if _qty <= 0:
                    continue
                _master = self.master_account_for_character(_aid)
                _legacy_by_master[_master] = _legacy_by_master.get(_master, 0) + _qty
            for _master, _qty in _legacy_by_master.items():
                _silver, _gold, _mithril = self.shared_wallet_for_master(_master)
                self.set_shared_wallet_for_master(
                    _master, _silver + _qty * 500, _gold, _mithril, commit=False
                )
            self.conn.execute("DELETE FROM inventory WHERE item_id='mithril_ore'")
            self.conn.execute("DELETE FROM profession_storage WHERE item_id='mithril_ore'")
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("legacy_mithril_ore_v0344",),
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
