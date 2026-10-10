# -*- coding: utf-8 -*-
"""v1.17.8: multi-session combat-log/SQLite regression tests without server socket."""
from __future__ import annotations

import ast
from contextlib import closing
import asyncio
import re
from pathlib import Path
import os
import sqlite3
import tempfile
import time
from types import SimpleNamespace

# This legacy session mixin needs a late-bound native world namespace on import.
# Compile only its unchanged, actual method ASTs for an isolated transport test.
_source = Path(__file__).resolve().parents[1] / 'player/session_mixins/io_auth_character.py'
_tree = ast.parse(_source.read_text(encoding='utf-8'), filename=str(_source))
_class = next(x for x in _tree.body if isinstance(x, ast.ClassDef) and x.name == 'SessionIOAuthCharacterMixin')
_methods = {'encode_session_text', 'combat_log_mode_cached_v1178', 'send', 'send_combat', 'set_combat_log'}
_selected = [x for x in _class.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name in _methods]
assert {x.name for x in _selected} == _methods
_node = ast.ClassDef(name='SessionIOAuthCharacterMixin', bases=[], keywords=[], body=_selected, decorator_list=[])
_mini = ast.fix_missing_locations(ast.Module(body=[_node], type_ignores=[]))
_ns = {'time': time, 're': re, 'COMBAT_LOG_MODE_CACHE_SECONDS_V1178': 30.0}
exec(compile(_mini, str(_source), 'exec'), _ns)
SessionIOAuthCharacterMixin = _ns['SessionIOAuthCharacterMixin']
from storage.db_progression import DatabaseProgressionMixin
from storage.db_crafting_extensions import DatabaseCraftingExtensionsMixin


class _Writer:
    def __init__(self):
        self.messages = []

    def write(self, data):
        self.messages.append(data)

    async def drain(self):
        await asyncio.sleep(0)


class _CountingDb:
    def __init__(self):
        self.modes = {}
        self.reads = {}
        self.saved = []

    def combat_log_mode(self, account):
        self.reads[account] = self.reads.get(account, 0) + 1
        return self.modes.get(account, 'normal')

    def set_combat_log_mode(self, account, mode):
        self.modes[account] = mode
        return mode

    def add_combat_event_v0320(self, account, text, kind):
        self.saved.append((account, text, kind))


class _Session(SessionIOAuthCharacterMixin):
    def __init__(self, db, account):
        self.server = SimpleNamespace(db=db)
        self.account_id = account
        self.auto_queue_casting = False
        self.combat_mob_key = None
        self.closed = False
        self.writer = _Writer()
        self.output_encoding = 'utf-8'
        self.history_replaying = False
        self.record_history_buffer = lambda *args, **kwargs: None
        self.normalize_description_query = lambda x: str(x).strip().lower()


async def _async_checks(check):
    db = _CountingDb()
    sessions = [_Session(db, i) for i in range(1, 5)]
    # Four players output 400 battle messages each while the event loop rotates.
    await asyncio.gather(*(one.send('Cios', combat_detail='normal', history_store=False)
                           for one in sessions for _ in range(400)))
    check(sum(db.reads.values()) == 4,
          'one SQLite mode query per session, not per 1600 combat messages')
    check(sum(len(one.writer.messages) for one in sessions) == 1600,
          'concurrent clients receive all normal combat messages')

    a = sessions[0]
    await a.set_combat_log('concise')
    start = len(a.writer.messages)
    await a.send('Zwykły atak', combat_detail='normal', history_store=False)
    await a.send('Ważne ostrzeżenie', combat_detail='essential', history_store=False)
    check(len(a.writer.messages) == start + 1,
          'concise filters ordinary hits but keeps essential warning')
    check(db.reads[1] == 1, 'changing mode is immediate without SQLite reread')

    await a.set_combat_log('full')
    start = len(a.writer.messages)
    await a.send('Pełny szczegół', combat_detail='full', history_store=False)
    check(len(a.writer.messages) == start + 1, 'full restores complete combat logs immediately')

    a.account_id = 50
    await a.send('Nowa postać', combat_detail='normal', history_store=False)
    check(db.reads.get(50) == 1, 'changing character ID cannot reuse previous mode')
    check(a.combat_log_mode_cached_v1178() == 'normal', 'new character defaults to normal')
    a._combat_log_mode_cache_v1178 = (50, 'full', time.monotonic()-90)
    db.modes[50] = 'concise'
    check(a.combat_log_mode_cached_v1178() == 'concise', 'external mode update seen after TTL')
    check(db.reads.get(50) == 2, 'expiry forces exactly one fresh SQLite lookup')

    await a.send_combat('Zapamiętane wydarzenie', 'essential')
    check((50, 'Zapamiętane wydarzenie', 'combat') in db.saved,
          'combat event history remains persisted despite output cache')


def audit_stability_v1178():
    errors = []
    checks = 0

    def check(ok, description):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(description)

    asyncio.run(_async_checks(check))

    # Exercise the actual progress database method via SQLite, not a mock.
    with tempfile.TemporaryDirectory(prefix='sb1178-') as folder:
        con = sqlite3.connect(os.path.join(folder, 'combat.db'))
        con.row_factory = sqlite3.Row
        con.execute('CREATE TABLE combat_log_settings(account_id INTEGER PRIMARY KEY, mode TEXT NOT NULL)')
        con.execute('CREATE TABLE skill_queue_settings(account_id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0)')
        con.execute('CREATE TABLE skill_queue(account_id INTEGER, queue_type TEXT, position INTEGER, skill_id TEXT, PRIMARY KEY(account_id,queue_type,position))')
        obj = object.__new__(DatabaseProgressionMixin)
        obj.conn = con
        check(obj.combat_log_mode(1) == 'normal', 'missing combat mode row created with default')
        check(con.execute('SELECT count(*) FROM combat_log_settings').fetchone()[0] == 1,
              'first lookup persists default mode')
        obj.set_combat_log_mode(1, 'full')
        check(obj.combat_log_mode(1) == 'full', 'existing saved full mode read unchanged')
        obj.set_combat_log_mode(1, 'concise')
        check(obj.combat_log_mode(1) == 'concise', 'existing saved concise mode read unchanged')
        check(con.execute('SELECT count(*) FROM combat_log_settings').fetchone()[0] == 1,
              'repeat reads do not duplicate mode rows')
        check(obj.skill_queue_enabled(1) is False, 'new player autoqueue starts disabled')
        check(con.execute('SELECT count(*) FROM skill_queue_settings').fetchone()[0] == 1,
              'default autoqueue persisted once')
        obj.set_skill_queue_enabled(1, True)
        for _ in range(500):
            check(obj.skill_queue_enabled(1) is True, 'enabled autoqueue survives repeated reads')
        obj.set_skill_queue_enabled(1, False)
        check(not obj.skill_queue_enabled(1), 'queue can be disabled immediately')
        obj.set_skill_queue_enabled(1, True)
        check(obj.add_skill_queue_entry(1, 'physical', 'slash')[0], 'physical skill appended')
        check(obj.add_skill_queue_entry(1, 'magic', 'fire')[0], 'magic skill appended')
        check(obj.add_skill_queue_entry(1, 'feedback', 'vmax')[0], 'feedback skill appended')
        check(not obj.add_skill_queue_entry(1, 'magic', 'slash')[0], 'same skill not duplicated')
        check(obj.add_skill_queue_entry(2, 'physical', 'slash')[0], 'second character has independent queue')
        con.commit()
        con.close()
        con = sqlite3.connect(os.path.join(folder, 'combat.db'))
        con.row_factory = sqlite3.Row
        obj.conn = con
        check(obj.skill_queue_enabled(1), 'reopened SQLite retains enabled status')
        check([r['skill_id'] for r in obj.skill_queue_rows(1)] == ['slash','fire','vmax'],
              'reopened SQLite retains all three Mec queue channels')
        check([r['skill_id'] for r in obj.skill_queue_rows(2)] == ['slash'],
              'second player queue independent after restart')
        check(obj.remove_skill_queue_entry(1, 'physical', 1) == 'slash',
              'remove queue entry works after restart')
        check([r['skill_id'] for r in obj.skill_queue_rows(1)] == ['fire','vmax'],
              'removal does not alter other queue channels')
        events = object.__new__(DatabaseCraftingExtensionsMixin)
        events.conn = con
        events.install_v0320_schema()
        for acct in range(1, 5):
            for n in range(60):
                events.add_combat_event_v0320(acct, f'Cios {n}', 'combat')
        for acct in range(1, 5):
            rows = con.execute('SELECT event_text FROM combat_events_v0320 WHERE account_id=? ORDER BY id', (acct,)).fetchall()
            check(len(rows) == 40, f'account {acct} retains exactly 40 latest combat events')
            check(rows[0]['event_text'] == 'Cios 20' and rows[-1]['event_text'] == 'Cios 59',
                  f'account {acct} event history remains ordered and isolated')
        con.commit()
        con.close()
        with closing(sqlite3.connect(os.path.join(folder, 'combat.db'))) as reopened:
            check(reopened.execute('SELECT count(*) FROM combat_events_v0320').fetchone()[0] == 160,
                  'all 160 historical events survive SQLite restart')
    return {'checks': checks, 'errors': errors, 'error_count': len(errors),
            'clients': 4, 'messages': 1600}


if __name__ == '__main__':
    result = audit_stability_v1178()
    print('STABILITY v1.17.8:', result)
    if result['error_count']:
        raise SystemExit(1)
