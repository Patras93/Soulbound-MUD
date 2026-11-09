# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: character_slots."""
from .dependencies import *

class CharacterSlotsV109Mixin:
    def _next_character_slot(self, master_account_id):
        used = {
            int(r["slot"]) for r in self.conn.execute(
                "SELECT slot FROM account_characters WHERE master_account_id=?",
                (master_account_id,),
            ).fetchall()
        }
        for slot in range(1, MAX_CHARACTERS_PER_ACCOUNT + 1):
            if slot not in used:
                return slot
        return None

    def _create_hidden_character_account(self, master_account_id, slot):
        # Profil jest wyłącznie technicznym kluczem danych postaci. Nie można
        # zalogować się do niego z ekranu logowania.
        while True:
            username = f"__char_{master_account_id}_{slot}_{secrets.token_hex(6)}"
            if not self.account_by_name(username):
                break
        salt, digest = hash_password(secrets.token_urlsafe(32))
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        return int(cur.lastrowid)
