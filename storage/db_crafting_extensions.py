# -*- coding: utf-8 -*-
'''Persistent crafting/recap extensions without runtime monkey-patching.

v0.46.0 consolidates the historical v0.31.14 and v0.32.0 Database patches
into a normal mixin. Public method names and SQLite table names stay unchanged.'''


class DatabaseCraftingExtensionsMixin:
    def install_crafting_extensions_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS equipment_socket_bonus_v03114(
          account_id INTEGER NOT NULL, item_id TEXT NOT NULL, bonus_sockets INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY(account_id,item_id));
        CREATE TABLE IF NOT EXISTS vmax_upgrades_v03114(
          account_id INTEGER PRIMARY KEY, duration_level INTEGER NOT NULL DEFAULT 0, cooling_level INTEGER NOT NULL DEFAULT 0);
        """)
        self.install_v0320_schema()
        self.conn.commit()

    def equipment_socket_bonus_v03114(self, account_id, item_id):
        row=self.conn.execute("SELECT bonus_sockets FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(account_id,item_id)).fetchone()
        return int(row["bonus_sockets"]) if row else 0

    def add_equipment_socket_v03114(self, account_id, item_id, max_bonus=2):
        cur=self.equipment_socket_bonus_v03114(account_id,item_id)
        if cur>=int(max_bonus): return cur
        cur+=1
        self.conn.execute("INSERT INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET bonus_sockets=excluded.bonus_sockets",(account_id,item_id,cur))
        self.conn.commit()
        return cur

    def vmax_upgrades_v03114(self, account_id):
        row=self.conn.execute("SELECT duration_level,cooling_level FROM vmax_upgrades_v03114 WHERE account_id=?",(account_id,)).fetchone()
        return (int(row['duration_level']),int(row['cooling_level'])) if row else (0,0)

    def add_vmax_upgrade_v03114(self, account_id, kind):
        d,c=self.vmax_upgrades_v03114(account_id)
        if kind=='duration': d=min(3,d+1)
        else: c=min(2,c+1)
        self.conn.execute("INSERT INTO vmax_upgrades_v03114(account_id,duration_level,cooling_level) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET duration_level=excluded.duration_level,cooling_level=excluded.cooling_level",(account_id,d,c))
        self.conn.commit()
        return d,c

    def install_v0320_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS tech_set_upgrades_v0320(
          account_id INTEGER NOT NULL,
          item_id TEXT NOT NULL,
          mark INTEGER NOT NULL DEFAULT 1,
          PRIMARY KEY(account_id,item_id)
        );
        CREATE TABLE IF NOT EXISTS combat_events_v0320(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          account_id INTEGER NOT NULL,
          event_text TEXT NOT NULL,
          event_kind TEXT NOT NULL DEFAULT 'combat',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_combat_events_v0320_account ON combat_events_v0320(account_id,id DESC);
        CREATE TABLE IF NOT EXISTS recap_summary_v0320(
          account_id INTEGER PRIMARY KEY, final_blow TEXT NOT NULL DEFAULT '', cause TEXT NOT NULL DEFAULT '',
          guard_saved INTEGER NOT NULL DEFAULT 0, healing_saved INTEGER NOT NULL DEFAULT 0, result TEXT NOT NULL DEFAULT '',
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()

    def tech_set_mark_v0320(self, account_id, item_id):
        row=self.conn.execute("SELECT mark FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(account_id,item_id)).fetchone()
        return max(1,int(row['mark'])) if row else 1

    def set_tech_set_mark_v0320(self, account_id, item_id, mark):
        mark=max(1,min(3,int(mark)))
        self.conn.execute("INSERT INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET mark=excluded.mark",(account_id,item_id,mark))
        self.conn.commit()
        return mark

    def add_combat_event_v0320(self, account_id, text, kind='combat'):
        if not account_id or not str(text or '').strip(): return
        self.conn.execute("INSERT INTO combat_events_v0320(account_id,event_text,event_kind) VALUES(?,?,?)",(account_id,str(text)[:700],str(kind or 'combat')[:40]))
        self.conn.execute("DELETE FROM combat_events_v0320 WHERE account_id=? AND id NOT IN (SELECT id FROM combat_events_v0320 WHERE account_id=? ORDER BY id DESC LIMIT 40)",(account_id,account_id))
        self.conn.commit()

    def combat_events_v0320(self, account_id, limit=10):
        return self.conn.execute("SELECT event_text,event_kind,created_at FROM combat_events_v0320 WHERE account_id=? ORDER BY id DESC LIMIT ?",(account_id,max(1,min(20,int(limit))))).fetchall()

    def set_recap_summary_v0320(self, account_id, final_blow='', cause='', guard_saved=0, healing_saved=0, result=''):
        self.conn.execute("INSERT INTO recap_summary_v0320(account_id,final_blow,cause,guard_saved,healing_saved,result,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(account_id) DO UPDATE SET final_blow=excluded.final_blow,cause=excluded.cause,guard_saved=excluded.guard_saved,healing_saved=excluded.healing_saved,result=excluded.result,updated_at=CURRENT_TIMESTAMP",(account_id,str(final_blow),str(cause),max(0,int(guard_saved)),max(0,int(healing_saved)),str(result)))
        self.conn.commit()

    def recap_summary_v0320(self, account_id):
        return self.conn.execute("SELECT * FROM recap_summary_v0320 WHERE account_id=?",(account_id,)).fetchone()

    def clear_equipment_crafting_v0925(self, account_id, item_id):
        super().clear_equipment_crafting_v0925(account_id,item_id)
        self.conn.execute("DELETE FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(account_id,item_id))
        self.conn.execute("DELETE FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(account_id,item_id))
        self.conn.commit()

    def transfer_equipment_crafting_v0925(self, from_account_id, to_account_id, item_id):
        bonus=self.equipment_socket_bonus_v03114(from_account_id,item_id)
        mark=self.tech_set_mark_v0320(from_account_id,item_id)
        super().transfer_equipment_crafting_v0925(from_account_id,to_account_id,item_id)
        if bonus>0:
            self.conn.execute("INSERT OR REPLACE INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?)",(to_account_id,item_id,bonus))
            self.conn.execute("DELETE FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        if mark>1:
            self.conn.execute("INSERT OR REPLACE INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?)",(to_account_id,item_id,mark))
            self.conn.execute("DELETE FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        self.conn.commit()
