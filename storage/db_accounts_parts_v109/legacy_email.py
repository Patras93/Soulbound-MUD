# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: legacy_email."""
from .dependencies import *

class LegacyEmailV109Mixin:
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
        """Deprecated: new accounts use regular create_account and in-game codes."""
        raise ValueError("Zakładanie konta tą metodą jest wyłączone.")

    def attach_verified_email_v1223(self, account_id, email):
        """Deprecated: existing stored addresses remain private but cannot be changed."""
        raise ValueError("Ta metoda została wyłączona.")

    def issue_email_reset_v1223(self, username, *, now=None):
        """Deprecated: fail-closed even if SMTP settings remain configured."""
        return None

    def revoke_email_reset_v1223(self, account_id):
        self.conn.execute("DELETE FROM email_password_reset_v1223 WHERE account_id=?", (int(account_id),))
        self.conn.commit()

    def reset_password_by_email_v1223(self, username, code, new_password, *, now=None):
        """Deprecated: only reset_password_with_code_v1222 may change a password."""
        return False
