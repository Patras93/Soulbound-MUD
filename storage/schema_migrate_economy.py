# -*- coding: utf-8 -*-
"""Account, class/race balance and unified currency migrations."""


def migrate_accounts_and_economy(
    self, legacy_currency_to_coins, normalize_currency_values, CLASSES,
    CLASS_STARTING_STAT_BONUSES, RACES, V0876_CLASS_STARTING_STAT_BONUSES,
    V0876_RACE_BASE_STATS,
):
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


