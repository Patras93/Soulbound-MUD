# -*- coding: utf-8 -*-
"""Regression of admin-owned cleanup: old logs survive migration, live logs survive purge."""
import sqlite3
from storage.database import Database, _DeferredCommitConnection, ensure_admin_error_status_v1371


def run_admin_error_cleanup_v1371():
    raw = sqlite3.connect(":memory:")
    raw.row_factory = sqlite3.Row
    raw.executescript("""
        CREATE TABLE admin_errors_v1224 (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            exception TEXT NOT NULL, file TEXT NOT NULL, line INTEGER NOT NULL,
            subsystem TEXT NOT NULL, handler TEXT NOT NULL
        );
        CREATE TABLE admin_actions_v1224 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            admin_login TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL DEFAULT ''
        );
        INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler)
          VALUES('SB-11111111','TypeError','example.py',1,'test','old');
        INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler)
          VALUES('SB-22222222','ValueError','other.py',2,'test','active');
    """)
    wrapper = _DeferredCommitConnection(raw)
    ensure_admin_error_status_v1371(wrapper)
    ensure_admin_error_status_v1371(wrapper)
    db = Database.__new__(Database)
    db.conn = wrapper
    old = wrapper.execute("SELECT * FROM admin_errors_v1224 WHERE id='SB-11111111'").fetchone()
    assert old and old['resolved_at'] == ''
    assert db.set_admin_error_resolved_v1371('SB-11111111','owner')
    assert not db.set_admin_error_resolved_v1371('SB-INVALID','owner')
    assert not db.set_admin_error_resolved_v1371('SB-33333333','owner')
    assert db.set_admin_error_resolved_v1371('SB-11111111','owner',False)
    assert wrapper.execute("SELECT resolved_at FROM admin_errors_v1224 WHERE id='SB-11111111'").fetchone()[0] == ''
    assert db.set_admin_error_resolved_v1371('SB-11111111','owner')
    assert db.purge_resolved_admin_errors_v1371('owner') == 1
    assert db.purge_resolved_admin_errors_v1371('owner') == 0
    assert wrapper.execute("SELECT COUNT(*) FROM admin_errors_v1224").fetchone()[0] == 1
    assert wrapper.execute("SELECT id FROM admin_errors_v1224").fetchone()[0] == 'SB-22222222'
    assert wrapper.execute("SELECT action,target FROM admin_actions_v1224 WHERE action='errors_purge_fixed' ORDER BY id LIMIT 1").fetchone()['target'] == 'count=1'
    raw.close()
    return {"checks": 13, "errors": 0}


if __name__ == '__main__':
    print(run_admin_error_cleanup_v1371())


def run_admin_error_commands_v1371():
    """Actual admin-command dispatch and permission tests; call after server bootstrap."""
    import asyncio
    from types import SimpleNamespace
    from player.session_mixins.admin_tools import SessionAdminToolsMixin
    from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES

    raw = sqlite3.connect(":memory:")
    raw.row_factory = sqlite3.Row
    raw.executescript("""
        CREATE TABLE admin_errors_v1224 (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            exception TEXT NOT NULL, file TEXT NOT NULL, line INTEGER NOT NULL,
            subsystem TEXT NOT NULL, handler TEXT NOT NULL,
            resolved_at TEXT NOT NULL DEFAULT '', resolved_by TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE admin_actions_v1224 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            admin_login TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL DEFAULT ''
        );
        INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler)
          VALUES('SB-AAAAAAAA','ValueError','one.py',23,'test','fixed');
        INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler)
          VALUES('SB-BBBBBBBB','TypeError','two.py',7,'test','live');
    """)
    db = Database.__new__(Database)
    db.conn = _DeferredCommitConnection(raw)
    db.account_name = lambda account_id: 'unauthorized'

    class FakeSession(SessionAdminToolsMixin):
        master_account_id = 1

        def __init__(self):
            self.server = SimpleNamespace(db=db)
            self.messages = []

        def normalize_description_query(self, value):
            return str(value).strip().casefold()

        async def send(self, value, **kwargs):
            self.messages.append(value)

    async def check_commands():
        actor = FakeSession()
        await actor.admin_command('blad naprawiony SB-AAAAAAAA')
        assert db.conn.execute("SELECT resolved_at FROM admin_errors_v1224 WHERE id='SB-AAAAAAAA'").fetchone()[0] == ''
        assert actor.messages[-1].startswith('Nieznana komenda')
        db.account_name = lambda account_id: 'admincleanupv1371'
        await actor.admin_command('blad naprawiony SB-AAAAAAAA')
        assert 'oznaczony jako naprawiony' in actor.messages[-1]
        await actor.admin_command('log podglad')
        assert 'Do wyczyszczenia: 1' in actor.messages[-1]
        await actor.admin_command('log wyczysc naprawione')
        assert db.conn.execute('SELECT COUNT(*) FROM admin_errors_v1224').fetchone()[0] == 2
        await actor.admin_command('log wyczysc naprawione POTWIERDZAM')
        assert 'wyczyszczono 1' in actor.messages[-1]
        assert db.conn.execute("SELECT id FROM admin_errors_v1224").fetchone()[0] == 'SB-BBBBBBBB'
        assert db.conn.execute("SELECT COUNT(*) FROM admin_actions_v1224 WHERE action='errors_purge_fixed'").fetchone()[0] == 1
        await actor.admin_command('log aktywne')
        assert any('SB-BBBBBBBB' in message for message in actor.messages)
        return 9

    ADMIN_ACCOUNT_NAMES.add('admincleanupv1371')
    try:
        checks = asyncio.run(check_commands())
    finally:
        ADMIN_ACCOUNT_NAMES.discard('admincleanupv1371')
        raw.close()
    return {'checks': checks, 'errors': 0}
