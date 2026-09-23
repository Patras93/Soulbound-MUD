# -*- coding: utf-8 -*-
"""Lifetime history, fishing and collection migrations."""


def migrate_history_and_collections(
    self, FISH_RESOURCE_IDS, canonical_profession_resource_id, MOB_TEMPLATES,
    base_fish_species_id, BOSS_COLLECTION_CATALOG, FISH_COLLECTION_CATALOG,
    GEM_COLLECTION_CATALOG, HERB_COLLECTION_CATALOG, MATERIAL_COLLECTION_CATALOG,
    MINERAL_COLLECTION_CATALOG, UNIQUE_ITEM_COLLECTION_CATALOG, canonical_bestiary_template_id,
):
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


