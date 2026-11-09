# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: shop_lots; AST bez zmian."""
from .dependencies import *

class ShopLotsV109Mixin:
    def record_shop_purchase_v1175(self, account_id, item_id, quantity, unit_paid_silver, commit=True):
        """Remember cash paid for each purchased inventory unit, including Charisma discount."""
        quantity = max(1, int(quantity))
        unit_paid_silver = max(0, int(unit_paid_silver))
        self.conn.execute(
            "INSERT INTO shop_purchase_lots_v1175(account_id,item_id,paid_silver,quantity) "
            "VALUES(?,?,?,?) ON CONFLICT(account_id,item_id,paid_silver) "
            "DO UPDATE SET quantity=quantity+excluded.quantity",
            (account_id, str(item_id), unit_paid_silver, quantity),
        )
        if commit:
            self.conn.commit()

    def shop_resale_total_v1175(self, account_id, item_id, quantity, normal_unit_silver):
        """Purchased units cannot resell above paid cash; earned loot keeps normal value."""
        remaining = max(0, int(quantity))
        normal_unit_silver = max(0, int(normal_unit_silver))
        total = 0
        for row in self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(item_id)),
        ):
            units = min(remaining, int(row['quantity']))
            total += units * min(normal_unit_silver, max(0, int(row['paid_silver'])))
            remaining -= units
            if remaining <= 0:
                break
        return total + remaining * normal_unit_silver

    def _consume_shop_purchase_lots_v1175(self, account_id, item_id, quantity, *, transfer_to=None):
        """Follow inventory removals and player-to-player transfers; caller owns transaction."""
        remaining = max(0, int(quantity))
        rows = self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(item_id)),
        ).fetchall()
        for row in rows:
            units = min(remaining, int(row['quantity']))
            if not units:
                break
            cost = int(row['paid_silver'])
            if units == int(row['quantity']):
                self.conn.execute(
                    "DELETE FROM shop_purchase_lots_v1175 "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (account_id, str(item_id), cost),
                )
            else:
                self.conn.execute(
                    "UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (units, account_id, str(item_id), cost),
                )
            if transfer_to is not None:
                self.record_shop_purchase_v1175(
                    transfer_to, item_id, units, cost, commit=False
                )
            remaining -= units
        self.conn.execute(
            "DELETE FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? AND quantity<=0",
            (account_id, str(item_id)),
        )

    def bank_purchase_lot_key_v1175(self, item_id):
        return "__bank_v1175__:" + str(item_id)

    def move_shop_purchase_basis_v1175(self, account_id, from_item_id, to_item_id, quantity):
        """Carry shop cost basis into/out of bank storage without minting cheap inventory."""
        remaining = max(0, int(quantity))
        rows = self.conn.execute(
            "SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 "
            "WHERE account_id=? AND item_id=? ORDER BY paid_silver ASC",
            (account_id, str(from_item_id)),
        ).fetchall()
        for row in rows:
            units = min(remaining, int(row["quantity"]))
            if not units:
                break
            price = int(row["paid_silver"])
            if units == int(row['quantity']):
                self.conn.execute(
                    "DELETE FROM shop_purchase_lots_v1175 "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (account_id, str(from_item_id), price),
                )
            else:
                self.conn.execute(
                    "UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? "
                    "WHERE account_id=? AND item_id=? AND paid_silver=?",
                    (units, account_id, str(from_item_id), price),
                )
            self.record_shop_purchase_v1175(
                account_id, to_item_id, units, price, commit=False
            )
            remaining -= units
        self.conn.execute(
            "DELETE FROM shop_purchase_lots_v1175 WHERE account_id=? "
            "AND item_id=? AND quantity<=0", (account_id, str(from_item_id)),
        )
        self.conn.commit()
