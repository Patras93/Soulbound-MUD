# -*- coding: utf-8 -*-
"""v104 etap 13: atomowy koszyk nagrod BigNumber, TYLKO na izolowanej kopii.

To prototyp magazynu nagrod; nie jest podpiety do normalnej walki ani
Database.__init__. Legacy INTEGER nie sa nadpisywane. Nie uruchamiac na produkcji.
"""
from __future__ import annotations

from hashlib import sha256
import json
import sqlite3

from core.big_numbers_v10400 import canonical_uint
from storage.big_number_events_v10400 import apply_event_copy, _ID
from storage.big_number_shadow_v10400 import _validate_axis


class RewardBundleConflictV104(ValueError):
    """Powtorzenie innej listy wyplat pod identyfikatorem starego zdarzenia."""


class RewardBundleCorruptV104(RuntimeError):
    """Niespojna historia wyplat; nie wolno dokonywac zapisu."""


def _canonical(account_id: int, event_id: str, deltas: dict) -> tuple[str, tuple]:
    if type(account_id) is not int or not 1 <= account_id <= (1 << 63) - 1:
        raise ValueError('Niepoprawny identyfikator postaci.')
    if type(event_id) is not str or not _ID.fullmatch(event_id):
        raise ValueError('Niepoprawny identyfikator nagrody.')
    if not isinstance(deltas, dict) or not deltas or len(deltas) > 24:
        raise ValueError('Podaj od 1 do 24 osi nagrod.')
    parts = []
    for item, delta in deltas.items():
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError('Oczekiwano klucza (os, podklucz).')
        axis, subkey = item
        _validate_axis(axis, subkey)
        if type(delta) is not int:
            raise TypeError('Kwoty musza byc calkowite, bez float/bool.')
        magnitude = canonical_uint(abs(delta))
        parts.append((axis, subkey, (delta > 0) - (delta < 0), magnitude))
    parts.sort()
    document = json.dumps([str(account_id), event_id, parts], ensure_ascii=True,
                          separators=(',', ':'))
    return sha256(document.encode('ascii')).hexdigest(), tuple(parts)


def _install(conn: sqlite3.Connection) -> None:
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_reward_bundles_v10400 (
        account_id INTEGER NOT NULL,
        event_id TEXT NOT NULL,
        payload_sha256 TEXT NOT NULL,
        axis_count INTEGER NOT NULL CHECK(axis_count BETWEEN 1 AND 24),
        PRIMARY KEY(account_id,event_id)
    )''')


def apply_reward_bundle_copy(conn: sqlite3.Connection, account_id: int,
                             event_id: str, deltas: dict) -> dict[tuple, int]:
    """Atomowo wyplac kilka osi i potwierdz jeden event (tylko kopia DB).

    Dopuszcza zewnetrzna transakcje SAVEPOINT. Replays kontroluja kwoty,
    istnienie kazdego podzdarzenia, integralnosc shadow i zgodnosc legacy.
    Nie przenosi EXP do normalnych kolumn INTEGER ani obiektu gracza.
    """
    digest, parts = _canonical(account_id, event_id, deltas)
    conn.execute('SAVEPOINT v104_bundle_atomic')
    try:
        _install(conn)
        row = conn.execute('''SELECT payload_sha256,axis_count
               FROM big_number_reward_bundles_v10400
               WHERE account_id=? AND event_id=?''', (account_id, event_id)).fetchone()
        if row is not None and (row[0] != digest or row[1] != len(parts)):
            raise RewardBundleConflictV104('Identyfikator juz rozliczono z innym zestawem nagrod.')
        if row is None:
            # A previous transaction cannot leave partial sub-events. If one
            # exists without a bundle receipt, do not silently accept it.
            orphaned = conn.execute('''SELECT 1 FROM sqlite_master
                    WHERE type='table' AND name='big_number_events_v10400' ''').fetchone()
            if orphaned:
                prior = conn.execute('''SELECT 1 FROM big_number_events_v10400
                     WHERE account_id=? AND event_id=? LIMIT 1''',
                     (account_id, event_id)).fetchone()
                if prior:
                    raise RewardBundleCorruptV104('Osierocona wyplata, potrzebna diagnostyka.')
        else:
            # Do not try to "repair" missing events after receipt. A missing
            # row is evidence of corruption, and must fail closed.
            recorded = conn.execute('''SELECT axis, source_key FROM big_number_events_v10400
                WHERE account_id=? AND event_id=?''',
                (account_id, event_id)).fetchall()
            if {tuple(r) for r in recorded} != {(a, k) for a, k, _, _ in parts} or len(recorded) != len(parts):
                raise RewardBundleCorruptV104('Niekompletny lub nadmiarowy pakiet wyplat.')
        result = {}
        for axis, key, sign, amount in parts:
            delta = sign * int(amount)
            result[(axis, key)] = apply_event_copy(
                conn, account_id, axis, delta, event_id, source_key=key)
        if row is None:
            conn.execute('''INSERT INTO big_number_reward_bundles_v10400
                (account_id,event_id,payload_sha256,axis_count) VALUES (?,?,?,?)''',
                (account_id, event_id, digest, len(parts)))
        conn.execute('RELEASE SAVEPOINT v104_bundle_atomic')
        return result
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v104_bundle_atomic')
        conn.execute('RELEASE SAVEPOINT v104_bundle_atomic')
        raise


def preview_quest_xp_bundle_copy(quest_id: str, quest: dict,
                                  *, class_name: str) -> dict:
    """Adapter rzeczywistego kalkulatora questow; bez wpisow do SQLite.

    Zachowuje tylko osie obecnie obsługiwane przez pilot TEXT. Pozostale
    statystyki, profesje, narzedzia i Multi Cap MUSZA byc osobno przeniesione.
    """
    from systems.quest_reward_floor_v1020012 import quest_xp_plan
    from core.classes_skills import CLASSES
    if class_name not in {row[0] for row in CLASSES}:
        raise ValueError('Nieznana klasa.')
    plan = quest_xp_plan(quest_id, quest)
    result = {('characters.character_xp',''): int(plan['character'])}
    if plan['soul']:
        result[('characters.soul_xp','')] = int(plan['soul'])
    if plan['class_xp']:
        result[('class_progress.xp',class_name)] = int(plan['class_xp'])
    return result
