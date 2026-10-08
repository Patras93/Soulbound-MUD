# -*- coding: utf-8 -*-
"""Independent per-character crisis participation with once-per-day claims."""

class DatabaseWorldCrisesV1220Mixin:
    def create_world_crises_schema_v1220(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS world_crises_v1220 (
          character_account_id INTEGER NOT NULL,
          region TEXT NOT NULL,
          day INTEGER NOT NULL,
          stage INTEGER NOT NULL DEFAULT 1,
          kills INTEGER NOT NULL DEFAULT 0,
          claimed INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY(character_account_id,region,day)
        )""")
        self.conn.commit()

    def crisis_status_v1220(self, account, region, day):
        row = self.conn.execute(
            "SELECT stage,kills,claimed FROM world_crises_v1220 "
            "WHERE character_account_id=? AND region=? AND day=?",
            (int(account), str(region), int(day)),
        ).fetchone()
        return dict(row) if row else None

    def crisis_start_v1220(self, account, region, day):
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO world_crises_v1220 "
            "(character_account_id,region,day,stage,kills,claimed) VALUES (?,?,?,1,0,0)",
            (int(account), str(region), int(day)),
        )
        self.conn.commit()
        return bool(cursor.rowcount)

    def crisis_kill_v1220(self, account, region, day, boss=False):
        """Only real kills can advance battle phases; no progress by reading status."""
        row = self.crisis_status_v1220(account, region, day)
        if not row or row["claimed"]:
            return None
        stage, kills = int(row["stage"]), int(row["kills"])
        if stage in (1, 2) and not boss:
            if stage == 2 and kills >= 4:
                return None
            kills += 1
            limit = 3 if stage == 1 else 4
            if kills >= limit and stage == 1:
                stage, kills = 2, 0
            else:
                kills = min(limit, kills)
        elif stage == 3 and boss:
            stage, kills = 4, 0
        else:
            return None
        self.conn.execute(
            "UPDATE world_crises_v1220 SET stage=?,kills=? "
            "WHERE character_account_id=? AND region=? AND day=? AND claimed=0",
            (stage, kills, int(account), str(region), int(day)),
        )
        self.conn.commit()
        return stage, kills

    def crisis_rescue_v1220(self, account, region, day):
        cursor = self.conn.execute(
            "UPDATE world_crises_v1220 SET stage=3,kills=0 "
            "WHERE character_account_id=? AND region=? AND day=? AND stage=2 AND kills>=4 AND claimed=0",
            (int(account), str(region), int(day)),
        )
        self.conn.commit()
        return cursor.rowcount == 1

    def crisis_claim_v1220(self, account, region, day, coins, item_id, quantity):
        """Claim marker, item and wallet in a single SQLite savepoint."""
        master = self.master_account_for_character(int(account))
        current = int(self.shared_wallet_for_master(master)[0])
        conn = self.conn
        conn.execute("SAVEPOINT crisis_claim_v1220")
        try:
            cursor = conn.execute(
                "UPDATE world_crises_v1220 SET claimed=1,stage=5 "
                "WHERE character_account_id=? AND region=? AND day=? AND stage=4 AND claimed=0",
                (int(account), str(region), int(day)),
            )
            if cursor.rowcount != 1:
                conn.execute("RELEASE SAVEPOINT crisis_claim_v1220")
                return False
            self.add_item(int(account), str(item_id), int(quantity), commit=False)
            from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL
            self.set_shared_wallet_for_master(master, min(CURRENCY_SQLITE_SAFE_TOTAL, current + int(coins)), 0, 0, commit=False)
            conn.execute("RELEASE SAVEPOINT crisis_claim_v1220")
            conn.commit()
            return True
        except Exception:
            conn.execute("ROLLBACK TO SAVEPOINT crisis_claim_v1220")
            conn.execute("RELEASE SAVEPOINT crisis_claim_v1220")
            raise
