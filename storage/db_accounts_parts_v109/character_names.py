# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: character_names."""
from .dependencies import *

class CharacterNamesV109Mixin:
    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def character_account_id_by_name_v0928(self, name):
        row = self.conn.execute(
            "SELECT account_id FROM characters WHERE name=? COLLATE NOCASE",
            (str(name or "").strip(),),
        ).fetchone()
        return int(row["account_id"]) if row else None

    def character_name_by_account_v0928(self, account_id):
        row = self.conn.execute(
            "SELECT name FROM characters WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        return str(row["name"]) if row else None
