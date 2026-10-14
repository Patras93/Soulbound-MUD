# -*- coding: utf-8 -*-
"""Historical account e-mail gate: all former password-reset entry points fail closed."""
import asyncio
import sqlite3
from storage.db_accounts import DatabaseAccountsMixin
from storage.schema_core import create_core_schema
from network.account_email_v1223 import smtp_ready_v1223, send_code_v1223


def audit_account_email_v1223():
    checks = 0
    def check(value, detail):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError('LOGIN CODE ONLY: ' + detail)

    class DB(DatabaseAccountsMixin):
        pass
    db = DB()
    db.conn = sqlite3.connect(':memory:')
    db.conn.row_factory = sqlite3.Row
    db.conn.execute('PRAGMA foreign_keys=ON')
    try:
        create_core_schema(db)
        aid = db.create_account('Test1', 'Initial_Password11')
        # Simulate a historical existing verified address and already issued reset.
        db.conn.execute("INSERT INTO account_emails_v1223(account_id,email,verified_at) VALUES(?,?,?)", (aid, 'old@example.org', 1))
        db.conn.execute("INSERT INTO email_password_reset_v1223(account_id,token_hash,issued_at,expires_at,attempts) VALUES(?,?,?,?,0)", (aid, 'abc', 1, 9999999999))
        db.conn.commit()
        check(db.verified_account_email_v1223(aid) == 'old@example.org', 'original address remains in sqlite')
        check(not smtp_ready_v1223(), 'SMTP remains disabled')
        check(db.issue_email_reset_v1223('Test1') is None, 'no email reset tokens')
        check(not db.reset_password_by_email_v1223('Test1', 'F'*16, 'Changed_Password12'), 'old reset code unusable')
        for fn, args in ((db.attach_verified_email_v1223, (aid, 'new@example.net')),
                         (db.create_account_verified_email_v1223, ('Another', 'Valid_Password12', 'new@example.net'))):
            try:
                fn(*args)
            except ValueError:
                check(True, 'old mail action blocked')
            else:
                check(False, 'old mail action still accepted')
        async def no_send():
            try:
                await send_code_v1223('old@example.org', 'reset', 'DEADBEEF')
            except RuntimeError:
                return True
            return False
        check(asyncio.run(no_send()), 'outbound mail blocked')
        check(db.conn.execute('SELECT count(*) FROM accounts').fetchone()[0] == 1, 'accounts unchanged')
        check(db.verified_account_email_v1223(aid) == 'old@example.org', 'historical data unchanged')
        return checks
    finally:
        db.conn.close()
