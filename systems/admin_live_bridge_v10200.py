# -*- coding: utf-8 -*-
"""Local loopback transport into the isolated *full* Soulbound server.

No production combat, database or rewards are executed in the owner's session.
The admin keeps the same MUD client, while input/output is switched to the
localhost cloned engine. Credentials are not copied or retained here.
"""
from __future__ import annotations
import asyncio
import logging
from systems import admin_live_native_arena_v8600 as native

HELP = ('ADMIN LIVE POMOC 74: arena real start POTWIERDZAM; '
        'arena real tunel POTWIERDZAM - polacz obecny klient MUD z izolowana '
        'pelna instancja silnika na 127.0.0.1:4900. W tunelu logujesz sie '
        'OSOBNO na kopii bazy. Wpisz dokladnie: arena wyjdz, aby wrocic. '
        'Uwaga: nie uruchamia produkcyjnej walki w tym samym procesie; '
        'to autentyczny silnik w izolowanym serwerze, dostepny z jednej sesji.')


def available_port():
    native._retire_if_exited()
    state=native._current
    if state is None or state['process'].poll() is not None or state['stop'].exists():
        raise ValueError('Najpierw uruchom arena real start POTWIERDZAM.')
    if state['port'] != 4900:
        raise ValueError('Tunel dostepny tylko na stalym prywatnym porcie 4900.')
    return state, state['port']


async def connect(session):
    if not session.is_admin():
        raise ValueError('Tylko administrator.')
    if getattr(session,'_v102_tunnel',None) is not None:
        raise ValueError('Tunel juz dziala.')
    if (getattr(session,'combat_mob_key',None) or getattr(session,'combat_pvp_target_id',None)
            or getattr(session,'combat_task',None) and not session.combat_task.done()):
        raise ValueError('Zakoncz prawdziwa walke przed polaczeniem z arena.')
    state,port=available_port()
    try:
        reader,writer=await asyncio.wait_for(asyncio.open_connection('127.0.0.1',port),timeout=3)
    except (OSError,asyncio.TimeoutError) as exc:
        raise ValueError('Izolowany silnik jeszcze nie nasluchuje. Wpisz arena real status.') from exc
    connection={'reader':reader,'writer':writer,'state':state,'owner':session.account_id,'task':None}
    session._v102_tunnel=connection
    connection['task']=asyncio.create_task(_pump(session,connection))
    return ('ARENA REAL TUNEL: polaczono z izolowanym silnikiem. '
            'Logowanie i walka odbywaja sie w KOPII gry. '
            'Aby wrocic do glownego Soulbound, wpisz: arena wyjdz.')


async def _pump(session,connection):
    try:
        while not session.closed and session._v102_tunnel is connection:
            chunk=await connection['reader'].read(4096)
            if not chunk:break
            # Preserve native Telnet negotiation/encoding; never send remote
            # content to the production command parser or database.
            session.writer.write(chunk)
            await session.writer.drain()
    except asyncio.CancelledError:
        # A local disconnect cancels only this copy-world stream.  The
        # finally clause still detaches it from the production session.
        return
    except (OSError, ConnectionError) as exc:
        logging.getLogger(__name__).info('Arena tunnel disconnected: %s', exc)
    finally:
        was_active=getattr(session,'_v102_tunnel',None) is connection
        _close_without_wait(session,connection)
        if was_active and not session.closed:
            try:await session.send('ARENA REAL TUNEL: polaczenie zakonczone. Wrociles do glownego Soulbound.')
            except (OSError,ConnectionError) as exc:
                logging.getLogger(__name__).debug('Arena disconnect notice not delivered: %s', exc)


def _close_without_wait(session,connection):
    if getattr(session,'_v102_tunnel',None) is connection:
        session._v102_tunnel=None
    connection['writer'].close()


async def disconnect(session):
    connection=getattr(session,'_v102_tunnel',None)
    if connection is None:return False
    _close_without_wait(session,connection)
    task=connection.get('task')
    if task is not None and task is not asyncio.current_task():
        task.cancel()
    return True


async def forward_if_connected(session,raw):
    """Executed BEFORE production parsing and any command logging."""
    connection=getattr(session,'_v102_tunnel',None)
    if connection is None:return False
    if raw.strip().casefold() in ('arena wyjdz','koniec areny'):
        await disconnect(session)
        await session.send('ARENA REAL TUNEL: powrot do glownego serwera.')
        return True
    try:
        state,_=available_port()
        if (state is not connection['state'] or session.account_id!=connection['owner']
                or not session.is_admin()):
            await disconnect(session)
            await session.send('ARENA REAL TUNEL: wlasciciel lub instancja zmieniona; polaczenie zakonczone.')
            return True
        if len(raw)>4096 or '\x00' in raw or '\n' in raw or '\r' in raw:
            await session.send('ARENA REAL TUNEL: niedozwolona dlugosc lub znak sterujacy.')
            return True
        connection['writer'].write((raw+'\r\n').encode('utf-8'))
        await connection['writer'].drain()
    except (OSError,ConnectionError,ValueError,RuntimeError):
        await disconnect(session)
        await session.send('ARENA REAL TUNEL: instancja niedostepna, wrociles do gry.')
    return True
