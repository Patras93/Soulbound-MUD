# -*- coding: utf-8 -*-
"""v115 true localhost TCP payout test on disposable accounts and SQLite.

Tests durable award queued before a server restart, ordered delivery on a
new TCP process, and absence of duplicates after another full server restart.
The queued award is a synthetic *test fixture*, not proof of a natural boss fight.
No real player data, production port, GitHub, or soundpack is used.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import closing, suppress

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
from validation.v2102_tcp_six_players import (
    guarded_child_env, free_local_port, wait_for_world_server, _stop_child,
    TcpPlayer, PASSWORD,
)
from systems.v115.fame_reward_snapshot import RewardSnapshot, stage_with_snapshot


async def login(account, name, port):
    player = TcpPlayer(account, name, port)
    player.reader, player.writer = await asyncio.open_connection('127.0.0.1', port)
    await player.until('Wybierz opcję: ')
    await player.send('1')
    await player.until('Nazwa konta: ')
    await player.send(account)
    await player.until('Hasło: ')
    await player.send(PASSWORD)
    await player.until('Wybierz opcję: ')
    await player.send('1')
    await player.until('Postać: ')
    await player.send('1')
    greeting = await player.until('Wpisz help, aby poznać komendy.')
    if name not in greeting:
        raise AssertionError('Nieprawidlowa postac TCP: ' + repr(greeting[-250:]))
    return player


def child_start(td, *, cycle):
    port = free_local_port()
    env, db_path = guarded_child_env(td, port)
    env['SOULBOUND_SOUND_EVENTS'] = '0'
    log = Path(td) / f'cycle-{cycle}.log'
    stream = log.open('w', encoding='utf-8')
    try:
        proc = subprocess.Popen(
            [sys.executable, '-u', str(ROOT / 'validation/v2102_tcp_child.py')],
            cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT)
        try:
            wait_for_world_server(proc, log, seconds=100)
        except BaseException as error:
            _stop_child(proc)
            stream.flush()
            raise RuntimeError('TCP child start failed; log tail: '+
                               log.read_text(encoding='utf-8',errors='replace')[-2200:]) from error
        return proc, stream, log, port, db_path
    except BaseException:
        stream.close()
        raise


def stage_offline_reward(db_path):
    # A completed fight from the past. Keep the normal 60..300s due time;
    # only move the event's origin into the past to avoid sleeping 5 minutes.
    with closing(sqlite3.connect(db_path)) as conn:
        aid = int(conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0])
        name = conn.execute('SELECT name FROM characters WHERE account_id=?', (aid,)).fetchone()[0]
        snapshot = RewardSnapshot(
            character_xp=115, soul_xp=45, class_xp=0, stat_xp=30,
            class_levels=(), class_max_level=800,
            overcap=False, character_name=name,
        )
        with conn:
            created = stage_with_snapshot(
                conn, aid, 'Testowa kraina', 'tcp_first_v115', 'Testowy strażnik',
                snapshot, now=time.time()-500)
            assert created
        row = conn.execute('SELECT status,due_at FROM v115_fame_delivery').fetchone()
        assert row[0] == 'WAITING' and row[1] <= time.time()
        assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name='fame_bosses_v1702'").fetchone()[0] == 0
        return aid


async def collect_ordered_messages(port):
    primary = await login('tcpcheck1','Testtcp1',port)
    other = await login('tcpcheck2','Testtcp2',port)
    try:
        content = ''
        event_times = {}
        until = time.monotonic() + 18
        while len(event_times) < 2 and time.monotonic() < until:
            remaining = until - time.monotonic()
            chunk = await asyncio.wait_for(primary.reader.read(16384), remaining)
            if not chunk:
                raise AssertionError('Zerwano polaczenie TCP podczas wyplaty')
            content += chunk.decode('utf-8', 'replace')
            if 'FAME MOB: zaległy EXP za Testowy strażnik' in content and 'exp' not in event_times:
                event_times['exp'] = time.monotonic()
            if 'FAMA: +1 za Testowy strażnik' in content and 'fame' not in event_times:
                event_times['fame'] = time.monotonic()
        if len(event_times) != 2:
            raise AssertionError('Brak dwóch wiadomosci TCP: ' + repr(content[-1000:]))
        if event_times['fame'] - event_times['exp'] < 1.8:
            raise AssertionError('Fama dotarla za szybko po EXP: '+repr(event_times))
        # Check the other player's private socket after the payout window.
        try:
            unrelated = await asyncio.wait_for(other.reader.read(16384), 0.8)
        except asyncio.TimeoutError:
            unrelated = b''
        if b'FAME MOB:' in unrelated or b'FAMA: +1' in unrelated:
            raise AssertionError('Przeciek nagrody do drugiej postaci')
        return event_times['fame'] - event_times['exp']
    finally:
        await asyncio.gather(primary.close(),other.close())


async def check_relogin_no_duplicate(port):
    player = await login('tcpcheck1','Testtcp1',port)
    try:
        try:
            data = await asyncio.wait_for(player.reader.read(16384), 4.5)
        except asyncio.TimeoutError:
            data = b''
        if b'FAME MOB:' in data or b'FAMA: +1' in data:
            raise AssertionError('Podwojna wyplata po kolejnym logowaniu')
    finally:
        await player.close()


def check_ledger(db_path, aid):
    with closing(sqlite3.connect(db_path)) as conn:
        status = conn.execute('SELECT status FROM v115_fame_delivery WHERE account_id=?', (aid,)).fetchone()[0]
        fame = conn.execute('SELECT count(*) FROM fame_bosses_v1702 WHERE account_id=? AND boss_id=?', (aid,'tcp_first_v115')).fetchone()[0]
        if status != 'DONE' or fame != 1:
            raise AssertionError(f'Nieutrwalona nagroda: {status=}, {fame=}')
        return status


def main():
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v115-restart-') as td:
        # Cycle 1: synthetic first-clear is queued while a real, isolated
        # TCP server is running but the owner is OFFLINE. Kill before payout.
        proc, stream, log, port, db_path = child_start(td, cycle=1)
        try:
            aid = stage_offline_reward(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                before = conn.execute(
                    'SELECT status FROM v115_fame_delivery WHERE account_id=?',
                    (aid,)).fetchone()[0]
                if before != 'WAITING':
                    raise AssertionError('Reward was settled without an online owner')
        finally:
            _stop_child(proc)
            stream.close()
        if proc.poll() is None:
            raise AssertionError('First server child still alive')
        print('v115 TCP restart: pending entry survived first server stop', flush=True)

        # Cycle 2: a new Python process reopens the SAME SQLite database.
        # Login must settle EXP before Fame and only for the correct socket.
        proc, stream, log, port, restarted_db = child_start(td, cycle=2)
        try:
            if restarted_db != db_path:
                raise AssertionError('Server restart did not reuse the same SQLite file')
            gap = asyncio.run(collect_ordered_messages(port))
            check_ledger(db_path, aid)
            output = log.read_text(encoding='utf-8', errors='replace')
            if 'Traceback (most recent call last):' in output:
                raise AssertionError('Server error during payout: '+output[-1400:])
        finally:
            _stop_child(proc)
            stream.close()
        print('v115 TCP restart: EXP then Fame, committed after restart',flush=True)

        # Cycle 3: after another complete process restart, the persisted
        # ledger must prevent replaying either of those two messages.
        proc, stream, log, port, restarted_db = child_start(td, cycle=3)
        try:
            asyncio.run(check_relogin_no_duplicate(port))
            check_ledger(db_path, aid)
            with closing(sqlite3.connect(db_path)) as conn:
                if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise AssertionError('SQLite integrity failed after three server boots')
            output = log.read_text(encoding='utf-8', errors='replace')
            if 'Traceback (most recent call last):' in output:
                raise AssertionError('Server error after second restart: '+output[-1400:])
        finally:
            _stop_child(proc)
            stream.close()
        print('v115 TCP THREE REAL SERVER BOOTS/SOUNDPACK OFF: PASS, '
              f'EXP->Fama gap={gap:.2f}s, no duplicate, valid SQLite', flush=True)


if __name__=='__main__':
    main()
    # Native runtime imports retain helper threads unrelated to the TCP
    # child. All 3 TCP children and SQLite resources have already closed.
    sys.stdout.flush()
    os._exit(0)
