# -*- coding: utf-8 -*-
"""Atomic live EXP-bank payout + level progression + durable character save.

This replaces the former three independent operations for character EXP in the
normal session gateway. It intentionally does NOT claim full TEXT BigNumber
support: legacy character XP/levels still require int64 and a production-wide
migration before values larger than int64 can become live.
"""
from __future__ import annotations

from systems.experience_bank_v2011 import banked_experience_v2011


def award_character_xp_atomic_v10400(db, character, account_id: int,
                                     amount: int, *, overcap: bool = False,
                                     single_level_cap: bool = False):
    """Return paid EXP and level messages, committed together with the bank.

    A SQLite SAVEPOINT lets this compose with another transaction. All methods
    which normally auto-commit are deferred until the savepoint is released.
    The in-memory level/XP is restored on every persistence error; no partial
    bank debit, lost XP or character save is allowed. No database initialization
    or network sockets are created here.
    """
    if db is None or character is None or account_id != character.account_id:
        raise ValueError('Nieprawidłowa postać do wypłaty EXP.')
    conn = db.conn
    if not hasattr(conn, 'deferred_commits'):
        raise TypeError('Wymagane bezpieczne transakcje SQLite Database.')
    old_level, old_xp = character.character_level, character.character_xp
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_character_xp_bank_atomic')
        try:
            paid = banked_experience_v2011(
                db, account_id, amount, 'character', int(old_level),
                overcap=overcap,
            )
            notes = character.add_character_xp(paid, single_level_cap=single_level_cap)
            if paid:
                # Persist all fields atomically with EXP-bank payout, including
                # the shared-wallet mirror. No independent legacy commit.
                db.save_character(character, commit=False)
            conn.execute('RELEASE SAVEPOINT v104_character_xp_bank_atomic')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v104_character_xp_bank_atomic')
                conn.execute('RELEASE SAVEPOINT v104_character_xp_bank_atomic')
            finally:
                character.character_level = old_level
                character.character_xp = old_xp
            raise
    return paid, notes
