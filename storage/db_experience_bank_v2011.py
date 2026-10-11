# -*- coding: utf-8 -*-
"""Persistent, account-scoped XP overflow. Unbounded decimal TEXT prevents 64-bit overflow."""

from systems.experience_cap_v2009 import KINDS


class DatabaseExperienceBankV2011Mixin:
    def create_experience_bank_schema_v2011(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS experience_bank_v2011 (
                account_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                source_key TEXT NOT NULL,
                balance TEXT NOT NULL DEFAULT '0',
                PRIMARY KEY(account_id, kind, source_key),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    def experience_bank_rows_v2011(self, account_id):
        rows = self.conn.execute(
            "SELECT kind, source_key, balance FROM experience_bank_v2011 "
            "WHERE account_id=? ORDER BY kind, source_key", (int(account_id),)
        ).fetchall()
        return [(str(r[0]), str(r[1]), max(0, int(r[2]))) for r in rows]

    def allocate_experience_bank_v2011(self, account_id, amount, kind, source_key, cap):
        """Deposit surplus; use spare capacity on this *same* award to repay bank.

        At most `cap` XP are paid now, so the Alter-style limit is respected.
        Different stat/class/profession/tool/skill accounts never mingle.
        """
        kind = str(kind).lower()
        if kind not in KINDS:
            raise ValueError('Unknown EXP kind: ' + kind)
        source_key = str(source_key or '').strip()
        if kind in ('character', 'soul'):
            source_key = ''
        if len(source_key) > 160:
            raise ValueError('EXP bank source key too long')
        amount, cap = max(0, int(amount or 0)), max(0, int(cap or 0))
        if not amount or not cap:
            return 0
        account_id = int(account_id)
        row = self.conn.execute(
            'SELECT balance FROM experience_bank_v2011 '
            'WHERE account_id=? AND kind=? AND source_key=?',
            (account_id, kind, source_key)
        ).fetchone()
        balance = max(0, int(row[0])) if row else 0
        fresh = min(amount, cap)
        repay = min(balance, cap - fresh)
        paid = fresh + repay
        new_balance = balance + amount - fresh - repay
        if new_balance != balance:
            self.conn.execute(
                'INSERT INTO experience_bank_v2011(account_id,kind,source_key,balance) '
                'VALUES(?,?,?,?) ON CONFLICT(account_id,kind,source_key) '
                'DO UPDATE SET balance=excluded.balance',
                (account_id, kind, source_key, str(new_balance))
            )
            self.conn.commit()
        return paid
