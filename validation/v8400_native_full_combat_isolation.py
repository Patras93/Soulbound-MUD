# -*- coding: utf-8 -*-
"""Release gate for full source-runtime isolation (not merely a model arena).

Validates a private, transactionally consistent SQLite clone and protected
working-directory copy. A separate TCP smoke test must still boot server.py.
"""
from __future__ import annotations
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
from arena_real_izolowana import _ignore, _private_env, make_clone


def run():
    passed = 0
    def check(ok, meaning):
        nonlocal passed
        if not ok:
            raise AssertionError(meaning)
        passed += 1
    with tempfile.TemporaryDirectory(prefix='uoss-native-isolation-') as tmp:
        base=Path(tmp)
        source=base/'production'
        source.mkdir()
        (source/'VERSION').write_text('83.00.0',encoding='utf-8')
        (source/'server.py').write_text('print("real runtime")',encoding='utf-8')
        (source/'CHANGELOG_PL.txt').write_text('game changelog',encoding='utf-8')
        (source/'secret.pem').write_text('must not copy',encoding='utf-8')
        (source/'.env').write_text('secrets',encoding='utf-8')
        (source/'.env.production').write_text('even more secrets',encoding='utf-8')
        (source/'logs').mkdir()
        (source/'logs'/'bledy.log').write_text('from real server',encoding='utf-8')
        (source/'LIVE_CONTENT').mkdir()
        (source/'LIVE_CONTENT'/'quest.json').write_text('{}',encoding='utf-8')
        (source/'sub').mkdir()
        (source/'sub'/'module.py').write_text('answer=42',encoding='utf-8')
        (source/'soulbound_world_seed.txt').write_text('seed',encoding='utf-8')
        original=source/'soulbound.db'
        db=sqlite3.connect(original)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE accounts (name TEXT PRIMARY KEY, gold INT)')
            db.execute('INSERT INTO accounts VALUES ("captain", 101)')
            db.commit()
            db.execute('INSERT INTO accounts VALUES ("uncommitted", 999)')
            target=base/'temporary_clone'
            copied=make_clone(source,target)
            check(copied,'Source database must be cloned')
            check((target/'server.py').is_file(),'Native server executable copied')
            check((target/'sub'/'module.py').is_file(),'Real modules copied')
            check((target/'LIVE_CONTENT'/'quest.json').is_file(),'OLC live content copied')
            check((target/'soulbound_world_seed.txt').read_text()=='seed','World seed preserved')
            for forbidden in ('.env','.env.production','secret.pem','logs','soulbound.db-wal','soulbound.db-shm'):
                check(not (target/forbidden).exists(),'No secret/WAL/log: '+forbidden)
            replica=sqlite3.connect(target/'soulbound.db')
            try:
                rows=replica.execute('SELECT name,gold FROM accounts').fetchall()
                check(rows==[('captain',101)],'WAL backup keeps committed but not uncommitted data')
                replica.execute('UPDATE accounts SET gold=999999 WHERE name="captain"')
                replica.commit()
            finally:replica.close()
            check(db.execute('SELECT gold FROM accounts WHERE name="captain"').fetchone()[0]==101,
                  'Clone gameplay never changes original balance')
            check(db.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]==2,
                  'Live uncommitted transaction stays in source')
            check((source/'secret.pem').read_text()=='must not copy','Source secrets untouched')
            for key in ('SOULBOUND_DB','SOULBOUND_API_SECRET','SMTP_PASSWORD','DATABASE_URL',
                        'RAILWAY_TCP_APPLICATION_PORT','PORT','AWS_ACCESS_KEY_ID','OPENAI_API_KEY',
                        'GITHUB_TOKEN','AZURE_CLIENT_SECRET','GOOGLE_APPLICATION_CREDENTIALS',
                        'MY_PRIVATE_KEY','MY_SERVICE_PASSWORD'):
                with patch.dict(os.environ,{key:'private-prod-credential'}):
                    env=_private_env(target,4900)
                    check(env.get(key)!='private-prod-credential','Environment scrub '+key)
            with patch.dict(os.environ, {'SOULBOUND_ADMIN_ACCOUNTS':'OwnerAdmin'}):
                admin_env=_private_env(target,4900)
                check(admin_env['SOULBOUND_ADMIN_ACCOUNTS']=='OwnerAdmin',
                      'Admin privileges preserved for copied private accounts')
            env=_private_env(target,4900)
            check(env['SOULBOUND_PORT']=='4900','Test port different from production')
            check(env['SOULBOUND_HOST']=='127.0.0.1','Only loopback exposure')
            check(env['SOULBOUND_DB']==str(target/'soulbound.db'),'Child database path private')
            check(env['SOULBOUND_WORLD_SEED_FILE']==str(target/'soulbound_world_seed.txt'),
                  'Child seed file private')
            check(not (target/'soulbound.db').is_symlink(),'No database symlink')
            try:
                make_clone(source,source)
            except ValueError:passed+=1
            else:raise AssertionError('Clone cannot overwrite source')
            # Recursive target under source must fail before copytree starts.
            nested = source/'sub'/'deep'/'target'
            try:
                make_clone(source,nested)
            except ValueError:passed+=1
            else:raise AssertionError('Recursive clone target must be rejected')
            check(not nested.exists(), 'Recursive clone must not create partial target')
            # --fresh must NEVER copy a readable existing source database.
            fresh_target = base/'empty_private'
            check(not make_clone(source,fresh_target,fresh=True),
                  'Fresh mode must ignore a present production database')
            check(not (fresh_target/'soulbound.db').exists(),
                  'Fresh mode creates no copied database')
            try:
                make_clone(source,base/'invalid_dual',database=original,fresh=True)
            except ValueError:passed+=1
            else:raise AssertionError('Mutually exclusive fresh/database ignored')
            check(not (base/'invalid_dual').exists(),
                  'Invalid dual mode creates no target directory')
        finally:
            db.rollback(); db.close()
    print(f'UOSS NATIVE ISOLATION: {passed} PASS',flush=True)
    return passed


if __name__=='__main__':
    run()
