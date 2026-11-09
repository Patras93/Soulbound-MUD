# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: storage; AST bez zmian."""
from .dependencies import *

class StorageV109Mixin:
    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def move_storage_equipment_v106(self, account_id, container, item_id, qty=1,
                                     *, withdraw=False, commit=True):
        """Opt-in physical gear move, disposable staging copy only."""
        from systems.equipment_inventory_flow_v10600 import storage_move
        return storage_move(self, account_id, container, item_id, qty,
                            withdraw=withdraw, commit=commit)

    def add_storage_item(self, account_id, container, item_id, qty=1, commit=True):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'storage.deposit')
        from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
        qty = max(1, require_sqlite_int64('storage.increment', qty))
        current = self.conn.execute(
            'SELECT quantity FROM profession_storage WHERE account_id=? '
            'AND container=? AND item_id=?', (account_id, container, item_id)).fetchone()
        balance = self._v104_crafting_quantity(current[0]) if current else 0
        require_sqlite_int64('storage.quantity', balance + qty)
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        if commit:
            self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1, commit=True):
        from systems.equipment_inventory_flow_v10600 import forbid_unintegrated
        forbid_unintegrated(self, item_id, 'storage.withdraw')
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        if commit:
            self.conn.commit()
        return True
