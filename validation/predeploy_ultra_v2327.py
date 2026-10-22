# -*- coding: utf-8 -*-
"""ULTRA release gates, always in an isolated candidate tree. No live DB writes.
Each case is one independently fail-closed predeployment stage; stdlib only.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import closing
import os
from pathlib import Path
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def verify_report(name, result):
    if not isinstance(result, dict):
        raise AssertionError(name + ': regression did not return report')
    errors = result.get('errors', result.get('failures', []))
    if errors or int(result.get('error_count', 0)):
        raise AssertionError(name + ': '+str(errors)[:1800])
    if not int(result.get('checks', 0)):
        raise AssertionError(name + ': no assertions run')
    print(name+': '+str(result['checks'])+' real checks PASS', flush=True)


def case_regression(n):
    if n == 10:
        from validation.class_balance_v1172 import audit_class_skill_balance_v1172
        verify_report('14 classes and skill rules', audit_class_skill_balance_v1172())
    elif n == 11:
        from validation.race_balance_v1177 import audit_race_balance_v1177
        verify_report('14 races x classes', audit_race_balance_v1177())
    elif n == 12:
        from validation.profession_balance_v1176 import audit_profession_balance_v1176
        verify_report('profession rules', audit_profession_balance_v1176())
    elif n == 13:
        from validation.great_world import audit_great_world_v1200
        verify_report('world graph quests events', audit_great_world_v1200())
    elif n == 14:
        from validation.v2325_deep_dungeon_pressure import run_regression
        assert run_regression() >= 40
        print('High terrain and infinite dungeons pressure PASS', flush=True)
    elif n == 15:
        from validation.v2321_ash_matron_spawn import run_static_source_regression
        assert run_static_source_regression() > 0
        print('Boss location/source path PASS; full dynamic spawns covered in prior gates', flush=True)
    elif n == 16:
        from validation.mercenary_full_power_v12213 import validate_mercenary_full_power_v12213
        assert validate_mercenary_full_power_v12213() > 0
        print('Mercenary scaling and real damage PASS', flush=True)
    elif n == 17:
        from validation.gold_prices_v1227 import validate_gold_prices_v1227
        assert validate_gold_prices_v1227() > 0
        print('Economic pricing source rules PASS', flush=True)
    elif n == 18:
        import unittest
        from validation import regression_economy4_v1360 as suite
        loaded = unittest.defaultTestLoader.loadTestsFromModule(suite)
        if loaded.countTestCases() < 3:
            raise AssertionError('Insufficient economy tests')
        result = unittest.TextTestRunner(verbosity=1).run(loaded)
        if not result.wasSuccessful():
            raise AssertionError('Economic regression failed')
        print('Economic transaction regression PASS', flush=True)
    elif n == 19:
        from validation.v2006_region_balance import run_regression
        assert run_regression() > 0
        print('Regional progression and difficulty PASS', flush=True)
    elif n == 20:
        import server  # Fully assemble catalogs before querying content_registry
        from validation.v2103_fame_exploration_quest_currency import run_regression
        verify_report('quest EXP fame currency', run_regression())
    elif n == 21:
        from validation.v1706_windows_no_locks import run_regression
        assert run_regression() > 0
        print('Windows unlock and clean restart regression PASS', flush=True)
    else:
        raise ValueError('Not a regression case: '+str(n))


def case_backup():
    import soulbound_backup_windows as backup
    with tempfile.TemporaryDirectory(prefix='sb-ultra-backup-') as td:
        root=Path(td)
        src=root/'game.db'
        db=sqlite3.connect(src)
        try:
            assert db.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower()=='wal'
            db.execute('CREATE TABLE progress (id INTEGER PRIMARY KEY, xp INTEGER NOT NULL)')
            db.execute('INSERT INTO progress VALUES (1,1000)')
            db.commit()
            # Prove the snapshot reads the latest committed WAL while a writer is open.
            with mock.patch.dict(os.environ, {'SOULBOUND_DB':str(src),
                      'SOULBOUND_BACKUP_DIR':str(root/'backups')}), mock.patch.object(backup,'ROOT',root):
                first=backup.create_backup('manual')
                assert first.is_file()
                with closing(sqlite3.connect(first)) as snap:
                    assert snap.execute('SELECT xp FROM progress WHERE id=1').fetchone()[0]==1000
                    assert snap.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                # A failed backup must not erase the previous copy.
                with mock.patch.dict(os.environ, {'SOULBOUND_DB':str(root/'not_found.db')}):
                    try:
                        backup.create_backup('manual')
                    except FileNotFoundError:  # AUDIT_INTENTIONAL_PASS: failure expected; preserve previous snapshot
                        pass
                    else:
                        raise AssertionError('Missing DB was accepted')
                assert first.is_file()
                db.execute('UPDATE progress SET xp=1500 WHERE id=1')
                db.commit()
                second=backup.create_backup('manual')
                assert first!=second
                with closing(sqlite3.connect(second)) as snap:
                    assert snap.execute('SELECT xp FROM progress WHERE id=1').fetchone()[0]==1500
                    assert snap.execute('PRAGMA journal_mode').fetchone()[0].lower()=='delete'
                with closing(sqlite3.connect(first)) as snap:
                    assert snap.execute('SELECT xp FROM progress WHERE id=1').fetchone()[0]==1000
        finally:
            db.close()
    print('SQLite WAL online backup, restore, failure and snapshots PASS', flush=True)


def case_watchdog():
    import supervisor_windows as watchdog
    with tempfile.TemporaryDirectory(prefix='sb-ultra-watchdog-') as td:
        root=Path(td)
        now=[0.0]
        pauses=[]
        attempts=[]
        def fake_clock():
            return now[0]
        def fake_sleep(t):
            pauses.append(t)
            now[0]+=t
        def fake_server():
            attempts.append(True)
            return 1
        with (mock.patch.object(watchdog,'ROOT',root),
              mock.patch.object(watchdog,'LOGS',root/'logs'),
              mock.patch.object(watchdog,'STATE',root/'logs'/'supervisor.json'),
              mock.patch.object(watchdog,'REQUEST',root/'logs'/'stop.json'),
              mock.patch.object(watchdog,'LOG',root/'logs'/'watchdog.log'),
              mock.patch.object(watchdog,'mutex_handle',return_value=None),
              mock.patch.object(watchdog,'process_alive',return_value=False)):
            watchdog.supervise(run_server_fn=fake_server, pause_fn=fake_sleep,
                               now_fn=fake_clock, max_cycles=3)
            assert len(attempts)==3, ('no restart after crash',len(attempts))
            assert sum(pauses) >= 15, ('no exponential backoff',sum(pauses))
            assert not watchdog.STATE.exists()
            call_count=[0]
            def asked_stop():
                call_count[0]+=1
                live=watchdog.read_json(watchdog.STATE)
                watchdog.atomic_json(watchdog.REQUEST,{'run_id':live['run_id']})
                return 0
            watchdog.supervise(run_server_fn=asked_stop, pause_fn=fake_sleep,
                               now_fn=fake_clock, max_cycles=5)
            assert call_count[0]==1 and not watchdog.STATE.exists() and not watchdog.REQUEST.exists()
    print('Watchdog: crash retry with backoff + STOP without restart PASS', flush=True)


def available_port():
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def stop_child(proc):
    """Stop the exact disposable child and wait before deleting TEMP files.

    Windows taskkill /T can itself hang for >12 seconds even when a TCP test
    has already succeeded, leaving server.log locked. Terminate the Popen
    child directly instead of relying on taskkill /T.
    Never swallow a failure to stop the process.
    """
    if proc.poll() is not None:
        proc.wait()
        return
    if os.name == 'nt':
        proc.terminate()
    else:
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        # Force the tracked child down, and close inherited file handles.
        proc.kill()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f'Test server PID {proc.pid} did not stop; TEMP files may remain locked') from exc


def case_twenty_tcp():
    """5 simultaneous banner connections on disposable local server; no fake logins."""
    with tempfile.TemporaryDirectory(prefix='sb-ultra-5-tcp-') as td:
        root=Path(td)
        port=available_port()
        env=os.environ.copy()
        for key in list(env):
            if key.startswith('RAILWAY_') or key.startswith('SOULBOUND_') or key in ('PORT','DATABASE_URL'):
                env.pop(key,None)
        env.update(SOULBOUND_DB=str(root/'stress.db'), SOULBOUND_HOST='127.0.0.1',
            SOULBOUND_PORT=str(port),SOULBOUND_MAX_CLIENTS='5',
            SOULBOUND_WORLD_SEED_FILE=str(root/'stress.seed'),
            PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',PYTHONUTF8='1')
        flags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0
        logfile=root/'server.log'
        with logfile.open('wb') as out:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'server.py')],
               env=env,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,
               creationflags=flags,start_new_session=os.name!='nt',stdin=subprocess.DEVNULL)
            try:
                deadline=time.monotonic()+150
                while time.monotonic()<deadline:
                    if proc.poll() is not None:
                        raise RuntimeError('Private server died: '+logfile.read_text(encoding='utf-8',errors='replace')[-1400:])
                    if 'World Core nasłuchuje:' in logfile.read_text(encoding='utf-8', errors='replace'):
                        break
                    time.sleep(.2)
                else:
                    raise TimeoutError('Private TCP server did not start')
                async def probe(n):
                    reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',port),15)
                    try:
                        data=await asyncio.wait_for(reader.readuntil('Wybierz opcję: '.encode('utf-8')),40)
                        await asyncio.sleep(.4)
                        return bool(data) and b'Wybierz opcj' in data
                    finally:
                        writer.close()
                        await writer.wait_closed()
                async def wave():
                    return await asyncio.gather(*(probe(i) for i in range(5)))
                successes=asyncio.run(wave())
                assert len(successes)==5 and all(successes),('banner failures',successes)
                print('5 concurrent REAL localhost TCP banner sessions PASS; not 5 full player logins/combat',flush=True)
            finally:
                stop_child(proc)


def case_migrate():
    source=os.getenv('SOULBOUND_ULTRA_SOURCE_DB','').strip()
    if not source:
        raise RuntimeError('Real SQLite clone required for ULTRA: SOULBOUND_ULTRA_SOURCE_DB missing')
    path=Path(source).resolve()
    if not path.is_file() or path.stat().st_size<1024:
        raise FileNotFoundError('ULTRA real production snapshot source not found: '+str(path))
    with tempfile.TemporaryDirectory(prefix='sb-ultra-sqlite-migrate-') as td:
        staged=Path(td)/'candidate.db'
        url=path.as_uri()+'?mode=ro'  # Windows drive-safe file:///C:/... URI
        src=sqlite3.connect(url,uri=True,timeout=30)
        try:
            src.execute('PRAGMA query_only=ON')
            before={row[0] for row in src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            before_columns={t:{r[1] for r in src.execute('PRAGMA table_info("'+t.replace('"','""')+'")')} for t in before}
            dst=sqlite3.connect(staged)
            try:
                src.backup(dst,pages=256,sleep=.15)
            finally:
                dst.close()
        finally:
            src.close()
        with closing(sqlite3.connect(staged)) as c:
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert not c.execute('PRAGMA foreign_key_check').fetchone(), 'Pre-existing foreign key issue in source backup'
        os.environ['SOULBOUND_DB']=str(staged)
        os.environ['SOULBOUND_HOST']='127.0.0.1'
        os.environ['SOULBOUND_WORLD_SEED_FILE']=str(Path(td)/'migration_seed.txt')
        import server  # Runtime-assembled catalog required by migration
        from storage.database import Database
        db=Database(str(staged))
        try:
            after={row[0] for row in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            assert before <= after, ('Candidate dropped tables',sorted(before-after))
            for t,cols in before_columns.items():
                after_cols={r[1] for r in db.conn.execute('PRAGMA table_info("'+t.replace('"','""')+'")')}
                assert cols <= after_cols, ('Candidate removed table fields',t,sorted(cols-after_cols))
            assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert not db.conn.execute('PRAGMA foreign_key_check').fetchone()
            account_tables=[t for t in before if 'account' in t.lower()]
            print('Production SQLite read-only backup -> candidate schema check: '
                  f'{len(before)} original tables, {len(after)} updated tables, '
                  f'{len(account_tables)} account-related tables; no destructive schema change',flush=True)
        finally:
            db.conn.close()
    print('Source DB never written by test; candidate DB destroyed with temporary workspace',flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--case',type=int,required=True)
    n=ap.parse_args().case
    if 10 <= n <= 21:
        case_regression(n)
    elif n==22:
        case_backup()
    elif n==23:
        case_watchdog()
    elif n==24:
        case_twenty_tcp()
    elif n==25:
        case_migrate()
    else:
        raise SystemExit('Unknown ULTRA gate: '+str(n))
    print(f'ULTRA GATE {n:02d}/25 PASS',flush=True)


if __name__=='__main__':
    main()
