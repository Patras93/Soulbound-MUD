# -*- coding: utf-8 -*-
"""Accounts, characters, shared wallet and presence."""

import secrets
import time
import hashlib
import hmac

from core.bootstrap_economy_professions import (
    MAX_CHARACTERS_PER_ACCOUNT, STARTING_GOLD, STARTING_MITHRIL, STARTING_SILVER,
    normalize_currency_values,
)
from core.classes_skills import class_starting_stats_for
from storage.db_shared import hash_password

class DatabaseAccountsMixin:
    def issue_password_recovery_v1222(self, account_id, kind, *, now=None):
        """Only called by an authenticated owner or a whitelisted administrator.

        Returns a plaintext bearer code exactly once; SQLite stores only its hash.
        """
        if kind not in ("backup", "admin"):
            raise ValueError("Invalid recovery type")
        account_id = int(account_id)
        now = int(time.time() if now is None else now)
        row = self.conn.execute("SELECT id FROM accounts WHERE id=?", (account_id,)).fetchone()
        if row is None or self.is_character_profile(account_id):
            return None
        previous = self.conn.execute(
            "SELECT issued_at FROM password_recovery_v1222 WHERE account_id=? AND kind=?",
            (account_id, kind),
        ).fetchone()
        if previous is not None and now - int(previous["issued_at"]) < 60:
            return None
        code = secrets.token_hex(16).upper()  # 128-bit token, safe to type with NVDA.
        digest = hashlib.sha256(code.encode("ascii")).hexdigest()
        expires = now + (15 * 60 if kind == "admin" else 365 * 24 * 3600)
        self.conn.execute(
            "INSERT INTO password_recovery_v1222(account_id,kind,code_hash,expires_at,attempts,issued_at) "
            "VALUES(?,?,?,?,0,?) ON CONFLICT(account_id,kind) DO UPDATE SET "
            "code_hash=excluded.code_hash,expires_at=excluded.expires_at,attempts=0,issued_at=excluded.issued_at",
            (account_id, kind, digest, expires, now),
        )
        self.conn.commit()
        return code

    def reset_password_with_code_v1222(self, username, code, new_password, *, now=None):
        """Atomically redeem a one-time code, revoke others, rotate password salt."""
        now = int(time.time() if now is None else now)
        if not isinstance(new_password, str) or len(new_password) < 10 or len(new_password) > 256:
            return False
        code = str(code or "").strip().upper().replace("-", "")
        if len(code) != 32 or any(ch not in "0123456789ABCDEF" for ch in code):
            return False
        target = self.master_account_by_name(str(username or "").strip())
        if target is None:
            return False
        account_id = int(target["id"])
        digest = hashlib.sha256(code.encode("ascii")).hexdigest()
        # BEGIN IMMEDIATE prevents competing redemption from consuming the same code.
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            records = self.conn.execute(
                "SELECT kind,code_hash,expires_at,attempts FROM password_recovery_v1222 "
                "WHERE account_id=?", (account_id,),
            ).fetchall()
            valid = any(
                int(row["expires_at"]) >= now and int(row["attempts"]) < 5
                and hmac.compare_digest(str(row["code_hash"]), digest)
                for row in records
            )
            if not valid:
                self.conn.execute(
                    "UPDATE password_recovery_v1222 SET attempts=attempts+1 "
                    "WHERE account_id=? AND expires_at>=? AND attempts<5",
                    (account_id, now),
                )
                self.conn.commit()
                return False
            salt, password_hash = hash_password(new_password)
            self.conn.execute(
                "UPDATE accounts SET password_salt=?,password_hash=? WHERE id=?",
                (salt, password_hash, account_id),
            )
            self.conn.execute("DELETE FROM password_recovery_v1222 WHERE account_id=?", (account_id,))
            self.conn.execute("DELETE FROM email_password_reset_v1223 WHERE account_id=?", (account_id,))
            self.conn.commit()
            return True
        except BaseException:
            self.conn.rollback()
            raise

    def verified_account_email_v1223(self, account_id):
        row = self.conn.execute(
            "SELECT email FROM account_emails_v1223 WHERE account_id=?", (int(account_id),)
        ).fetchone()
        return str(row["email"]) if row else None

    def email_taken_v1223(self, email):
        return self.conn.execute(
            "SELECT 1 FROM account_emails_v1223 WHERE email=? COLLATE NOCASE", (email,)
        ).fetchone() is not None

    def create_account_verified_email_v1223(self, username, password, email):
        """Create the login and its verified email atomically, never orphan a login."""
        from network.account_email_v1223 import normalized_email_v1223
        email = normalized_email_v1223(email)
        if email is None:
            raise ValueError("Nieprawidlowy email")
        salt, digest = hash_password(password)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
                (username, salt, digest),
            )
            self.conn.execute(
                "INSERT INTO account_emails_v1223(account_id,email,verified_at) VALUES(?,?,?)",
                (cur.lastrowid, email, int(time.time())),
            )
        return cur.lastrowid

    def attach_verified_email_v1223(self, account_id, email):
        from network.account_email_v1223 import normalized_email_v1223
        email = normalized_email_v1223(email)
        if email is None or self.is_character_profile(account_id):
            raise ValueError("Nieprawidlowy email lub konto techniczne")
        with self.conn:
            self.conn.execute(
                "INSERT INTO account_emails_v1223(account_id,email,verified_at) VALUES(?,?,?) "
                "ON CONFLICT(account_id) DO UPDATE SET email=excluded.email, "
                "verified_at=excluded.verified_at",
                (int(account_id), email, int(time.time())),
            )
            # Old mailbox must not be able to redeem a pending reset after change.
            self.conn.execute("DELETE FROM email_password_reset_v1223 WHERE account_id=?", (int(account_id),))

    def issue_email_reset_v1223(self, username, *, now=None):
        """Hash-only stored token and per-account rate limit. Plaintext sent once."""
        target = self.master_account_by_name(str(username or "").strip())
        if target is None:
            return None
        account_id = int(target["id"])
        email = self.verified_account_email_v1223(account_id)
        if not email:
            return None
        now = int(time.time() if now is None else now)
        prev = self.conn.execute(
            "SELECT issued_at FROM email_password_reset_v1223 WHERE account_id=?",
            (account_id,),
        ).fetchone()
        if prev is not None and now - int(prev["issued_at"]) < 300:
            return None
        code = secrets.token_hex(8).upper()
        digest = hashlib.sha256(code.encode("ascii")).hexdigest()
        self.conn.execute(
            "INSERT INTO email_password_reset_v1223(account_id,token_hash,issued_at,expires_at,attempts) "
            "VALUES(?,?,?,?,0) ON CONFLICT(account_id) DO UPDATE SET "
            "token_hash=excluded.token_hash,issued_at=excluded.issued_at,"
            "expires_at=excluded.expires_at,attempts=0",
            (account_id, digest, now, now + 900),
        )
        self.conn.commit()
        return account_id, email, code

    def revoke_email_reset_v1223(self, account_id):
        self.conn.execute("DELETE FROM email_password_reset_v1223 WHERE account_id=?", (int(account_id),))
        self.conn.commit()

    def reset_password_by_email_v1223(self, username, code, new_password, *, now=None):
        if not isinstance(new_password, str) or not 10 <= len(new_password) <= 256:
            return False
        code = str(code or "").strip().upper()
        if len(code) != 16 or any(c not in "0123456789ABCDEF" for c in code):
            return False
        target = self.master_account_by_name(str(username or "").strip())
        if target is None:
            return False
        account_id = int(target["id"])
        now = int(time.time() if now is None else now)
        digest = hashlib.sha256(code.encode("ascii")).hexdigest()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "SELECT token_hash,expires_at,attempts FROM email_password_reset_v1223 WHERE account_id=?",
                (account_id,),
            ).fetchone()
            valid = (row is not None and int(row["expires_at"]) >= now
                     and int(row["attempts"]) < 5
                     and hmac.compare_digest(str(row["token_hash"]), digest))
            if not valid:
                self.conn.execute(
                    "UPDATE email_password_reset_v1223 SET attempts=attempts+1 "
                    "WHERE account_id=? AND expires_at>=? AND attempts<5",
                    (account_id, now),
                )
                self.conn.commit()
                return False
            salt, ph = hash_password(new_password)
            self.conn.execute("UPDATE accounts SET password_salt=?,password_hash=? WHERE id=?", (salt, ph, account_id))
            self.conn.execute("DELETE FROM email_password_reset_v1223 WHERE account_id=?", (account_id,))
            self.conn.execute("DELETE FROM password_recovery_v1222 WHERE account_id=?", (account_id,))
            self.conn.commit()
            return True
        except BaseException:
            self.conn.rollback()
            raise

    def account_name(self, account_id):
        row = self.conn.execute(
            "SELECT username FROM accounts WHERE id=?", (int(account_id),)
        ).fetchone()
        return str(row["username"]) if row else ""

    def wipe_characters_for_master(self, master_account_id):
        """Usuń postacie/progres konta, ale zachowaj login i hasło konta."""
        master_account_id = int(master_account_id)
        rows = self.conn.execute(
            "SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot",
            (master_account_id,),
        ).fetchall()
        char_ids = [int(row["character_account_id"]) for row in rows]

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
            protected = {"accounts", "account_characters", "account_wallet"}
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
            protected = {"accounts", "account_characters", "account_wallet"}
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
        return removed, masters

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

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

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

    def shared_wallet_for_master(self, master_account_id):
        master_account_id = int(master_account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM account_wallet "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        if row:
            silver, gold, mithril = normalize_currency_values(
                row["silver"], row["gold"], row["mithril"]
            )
            if gold or mithril or silver != int(row["silver"]):
                self.set_shared_wallet_for_master(
                    master_account_id, silver, gold, mithril
                )
            return (silver, gold, mithril)

        # Bezpieczny fallback dla świeżego konta albo nietypowego starego save'a.
        sums = self.conn.execute(
            """
            SELECT COALESCE(SUM(c.silver),0) AS silver,
                   COALESCE(SUM(c.gold),0) AS gold,
                   COALESCE(SUM(c.mithril),0) AS mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            """,
            (master_account_id,),
        ).fetchone()
        silver, gold, mithril = normalize_currency_values(
            int(sums["silver"] or 0), int(sums["gold"] or 0), int(sums["mithril"] or 0)
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO account_wallet("
            "master_account_id,silver,gold,mithril,updated_at"
            ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (master_account_id, silver, gold, mithril),
        )
        self.conn.commit()
        return silver, gold, mithril

    def shared_wallet_for_character(self, character_account_id):
        return self.shared_wallet_for_master(
            self.master_account_for_character(character_account_id)
        )

    def set_shared_wallet_for_master(self, master_account_id, silver, gold, mithril, *, commit=True):
        master_account_id = int(master_account_id)
        silver, gold, mithril = normalize_currency_values(silver, gold, mithril)
        self.conn.execute(
            """
            INSERT INTO account_wallet(master_account_id,silver,gold,mithril,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(master_account_id) DO UPDATE SET
                silver=excluded.silver,
                gold=excluded.gold,
                mithril=excluded.mithril,
                updated_at=CURRENT_TIMESTAMP
            """,
            (master_account_id, silver, gold, mithril),
        )
        # Trzymamy kolumny legacy zsynchronizowane, żeby wszystkie starsze
        # fragmenty gry i narzędzia administracyjne widziały to samo saldo.
        self.conn.execute(
            """
            UPDATE characters SET silver=?,gold=?,mithril=?
            WHERE account_id IN (
                SELECT character_account_id FROM account_characters
                WHERE master_account_id=?
            )
            """,
            (silver, gold, mithril, master_account_id),
        )
        if commit:
            self.conn.commit()
        return silver, gold, mithril

    def set_shared_wallet_for_character(self, character_account_id, silver, gold, mithril, *, commit=True):
        return self.set_shared_wallet_for_master(
            self.master_account_for_character(character_account_id),
            silver, gold, mithril, commit=commit,
        )

    def apply_shared_wallet_to_character(self, character):
        silver, gold, mithril = self.shared_wallet_for_character(character.account_id)
        character.silver = silver
        character.gold = gold
        character.mithril = mithril
        return character

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def characters_for_master(self, master_account_id):
        return self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.*
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot
            """,
            (master_account_id,),
        ).fetchall()

    def character_count_for_master(self, master_account_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM account_characters "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        return int(row["n"] or 0) if row else 0

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

    def create_character_for_master(self, master_account_id, name, race, cls, name_cases, gender="nieokreślona"):
        if self.character_count_for_master(master_account_id) >= MAX_CHARACTERS_PER_ACCOUNT:
            raise ValueError("character_limit")

        slot = self._next_character_slot(master_account_id)
        if slot is None:
            raise ValueError("character_limit")

        existing_master_character = self.character_for_account(master_account_id)
        master_link = self.conn.execute(
            "SELECT 1 FROM account_characters WHERE character_account_id=?",
            (master_account_id,),
        ).fetchone()

        if slot == 1 and not existing_master_character and not master_link:
            character_account_id = int(master_account_id)
        else:
            character_account_id = self._create_hidden_character_account(
                master_account_id, slot
            )

        self.conn.execute(
            "INSERT INTO account_characters(master_account_id,character_account_id,slot) "
            "VALUES(?,?,?)",
            (master_account_id, character_account_id, slot),
        )
        try:
            self.create_character(
                character_account_id, name, race, cls, name_cases, gender=gender
            )
            wallet_row = self.conn.execute(
                "SELECT silver,gold,mithril FROM account_wallet "
                "WHERE master_account_id=?",
                (master_account_id,),
            ).fetchone()
            if wallet_row is None:
                # Pierwsza postać zakłada wspólny portfel z pakietem startowym.
                created = self.character_for_account(character_account_id)
                self.set_shared_wallet_for_master(
                    master_account_id,
                    created["silver"], created["gold"], created["mithril"],
                )
            else:
                # Każda następna postać dostaje dokładnie saldo konta,
                # bez ponownego przyznawania startowych monet.
                self.set_shared_wallet_for_master(
                    master_account_id,
                    wallet_row["silver"], wallet_row["gold"], wallet_row["mithril"],
                )
            # v0.34.5: Gildia jest dziedziczona przez nowe postacie tego samego
            # konta. Ranga zawsze startuje jako `member`; uprawnienia lidera/oficera
            # pozostają przy postaci, która faktycznie dostała tę rangę.
            self.ensure_character_guild_from_master_v0345(
                master_account_id, character_account_id
            )
        except Exception:
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND slot=?",
                (master_account_id, slot),
            )
            if character_account_id != master_account_id:
                self.conn.execute(
                    "DELETE FROM accounts WHERE id=?", (character_account_id,)
                )
            self.conn.commit()
            raise
        return character_account_id, slot

    def mark_player_login_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_login_ts,last_seen_ts,login_count) VALUES(?,?,?,1) "
            "ON CONFLICT(account_id) DO UPDATE SET last_login_ts=excluded.last_login_ts,last_seen_ts=excluded.last_seen_ts,login_count=player_presence_v0363.login_count+1",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def mark_player_logout_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_logout_ts,last_seen_ts,login_count) VALUES(?,?,?,0) "
            "ON CONFLICT(account_id) DO UPDATE SET last_logout_ts=excluded.last_logout_ts,last_seen_ts=excluded.last_seen_ts",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def player_presence_v0363(self, account_id):
        return self.conn.execute(
            "SELECT last_login_ts,last_logout_ts,last_seen_ts,login_count FROM player_presence_v0363 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

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

    def friend_master_v12213(self, character_or_master_id):
        """Friendship belongs to the actual login account, not a character slot."""
        return self.master_account_for_character(int(character_or_master_id))

    def friend_character_names_v12213(self, master_id):
        """Always read current characters, including ones created after friendship."""
        names = [str(row["name"]) for row in self.characters_for_master(master_id)]
        if not names:
            name = self.character_name_by_account_v0928(master_id)
            return [name] if name else []
        return names

    def migrate_friend_accounts_v12213(self):
        """Move old per-character edges to master accounts once, atomically.

        A pending request never becomes an accepted friendship by migration.
        """
        flag = 'friends_master_accounts_v12213'
        if self.conn.execute('SELECT 1 FROM migration_flags WHERE flag=?', (flag,)).fetchone():
            return
        self.conn.execute('SAVEPOINT migrate_friends_v12213')
        try:
            accepted = self.conn.execute(
                'SELECT account_id,friend_account_id,created_at FROM player_friends_v0928'
            ).fetchall()
            requests = self.conn.execute(
                'SELECT sender_account_id,target_account_id,created_at FROM player_friend_requests_v0928'
            ).fetchall()
            approved = set()
            for row in accepted:
                a = self.friend_master_v12213(row['account_id'])
                b = self.friend_master_v12213(row['friend_account_id'])
                if a != b:
                    approved.add((min(a,b), max(a,b)))
            self.conn.execute('DELETE FROM player_friends_v0928')
            for a,b in sorted(approved):
                self.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (a,b))
                self.conn.execute('INSERT INTO player_friends_v0928(account_id,friend_account_id) VALUES(?,?)', (b,a))
            self.conn.execute('DELETE FROM player_friend_requests_v0928')
            for row in requests:
                a = self.friend_master_v12213(row['sender_account_id'])
                b = self.friend_master_v12213(row['target_account_id'])
                if a == b or (min(a,b),max(a,b)) in approved:
                    continue
                self.conn.execute('INSERT OR IGNORE INTO player_friend_requests_v0928 '
                                  '(sender_account_id,target_account_id,created_at) VALUES(?,?,?)',
                                  (a,b,row['created_at']))
            self.conn.execute('INSERT INTO migration_flags(flag) VALUES(?)', (flag,))
            self.conn.execute('RELEASE SAVEPOINT migrate_friends_v12213')
            self.conn.commit()
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT migrate_friends_v12213')
            self.conn.execute('RELEASE SAVEPOINT migrate_friends_v12213')
            raise

    def are_friends_v0928(self, account_id, friend_account_id):
        return self.conn.execute(
            "SELECT 1 FROM player_friends_v0928 WHERE account_id=? AND friend_account_id=?",
            (self.friend_master_v12213(account_id), self.friend_master_v12213(friend_account_id)),
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases, gender="nieokreślona"):
        rname, _, _race_strength, _race_dexterity, _race_constitution, _race_intelligence, _race_willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        raw_gender = str(gender or "").strip().casefold()
        if raw_gender in ("kobieta", "k"):
            gender = "kobieta"
        elif raw_gender in ("mężczyzna", "mezczyzna", "m"):
            gender = "mężczyzna"
        elif raw_gender in ("nieokreślona", "nieokreslona", ""):
            gender = "nieokreślona"
        else:
            raise ValueError("invalid_gender")
        if rname == "Driada" and gender != "kobieta":
            raise ValueError("dryad_female_only")
        starting_stats = class_starting_stats_for(race, cls)
        strength = starting_stats["strength"]
        dexterity = starting_stats["dexterity"]
        constitution = starting_stats["constitution"]
        intelligence = starting_stats["intelligence"]
        willpower = starting_stats["willpower"]
        charisma = starting_stats["charisma"]
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,gender,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,charisma,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',?,?,?,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, gender, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower, charisma,
                STARTING_SILVER, STARTING_GOLD, STARTING_MITHRIL,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        if rname == "Cyborg":
            self.conn.execute(
                "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
                (account_id, "moogle_board", 1),
            )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()

    def save_character(self, c, commit=True):
        (
            c.silver,
            c.gold,
            c.mithril,
        ) = normalize_currency_values(
            c.silver,
            c.gold,
            c.mithril,
        )

        # v0.8.32: waluta należy do konta głównego, nie do slotu postaci.
        self.set_shared_wallet_for_character(
            c.account_id, c.silver, c.gold, c.mithril, commit=False
        )

        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, strength_progress=?, dexterity_progress=?,
                constitution_progress=?, intelligence_progress=?, willpower_progress=?,
                charisma_progress=?, soul_level=?, soul_xp=?, soul_tier=?,
                soul_weapon_mastery_level=?, soul_weapon_mastery_xp=?, room_id=?,
                silver=?, gold=?, mithril=?, charisma=?, character_level=?, character_xp=?, deaths=?,
                guild_reputation_json=?, guild_exams_json=?,
                guild_class_quests_json=?, guild_bounty_json=?,
                loot_filter=?, active_title=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                min(c.strength_progress, c.dexterity_progress, c.constitution_progress,
                    c.intelligence_progress, c.willpower_progress, c.charisma_progress),
                c.strength_progress, c.dexterity_progress, c.constitution_progress,
                c.intelligence_progress, c.willpower_progress, c.charisma_progress,
                c.soul_level, c.soul_xp, c.soul_tier,
                c.soul_weapon_mastery_level, c.soul_weapon_mastery_xp, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.character_level, c.character_xp, c.deaths,
                c.guild_reputation_json, c.guild_exams_json,
                c.guild_class_quests_json, c.guild_bounty_json,
                c.loot_filter, c.active_title,
                c.account_id,
            ),
        )
        if commit:
            self.conn.commit()
