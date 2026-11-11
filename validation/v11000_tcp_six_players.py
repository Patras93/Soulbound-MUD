# -*- coding: utf-8 -*-
"""Six authenticated localhost TCP clients, with disposable accounts and SQLite.

This is an actual TCP/login/party/command integration gate. It is NOT a combat
benchmark or a remote load test. Only 127.0.0.1 and an ephemeral port are used.
Never connect to a running player's server; start an isolated child instead.
"""
from __future__ import annotations

import asyncio
import json
import re
from contextlib import closing, suppress
import os
from pathlib import Path
import socket
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PLAYERS = 6
PASSWORD = 'test_only_tcp_2026_password'
BOOT_TIMEOUT = 240
PROMPT_TIMEOUT = 40
# Heavy real-time combat can postpone quest replies; timeout stays finite and
# a genuinely stuck command still fails the gate (unlike silent retry PASS).
COMMAND_TIMEOUT = 30


def guarded_child_env(directory, port):
    """Deliberately discard inherited production paths, credentials and port."""
    work = Path(directory).resolve()
    assert work.is_dir() and work != ROOT and work != ROOT.parent and ROOT not in work.parents
    db_path = work / 'six_players.sqlite'
    env = os.environ.copy()
    for key in ('PORT', 'RAILWAY_TCP_APPLICATION_PORT', 'DATABASE_URL',
                'RAILWAY_VOLUME_MOUNT_PATH', 'SOULBOUND_WORLD_SEED_FILE',
                'SOULBOUND_WORLD_SEED', 'SOULBOUND_SMTP_PASSWORD',
                'SOULBOUND_MAIL_PASSWORD', 'SMTP_PASSWORD',
                'SOULBOUND_CONTROL_FILE', 'SOULBOUND_CONTROL_TOKEN',
                'SOULBOUND_FULL_AUDIT', 'SOULBOUND_HISTORICAL_AUDITS',
                'SOULBOUND_ADMIN_ACCOUNTS'):
        env.pop(key, None)
    env.update(SOULBOUND_DB=str(db_path), SOULBOUND_PORT=str(port),
               SOULBOUND_HOST='127.0.0.1', SOULBOUND_TCP_TEST_CHILD='1',
               SOULBOUND_WORLD_SEED_FILE=str(work / 'test_seed.txt'),
               SOULBOUND_MAX_CLIENTS='6', SOULBOUND_V107_STAGING='1',
               SOULBOUND_V109_STAGING='1', SOULBOUND_V110_STAGING='1', PYTHONUTF8='1',
               PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               PYTHONDONTWRITEBYTECODE='1')
    return env, db_path


def free_local_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class TcpPlayer:
    def __init__(self, account, name, port):
        self.account, self.name, self.port = account, name, port
        self.reader = self.writer = None
        self.times = []

    async def until(self, marker: str, timeout=PROMPT_TIMEOUT):
        # The login prompts may have no trailing newline. Use readuntil, not readline.
        raw = await asyncio.wait_for(self.reader.readuntil(marker.encode('utf-8')), timeout)
        return raw.decode('utf-8', 'replace')

    async def send(self, command):
        self.writer.write((command + '\n').encode('utf-8'))
        await asyncio.wait_for(self.writer.drain(), COMMAND_TIMEOUT)

    async def connect_and_login(self):
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', self.port), 10)
        await self.until('Wybierz opcję: ')
        await self.send('1')
        await self.until('Nazwa konta: ')
        await self.send(self.account)
        await self.until('Hasło: ')
        await self.send(PASSWORD)
        await self.until('Wybierz opcję: ')
        await self.send('1')
        await self.until('Postać: ')
        await self.send('1')
        response = await self.until('Wpisz help, aby poznać komendy.')
        if f'Witaj, {self.name}' not in response and self.name not in response:
            raise AssertionError(f'{self.name}: login did not enter the game')
        await self.drain_idle()

    async def drain_idle(self, quiet=0.15, total=2):
        chunks = []
        until = time.monotonic() + total
        while time.monotonic() < until:
            try:
                data = await asyncio.wait_for(self.reader.read(16384), quiet)
            except asyncio.TimeoutError:
                break
            if not data:
                raise ConnectionError(f'{self.name}: connection closed')
            chunks.append(data)
        return b''.join(chunks).decode('utf-8', 'replace')

    async def command(self, command, quiet=0.18):
        await self.drain_idle(quiet=0.05, total=0.12)
        begin = time.perf_counter()
        await self.send(command)
        # A quiet period is not enough if the server is slow: wait for first bytes.
        first = await asyncio.wait_for(self.reader.read(16384), COMMAND_TIMEOUT)
        if not first:
            raise ConnectionError(f'{self.name}: server closed after {command}')
        tail = await self.drain_idle(quiet=quiet, total=1.8)
        elapsed = (time.perf_counter() - begin) * 1000
        self.times.append(elapsed)
        result = first.decode('utf-8', 'replace') + tail
        if 'Wystąpił błąd komendy' in result or 'Wystąpił błąd sesji' in result or 'Traceback (most recent call last)' in result:
            raise AssertionError(f'{self.name}: runtime failure in {command}: {result[-450:]}')
        return result

    async def close(self):
        if self.writer is not None:
            self.writer.close()
            with suppress(ConnectionError, OSError, asyncio.TimeoutError):
                await asyncio.wait_for(self.writer.wait_closed(), 2)


async def read_complete_party_roster(client, initial, expected_names, *, timeout=20.0):
    """Read a line-streamed status until each numbered member line arrives.

    A short network quiet interval after the header is not proof that the
    following await self.send(...) lines have finished.  An actual missing
    player must STILL fail; never accept the header's count as proof.
    """
    def listed_names(data):
        clean = data.replace("\r", "")
        return {name for name in expected_names if re.search(
            rf"(?im)^\s*\d+\.\s*{re.escape(name)}\.\s+Lokacja:", clean
        )}

    data = initial
    deadline = time.monotonic() + timeout
    while len(listed_names(data)) != len(expected_names):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            chunk = await asyncio.wait_for(client.reader.read(16384), remaining)
        except asyncio.TimeoutError:
            break
        if not chunk:
            break
        data += chunk.decode('utf-8', 'replace')
        if len(data) > 65536:
            raise AssertionError('Party status emitted excessive data without a complete roster')
        if ('Wystąpił błąd komendy' in data or 'Wystąpił błąd sesji' in data
                or 'Traceback (most recent call last)' in data):
            raise AssertionError('Runtime failure while reading party roster: ' + data[-500:])
    missing = [name for name in expected_names if name not in listed_names(data)]
    return data, missing


def run_party_stream_regression():
    """Check split TCP responses, unrelated notices, and genuinely missing members."""
    class FakeReader:
        def __init__(self, chunks):
            self.chunks = iter(chunks)
        async def read(self, _):
            await asyncio.sleep(0)
            return next(self.chunks, b'')
    class FakeClient:
        def __init__(self, chunks):
            self.reader = FakeReader(chunks)
    names = [f'Testtcp{i}' for i in range(1, 7)]
    header = 'DRUŻYNA. Lider: Testtcp1. Członkowie: 6 z 8.\n'
    roster = ''.join(f'{i}. {name}. Lokacja: Plac.\r\n' for i, name in enumerate(names, 1))

    async def check():
        checks = 0
        full, missing = await read_complete_party_roster(FakeClient([]), header + roster, names, timeout=.1)
        assert not missing and len(full) > len(header); checks += 1
        # Force header to arrive separately and split one numbered member line.
        bits = [roster[:12].encode('utf-8'), roster[12:29].encode('utf-8'), roster[29:].encode('utf-8')]
        full, missing = await read_complete_party_roster(FakeClient(bits), header, names, timeout=.1)
        assert not missing and 'Testtcp6. Lokacja:' in full; checks += 1
        # A notification mentioning player names must not masquerade as roster entries.
        notice = ''.join(f'{name} dolaczyl do druzyny.\n' for name in names)
        full, missing = await read_complete_party_roster(FakeClient([]), header + notice, names, timeout=.1)
        assert missing == names; checks += 1
        # A six-person header with only five roster lines must still fail.
        full, missing = await read_complete_party_roster(FakeClient([]), header + ''.join(
            f'{i}. {name}. Lokacja: Plac.\n' for i, name in enumerate(names[:5], 1)
        ), names, timeout=.1)
        assert missing == ['Testtcp6']; checks += 1
        # An unrelated runtime error must not be swallowed while awaiting the roster.
        try:
            await read_complete_party_roster(FakeClient([b'Wystapil blad'.replace(b'Wystapil blad',
                'Wystąpił błąd komendy'.encode('utf-8'))]), header, names, timeout=.1)
        except AssertionError as exc:
            assert 'Runtime failure' in str(exc); checks += 1
        else:
            raise AssertionError('Runtime error during roster collection not detected')
        return checks
    return asyncio.run(check())


def _money_snapshot(response: str) -> tuple[int, int, int]:
    """Extract actual displayed currency amounts from a complete money reply.

    Additional notices, formatting, and other async messages can differ
    between two TCP reads. Missing/ambiguous currency responses must FAIL.
    """
    pattern = r'(?m)^Masz\s+([0-9]+) mithril,\s+([0-9]+) złota,\s+([0-9]+) srebra\.'
    matches = re.findall(pattern, response.replace('\r', ''))
    if len(matches) != 1:
        raise AssertionError('Brak jednoznacznej odpowiedzi salda money, matches=' + str(len(matches)))
    return tuple(int(n) for n in matches[0])


async def exercise(names, port, *, after_restart=False, routes=None):
    clients = [TcpPlayer(account, name, port) for account, name in names]
    checks = 0
    try:
        await asyncio.gather(*(c.connect_and_login() for c in clients))
        checks += PLAYERS
        # The sixth socket must be rejected by the REAL private game handler,
        # not just by a mocked concurrency constant. Never send credentials.
        overflow_reader, overflow_writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', port), 10)
        try:
            overflow_banner = await asyncio.wait_for(overflow_reader.read(4096), 8)
            if 'Serwer jest pełny' not in overflow_banner.decode('utf-8', 'replace'):
                raise AssertionError('Seventh connection not rejected at six-player cap: '
                                     + repr(overflow_banner[-180:]))
            checks += 1
            print('TCP LIMIT 6: siodme polaczenie odrzucone przez serwer PASS', flush=True)
        finally:
            overflow_writer.close()
            with suppress(ConnectionError, OSError, asyncio.TimeoutError):
                await asyncio.wait_for(overflow_writer.wait_closed(), 2)
        # Every command is sent by all SIX real sessions concurrently.
        for command in ('who', 'status', 'look', 'help', 'tytani lista', 'expbank', 'lochy7',
                        'quests', 'skills', 'professions', 'inventory', 'equipment',
                        'map', 'where', 'money', 'fame', 'titles', 'achievements',
                        'tools', 'spells', 'soul', 'friends', 'atlas', 'bestiary',
                        'codex'):
            results = await asyncio.gather(*(c.command(command) for c in clients))
            if any(not response.strip() for response in results):
                raise AssertionError('No response to ' + command)
            if command == 'tytani lista' and any('tytan' not in r.casefold() for r in results):
                raise AssertionError('Titan command did not return Titan status')
            if command == 'expbank' and any('exp' not in r.casefold() for r in results):
                raise AssertionError('EXP Bank command not available')
            checks += PLAYERS
            if command in ('lochy7', 'money', 'soul', 'codex'):
                print(f'TCP SIX: command batch through {command} ({clients[0].name}..{clients[-1].name}) PASS', flush=True)

        print(f'TCP SIX: {len(clients)} logged-in clients completed {len(clients[0].times)} read-only commands each', flush=True)

        # v2.30.2: real TCP commands with negative routes, on first cycle only.
        # The game must not reward players for invalid NPC/recipe/ship inputs.
        if not after_restart:
            from validation.v2302_exhaustive_game_coverage import (
                ADDITIONAL_TCP_CASES, NEGATIVE_TCP_CASES,
            )
            lead = clients[0]
            balance_before = _money_snapshot(await lead.command('money'))
            for extra in ADDITIONAL_TCP_CASES:
                response = await lead.command(extra)
                print(f'TCP EXTRA: {extra} PASS ({lead.times[-1]:.0f}ms)', flush=True)
                if not response.strip():
                    raise AssertionError('Brak odpowiedzi komendy: ' + extra)
                checks += 1
            balance_after = _money_snapshot(await lead.command('money'))
            if balance_before != balance_after:
                raise AssertionError('Komendy testowe zmienily saldo: '
                                     + repr(balance_before) + ' -> ' + repr(balance_after))
            checks += 1
            print('TCP SCENARIUSZE 2.30.2: '
                  f'{len(ADDITIONAL_TCP_CASES)} dodatkowych polecen, '
                  f'{len(NEGATIVE_TCP_CASES)} bledne argumenty, waluta bez zmian PASS', flush=True)

        if after_restart:
            print('TCP SIX: starting post-restart quest and courier checks', flush=True)
            # v2.32.0: a genuine NPC quest and combat kill must survive restart.
            from validation.v2320_autonomous_tcp import check_after_restart
            checks += await check_after_restart(clients, routes)
            times = [t for c in clients for t in c.times]
            return {'checks': checks, 'logged_in': PLAYERS, 'commands': len(times),
                    'average_ms': round(statistics.mean(times), 1),
                    'p95_ms': round(sorted(times)[max(0, int(len(times)*.95)-1)], 1),
                    'max_ms': round(max(times), 1)}

        print('TCP SIX: starting party invitations', flush=True)
        lead = clients[0]
        result = await lead.command('druzyna zaloz')
        if 'drużyn' not in result.lower() and 'druzyn' not in result.lower():
            raise AssertionError('Party creation response missing: ' + result[-350:])
        checks += 1
        for member in clients[1:]:
            await lead.command('druzyna zapros ' + member.name)
            result = await member.command('dolacz')
            if 'dołącza' not in result.lower() and 'drużyn' not in result.lower() and 'druzyn' not in result.lower():
                raise AssertionError(member.name + ': party invitation not accepted: ' + result[-300:])
            checks += 1
            print('TCP PARTY INVITE: '+member.name+' PASS', flush=True)
        party = await lead.command('druzyna status')
        party, missing = await read_complete_party_roster(
            lead, party, [client.name for client in clients], timeout=20.0)
        if missing:
            raise AssertionError('Party missing roster entries: ' + ', '.join(missing)
                                 + '; ' + party[-1200:])
        checks += PLAYERS
        results = await asyncio.gather(*(c.command('druzyna status') for c in clients))
        if any('drużyn' not in item.lower() and 'druzyn' not in item.lower() for item in results):
            raise AssertionError('Party status did not arrive on all clients')
        checks += PLAYERS
        print('TCP SIX: all 6 party members verified; begin NPC story and real combat', flush=True)
        # v2.32.0: invoke the actual NPC dialogue, player command router,
        # basement navigation, combat and quest progress on private TCP.
        from validation.v11000_tcp_six_party_journey import run_six_player_journey
        journey = await run_six_player_journey(clients)
        checks += journey['checks']
        times = [t for c in clients for t in c.times]
        return {'checks': checks, 'logged_in': PLAYERS,
                'commands': len(times), 'average_ms': round(statistics.mean(times), 1),
                'p95_ms': round(sorted(times)[max(0, int(len(times) * .95) - 1)], 1),
                'max_ms': round(max(times), 1)}
    finally:
        await asyncio.gather(*(c.close() for c in clients), return_exceptions=True)


def wait_for_world_server(process, logfile, seconds=BOOT_TIMEOUT):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Child server quit during startup (code ' + str(process.returncode) + ')')
        text = logfile.read_text(encoding='utf-8', errors='replace') if logfile.exists() else ''
        if 'TEST_TCP_ACCOUNTS_READY' in text and 'World Core nasłuchuje:' in text:
            return
        time.sleep(.25)
    raise TimeoutError('World Core failed to start within ' + str(seconds) + ' seconds')


def run_contract():
    """Fast release gate for six-player harness isolation, without sockets."""
    import tempfile
    checks = 0
    assert PLAYERS == 6; checks += 1
    with tempfile.TemporaryDirectory(prefix='sb110_tcp6_contract-') as temp:
        env, path = guarded_child_env(temp, 45672)
        for condition in (
            path.parent == Path(temp).resolve(),
            path.name == 'six_players.sqlite',
            env['SOULBOUND_DB'] == str(path),
            env['SOULBOUND_HOST'] == '127.0.0.1',
            env['SOULBOUND_PORT'] == '45672',
            env['SOULBOUND_TCP_TEST_CHILD'] == '1',
            'RAILWAY_TCP_APPLICATION_PORT' not in env,
            'PORT' not in env,
            'SOULBOUND_ADMIN_ACCOUNTS' not in env,
            'RAILWAY_VOLUME_MOUNT_PATH' not in env,
            env['SOULBOUND_WORLD_SEED_FILE'] == str(Path(temp).resolve() / 'test_seed.txt'),
            env['SOULBOUND_MAX_CLIENTS'] == '6',
        ):
            assert condition
            checks += 1
    return checks




def _stop_child(proc):
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def _run_server_cycle(temp, db_path, names, *, after_restart=False):
    """Start a PRIVATE child; reuse only the test DB during restart."""
    port = free_local_port()
    env, actual_db = guarded_child_env(temp, port)
    assert actual_db == db_path
    path = Path(temp) / ('server-restart.log' if after_restart else 'server-initial.log')
    proc = None
    try:
        with path.open('w', encoding='utf-8') as sink:
            proc = subprocess.Popen(
                [sys.executable, '-u', str(ROOT / 'validation' / 'v11000_tcp_child.py')],
                cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                stdout=sink, stderr=subprocess.STDOUT)
            wait_for_world_server(proc, path)
            route_lines = [line.split('TEST_AUTOPLAYER_ROUTE_JSON:',1)[1]
                           for line in path.read_text(encoding='utf-8').splitlines()
                           if line.startswith('TEST_AUTOPLAYER_ROUTE_JSON:')]
            if len(route_lines) != 1:
                raise AssertionError('Missing actual NPC route from private TCP child')
            routes = json.loads(route_lines[0])
            if after_restart:
                _durable_rat_quest_progress(db_path,label='after restart, before login')
            result = asyncio.run(exercise(names, port, after_restart=after_restart,
                                          routes=routes))
            if not after_restart:
                # The UI can announce 1/10 while the combat reward transaction
                # is still finishing. Do not SIGTERM the private server until
                # an INDEPENDENT SQLite reader proves that the event committed.
                deadline=time.monotonic()+30
                while True:
                    durable=_durable_rat_quest_progress(db_path,label='commit verification')
                    if any(status=='active' and int(progress)>=1 for status,progress in durable):
                        print('TCP QUEST DURABILITY: kill committed before restart PASS',flush=True)
                        break
                    if time.monotonic() >= deadline:
                        raise AssertionError('Real kill visible to client, but not committed within 30 sec')
                    time.sleep(.5)
        if proc.poll() is not None:
            raise RuntimeError('Private server stopped while clients were active')
        # The test must also verify that the server did not log an unhandled exception.
        server_text = path.read_text(encoding='utf-8', errors='replace')
        if 'Traceback (most recent call last):' in server_text:
            raise AssertionError('Private server wrote Python traceback: ' + server_text[-1800:])
        return result
    except BaseException:
        import traceback
        print('TCP TEST FAIL: ' + ('restart' if after_restart else 'initial login'), flush=True)
        traceback.print_exc()
        if path.exists():
            print('LAST SERVER LOG LINES:', flush=True)
            print('\n'.join(path.read_text(encoding='utf-8', errors='replace').splitlines()[-30:]), flush=True)
        raise
    finally:
        _stop_child(proc)


def _check_db(db_path):
    # sqlite3.Connection as context manager does NOT close the connection.
    # On Windows an open handle prevents TemporaryDirectory from deleting the DB.
    with closing(sqlite3.connect(db_path)) as conn:
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        rows = conn.execute("SELECT username FROM accounts WHERE username LIKE 'tcpcheck%' ORDER BY username").fetchall()
        chars = conn.execute('SELECT COUNT(*) FROM characters').fetchone()[0]
        if integrity != 'ok' or len(rows) != PLAYERS or chars != PLAYERS:
            raise AssertionError(f'Persistence failure: SQLite {integrity}, accounts={len(rows)}, characters={chars}')
        return chars


def _durable_rat_quest_progress(db_path, *, label):
    # Read from a completely independent SQLite connection, never from the
    # live event-loop transaction. This is diagnostic AND a durability gate.
    with closing(sqlite3.connect(db_path,timeout=10)) as conn:
        rows=conn.execute("SELECT q.status,q.progress FROM quests q JOIN accounts a "
                          "ON q.account_id=a.id WHERE a.username='tcpcheck1' "
                          "AND q.quest_id='temple_rats'").fetchall()
    print(f'TCP DURABLE RAT QUEST [{label}]: {rows!r}',flush=True)
    return rows

def _check_autoplayer_delivery(db_path):
    """The private courier quest must be persisted after the TCP player exits."""
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute("""
            SELECT q.status, q.completion_count
            FROM quests AS q JOIN accounts AS a ON a.id = q.account_id
            WHERE a.username = 'tcpcheck1'
              AND q.quest_id = 'sol_starter_blacksmith_delivery'
        """).fetchone()
        if row is None or row[0] != 'completed' or int(row[1]) != 1:
            raise AssertionError('Courier reward not durably recorded: '+repr(row))
        return 1


def run_sqlite_cleanup_regression():
    """Ensure both success and exception paths CLOSE SQLite handles on Windows.

    A ``with sqlite3.connect(...)`` block commits but does not close the DB.
    TrackingConnection makes that mistake fail on every OS, not just Windows.
    The scratch file is unrelated to character/world databases.
    """
    from unittest.mock import patch

    real_connect = sqlite3.connect
    opened = []

    class TrackingConnection(sqlite3.Connection):
        did_close = False

        def close(self):
            self.did_close = True
            return super().close()

    def tracking_connect(*args, **kwargs):
        kwargs['factory'] = TrackingConnection
        result = real_connect(*args, **kwargs)
        opened.append(result)
        return result

    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb110_tcp6_close_contract_') as temp:
        db_path = Path(temp) / 'six_players.sqlite'
        with closing(real_connect(db_path)) as db:
            db.execute('CREATE TABLE accounts (username TEXT)')
            db.execute('CREATE TABLE characters (id INTEGER)')
            db.executemany('INSERT INTO accounts VALUES (?)', [(f'tcpcheck{i+1}',) for i in range(PLAYERS)])
            db.executemany('INSERT INTO characters VALUES (?)', [(i+1,) for i in range(PLAYERS)])
            db.commit()
        with patch.object(sqlite3, 'connect', tracking_connect):
            assert _check_db(db_path) == PLAYERS
        checks += 1
        assert len(opened) == 1 and opened[-1].did_close, 'Success left SQLite open'
        checks += 1

        # A malformed test DB should fail, but the error must not leak a handle.
        with closing(real_connect(db_path)) as db:
            db.execute('DROP TABLE characters')
            db.commit()
        with patch.object(sqlite3, 'connect', tracking_connect):
            try:
                _check_db(db_path)
            except sqlite3.OperationalError:
                checks += 1
            else:
                raise AssertionError('Missing characters table was not detected')
        assert len(opened) == 2 and opened[-1].did_close, 'Error left SQLite open'
        checks += 1

        # On Windows these operations would throw WinError 32 if handles remain.
        renamed = db_path.with_name('cleaned.sqlite')
        db_path.rename(renamed)
        checks += 1
        renamed.unlink()
        checks += 1
        assert not renamed.exists() and not db_path.exists()
        checks += 1
    return checks


def main():
    start = time.monotonic()
    print('TCP 6 GRACZY v3.31.5: dwa starty, 6 logowan, party i zapis SQLite', flush=True)
    stream_checks = run_party_stream_regression()
    print(f'TCP PARTY STREAM: {stream_checks} segment/roster checks PASS', flush=True)
    from validation.v11000_tcp_six_party_journey import run_contract as six_quest_contract
    assert six_quest_contract() == 3
    print('TCP SIX QUEST SHARING CONTRACT: 3/3 PASS', flush=True)
    assert run_contract() >= 12
    assert run_sqlite_cleanup_regression() == 7
    print('TCP ISOLATION + SQLITE HANDLES: PASS', flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix='sb110_tcp6_') as temp:
            db_path = Path(temp).resolve() / 'six_players.sqlite'
            names = [(f'tcpcheck{i+1}', f'Testtcp{i+1}') for i in range(PLAYERS)]
            first = _run_server_cycle(temp, db_path, names)
            count = _check_db(db_path)
            durable = _durable_rat_quest_progress(db_path,label='after first stop')
            print(f"TCP ROUND 1: {first['logged_in']}/{PLAYERS} players; "
                  f"{first['commands']} commands; {first['checks']} checks PASS", flush=True)
            print(f"TCP latency: avg {first['average_ms']} ms; p95 {first['p95_ms']} ms; "
                  f"max {first['max_ms']} ms (localhost, incl. response collection)", flush=True)
            print(f'SQLite after stop: {count} characters PASS', flush=True)
            second = _run_server_cycle(temp, db_path, names, after_restart=True)
            count = _check_db(db_path)
            print(f"TCP RESTART: {second['logged_in']}/{PLAYERS} relogged; "
                  f"{second['commands']} commands; {second['checks']} checks PASS", flush=True)
            _check_autoplayer_delivery(db_path)
            print(f'SQLite after restart: {count} original characters; integralnosc PASS; '
                  'kurier Sol -> Doran zakonczony w SQLite PASS', flush=True)
    except Exception as exc:
        print('TCP 6 GRACZY: FAIL: ' + str(exc), flush=True)
        return 1
    print(f'TCP 6 GRACZY: PASS; czas {time.monotonic()-start:.1f} s; '
          'testowa baza usunieta, prawdziwa baza NIETKNIETA', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
