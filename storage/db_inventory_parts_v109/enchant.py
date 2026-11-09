# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: enchant; AST bez zmian."""
from .dependencies import *

class EnchantV109Mixin:
    def equipment_enchant_v03053(self, account_id, slot):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? AND slot=?",(account_id,slot)).fetchone()

    def set_equipment_enchant_v03053(self, account_id, slot, enchant_key, stat, amount):
        self.conn.execute("INSERT INTO equipment_enchants_v03053(account_id,slot,enchant_key,stat,amount) VALUES(?,?,?,?,?) ON CONFLICT(account_id,slot) DO UPDATE SET enchant_key=excluded.enchant_key,stat=excluded.stat,amount=excluded.amount,updated_at=CURRENT_TIMESTAMP",(account_id,slot,enchant_key,stat,int(amount)))
        self.conn.commit()

    def equipment_enchants_v03053(self, account_id):
        return self.conn.execute("SELECT * FROM equipment_enchants_v03053 WHERE account_id=? ORDER BY slot",(account_id,)).fetchall()
