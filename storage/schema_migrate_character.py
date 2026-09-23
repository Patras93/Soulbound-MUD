# -*- coding: utf-8 -*-
"""Character schema migrations."""


def migrate_character_columns(self):
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

    return _v027_character_level_new


def migrate_character_legacy(self, character_level_was_new):
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
    if character_level_was_new:
        self.conn.execute("""
            UPDATE characters SET character_level = MIN(400, MAX(1,
                soul_level,
                COALESCE((SELECT MAX(level) FROM class_progress cp WHERE cp.account_id=characters.account_id),1),
                COALESCE((SELECT MAX(level) FROM professions p WHERE p.account_id=characters.account_id),1),
                COALESCE((SELECT MAX(level) FROM tools t WHERE t.account_id=characters.account_id),1)
            )), character_xp=0
        """)
        self.conn.execute("INSERT OR IGNORE INTO migration_flags(flag) VALUES(?)",("character_level_v0270",))


