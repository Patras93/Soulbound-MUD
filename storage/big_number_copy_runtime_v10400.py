# -*- coding: utf-8 -*-
"""EXPERIMENTAL 14-axis exact progression round-trip on a disposable copy.

This intentionally does NOT monkey-patch normal Database.save_character or
character_for_account. It is a migration integration harness, not a production
feature flag. Production still uses guarded INTEGER columns.
"""
from __future__ import annotations

from pathlib import Path
from core.big_numbers_v10400 import canonical_uint, number, SQLITE_INT64_MAX
from storage.big_number_shadow_v10400 import (
    install_shadow_schema, stage_shadow, fetch_shadow, EXTRA_COPY_PROGRESS_AXES,
)

# Strict allowlist; never derived from external column names or input.
AXES = ('character_xp', 'soul_xp') + tuple(
    item.removeprefix('characters.') for item in EXTRA_COPY_PROGRESS_AXES
)
CHARACTER_COPY_AXES = AXES + ('silver', 'gold', 'mithril')
_MARKER = '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA'


def _mark_complete_copy_group(conn, account_id, axes):
    """Write a rollback-aware receipt for one complete test-copy shadow group.

    The receipt detects deleting *every* shadow entry after a successful copy.
    It is a consistency check, not an external or tamper-proof signature.
    """
    from hashlib import sha256
    group = tuple(sorted(axes))
    if not group or len(set(group)) != len(group):
        raise ValueError('BigNumber: niepoprawna grupa potwierdzenia.')
    uid = int(account_id)
    scope = '|'.join(group)
    digest = sha256(f'{uid}|{scope}'.encode('utf-8')).hexdigest()
    conn.execute("""CREATE TABLE IF NOT EXISTS big_number_copy_receipt_v10400 (
        account_id INTEGER NOT NULL, scope TEXT NOT NULL, axes_count INTEGER NOT NULL,
        digest TEXT NOT NULL, PRIMARY KEY(account_id,scope))""")
    conn.execute("""INSERT INTO big_number_copy_receipt_v10400
        (account_id,scope,axes_count,digest) VALUES (?,?,?,?)
        ON CONFLICT(account_id,scope) DO UPDATE SET
        axes_count=excluded.axes_count,digest=excluded.digest""",
        (uid, scope, len(group), digest))



def _mark_single_axis_receipt(conn, account_id, axis):
    """Record an atomic, copy-only receipt even for a ONE-axis XP write.

    A two-axis group receipt cannot protect a one-field pilot write: deleting
    its only shadow row previously exposed the saturated INTEGER mirror.
    """
    from hashlib import sha256
    if axis not in ('characters.character_xp', 'characters.soul_xp'):
        raise ValueError('BigNumber: niepoprawna pojedyncza os EXP.')
    uid = int(account_id)
    if uid < 1:
        raise ValueError('BigNumber: niepoprawne konto.')
    digest = sha256(f'{uid}|{axis}'.encode('utf-8')).hexdigest()
    conn.execute("""CREATE TABLE IF NOT EXISTS big_number_copy_axis_receipt_v10400 (
        account_id INTEGER NOT NULL, axis TEXT NOT NULL, digest TEXT NOT NULL,
        PRIMARY KEY(account_id,axis))""")
    conn.execute("""INSERT INTO big_number_copy_axis_receipt_v10400
        (account_id,axis,digest) VALUES (?,?,?)
        ON CONFLICT(account_id,axis) DO UPDATE SET digest=excluded.digest""",
        (uid, axis, digest))


def _require_single_axis_receipt(conn, account_id, axis):
    """Refuse silent fallback when a receipted single-axis shadow disappeared."""
    from hashlib import sha256
    if axis not in ('characters.character_xp', 'characters.soul_xp'):
        return
    present = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='big_number_copy_axis_receipt_v10400'"
    ).fetchone()
    if present is None:  # Older unreceipted snapshots remain compatible.
        return
    uid = int(account_id)
    receipt = conn.execute("""SELECT digest FROM big_number_copy_axis_receipt_v10400
        WHERE account_id=? AND axis=?""", (uid, axis)).fetchone()
    if receipt is None:
        return
    if receipt[0] != sha256(f'{uid}|{axis}'.encode('utf-8')).hexdigest():
        raise ValueError('BigNumber: uszkodzone potwierdzenie pojedynczej osi EXP.')
    shadow_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='big_number_shadow_v10400'"
    ).fetchone()
    if shadow_exists is None or conn.execute("""SELECT 1 FROM big_number_shadow_v10400
        WHERE account_id=? AND axis=? AND source_key=?""",
        (uid, axis, '')).fetchone() is None:
        raise ValueError('BigNumber: brak dokładnego rekordu pojedynczej osi EXP.')

def _mark_exact_key_receipt(conn, account_id, axis, source_key):
    """Remember a successful keyed copy-only write in the SAME savepoint.

    A separate receipt makes deleting the only class/profession/tool TEXT row
    detectable; a checksum on the missing row cannot do that. No production
    schema is touched, because all callers are behind _require_copy_path().
    """
    from hashlib import sha256
    from storage.big_number_shadow_v10400 import _validate_axis
    _validate_axis(axis, source_key)
    if axis not in ('class_progress.xp', 'professions.xp', 'tools.xp'):
        raise ValueError('BigNumber: potwierdzenie spoza osi z kluczem.')
    uid = int(account_id)
    if uid < 1:
        raise ValueError('BigNumber: niepoprawne konto w potwierdzeniu.')
    digest = sha256(f'{uid}|{axis}|{source_key}'.encode('utf-8')).hexdigest()
    conn.execute("""CREATE TABLE IF NOT EXISTS big_number_copy_key_receipt_v10400 (
        account_id INTEGER NOT NULL, axis TEXT NOT NULL, source_key TEXT NOT NULL,
        digest TEXT NOT NULL, PRIMARY KEY(account_id,axis,source_key))""")
    conn.execute("""INSERT INTO big_number_copy_key_receipt_v10400
        (account_id,axis,source_key,digest) VALUES(?,?,?,?)
        ON CONFLICT(account_id,axis,source_key) DO UPDATE SET digest=excluded.digest""",
        (uid, axis, source_key, digest))


def _require_exact_key_receipt(conn, account_id, axis, source_key):
    """Fail closed if a previously receipted keyed shadow row disappeared.

    Older snapshots with no receipt remain readable for compatibility. This is
    local corruption detection, not protection against deleting both tables.
    """
    from hashlib import sha256
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='big_number_copy_key_receipt_v10400'"
    ).fetchone()
    if exists is None:
        return
    uid = int(account_id)
    saved = conn.execute("""SELECT digest FROM big_number_copy_key_receipt_v10400
        WHERE account_id=? AND axis=? AND source_key=?""",
        (uid, axis, source_key)).fetchone()
    if saved is None:
        return
    expected = sha256(f'{uid}|{axis}|{source_key}'.encode('utf-8')).hexdigest()
    if saved[0] != expected:
        raise ValueError('BigNumber: uszkodzone potwierdzenie EXP osi z kluczem.')
    shadow_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='big_number_shadow_v10400'"
    ).fetchone()
    if shadow_table is None or conn.execute("""SELECT 1 FROM big_number_shadow_v10400
        WHERE account_id=? AND axis=? AND source_key=?""",
        (uid, axis, source_key)).fetchone() is None:
        raise ValueError('BigNumber: brak dokładnego rekordu EXP po migracji próbnej.')


def _require_complete_shadow_group(conn, account_id, axes, *, allow_partial_without_receipt=False):
    """Reject a partially or completely deleted copy-only shadow group.

    Old pilot snapshots without a receipt retain historical partial-group
    validation; a new write records a receipt atomically with its TEXT rows.
    """
    from hashlib import sha256
    group = tuple(sorted(axes))
    if not group:
        return
    uid = int(account_id)
    receipt_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_copy_receipt_v10400'"
    ).fetchone()
    receipt = None
    if receipt_table:
        receipt = conn.execute("""SELECT axes_count,digest
            FROM big_number_copy_receipt_v10400 WHERE account_id=? AND scope=?""",
            (uid, '|'.join(group))).fetchone()
        if receipt is not None:
            expected = sha256(f"{uid}|{'|'.join(group)}".encode('utf-8')).hexdigest()
            if tuple(receipt) != (len(group), expected):
                raise ValueError('BigNumber: uszkodzone potwierdzenie zestawu shadow.')
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'"
    ).fetchone()
    if not exists:
        if receipt is not None:
            raise ValueError('BigNumber: brak calej tabeli shadow po migracji probnej.')
        return
    present = {
        row[0] for row in conn.execute(
            'SELECT axis FROM big_number_shadow_v10400 '
            "WHERE account_id=? AND source_key='' AND axis IN ("
            + ','.join('?' for _ in group) + ')',
            (uid, *group),
        )
    }
    if (receipt is not None or (present and not allow_partial_without_receipt)) and len(present) != len(group):
        missing = sorted(set(group) - present)
        raise ValueError('BigNumber: niekompletny zestaw shadow; brak: ' + ', '.join(missing))


def _require_copy_path(db):
    path = Path(db.path).resolve(strict=True)
    if not path.is_file() or not (path.parent / _MARKER).is_file():
        raise PermissionError('BigNumber: odmowa zapisu. Brak znacznika IZOLowanej kopii testowej.')
    main = next((row[2] for row in db.conn.execute('PRAGMA database_list')
                 if row[1] == 'main'), '')
    if not main or Path(main).resolve(strict=True) != path:
        raise PermissionError('BigNumber: sciezka bazy nie zgadza sie z aktywnym SQLite.')
    if path.name.lower() in {'soulbound.db', 'game.db', 'players.db'}:
        raise PermissionError('BigNumber: odmowa zapisu do nazwy produkcyjnej bazy.')
    return path


def read_exact_progression_copy(db, account_id, axis):
    _require_copy_path(db)
    if axis not in CHARACTER_COPY_AXES:
        raise ValueError('Oś poza pilotażem BigNumber.')
    row = db.conn.execute('SELECT "' + axis + '" FROM characters WHERE account_id=?',
                          (account_id,)).fetchone()
    if row is None:
        raise LookupError('Nie znaleziono postaci.')
    legacy = row[0]
    # Validate signed/float corruption instead of silently converting.
    if type(legacy) is not int or legacy < 0:
        raise ValueError('Uszkodzone starsze pole liczbowe.')
    if axis in AXES:
        # Detect full removal of the older two-field pilot after its receipt.
        _require_complete_shadow_group(db.conn, account_id,
                                       ('characters.character_xp', 'characters.soul_xp'),
                                       allow_partial_without_receipt=True)
        # An existing receipt must detect removal of every progress shadow
        # row even when the old INTEGER columns are still present.
        _require_complete_shadow_group(db.conn, account_id,
            tuple('characters.' + a for a in AXES),
            allow_partial_without_receipt=True)
        # Any extended progress axis implies a complete 14-axis character
        # snapshot. The older two-axis pilot deliberately remains supported.
        extended = tuple('characters.' + a for a in AXES[2:])
        if db.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'").fetchone():
            if db.conn.execute('SELECT 1 FROM big_number_shadow_v10400 WHERE account_id=? '
                               'AND source_key=\'\' AND axis IN (' + ','.join('?' for _ in extended) + ') LIMIT 1',
                               (account_id, *extended)).fetchone():
                _require_complete_shadow_group(db.conn, account_id,
                                               tuple('characters.' + a for a in AXES))
        _require_single_axis_receipt(db.conn, account_id, 'characters.' + axis)
    elif axis in _CURRENCY_KEYS:
        _require_complete_shadow_group(db.conn, account_id,
                                       tuple('characters.' + a for a in _CURRENCY_KEYS))
    table_exists = db.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'"
    ).fetchone()
    if not table_exists:
        return legacy
    shadow = db.conn.execute('''SELECT base_int64_text FROM big_number_shadow_v10400
        WHERE account_id=? AND axis=? AND source_key='' ''',
        (account_id, 'characters.' + axis)).fetchone()
    if shadow is None:
        return legacy
    if number(shadow[0]) != legacy:
        raise ValueError('Stary zapis zmieniony poza migracją: odmowa odczytu BigNumber.')
    return fetch_shadow(db.conn, account_id, 'characters.' + axis)


def write_exact_progression_copy(db, account_id, *, character_xp=None, soul_xp=None):
    """Two fields together, full rollback, no conversion through REAL/float.

    The INTEGER legacy mirror saturates, but exact values live in checksummed
    TEXT and are read back only by this OFFLINE rehearsal API. Never live.
    """
    _require_copy_path(db)
    changes = {k: v for k, v in (
        ('character_xp', character_xp), ('soul_xp', soul_xp)) if v is not None}
    if not changes:
        raise ValueError('Brak wartości do migracji próbnej.')
    exact = {key: number(canonical_uint(value)) for key, value in changes.items()}
    conn = db.conn
    conn.execute('SAVEPOINT v104_progression_copy_only')
    try:
        install_shadow_schema(conn)
        for axis, value in exact.items():
            # Enforce CAS against changes made by legacy code since shadow write.
            read_exact_progression_copy(db, account_id, axis)
            mirror = min(value, SQLITE_INT64_MAX)
            cursor = conn.execute('UPDATE characters SET "' + axis + '"=? WHERE account_id=?',
                                  (mirror, account_id))
            if cursor.rowcount != 1:
                raise LookupError('Postać nie istnieje.')
            stage_shadow(conn, account_id, 'characters.' + axis, value, base_value=mirror)
            _mark_single_axis_receipt(conn, account_id, 'characters.' + axis)
        if len(exact) == 2:
            _mark_complete_copy_group(conn, account_id,
                ('characters.character_xp', 'characters.soul_xp'))
        for axis, value in exact.items():
            if read_exact_progression_copy(db, account_id, axis) != value:
                raise AssertionError('Utrata danych w zapisie BigNumber TEXT.')
        conn.execute('RELEASE SAVEPOINT v104_progression_copy_only')
    except BaseException:
        try:
            conn.execute('ROLLBACK TO SAVEPOINT v104_progression_copy_only')
        finally:
            conn.execute('RELEASE SAVEPOINT v104_progression_copy_only')
        raise
    return exact


def make_offline_copy_for_rehearsal(source_database, empty_directory):
    """Backup a real source READ ONLY; create a *new* fenced rehearsal DB.

    No source schema DDL and no automatic migration. Caller must explicitly
    provide an empty destination directory under its control.
    """
    import sqlite3
    source = Path(source_database).resolve(strict=True)
    folder = Path(empty_directory).resolve(strict=True)
    if not source.is_file() or not folder.is_dir():
        raise ValueError('Zrodlo musi byc plikiem, a katalog kopii musi istniec.')
    if any(folder.iterdir()):
        raise FileExistsError('Katalog kopii musi byc pusty: odmowa nadpisania.')
    output = folder / 'SB104_OFFLINE_TEST.sqlite'
    if output == source:
        raise ValueError('Odmowa pracy na zrodle.')
    try:
        # Read-only URI handles concurrent WAL readers without source writes.
        uri = source.as_uri() + '?mode=ro'
        with sqlite3.connect(uri, uri=True) as read_only:
            with sqlite3.connect(output) as destination:
                read_only.backup(destination)
                check = destination.execute('PRAGMA quick_check').fetchone()[0]
                if check != 'ok':
                    raise ValueError('Kopia SQLite nie przechodzi quick_check.')
        (folder / _MARKER).write_text('TYLKO KOPIA TESTOWA\n', encoding='utf-8')
    except BaseException:
        output.unlink(missing_ok=True)
        (folder / _MARKER).unlink(missing_ok=True)
        raise
    return output


class _ExactProgressRow:
    """Read-only sqlite3.Row facade preserving both named and numeric lookup."""
    def __init__(self, row, overrides):
        self._row = row
        # sqlite3.Row looks up column names without ASCII-case sensitivity.
        # An uppercase column alias must never bypass the exact TEXT value and
        # accidentally expose the saturated 64-bit compatibility mirror.
        self._overrides = {str(name).lower(): value for name, value in overrides.items()}
        self._column_names = frozenset(name.lower() for name in row.keys())
    def keys(self):
        return self._row.keys()
    def __len__(self):
        return len(self._row)
    def __getitem__(self, key):
        if isinstance(key, str) and key.lower() in self._overrides:
            # Only override a real result column; preserve sqlite3.Row's
            # IndexError for missing names even if they are in the mapping.
            if key.lower() in self._column_names:
                return self._overrides[key.lower()]
        if isinstance(key, int):
            return self[self._row.keys()[key]]
        if isinstance(key, slice):
            # sqlite3.Row supports tuple slices as well as positional reads.
            # Both must reflect exact values, not saturated legacy mirrors.
            indices = range(*key.indices(len(self)))
            return tuple(self[index] for index in indices)
        return self._row[key]
    def __iter__(self):
        return (self[key] for key in self.keys())


def read_exact_class_xp_copy(db, account_id, class_name):
    """Read one class XP with conflict detection, only on an attested test copy."""
    _require_copy_path(db)
    if not isinstance(class_name, str) or not class_name or len(class_name) > 160:
        raise ValueError('Niepoprawna nazwa klasy w testowym BigNumber.')
    row = db.conn.execute(
        'SELECT xp FROM class_progress WHERE account_id=? AND class_name=?',
        (account_id, class_name),
    ).fetchone()
    if row is None:
        raise LookupError('Nie znaleziono zapisu tej klasy.')
    legacy = row[0]
    if type(legacy) is not int or legacy < 0:
        raise ValueError('Uszkodzony klasyczny zapis EXP klasy.')
    _require_exact_key_receipt(db.conn, account_id, 'class_progress.xp', class_name)
    table_exists = db.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'"
    ).fetchone()
    if not table_exists:
        return legacy
    shadow = db.conn.execute('''SELECT base_int64_text FROM big_number_shadow_v10400
        WHERE account_id=? AND axis='class_progress.xp' AND source_key=?''',
        (account_id, class_name)).fetchone()
    if shadow is None:
        return legacy
    if number(shadow[0]) != legacy:
        raise ValueError('EXP klasy zmieniony poza migracja: odmawiam nadpisania.')
    return fetch_shadow(db.conn, account_id, 'class_progress.xp', source_key=class_name)


def write_exact_class_xp_copy(db, account_id, class_name, xp, *, level=None):
    """Write class XP as TEXT + saturated legacy mirror, on TEST COPY only.

    A SAVEPOINT ensures both representations are committed or neither.
    Class name is bound as a value, never used as an SQL identifier.
    """
    _require_copy_path(db)
    from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
    exact = number(canonical_uint(xp))
    if level is not None:
        require_sqlite_int64('class_progress.level', level)
    db.conn.execute('SAVEPOINT v104_class_copy_exact')
    try:
        read_exact_class_xp_copy(db, account_id, class_name)  # legacy CAS
        mirror = min(exact, SQLITE_INT64_MAX)
        if level is None:
            changed = db.conn.execute(
                'UPDATE class_progress SET xp=? WHERE account_id=? AND class_name=?',
                (mirror, account_id, class_name),
            )
        else:
            changed = db.conn.execute(
                'UPDATE class_progress SET level=?,xp=? WHERE account_id=? AND class_name=?',
                (level, mirror, account_id, class_name),
            )
        if changed.rowcount != 1:
            raise LookupError('Nie znaleziono klasy: zapis wycofany.')
        install_shadow_schema(db.conn)
        stage_shadow(db.conn, account_id, 'class_progress.xp', exact,
                     source_key=class_name, base_value=mirror)
        _mark_exact_key_receipt(db.conn, account_id, 'class_progress.xp', class_name)
        if read_exact_class_xp_copy(db, account_id, class_name) != exact:
            raise AssertionError('Niepoprawny zapis EXP klasy w TEXT.')
        db.conn.execute('RELEASE SAVEPOINT v104_class_copy_exact')
    except BaseException:
        try:
            db.conn.execute('ROLLBACK TO SAVEPOINT v104_class_copy_exact')
        finally:
            db.conn.execute('RELEASE SAVEPOINT v104_class_copy_exact')
        raise
    return exact

# Exact profession/tool EXP is a copy-only pilot, never production.
_COPY_WORK_TABLES = {
    'profession': ('professions', 'profession', 'actions'),
    'tool': ('tools', 'tool_type', 'uses'),
}


def read_exact_work_xp_copy(db, account_id, kind, key):
    _require_copy_path(db)
    if kind not in _COPY_WORK_TABLES:
        raise ValueError('Nieznany rodzaj postępu.')
    if not isinstance(key, str) or not key.strip() or len(key) > 160:
        raise ValueError('Niepoprawna nazwa profesji lub narzędzia.')
    table, key_col, _ = _COPY_WORK_TABLES[kind]
    row = db.conn.execute(
        f'SELECT xp FROM {table} WHERE account_id=? AND {key_col}=?',
        (account_id, key)).fetchone()
    if row is None:
        raise LookupError('Brak zapisu profesji lub narzędzia.')
    value = row[0]
    if type(value) is not int or value < 0:
        raise ValueError('Nieprawidłowa stara wartość EXP.')
    _require_exact_key_receipt(db.conn, account_id, table + '.xp', key)
    table_exists = db.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'"
    ).fetchone()
    if not table_exists:
        return value
    axis = table + '.xp'
    shadow = db.conn.execute('''SELECT base_int64_text FROM big_number_shadow_v10400
        WHERE account_id=? AND axis=? AND source_key=?''',
        (account_id, axis, key)).fetchone()
    if shadow is None:
        return value
    if number(shadow[0]) != value:
        raise ValueError('EXP zmieniony poza migracją próbną: nie nadpisuj.')
    return fetch_shadow(db.conn, account_id, axis, source_key=key)


def write_exact_work_xp_copy(db, account_id, kind, key, *, level, xp, counter):
    _require_copy_path(db)
    if kind not in _COPY_WORK_TABLES:
        raise ValueError('Nieznany rodzaj postępu.')
    from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
    table, key_col, counter_col = _COPY_WORK_TABLES[kind]
    require_sqlite_int64(table + '.level', level)
    require_sqlite_int64(table + '.' + counter_col, counter)
    exact = number(canonical_uint(xp))
    conn = db.conn
    conn.execute('SAVEPOINT v104_work_copy_only')
    try:
        read_exact_work_xp_copy(db, account_id, kind, key)
        mirror = min(exact, SQLITE_INT64_MAX)
        cursor = conn.execute(
            f'UPDATE {table} SET level=?, xp=?, {counter_col}=? WHERE account_id=? AND {key_col}=?',
            (level, mirror, counter, account_id, key))
        if cursor.rowcount != 1:
            raise LookupError('Nie znaleziono profesji lub narzędzia.')
        install_shadow_schema(conn)
        stage_shadow(conn, account_id, table + '.xp', exact,
                     source_key=key, base_value=mirror)
        _mark_exact_key_receipt(conn, account_id, table + '.xp', key)
        if read_exact_work_xp_copy(db, account_id, kind, key) != exact:
            raise AssertionError('Niedokładny zapis EXP pracy.')
        conn.execute('RELEASE SAVEPOINT v104_work_copy_only')
    except BaseException:
        try:
            conn.execute('ROLLBACK TO SAVEPOINT v104_work_copy_only')
        finally:
            conn.execute('RELEASE SAVEPOINT v104_work_copy_only')
        raise
    return exact

# v104 test-copy currency bridge. No production activation; do not change
# normal wallet or bank limits without migrating ALL game money paths.
_CURRENCY_KEYS = ('silver', 'gold', 'mithril')
_CURRENCY_TABLES = {
    'wallet': ('account_wallet', 'master_account_id'),
    'bank': ('bank_balances', 'account_id'),
}


def currency_total_copy(silver, gold, mithril):
    """Exact silver total using integer arithmetic only (100 / 100000)."""
    from core.bootstrap_economy_professions import (
        SILVER_PER_GOLD, SILVER_PER_MITHRIL,
    )
    a, b, c = (number(canonical_uint(x)) for x in (silver, gold, mithril))
    total = a + b * SILVER_PER_GOLD + c * SILVER_PER_MITHRIL
    return number(canonical_uint(total))


def read_exact_currency_copy(db, account_id, kind):
    """Read and verify three mirrored denominations on a fenced DB only."""
    _require_copy_path(db)
    if kind not in _CURRENCY_TABLES:
        raise ValueError('Nieznana tabela walutowa w kopii testowej.')
    table, pk = _CURRENCY_TABLES[kind]
    row = db.conn.execute(
        f'SELECT silver,gold,mithril FROM "{table}" WHERE "{pk}"=?',
        (account_id,),
    ).fetchone()
    if row is None:
        return None
    results = []
    shadow_exists = db.conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'"
    ).fetchone() is not None
    _require_complete_shadow_group(
        db.conn, account_id, tuple(table + '.' + field for field in _CURRENCY_KEYS)
    )
    for field, legacy in zip(_CURRENCY_KEYS, row):
        if type(legacy) is not int or legacy < 0:
            raise ValueError('Niepoprawna waluta INTEGER w kopii testowej.')
        if not shadow_exists:
            results.append(legacy)
            continue
        axis = table + '.' + field
        ref = db.conn.execute('''SELECT base_int64_text FROM big_number_shadow_v10400
            WHERE account_id=? AND axis=? AND source_key='' ''',
            (account_id, axis)).fetchone()
        if ref is None:
            results.append(legacy)
            continue
        if number(ref[0]) != legacy:
            raise ValueError('Waluta INTEGER zmieniona poza migracją próbną.')
        results.append(fetch_shadow(db.conn, account_id, axis))
    return tuple(results)


def write_exact_currency_copy(db, account_id, kind, silver, gold, mithril):
    """Exact wallet/bank TEXT + int64 mirror in one nested SAVEPOINT.

    For wallet, all character-slot mirrors and their TEXT values update in the
    *same* transaction. On conflict, neither money nor player data changes.
    """
    _require_copy_path(db)
    if kind not in _CURRENCY_TABLES:
        raise ValueError('Nieznana tabela walutowa w kopii testowej.')
    from core.big_numbers_v10400 import legacy_sqlite_uint
    uid = legacy_sqlite_uint(account_id)
    if uid < 1:
        raise ValueError('Brak identyfikatora konta.')
    total = currency_total_copy(silver, gold, mithril)
    table, pk = _CURRENCY_TABLES[kind]
    conn = db.conn
    conn.execute('SAVEPOINT v104_currency_copy_atomic')
    try:
        previous = read_exact_currency_copy(db, uid, kind)
        if previous is None:
            if kind == 'bank':
                raise LookupError('Brak rachunku bankowego; najpierw ensure_bank.')
            # Historically, an account wallet can be absent before its first save.
            conn.execute('INSERT INTO account_wallet(master_account_id,silver,gold,mithril) '
                         'VALUES(?,0,0,0)', (uid,))
        mirror = min(total, SQLITE_INT64_MAX)
        conn.execute(f'UPDATE "{table}" SET silver=?,gold=0,mithril=0 WHERE "{pk}"=?',
                     (mirror, uid))
        install_shadow_schema(conn)
        # Retain the older 14-axis pilot scope for ordinary in-range saves.
        # New currency shadow rows are necessary only after a true overflow,
        # or when overwriting an already-migrated TEXT balance.
        prior_currency = conn.execute('''SELECT 1 FROM big_number_shadow_v10400
            WHERE account_id=? AND axis IN (?,?,?) LIMIT 1''',
            (uid, *(table + '.' + f for f in _CURRENCY_KEYS))).fetchone()
        use_currency_shadow = total > SQLITE_INT64_MAX or prior_currency is not None
        if use_currency_shadow:
            for field, exact, old_value in zip(_CURRENCY_KEYS, (total, 0, 0),
                                               (mirror, 0, 0)):
                stage_shadow(conn, uid, table + '.' + field, exact, base_value=old_value)
            _mark_complete_copy_group(conn, uid,
                tuple(table + '.' + field for field in _CURRENCY_KEYS))
        if kind == 'wallet':
            character_ids = [row[0] for row in conn.execute('''SELECT
                ac.character_account_id FROM account_characters ac
                JOIN characters c ON c.account_id=ac.character_account_id
                WHERE ac.master_account_id=?''', (uid,))]
            for char_id in character_ids:
                # Fail-closed if any legacy character slot changed independently.
                for field in _CURRENCY_KEYS:
                    read_exact_progression_copy(db, char_id, field)
            conn.execute('''UPDATE characters SET silver=?,gold=0,mithril=0
                WHERE account_id IN (SELECT character_account_id
                FROM account_characters WHERE master_account_id=?)''', (mirror, uid))
            for char_id in character_ids:
                prior_char = conn.execute('''SELECT 1 FROM big_number_shadow_v10400
                    WHERE account_id=? AND axis IN (
                    'characters.silver','characters.gold','characters.mithril') LIMIT 1''',
                    (char_id,)).fetchone()
                if use_currency_shadow or prior_char:
                    for field, exact, old_value in zip(_CURRENCY_KEYS, (total, 0, 0),
                                                       (mirror, 0, 0)):
                        stage_shadow(conn, char_id, 'characters.' + field, exact,
                                     base_value=old_value)
                    _mark_complete_copy_group(conn, char_id,
                        tuple('characters.' + field for field in _CURRENCY_KEYS))
        if read_exact_currency_copy(db, uid, kind) != (total, 0, 0):
            raise AssertionError('Portfel nie zachowal pelnej kwoty TEXT.')
        conn.execute('RELEASE SAVEPOINT v104_currency_copy_atomic')
        return total, 0, 0
    except BaseException:
        try:
            conn.execute('ROLLBACK TO SAVEPOINT v104_currency_copy_atomic')
        finally:
            conn.execute('RELEASE SAVEPOINT v104_currency_copy_atomic')
        raise
