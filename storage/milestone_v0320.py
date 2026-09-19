# -*- coding: utf-8 -*-
"""Soulbound v0.32.0 persistence additions."""

def install_v0320_schema(self):
    self.conn.executescript('''
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
    ''')
    self.conn.commit()

def tech_set_mark_v0320(self, account_id, item_id):
    row=self.conn.execute("SELECT mark FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(account_id,item_id)).fetchone()
    return max(1,int(row['mark'])) if row else 1

def set_tech_set_mark_v0320(self, account_id, item_id, mark):
    mark=max(1,min(3,int(mark)))
    self.conn.execute("INSERT INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET mark=excluded.mark",(account_id,item_id,mark))
    self.conn.commit(); return mark

def add_combat_event_v0320(self, account_id, text, kind='combat'):
    if not account_id or not str(text or '').strip(): return
    self.conn.execute("INSERT INTO combat_events_v0320(account_id,event_text,event_kind) VALUES(?,?,?)",(account_id,str(text)[:700],str(kind or 'combat')[:40]))
    # retain only recent 40 per character
    self.conn.execute("DELETE FROM combat_events_v0320 WHERE account_id=? AND id NOT IN (SELECT id FROM combat_events_v0320 WHERE account_id=? ORDER BY id DESC LIMIT 40)",(account_id,account_id))
    self.conn.commit()

def combat_events_v0320(self, account_id, limit=10):
    return self.conn.execute("SELECT event_text,event_kind,created_at FROM combat_events_v0320 WHERE account_id=? ORDER BY id DESC LIMIT ?",(account_id,max(1,min(20,int(limit))))).fetchall()

Database.install_v0320_schema=install_v0320_schema
Database.tech_set_mark_v0320=tech_set_mark_v0320
Database.set_tech_set_mark_v0320=set_tech_set_mark_v0320
Database.add_combat_event_v0320=add_combat_event_v0320
Database.combat_events_v0320=combat_events_v0320
_old_init_v0320=Database.__init__
def _init_v0320(self,*a,**kw):
    _old_init_v0320(self,*a,**kw); self.install_v0320_schema()
Database.__init__=_init_v0320


def set_recap_summary_v0320(self, account_id, final_blow='', cause='', guard_saved=0, healing_saved=0, result=''):
    self.conn.execute("INSERT INTO recap_summary_v0320(account_id,final_blow,cause,guard_saved,healing_saved,result,updated_at) VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP) ON CONFLICT(account_id) DO UPDATE SET final_blow=excluded.final_blow,cause=excluded.cause,guard_saved=excluded.guard_saved,healing_saved=excluded.healing_saved,result=excluded.result,updated_at=CURRENT_TIMESTAMP",(account_id,str(final_blow),str(cause),max(0,int(guard_saved)),max(0,int(healing_saved)),str(result)))
    self.conn.commit()

def recap_summary_v0320(self, account_id):
    return self.conn.execute("SELECT * FROM recap_summary_v0320 WHERE account_id=?",(account_id,)).fetchone()
Database.set_recap_summary_v0320=set_recap_summary_v0320
Database.recap_summary_v0320=recap_summary_v0320


_old_clear_crafting_v0320=Database.clear_equipment_crafting_v0925
def _clear_crafting_v0320(self,account_id,item_id):
    _old_clear_crafting_v0320(self,account_id,item_id)
    self.conn.execute("DELETE FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(account_id,item_id)); self.conn.commit()
Database.clear_equipment_crafting_v0925=_clear_crafting_v0320

_old_transfer_crafting_v0320=Database.transfer_equipment_crafting_v0925
def _transfer_crafting_v0320(self,from_account_id,to_account_id,item_id):
    mark=self.tech_set_mark_v0320(from_account_id,item_id)
    _old_transfer_crafting_v0320(self,from_account_id,to_account_id,item_id)
    if mark>1:
        self.conn.execute("INSERT OR REPLACE INTO tech_set_upgrades_v0320(account_id,item_id,mark) VALUES(?,?,?)",(to_account_id,item_id,mark))
        self.conn.execute("DELETE FROM tech_set_upgrades_v0320 WHERE account_id=? AND item_id=?",(from_account_id,item_id)); self.conn.commit()
Database.transfer_equipment_crafting_v0925=_transfer_crafting_v0320
