# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: inventory; AST bez zmian."""
from .dependencies import *

class InventoryV109Mixin:
    def _persisted_dynamic_item_ids(self, prefix, log_label):
        """Find self-describing dynamic item IDs across inventory-like storage."""
        prefix=str(prefix or "")
        found=set()
        tables=self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table_row in tables:
            table=str(table_row[0])
            if not table.replace("_","").isalnum():
                continue
            try:
                cols=[str(row[1]) for row in self.conn.execute(f"PRAGMA table_info({table})").fetchall()]
            except Exception:
                continue
            for col in cols:
                if col not in ("item_id","jewelry_item_id","attachment_item_id"):
                    continue
                try:
                    rows=self.conn.execute(
                        f"SELECT DISTINCT {col} FROM {table} WHERE {col} LIKE ?",
                        (prefix+"%",),
                    ).fetchall()
                    found.update(str(row[0]) for row in rows if row[0])
                except Exception as exc:
                    print(f"{log_label}_SCAN_TABLE_ERROR: {type(exc).__name__}: {exc}", flush=True)
        # Housing 2.0 stores item IDs inside JSON rather than a normal item_id column.
        try:
            import json as _json
            rows=self.conn.execute("SELECT storage_json FROM player_housing_v03051").fetchall()
            for row in rows:
                try:
                    box=_json.loads(row[0] or "{}")
                except Exception:
                    continue
                if isinstance(box,dict):
                    for item_id in box:
                        item_id=str(item_id or "")
                        if item_id.startswith(prefix):
                            found.add(item_id)
        except Exception as exc:
            print(f"{log_label}_HOUSING_SCAN_ERROR: {type(exc).__name__}: {exc}", flush=True)
        return sorted(found)

    def persisted_crafting_quality_item_ids_v0332(self):
        return self._persisted_dynamic_item_ids("craftq_", "CRAFTQ")

    def persisted_infinite_equipment_item_ids_v11330(self):
        return self._persisted_dynamic_item_ids("deepq_", "DEEPQ")

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def drop_history_rows(self, account_id, limit=20):
        return self.conn.execute(
            "SELECT item_name,rarity,source,zone,created_at FROM drop_history "
            "WHERE account_id=? ORDER BY id DESC LIMIT ?",
            (account_id, max(1, min(DROP_HISTORY_LIMIT, int(limit)))),
        ).fetchall()

    def remove_item(self, account_id, item_id, qty=1, commit=True):
        from systems.equipment_inventory_flow_v10600 import tracked, remove
        if tracked(self, item_id):
            return remove(self, account_id, item_id, qty, commit=commit)
        from systems.equipment_evolution_v10500 import is_evolved
        if is_evolved(self.conn, account_id, item_id):
            return False  # evolved EQ cannot disappear while its stage is bound
        qty = max(1, int(qty))
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self._consume_shop_purchase_lots_v1175(account_id, item_id, qty)
        if commit:
            self.conn.commit()
        return True

    def transfer_inventory_item(self, from_account_id, to_account_id, item_id, qty=1):
        """Atomowo przenosi zwykły item inventory między dwiema postaciami."""
        from systems.equipment_inventory_flow_v10600 import tracked, transfer
        if tracked(self, item_id):
            return transfer(self, from_account_id, to_account_id, item_id, qty)
        from systems.equipment_evolution_v10500 import is_evolved
        if is_evolved(self.conn, from_account_id, item_id):
            return False  # evolved EQ is character-bound
        qty = max(1, int(qty))
        if from_account_id == to_account_id:
            return False
        current = self.item_qty(from_account_id, item_id)
        if current < qty:
            return False
        try:
            self.conn.execute("BEGIN")
            new_qty = current - qty
            if new_qty <= 0:
                self.conn.execute(
                    "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                    (from_account_id, item_id),
                )
            else:
                self.conn.execute(
                    "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                    (new_qty, from_account_id, item_id),
                )
            self.conn.execute(
                """
                INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
                ON CONFLICT(account_id,item_id)
                DO UPDATE SET quantity=quantity+excluded.quantity
                """,
                (to_account_id, item_id, qty),
            )
            self._consume_shop_purchase_lots_v1175(
                from_account_id, item_id, qty, transfer_to=to_account_id
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise
