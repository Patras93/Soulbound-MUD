# -*- coding: utf-8 -*-
"""v104 etap 12 — idempotentny dziennik zmian BigNumber, tylko na kopii bazy.

Dziennik nie jest włączony do normalnej gry: na żywej bazie istnieją
nieprzeniesione czytniki/wpisy INTEGER. Każdy przyrost ma identyfikator
zdarzenia i może zostać bezpiecznie powtórzony po utracie odpowiedzi.
"""
from __future__ import annotations

from hashlib import sha256
import re
import sqlite3

from core.big_numbers_v10400 import canonical_uint
from storage.big_number_ledger_v10400 import (
    get_exact_copy, add_exact_copy, MissingLedgerRowV104,
)
from storage.big_number_shadow_v10400 import _validate_axis

_ID = re.compile(r'^[A-Za-z0-9_.:-]{1,120}$', re.ASCII)


class EventConflictV104(ValueError):
    """Ta sama nazwa zdarzenia zostala uzyta z innymi parametrami."""


def install_event_schema_copy(conn: sqlite3.Connection) -> None:
    """Uruchamiaj wyłącznie na jawnie dostarczonej bazie testowej."""
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_events_v10400 (
        account_id INTEGER NOT NULL,
        axis TEXT NOT NULL,
        source_key TEXT NOT NULL,
        event_id TEXT NOT NULL,
        delta_sign INTEGER NOT NULL CHECK (delta_sign IN (-1,0,1)),
        delta_abs_text TEXT NOT NULL,
        value_after_text TEXT NOT NULL,
        digest TEXT NOT NULL,
        PRIMARY KEY (account_id,axis,source_key,event_id)
    )''')


def _checksum(uid: int, axis: str, key: str, event_id: str, sign: int,
              magnitude: str, value: str) -> str:
    fields = (str(uid), axis, key, event_id, str(sign), magnitude, value)
    return sha256('|'.join(fields).encode('ascii')).hexdigest()


def _params(account_id: int, axis: str, delta: int, event_id: str,
            source_key: str) -> tuple:
    _validate_axis(axis, source_key)
    if type(account_id) is not int or not 1 <= account_id <= (1 << 63) - 1:
        raise ValueError('Niepoprawny numer konta.')
    if type(delta) is not int:
        raise TypeError('Przyrost musi byc liczba calkowita.')
    if type(event_id) is not str or not _ID.fullmatch(event_id):
        raise ValueError('Niepoprawny identyfikator zdarzenia.')
    sign = (delta > 0) - (delta < 0)
    magnitude = canonical_uint(abs(delta))
    return account_id, axis, source_key, event_id, sign, magnitude


def apply_event_copy(conn: sqlite3.Connection, account_id: int,
                     axis: str, delta: int, event_id: str,
                     *, source_key: str = '') -> int:
    """Zapisz przyrost i pokwitowanie jako JEDNĄ transakcję SAVEPOINT.

    Powtórzenie identycznego event_id jest no-op, również po innych zdarzeniach.
    Zmiana payloadu pod tym samym event_id jest błędem. Zmiana legacy INTEGER
    po utworzeniu ledgera zawsze blokuje operację. Nie dotyka kolumn INTEGER.
    """
    uid, axis, key, eid, sign, magnitude = _params(
        account_id, axis, delta, event_id, source_key)
    conn.execute('SAVEPOINT v104_event_atomic')
    try:
        install_event_schema_copy(conn)
        # Validation performed even for retries: stale INTEGER or forged checksums
        # must not be hidden by the existence of a matching event_id.
        existing = conn.execute('''SELECT delta_sign,delta_abs_text,value_after_text,digest
           FROM big_number_events_v10400
           WHERE account_id=? AND axis=? AND source_key=? AND event_id=?''',
           (uid, axis, key, eid)).fetchone()
        if existing is not None:
            old_sign, old_amount, old_value, digest = existing
            if (type(old_sign) is not int or old_sign != sign
                    or old_amount != magnitude):
                raise EventConflictV104('Wykryto powtorzony identyfikator z inna wyplata.')
            after = canonical_uint(old_value)
            if digest != _checksum(uid, axis, key, eid, sign, magnitude, after):
                raise EventConflictV104('Niespojny dziennik operacji.')
            current = get_exact_copy(conn, uid, axis, source_key=key)
            conn.execute('RELEASE SAVEPOINT v104_event_atomic')
            return current
        # Legacy guard is checked by add_exact_copy; journaling remains atomic.
        updated = add_exact_copy(conn, uid, axis, delta, source_key=key)
        value = canonical_uint(updated)
        digest = _checksum(uid, axis, key, eid, sign, magnitude, value)
        conn.execute('''INSERT INTO big_number_events_v10400
            (account_id,axis,source_key,event_id,delta_sign,delta_abs_text,
             value_after_text,digest) VALUES (?,?,?,?,?,?,?,?)''',
            (uid,axis,key,eid,sign,magnitude,value,digest))
        conn.execute('RELEASE SAVEPOINT v104_event_atomic')
        return updated
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v104_event_atomic')
        conn.execute('RELEASE SAVEPOINT v104_event_atomic')
        raise


def verify_events_copy(conn: sqlite3.Connection) -> int:
    """Weryfikacja integralności pokwitowań (nie potwierdza migracji produkcyjnej)."""
    count = 0
    for uid,axis,key,eid,sign,amount,value,digest in conn.execute('''SELECT
        account_id,axis,source_key,event_id,delta_sign,delta_abs_text,
        value_after_text,digest FROM big_number_events_v10400'''):
        _params(uid,axis,sign*int(canonical_uint(amount)),eid,key)
        canonical = canonical_uint(value)
        if amount != canonical_uint(amount) or value != canonical:
            raise ValueError('Niekanoniczne liczby w dzienniku.')
        if digest != _checksum(uid,axis,key,eid,sign,amount,value):
            raise ValueError('Niepoprawna suma kontrolna zdarzenia.')
        count += 1
    return count
