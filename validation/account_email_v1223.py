# -*- coding: utf-8 -*-
"""Fast, offline, real SQLite tests of e-mail account features."""
import hashlib
import sqlite3
from storage.db_accounts import DatabaseAccountsMixin
from storage.schema_core import create_core_schema
from storage.db_shared import hash_password
from network.account_email_v1223 import normalized_email_v1223


def audit_account_email_v1223():
    checks = 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            raise RuntimeError("ACCOUNT EMAIL v1.22.3: " + reason)

    class DB(DatabaseAccountsMixin):
        pass
    db = DB()
    db.conn = sqlite3.connect(":memory:")
    db.conn.row_factory = sqlite3.Row
    db.conn.execute("PRAGMA foreign_keys=ON")
    try:
        create_core_schema(db)
        check(normalized_email_v1223(" TEST+tag@Example.org ") == "test+tag@example.org", "normalization")
        for bad in ("", "not-address", "joe@example", "a@b..com", "a\n@example.com"):
            check(normalized_email_v1223(bad) is None, "malformed email")
        id1 = db.create_account_verified_email_v1223("Test1", "SecretPassword_1", "test1@example.org")
        check(db.verified_account_email_v1223(id1) == "test1@example.org", "verified registration")
        check(db.email_taken_v1223("TEST1@EXAMPLE.ORG"), "case-insensitive uniqueness")
        codeinfo = db.issue_email_reset_v1223("Test1", now=1700000000)
        check(codeinfo is not None and len(codeinfo[2]) == 16, "secure reset token")
        check(codeinfo[2] not in str(db.conn.execute("SELECT * FROM email_password_reset_v1223").fetchone()), "code not stored as plaintext")
        check(db.issue_email_reset_v1223("Test1", now=1700000001) is None, "5-minute send throttle")
        for _ in range(5):
            check(not db.reset_password_by_email_v1223("Test1", "0"*16, "NewPassword_1", now=1700000002), "wrong token blocked")
        check(not db.reset_password_by_email_v1223("Test1", codeinfo[2], "NewPassword_1", now=1700000003), "five attempts lock token")
        codeinfo = db.issue_email_reset_v1223("Test1", now=1700000400)
        check(codeinfo is not None, "new token after throttle")
        check(not db.reset_password_by_email_v1223("Test1", codeinfo[2], "NewPassword_1", now=1700001500), "expiration")
        codeinfo = db.issue_email_reset_v1223("Test1", now=1700002000)
        check(db.reset_password_by_email_v1223("Test1", codeinfo[2], "NewPassword_1", now=1700002001), "redemption")
        check(not db.reset_password_by_email_v1223("Test1", codeinfo[2], "NewPassword_1", now=1700002002), "one-time")
        row = db.master_account_by_name("Test1")
        check(row['password_hash'] == hash_password("NewPassword_1", bytes.fromhex(row['password_salt']))[1], "password rotated")
        id2 = db.create_account("OldAccount", "OldPassword_1")
        check(db.verified_account_email_v1223(id2) is None, "old account unaffected")
        db.attach_verified_email_v1223(id2, "second@example.net")
        check(db.verified_account_email_v1223(id2) == "second@example.net", "legacy email attach")
        duplicate_rejected = False
        try:
            db.attach_verified_email_v1223(id2, "test1@example.org")
        except sqlite3.IntegrityError:
            duplicate_rejected = True
        check(duplicate_rejected, "duplicate accepted")
        check(db.verified_account_email_v1223(id2) == "second@example.net", "duplicate rollback")
        old = db.issue_email_reset_v1223("OldAccount", now=1700003000)
        db.attach_verified_email_v1223(id2, "changed@example.net")
        check(not db.reset_password_by_email_v1223("OldAccount", old[2], "Changed_1_Password", now=1700003001), "old mailbox token revoked")
        check(db.verified_account_email_v1223(id2) == "changed@example.net", "new verified mailbox")
        check(db.verified_account_email_v1223(id1) == "test1@example.org", "accounts separated")
        return checks
    finally:
        db.conn.close()
