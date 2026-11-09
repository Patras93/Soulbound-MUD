# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: master_accounts."""
from .dependencies import *

class MasterAccountsV109Mixin:
    def account_name(self, account_id):
        row = self.conn.execute(
            "SELECT username FROM accounts WHERE id=?", (int(account_id),)
        ).fetchone()
        return str(row["username"]) if row else ""

    def master_accounts(self):
        """v0.30.1: lista prawdziwych kont logowania, bez ukrytych profili postaci."""
        return self.conn.execute(
            """
            SELECT a.id,a.username,COUNT(ac.character_account_id) AS character_count
            FROM accounts a
            LEFT JOIN account_characters ac ON ac.master_account_id=a.id
            WHERE a.id NOT IN (
                SELECT character_account_id FROM account_characters
                WHERE character_account_id<>master_account_id
            )
            GROUP BY a.id,a.username
            ORDER BY a.username COLLATE NOCASE,a.id
            """
        ).fetchall()

    def master_account_by_name(self, username):
        """v0.30.1: znajdź tylko konto główne; profil techniczny postaci nie jest celem admina."""
        return self.conn.execute(
            """
            SELECT a.* FROM accounts a
            WHERE a.username=? COLLATE NOCASE
              AND a.id NOT IN (
                  SELECT character_account_id FROM account_characters
                  WHERE character_account_id<>master_account_id
              )
            """,
            (username,),
        ).fetchone()
