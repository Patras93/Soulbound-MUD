# -*- coding: utf-8 -*-
"""Persisted mercenary contracts; one contract per character and role."""
import time

class DatabaseMercenariesMixin:
    def create_mercenary_schema(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS mercenary_contracts (
            character_account_id INTEGER NOT NULL, role TEXT NOT NULL,
            expires_at REAL NOT NULL, PRIMARY KEY(character_account_id, role)
        )""")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mercenary_expiry ON mercenary_contracts(expires_at)")
        self.conn.commit()

    def mercenary_contracts(self, character_account_id, now=None):
        now = time.time() if now is None else float(now)
        self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=? AND expires_at<=?", (int(character_account_id), now))
        return [dict(row) for row in self.conn.execute(
            "SELECT role,expires_at FROM mercenary_contracts WHERE character_account_id=? ORDER BY role",
            (int(character_account_id),)).fetchall()]

    def hire_mercenary(self, character_account_id, role, price_silver, duration=2700, now=None):
        """Atomic charge and roster update; no await between checking and paying."""
        now = time.time() if now is None else float(now)
        ident = int(character_account_id)
        role = str(role)
        self.mercenary_contracts(ident, now)
        self.conn.execute("SAVEPOINT merc_hire")
        try:
            already = self.conn.execute("SELECT 1 FROM mercenary_contracts WHERE character_account_id=? AND role=?", (ident, role)).fetchone()
            size = self.conn.execute("SELECT COUNT(*) FROM mercenary_contracts WHERE character_account_id=?", (ident,)).fetchone()[0]
            if already:
                result = "duplicate"
            elif size >= 3:
                result = "full"
            else:
                master = self.master_account_for_character(ident)
                coins = int(self.shared_wallet_for_master(master)[0])
                if coins < price_silver:
                    result = "money"
                else:
                    self.set_shared_wallet_for_master(master, coins-price_silver, 0, 0, commit=False)
                    self.conn.execute("INSERT INTO mercenary_contracts VALUES(?,?,?)", (ident, role, now+int(duration)))
                    result = "ok"
            self.conn.execute("RELEASE SAVEPOINT merc_hire")
            if result == "ok":
                self.conn.commit()
            return result
        except Exception:
            self.conn.execute("ROLLBACK TO SAVEPOINT merc_hire")
            self.conn.execute("RELEASE SAVEPOINT merc_hire")
            raise

    def dismiss_mercenary(self, character_account_id, role=None):
        if role:
            self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=? AND role=?",(int(character_account_id),str(role)))
        else:
            self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=?",(int(character_account_id),))
        self.conn.commit()
