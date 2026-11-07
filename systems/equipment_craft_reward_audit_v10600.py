# -*- coding: utf-8 -*-
"""v106 staging: explicitly documented MANUAL settlement of uncertain craft grants.

This never grants an item, XP, quest, guild or collection reward. It only
unblocks a disposable-copy account AFTER an operator has separately verified
all affected systems. It is not a production migration or automatic replay.
"""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
import re

from systems.equipment_crafting_guard_v10600 import active
from systems.equipment_craft_reward_journal_v10600 import STAGES

_DOMAINS = ('collections', 'quest', 'guild', 'xp')
_ALLOWED = frozenset(('zgodne', 'skorygowano_osobno'))
_CONFIRMATION = 'POTWIERDZAM RECZNY AUDYT CZTERECH NAGROD BEZ PONOWNEJ WYPLATY'
_HEX32 = re.compile(r'^[0-9a-f]{32}$')


def _read_database(db):
    if not active(db):
        raise PermissionError('v106: audyt tylko w izolowanym stagingu')
    return db.conn


def _row(db, account_id, run_id):
    conn = _read_database(db)
    if type(account_id) is not int or account_id < 1:
        raise ValueError('v106: nieprawidlowe konto')
    if not isinstance(run_id, str) or _HEX32.fullmatch(run_id) is None:
        raise ValueError('v106: nieprawidlowy identyfikator wykonania')
    # No DDL here: inspecting a journal must not alter SQLite.
    exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' "
                          "AND name='v106_craft_reward_journal'").fetchone()
    if not exists:
        return None
    row = conn.execute('''SELECT run_id,account_id,recipe_id,base_item_id,
                 output_id,output_qty,stage,created_at,updated_at
                 FROM v106_craft_reward_journal
                 WHERE run_id=? AND account_id=?''', (run_id, account_id)).fetchone()
    if row is None:
        return None
    if row[6] not in STAGES or type(row[5]) is not int or row[5] <= 0:
        raise RuntimeError('v106: uszkodzone dane dziennika, audyt wstrzymany')
    return dict(zip(('run_id','account_id','recipe_id','base_item_id',
                     'output_id','output_qty','stage','created_at','updated_at'), row))


def _fingerprint(row):
    payload = json.dumps(row, ensure_ascii=True, sort_keys=True,
                         separators=(',', ':')).encode('ascii')
    return hashlib.sha256(payload).hexdigest()


def inspect(db, account_id, run_id):
    """Read-only snapshot with stale-state fingerprint; no effects, no DDL."""
    row = _row(db, account_id, run_id)
    if row is None:
        raise LookupError('v106: brak wskazanego rozliczenia na koncie')
    return {**row, 'fingerprint': _fingerprint(row),
            'uncertainty': ('Etap oznacza ostatni zapisany checkpoint, '
                            'nie dowod otrzymania wszystkich nagrod.'),
            'automatic_grants': False}


def close_after_verified_manual_audit(db, account_id, run_id, *,
                                      fingerprint, operator, reviews, confirmation):
    """Close only a verified pending receipt on an EXPLICIT disposable DB.

    ``reviews`` supplies independent evidence for all four non-atomic domains.
    No XP, quest or other grant is issued. A unique immutable audit receipt is
    stored within the same SQLite SAVEPOINT as marking the run complete.
    """
    if not active(db) or getattr(db, '_v106_craft_audit_disposable_copy', False) is not True:
        raise PermissionError('v106: zamykanie wymaga drugiego oznaczenia KOPII testowej')
    if confirmation != _CONFIRMATION:
        raise PermissionError('v106: wymagane pelne reczne potwierdzenie audytu')
    if not isinstance(operator, str) or not 3 <= len(operator.strip()) <= 80 or any(
            ord(ch)<32 for ch in operator):
        raise ValueError('v106: podpis operatora jest nieprawidlowy')
    if not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
        raise ValueError('v106: nieprawidlowy identyfikator snapshotu')
    if not isinstance(reviews, dict) or set(reviews) != set(_DOMAINS):
        raise ValueError('v106: oddzielnie sprawdz kolekcje, quest, gildie i EXP')
    checked = {}
    evidences = set()
    for key in _DOMAINS:
        value=reviews[key]
        if not isinstance(value, dict) or set(value) != {'status','evidence'}:
            raise ValueError('v106: brak statusu i uzasadnienia dla '+key)
        status, evidence = value['status'], value['evidence']
        if status not in _ALLOWED or not isinstance(evidence,str) or not (16 <= len(evidence.strip()) <= 1000):
            raise ValueError('v106: niekompletna kontrola '+key)
        if any(ord(ch)<32 for ch in evidence):
            raise ValueError('v106: niedozwolone znaki w audycie '+key)
        normalized = evidence.strip().casefold()
        if normalized in evidences:
            raise ValueError('v106: kazda dziedzina wymaga osobnego dowodu')
        evidences.add(normalized)
        checked[key]={'status':status,'evidence':evidence.strip()}
    conn = _read_database(db)
    owner = conn.deferred_commits() if hasattr(conn,'deferred_commits') else nullcontext()
    with owner:
        conn.execute('SAVEPOINT v106_manual_craft_reward_resolution')
        try:
            before = _row(db, account_id, run_id)
            if before is None or before['stage'] == 'complete':
                raise RuntimeError('v106: brak otwartego rozliczenia; nie powtarzaj audytu')
            if _fingerprint(before) != fingerprint:
                raise RuntimeError('v106: dziennik zmienil sie od audytu; odczytaj go ponownie')
            conn.execute('''CREATE TABLE IF NOT EXISTS v106_craft_reward_manual_audit (
                run_id TEXT PRIMARY KEY,
                account_id INTEGER NOT NULL,
                previous_stage TEXT NOT NULL,
                snapshot_sha256 TEXT NOT NULL,
                operator TEXT NOT NULL,
                reviews_json TEXT NOT NULL,
                decision TEXT NOT NULL DEFAULT 'manual_verified_no_replay',
                reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''')
            conn.execute('''INSERT INTO v106_craft_reward_manual_audit
                (run_id,account_id,previous_stage,snapshot_sha256,operator,reviews_json)
                VALUES(?,?,?,?,?,?)''',(
                run_id, account_id, before['stage'], fingerprint, operator.strip(),
                json.dumps(checked, ensure_ascii=False, sort_keys=True)))
            changed=conn.execute('''UPDATE v106_craft_reward_journal
                SET stage='complete',updated_at=CURRENT_TIMESTAMP
                WHERE run_id=? AND account_id=? AND stage=? AND updated_at=?''',
                (run_id,account_id,before['stage'],before['updated_at'])).rowcount
            if changed!=1:
                raise RuntimeError('v106: konflikt zapisu dziennika; anulowano odblokowanie')
            conn.execute('RELEASE SAVEPOINT v106_manual_craft_reward_resolution')
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT v106_manual_craft_reward_resolution')
            conn.execute('RELEASE SAVEPOINT v106_manual_craft_reward_resolution')
            raise
    return {'run_id': run_id, 'account_id': account_id,
            'old_stage': before['stage'], 'new_stage': 'complete',
            'automatic_grants': False}


CONFIRMATION = _CONFIRMATION
REVIEW_DOMAINS = _DOMAINS
