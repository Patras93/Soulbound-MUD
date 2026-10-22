# -*- coding: utf-8 -*-
"""Admin-only NEWS channel regression without production database mutations."""
import asyncio
import ast
from pathlib import Path
import sqlite3
from types import SimpleNamespace

# Inspect the exact production method without importing the entire runtime
# (which requires its initialized world catalogues).
_source = Path(__file__).resolve().parents[1] / 'player/session_mixins/social_expansion.py'
_tree = ast.parse(_source.read_text('utf-8'))
_group = next(node for node in _tree.body if isinstance(node, ast.ClassDef) and node.name == 'SessionSocialExpansionMixin')
_method = next(node for node in _group.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'news_channel_v1204')
_single = ast.ClassDef(name='SessionSocialExpansionMixin', bases=[], keywords=[], body=[_method], decorator_list=[])
_module = ast.fix_missing_locations(ast.Module(body=[_single], type_ignores=[]))
_scope = {'normalize_lookup_text': lambda value: str(value).strip().lower()}
exec(compile(_module, str(_source), 'exec'), _scope)
SessionSocialExpansionMixin = _scope['SessionSocialExpansionMixin']


class _DB:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE social_channel_settings_v03051(account_id INTEGER,channel TEXT,enabled INTEGER,PRIMARY KEY(account_id,channel));
        CREATE TABLE social_channel_history_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT,channel TEXT,sender_account_id INTEGER,sender_name TEXT,message TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        self.actions = []

    def account_name(self, aid):
        return 'admin' if int(aid) == 1 else 'player'

    def record_admin_action_v1224(self, user, action, target=''):
        self.actions.append((user, action, target))


class _Session:
    def __init__(self, server, aid, admin=False):
        self.server = server
        self.account_id = aid
        self.master_account_id = aid
        self.character = SimpleNamespace(name='Administrator' if admin else 'Gracz')
        self.closed = False
        self.admin = admin
        self.sent = []

    def is_admin(self):
        return self.admin

    def channel_enabled_v03051(self, channel):
        row = self.server.db.conn.execute('SELECT enabled FROM social_channel_settings_v03051 WHERE account_id=? AND channel=?', (self.account_id, channel)).fetchone()
        return row is None or bool(row['enabled'])

    async def send(self, text, **kwargs):
        self.sent.append(str(text))

    async def show_channel_history_v03051(self, channel, limit=20):
        rows = self.server.db.conn.execute('SELECT message FROM social_channel_history_v03051 WHERE channel=? ORDER BY id DESC LIMIT ?', (channel,limit)).fetchall()
        for row in rows: await self.send(row['message'])

    def is_ignored_v03051(self, aid, other):
        return False


async def _check():
    db = _DB()
    server = SimpleNamespace(db=db, sessions=[])
    admin = _Session(server, 1, True)
    gracz = _Session(server, 2, False)
    server.sessions = [admin, gracz]
    count = 0
    cmd = SessionSocialExpansionMixin.news_channel_v1204
    await cmd(gracz, 'Przejmuję serwer')
    assert any('tylko administratorzy' in m for m in gracz.sent); count += 1
    assert db.conn.execute('SELECT COUNT(*) FROM social_channel_history_v03051').fetchone()[0] == 0; count += 1
    await cmd(admin, 'Zaktualizowano Krypty')
    assert db.conn.execute('SELECT COUNT(*) FROM social_channel_history_v03051').fetchone()[0] == 1; count += 1
    assert any('[NEWS] Administracja' in m for m in gracz.sent); count += 1
    assert len(db.actions) == 1; count += 1
    await cmd(gracz, 'off')
    assert not gracz.channel_enabled_v03051('news'); count += 1
    sent = len(gracz.sent)
    await cmd(admin, 'Dodano nowe lokacje')
    assert len(gracz.sent) == sent; count += 1
    assert db.conn.execute('SELECT COUNT(*) FROM social_channel_history_v03051').fetchone()[0] == 2; count += 1
    await cmd(gracz, 'on')
    assert gracz.channel_enabled_v03051('news'); count += 1
    await cmd(gracz, '')
    assert any('Dodano nowe lokacje' in m for m in gracz.sent); count += 1
    await cmd(admin, 'x'*501)
    assert db.conn.execute('SELECT COUNT(*) FROM social_channel_history_v03051').fetchone()[0] == 2; count += 1
    db.conn.close()
    return count


def run_regression():
    return asyncio.run(_check())

if __name__ == '__main__':
    print(f'V12.00.4 KANAL NEWS ADMIN ONLY: {run_regression()} checks PASS')
