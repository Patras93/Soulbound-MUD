# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: password_recovery."""
from .dependencies import *

class PasswordRecoveryV109Mixin:
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
