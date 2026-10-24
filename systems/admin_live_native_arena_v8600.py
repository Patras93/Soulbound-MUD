# -*- coding: utf-8 -*-
"""Admin Live v86: manage a *separate native server*, never mutate in-session arena.

The owner runs the exact existing combat engine against a read-only SQLite
snapshot. One private listener on 127.0.0.1:4900 per host. Session-local
simulations remain available, with their different fidelity clearly labelled.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile


HELP = (
    'ADMIN LIVE POMOC 44: arena real start POTWIERDZAM - uruchom caly oryginalny '
    'silnik gry na prywatnej migawce SQLite, 127.0.0.1:4900; '
    'arena real start pusta POTWIERDZAM - NOWA PUSTA baza bez kopiowania kont; '
    'arena real stop POTWIERDZAM - zatrzymaj i usun kopie. '
    'Zaloguj sie osobnym polaczeniem klienta MUD na port 4900. '
    'Postep, nagrody i zmiany w kopii sa usuwane; serwer port 4000 nietkniety. '
    'Tylko administrator; nie jest to symulator w tej samej sesji.'
)

# Intentionally process-wide: never spawn one private server per player session.
_current = None


def _loopback_port_free(port=4900):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', port))


def _db_file(server):
    """Ask SQLite for its actual opened database, not an assumed file path."""
    connection = server.db.conn
    for _, name, filename in connection.execute('PRAGMA database_list'):
        if name == 'main' and filename:
            candidate = Path(filename).resolve()
            if candidate.is_file():
                return candidate
    raise ValueError('Baza SQLite nie ma lokalnego pliku; arena real odmowila uruchomienia.')


def _retire_if_exited():
    global _current
    state = _current
    if state is not None and state['process'].poll() is not None:
        _current = None
        try:
            shutil.rmtree(state['control'])
        except OSError:  # AUDIT_INTENTIONAL_PASS: temporary control files may be locked on Windows after worker exit
            pass
        return True
    return False


def arena_status():
    if _current is None:
        return 'ARENA REAL: WYLACZONA. Wpisz admin live arena real start POTWIERDZAM.'
    state = _current
    if state['process'].poll() is not None:
        code = state['process'].returncode
        log = _last_log(state)
        _retire_if_exited()
        return f'ARENA REAL: zakonczona (kod {code}). {log}'
    log = _last_log(state)
    if 'World Core nasłuchuje:' in log or 'World Core nasluchuje:' in log:
        state['ready'] = True
    status = 'DZIALA' if state.get('ready') else 'URUCHAMIANIE'
    if state['stop'].exists():
        status = 'ZATRZYMYWANIE'
    return f"ARENA REAL: {status}, 127.0.0.1:{state['port']}. Klient MUD lacz osobno. {log}"


def _last_log(state):
    path = state['log']
    try:
        # Read only a bounded tail for accessibility; no production credentials.
        with path.open('rb') as handle:
            handle.seek(0, 2)
            handle.seek(max(0, handle.tell() - 1600))
            data = handle.read(1600)
        content = data.decode('utf-8', errors='replace')
        if 'Traceback' in content or 'ODMOWA' in content:
            return 'Blad uruchomienia instancji; sprawdz test serwera.'
        if 'World Core nasłuchuje:' in content or 'World Core nasluchuje:' in content:
            return 'World Core nasłuchuje:'
    except OSError:  # AUDIT_INTENTIONAL_PASS: logfile may not exist while arena starts; status reports pending state
        pass
    return ''


def arena_start(server, *, source=None, port=4900, fresh=False):
    global _current
    _retire_if_exited()
    if _current is not None:
        raise ValueError('ARENA REAL jest juz uruchomiona; jedna instancja na serwer.')
    if port == 4000 or not 1024 <= port <= 65535:
        raise ValueError('Port laboratoryjny niedozwolony.')
    _loopback_port_free(port)
    # In fresh mode not even the original SQLite connection is inspected.
    dbfile = None if fresh else _db_file(server)
    root = (Path(source) if source is not None else Path(__file__).resolve().parents[1]).resolve()
    if not (root / 'arena_real_izolowana.py').is_file() or not (root / 'VERSION').is_file():
        raise ValueError('Brak pelnego pakietu silnika areny.')
    control = Path(tempfile.mkdtemp(prefix='Soulbound_Lab_Kontrola_'))
    stop = control / 'stop.signal'
    logfile = control / 'arena.log'
    try:
        # Console-free controller: the lab watches stop.signal and owning PID.
        with logfile.open('wb') as sink:
            params=[sys.executable, '-u', str(root / 'arena_real_izolowana.py'),
                    '--source', str(root), '--port', str(port),
                    '--stop-file', str(stop), '--parent-pid', str(os.getpid())]
            if fresh:
                params.append('--fresh')
            else:
                params.extend(['--database',str(dbfile)])
            proc = subprocess.Popen(params,
                cwd=str(root), stdin=subprocess.DEVNULL, stdout=sink,
                stderr=subprocess.STDOUT, close_fds=True)
        _current = {'process': proc, 'control': control, 'stop': stop, 'log': logfile, 'port': port}
    except BaseException:
        shutil.rmtree(control, ignore_errors=True)
        raise
    mode = 'pusta baza bez kont produkcyjnych' if fresh else 'osobna migawka SQLite'
    return f'ARENA REAL: START, {mode}, tylko 127.0.0.1:{port}. Sprawdz admin live arena real status. Nagrody z testu nie trafiaja na serwer glowny.'


async def arena_stop():
    _retire_if_exited()
    if _current is None:
        return 'ARENA REAL: juz wylaczona.'
    state = _current
    # Do not terminate/kill the wrapper; it MUST run its finally to delete DB.
    state['stop'].write_text('STOP\n', encoding='ascii')
    for _ in range(80):
        if state['process'].poll() is not None:
            _retire_if_exited()
            return 'ARENA REAL: zatrzymana; prywatna baza i nagrody usuniete.'
        await asyncio.sleep(0.2)
    return 'ARENA REAL: wyslano STOP, instancja nadal konczy prace. Sprawdz status; nie zamykaj na sile.'


async def dispatch_v8600(session, cmd, tail):
    if cmd == 'pomoc' and tail.strip() == '44':
        if not session.is_admin():
            await session.send('Nieznana komenda.')
        else:
            await session.send(HELP)
        return True
    if cmd != 'arena' or not tail.strip().casefold().startswith('real'):
        return False
    if not session.is_admin():
        await session.send('Nieznana komenda.')
        return True
    parts = tail.strip().split()
    if not parts or parts[0].casefold() != 'real':
        return False
    try:
        if len(parts) == 2 and parts[1].casefold() == 'status':
            result = arena_status()
        elif len(parts) == 4 and parts[1].casefold() in ('start','uruchom') and parts[2].casefold() == 'pusta' and parts[3] == 'POTWIERDZAM':
            result = arena_start(session.server,fresh=True)
        elif len(parts) == 3 and parts[1].casefold() in ('start','uruchom') and parts[2] == 'POTWIERDZAM':
            result = arena_start(session.server)
        elif len(parts) == 3 and parts[1].casefold() in ('stop','zatrzymaj') and parts[2] == 'POTWIERDZAM':
            result = await arena_stop()
        else:
            result = HELP
    except (OSError, ValueError, RuntimeError) as error:
        result = 'ARENA REAL: odmowa - ' + str(error)
    await session.send(result)
    return True
