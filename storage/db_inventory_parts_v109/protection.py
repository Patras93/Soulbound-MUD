# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: protection; AST bez zmian."""
from .dependencies import *

class ProtectionV109Mixin:
    def inventory_is_protected_v1280(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT 1 FROM protected_inventory_v1280 WHERE account_id=? AND item_id=?",
            (int(account_id), str(item_id)),
        ).fetchone()
        return bool(row)

    def inventory_set_protected_v1280(self, account_id, item_id, state):
        if state:
            self.conn.execute(
                "INSERT OR IGNORE INTO protected_inventory_v1280(account_id,item_id) VALUES (?,?)",
                (int(account_id), str(item_id)),
            )
        else:
            self.conn.execute(
                "DELETE FROM protected_inventory_v1280 WHERE account_id=? AND item_id=?",
                (int(account_id), str(item_id)),
            )
        self.conn.commit()
