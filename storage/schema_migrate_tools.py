# -*- coding: utf-8 -*-
"""Statistics and character-bound tool migrations."""

def migrate_stats_and_tools(self, CHARACTER_BOUND_TOOL_IDS):
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


