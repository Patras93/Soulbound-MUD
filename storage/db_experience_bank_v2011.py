# -*- coding: utf-8 -*-
"""Persistent, account-scoped XP overflow. Unbounded decimal TEXT prevents 64-bit overflow."""

from systems.experience_cap_v2009 import KINDS
from core.big_numbers_v10400 import canonical_uint, number


class DatabaseExperienceBankV2011Mixin:
    def multi_cap_v23215(self, account_id):
        from systems.multi_cap_v23215 import multi_cap_experience_v23215
        return multi_cap_experience_v23215(self.conn, account_id)

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
        # Nie ukrywaj ujemnego/uszkodzonego salda jako zera.
        return [(str(r[0]), str(r[1]), number(r[2])) for r in rows]

    def allocate_experience_bank_v2011(self, account_id, amount, kind, source_key, cap):
        """Nalicz nagrodę w PRAWDZIWYM EXP Bank bez utraty nadwyżek.

        v104 etap 14: zero-cap nie usuwa EXP — całość jest odkładana.
        Zapis TEXT i wypłata obliczane są wewnątrz SAVEPOINT, bez float,
        max(0,...) na uszkodzonych saldach i SQL SUM/CAST. Bez osobnej
        migracji kolumn character_xp i soul_xp: pełne BigNumber nadal nieaktywne.
        """
        kind = str(kind).lower()
        if kind not in KINDS:
            raise ValueError('Unknown EXP kind: ' + kind)
        source_key = str(source_key or '').strip()
        if kind in ('character', 'soul'):
            source_key = ''
        if len(source_key) > 160:
            raise ValueError('EXP bank source key too long')
        # Int/decimal TEXT only. Silent truncation of float/negative values
        # would corrupt earned EXP; callers must provide nonnegative counts.
        amount = number(amount if amount is not None else 0)
        cap = number(cap if cap is not None else 0)
        if type(account_id) is not int or not 1 <= account_id <= (1 << 63) - 1:
            raise ValueError('Niepoprawny identyfikator konta EXP Bank.')
        if not amount:
            return 0
        self.conn.execute('SAVEPOINT v104_xp_bank_award')
        try:
            row = self.conn.execute(
                'SELECT balance FROM experience_bank_v2011 '
                'WHERE account_id=? AND kind=? AND source_key=?',
                (account_id, kind, source_key)
            ).fetchone()
            balance = number(row[0]) if row else 0
            fresh = min(amount, cap)
            # A zero cap is a temporary inability to pay; it must not be
            # interpreted as permission to destroy the whole reward.
            repay = min(balance, cap - fresh, fresh)
            paid = fresh + repay
            new_balance = balance + amount - paid
            canonical = canonical_uint(new_balance)
            if paid + new_balance != amount + balance:
                raise AssertionError('Niespojny bilans EXP Bank.')
            if new_balance != balance:
                self.conn.execute(
                    'INSERT INTO experience_bank_v2011(account_id,kind,source_key,balance) '
                    'VALUES(?,?,?,?) ON CONFLICT(account_id,kind,source_key) '
                    'DO UPDATE SET balance=excluded.balance',
                    (account_id, kind, source_key, canonical)
                )
            self.conn.execute('RELEASE SAVEPOINT v104_xp_bank_award')
        except BaseException:
            self.conn.execute('ROLLBACK TO SAVEPOINT v104_xp_bank_award')
            self.conn.execute('RELEASE SAVEPOINT v104_xp_bank_award')
            raise
        # Preserve the legacy API commit behavior; deferred-commit wrappers
        # can still postpone the outermost commit safely.
        if new_balance != balance:
            self.conn.commit()
        return paid
