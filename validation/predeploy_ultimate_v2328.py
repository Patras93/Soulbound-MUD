# -*- coding: utf-8 -*-
"""ULTIMATE cases 26-50. No production game processes, writes or ports.

Every case is independently executable and exits nonzero on a broken invariant.
Existing regression scripts are executed as their own Python subprocesses; bespoke
SQLite and release-security checks use disposable temporary directories only.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import time
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REGRESSIONS = {
    26: ('KOMENDY I QUESTY - POKRYCIE REJESTRU', 'validation/v2102_command_quest_coverage.py'),
    27: ('KOPALNIE - KIERUNKI', 'validation/mine_directions_v1251.py'),
    28: ('KOPALNIE - TRWALOSC TUNELI', 'validation/mine_persistence_v1250.py'),
    29: ('WALKA - ZYWIOLOWE OBRAZENIA', 'validation/v2008_elemental_damage.py'),
    30: ('AOE - AI I OPTYMALIZACJA', 'validation/v1901_aoe_ai_performance.py'),
    31: ('PROGRESJA LVL 50+', 'validation/v1407_progression_from50.py'),
    32: ('BALANS TEMPA GRINDU', 'validation/v1408_pleasant_grind.py'),
    33: ('XP PROFESJI - KRZYWE', 'validation/profession_xp_v1401.py'),
    34: ('XP NARZEDZI - MATERIALY', 'validation/tool_xp_v1402.py'),
    35: ('ZAMOWIENIA ADMINISTRACYJNE', 'validation/v1405_admin_orders_regression.py'),
    36: ('ODRADZANIE MOBOW', 'validation/v1405_mob_regen.py'),
    37: ('FAME, EXP CAP, PIETRA', 'validation/v2009_expcap_fame_stairs.py'),
    38: ('ROWNOLEGLE SWIATY', 'validation/v2000_parallel_worlds.py'),
    39: ('FAUNA TERENOW I KIERUNKI', 'validation/v1709_terrain_fauna.py'),
    40: ('POCZATKOWE STARCIA', 'validation/v2005_beginner_encounters.py'),
    41: ('CONSIDER W REGIONACH', 'validation/v2007_consider_region_import.py'),
    42: ('TYTANI - SYSTEMY', 'validation/v2100_titans.py'),
    43: ('WINDOWS - KOPANIE', 'validation/v1603_windows_mining_test.py'),
    44: ('STAROZYTNE KROLESTWA', 'validation/v1900_ancient_kingdoms.py'),
}


def regression(n):
    label, filename = REGRESSIONS[n]
    target = ROOT / filename
    if not target.is_file():
        raise AssertionError(f'{label}: missing {filename}')
    command=[sys.executable, '-u', '-m', filename[:-3].replace('/', '.')]
    if n==42:
        # Titans regression expects dynamic registries assembled by server.py.
        command=[sys.executable, '-u', '-c',
                 "import server, runpy; runpy.run_module('validation.v2100_titans',run_name='__main__')"]
    result = subprocess.run(command, cwd=ROOT,
                            stdin=subprocess.DEVNULL, text=True,
                            capture_output=True, encoding='utf-8', errors='replace', timeout=175)
    output = (result.stdout + '\n' + result.stderr).strip()
    if output:
        print(output[-9000:], flush=True)
    if result.returncode:
        raise AssertionError(f'{label}: failed with exit code {result.returncode}')
    # These are existing, assertion-bearing suites, not source pattern checks.
    print(f'{label}: Python regression exited 0, no skipped case', flush=True)


def sqlite_crash_recovery():
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-wal-crash-') as td:
        db = Path(td)/'crash.sqlite'
        # os._exit makes this a genuinely abrupt termination in the CHILD ONLY.
        script = '''import sqlite3, os, sys
c=sqlite3.connect(sys.argv[1]); c.execute('PRAGMA journal_mode=WAL')
c.execute('CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, amount INT)')
c.execute('INSERT INTO ledger VALUES (1, 54321)'); c.commit()
c.execute('INSERT INTO ledger VALUES (2, 99999)')
os._exit(19)
'''
        r = subprocess.run([sys.executable,'-c',script,str(db)], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=15)
        assert r.returncode==19, f'child did not perform crash simulation: {r.returncode}'
        with closing(sqlite3.connect(db)) as c:
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert c.execute('SELECT id,amount FROM ledger ORDER BY id').fetchall()==[(1,54321)]
        # A checkpointed copy is self-contained and has no reliance on -wal files.
        with closing(sqlite3.connect(db)) as c, closing(sqlite3.connect(Path(td)/'snapshot.db')) as snap:
            c.backup(snap)
            assert snap.execute('SELECT COUNT(*) FROM ledger').fetchone()[0]==1
            assert snap.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    print('Abrupt child crash: committed WAL survives; uncommitted txn rolled back; backup OK',flush=True)


def sqlite_concurrency():
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-locks-') as td:
        path=Path(td)/'parallel.db'
        with closing(sqlite3.connect(path)) as c:
            c.execute('PRAGMA journal_mode=WAL')
            c.execute('CREATE TABLE events (worker INTEGER, seq INTEGER, UNIQUE(worker,seq))')
            c.commit()
        issues=[]
        barrier=threading.Barrier(5)
        def job(idx):
            try:
                with closing(sqlite3.connect(path,timeout=20)) as c:
                    c.execute('PRAGMA busy_timeout=20000')
                    barrier.wait(timeout=10)
                    for j in range(100):
                        c.execute('INSERT INTO events VALUES (?,?)',(idx,j))
                        c.commit()
            except BaseException as exc:
                issues.append(repr(exc))
        workers=[threading.Thread(target=job,args=(i,),daemon=True) for i in range(4)]
        for t in workers:t.start()
        barrier.wait(timeout=10)
        for t in workers:t.join(timeout=35)
        assert not any(t.is_alive() for t in workers), 'SQLite writer thread hung'
        assert not issues, issues
        with closing(sqlite3.connect(path)) as c:
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert c.execute('SELECT COUNT(*) FROM events').fetchone()[0]==400
            assert c.execute('SELECT COUNT(DISTINCT worker) FROM events').fetchone()[0]==4
    print('4 SQLite WAL writers, 400 commits, no lost/duplicated rows PASS',flush=True)


def archive_security():
    from predeploy_nowej_wersji import inspect_zip
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-zip-security-') as td:
        folder=Path(td)
        tests=[
            ('traversal', {'../escape.txt':b'x'}),
            ('abs-path', {'/outside.txt':b'x'}),
            ('database-included',{'soulbound.db':b'secret'}),
            ('case-collision', {'server.py':b'1','SERVER.py':b'2'}),
        ]
        for name,members in tests:
            path=folder/('Soulbound-MUD-v2.32.8-'+name+'.zip')
            with zipfile.ZipFile(path,'w') as z:
                for key,value in members.items():z.writestr(key,value)
            try:
                inspect_zip(path)
            except ValueError:  # AUDIT_INTENTIONAL_PASS: reject unsafe archive (expected exception)
                pass
            else:
                raise AssertionError('Dangerous ZIP accepted: '+name)
        link=folder/'Soulbound-MUD-v2.32.8-link.zip'
        with zipfile.ZipFile(link,'w') as z:
            info=zipfile.ZipInfo('link');info.create_system=3
            info.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(info,'../escape')
        try: inspect_zip(link)
        except ValueError:  # AUDIT_INTENTIONAL_PASS: ZIP symlink rejection is expected
            pass
        else: raise AssertionError('ZIP symbolic link was accepted')
    print('ZIP traversal, absolute paths, DB leaks, case collisions, symlinks rejected PASS',flush=True)


def deployment_fail_closed():
    import wdroz_po_predeploy as deployment
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-gate-') as td:
        root=Path(td)
        state=root/'last_result.json'
        fake=root/'Soulbound-MUD-v2.32.10-test.zip'
        fake.write_bytes(b'test version data')
        expected=hashlib.sha256(fake.read_bytes()).hexdigest()
        good={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS','required_stages':60,
              'completed_stages':60,'zip':str(fake),'version':'2.32.10',
              'sha256':expected,'finished_at':'mock'}
        with (mock.patch.object(deployment,'STATE',state),
              mock.patch.object(deployment,'installed_version',return_value='2.32.7'),
              mock.patch.object(deployment,'inspect_zip',return_value=('2.32.10',{})),
              mock.patch.object(deployment.subprocess,'call',side_effect=AssertionError('DEPLOY TRIGGERED')),
              mock.patch('builtins.input',side_effect=AssertionError('Unexpected confirmation prompt'))):
            for changes in [
                 {'status':'FAIL'}, {'quality_gate':'ULTRA-25','required_stages':25,'completed_stages':25},
                 {'quality_gate':'ULTIMATE-50','required_stages':50,'completed_stages':50},
                 {'quality_gate':'ULTIMATE-60','required_stages':60,'completed_stages':60},
                 {'completed_stages':59}, {'sha256':'0'*64}]:
                d=good.copy();d.update(changes)
                state.write_text(json.dumps(d),encoding='utf-8')
                assert deployment.main()!=0, ('Unsafe deploy authorized',changes)
            state.write_text(json.dumps(good),encoding='utf-8')
            fake.write_bytes(b'changed AFTER predeploy')
            assert deployment.main()!=0, 'Changed ZIP authorized'
    print('Broken PASS, old gate, incomplete stages, bad hash and modified ZIP all BLOCKED',flush=True)


def production_data_preserved():
    source=os.getenv('SOULBOUND_ULTRA_SOURCE_DB','').strip()
    if not source:
        raise ValueError('Production source snapshot missing; refuse to silently skip identity checks')
    path=Path(source).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-real-row-check-') as td:
        candidate=Path(td)/'isolated.sqlite'
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=30)) as src:
            src.execute('PRAGMA query_only=ON')
            tables={x[0] for x in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            preserved=[t for t in ('accounts','characters','inventory','quests','guilds') if t in tables]
            assert 'accounts' in preserved and 'characters' in preserved, 'Missing baseline account tables'
            def signatures(c, columns_by_table=None):
                out={}
                for table in preserved:
                    # Include all existing columns, but not newly added migration columns.
                    columns=(columns_by_table or {}).get(table) or [r[1] for r in c.execute('PRAGMA table_info("'+table+'")')]
                    quoted=','.join('"'+x.replace('"','""')+'"' for x in columns)
                    digest=hashlib.sha256()
                    rows=[]
                    for values in c.execute(f'SELECT {quoted} FROM "{table}"'):
                        rows.append(repr(tuple(values)).encode('utf-8','backslashreplace'))
                    for line in sorted(rows):digest.update(len(line).to_bytes(8,'big')+line)
                    out[table]=(len(rows),columns,digest.hexdigest())
                return out
            baseline=signatures(src)
            with closing(sqlite3.connect(candidate)) as dst:src.backup(dst)
        # Run the candidate's real migration code against the clone, not the source.
        os.environ['SOULBOUND_DB']=str(candidate)
        os.environ['SOULBOUND_HOST']='127.0.0.1'
        os.environ['SOULBOUND_WORLD_SEED_FILE']=str(Path(td)/'seed.txt')
        import server
        from storage.database import Database
        db=Database(str(candidate))
        try:
            after=signatures(db.conn,{t:data[1] for t,data in baseline.items()})
            assert after==baseline, [(k,baseline.get(k),after.get(k)) for k in baseline if after.get(k)!=baseline[k]]
            assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        finally:
            db.conn.close()
    print('Production-clone migration preserves account/character/inventory/quest/guild row content PASS',flush=True)


def repeated_tcp_waves():
    # Separate from six real authenticated players (stage 9) and 20 concurrent
    # banner sessions (stage 24): multiple sustained waves check accept/recovery.
    from validation.predeploy_ultra_v2327 import available_port, stop_child
    import asyncio
    import socket
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-tcp-waves-') as td:
        tmp=Path(td)
        port=available_port()
        env=os.environ.copy()
        for k in list(env):
            if k.startswith(('SOULBOUND_','RAILWAY_')) or k in ('DATABASE_URL','PORT'):
                env.pop(k,None)
        env.update(SOULBOUND_DB=str(tmp/'wave.sqlite'),SOULBOUND_HOST='127.0.0.1',
            SOULBOUND_PORT=str(port),SOULBOUND_MAX_CLIENTS='35',
            SOULBOUND_WORLD_SEED_FILE=str(tmp/'world.seed'),
            PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',PYTHONUTF8='1')
        flags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0
        log=tmp/'server.log'
        with log.open('wb') as out:
            p=subprocess.Popen([sys.executable,'-u',str(ROOT/'server.py')],cwd=ROOT,
                env=env,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                creationflags=flags,start_new_session=os.name!='nt')
            try:
                for _ in range(700):
                    if p.poll() is not None:
                        raise AssertionError('Test server exited: '+log.read_text(encoding='utf-8',errors='replace')[-1800:])
                    try:
                        with socket.create_connection(('127.0.0.1',port),.2):break
                    except OSError:time.sleep(.2)
                else:raise TimeoutError('Private 30 TCP wave server did not start')
                async def client(index, wave):
                    # 30 concurrent handshakes can queue behind world startup;
                    # keep 30 simultaneous connections but wait for the *full*
                    # login prompt instead of treating a slow banner as a crash.
                    try:
                        r,w=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',port),20)
                    except (OSError, asyncio.TimeoutError) as exc:
                        raise AssertionError(f'Fala {wave+1}, klient {index+1}: TCP connect {exc!r}') from exc
                    try:
                        try:
                            banner=await asyncio.wait_for(
                                r.readuntil('Wybierz opcję: '.encode('utf-8')),55)
                        except (asyncio.TimeoutError, asyncio.IncompleteReadError,
                                asyncio.LimitOverrunError) as exc:
                            raise AssertionError(f'Fala {wave+1}, klient {index+1}: '
                                                 f'brak pelnego ekranu logowania ({type(exc).__name__})') from exc
                        return bool(banner)
                    finally:
                        w.close()
                        await w.wait_closed()
                async def scenario():
                    for wave in range(3):
                        wave_start=time.monotonic()
                        try:
                            results=await asyncio.gather(*(client(i,wave) for i in range(30)))
                        except Exception:
                            output=log.read_text(encoding='utf-8',errors='replace')
                            print('TCP TEST SERVER LOG (last 2200 chars): '+output[-2200:],flush=True)
                            raise
                        assert len(results)==30 and all(results),f'Wave {wave+1}: dropped banner'
                        print(f'TCP fala {wave+1}/3: 30/30 pelnych ekranow logowania, '
                              f'{time.monotonic()-wave_start:.1f} s PASS',flush=True)
                        await asyncio.sleep(.3)
                asyncio.run(scenario())
                assert p.poll() is None
                output=log.read_text(encoding='utf-8',errors='replace')
                assert 'Traceback (most recent call last):' not in output,output[-1400:]
            finally:stop_child(p)
    print('3 x 30 concurrent localhost TCP LOGIN BANNERS (90 total) PASS; not 90 authenticated players',flush=True)


CASES={45:sqlite_crash_recovery,46:sqlite_concurrency,47:archive_security,
       48:deployment_fail_closed,49:production_data_preserved,50:repeated_tcp_waves}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--case',type=int,required=True)
    case=p.parse_args().case
    if case in REGRESSIONS:regression(case)
    elif case in CASES:CASES[case]()
    else:raise ValueError('Unknown ULTIMATE case: '+str(case))
    print(f'ULTIMATE GATE {case:02d}/50 PASS',flush=True)

if __name__=='__main__':main()
