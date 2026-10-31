# -*- coding: utf-8 -*-
"""Production, lazy exact TEXT store for the 14 character progression axes.

Only explicitly enumerated progression fields are handled. Currency, combat HP
and derived base combat stats remain subject to their existing SQLite guards.
Every exact shadow has an independent receipt; missing, stale or corrupted TEXT
causes a hard error instead of exposing a saturated INTEGER mirror.
"""
from __future__ import annotations
from hashlib import sha256
from core.big_numbers_v10400 import SQLITE_INT64_MAX, canonical_uint, number
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64

CHARACTER_AXES = (
    'character_xp', 'soul_xp', 'character_level', 'soul_level',
    'soul_tier', 'soul_weapon_mastery_level', 'soul_weapon_mastery_xp',
    'stat_progress', 'strength_progress', 'dexterity_progress',
    'constitution_progress', 'intelligence_progress',
    'willpower_progress', 'charisma_progress',
)


def _signature(uid, axis, val, mirror):
    return sha256(f'{uid}|{axis}|{val}|{mirror}'.encode('utf-8')).hexdigest()


def _receipt(uid, axis):
    return sha256(f'{uid}|{axis}|receipt'.encode('utf-8')).hexdigest()


def install_live_character_progress(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_live_character_v10400 (
        account_id INTEGER NOT NULL, axis TEXT NOT NULL, value_text TEXT NOT NULL,
        mirror_text TEXT NOT NULL, checksum TEXT NOT NULL,
        PRIMARY KEY(account_id,axis),
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_live_character_receipt_v10400 (
        account_id INTEGER NOT NULL, axis TEXT NOT NULL, checksum TEXT NOT NULL,
        PRIMARY KEY(account_id,axis),
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE)''')
    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='characters'").fetchone()
    if not exists:
        return
    # The mirror changes only through the atomic production writer, which
    # stages authoritative TEXT first and then updates the legacy columns.
    mismatches = ' OR '.join(
        f'''EXISTS(SELECT 1 FROM big_number_live_character_v10400 s
            WHERE s.account_id=NEW.account_id AND s.axis='{field}'
              AND s.mirror_text != CAST(NEW."{field}" AS TEXT))'''
        for field in CHARACTER_AXES
    )
    columns=','.join('"'+field+'"' for field in CHARACTER_AXES)
    conn.execute(f'''CREATE TRIGGER IF NOT EXISTS sb104_live_character_update
        BEFORE UPDATE OF {columns} ON characters
        WHEN {mismatches}
        BEGIN SELECT RAISE(ABORT,'SB104: odmowa nadpisania lustra BigNumber postaci'); END''')


def read_live_character_axes(db, uid, row):
    """Return overrides; reject all missing/corrupted/stale authoritative rows."""
    uid=require_sqlite_int64('account_id',uid)
    if uid <= 0:
        raise ValueError('BigNumber: nieprawidlowe konto postaci.')
    shadows={r[0]: tuple(r[1:]) for r in db.conn.execute('''SELECT axis,value_text,mirror_text,checksum
         FROM big_number_live_character_v10400 WHERE account_id=?''',(uid,))}
    receipts={r[0]: r[1] for r in db.conn.execute('''SELECT axis,checksum
         FROM big_number_live_character_receipt_v10400 WHERE account_id=?''',(uid,))}
    allowed=set(CHARACTER_AXES)
    if not set(shadows).issubset(allowed) or not set(receipts).issubset(allowed):
        raise ValueError('BigNumber: nieznana os postaci w bazie.')
    if set(shadows)!=set(receipts):
        raise ValueError('BigNumber: brak potwierdzenia lub dokladnej osi EXP.')
    values={}
    for axis in CHARACTER_AXES:
        legacy=row[axis]
        if type(legacy) is not int or legacy < 0:
            raise ValueError('BigNumber: uszkodzony stary zapis postaci.')
        if axis not in shadows:
            values[axis]=legacy
            continue
        val, mirror, checksum=shadows[axis]
        if canonical_uint(val)!=val or canonical_uint(mirror)!=mirror:
            raise ValueError('BigNumber: niekanoniczny zapis postaci.')
        if checksum!=_signature(uid,axis,val,mirror) or receipts[axis]!=_receipt(uid,axis):
            raise ValueError('BigNumber: suma kontrolna osi postaci jest niezgodna.')
        if mirror!=str(legacy) or min(number(val),SQLITE_INT64_MAX)!=legacy:
            raise ValueError('BigNumber: niezgodne lustro INTEGER postaci.')
        values[axis]=number(val)
    return values


def stage_live_character_axes(db, uid, values):
    """Only call inside the caller-owned SAVEPOINT, BEFORE legacy UPDATE."""
    uid=require_sqlite_int64('account_id',uid)
    if set(values)!=set(CHARACTER_AXES):
        raise ValueError('BigNumber: niepelny zapis osi postaci.')
    row=db.conn.execute('SELECT * FROM characters WHERE account_id=?',(uid,)).fetchone()
    if row is None:
        raise LookupError('BigNumber: brak postaci.')
    # Check ALL prior shadows before touching any of them.
    read_live_character_axes(db,uid,row)
    existing={r[0] for r in db.conn.execute('''SELECT axis FROM big_number_live_character_v10400
        WHERE account_id=?''',(uid,))}
    for axis in CHARACTER_AXES:
        exact=canonical_uint(values[axis])
        val=number(exact)
        if val<=SQLITE_INT64_MAX and axis not in existing:
            continue
        mirror=str(min(val,SQLITE_INT64_MAX))
        db.conn.execute('''INSERT INTO big_number_live_character_v10400
            (account_id,axis,value_text,mirror_text,checksum) VALUES(?,?,?,?,?)
            ON CONFLICT(account_id,axis) DO UPDATE SET value_text=excluded.value_text,
                mirror_text=excluded.mirror_text,checksum=excluded.checksum''',
            (uid,axis,exact,mirror,_signature(uid,axis,exact,mirror)))
        db.conn.execute('''INSERT INTO big_number_live_character_receipt_v10400
            (account_id,axis,checksum) VALUES(?,?,?)
            ON CONFLICT(account_id,axis) DO UPDATE SET checksum=excluded.checksum''',
            (uid,axis,_receipt(uid,axis)))
