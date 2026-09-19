# -*- coding: utf-8 -*-
"""Persistent Forge & Materials 3.0 state."""
def _v03114_install_schema(self):
    self.conn.executescript("""
    CREATE TABLE IF NOT EXISTS equipment_socket_bonus_v03114(
      account_id INTEGER NOT NULL, item_id TEXT NOT NULL, bonus_sockets INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(account_id,item_id));
    CREATE TABLE IF NOT EXISTS vmax_upgrades_v03114(
      account_id INTEGER PRIMARY KEY, duration_level INTEGER NOT NULL DEFAULT 0, cooling_level INTEGER NOT NULL DEFAULT 0);
    """)
    self.conn.commit()

def equipment_socket_bonus_v03114(self, account_id, item_id):
    row=self.conn.execute("SELECT bonus_sockets FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(account_id,item_id)).fetchone()
    return int(row["bonus_sockets"]) if row else 0

def add_equipment_socket_v03114(self, account_id, item_id, max_bonus=2):
    cur=self.equipment_socket_bonus_v03114(account_id,item_id)
    if cur>=int(max_bonus): return cur
    cur+=1
    self.conn.execute("INSERT INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?) ON CONFLICT(account_id,item_id) DO UPDATE SET bonus_sockets=excluded.bonus_sockets",(account_id,item_id,cur)); self.conn.commit(); return cur

def vmax_upgrades_v03114(self, account_id):
    row=self.conn.execute("SELECT duration_level,cooling_level FROM vmax_upgrades_v03114 WHERE account_id=?",(account_id,)).fetchone()
    return (int(row['duration_level']),int(row['cooling_level'])) if row else (0,0)

def add_vmax_upgrade_v03114(self, account_id, kind):
    d,c=self.vmax_upgrades_v03114(account_id)
    if kind=='duration': d=min(3,d+1)
    else: c=min(2,c+1)
    self.conn.execute("INSERT INTO vmax_upgrades_v03114(account_id,duration_level,cooling_level) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET duration_level=excluded.duration_level,cooling_level=excluded.cooling_level",(account_id,d,c)); self.conn.commit(); return d,c

_old_init_v03114=Database.__init__
def _init_v03114(self,*a,**kw):
    _old_init_v03114(self,*a,**kw); _v03114_install_schema(self)
Database.__init__=_init_v03114
Database.equipment_socket_bonus_v03114=equipment_socket_bonus_v03114
Database.add_equipment_socket_v03114=add_equipment_socket_v03114
Database.vmax_upgrades_v03114=vmax_upgrades_v03114
Database.add_vmax_upgrade_v03114=add_vmax_upgrade_v03114

_old_clear_crafting_v03114=Database.clear_equipment_crafting_v0925
def _clear_crafting_v03114(self,account_id,item_id):
    _old_clear_crafting_v03114(self,account_id,item_id)
    self.conn.execute("DELETE FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(account_id,item_id)); self.conn.commit()
Database.clear_equipment_crafting_v0925=_clear_crafting_v03114

_old_transfer_crafting_v03114=Database.transfer_equipment_crafting_v0925
def _transfer_crafting_v03114(self,from_account_id,to_account_id,item_id):
    bonus=self.equipment_socket_bonus_v03114(from_account_id,item_id)
    _old_transfer_crafting_v03114(self,from_account_id,to_account_id,item_id)
    if bonus>0:
        self.conn.execute("INSERT OR REPLACE INTO equipment_socket_bonus_v03114(account_id,item_id,bonus_sockets) VALUES(?,?,?)",(to_account_id,item_id,bonus))
        self.conn.execute("DELETE FROM equipment_socket_bonus_v03114 WHERE account_id=? AND item_id=?",(from_account_id,item_id)); self.conn.commit()
Database.transfer_equipment_crafting_v0925=_transfer_crafting_v03114
