# -*- coding: utf-8 -*-
"""Security and real-account flow regressions for in-game one-use codes."""
import asyncio
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import server  # Bootstraps legacy gameplay globals before Session imports.
from network.account_email_v1223 import smtp_ready_v1223
from storage.db_accounts import DatabaseAccountsMixin
from storage.db_shared import hash_password
from storage.schema_core import create_core_schema
from player.session_mixins.password_recovery_v1222 import SessionPasswordRecoveryV1222Mixin
from player.session import Session


def audit_v5001_recovery_codes():
    n = 0
    def check(value, message):
        nonlocal n
        n += 1
        if not value:
            raise AssertionError('v5.00.1 password recovery: ' + message)

    class DB(DatabaseAccountsMixin):
        pass
    db = DB()
    db.conn = sqlite3.connect(':memory:')
    db.conn.row_factory = sqlite3.Row
    db.conn.execute('PRAGMA foreign_keys=ON')
    create_core_schema(db)

    class Fake(SessionPasswordRecoveryV1222Mixin):
        def __init__(self, account_id=None, answers=()):
            self.master_account_id = account_id
            self.account_id = None
            self.answers = list(answers)
            self.messages = []
            self.server = SimpleNamespace(db=db, sessions=set())
        async def send(self, msg='', **kwargs):
            self.messages.append((str(msg), kwargs))
        async def ask(self, prompt):
            self.messages.append((str(prompt), {}))
            return self.answers.pop(0) if self.answers else None
        async def character_selection_flow(self):
            return True
        async def negotiate_polish_charset(self):
            pass
        async def close_from_main_menu(self):
            pass
        def normalize_description_query(self, text):
            return text

    try:
        # New player: creation immediately produces one private backup code.
        new = Fake(answers=['NewPlayer','InitialPassword123','InitialPassword123'])
        check(asyncio.run(Session.do_new_account(new)), 'registration completes')
        aid = new.master_account_id
        check(aid is not None, 'new account exists')
        private = [msg for msg, kw in new.messages if 'TWÓJ JEDNORAZOWY KOD' in msg and kw.get('history_store') is False]
        check(len(private) == 1, 'one secret immediately at registration, no history')
        one = private[0].split('ODZYSKIWANIA: ', 1)[1].split('.', 1)[0]
        check(len(one)==32 and all(ch in '0123456789ABCDEF' for ch in one), '128-bit hex code')
        check(one not in str(db.conn.execute('SELECT * FROM password_recovery_v1222').fetchall()), 'no plaintext in sqlite')
        check(not smtp_ready_v1223(), 'mail disabled')

        existing = Fake(account_id=aid)
        asyncio.run(existing.account_recovery_command_v1222(''))
        check(any('konto kod' in msg for msg,_ in existing.messages), 'short command documented')
        asyncio.run(existing.account_recovery_command_v1222('kod'))
        check(any('Odczekaj' in msg for msg,_ in existing.messages), 'one-minute reissue throttle')
        old_time=int(time.time())
        # Simulate a real player returning later; preserve all credentials/characters.
        db.conn.execute('UPDATE password_recovery_v1222 SET issued_at=? WHERE account_id=?', (old_time-90, aid));db.conn.commit()
        existing.messages.clear()
        asyncio.run(existing.account_recovery_command_v1222('haslo kod'))
        codes=[msg.split('ODZYSKIWANIA: ',1)[1].split('.',1)[0] for msg,kw in existing.messages if 'TWÓJ JEDNORAZOWY KOD' in msg and kw.get('history_store') is False]
        check(len(codes)==1 and codes[0]!=one, 'regeneration private and fresh')
        code=codes[0]
        check(not db.reset_password_with_code_v1222('NewPlayer',one,'ChangedPassword123'), 'old code revoked')
        check(not db.reset_password_with_code_v1222('BadAccount',code,'ChangedPassword123'), 'wrong account blocked')
        guest=Fake()
        asyncio.run(guest.account_recovery_command_v1222('kod'))
        check(not any('TWÓJ JEDNORAZOWY' in msg for msg,_ in guest.messages), 'no code without login')
        # Login menu uses the code, then invalidates it atomically.
        recovery=Fake(answers=['NewPlayer',code,'ChangedPassword123','ChangedPassword123'])
        asyncio.run(Session.recover_password_from_login_v1222(recovery))
        check(any('Hasło zostało zmienione' in msg for msg,_ in recovery.messages), 'password reset works from login')
        check(not db.reset_password_with_code_v1222('NewPlayer',code,'DifferentPassword123'), 'one-time redemption')
        row=db.account_by_name('NewPlayer')
        from network.protocol_gameplay_utils import verify_password
        check(verify_password('ChangedPassword123',row['password_salt'],row['password_hash']), 'new password stored')
        check(not db.conn.execute('SELECT 1 FROM password_recovery_v1222 WHERE account_id=?',(aid,)).fetchone(), 'code consumed')
        # Main login menu should never offer mail as a reset path.
        menu=Fake(answers=['3'])
        asyncio.run(Session.login_flow(menu))
        check(any('4. Odzyskaj hasło (jednorazowy kod)' in msg for msg,_ in menu.messages), 'menu code-only')
        check(not any('e-mail' in msg.lower() or 'email' in msg.lower() for msg,_ in menu.messages), 'no email mentions in menu')
        # Old stored e-mail reset tokens may exist, but cannot authenticate.
        db.conn.execute('INSERT INTO email_password_reset_v1223(account_id,token_hash,issued_at,expires_at,attempts) VALUES (?,?,?,?,0)',(aid,'xyz',1,9999999999));db.conn.commit()
        check(not db.reset_password_by_email_v1223('NewPlayer','A'*16,'InsecurePassword123'), 'legacy mail token blocked')
        check(db.issue_email_reset_v1223('NewPlayer') is None,'no new e-mail tokens')
        return n
    finally:
        db.conn.close()

if __name__ == '__main__':
    print('KODY ODZYSKIWANIA v5.00.1:',audit_v5001_recovery_codes(),'checks PASS')
