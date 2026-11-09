# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: character_deletion."""
from .dependencies import *

class CharacterDeletionV109Mixin:
    def _delete_character_mercenary_data_v3002(self, character_account_id):
        """Wipe character-bound mercenaries, including tables without account FK.

        Mercenary tables use character_account_id (rather than account_id) and
        have no REFERENCES accounts CASCADE. Wiping a primary character used
        to leave its hires and tactics on the durable login id; deleting a
        secondary character leaked orphaned contracts too.
        """
        char_id = int(character_account_id)
        self.conn.execute(
            "DELETE FROM mercenary_contracts WHERE character_account_id=?", (char_id,)
        )
        self.conn.execute(
            "DELETE FROM mercenary_progress_v1220 WHERE character_account_id=?", (char_id,)
        )

    def wipe_characters_for_master(self, master_account_id):
        """Usuń postacie/progres/najemników konta, zachowując login i hasło."""
        master_account_id = int(master_account_id)
        rows = self.conn.execute(
            "SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot",
            (master_account_id,),
        ).fetchall()
        char_ids = [int(row["character_account_id"]) for row in rows]

        # Najemnicy nie mają ON DELETE CASCADE i używają innego klucza niż
        # pozostałe tabele. Czyść ich kontrakty i zapis taktyki dla KAŻDEJ
        # usuwanej postaci, zanim skasujesz profil techniczny.
        for char_id in char_ids:
            self._delete_character_mercenary_data_v3002(char_id)

        # Ukryte konta profili można bezpiecznie usunąć — FK CASCADE czyści ich dane.
        for char_id in char_ids:
            if char_id != master_account_id:
                self.conn.execute("DELETE FROM accounts WHERE id=?", (char_id,))

        # Pierwsza postać może używać ID konta głównego, więc kasujemy jej dane,
        # ale nigdy rekordu logowania w accounts.
        if master_account_id in char_ids:
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {
                "accounts", "account_characters", "account_wallet",
                # These belong to the LOGIN account, never to the character.
                "account_emails_v1223", "email_password_reset_v1223", "password_recovery_v1222",
            }
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )

        self.conn.execute(
            "DELETE FROM account_characters WHERE master_account_id=?",
            (master_account_id,),
        )
        # Portfel jest częścią postępu gry, nie danych logowania. Nowa pierwsza
        # postać ponownie dostanie normalny pakiet startowy.
        self.conn.execute(
            "DELETE FROM account_wallet WHERE master_account_id=?",
            (master_account_id,),
        )
        self.conn.commit()
        return len(char_ids)

    def delete_character_for_master(self, master_account_id, character_account_id):
        """v0.9.1: usuń dokładnie jedną postać bez kasowania konta ani wspólnego portfela.

        Pierwsza postać może używać ID konta głównego, dlatego nie wolno wtedy
        usuwać rekordu z accounts. Dodatkowe postacie mają ukryte konta techniczne
        i ich usunięcie przez FK CASCADE czyści cały własny progres postaci.
        """
        master_account_id = int(master_account_id)
        character_account_id = int(character_account_id)
        row = self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.name
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? AND ac.character_account_id=?
            """,
            (master_account_id, character_account_id),
        ).fetchone()
        if not row:
            return None

        slot = int(row["slot"])
        name = str(row["name"])

        # Również "usuń jedną postać" musi czyścić trwałe najmy i ich taktyki.
        self._delete_character_mercenary_data_v3002(character_account_id)
        if character_account_id != master_account_id:
            # Ukryty profil postaci. Usunięcie konta technicznego uruchamia
            # ON DELETE CASCADE dla całego progresu i samego powiązania slotu.
            self.conn.execute(
                "DELETE FROM accounts WHERE id=?", (character_account_id,)
            )
        else:
            # Slot oparty na koncie głównym: zachowujemy login, hasło i
            # account_wallet, a czyścimy wyłącznie dane tej postaci.
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {
                "accounts", "account_characters", "account_wallet",
                # These belong to the LOGIN account, never to the character.
                "account_emails_v1223", "email_password_reset_v1223", "password_recovery_v1222",
            }
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND character_account_id=?",
                (master_account_id, character_account_id),
            )

        self.conn.commit()
        return {"slot": slot, "name": name}

    def wipe_all_characters_preserve_accounts(self):
        masters = [
            int(row["id"])
            for row in self.conn.execute(
                "SELECT id FROM accounts WHERE id NOT IN ("
                "SELECT character_account_id FROM account_characters "
                "WHERE character_account_id<>master_account_id) ORDER BY id"
            ).fetchall()
        ]
        removed = 0
        for master_id in masters:
            removed += self.wipe_characters_for_master(master_id)
        # Tylko JAWNY globalny wipe: po usunieciu wszystkich postaci
        # sprzatamy rowniez historyczne osierocone wynajmy i taktyki.
        # Nie robimy tego przy zwyklym starcie ani migracji SQLite.
        self.conn.execute("DELETE FROM mercenary_contracts")
        self.conn.execute("DELETE FROM mercenary_progress_v1220")
        self.conn.commit()
        return removed, masters
