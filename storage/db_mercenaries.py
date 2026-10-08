# -*- coding: utf-8 -*-
"""Persisted, permanent mercenary contracts; one per character and role."""
import time

class DatabaseMercenariesMixin:
    def create_mercenary_schema(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS mercenary_contracts (
            character_account_id INTEGER NOT NULL, role TEXT NOT NULL,
            expires_at REAL NOT NULL, PRIMARY KEY(character_account_id, role)
        )""")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_mercenary_expiry ON mercenary_contracts(expires_at)")
        # v1.21.2: retain the existing schema and preserve currently active
        # 45-minute hires when upgrading. Remove expired historical hires,
        # then turn valid hires into permanent contracts using sentinel 0.
        self.conn.execute("DELETE FROM mercenary_contracts WHERE expires_at>0 AND expires_at<=?", (time.time(),))
        self.conn.execute("UPDATE mercenary_contracts SET expires_at=0 WHERE expires_at>0")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS mercenary_progress_v1220 (
            character_account_id INTEGER NOT NULL, role TEXT NOT NULL,
            xp INTEGER NOT NULL DEFAULT 0, specialization TEXT NOT NULL DEFAULT '',
            actions INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(character_account_id,role)
        )""")
        self.conn.commit()

    def mercenary_progress_v1220(self, character_account_id, role):
        row = self.conn.execute(
            "SELECT xp,specialization,actions FROM mercenary_progress_v1220 "
            "WHERE character_account_id=? AND role=?",
            (int(character_account_id), str(role)),
        ).fetchone()
        return dict(row) if row else {"xp": 0, "specialization": "", "actions": 0}

    def mercenary_gain_xp_v1220(self, character_account_id, role, xp):
        self.conn.execute(
            "INSERT INTO mercenary_progress_v1220(character_account_id,role,xp,actions) "
            "VALUES(?,?,?,1) ON CONFLICT(character_account_id,role) "
            "DO UPDATE SET xp=xp+excluded.xp,actions=actions+1",
            (int(character_account_id), str(role), max(1,int(xp))),
        )
        self.conn.commit()
        return self.mercenary_progress_v1220(character_account_id,role)

    def mercenary_specialize_v1220(self, character_account_id, role, name, owner_level=1):
        """Choose a specialization based on the OWNER's level (v1.22.8)."""
        from systems.mercenary_growth_v1220 import SPECIALIZATIONS
        if name not in SPECIALIZATIONS:
            return "unknown"
        hired = self.conn.execute(
            "SELECT 1 FROM mercenary_contracts WHERE character_account_id=? AND role=?",
            (int(character_account_id), str(role)),
        ).fetchone()
        if not hired:
            return "not_hired"
        current = self.mercenary_progress_v1220(character_account_id, role)
        if current['specialization']:
            return "already"
        if max(1, int(owner_level or 1)) < 10:
            return "level"
        self.conn.execute(
            "INSERT OR IGNORE INTO mercenary_progress_v1220(character_account_id,role) VALUES (?,?)",
            (int(character_account_id),str(role)),
        )
        self.conn.execute(
            "UPDATE mercenary_progress_v1220 SET specialization=? "
            "WHERE character_account_id=? AND role=? AND specialization=''",
            (str(name),int(character_account_id),str(role)),
        )
        self.conn.commit()
        return "ok"

    def mercenary_contracts(self, character_account_id, now=None):
        now = time.time() if now is None else float(now)
        self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=? AND expires_at>0 AND expires_at<=?", (int(character_account_id), now))
        return [dict(row) for row in self.conn.execute(
            "SELECT role,expires_at FROM mercenary_contracts WHERE character_account_id=? ORDER BY role",
            (int(character_account_id),)).fetchall()]

    def hire_mercenary(self, character_account_id, role, price_silver, duration=0, now=None):
        """One-time payment for a permanent hire; duration is legacy-only."""
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
                    self.conn.execute("INSERT INTO mercenary_contracts VALUES(?,?,?)", (ident, role, 0.0))
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
            result = self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=? AND role=?",(int(character_account_id),str(role)))
        else:
            result = self.conn.execute("DELETE FROM mercenary_contracts WHERE character_account_id=?",(int(character_account_id),))
        self.conn.commit()
        return result.rowcount
