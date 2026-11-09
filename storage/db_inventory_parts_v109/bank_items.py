# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: bank_items; AST bez zmian."""
from .dependencies import *

class BankItemsV109Mixin:
    def bank_items(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM bank_items "
            "WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def bank_item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM bank_items "
            "WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def move_bank_equipment_v106(self, account_id, item_id, qty=1, *, withdraw=False, commit=True):
        """Staging-only atomic move, never used by legacy banking methods."""
        from systems.equipment_inventory_flow_v10600 import bank_move
        return bank_move(self, account_id, item_id, qty, withdraw=withdraw, commit=commit)

    def add_bank_item(self, account_id, item_id, qty=1):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'bank.deposit')
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = max(1, require_sqlite_int64('bank_items.increment', qty))
        current = self.conn.execute(
            'SELECT quantity FROM bank_items WHERE account_id=? AND item_id=?',
            (account_id, item_id)).fetchone()
        balance = self._v104_crafting_quantity(current[0]) if current else 0
        require_sqlite_int64('bank_items.quantity', balance + qty)
        self.conn.execute(
            """
            INSERT INTO bank_items(account_id,item_id,quantity)
            VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_bank_item(self, account_id, item_id, qty=1):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'bank.withdraw')
        qty = max(1, int(qty))
        current = self.bank_item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM bank_items "
                "WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE bank_items SET quantity=? "
                "WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True
