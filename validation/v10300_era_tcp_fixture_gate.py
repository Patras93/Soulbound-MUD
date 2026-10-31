# -*- coding: utf-8 -*-
"""ETAP 7: fast regression for a genuine, fully linked account fixture.

The real TCP test is separate and optional; this one must fail if the setup
creates a legacy character without an account_characters linkage.
No real user accounts or database files are read or modified.
"""
from __future__ import annotations

from pathlib import Path
import tempfile


def run():
    from storage.database import Database
    from core.classes_skills import CLASSES, RACES
    from validation.v2102_tcp_six_players import guarded_child_env
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb103-era-tcp-fixture-') as td:
        env, dbpath = guarded_child_env(td, 45811)
        assert Path(env['SOULBOUND_DB']).resolve() == dbpath.resolve();checks += 1
        assert env['SOULBOUND_TCP_TEST_CHILD'] == '1';checks += 1
        assert env['SOULBOUND_HOST'] == '127.0.0.1';checks += 1
        assert env['SOULBOUND_PORT'] == '45811';checks += 1
        for forbidden in ('DATABASE_URL', 'RAILWAY_VOLUME_MOUNT_PATH',
                          'SOULBOUND_ADMIN_ACCOUNTS', 'RAILWAY_TCP_APPLICATION_PORT'):
            assert forbidden not in env, forbidden
            checks += 1
        db = Database(str(dbpath))
        for account_name, char_name in [('era103tcpone', 'Era103One'),
                                        ('era103tcptwo', 'Era103Two')]:
            aid = db.create_account(account_name, 'test_only_tcp_2026_password')
            assert db.account_by_name(account_name)['id'] == aid; checks += 1
            character_id, slot = db.create_character_for_master(
                aid, char_name, RACES[0], CLASSES[0],
                {k: char_name for k in ('nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc')})
            assert slot == 1; checks += 1
            entries = db.characters_for_master(aid)
            assert len(entries) == 1, (account_name, 'no selectable character')
            checks += 1
            assert entries[0]['name'] == char_name; checks += 1
            assert entries[0]['character_account_id'] == character_id; checks += 1
            assert db.character_for_account(character_id)['name'] == char_name; checks += 1
            assert not db.is_character_profile(aid); checks += 1
        db.conn.commit()
        db.conn.close()
        db2 = Database(str(dbpath))
        for account_name in ('era103tcpone', 'era103tcptwo'):
            account = db2.account_by_name(account_name)
            assert account is not None; checks += 1
            assert len(db2.characters_for_master(int(account['id']))) == 1; checks += 1
        db2.conn.close()
        assert checks == 26, checks
    assert not dbpath.exists(), 'Disposable SQLite leaked'
    return checks + 1


if __name__ == '__main__':
    print(f'ERA 103 TCP FIXTURE: {run()} checks PASS', flush=True)
