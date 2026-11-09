# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: account_identity."""
from .dependencies import *

class AccountIdentityV109Mixin:
    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def is_character_profile(self, account_id):
        row = self.conn.execute(
            "SELECT 1 FROM account_characters "
            "WHERE character_account_id=? AND master_account_id<>character_account_id",
            (account_id,),
        ).fetchone()
        return row is not None

    def master_account_for_character(self, character_account_id):
        row = self.conn.execute(
            "SELECT master_account_id FROM account_characters "
            "WHERE character_account_id=?",
            (character_account_id,),
        ).fetchone()
        if row:
            return int(row["master_account_id"])
        return int(character_account_id)
