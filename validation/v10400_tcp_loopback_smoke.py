# -*- coding: utf-8 -*-
"""Optional disposable TCP smoke test. 127.0.0.1 only, never port 4000.

Does not authenticate or perform combat; it checks startup and login banner,
not end-to-end player/raid gameplay. The database is created in TemporaryDirectory.
"""
from __future__ import annotations
import os, socket, subprocess, sys, tempfile, time
from validation.v10400_release_isolation_guard import private_tcp_environment
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _wait_for_banner(host, port, deadline, *, child=None, required_markers=(b'SOULBOUND ONLINE',)):
    """Keep ONE socket queued during slow world bootstrap.

    server.py opens a pre-bound listening socket before loading the world.
    A successful connect() alone does not mean asyncio is serving login.
    Closing and reconnecting in a loop can fill that bootstrap backlog.
    """
    last_error = None
    client = None
    received = bytearray()
    try:
        while time.monotonic() < deadline:
            if child is not None and child.poll() is not None:
                raise RuntimeError('Serwer zakonczyl dzialanie przed ekranem logowania.')
            if client is None:
                try:
                    client = socket.create_connection((host, port), timeout=min(1, max(.1, deadline-time.monotonic())))
                    client.settimeout(.5)
                except OSError as exc:
                    last_error = str(exc)
                    time.sleep(.15)
                    continue
            try:
                client.settimeout(min(.35, max(.02, deadline-time.monotonic())))
                data=client.recv(4096)
                if not data:
                    raise RuntimeError('Serwer zamknal polaczenie przed ekranem logowania.')
                received.extend(data)
                if len(received) > 65536:
                    raise RuntimeError('Przekroczony rozmiar powitania TCP.')
                # Telnet IAC / negocjacja UTF-8 NIE sa dowodem gotowego loginu.
                # TCP moze przeslac naglowek i menu w osobnych pakietach.
                if all(marker in received for marker in required_markers):
                    return bytes(received)
            except socket.timeout:
                continue
            except OSError as exc:
                last_error=str(exc)
                client.close();client=None
        raise TimeoutError('Brak powitania TCP przed limitem; ostatni blad: '+str(last_error))
    finally:
        if client is not None:
            client.close()

def run(*, startup_timeout=115):
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as temp:
        while True:
            with socket.socket() as s:
                s.bind(('127.0.0.1', 0))
                port=s.getsockname()[1]
            if port != 4000:
                break
        env=private_tcp_environment(os.environ, temp, port)
        with open(Path(temp)/'stdout.txt','w',encoding='utf-8') as log:
            p=subprocess.Popen([sys.executable,'-u',str(ROOT/'server.py')],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                try:
                    received=_wait_for_banner('127.0.0.1',port,
                        time.monotonic()+startup_timeout,child=p,
                        required_markers=(b'SOULBOUND ONLINE',b'MENU G',b'Wybierz opcj'))
                except (RuntimeError,TimeoutError) as exc:
                    tail=(Path(temp)/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-1400:]
                    stage=('tylko socket bootstrap' if 'bootstrap port open' in tail
                           and 'World Core nasłuchuje' not in tail else 'start gry / logowanie')
                    raise RuntimeError(f'TCP smoke FAIL ({stage}): {exc}; log: {tail}') from exc
                return {'connected':True,'login_menu_ready':True,
                        'banner':received.decode('utf-8','replace')[-500:],
                        'port':port,'production_used':False}
            finally:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill();p.wait(timeout=3)

if __name__=='__main__':
    print(run())
