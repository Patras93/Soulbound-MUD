# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: gems; AST bez zmian."""
from .dependencies import *

class GemsV109Mixin:
    def socketed_gems(self, account_id, slot, jewelry_item_id=None):
        if jewelry_item_id is None:
            return self.conn.execute(
                "SELECT socket_index,jewelry_item_id,gem_id "
                "FROM equipment_gems "
                "WHERE account_id=? AND slot=? "
                "ORDER BY socket_index",
                (account_id, slot),
            ).fetchall()
        return self.conn.execute(
            "SELECT socket_index,jewelry_item_id,gem_id "
            "FROM equipment_gems "
            "WHERE account_id=? AND slot=? AND jewelry_item_id=? "
            "ORDER BY socket_index",
            (account_id, slot, jewelry_item_id),
        ).fetchall()

    def add_socketed_gem(
        self, account_id, slot, jewelry_item_id,
        socket_index, gem_id,
    ):
        self.conn.execute(
            """
            INSERT INTO equipment_gems(
                account_id,slot,socket_index,jewelry_item_id,gem_id
            ) VALUES(?,?,?,?,?)
            ON CONFLICT(account_id,slot,socket_index)
            DO UPDATE SET
                jewelry_item_id=excluded.jewelry_item_id,
                gem_id=excluded.gem_id
            """,
            (
                account_id, slot, int(socket_index),
                jewelry_item_id, gem_id,
            ),
        )
        self.conn.commit()

    def clear_socketed_gems(self, account_id, slot):
        rows = self.socketed_gems(account_id, slot)
        self.conn.execute(
            "DELETE FROM equipment_gems "
            "WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()
        return rows
