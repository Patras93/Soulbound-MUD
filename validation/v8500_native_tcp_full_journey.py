# -*- coding: utf-8 -*-
"""Real TCP -> real character -> real mob kill -> SQLite isolation -> cleanup.

Creates only disposable synthetic accounts and characters in a disposable source.
Never uses the operator's production DB or an existing TCP listener.
Fails closed on missing quest progress, incomplete responses, leaked data or orphan lab.
"""
from __future__ import annotations
import asyncio
from contextlib import closing
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

from arena_real_izolowana import _ignore

ROOT = Path(__file__).resolve().parents[1]
USER = 'isouosstest'
NAME = 'Isouosstest'
PASS = 'test_only_tcp_2026_password'
QUEST = 'temple_rats'


def _port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        candidate = s.getsockname()[1]
    if candidate == 4000:
        return _port()
    return candidate


def _progress(path):
    with closing(sqlite3.connect(str(path), timeout=8)) as db:
        db.row_factory = sqlite3.Row
        assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
        rows = db.execute('''SELECT q.status,q.progress FROM quests q
            JOIN accounts a ON q.account_id=a.id WHERE a.username=? AND q.quest_id=?''',
            (USER,QUEST)).fetchall()
        return [(str(r[0]), int(r[1])) for r in rows]


async def _journey(port, logpath):
    from validation.v2102_tcp_six_players import TcpPlayer
    player = TcpPlayer(USER, NAME, port)
    try:
        await player.connect_and_login()
        look = await player.command('look')
        assert 'Kapłan Elor' in look, 'Temple NPC not present'
        offer = await player.command('quest list Kapłan Elor')
        assert 'Szczury pod świątynią' in offer, 'Quest offer missing'
        await player.command('przyjmij 1')
        # Don't trust asynchronous single recv from game; verify with DB later.
        await player.command('down')
        room = await player.command('look')
        assert 'Piwnic' in room and 'Szczur' in room, 'Real rats not present'
        start = await player.command('attack Szczur')
        assert 'Walka' in start or 'Szczur' in start, 'Attack did not start'
        deadline = time.monotonic() + 100
        progress = 0
        while time.monotonic() < deadline:
            await asyncio.sleep(1.4)
            await player.command('quests')
            logfile = logpath.read_text(encoding='utf-8', errors='replace')
            match = re.search(r'(?m)^Baza danych: (.+)$', logfile)
            if match:
                clone_db = Path(match.group(1).strip())
                if clone_db.is_file():
                    entries = _progress(clone_db)
                    if any(status == 'active' and qty > 0 for status, qty in entries):
                        progress = max(qty for status, qty in entries)
                        return clone_db, progress
        raise AssertionError('Real TCP combat did not commit a rat kill to isolated SQLite in 100 seconds')
    finally:
        await player.close()


def _stop(proc):
    if proc is None:
        return
    if proc.poll() is None:
        if os.name == 'nt':
            # Graceful Ctrl+Break is required on Windows; TerminateProcess would
            # skip the private wrapper's finally and leave a child running.
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            proc.terminate()
    try:
        return proc.wait(timeout=35)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)
        raise RuntimeError('Isolated test server refused graceful stop')


def run():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='soulbound-v85-native-tcp-') as tmp:
        base = Path(tmp)
        source = base / 'synthetic_source'
        # DBs, WAL, secrets and logs are all excluded; only game code/content.
        shutil.copytree(ROOT, source, ignore=_ignore)
        assert not (source/'soulbound.db').exists()
        checks += 1
        from storage.database import Database
        from core.classes_skills import CLASSES, RACES
        db = Database(str(source/'soulbound.db'))
        try:
            user_id = db.create_account(USER, PASS)
            cases = {key:NAME for key in ('nom','gen','dat','acc','ins','loc','voc')}
            db.create_character_for_master(user_id, NAME, RACES[0], CLASSES[0], cases)
            db.conn.commit()
        finally:
            db.conn.close()
        source_db = source / 'soulbound.db'
        assert _progress(source_db) == []
        checks += 1
        port = _port()
        logfile = base / 'private_runtime.log'
        child = None
        clone_db = None
        try:
            env = os.environ.copy()
            # Explicitly avoid CI or local launch config changing the wrapper.
            for key in ('PORT','RAILWAY_TCP_APPLICATION_PORT','SOULBOUND_DB'):
                env.pop(key,None)
            kwargs = ({'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP}
                      if os.name == 'nt' else {})
            with logfile.open('w',encoding='utf-8') as sink:
                child = subprocess.Popen([sys.executable,'-u',str(ROOT/'arena_real_izolowana.py'),
                    '--source',str(source),'--database',str(source_db),'--port',str(port)],
                    cwd=source,env=env,stdout=sink,stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,**kwargs)
                deadline=time.monotonic()+155
                while time.monotonic()<deadline:
                    if child.poll() is not None:
                        raise RuntimeError('Isolated launcher exited prematurely: '+logfile.read_text(errors='replace')[-2500:])
                    if 'World Core nasłuchuje:' in logfile.read_text(errors='replace'):
                        break
                    time.sleep(.3)
                else:
                    raise TimeoutError('Native engine did not announce readiness: '+logfile.read_text(errors='replace')[-1600:])
                checks += 1
                clone_db,progress=asyncio.run(_journey(port,logfile))
                assert clone_db.exists(), 'Private DB missing before stop'
                assert source_db.resolve()!=clone_db.resolve(), 'Private DB overlaps source!'
                checks += 1
                entries=_progress(clone_db)
                assert any(q>0 for _,q in entries), 'Kill not committed in SQLite'
                checks += 1
                assert _progress(source_db)==[], 'Source characters/quest state mutated'
                checks += 1
                print(f'FULL TCP WORLD: login + NPC + quest + movement + real kill '
                      f'+ isolated SQLite {progress}/10 PASS', flush=True)
        finally:
            if child is not None:
                _stop(child)
        if clone_db is not None:
            assert not clone_db.parent.parent.exists(), 'Private runtime not deleted on normal shutdown'
            checks += 1
        assert _progress(source_db)==[], 'Source changed even after shutdown'
        checks += 1
        output=logfile.read_text(encoding='utf-8',errors='replace')
        assert 'Kopia testowa zostala usunieta' in output, 'Cleanup not confirmed'
        checks += 1
        assert 'Traceback (most recent call last)' not in output, output[-2000:]
        checks += 1
    print(f'UOSS FULL TCP & ISOLATION: {checks} PASS',flush=True)
    return checks

if __name__ == '__main__':
    run()
